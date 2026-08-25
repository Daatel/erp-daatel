"""
Ponte de integração entre a NLU de Voz e o banco de dados do ERP DAATEL (`database.py`).
Gerencia a busca de rascunhos, validação de alçadas, pré-check de estoque e execução atômica de lançamentos.
"""

import json
import uuid
import logging
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, date, timedelta

import database
from services.voice_nlu_service import VoiceCommandSchema
from services.voice_entity_matcher import (
    buscar_cliente_fuzzy,
    buscar_fornecedor_fuzzy,
    buscar_produto_fuzzy,
    buscar_plano_contas_fuzzy
)
from services.voice_pdf_service import gerar_pdf_dav

logger = logging.getLogger("ERPVoiceBridge")


def obter_limite_alcada_usuario(chat_id: int) -> Tuple[int, str, float]:
    """
    Retorna (usuario_id, usuario_nome, limite_alcada) do operador do Telegram.
    Se não cadastrado, retorna (0, 'Desconhecido', 0.0).
    """
    df = database.fetch_all("""
        SELECT tua.usuario_id, tua.limite_alcada, u.nome
        FROM telegram_usuarios_autorizados tua
        JOIN usuarios u ON tua.usuario_id = u.id
        WHERE tua.chat_id = ? AND tua.status = 'ATIVO' AND u.status = 'ATIVO'
    """, (chat_id,))
    
    if not df.empty:
        r = df.iloc[0]
        return int(r['usuario_id']), str(r['nome']), float(r['limite_alcada'] or 0.0)
    
    # Check fallback: Se o chat_id for do admin principal da empresa_config
    df_emp = database.fetch_all("SELECT telegram_chat_id FROM empresa_config LIMIT 1")
    if not df_emp.empty and str(df_emp.iloc[0]['telegram_chat_id']).strip() == str(chat_id).strip():
        # Admin master
        df_admin = database.fetch_all("SELECT id, nome FROM usuarios WHERE nivel_permissao = 'ADMIN' LIMIT 1")
        if not df_admin.empty:
            return int(df_admin.iloc[0]['id']), str(df_admin.iloc[0]['nome']), 999999.0
            
    return 0, "Usuário Não Autorizado", 0.0


def consultar_saldo_estoque_produto(produto_id: int) -> float:
    """Calcula o saldo de estoque disponível para o produto no ERP."""
    df_mov = database.fetch_all("""
        SELECT COALESCE(SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END), 0.0) as saldo
        FROM estoque_movimentos
        WHERE produto_id = ?
    """, (produto_id,))
    
    if not df_mov.empty:
        return float(df_mov.iloc[0]['saldo'] or 0.0)
    return 0.0


def obter_conta_bancaria_destino(forma_pagto: Optional[str]) -> Tuple[Optional[int], str, Optional[str]]:
    """
    Retorna (conta_bancaria_id, nome_conta_formatado, erro_alerta).
    - Dinheiro: Vincula à conta 'Caixa Físico' / 'Espécie'.
    - Pix: Vincula obrigatoriamente ao banco 'Bradesco'.
    - Cartão: Retorna bloqueio informativo (desabilitado).
    - Omitido: Exige seleção explícita.
    """
    if not forma_pagto:
        return None, "Não informado", "NAO_INFORMADO"

    fp_clean = str(forma_pagto).strip().upper()

    if "CARTAO" in fp_clean or "CREDITO" in fp_clean or "DEBITO" in fp_clean:
        return None, "Cartão (Indisponível)", "CARTAO_DESABILITADO"

    df_contas = database.fetch_all("SELECT * FROM contas_bancarias WHERE status = 'ATIVO'")

    if "DINHEIRO" in fp_clean or "ESPECIE" in fp_clean or "CAIXA" in fp_clean:
        if not df_contas.empty:
            for _, r in df_contas.iterrows():
                nm = f"{r.get('banco', '')} {r.get('apelido', '')} {r.get('tipo_conta', '')}".upper()
                if "CAIXA" in nm or "ESPECIE" in nm or "DINHEIRO" in nm:
                    return int(r['id']), f"Caixa Físico (#{r['id']})", None
            # Fallback para a primeira conta se não achar nome 'caixa'
            r0 = df_contas.iloc[0]
            return int(r0['id']), f"Caixa Físico ({r0.get('banco', 'Geral')})", None
        return 1, "Caixa Físico (#1)", None

    if "PIX" in fp_clean or "BRADESCO" in fp_clean:
        if not df_contas.empty:
            for _, r in df_contas.iterrows():
                nm = f"{r.get('banco', '')} {r.get('apelido', '')} {r.get('tipo_conta', '')}".upper()
                if "BRADESCO" in nm or "PIX" in nm:
                    return int(r['id']), f"Pix Bradesco (#{r['id']})", None
            # Fallback primeira conta
            r0 = df_contas.iloc[0]
            return int(r0['id']), f"Pix Bradesco ({r0.get('banco', 'Bradesco')})", None
        return 1, "Pix Bradesco (#1)", None

    return None, "Não informado", "NAO_INFORMADO"


def preparar_resumo_lancamento(cmd: VoiceCommandSchema, chat_id: int) -> Dict[str, Any]:
    """
    Analisa o comando NLU, busca correspondências no banco de dados e prepara
    o rascunho com salvamento atômico na tabela `rascunhos_voz_telegram`.
    """
    usuario_id, usuario_nome, limite_alcada = obter_limite_alcada_usuario(chat_id)
    
    data_hoje = date.today().strftime("%Y-%m-%d")
    data_venc = cmd.data_vencimento
    
    rascunho_id = str(uuid.uuid4())[:8]

    # Resolução de Meio de Pagamento e Conta Destino
    conta_id, conta_nome, err_fp = obter_conta_bancaria_destino(cmd.forma_pagamento_nome)
    
    match_info = {
        "rascunho_id": rascunho_id,
        "chat_id": chat_id,
        "usuario_id": usuario_id,
        "usuario_nome": usuario_nome,
        "limite_alcada": limite_alcada,
        "tipo_operacao": cmd.tipo_operacao,
        "valor_total": cmd.valor_total or 0.0,
        "data_vencimento": data_venc,
        "condicao_pagamento": cmd.condicao_pagamento or "A_VISTA",
        "forma_pagamento_nome": cmd.forma_pagamento_nome or None,
        "conta_bancaria_id": conta_id,
        "conta_bancaria_nome": conta_nome,
        "descricao": cmd.descricao_observacao or "Lançamento por voz via Telegram",
        "parceiro_id": None,
        "parceiro_nome": cmd.nome_parceiro or "Não informado",
        "plano_conta_id": None,
        "plano_conta_nome": cmd.categoria_plano_contas or "Não informado",
        "itens": [],
        "pronto_para_gravar": True,
        "forma_pagamento_pendente": False,
        "requer_aprovacao_supervisor": False,
        "estoque_insuficiente_alerta": False,
        "alertas": []
    }

    if cmd.tipo_operacao == "PDV_EXPRESS":
        if err_fp == "NAO_INFORMADO":
            match_info["forma_pagamento_pendente"] = True
            match_info["pronto_para_gravar"] = False
            match_info["alertas"].append("⚠️ **Forma de pagamento não informada no áudio.** Selecione a forma de pagamento abaixo para faturar:")
        elif err_fp == "CARTAO_DESABILITADO":
            match_info["pronto_para_gravar"] = False
            match_info["alertas"].append("🛑 **Cartão Indisponível:** A fábrica opera atualmente apenas com Dinheiro (Caixa) ou Pix (Bradesco).")

    if usuario_id == 0:
        match_info["alertas"].append("🛑 Usuário ou Chat ID não autorizado a operar no Telegram.")
        match_info["pronto_para_gravar"] = False

    # 1. Resolver Parceiro Comercial
    if cmd.tipo_operacao == "CONTA_PAGAR":
        df_forn = database.get_fornecedores_ativos_cached()
        if cmd.nome_parceiro:
            forn, score = buscar_fornecedor_fuzzy(cmd.nome_parceiro, df_forn)
            if forn:
                match_info["parceiro_id"] = int(forn["id"])
                match_info["parceiro_nome"] = f"{forn.get('nome')} (#{forn.get('id')})"
            else:
                match_info["alertas"].append(f"⚠️ Fornecedor '{cmd.nome_parceiro}' não cadastrado (Bloqueado sem parceiro).")
                match_info["pronto_para_gravar"] = False
        else:
            match_info["alertas"].append("⚠️ Fornecedor não informado para Conta a Pagar (Obrigatório).")
            match_info["pronto_para_gravar"] = False

    elif cmd.tipo_operacao in ["CONTA_RECEBER", "PEDIDO_VENDA"]:
        df_cli = database.get_clientes_ativos_cached()
        if cmd.nome_parceiro:
            cli, score = buscar_cliente_fuzzy(cmd.nome_parceiro, df_cli)
            if cli:
                match_info["parceiro_id"] = int(cli["id"])
                match_info["parceiro_nome"] = f"{cli.get('nome')} (#{cli.get('id')})"
            else:
                match_info["alertas"].append(f"⚠️ Cliente '{cmd.nome_parceiro}' não cadastrado.")
                match_info["pronto_para_gravar"] = False
        else:
            match_info["alertas"].append("⚠️ Cliente não informado (Obrigatório para esta operação).")
            match_info["pronto_para_gravar"] = False

    elif cmd.tipo_operacao == "PDV_EXPRESS":
        df_cli = database.get_clientes_ativos_cached()
        nome_busca = cmd.nome_parceiro or "CONSUMIDOR"
        cli, score = buscar_cliente_fuzzy(nome_busca, df_cli)
        if cli:
            match_info["parceiro_id"] = int(cli["id"])
            match_info["parceiro_nome"] = f"{cli.get('nome')} (#{cli.get('id')})"
        else:
            # Fallback para CONSUMIDOR ID #1
            df_cons = database.fetch_all("SELECT id, nome FROM clientes WHERE nome='CONSUMIDOR' LIMIT 1")
            if not df_cons.empty:
                match_info["parceiro_id"] = int(df_cons.iloc[0]['id'])
                match_info["parceiro_nome"] = "CONSUMIDOR (#1)"

        # Bloqueio H3: CONSUMIDOR a prazo
        if match_info["condicao_pagamento"] == "A_PRAZO" and "CONSUMIDOR" in match_info["parceiro_nome"].upper():
            match_info["alertas"].append("🛑 Bloqueio: Não é permitido venda a prazo para o cliente CONSUMIDOR genérico.")
            match_info["pronto_para_gravar"] = False

    # 2. Resolver Plano de Contas se informado
    if cmd.categoria_plano_contas:
        df_pc = database.fetch_all("SELECT id, categoria, descricao, codigo FROM planos_de_contas")
        pc, score_pc = buscar_plano_contas_fuzzy(cmd.categoria_plano_contas, df_pc)
        if pc:
            match_info["plano_conta_id"] = int(pc["id"])
            match_info["plano_conta_nome"] = str(pc.get("categoria") or pc.get("descricao"))

    # 3. Resolver Produtos e Pré-check de Estoque (PDV_EXPRESS / PEDIDO_VENDA)
    if cmd.tipo_operacao in ["PDV_EXPRESS", "PEDIDO_VENDA"]:
        df_prod = database.get_produtos_cached()
        valor_calculado = 0.0
        
        for item in cmd.itens_pedido:
            prod, score = buscar_produto_fuzzy(item.produto_nome_falado, df_prod)
            item_dict = {
                "produto_falado": item.produto_nome_falado,
                "produto_id": int(prod["id"]) if prod else None,
                "produto_nome": prod.get("nome") if prod else "Desconhecido",
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario_informado or (float(prod.get("preco_venda_base") or 0.0) if prod else 0.0),
            }
            item_dict["valor_item"] = item_dict["quantidade"] * item_dict["preco_unitario"]
            valor_calculado += item_dict["valor_item"]
            
            if prod and cmd.tipo_operacao == "PDV_EXPRESS":
                # Pré-check de estoque (Regra H4)
                saldo_disp = consultar_saldo_estoque_produto(int(prod["id"]))
                if item_dict["quantidade"] > saldo_disp:
                    match_info["estoque_insuficiente_alerta"] = True
                    match_info["alertas"].append(
                        f"⚠️ **Estoque Insuficiente:** Solicitado {item_dict['quantidade']:.1f}kg de {item_dict['produto_nome']}, "
                        f"mas há apenas {saldo_disp:.1f}kg em estoque. Confirmar gerará estoque negativo."
                    )

            if not prod:
                match_info["alertas"].append(f"⚠️ Produto '{item.produto_nome_falado}' não encontrado no cadastro.")
                match_info["pronto_para_gravar"] = False

            match_info["itens"].append(item_dict)

        if valor_calculado > 0 and (not cmd.valor_total or cmd.valor_total == 0):
            match_info["valor_total"] = valor_calculado

    # 4. Checagem de Data de Vencimento Obrigatória no Financeiro
    if cmd.tipo_operacao in ["CONTA_PAGAR", "CONTA_RECEBER"] and not match_info["data_vencimento"]:
        match_info["alertas"].append("⚠️ **Data de Vencimento não informada.** Por favor, informe a data de vencimento.")
        match_info["pronto_para_gravar"] = False

    # 5. Checagem de Alçada por Valor
    if match_info["valor_total"] > limite_alcada and limite_alcada > 0:
        match_info["requer_aprovacao_supervisor"] = True
        match_info["alertas"].append(
            f"🛡️ **Alçada Excedida:** Valor de R$ {match_info['valor_total']:,.2f} excede seu limite de alçada (R$ {limite_alcada:,.2f}). "
            f"O lançamento exigirá aprovação da gerência."
        )

    # 6. Salvar Rascunho no Banco de Dados (`rascunhos_voz_telegram`)
    expira_dt = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    status_rascunho = "PENDENTE_APROVACAO_SUPERVISOR" if match_info["requer_aprovacao_supervisor"] else "PENDENTE"
    
    database.run_query("""
        INSERT INTO rascunhos_voz_telegram (id, chat_id, usuario_id, tipo_operacao, payload_json, status, expira_em)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        rascunho_id,
        chat_id,
        usuario_id,
        cmd.tipo_operacao,
        json.dumps(match_info, ensure_ascii=False),
        status_rascunho,
        expira_dt
    ))

    # Log de Auditoria Inicial
    database.run_query("""
        INSERT INTO audit_log_voz (rascunho_id, usuario_id, chat_id, acao, tipo_operacao, valor_total, payload_json, status_execucao)
        VALUES (?, ?, ?, 'SUBMISSAO', ?, ?, ?, 'PENDENTE')
    """, (rascunho_id, usuario_id, chat_id, cmd.tipo_operacao, match_info["valor_total"], json.dumps(match_info, ensure_ascii=False)))

    database.registrar_log_acesso(usuario_id, usuario_nome, "", "SUBMISSAO_VOZ", f"Rascunho {rascunho_id} ({cmd.tipo_operacao})")

    # 7. Formatar Texto da Mensagem para o Telegram
    msg_lines = []
    if cmd.tipo_operacao == "PDV_EXPRESS":
        msg_lines.append("⚡ <b>Lançamento: PDV EXPRESS (Venda Balcão)</b>")
        msg_lines.append(f"<b>Cliente:</b> {match_info['parceiro_nome']}")
        msg_lines.append(f"<b>Condição:</b> {match_info['condicao_pagamento']} ({match_info['forma_pagamento_nome']})")
        msg_lines.append("<b>Itens do Balcão:</b>")
        for it in match_info["itens"]:
            msg_lines.append(f"  • {it['quantidade']:.1f}x {it['produto_nome']} @ R$ {it['preco_unitario']:,.2f} = R$ {it['valor_item']:,.2f}")
        msg_lines.append(f"💰 <b>TOTAL: R$ {match_info['valor_total']:,.2f}</b>")

    elif cmd.tipo_operacao == "PEDIDO_VENDA":
        msg_lines.append("🛒 <b>Lançamento: PEDIDO DE VENDA</b>")
        msg_lines.append(f"<b>Cliente:</b> {match_info['parceiro_nome']}")
        msg_lines.append("<b>Itens Solicitados:</b>")
        for it in match_info["itens"]:
            msg_lines.append(f"  • {it['quantidade']:.1f}x {it['produto_nome']} @ R$ {it['preco_unitario']:,.2f}")
        msg_lines.append(f"💰 <b>TOTAL ESTIMADO: R$ {match_info['valor_total']:,.2f}</b>")

    elif cmd.tipo_operacao == "CONTA_PAGAR":
        msg_lines.append("🔴 <b>Lançamento: CONTA A PAGAR</b>")
        msg_lines.append(f"<b>Fornecedor:</b> {match_info['parceiro_nome']}")
        msg_lines.append(f"<b>Valor:</b> R$ {match_info['valor_total']:,.2f}")
        msg_lines.append(f"<b>Vencimento:</b> {match_info['data_vencimento']}")
        msg_lines.append(f"<b>Descrição:</b> {match_info['descricao']}")

    elif cmd.tipo_operacao == "CONTA_RECEBER":
        msg_lines.append("🟢 <b>Lançamento: CONTA A RECEBER</b>")
        msg_lines.append(f"<b>Cliente:</b> {match_info['parceiro_nome']}")
        msg_lines.append(f"<b>Valor:</b> R$ {match_info['valor_total']:,.2f}")
        msg_lines.append(f"<b>Vencimento:</b> {match_info['data_vencimento']}")
        msg_lines.append(f"<b>Descrição:</b> {match_info['descricao']}")
    else:
        msg_lines.append("❓ <b>Comando não identificado com clareza.</b>")

    if match_info["alertas"]:
        msg_lines.append("\n" + "\n".join(match_info["alertas"]))

    match_info["texto_formatado"] = "\n".join(msg_lines)
    return match_info


def efetivar_lancamento_rascunho(rascunho_id: str, executado_por_usuario_id: int, forcar_estoque_negativo: bool = False) -> Tuple[bool, str, Optional[str]]:
    """
    Executa a trava atômica `UPDATE rascunhos_voz_telegram ... WHERE status IN ('PENDENTE', 'PENDENTE_APROVACAO_SUPERVISOR')`
    e efetiva a transação no banco de dados do ERP.
    """
    # 1. Recuperar payload do rascunho
    df_rasc = database.fetch_all("SELECT payload_json, status, usuario_id, chat_id FROM rascunhos_voz_telegram WHERE id = ?", (rascunho_id,))
    if df_rasc.empty:
        return False, "❌ Rascunho de lançamento não encontrado.", None

    row = df_rasc.iloc[0]
    draft = json.loads(row['payload_json'])
    status_atual = str(row['status'])
    solicitante_id = int(row['usuario_id'])
    chat_id = int(row['chat_id'])

    if status_atual not in ["PENDENTE", "PENDENTE_APROVACAO_SUPERVISOR"]:
        return False, f"⚠️ Este lançamento já foi processado ou expirou (Status: {status_atual}).", None

    # 2. Reserva Atômica com check de rowcount
    try:
        with database.db_connection() as conn:
            cursor = conn.cursor()
            query_lock = """
                UPDATE rascunhos_voz_telegram
                SET status = 'PROCESSADO', aprovado_por = ?, processado_em = CURRENT_TIMESTAMP
                WHERE id = ? AND status IN ('PENDENTE', 'PENDENTE_APROVACAO_SUPERVISOR')
            """
            cursor.execute(database.format_pg(query_lock), (executado_por_usuario_id, rascunho_id))
            if cursor.rowcount == 0:
                return False, "⚠️ Concorrência: Este rascunho já foi confirmado ou aprovado por outro usuário.", None
            conn.commit()
    except Exception as lock_err:
        logger.error(f"Erro na trava atômica de rascunho: {lock_err}")
        return False, f"Erro de concorrência: {lock_err}", None

    # 3. Gravação da Transação no ERP
    tipo = draft.get("tipo_operacao")
    num_doc = f"VOICE-{int(datetime.now().timestamp())}"
    hoje_str = date.today().strftime("%Y-%m-%d")
    pdf_path = None

    try:
        if tipo == "PDV_EXPRESS":
            # Número DAV sequencial
            df_dav = database.fetch_all("SELECT MAX(CAST(numero_documento AS INTEGER)) as max_dav FROM vendas WHERE tipo_documento = 'DAV'")
            max_dav = df_dav.iloc[0]['max_dav'] if not df_dav.empty and pd.notna(df_dav.iloc[0]['max_dav']) else 0
            novo_dav = int(max_dav) + 1
            num_doc_dav = f"{novo_dav:010d}"

            venda_ids = []
            for item in draft.get("itens", []):
                database.run_query("""
                    INSERT INTO vendas (data, cliente_id, produto_id, quantidade, valor_unitario, valor_total, status, tipo_documento, numero_documento)
                    VALUES (?, ?, ?, ?, ?, ?, 'FATURADO', 'DAV', ?)
                """, (hoje_str, draft.get("parceiro_id"), item.get("produto_id"), float(item.get("quantidade")), float(item.get("preco_unitario")), float(item.get("valor_item")), num_doc_dav))
                
                df_v = database.fetch_all("SELECT MAX(id) as max_id FROM vendas")
                v_id = int(df_v.iloc[0]['max_id'])
                venda_ids.append(v_id)

                # Baixa de estoque FIFO
                custo_cmv, is_est, cmv_metodo, custo_aus = database.consumir_estoque_fifo(
                    produto_id=int(item.get("produto_id")),
                    quantidade=float(item.get("quantidade")),
                    data_mov=hoje_str,
                    origem='Venda Balcão Express (Voz)',
                    doc_ref=f"DAV #{num_doc_dav}"
                )
                database.run_query("UPDATE vendas SET custo_cmv_real = ?, cmv_metodo = ? WHERE id = ?", (custo_cmv, cmv_metodo, v_id))

            # Financeiro à vista ou a prazo
            if draft.get("condicao_pagamento") == "A_VISTA":
                c_id = draft.get("conta_bancaria_id") or 1
                database.run_query("""
                    INSERT INTO contas_a_receber (cliente_id, descricao, valor, data_vencimento, data_recebimento, status, conta_bancaria_id)
                    VALUES (?, ?, ?, ?, ?, 'RECEBIDO', ?)
                """, (draft.get("parceiro_id"), f"DAV #{num_doc_dav} (Voz Balcão)", float(draft.get("valor_total")), hoje_str, hoje_str, c_id))

                database.run_query("""
                    INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, conciliado, cliente_id, conta_bancaria_id)
                    VALUES (?, 'Entrada', 'Receita Com Vendas', ?, ?, TRUE, ?, ?)
                """, (hoje_str, f"REC. Balcão Voz ({draft.get('conta_bancaria_nome', 'Caixa')}): DAV #{num_doc_dav}", float(draft.get("valor_total")), draft.get("parceiro_id"), c_id))

            # Gerar PDF do DAV
            venda_info_pdf = {
                "numero_documento": num_doc_dav,
                "cliente_nome": draft.get("parceiro_nome"),
                "data": hoje_str,
                "condicao_pagamento": draft.get("condicao_pagamento"),
                "valor_total": draft.get("valor_total"),
                "itens": draft.get("itens", [])
            }
            pdf_path = gerar_pdf_dav(venda_info_pdf)

            # Log de Auditoria
            database.run_query("""
                INSERT INTO audit_log_voz (rascunho_id, usuario_id, chat_id, acao, tipo_operacao, valor_total, status_execucao, detalhe)
                VALUES (?, ?, ?, 'EXECUCAO', 'PDV_EXPRESS', ?, 'SUCESSO', ?)
            """, (rascunho_id, executado_por_usuario_id, chat_id, draft.get("valor_total"), f"DAV #{num_doc_dav} Faturado"))

            return True, f"✅ Venda Balcão faturada com sucesso! (DAV #{num_doc_dav})", pdf_path

        elif tipo == "PEDIDO_VENDA":
            num_doc_ped = f"PED-{int(datetime.now().timestamp())}"
            for item in draft.get("itens", []):
                database.run_query("""
                    INSERT INTO vendas (data, cliente_id, produto_id, quantidade, valor_unitario, valor_total, status, tipo_documento, numero_documento)
                    VALUES (?, ?, ?, ?, ?, ?, 'APROVADO', 'PEDIDO_VOZ', ?)
                """, (hoje_str, draft.get("parceiro_id"), item.get("produto_id"), float(item.get("quantidade")), float(item.get("preco_unitario")), float(item.get("valor_item")), num_doc_ped))

            return True, f"✅ Pedido de Venda registrado em carteira! (Doc: {num_doc_ped})", None

        elif tipo == "CONTA_PAGAR":
            database.run_query("""
                INSERT INTO contas_a_pagar (numero_documento, fornecedor_id, plano_conta_id, descricao, valor, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')
            """, (num_doc, draft.get("parceiro_id"), draft.get("plano_conta_id"), draft.get("descricao"), float(draft.get("valor_total")), draft.get("data_vencimento")))

            return True, f"✅ Conta a Pagar registrada com sucesso! (Doc: {num_doc})", None

        elif tipo == "CONTA_RECEBER":
            database.run_query("""
                INSERT INTO contas_a_receber (numero_documento, cliente_id, plano_conta_id, descricao, valor, data_emissao, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDENTE')
            """, (num_doc, draft.get("parceiro_id"), draft.get("plano_conta_id"), draft.get("descricao"), float(draft.get("valor_total")), hoje_str, draft.get("data_vencimento")))

            return True, f"✅ Conta a Receber registrada com sucesso! (Doc: {num_doc})", None

        return False, "Tipo de operação desconhecido.", None

    except Exception as exec_err:
        logger.error(f"Erro na efetivação de lançamento: {exec_err}")
        return False, f"❌ Erro ao gravar lançamento no ERP: {str(exec_err)}", None
