import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import run_query, fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="Faturamento & Expedição", page_icon="📦", layout="wide")
carregar_estilo()

st.title("📦 Faturamento & Expedição (SEFAZ)")
st.markdown("Central de liberação de carga. Fature os pedidos aprovados na Venda, bata o estoque e gere arquivos de integração fiscal.")

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

df_clientes = fetch_all("SELECT id, nome, uf FROM clientes WHERE status='ATIVO'")
df_produtos = fetch_all("SELECT id, nome, preco_venda_base FROM produtos")

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
            sobrescrever = col_f2.checkbox("Sobrescrever Vencimento do Cliente?")
            venc_boleto_override = col_f2.date_input("Vencimento Forçado", value=date.today() + timedelta(days=30)) if sobrescrever else None
            
            if col_f3.button("📦 Processar Faturamento Selecionado", type="primary", use_container_width=True):
                # Pega a conta de receita do plano de contas
                p_c = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                pc_id = int(p_c.iloc[0]['id']) if not p_c.empty else None
                
                for _, row in pedidos_selecionados.iterrows():
                    pid = int(row['pedido_id'])
                    
                    # Pega detalhes originais da venda para o DB
                    vd = df_fila[df_fila['pedido_id'] == pid].iloc[0]
                    v_total = float(vd['valor_total'])
                    cli_nome = vd['cliente']
                    prod_nome = vd['produto']
                    prod_id = int(vd['p_id'])
                    qtd = float(vd['quantidade'])
                    
                    # Lote e Validade JIT
                    lote_impresso = row.get('Lote Impresso (NF/DAV)', '')
                    validade_impressa = row.get('Validade (NF/DAV)', '')
                    
                    # 1. Muda Status da Venda e Numeração (DAV)
                    if "DAV" in tipo_doc:
                        df_dav_max = fetch_all("SELECT MAX(CAST(numero_documento AS INTEGER)) as max_dav FROM vendas WHERE tipo_documento LIKE '%DAV%'")
                        max_dav = df_dav_max.iloc[0]['max_dav'] if not df_dav_max.empty and pd.notna(df_dav_max.iloc[0]['max_dav']) else 0
                        novo_dav = int(max_dav) + 1
                        dav_str = f"{novo_dav:010d}"
                        run_query("UPDATE vendas SET status='FATURADO', tipo_documento=?, numero_documento=?, lote_impresso=?, validade_impressa=? WHERE id=?", (tipo_doc, dav_str, lote_impresso, validade_impressa, pid))
                    else:
                        run_query("UPDATE vendas SET status='FATURADO', tipo_documento=?, lote_impresso=?, validade_impressa=? WHERE id=?", (tipo_doc, lote_impresso, validade_impressa, pid))
                    
                    # 2. Baixa de Estoque
                    run_query("INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia) VALUES (?, ?, ?, ?, ?, ?)",
                              (date.today().strftime("%Y-%m-%d"), prod_id, 'Saída', qtd, f'Expedição {tipo_doc}', f"Venda Lote #{pid}"))
                    
                    # 3. Lançamento Financeiro com Inteligência de Prazo do Cliente
                    cli_id_df = fetch_all("SELECT cliente_id FROM vendas WHERE id=?", (pid,))
                    cli_id = int(cli_id_df.iloc[0]['cliente_id']) if not cli_id_df.empty else 0
                    
                    cli_prazo_df = fetch_all("SELECT prazo_pagamento_dias FROM clientes WHERE id=?", (cli_id,))
                    prazo_dias = int(cli_prazo_df.iloc[0]['prazo_pagamento_dias']) if not cli_prazo_df.empty and 'prazo_pagamento_dias' in cli_prazo_df.columns and pd.notnull(cli_prazo_df.iloc[0]['prazo_pagamento_dias']) else 30
                    
                    venc_final = venc_boleto_override if sobrescrever else date.today() + timedelta(days=prazo_dias)

                    dsc_financeira = f"{tipo_doc} - Venda #{pid} ({cli_nome} - {prod_nome})"
                    run_query("INSERT INTO contas_a_receber (venda_id, cliente_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (pid, cli_id, pc_id, dsc_financeira, v_total, venc_final.strftime("%Y-%m-%d"), 'PENDENTE'))
                    
                    # 4. Geração de Passivo (Contas a Pagar) para Acordos Comerciais de Rede
                    custo_acordos = float(vd['custo_acordos_rede']) if pd.notnull(vd['custo_acordos_rede']) else 0.0
                    if custo_acordos > 0:
                        venc_acordo = date.today() + timedelta(days=30)
                        cli_rede_df = fetch_all("SELECT rede_clientes FROM clientes WHERE id=?", (cli_id,))
                        rede_str = cli_rede_df.iloc[0]['rede_clientes'] if not cli_rede_df.empty and cli_rede_df.iloc[0]['rede_clientes'] else "Rede Desconhecida"
                        desc_acordo = f"Repasse Acordo Comercial (Contrato/Logística): REDE {str(rede_str).upper()} - Venda #{pid}"
                        
                        p_c_acordo = fetch_all("SELECT id FROM planos_de_contas WHERE nome LIKE '%Acordo%' OR nome LIKE '%Comiss%' LIMIT 1")
                        pc_acord_id = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None
                        
                        run_query("INSERT INTO contas_a_pagar (plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
                                  (pc_acord_id, desc_acordo, custo_acordos, venc_acordo.strftime("%Y-%m-%d")))
                    
                    # 5. Taxa de Descarga do Cliente → Contas a Pagar imediato (D+0) + grava custo na venda
                    cli_taxa_df = fetch_all("SELECT taxa_descarga, regras_descarga, nome FROM clientes WHERE id=?", (cli_id,))
                    if not cli_taxa_df.empty:
                        taxa_desc = float(cli_taxa_df.iloc[0]['taxa_descarga'] or 0.0)
                        if taxa_desc > 0:
                            regra_str = cli_taxa_df.iloc[0]['regras_descarga'] or "Sem regras específicas"
                            desc_taxa = f"Taxa de Descarga CD - {cli_nome} - Venda #{pid} | Regra: {regra_str}"
                            # Gera passivo financeiro
                            run_query("INSERT INTO contas_a_pagar (plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
                                      (None, desc_taxa, taxa_desc, date.today().strftime("%Y-%m-%d")))
                            # Grava na venda para o DRE classificar como custo comercial variável
                            run_query("UPDATE vendas SET custo_descarga=? WHERE id=?", (taxa_desc, pid))

                st.balloons()
                st.success(f"✅ {len(pedidos_selecionados)} Pedido(s) Faturados com Sucesso! Estoque e Financeiro atualizados.")
                import time; time.sleep(2); st.rerun()
                
        st.markdown("---")
        with st.expander("🖨️ Reimpressão e Visualização de Documentos (DAV)"):
            df_fat = fetch_all("SELECT v.id, c.nome, v.tipo_documento, v.numero_documento, v.data FROM vendas v JOIN clientes c ON v.cliente_id=c.id WHERE v.status='FATURADO' ORDER BY v.id DESC LIMIT 30")
            if not df_fat.empty:
                opcoes_fat = {f"Venda #{r['id']} - {r['nome']} ({r['tipo_documento']})": r['id'] for _, r in df_fat.iterrows()}
                v_sel = st.selectbox("Selecione o pedido faturado para visualizar/imprimir:", ["-- SELECIONE --"] + list(opcoes_fat.keys()))
                if v_sel != "-- SELECIONE --":
                    vid = opcoes_fat[v_sel]
                    import streamlit.components.v1 as components
                    from utils_dav import buscar_dados_venda, gerar_html_dav
                    
                    venda_info = buscar_dados_venda(vid)
                    if venda_info and "DAV" in venda_info['tipo_documento']:
                        html_dav = gerar_html_dav(venda_info)
                        components.html(html_dav, height=800, scrolling=True)
                    elif venda_info:
                        st.info("Documento selecionado não é um DAV. Documentos fiscais (NF) são impressos via Emissor SEFAZ externo.")
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
            SELECT v.id as NUM_PEDIDO, c.nome as CLIENTE, c.cnpj as CNPJ, c.uf as UF_DESTINO,
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
            csv_str = df_export.to_csv(index=False, sep=";")
            
            st.download_button(
                label="📥 Baixar Arquivo de Integração (CSV SEFAZ)",
                data=csv_str,
                file_name=f"export_sefaz_{mes_fiscal}.csv",
                mime="text/csv",
                type="primary"
            )

# ======= 3. LOGISTICA REVERSA =======
with tab3:
    st.subheader("Processamento de Devoluções e Revalidação")
    st.markdown("Mercadoria que chegou podre no destino ou venceu na gôndola. Isso abaterá o imposto lá no DRE (como Logística Reversa).")
    
    with st.form("form_devol"):
        d1, d2 = st.columns(2)
        dt_dev = d1.date_input("Data do Ocorrido")
        
        if df_clientes.empty or df_produtos.empty:
            st.warning("Cadastros incompletos.")
        else:
            c_opts_dev = {f"{r['nome']}": r['id'] for _, r in df_clientes.iterrows()}
            cli_dev = d2.selectbox("Rede/Cliente Reclamante", list(c_opts_dev.keys()))
            
            d3, d4, d5 = st.columns([2, 1, 1])
            p_opts_dev = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
            prod_dev = d3.selectbox("Pacote/Produto Avariado", list(p_opts_dev.keys()))
            qtd_dev = d4.number_input("Carga Negada (Un/Kg)", min_value=0.1, step=1.0)
            
            p_base = float(p_opts_dev[prod_dev]['preco_venda_base'])
            valor_abatido = d5.number_input("Sangria Financeira R$ (Amargar no DRE)", value=float(qtd_dev * p_base), min_value=0.0)
            
            d6, d7 = st.columns([1, 2])
            motivo = d6.selectbox("Fator", ["Alho Esponjoso / Mofo", "Vencimento na Gôndola (S/ Giro)", "Amassado pelo Carga", "Quebra Direta"])
            obs_dev = d7.text_input("Nota Restritiva")
            
            if st.form_submit_button("Protocolar Sangria (Estornar Dinheiro da Fábrica)"):
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
