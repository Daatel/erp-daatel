"""
Servidor Listener do Telegram Bot para o Conector por Voz ERP DAATEL (v5).
Executa em Event Loop assíncrono com asyncio.to_thread, suporte a botões inline,
envio de PDF do DAV via sendDocument e Job de Expiração de Rascunhos TTL.
"""

import os
import sys
import time
import json
import uuid
import asyncio
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

import database
from services.voice_nlu_service import VoiceNLUService
from services.erp_voice_bridge import (
    preparar_resumo_lancamento,
    efetivar_lancamento_rascunho,
    obter_limite_alcada_usuario
)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TelegramVoiceListener")


def _get_bot_token() -> Optional[str]:
    """Obtém o token do bot a partir da tabela empresa_config ou variável de ambiente."""
    token_env = os.getenv("TELEGRAM_BOT_TOKEN")
    if token_env:
        return token_env.strip()

    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_token FROM empresa_config LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        database.release_connection(conn)
        if row and row[0]:
            return str(row[0]).strip()
    except Exception as e:
        logger.warning(f"Erro ao buscar token no banco: {e}")

    return None


def _call_telegram_api(token: str, method: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Realiza chamada HTTP POST síncrona para a API do Telegram."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        headers = {"Content-Type": "application/json"}
        data_bytes = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=35) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("ok"):
                return res_data.get("result")
            else:
                logger.error(f"Erro API Telegram ({method}): {res_data}")
                return None
    except Exception as e:
        logger.error(f"Exceção na chamada Telegram API ({method}): {e}")
        return None


def _send_telegram_document(token: str, chat_id: int, file_path: str, caption: str = "") -> bool:
    """Envia um arquivo físico (como o DAV em PDF) via multipart/form-data (sendDocument)."""
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado para envio: {file_path}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    
    body = []
    
    # Campo chat_id
    body.append(f"--{boundary}\r\n".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode("utf-8"))
    
    # Campo caption
    if caption:
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode("utf-8"))
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n'.encode("utf-8"))
    
    # Arquivo
    filename = os.path.basename(file_path)
    body.append(f"--{boundary}\r\n".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode("utf-8"))
    body.append(f'Content-Type: application/pdf\r\n\r\n'.encode("utf-8"))
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    body.append(file_bytes)
    body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    
    payload_bytes = b"".join(body)
    
    try:
        req = urllib.request.Request(url, data=payload_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return bool(res_data.get("ok"))
    except Exception as e:
        logger.error(f"Erro ao enviar documento PDF via Telegram: {e}")
        return False


def _download_voice_file(token: str, file_id: str, dest_path: str) -> bool:
    """Baixa o arquivo de áudio recebido no Telegram."""
    file_info = _call_telegram_api(token, "getFile", {"file_id": file_id})
    if not file_info or not file_info.get("file_path"):
        return False

    remote_path = file_info["file_path"]
    download_url = f"https://api.telegram.org/file/bot{token}/{remote_path}"

    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        urllib.request.urlretrieve(download_url, dest_path)
        return True
    except Exception as e:
        logger.error(f"Erro ao baixar áudio do Telegram: {e}")
        return False


def executar_job_expiracao_ttl():
    """Varre e marca rascunhos vencidos no banco como EXPIRADO (Job desacoplado)."""
    try:
        database.run_query("""
            UPDATE rascunhos_voz_telegram
            SET status = 'EXPIRADO'
            WHERE expira_em < CURRENT_TIMESTAMP
              AND status IN ('PENDENTE', 'PENDENTE_APROVACAO_SUPERVISOR')
        """)
    except Exception as e:
        logger.warning(f"Erro ao executar job de expiração TTL: {e}")


def _notificar_supervisores_alcada(token: str, draft: Dict[str, Any]):
    """Envia notificação para todos os administradores cadastrados para aprovação de alçada."""
    df_admins = database.fetch_all("""
        SELECT tua.chat_id, u.nome
        FROM usuarios u
        JOIN telegram_usuarios_autorizados tua ON tua.usuario_id = u.id
        WHERE u.nivel_permissao = 'ADMIN' AND u.status = 'ATIVO' AND tua.status = 'ATIVO'
    """)
    
    if df_admins.empty:
        # Fallback: envia para o chat_id master em empresa_config
        df_emp = database.fetch_all("SELECT telegram_chat_id FROM empresa_config LIMIT 1")
        if not df_emp.empty and df_emp.iloc[0]['telegram_chat_id']:
            df_admins = pd.DataFrame([{"chat_id": int(df_emp.iloc[0]['telegram_chat_id']), "nome": "Admin Master"}])

    rascunho_id = draft.get("rascunho_id")
    msg_admin = (
        f"🛡️ <b>SOLICITAÇÃO DE APROVAÇÃO DE ALÇADA</b>\n\n"
        f"<b>Solicitante:</b> {draft.get('usuario_nome')}\n"
        f"<b>Operação:</b> {draft.get('tipo_operacao')}\n"
        f"<b>Parceiro:</b> {draft.get('parceiro_nome')}\n"
        f"<b>Valor:</b> R$ {draft.get('valor_total'):,.2f} (Limite Operador: R$ {draft.get('limite_alcada'):,.2f})\n\n"
        f"<i>Aprovação necessária para efetivar a transação.</i>"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🔓 Aprovar e Faturar", "callback_data": f"CONFIRM:{rascunho_id}"},
                {"text": "❌ Rejeitar", "callback_data": f"CANCEL:{rascunho_id}"}
            ]
        ]
    }

    for _, row in df_admins.iterrows():
        admin_chat = int(row['chat_id'])
        _call_telegram_api(token, "sendMessage", {
            "chat_id": admin_chat,
            "text": msg_admin,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        })


def _send_draft_confirmation(token: str, chat_id: int, draft: Dict[str, Any]):
    """Envia o card de confirmação com os botões inline adequados."""
    rascunho_id = draft.get("rascunho_id")
    text = draft.get("texto_formatado", "")

    if draft.get("forma_pagamento_pendente"):
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "💵 Dinheiro (Caixa Físico)", "callback_data": f"FPAG:DINHEIRO:{rascunho_id}"},
                    {"text": "📱 Pix (Bradesco)", "callback_data": f"FPAG:PIX:{rascunho_id}"}
                ],
                [
                    {"text": "💳 Cartão (Indisponível)", "callback_data": f"FPAG:CARTAO:{rascunho_id}"},
                    {"text": "❌ Cancelar", "callback_data": f"CANCEL:{rascunho_id}"}
                ]
            ]
        }
    elif draft.get("requer_aprovacao_supervisor"):
        reply_markup = {
            "inline_keyboard": [
                [{"text": "⏳ Aguardando Aprovação do Gerente", "callback_data": f"INFO:{rascunho_id}"}],
                [{"text": "❌ Cancelar Solicitação", "callback_data": f"CANCEL:{rascunho_id}"}]
            ]
        }
        # Dispara notificação para gerência
        _notificar_supervisores_alcada(token, draft)

    elif draft.get("estoque_insuficiente_alerta"):
        reply_markup = {
            "inline_keyboard": [
                [{"text": "⚠️ Confirmar Mesmo com Estoque Negativo", "callback_data": f"CONFIRM:{rascunho_id}"}],
                [{"text": "❌ Cancelar Venda", "callback_data": f"CANCEL:{rascunho_id}"}]
            ]
        }
    elif draft.get("pronto_para_gravar"):
        btn_text = "⚡ Efetivar Venda Balcão & Gerar DAV" if draft.get("tipo_operacao") == "PDV_EXPRESS" else "✅ Confirmar Lançamento"
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": btn_text, "callback_data": f"CONFIRM:{rascunho_id}"},
                    {"text": "❌ Cancelar", "callback_data": f"CANCEL:{rascunho_id}"}
                ]
            ]
        }
    else:
        reply_markup = {
            "inline_keyboard": [
                [{"text": "❌ Descartar", "callback_data": f"CANCEL:{rascunho_id}"}]
            ]
        }

    _call_telegram_api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    })


def _handle_callback_query_sync(token: str, callback: Dict[str, Any]):
    """Processa o clique dos botões inline com trava atômica no banco."""
    callback_id = callback.get("id")
    data = callback.get("data", "")
    message = callback.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    msg_id = message.get("message_id")
    from_user = callback.get("from", {})

    _call_telegram_api(token, "answerCallbackQuery", {"callback_query_id": callback_id})

    if not data:
        return

    action, rascunho_id = data.split(":", 1) if ":" in data else (data, "")
    executador_id, executador_nome, _ = obter_limite_alcada_usuario(chat_id)

    if action == "FPAG":
        parts = rascunho_id.split(":", 1)
        if len(parts) == 2:
            fp_escolhida, rasc_uuid = parts[0], parts[1]
            if fp_escolhida == "CARTAO":
                _call_telegram_api(token, "answerCallbackQuery", {
                    "callback_query_id": callback_id,
                    "text": "🛑 A fábrica opera atualmente apenas com Dinheiro (Caixa) ou Pix (Bradesco).",
                    "show_alert": True
                })
                return
            
            from services.erp_voice_bridge import obter_conta_bancaria_destino
            c_id, c_nome, _ = obter_conta_bancaria_destino(fp_escolhida)

            df_r = database.fetch_all("SELECT payload_json FROM rascunhos_voz_telegram WHERE id = ?", (rasc_uuid,))
            if not df_r.empty:
                d_payload = json.loads(df_r.iloc[0]['payload_json'])
                d_payload["forma_pagamento_nome"] = fp_escolhida.title()
                d_payload["conta_bancaria_id"] = c_id
                d_payload["conta_bancaria_nome"] = c_nome
                d_payload["forma_pagamento_pendente"] = False
                d_payload["pronto_para_gravar"] = True

                # Re-formatar texto do resumo
                lines = d_payload.get("texto_formatado", "").split("\n")
                new_lines = []
                for ln in lines:
                    if "Forma de pagamento não informada" in ln:
                        continue
                    if "<b>Condição:</b>" in ln:
                        new_lines.append(f"<b>Condição:</b> {d_payload.get('condicao_pagamento')} ({fp_escolhida.title()} - {c_nome})")
                    else:
                        new_lines.append(ln)
                
                d_payload["texto_formatado"] = "\n".join(new_lines)

                database.run_query("UPDATE rascunhos_voz_telegram SET payload_json = ? WHERE id = ?", (json.dumps(d_payload, ensure_ascii=False), rasc_uuid))

                btn_text = "⚡ Efetivar Venda Balcão & Gerar DAV" if d_payload.get("tipo_operacao") == "PDV_EXPRESS" else "✅ Confirmar Lançamento"
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {"text": btn_text, "callback_data": f"CONFIRM:{rasc_uuid}"},
                            {"text": "❌ Cancelar", "callback_data": f"CANCEL:{rasc_uuid}"}
                        ]
                    ]
                }

                _call_telegram_api(token, "editMessageText", {
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": d_payload["texto_formatado"],
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup
                })

    elif action == "CONFIRM":
        sucesso, result_msg, pdf_path = efetivar_lancamento_rascunho(rascunho_id, executador_id)
        
        edited_text = f"<b>STATUS DO LANÇAMENTO:</b>\n{result_msg}"
        _call_telegram_api(token, "editMessageText", {
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": edited_text,
            "parse_mode": "HTML"
        })

        # Se houver PDF do DAV gerado, envia anexado via sendDocument
        if sucesso and pdf_path and os.path.exists(pdf_path):
            _send_telegram_document(token, chat_id, pdf_path, caption="📄 <b>Documento Auxiliar de Venda (DAV) impresso em PDF</b>")
            try:
                os.remove(pdf_path)
            except Exception:
                pass

    elif action == "CANCEL":
        database.run_query("UPDATE rascunhos_voz_telegram SET status = 'CANCELADO' WHERE id = ?", (rascunho_id,))
        _call_telegram_api(token, "editMessageText", {
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": "❌ <b>Lançamento cancelado pelo usuário.</b>",
            "parse_mode": "HTML"
        })


async def process_voice_message_async(token: str, chat_id: int, voice_obj: Dict[str, Any], nlu_service: VoiceNLUService):
    """Processa a mensagem de voz recebida isolando I/O bloqueante via asyncio.to_thread."""
    file_id = voice_obj["file_id"]
    temp_path = os.path.join("scratch", "temp_voice", f"voice_{uuid.uuid4().hex[:8]}.ogg")

    # Download do áudio em thread
    download_ok = await asyncio.to_thread(_download_voice_file, token, file_id, temp_path)
    if not download_ok:
        _call_telegram_api(token, "sendMessage", {"chat_id": chat_id, "text": "❌ Falha ao baixar o arquivo de áudio."})
        return

    try:
        # NLU Gemini em thread
        cmd_schema = await asyncio.to_thread(nlu_service.process_voice_audio, temp_path)
        
        # Preparação do rascunho em thread
        draft = await asyncio.to_thread(preparar_resumo_lancamento, cmd_schema, chat_id)
        
        # Envio de resposta no Telegram
        await asyncio.to_thread(_send_draft_confirmation, token, chat_id, draft)

    except Exception as err:
        logger.error(f"Erro ao processar voz: {err}")
        _call_telegram_api(token, "sendMessage", {
            "chat_id": chat_id,
            "text": f"⚠️ Não foi possível interpretar o áudio: {str(err)}"
        })
    finally:
        # Expurgo local do áudio temporário
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


async def main_async_loop(poll_interval: float = 2.0):
    """Loop principal de Long Polling em Event Loop assíncrono."""
    token = _get_bot_token()
    if not token:
        logger.error("Telegram Token não encontrado. Abortando.")
        return

    logger.info("🤖 Conector por Voz ERP (v5) iniciado com sucesso. Aguardando mensagens...")

    # Inicializar Scheduler de Expiração TTL em background se disponível
    if APSCHEDULER_AVAILABLE:
        scheduler = BackgroundScheduler()
        scheduler.add_job(executar_job_expiracao_ttl, 'interval', minutes=15)
        scheduler.start()

    nlu_service = VoiceNLUService()
    offset = 0

    while True:
        try:
            payload = {"offset": offset, "timeout": 20}
            updates = await asyncio.to_thread(_call_telegram_api, token, "getUpdates", payload)

            if updates:
                for up in updates:
                    offset = up["update_id"] + 1

                    # 1. Tratar Botões Inline
                    if "callback_query" in up:
                        await asyncio.to_thread(_handle_callback_query_sync, token, up["callback_query"])
                        continue

                    # 2. Tratar Mensagens de Voz
                    msg = up.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    voice = msg.get("voice") or msg.get("audio")

                    if voice and chat_id:
                        asyncio.create_task(process_voice_message_async(token, chat_id, voice, nlu_service))

            await asyncio.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Encerrando bot...")
            break
        except Exception as loop_err:
            logger.error(f"Erro no loop assíncrono: {loop_err}")
            await asyncio.sleep(5.0)


if __name__ == "__main__":
    asyncio.run(main_async_loop())
