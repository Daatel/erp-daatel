import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import (
    run_query, fetch_all, gerar_comissao_se_necessario,
    db_transaction, run_query_tx, fetch_all_tx,
    consumir_estoque_fifo_tx, gerar_comissao_se_necessario_tx,
    get_clientes_ativos_cached, get_produtos_cached
)
from estilo import carregar_estilo

st.set_page_config(page_title="Faturamento & Expedição", page_icon="📦", layout="wide")
carregar_estilo()

st.title("📦 Faturamento & Expedição (SEFAZ)")
st.markdown("Central de liberação de carga. Fature os pedidos aprovados na Venda, bata o estoque e gere arquivos de integração fiscal.")

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

df_clientes = get_clientes_ativos_cached()
df_produtos = get_produtos_cached()

tab1, tab2, tab3 = st.tabs(["🚀 Fila de Faturamento (Em Lote)", "📂 Gerador Fiscal (SEFAZ/Emissor)", "🔄 Logística Reversa (Devoluções)"])

# ======= 1. FILA DE FATURAMENTO =======
with tab1:
    st.subheader("Fila de Pedidos Aprovados")
    st.markdown("Selecione os pedidos que deseja faturar agora. **Atenção ao farol de estoque:** O sistema permite faturar no vermelho, mas o saldo do Produto Acabado ficará negativo.")

    # Busca saldos de estoque atuais por produto
    df_saldos = fetch_all('''
        SELECT produto_id, SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END) as saldo_atual 
        FROM estoque_movimentos GROUP BY produto_id
    ''')
    dict_saldos = {}
    if not df_saldos.empty:
        dict_saldos = dict(zip(df_saldos['produto_id'], df_saldos['saldo_atual']))

    # Busca fila de pedidos abertos
    df_fila = fetch_all('''
        SELECT v.id as pedido_id, v.data as data_pedido, c.nome as cliente, c.uf as uf_cliente, 
               p.nome as produto, p.id as p_id, v.quantidade, v.valor_total, v.custo_acordos_rede
        FROM vendas v 
        JOIN clientes c ON v.cliente_id=c.id
        JOIN produtos p ON v.produto_id=p.id
        WHERE v.status = 'APROVADO'
        ORDER BY v.id ASC
    ''')

    if df_fila.empty:
        st.info("Nenhum pedido aguardando faturamento na fila. Todos os pedidos aprovados já foram faturados.")
    else:
        # Prepara grid com indicadores
        df_grid = df_fila.copy()
        df_grid['Selecionar'] = False
        df_grid['Saldo em Estoque'] = df_grid['p_id'].apply(lambda x: dict_saldos.get(x, 0.0))
        
        # Farol
        def get_farol(row):
            if row['Saldo em Estoque'] >= row['quantidade']: return "🟢 OK"
            elif row['Saldo em Estoque'] > 0: return "🟡 Parcial"
            return "🔴 Sem Saldo"
            
        df_grid['Farol (Status Físico)'] = df_grid.apply(get_farol, axis=1)
        
        # Sugestão JIT (Just-In-Time)
        df_grid['Lote Impresso (NF/DAV)'] = date.today().strftime('FAB %d/%m')
        df_grid['Validade (NF/DAV)'] = (date.today() + timedelta(days=90)).strftime('%d/%m/%Y')
        
        # Formatações visuais
        df_grid['data_pedido'] = pd.to_datetime(df_grid['data_pedido']).dt.strftime('%d/%m/%Y')
        df_grid['Valor Pedido'] = df_grid['valor_total'].apply(format_brl)
        
        df_view = df_grid[['Selecionar', 'pedido_id', 'data_pedido', 'cliente', 'produto', 'quantidade', 'Saldo em Estoque', 'Farol (Status Físico)', 'Valor Pedido', 'Lote Impresso (NF/DAV)', 'Validade (NF/DAV)']]
        
        st.markdown("### Selecione os Pedidos para Expedição")
        st.markdown("*Dica Comercial:* Digite ou aceite o Lote e Validade que a fábrica vai imprimir hoje à noite. Essa informação não trava o sistema contábil, apenas sai no papel para o cliente.")
        
        edited_df = st.data_editor(df_view, hide_index=True, width="stretch",
                                   column_config={
                                       "Selecionar": st.column_config.CheckboxColumn("Faturar?", default=False),
                                       "Lote Impresso (NF/DAV)": st.column_config.TextColumn("📝 Lote (Editar)"),
                                       "Validade (NF/DAV)": st.column_config.TextColumn("📅 Validade (Editar)")
                                   },
                                   disabled=["pedido_id", "data_pedido", "cliente", "produto", "quantidade", "Saldo em Estoque", "Farol (Status Físico)", "Valor Pedido"]
                                  )
        
        pedidos_selecionados = edited_df[edited_df['Selecionar'] == True]
        
        if not pedidos_selecionados.empty:
            st.markdown("---")
            st.subheader("⚙️ Ação em Lote")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            tipo_doc = col_f1.selectbox("Tipo de Documento", ["Nota Fiscal (NF)", "DAV (Documento Auxiliar de Venda)"])
            
            # Aviso contextual por tipo de documento
            if "DAV" in tipo_doc:
                col_f1.success("✅ **DAV:** Número gerado automaticamente. Embarque liberado imediatamente após o faturamento.")
            else:
                col_f1.warning(
                    "⏳ **Nota Fiscal:** O embarque na Logística ficará **retido** até o número "
                    "oficial da SEFAZ ser registrado na aba *Gerador Fiscal*. "
                    "Se precisar embarcar imediatamente, use a DAV."
                )
            
            sobrescrever = col_f2.checkbox("Sobrescrever Vencimento do Cliente?")
            venc_boleto_override = col_f2.date_input("Vencimento Forçado", value=date.today() + timedelta(days=30)) if sobrescrever else None
            
            def simular_emissao_sefaz_with_retry(venda_id, cliente_nome, valor, max_retries=3):
                import random
                import time
                status_placeholder = st.empty()
                status_placeholder.info(f"📡 Transmitindo NF-e da Venda #{venda_id} ({cliente_nome}) para a SEFAZ... Valor: R$ {valor:,.2f}")
                time.sleep(0.5)
                base_backoff = 1.0  # segundos
                for attempt in range(1, max_retries + 1):
                    try:
                        # 20% de chance de instabilidade temporária na SEFAZ para fins de demonstração
                        if random.random() < 0.20:
                            raise Exception("Erro HTTP 503: SEFAZ fora do ar temporariamente.")
                        status_placeholder.success(f"✅ NF da Venda #{venda_id} ({cliente_nome}) autorizada na SEFAZ (Tentativa {attempt})!")
                        time.sleep(0.5)
                        status_placeholder.empty()
                        return True
                    except Exception as e:
                        if attempt == max_retries:
                            status_placeholder.error(f"🛑 Falha final: SEFAZ inalcançável após {max_retries} tentativas. Revertendo alterações.")
                            raise e
                        sleep_time = (base_backoff * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)
                        status_placeholder.warning(f"⚠️ Tentativa {attempt} falhou ({str(e)}). Retentando em {sleep_time:.2f}s...")
                        time.sleep(sleep_time)

            if col_f3.button("📦 Processar Faturamento Selecionado", type="primary", use_container_width=True):
                p_c = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                pc_id = int(p_c.iloc[0]['id']) if not p_c.empty else None
                
                try:
                    # Envolve tudo em uma transação atômica
                    with db_transaction() as conn:
                        cursor = conn.cursor()
                        
                        for _, row in pedidos_selecionados.iterrows():
                            pid = int(row['pedido_id'])
                            
                            # Pega detalhes originais da venda para o DB
                            vd_df = fetch_all_tx(cursor, '''
                                SELECT v.id as pedido_id, v.data as data_pedido, c.nome as cliente, c.uf as uf_cliente, 
                                       p.nome as produto, p.id as p_id, v.quantidade, v.valor_total, v.custo_acordos_rede
                                FROM vendas v 
                                JOIN clientes c ON v.cliente_id=c.id
                                JOIN produtos p ON v.produto_id=p.id
                                WHERE v.id = ?
                            ''', (pid,))
                            
                            if vd_df.empty:
                                continue
                            
                            vd = vd_df.iloc[0]
                            v_total = float(vd['valor_total'])
                            cli_nome = vd['cliente']
                            prod_nome = vd['produto']
                            prod_id = int(vd['p_id'])
                            qtd = float(vd['quantidade'])
                            
                            lote_impresso = row.get('Lote Impresso (NF/DAV)', '')
                            validade_impressa = row.get('Validade (NF/DAV)', '')
                            
                            # Se for Nota Fiscal, transmite para o SEFAZ antes de baixar no banco
                            if "Nota Fiscal" in tipo_doc:
                                simular_emissao_sefaz_with_retry(pid, cli_nome, v_total)
                            
                            # 1. Muda Status da Venda e Numeração (DAV)
                            if "DAV" in tipo_doc:
                                df_dav_max = fetch_all_tx(cursor, "SELECT MAX(CAST(numero_documento AS INTEGER)) as max_dav FROM vendas WHERE tipo_documento LIKE '%DAV%'")
                                max_dav = df_dav_max.iloc[0]['max_dav'] if not df_dav_max.empty and pd.notna(df_dav_max.iloc[0]['max_dav']) else 0
                                novo_dav = int(max_dav) + 1
                                dav_str = f"{novo_dav:010d}"
                                run_query_tx(cursor, "UPDATE vendas SET status='FATURADO', tipo_documento=?, numero_documento=?, lote_impresso=?, validade_impressa=? WHERE id=?", (tipo_doc, dav_str, lote_impresso, validade_impressa, pid))
                            else:
                                run_query_tx(cursor, "UPDATE vendas SET status='FATURADO', tipo_documento=?, lote_impresso=?, validade_impressa=? WHERE id=?", (tipo_doc, lote_impresso, validade_impressa, pid))
                            
                            # 2. Baixa de Estoque via FIFO na transação
                            custo_cmv_real, is_estimado = consumir_estoque_fifo_tx(
                                cursor=cursor,
                                produto_id=prod_id,
                                quantidade=qtd,
                                data_mov=date.today().strftime("%Y-%m-%d"),
                                origem=f'Expedição {tipo_doc}',
                                doc_ref=f"Venda Lote #{pid}"
                            )
                            
                            run_query_tx(cursor, "UPDATE vendas SET custo_cmv_real = ? WHERE id = ?", (custo_cmv_real, pid))
                            
                            if is_estimado:
                                st.warning(f"⚠️ O CMV do Pedido #{pid} ({cli_nome}) foi estimado por falta de lote correspondente no estoque (Estoque Negativo).")
                            
                            # 3. Lançamento Financeiro
                            cli_id_df = fetch_all_tx(cursor, "SELECT cliente_id FROM vendas WHERE id=?", (pid,))
                            cli_id = int(cli_id_df.iloc[0]['cliente_id']) if not cli_id_df.empty else 0
                            
                            cli_prazo_df = fetch_all_tx(cursor, "SELECT prazo_pagamento_dias FROM clientes WHERE id=?", (cli_id,))
                            prazo_dias = int(cli_prazo_df.iloc[0]['prazo_pagamento_dias']) if not cli_prazo_df.empty and 'prazo_pagamento_dias' in cli_prazo_df.columns and pd.notnull(cli_prazo_df.iloc[0]['prazo_pagamento_dias']) else 30
                            
                            venc_final = venc_boleto_override if sobrescrever else date.today() + timedelta(days=prazo_dias)
                            dsc_financeira = f"{tipo_doc} - Venda #{pid} ({cli_nome} - {prod_nome})"
                            
                            run_query_tx(cursor, "INSERT INTO contas_a_receber (venda_id, cliente_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                      (pid, cli_id, pc_id, dsc_financeira, v_total, venc_final.strftime("%Y-%m-%d"), 'PENDENTE'))
                            
                            # 4. Acordos de Rede
                            custo_acordos = float(vd['custo_acordos_rede']) if pd.notnull(vd['custo_acordos_rede']) else 0.0
                            if custo_acordos > 0:
                                venc_acordo = date.today() + timedelta(days=30)
                                cli_rede_df = fetch_all_tx(cursor, "SELECT rede_clientes FROM clientes WHERE id=?", (cli_id,))
                                rede_str = cli_rede_df.iloc[0]['rede_clientes'] if not cli_rede_df.empty and cli_rede_df.iloc[0]['rede_clientes'] else "Rede Desconhecida"
                                desc_acordo = f"Repasse Acordo Comercial (Contrato/Logística): REDE {str(rede_str).upper()} - Venda #{pid}"
                                
                                p_c_acordo = fetch_all_tx(cursor, "SELECT id FROM planos_de_contas WHERE codigo = '2.2.2' OR nome LIKE '%Acordo%' OR nome LIKE '%Comiss%' LIMIT 1")
                                pc_acord_id = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None
                                
                                run_query_tx(cursor, "INSERT INTO contas_a_pagar (plano_conta_id, cliente_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, 'PENDENTE')",
                                          (pc_acord_id, cli_id, desc_acordo, custo_acordos, venc_acordo.strftime("%Y-%m-%d")))
                            
                            # 5. Taxa de Descarga
                            cli_taxa_df = fetch_all_tx(cursor, "SELECT taxa_descarga, regras_descarga, nome FROM clientes WHERE id=?", (cli_id,))
                            if not cli_taxa_df.empty:
                                taxa_desc = float(cli_taxa_df.iloc[0]['taxa_descarga'] or 0.0)
                                if taxa_desc > 0:
                                    regra_str = cli_taxa_df.iloc[0]['regras_descarga'] or "Sem regras específicas"
                                    desc_taxa = f"Taxa de Descarga CD - {cli_nome} - Venda #{pid} | Regra: {regra_str}"
                                    
                                    p_c_descarga = fetch_all_tx(cursor, "SELECT id FROM planos_de_contas WHERE codigo = '2.1.5' OR nome LIKE '%Frete%' OR nome LIKE '%Descarga%' LIMIT 1")
                                    pc_desc_id = int(p_c_descarga.iloc[0]['id']) if not p_c_descarga.empty else None
                                    
                                    run_query_tx(cursor, "INSERT INTO contas_a_pagar (plano_conta_id, cliente_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, 'PENDENTE')",
                                              (pc_desc_id, cli_id, desc_taxa, taxa_desc, date.today().strftime("%Y-%m-%d")))
                                    run_query_tx(cursor, "UPDATE vendas SET custo_descarga=? WHERE id=?", (taxa_desc, pid))
                                     
                            # 6. Comissão
                            gerar_comissao_se_necessario_tx(cursor, pid, 'FATURAMENTO', cli_nome)
                        
                        st.success(f"✅ {len(pedidos_selecionados)} Pedido(s) Faturados com Sucesso! Estoque e Financeiro atualizados de forma consistente.")
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"🛑 Erro ao processar faturamento (Operação cancelada/revertida): {str(e)}")
                
    st.markdown("---")
    with st.expander("🖨️ Reimpressão e Visualização de Documentos (DAV)"):
        df_fat = fetch_all("SELECT v.id, c.nome, v.tipo_documento, v.numero_documento, v.data FROM vendas v JOIN clientes c ON v.cliente_id=c.id WHERE v.status='FATURADO' ORDER BY v.id DESC LIMIT 30")
        if not df_fat.empty:
            opcoes_fat = {f"Venda #{r['id']} - {r['nome']} ({r['tipo_documento']})": r['id'] for _, r in df_fat.iterrows()}
            v_sel = st.selectbox("Selecione o pedido faturado para visualizar/imprimir:", ["-- SELECIONE --"] + list(opcoes_fat.keys()))
            if v_sel != "-- SELECIONE --":
                vid = opcoes_fat[v_sel]
                
                # --- ÁREA DE SEGURANÇA E ESTORNO DE FATURAMENTO ---
                with st.container():
                    st.markdown("#### 🔄 Central de Segurança: Estornar/Desfazer Faturamento")
                    df_venda_manifesto = fetch_all("SELECT manifesto_id FROM vendas WHERE id = ?", (vid,))
                    manifesto_id = df_venda_manifesto.iloc[0]['manifesto_id'] if not df_venda_manifesto.empty else None
                    
                    if manifesto_id is not None:
                        st.error(f"🛑 **Estorno Bloqueado:** Este pedido já está vinculado ao **Manifesto de Logística #{manifesto_id}**! Remova o pedido do caminhão no módulo de Logística antes de tentar estornar o faturamento.")
                    else:
                        st.warning("⚠️ **Atenção:** Desfazer o faturamento irá excluir a conta a receber, estornar o saldo JIT dos lotes originais no estoque e retornar o pedido para a fila comercial de Pendentes.")
                        
                        if st.button("🔄 Executar Estorno de Faturamento", type="primary", key=f"btn_estorno_venda_{vid}"):
                            # 1. Buscar movimentações originais de saída para reverter
                            df_movs = fetch_all('''
                                SELECT produto_id, quantidade, lote_origem_id 
                                FROM estoque_movimentos 
                                WHERE documento_referencia = ? AND tipo_movimento = 'Saída'
                            ''', (f"Venda Lote #{vid}",))
                            
                            # 2. Inserir entradas reversoras
                            for _, mov in df_movs.iterrows():
                                p_id = int(mov['produto_id'])
                                qtd = float(mov['quantidade'])
                                lote_origem = int(mov['lote_origem_id']) if pd.notnull(mov['lote_origem_id']) else None
                                
                                run_query(
                                    """INSERT INTO estoque_movimentos 
                                       (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id) 
                                       VALUES (?, ?, 'Entrada', ?, ?, ?, ?)""",
                                    (date.today().strftime("%Y-%m-%d"), p_id, qtd, 'Estorno de Faturamento', f"Estorno Venda Lote #{vid}", lote_origem)
                                )
                                
                            # 3. Deletar Contas a Receber associada
                            run_query("DELETE FROM contas_a_receber WHERE venda_id = ?", (vid,))
                            
                            # 4. Deletar Contas a Pagar associadas (descarga e acordos de rede)
                            desc_descarga = f"%Venda #{vid}%"
                            run_query("DELETE FROM contas_a_pagar WHERE descricao LIKE ? AND status = 'PENDENTE'", (desc_descarga,))
                            
                            # 5. Resetar registro da venda de volta para APROVADO (Pendente)
                            run_query('''
                                UPDATE vendas 
                                SET status = 'APROVADO', 
                                    tipo_documento = NULL, 
                                    numero_documento = NULL, 
                                    custo_cmv_real = 0.0, 
                                    custo_descarga = 0.0, 
                                    lote_impresso = NULL, 
                                    validade_impressa = NULL
                                WHERE id = ?
                            ''', (vid,))
                            
                            st.success(f"✅ Faturamento do Pedido #{vid} estornado com sucesso! Estoque e financeiro reestabelecidos.")
                            import time; time.sleep(1.5); st.rerun()
                            
                st.markdown("---")
                
                import streamlit.components.v1 as components
                from utils_dav import buscar_dados_venda, gerar_html_dav
                
                venda_info = buscar_dados_venda(vid)
                if venda_info and "DAV" in venda_info['tipo_documento']:
                    html_dav = gerar_html_dav(venda_info)
                    components.html(html_dav, height=800, scrolling=True)
                elif venda_info:
                    # Painel de dados para NF (sem XML, mas com todas as informações do registro)
                    st.markdown("#### 🧾 Dados da Nota Fiscal Registrada")
                    df_nf_detail = fetch_all("""
                        SELECT v.id, v.data, v.numero_documento, v.tipo_documento,
                               v.valor_total, v.quantidade, v.lote_impresso, v.validade_impressa,
                               c.nome as cliente, c.cnpj_cpf, c.cidade, c.uf,
                               p.nome as produto, f.nome as vendedor
                        FROM vendas v
                        JOIN clientes c ON v.cliente_id = c.id
                        JOIN produtos p ON v.produto_id = p.id
                        LEFT JOIN funcionarios f ON v.vendedor_id = f.id
                        WHERE v.id = ?
                    """, (vid,))
                    if not df_nf_detail.empty:
                        nf = df_nf_detail.iloc[0]
                        num_nf = nf['numero_documento'] or "(Aguardando número SEFAZ)"
                        data_fat = pd.to_datetime(nf['data']).strftime('%d/%m/%Y') if pd.notna(nf['data']) else "-"
                        
                        info_col1, info_col2, info_col3 = st.columns(3)
                        info_col1.metric("Nº do Documento", num_nf)
                        info_col1.metric("Data de Faturamento", data_fat)
                        info_col1.metric("Tipo", nf['tipo_documento'])
                        
                        info_col2.metric("Cliente", nf['cliente'])
                        info_col2.metric("CNPJ/CPF", nf['cnpj_cpf'] or "(não informado)")
                        info_col2.metric("Cidade/UF", f"{nf['cidade'] or '-'} / {nf['uf'] or '-'}")
                        
                        info_col3.metric("Produto", nf['produto'])
                        info_col3.metric("Quantidade", f"{nf['quantidade']:,.2f}")
                        info_col3.metric("Valor Total", format_brl(nf['valor_total']))
                        
                        st.markdown("---")
                        det_col1, det_col2 = st.columns(2)
                        det_col1.info(f"📦 **Lote Impresso:** {nf['lote_impresso'] or '(não informado)'}")
                        det_col2.info(f"📅 **Validade Impressa:** {nf['validade_impressa'] or '(não informada)'}")
                        
                        if not num_nf or num_nf == "(Aguardando número SEFAZ)":
                            st.warning(
                                "⏳ Esta NF ainda não possui número SEFAZ registrado. "
                                "Registre o número na aba **Gerador Fiscal (SEFAZ/Emissor)** para liberar o embarque."
                            )
                        else:
                            st.success(f"✅ NF autorizada. Para reimprimir o DANFE, utilize seu Emissor SEFAZ com o número **{num_nf}**.")
        else:
            st.info("Nenhuma venda faturada encontrada.")

# ======= 2. EXPORTADOR SEFAZ =======
with tab2:
    st.subheader("📥 Exportador Fiscal (Geração de Arquivo SEFAZ)")
    st.markdown("Exporte as vendas faturadas no mês para um arquivo TXT/CSV padronizado para importação no Emissor SEFAZ de Terceiros.")
    
    hoje = date.today()
    mes_fiscal = st.selectbox("Mês de Competência do Arquivo", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')])
    
    uf_fabrica = st.selectbox("UF Origem (Fábrica)", ["SP", "MG", "RJ", "PR", "SC", "RS", "GO", "DF", "BA", "PE", "CE"])
    
    if st.button("🔄 Consultar Faturamentos e Gerar Arquivo"):
        # Pega as vendas FATURADAS do mês
        q_sefaz = '''
            SELECT v.id as NUM_PEDIDO, c.nome as CLIENTE, c.cnpj_cpf as CNPJ, c.uf as UF_DESTINO,
                   p.nome as PRODUTO, v.quantidade as QTD, v.valor_unitario as V_UNIT, v.valor_total as V_TOTAL,
                   v.lote_impresso as LOTE_NF, v.validade_impressa as VAL_NF,
                   v.data as DATA_FATURAMENTO, v.tipo_documento as DOC_ORIGEM
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.status = 'FATURADO' 
              AND v.tipo_documento = 'Nota Fiscal (NF)'
              AND strftime('%Y-%m', v.data) = ?
        '''
        df_export = fetch_all(q_sefaz, (mes_fiscal,))
        
        if df_export.empty:
            st.warning("Nenhum faturamento encontrado neste mês de competência.")
        else:
            # Enriquecendo com CFOP Dinâmico e NCM fixo para MVP
            df_export['NCM'] = "0703.20.90"
            df_export['CFOP'] = df_export['UF_DESTINO'].apply(lambda uf: "5101" if uf == uf_fabrica else "6101")
            
            st.success(f"Pronto! {len(df_export)} registros fiscais compilados.")
            st.dataframe(df_export, hide_index=True)
            
            # Geração do Arquivo Físico para Download
            csv_bytes = df_export.to_csv(index=False, sep=";").encode('utf-8-sig')
            
            st.download_button(
                label="📥 Baixar Arquivo de Integração (CSV SEFAZ)",
                data=csv_bytes,
                file_name=f"export_sefaz_{mes_fiscal}.csv",
                mime="text/csv",
                type="primary"
            )

    st.markdown("---")
    st.subheader("✍️ Atualizar Números de Notas Fiscais Autorizadas (Retorno SEFAZ)")
    st.markdown("Digite os números oficiais das notas geradas no SEFAZ para atualizar o ERP e liberar o embarque seguro na Logística.")
    
    # Busca vendas faturadas como 'Nota Fiscal (NF)' sem número de documento
    df_nfs_pendentes = fetch_all('''
        SELECT v.id as 'Venda ID', v.data as 'Data', c.nome as 'Cliente', p.nome as 'Produto', 
               v.quantidade as 'Qtd', v.valor_total as 'Valor Total', v.numero_documento as 'Número da NF-e'
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = 'FATURADO'
          AND v.tipo_documento = 'Nota Fiscal (NF)'
          AND (v.numero_documento IS NULL OR v.numero_documento = '')
        ORDER BY v.id ASC
    ''')
    
    if df_nfs_pendentes.empty:
        st.success("🎉 Nenhuma Nota Fiscal faturada pendente de número oficial!")
    else:
        df_nfs_pendentes['Data'] = pd.to_datetime(df_nfs_pendentes['Data']).dt.strftime('%d/%m/%Y')
        df_nfs_pendentes['Valor Total'] = df_nfs_pendentes['Valor Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Garante que Número da NF-e seja string
        df_nfs_pendentes['Número da NF-e'] = df_nfs_pendentes['Número da NF-e'].fillna("").astype(str)
        
        st.info("💡 **Dica:** Digite as numerações diretamente na coluna **'Número da NF-e'** abaixo e clique no botão para salvar tudo de uma vez.")
        
        edited_nfs = st.data_editor(
            df_nfs_pendentes,
            hide_index=True,
            width="stretch",
            column_config={
                "Número da NF-e": st.column_config.TextColumn("📝 Número da NF-e (Digitar)", help="Insira o número oficial da nota emitida pelo SEFAZ"),
            },
            disabled=["Venda ID", "Data", "Cliente", "Produto", "Qtd", "Valor Total"]
        )
        
        if st.button("💾 Salvar Números de NF-e", type="primary", use_container_width=True):
            saved_count = 0
            for idx, row in edited_nfs.iterrows():
                v_id = int(row['Venda ID'])
                nfe_num = str(row['Número da NF-e']).strip()
                if nfe_num != "":
                    run_query("UPDATE vendas SET numero_documento = ? WHERE id = ?", (nfe_num, v_id))
                    saved_count += 1
            
            if saved_count > 0:
                st.success(f"✅ {saved_count} Notas Fiscais atualizadas com sucesso! Embarque liberado na Logística.")
                import time; time.sleep(1.5); st.rerun()
            else:
                st.warning("Nenhum número de nota foi inserido.")

# ======= 3. LOGISTICA REVERSA =======
with tab3:
    st.subheader("Processamento de Devoluções e Revalidação")
    st.markdown("Mercadoria que chegou podre no destino ou venceu na gôndola. Isso abaterá o imposto lá no DRE (como Logística Reversa).")
    
    with st.form("form_devol", clear_on_submit=True):
        d1, d2 = st.columns(2)
        dt_dev = d1.date_input("Data do Ocorrido")
        
        if df_clientes.empty or df_produtos.empty:
            st.warning("Cadastros incompletos.")
        else:
            c_opts_dev = {f"{r['nome']}": r['id'] for _, r in df_clientes.iterrows()}
            cli_options = ["-- SELECIONE O CLIENTE --"] + list(c_opts_dev.keys())
            cli_dev = d2.selectbox("Rede/Cliente Reclamante", cli_options)
            
            d3, d4, d5 = st.columns([2, 1, 1])
            p_opts_dev = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
            prod_options = ["-- SELECIONE O PRODUTO --"] + list(p_opts_dev.keys())
            prod_dev = d3.selectbox("Pacote/Produto Avariado", prod_options)
            qtd_dev = d4.number_input("Carga Negada (Un/Kg)", min_value=0.1, step=1.0)
            
            if prod_dev != "-- SELECIONE O PRODUTO --":
                p_base = float(p_opts_dev[prod_dev]['preco_venda_base'])
                val_sug = float(qtd_dev * p_base)
            else:
                val_sug = 0.0
            valor_abatido = d5.number_input("Sangria Financeira R$ (Amargar no DRE)", value=val_sug, min_value=0.0)
            
            d6, d7 = st.columns([1, 2])
            motivo = d6.selectbox("Fator", ["Alho Esponjoso / Mofo", "Vencimento na Gôndola (S/ Giro)", "Amassado pelo Carga", "Quebra Direta"])
            obs_dev = d7.text_input("Nota Restritiva")
            
            if st.form_submit_button("Protocolar Sangria (Estornar Dinheiro da Fábrica)"):
                if cli_dev == "-- SELECIONE O CLIENTE --":
                    st.error("Por favor, selecione a Rede/Cliente Reclamante.")
                elif prod_dev == "-- SELECIONE O PRODUTO --":
                    st.error("Por favor, selecione o Pacote/Produto Avariado.")
                else:
                    c_id = c_opts_dev[cli_dev]
                    p_id = p_opts_dev[prod_dev]['id']
                    
                    # --- LÓGICA FINANCEIRA (DRE) ---
                    run_query("INSERT INTO devolucoes (data, cliente_id, produto_id, quantidade, motivo, valor_financeiro_abatido, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (dt_dev, c_id, p_id, qtd_dev, motivo, valor_abatido, obs_dev))
                              
                    run_query("INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                              (dt_dev, "Saída", "Logística Reversa (Devoluções)", valor_abatido, f"Estorno: {cli_dev} ({qtd_dev}x {prod_dev}) - {motivo}"))
                              
                    # --- LÓGICA DE ESTOQUE FÍSICO (Retorno com Custo Zero) ---
                    # 1. Busca Saldo Atual
                    df_saldo = fetch_all("SELECT SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END) as saldo FROM estoque_movimentos WHERE produto_id = ?", (p_id,))
                    saldo_atual = float(df_saldo.iloc[0]['saldo']) if not df_saldo.empty and pd.notna(df_saldo.iloc[0]['saldo']) else 0.0
                    if saldo_atual < 0: saldo_atual = 0.0 # Previne anomalias matemáticas
                    
                    # 2. Busca Custo Atual
                    df_custo = fetch_all("SELECT custo_unidade FROM produtos WHERE id = ?", (p_id,))
                    custo_atual = float(df_custo.iloc[0]['custo_unidade']) if not df_custo.empty and pd.notna(df_custo.iloc[0]['custo_unidade']) else 0.0
                    
                    # 3. Calcula o Custo Médio Ponderado (O lote devolvido entra valendo R$ 0,00)
                    novo_saldo = saldo_atual + qtd_dev
                    novo_custo_medio = (saldo_atual * custo_atual + qtd_dev * 0.0) / novo_saldo if novo_saldo > 0 else custo_atual
                    
                    # 4. Atualiza o cadastro do produto com o custo barateado
                    run_query("UPDATE produtos SET custo_unidade = ? WHERE id = ?", (novo_custo_medio, p_id))
                    
                    # 5. Dá a Entrada Física no Galpão
                    run_query("INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia) VALUES (?, ?, ?, ?, ?, ?)",
                              (dt_dev, p_id, 'Entrada', qtd_dev, 'Devolução de Cliente', f"Motivo: {motivo} (Cliente: {cli_dev})"))
    
                    st.error(f"Devolução Homologada! Mercadoria retornou ao estoque com custo R$0,00. Custo médio do produto caiu para R$ {novo_custo_medio:.2f}. Impacto DRE: R$ -{valor_abatido:,.2f}")
                    st.cache_data.clear()
                    import time; time.sleep(4); st.rerun()
            
    st.markdown("---")
    df_dev = fetch_all('''
       SELECT d.id as Req, d.data as Data, c.nome as Conta, p.nome as Carga, d.quantidade as Qtd, d.motivo as Causa, d.valor_financeiro_abatido as 'Estorno Financeiro'
       FROM devolucoes d JOIN clientes c ON d.cliente_id=c.id JOIN produtos p ON d.produto_id=p.id ORDER BY d.id DESC LIMIT 50
    ''')
    if not df_dev.empty:
        df_dev['Data'] = pd.to_datetime(df_dev['Data'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_dev['Estorno Financeiro'] = df_dev['Estorno Financeiro'].apply(format_brl)
        st.dataframe(df_dev, hide_index=True, width="stretch")
