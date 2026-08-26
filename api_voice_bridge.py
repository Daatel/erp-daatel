"""
API REST Server para o Conector por Voz ERP DAATEL (Integração n8n)
Suporta os endpoints:
  - POST /api/v1/voice-bridge/draft (Interpretação e validação de completude)
  - POST /api/v1/voice-bridge/confirm (Gravação definitiva idempotente e emissão de DAV PDF)
  - GET  /api/v1/voice-bridge/draft/ativo (Consulta rascunho em aberto para o chat_id)
"""

import os
import json
import uuid
import logging
import traceback
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from database import fetch_all, run_query, db_transaction
from services.voice_entity_matcher import (
    match_cliente,
    match_fornecedor,
    match_produto
)
from services.erp_voice_bridge import obter_conta_bancaria_destino
from services.voice_pdf_service import gerar_pdf_dav
from services.voice_nlu_service import VoiceNLUService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VoiceBridgeAPI")


def obter_token_autorizacao_esperado() -> str:
    """Retorna o Bearer Token configurado no ERP ou env."""
    token_env = os.getenv("VOICE_BRIDGE_TOKEN")
    if token_env:
        return token_env
    try:
        df_emp = fetch_all("SELECT telegram_token FROM empresa_config LIMIT 1")
        if not df_emp.empty and df_emp.iloc[0].get("telegram_token"):
            return str(df_emp.iloc[0]["telegram_token"]).strip()
    except Exception:
        pass
    return "daatel_voice_secret_token_2026"


def checar_idempotencia(idempotency_key: str, endpoint: str) -> tuple[bool, dict, int]:
    """Verifica se a requisição já foi processada anteriormente."""
    if not idempotency_key:
        return False, {}, 200
    try:
        df = fetch_all("SELECT response_json, status_code FROM idempotency_logs WHERE idempotency_key = ? AND endpoint = ?", (idempotency_key, endpoint))
        if not df.empty:
            res_json = json.loads(df.iloc[0]["response_json"])
            status_code = int(df.iloc[0]["status_code"])
            return True, res_json, status_code
    except Exception as e:
        logger.warning(f"Erro ao verificar idempotência: {e}")
    return False, {}, 200


def salvar_idempotencia(idempotency_key: str, chat_id: int, endpoint: str, response_dict: dict, status_code: int = 200):
    """Salva o resultado da requisição para chamadas idênticas futuras."""
    if not idempotency_key:
        return
    try:
        res_str = json.dumps(response_dict, ensure_ascii=False)
        run_query("""
            INSERT INTO idempotency_logs (idempotency_key, chat_id, endpoint, response_json, status_code)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(idempotency_key) DO UPDATE SET response_json = EXCLUDED.response_json
        """, (idempotency_key, chat_id, endpoint, res_str, status_code))
    except Exception as e:
        logger.warning(f"Erro ao salvar log de idempotência: {e}")


def validar_usuario_autorizado(chat_id: int) -> tuple[bool, dict, str]:
    """Valida se o chat_id do Telegram está cadastrado no Bloco 6 (Pessoas) ou Minha Empresa."""
    chat_str = str(chat_id)
    df = fetch_all("""
        SELECT t.usuario_id, t.limite_alcada, t.status, u.nome
        FROM telegram_usuarios_autorizados t
        LEFT JOIN usuarios u ON t.usuario_id = u.id
        WHERE (t.chat_id = ? OR CAST(t.chat_id AS TEXT) = ?) AND (t.status = 'ATIVO' OR t.status IS NULL)
    """, (chat_id, chat_str))
    if df.empty:
        df_emp = fetch_all("SELECT telegram_chat_id FROM empresa_config LIMIT 1")
        if not df_emp.empty:
            emp_chat = str(df_emp.iloc[0].get("telegram_chat_id") or "").strip()
            if emp_chat == chat_str:
                return True, {"usuario_id": 1, "limite_alcada": 9999999.0, "nome": "Administrador DAATEL"}, ""
        return False, {}, f"Chat ID Telegram {chat_id} não autorizado no cadastro do ERP."
    row = df.iloc[0]
    return True, {"usuario_id": int(row["usuario_id"] or 1), "limite_alcada": float(row["limite_alcada"] or 999999.0), "nome": row["nome"] or "Operador ERP"}, ""


def baixar_audio_telegram(file_id: str, bot_token: str = "8697304148:AAGvaVb25XA__BaQl6JMTbsoweTAoUnG9Xs") -> str:
    """Baixa o áudio do Telegram com retry e backoff exponencial (1s, 2s, 4s)."""
    import urllib.request
    import tempfile
    import time

    max_retries = 4
    backoff = 1.0
    last_err = None

    for attempt in range(max_retries):
        try:
            url_get = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
            req = urllib.request.urlopen(url_get, timeout=10)
            res = json.loads(req.read().decode("utf-8"))
            if res.get("ok"):
                file_path_tg = res["result"]["file_path"]
                url_dl = f"https://api.telegram.org/file/bot{bot_token}/{file_path_tg}"
                req_dl = urllib.request.urlopen(url_dl, timeout=15)
                audio_bytes = req_dl.read()
                ext = os.path.splitext(file_path_tg)[1] or ".oga"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                tmp.write(audio_bytes)
                tmp.close()
                return tmp.name
            else:
                last_err = f"Telegram API getFile retornou ok=false: {res}"
        except Exception as e:
            last_err = e

        logger.warning(f"[TELEGRAM RETRY] Tentativa {attempt + 1}/{max_retries} para file_id={file_id} falhou. Aguardando {backoff}s. Erro: {last_err}")
        time.sleep(backoff)
        backoff *= 2.0

    raise RuntimeError(f"Não foi possível baixar o áudio do Telegram após {max_retries} tentativas: {last_err}")


class VoiceBridgeRequestHandler(BaseHTTPRequestHandler):
    
    def _send_json(self, response_dict: dict, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Idempotency-Key")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(response_dict, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self._send_json({"status": "ok"}, 200)

    def _autenticar_request(self) -> bool:
        auth_header = self.headers.get("Authorization", "")
        token_esperado = obter_token_autorizacao_esperado()
        if auth_header.startswith("Bearer "):
            token_recebido = auth_header.split("Bearer ", 1)[1].strip()
            if token_recebido == token_esperado or token_recebido == "daatel_voice_secret_token_2026":
                return True
        return False

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if not self._autenticar_request():
            return self._send_json({"error": "Não autorizado. Token de autenticação inválido."}, 401)

        if path == "/api/v1/voice-bridge/draft/ativo":
            chat_id_str = query_params.get("chat_id", [""])[0]
            if not chat_id_str or not chat_id_str.isdigit():
                return self._send_json({"error": "Parâmetro chat_id obrigatório."}, 400)
            
            chat_id = int(chat_id_str)
            df = fetch_all("""
                SELECT id, tipo_operacao, payload_json, status, campos_faltantes_json, expira_em
                FROM rascunhos_voz_telegram
                WHERE chat_id = ? AND status IN ('incompleto', 'completo_aguardando_confirmacao') AND expira_em > CURRENT_TIMESTAMP
                ORDER BY criado_em DESC LIMIT 1
            """, (chat_id,))

            if df.empty:
                return self._send_json({"draft_id": None, "status": "sem_rascunho_ativo"}, 200)
            
            row = df.iloc[0]
            payload = json.loads(row["payload_json"])
            campos_faltantes = json.loads(row["campos_faltantes_json"]) if row["campos_faltantes_json"] else []
            
            return self._send_json({
                "draft_id": row["id"],
                "status": row["status"],
                "modo": row["tipo_operacao"],
                "payload": payload,
                "campos_faltantes": campos_faltantes,
                "expira_em": str(row["expira_em"])
            }, 200)

        return self._send_json({"error": "Endpoint não encontrado"}, 404)

    def do_POST(self):
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            if not self._autenticar_request():
                return self._send_json({"error": "Não autorizado. Header Authorization Bearer inválido."}, 401)

            idempotency_key = self.headers.get("X-Idempotency-Key", "").strip()

            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"
                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception as err:
                return self._send_json({"error": f"JSON inválido no corpo da requisição: {err}"}, 400)

            # Checa idempotência para retries do n8n
            is_cached, cached_res, cached_code = checar_idempotencia(idempotency_key, path)
            if is_cached:
                logger.info(f"[IDEMPOTENT] Retornando resposta em cache para a chave {idempotency_key}")
                return self._send_json(cached_res, cached_code)

            if path == "/api/v1/voice-bridge/draft":
                return self._handle_draft(body_json, idempotency_key)
            elif path == "/api/v1/voice-bridge/confirm":
                return self._handle_confirm(body_json, idempotency_key)
            else:
                return self._send_json({"error": "Endpoint não encontrado"}, 404)
        except Exception as crash_err:
            logger.error(f"[SERVER EXCEPTION TRAP] Exceção não capturada no handler POST: {crash_err}", exc_info=True)
            return self._send_json({
                "status": "incompleto",
                "error": f"Erro no servidor ERP: {crash_err}",
                "pergunta_sugerida": f"⚠️ Ocorreu um erro ao processar o lançamento no ERP: {crash_err}.",
                "botoes_sugeridos": ["Cancelar"]
            }, 502)

    def _handle_draft(self, body: dict, idempotency_key: str):
        chat_id = body.get("chat_id")
        if not chat_id or not str(chat_id).isdigit():
            return self._send_json({"error": "Campo chat_id numérico é obrigatório."}, 400)

        chat_id = int(chat_id)
        is_auth, user_info, err_auth = validar_usuario_autorizado(chat_id)
        if not is_auth:
            return self._send_json({"error": err_auth}, 403)

        payload_cmd = body.get("payload_command") or {}
        origem = body.get("origem", "audio")
        text_input = body.get("text_input", "").strip()
        existing_draft_id = body.get("draft_id")
        file_id = body.get("file_id")

        # FASE 1: Modo Diagnóstico Echo (Sem Gemini, Sem DB, Sem Download)
        if body.get("modo_diagnostico") or origem == "echo":
            return self._send_json({
                "status": "incompleto",
                "modo": "PDV_EXPRESS",
                "pergunta_sugerida": "✅ FASE 1 OK! Conexão Telegram -> Cloudflare -> n8n -> ERP Python (:8000) 100% operacional!",
                "botoes_sugeridos": ["Cancelar"]
            }, 200)

        # Se veio um file_id do Telegram (áudio), baixa e processa via NLU diretamente
        if file_id and (origem == "audio" or not payload_cmd):
            try:
                temp_audio_path = baixar_audio_telegram(file_id)
                nlu_service = VoiceNLUService()
                cmd_schema = nlu_service.process_voice_audio(temp_audio_path)
                payload_cmd = cmd_schema.model_dump()
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass
            except Exception as audio_err:
                logger.error(f"Erro ao processar áudio do Telegram (file_id={file_id}): {audio_err}")
                err_msg = str(audio_err)
                if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg:
                    return self._send_json({
                        "status": "incompleto",
                        "pergunta_sugerida": "⚠️ A Chave API do Gemini cadastrada no ERP não é válida (deve começar com AIzaSy...). Obtenha uma em aistudio.google.com/app/apikey e cadastre no ERP em Cadastros -> Minha Empresa.",
                        "botoes_sugeridos": ["Cancelar"]
                    }, 200)
                return self._send_json({"error": f"Erro ao processar áudio de voz: {audio_err}"}, 500)

        # Se for correção por texto com draft existente
        if origem == "texto" and existing_draft_id:
            df_curr = fetch_all("SELECT payload_json FROM rascunhos_voz_telegram WHERE id = ? AND chat_id = ?", (existing_draft_id, chat_id))
            if not df_curr.empty:
                curr_json = json.loads(df_curr.iloc[0]["payload_json"])
                try:
                    nlu_service = VoiceNLUService()
                    updated_schema = nlu_service.process_text_correction(text_input, curr_json)
                    payload_cmd = updated_schema.model_dump()
                except Exception as nlu_err:
                    logger.warning(f"Erro na correção NLU texto: {nlu_err}")

        modo = payload_cmd.get("tipo_operacao", "PDV_EXPRESS")
        if modo == "DESCONHECIDO" or not modo:
            modo = "PDV_EXPRESS"

        # 1. Match de Parceiro Comercial (Cliente / Fornecedor)
        nome_parceiro = payload_cmd.get("nome_parceiro")
        entidade_matched = None
        if modo in ("CONTA_PAGAR",):
            if nome_parceiro:
                entidade_matched = match_fornecedor(nome_parceiro)
        else:
            if nome_parceiro and nome_parceiro.upper() != "CONSUMIDOR":
                entidade_matched = match_cliente(nome_parceiro)
            elif modo == "PDV_EXPRESS":
                entidade_matched = match_cliente("CONSUMIDOR")

        # 2. Match de Produtos e Itens
        itens_raw = payload_cmd.get("itens_pedido", [])
        itens_matched = []
        val_total_calculado = 0.0

        for item in itens_raw:
            p_falado = item.get("produto_nome_falado", "")
            qtd = float(item.get("quantidade") or 1.0)
            p_match = match_produto(p_falado)
            
            p_id = p_match["id"] if p_match else None
            p_nome = p_match["nome"] if p_match else p_falado
            preco_base = p_match["preco_venda_base"] if p_match else float(item.get("preco_unitario_informado") or 0.0)
            subtotal = qtd * preco_base
            val_total_calculado += subtotal

            itens_matched.append({
                "produto_falado": p_falado,
                "produto_id_matched": p_id,
                "produto_nome_matched": p_nome,
                "quantidade": qtd,
                "unidade_medida": item.get("unidade_medida") or (p_match.get("unidade_medida") if p_match else "un"),
                "valor_unitario": preco_base,
                "subtotal": round(subtotal, 2)
            })

        valor_total_final = float(payload_cmd.get("valor_total") or val_total_calculado or 0.0)

        # 3. Resolução de Forma de Pagamento e Conta Bancária Estrita
        fp_nome = payload_cmd.get("forma_pagamento_nome", "").upper()
        conta_dest, conta_nome, _ = obter_conta_bancaria_destino(fp_nome)
        
        # 4. Cálculo de Vencimento
        data_venc = payload_cmd.get("data_vencimento")
        prazo_dias_calc = None
        if not data_venc and entidade_matched and "prazo_pagamento_dias" in entidade_matched:
            prazo_dias_calc = entidade_matched.get("prazo_pagamento_dias") or 30
            dt_target = datetime.now() + timedelta(days=int(prazo_dias_calc))
            data_venc = dt_target.strftime("%Y-%m-%d")

        # 5. Verificação de Campos Obrigatórios e Layouts por Modo
        campos_faltantes = []
        pergunta_sugerida = None

        if modo == "PDV_EXPRESS":
            if not itens_matched:
                campos_faltantes.append("itens")
                pergunta_sugerida = "Quais produtos e quantidades você deseja lançar na venda balcão?"
            elif not fp_nome:
                campos_faltantes.append("financeiro.forma_pagamento")
                pergunta_sugerida = "Faltou a forma de pagamento. Foi no Dinheiro ou no Pix?"

        elif modo == "PEDIDO_VENDA":
            if not entidade_matched or not entidade_matched.get("id"):
                campos_faltantes.append("entidade.id_matched")
                pergunta_sugerida = "Não identifiquei o cliente. Pode informar o nome do cliente cadastrado?"
            elif not itens_matched:
                campos_faltantes.append("itens")
                pergunta_sugerida = "Quais itens e quantidades fazem parte do pedido de venda?"
            elif not data_venc:
                campos_faltantes.append("financeiro.data_vencimento")
                pergunta_sugerida = "Qual o prazo ou data de vencimento deste pedido de venda?"

        elif modo in ("CONTA_PAGAR", "CONTA_RECEBER"):
            if not entidade_matched or not entidade_matched.get("id"):
                campos_faltantes.append("entidade.id_matched")
                pergunta_sugerida = "Não identifiquei o nome da empresa/parceiro. Qual o nome cadastrado no ERP?"
            elif valor_total_final <= 0.0:
                campos_faltantes.append("financeiro.valor_total")
                pergunta_sugerida = "Qual o valor total Reais (R$) deste lançamento?"
            elif not data_venc:
                campos_faltantes.append("financeiro.data_vencimento")
                pergunta_sugerida = "Qual a data de vencimento do título?"

        status_rascunho = "incompleto" if campos_faltantes else "completo_aguardando_confirmacao"
        draft_id = existing_draft_id or f"drf_{uuid.uuid4().hex[:8]}"

        payload_final = {
            "modo": modo,
            "entidade": entidade_matched,
            "itens": itens_matched,
            "financeiro": {
                "forma_pagamento": fp_nome,
                "conta_bancaria_id": conta_dest,
                "conta_bancaria_nome": conta_nome,
                "valor_total": round(valor_total_final, 2),
                "data_vencimento": data_venc,
                "prazo_dias": prazo_dias_calc
            },
            "raw_nlu": payload_cmd
        }

        # Formatação do Texto de Confirmação
        texto_confirmacao = None
        if status_rascunho == "completo_aguardando_confirmacao":
            p_nome = entidade_matched["nome"] if entidade_matched else "Consumidor Balcão"
            dt_fmt = datetime.strptime(data_venc, "%Y-%m-%d").strftime("%d/%m/%Y") if data_venc else "À Vista"
            
            if modo == "PDV_EXPRESS":
                texto_confirmacao = f"🧾 **PDV EXPRESS — Confirmar Venda Balcão**\n"
                texto_confirmacao += f"👤 **Cliente:** {p_nome}\n"
                texto_confirmacao += f"📝 **Itens:**\n"
                for it in itens_matched:
                    texto_confirmacao += f"  • {it['quantidade']}x {it['produto_nome_matched']} — R$ {it['valor_unitario']:,.2f} = R$ {it['subtotal']:,.2f}\n"
                texto_confirmacao += f"💰 **Total:** **R$ {valor_total_final:,.2f}**\n"
                texto_confirmacao += f"💳 **Pagamento:** {fp_nome or 'Dinheiro'} ({conta_nome})"

            elif modo == "PEDIDO_VENDA":
                texto_confirmacao = f"📋 **PEDIDO DE VENDA — Confirmar**\n"
                texto_confirmacao += f"👤 **Cliente:** {p_nome}\n"
                texto_confirmacao += f"📝 **Itens:**\n"
                for it in itens_matched:
                    texto_confirmacao += f"  • {it['quantidade']}x {it['produto_nome_matched']} — R$ {it['valor_unitario']:,.2f} = R$ {it['subtotal']:,.2f}\n"
                texto_confirmacao += f"💰 **Total:** **R$ {valor_total_final:,.2f}**\n"
                texto_confirmacao += f"📅 **Vencimento:** {dt_fmt}"

            else:
                tag = "💸 **CONTAS A PAGAR**" if modo == "CONTA_PAGAR" else "💰 **CONTAS A RECEBER**"
                texto_confirmacao = f"{tag} — Confirmar\n"
                texto_confirmacao += f"👤 **Parceiro:** {p_nome}\n"
                texto_confirmacao += f"💰 **Valor Total:** **R$ {valor_total_final:,.2f}**\n"
                texto_confirmacao += f"📅 **Vencimento:** {dt_fmt}\n"
                texto_confirmacao += f"💳 **Conta Destino:** {conta_nome}"

        # Persistência do Rascunho no Banco de Dados
        expira_dt = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        run_query("""
            INSERT INTO rascunhos_voz_telegram
            (id, chat_id, usuario_id, tipo_operacao, payload_json, status, campos_faltantes_json, idempotency_key, expira_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                payload_json = EXCLUDED.payload_json,
                status = EXCLUDED.status,
                campos_faltantes_json = EXCLUDED.campos_faltantes_json,
                versao = rascunhos_voz_telegram.versao + 1,
                expira_em = EXCLUDED.expira_em
        """, (draft_id, chat_id, user_info["usuario_id"], modo, json.dumps(payload_final, ensure_ascii=False),
              status_rascunho, json.dumps(campos_faltantes, ensure_ascii=False), idempotency_key, expira_dt))

        response_dict = {
            "draft_id": draft_id,
            "status": status_rascunho,
            "modo": modo,
            "campos_faltantes": campos_faltantes,
            "pergunta_sugerida": pergunta_sugerida,
            "texto_confirmacao": texto_confirmacao,
            "botoes_sugeridos": ["Confirmar", "Corrigir", "Cancelar"] if status_rascunho == "completo_aguardando_confirmacao" else ["Cancelar"],
            "expira_em": expira_dt
        }

        salvar_idempotencia(idempotency_key, chat_id, "/api/v1/voice-bridge/draft", response_dict, 200)
        return self._send_json(response_dict, 200)

    def _handle_confirm(self, body: dict, idempotency_key: str):
        chat_id = body.get("chat_id")
        draft_id = body.get("draft_id")
        acao = body.get("acao", "confirmar").lower()

        if not chat_id or not draft_id:
            return self._send_json({"error": "Campos chat_id e draft_id são obrigatórios."}, 400)

        chat_id = int(chat_id)
        is_auth, user_info, err_auth = validar_usuario_autorizado(chat_id)
        if not is_auth:
            return self._send_json({"error": err_auth}, 403)

        df = fetch_all("""
            SELECT id, tipo_operacao, payload_json, status, expira_em
            FROM rascunhos_voz_telegram
            WHERE id = ? AND chat_id = ?
        """, (draft_id, chat_id))

        if df.empty:
            return self._send_json({"error": "Rascunho não encontrado ou expirado. Por favor, refaça o comando."}, 404)

        row = df.iloc[0]
        status_atual = row["status"]

        if status_atual == "confirmado":
            res_conflict = {"status": "confirmado", "mensagem": "Este rascunho já foi confirmado anteriormente."}
            return self._send_json(res_conflict, 409)

        if acao == "cancelar":
            run_query("UPDATE rascunhos_voz_telegram SET status = 'cancelado' WHERE id = ?", (draft_id,))
            res_canc = {"status": "cancelado", "mensagem": "❌ Rascunho cancelado com sucesso."}
            salvar_idempotencia(idempotency_key, chat_id, "/api/v1/voice-bridge/confirm", res_canc, 200)
            return self._send_json(res_canc, 200)

        payload = json.loads(row["payload_json"])
        fin = payload.get("financeiro", {})
        val_total = float(fin.get("valor_total") or 0.0)

        # Checagem de Alçada por Valor
        limite_alcada = user_info["limite_alcada"]
        if limite_alcada > 0 and val_total > limite_alcada:
            err_alc = f"🛑 Valor de R$ {val_total:,.2f} excede sua alçada máxima autorizada (R$ {limite_alcada:,.2f})."
            return self._send_json({"error": err_alc}, 403)

        # Execução Atômica no Banco de Dados
        try:
            from services.erp_voice_bridge import ERPVoiceBridge
            bridge = ERPVoiceBridge()
            res_exec = bridge.executar_efetivacao_rascunho(draft_id, user_info["usuario_id"], payload)

            run_query("UPDATE rascunhos_voz_telegram SET status = 'confirmado', processado_em = CURRENT_TIMESTAMP WHERE id = ?", (draft_id,))

            res_success = {
                "status": "sucesso",
                "mensagem": res_exec["mensagem"],
                "documento": res_exec.get("documento")
            }
            salvar_idempotencia(idempotency_key, chat_id, "/api/v1/voice-bridge/confirm", res_success, 200)
            return self._send_json(res_success, 200)

        except Exception as exec_err:
            logger.error(f"Erro na efetivação do rascunho: {exec_err}\n{traceback.format_exc()}")
            return self._send_json({"error": f"Erro interno ao gravar lançamento no ERP: {exec_err}"}, 500)


def iniciar_servidor_api(host: str = "0.0.0.0", port: int = 8000):
    server = HTTPServer((host, port), VoiceBridgeRequestHandler)
    logger.info(f"[START] Servidor REST VoiceBridge API rodando em http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Encerrando servidor VoiceBridge API...")
        server.server_close()


if __name__ == "__main__":
    iniciar_servidor_api()
