import re
import pandas as pd
from datetime import datetime
import streamlit as st
from database import fetch_all, db_transaction, run_query_tx


def parse_ofx(ofx_content: str):
    """
    Parser de alta resiliência para extratos OFX (SGML/XML) de todos os bancos brasileiros.
    Extrai a seção <BANKTRANLIST> e divide os registros por <STMTTRN>.
    """
    transacoes = []
    if not ofx_content or not isinstance(ofx_content, str):
        return transacoes

    # 1. Isola a lista de transações bancárias entre <BANKTRANLIST> e </BANKTRANLIST>
    list_match = re.search(r'<BANKTRANLIST>(.*?)(?:</BANKTRANLIST>|$)', ofx_content, re.DOTALL | re.IGNORECASE)
    if not list_match:
        return transacoes

    bank_content = list_match.group(1)

    # 2. Divide os blocos por <STMTTRN> (independente de ter </STMTTRN> ou quebra de linha)
    raw_blocks = re.split(r'<STMTTRN>', bank_content, flags=re.IGNORECASE)[1:]

    for block in raw_blocks:
        def get_tag(tag_name):
            m = re.search(rf'<{tag_name}>([^<\r\n]+)', block, re.IGNORECASE)
            return m.group(1).strip() if m else ""

        trntype = get_tag("TRNTYPE")
        dtposted_str = get_tag("DTPOSTED")
        trnamt_str = get_tag("TRNAMT")
        fitid = get_tag("FITID")
        memo = get_tag("MEMO") or get_tag("PAYEE") or "Lançamento Bancário"

        # Trata data YYYYMMDD
        dt_parsed = None
        if dtposted_str:
            clean_date = dtposted_str[:8]
            try:
                dt_parsed = datetime.strptime(clean_date, "%Y%m%d").date()
            except ValueError:
                dt_parsed = None

        # Trata valor float
        val_float = 0.0
        if trnamt_str:
            try:
                val_float = float(trnamt_str.replace(",", "."))
            except ValueError:
                val_float = 0.0

        if fitid and dt_parsed and val_float != 0.0:
            transacoes.append({
                "fitid": fitid,
                "data": dt_parsed,
                "valor": val_float,
                "tipo": "Entrada" if val_float > 0 else "Saída",
                "tipo_ofx": trntype,
                "memo": memo
            })

    return transacoes


def sugerir_conciliacao(transacoes_ofx, conta_bancaria_id):
    """
    Cruza cada transação do OFX com os títulos pendentes no ERP mantendo estado (Pool de Candidatos).
    Previne que dois lançamentos de mesmo valor apontem para o mesmo título.
    Tolerância de vencimento: Máximo D-2 (<= 2 dias).
    """
    # 1. Carrega FITIDs já conciliados no banco para evitar duplicidades
    df_fitids = fetch_all("SELECT fitid FROM fluxo_caixa WHERE fitid IS NOT NULL AND fitid != ''")
    fitids_existentes = set(df_fitids['fitid'].tolist()) if not df_fitids.empty else set()

    # 2. Carrega Contas a Pagar e Receber Pendentes
    df_pagar = fetch_all("""
        SELECT p.id, p.numero_documento, f.nome_fantasia as fornecedor, p.valor, p.data_vencimento, pc.nome as plano_conta
        FROM contas_a_pagar p
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        LEFT JOIN planos_de_contas pc ON p.plano_conta_id = pc.id
        WHERE p.status = 'PENDENTE'
    """)

    df_receber = fetch_all("""
        SELECT r.id, r.numero_documento, c.nome_fantasia as cliente, r.valor, r.data_vencimento, pc.nome as plano_conta
        FROM contas_a_receber r
        LEFT JOIN clientes c ON r.cliente_id = c.id
        LEFT JOIN planos_de_contas pc ON r.plano_conta_id = pc.id
        WHERE r.status = 'PENDENTE'
    """)

    # Pool de IDs já consumidos nesta sessão para evitar reutilização de títulos por lançamentos duplicados
    pagar_consumidos = set()
    receber_consumidos = set()

    resultados = []

    for t in transacoes_ofx:
        fitid = t['fitid']
        val_abs = abs(t['valor'])
        memo_upper = t['memo'].upper()
        dt_trn = t['data']

        # Trava Anti-Duplicidade por FITID
        if fitid in fitids_existentes:
            resultados.append({
                **t,
                "status_importacao": "Já Conciliado",
                "sugestao_acao": "🚫 Já Conciliado",
                "titulo_id": None,
                "titulo_sugerido_desc": "Lançamento bancário já importado anteriormente",
                "plano_conta_sugerido": "N/A"
            })
            continue

        sugestao_titulo = None
        sugestao_id = None
        plano_sugerido = None

        # --- BUSCA EM SAÍDAS (Contas a Pagar) ---
        if t['tipo'] == 'Saída' and not df_pagar.empty:
            df_candidatos = df_pagar[~df_pagar['id'].isin(pagar_consumidos)].copy()
            df_match = df_candidatos[abs(df_candidatos['valor'] - val_abs) < 0.01].copy()

            if not df_match.empty:
                df_match['diff_dias'] = df_match['data_vencimento'].apply(
                    lambda d: abs((datetime.strptime(str(d)[:10], "%Y-%m-%d").date() - dt_trn).days) if d else 999
                )
                df_match = df_match.sort_values(by='diff_dias')
                melhor_match = df_match.iloc[0]

                # Tolerância estrita D-1/D-2 (<= 2 dias)
                if melhor_match['diff_dias'] <= 2:
                    sugestao_id = int(melhor_match['id'])
                    pagar_consumidos.add(sugestao_id)  # Consome o título do pool!
                    forn_nome = melhor_match['fornecedor'] or "Fornecedor"
                    sugestao_titulo = f"PAG #{sugestao_id} - {forn_nome} (R$ {val_abs:,.2f})"
                    plano_sugerido = melhor_match['plano_conta'] or "2.05 - Matéria-Prima / Insumos"

        # --- BUSCA EM ENTRADAS (Contas a Receber) ---
        elif t['tipo'] == 'Entrada' and not df_receber.empty:
            df_candidatos = df_receber[~df_receber['id'].isin(receber_consumidos)].copy()
            df_match = df_candidatos[abs(df_candidatos['valor'] - val_abs) < 0.01].copy()

            if not df_match.empty:
                df_match['diff_dias'] = df_match['data_vencimento'].apply(
                    lambda d: abs((datetime.strptime(str(d)[:10], "%Y-%m-%d").date() - dt_trn).days) if d else 999
                )
                df_match = df_match.sort_values(by='diff_dias')
                melhor_match = df_match.iloc[0]

                # Tolerância estrita D-1/D-2 (<= 2 dias)
                if melhor_match['diff_dias'] <= 2:
                    sugestao_id = int(melhor_match['id'])
                    receber_consumidos.add(sugestao_id)  # Consome o título do pool!
                    cli_nome = melhor_match['cliente'] or "Cliente"
                    sugestao_titulo = f"REC #{sugestao_id} - {cli_nome} (R$ {val_abs:,.2f})"
                    plano_sugerido = melhor_match['plano_conta'] or "1.01 - Receita de Vendas"

        # --- AUTO-CATEGORIZAÇÃO POR PALAVRA-CHAVE (Se não casou título) ---
        if not plano_sugerido:
            if any(k in memo_upper for k in ["TARIFA", "TAR ", "CEST", "MANUT", "MENSALIDADE"]):
                plano_sugerido = "4.02 - Despesas Bancárias e Tarifas"
            elif any(k in memo_upper for k in ["IOF", "IMPOSTO", "TAXA"]):
                plano_sugerido = "4.03 - Taxas e Encargos Financeiros"
            elif any(k in memo_upper for k in ["REND", "APLIC", "JUROS REC"]):
                plano_sugerido = "1.03 - Receitas Financeiras"
            else:
                plano_sugerido = "OUTROS - A Classificar"  # Fallback neutro sem chutes

        resultados.append({
            **t,
            "status_importacao": "Pendente",
            "sugestao_acao": "🎯 Confirmar Título" if sugestao_titulo else "➕ Lançamento Direto",
            "titulo_sugerido_desc": sugestao_titulo or "Sem título pendente equivalente",
            "titulo_id": sugestao_id,
            "plano_conta_sugerido": plano_sugerido
        })

    return resultados


def executar_baixa_conciliacao_lote(df_grid, conta_bancaria_id, modo_simulacao=False):
    """
    Executa a baixa de títulos e inserção no fluxo_caixa dentro de UMA ÚNICA TRANSAÇÃO ATÔMICA ACID.
    Se qualquer query falhar, NENHUMA alteração é persistida no banco de dados (ROLLBACK integral via db_transaction).
    """
    sucessos = 0
    erros = 0
    relatorio_simulacao = []

    if modo_simulacao:
        for _, row in df_grid.iterrows():
            acao = row['sugestao_acao']
            if acao in ["🚫 Ignorar", "Já Conciliado", "🚫 Já Conciliado"]:
                continue
            relatorio_simulacao.append(
                f"[SIMULAÇÃO] Ação: {acao} | Data: {row['data']} | Valor: R$ {row['valor']:,.2f} | Histórico: {row['memo']} | Plano: {row['plano_conta_sugerido']}"
            )
            sucessos += 1
        return True, f"🔍 Modo Simulação Concluído! {sucessos} lançamentos validados (nenhum dado gravado no banco).", relatorio_simulacao

    try:
        with db_transaction() as conn:
            cursor = conn.cursor()

            for _, row in df_grid.iterrows():
                acao = row['sugestao_acao']
                if acao in ["🚫 Ignorar", "Já Conciliado", "🚫 Já Conciliado"]:
                    continue

                fitid = str(row['fitid'])
                dt_str = str(row['data'])[:10]
                val = float(row['valor'])
                tipo_mov = "Entrada" if val > 0 else "Saída"
                memo = str(row['memo'])
                plano_nome = str(row['plano_conta_sugerido'])

                # Busca o ID do Plano de Contas selecionado na linha
                df_pc = fetch_all("SELECT id FROM planos_de_contas WHERE nome = ? LIMIT 1", (plano_nome,))
                plano_id = int(df_pc.iloc[0]['id']) if not df_pc.empty else None

                # --- CASO A: CONFIRMAR TÍTULO (Contas a Pagar / Receber) ---
                if acao == "🎯 Confirmar Título" and row.get('titulo_id') and pd.notna(row['titulo_id']):
                    titulo_id = int(row['titulo_id'])
                    titulo_desc = str(row['titulo_sugerido_desc'])

                    if titulo_desc.startswith("PAG"):
                        # 1. Dar Baixa em Contas a Pagar
                        run_query_tx(cursor, """
                            UPDATE contas_a_pagar 
                            SET status = 'LIQUIDADO', data_pagamento = ?, conta_bancaria_id = ?
                            WHERE id = ?
                        """, (dt_str, conta_bancaria_id, titulo_id))

                        # 2. Inserir no Fluxo de Caixa vinculado ao Título
                        run_query_tx(cursor, """
                            INSERT INTO fluxo_caixa 
                              (data, tipo, categoria, descricao, valor, conta_bancaria_id, fonte_id, plano_conta_id, conciliado, fitid)
                            VALUES (?, 'Saída', ?, ?, ?, ?, ?, ?, TRUE, ?)
                        """, (dt_str, plano_nome, f"Baixa PAG #{titulo_id} | {memo}", abs(val), conta_bancaria_id, titulo_id, plano_id, fitid))

                    elif titulo_desc.startswith("REC"):
                        # 1. Dar Baixa em Contas a Receber
                        run_query_tx(cursor, """
                            UPDATE contas_a_receber 
                            SET status = 'RECEBIDO', data_recebimento = ?, conta_bancaria_id = ?
                            WHERE id = ?
                        """, (dt_str, conta_bancaria_id, titulo_id))

                        # 2. Inserir no Fluxo de Caixa vinculado ao Título
                        run_query_tx(cursor, """
                            INSERT INTO fluxo_caixa 
                              (data, tipo, categoria, descricao, valor, conta_bancaria_id, fonte_id, plano_conta_id, conciliado, fitid)
                            VALUES (?, 'Entrada', ?, ?, ?, ?, ?, ?, TRUE, ?)
                        """, (dt_str, plano_nome, f"Baixa REC #{titulo_id} | {memo}", abs(val), conta_bancaria_id, titulo_id, plano_id, fitid))

                # --- CASO B: LANÇAMENTO DIRETO (Tarifas, Pix Avulso, IOF) ---
                elif acao == "➕ Lançamento Direto" or not row.get('titulo_id'):
                    run_query_tx(cursor, """
                        INSERT INTO fluxo_caixa 
                          (data, tipo, categoria, descricao, valor, conta_bancaria_id, plano_conta_id, conciliado, fitid)
                        VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, ?)
                    """, (dt_str, tipo_mov, plano_nome, memo, abs(val), conta_bancaria_id, plano_id, fitid))

                sucessos += 1

        # Limpa cache do Streamlit
        try:
            st.cache_data.clear()
        except Exception:
            pass

        return True, f"✔️ {sucessos} conciliações realizadas e gravadas com sucesso no banco de dados!", []

    except Exception as err:
        return False, f"❌ Erro na transação atômica. Nenhuma alteração foi salva no banco: {str(err)}", []
