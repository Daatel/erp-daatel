import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
from database import run_query, fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="Pedidos de Venda", page_icon="📝", layout="wide")
carregar_estilo()

st.title("📝 Captação de Pedidos de Venda")
st.markdown("Registre a intenção de compra do cliente. **Atenção:** Isso gera apenas um Pedido em Aberto. A baixa de estoque e o título financeiro só ocorrem no módulo de **Faturamento**.")

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

df_clientes = fetch_all("SELECT id, nome, rede_clientes, prazo_pagamento FROM clientes WHERE status='ATIVO'")
df_vendedores = fetch_all("SELECT id, nome, gatilho_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")
df_produtos = fetch_all("SELECT id, nome, preco_venda_base FROM produtos WHERE is_materia_prima = 0")
df_regras = fetch_all("SELECT vendedor_id, produto_id, rede_clientes, percentual FROM comissoes_regras")

tab1, tab_deg, tab2, tab5 = st.tabs(["🛒 Lançar Novo Pedido", "🍇 Degustação & Amostras", "📋 Meus Pedidos Abertos", "📊 Tabelas de Preços"])

# ======= 1. CAPTAÇÃO DE PEDIDO =======
with tab1:
    if df_clientes.empty or df_vendedores.empty or df_produtos.empty:
        st.warning("Cadastre Clientes, Vendedores e Produtos antes de iniciar as vendas!")
    else:
        col1, col2 = st.columns([1, 2])
        data_venda = col1.date_input("Data do Pedido", value=date.today())
        
        c_opts = {f"{r['nome']}": r for _, r in df_clientes.iterrows()}
        cliente_sel = col2.selectbox("Cliente Destino (Ativos)", list(c_opts.keys()))
        
        v_opts = {f"{r['nome']}": r for _, r in df_vendedores.iterrows()}
        vendedor_sel = st.selectbox("Vendedor / Representante", list(v_opts.keys()))
        
        st.markdown("##### Informações do Produto")
        col3, col4, col_tipo, col5 = st.columns([2, 1, 1.2, 1.2])
        p_opts = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
        produto_sel = col3.selectbox("Produto Final Solicitado", list(p_opts.keys()))
        qtd = col4.number_input("Quantidade Negociada (Volumes/Kg)", min_value=1.0, step=1.0)
        tipo_item = col_tipo.selectbox("Tipo de Lançamento", ["Comercial (Venda)", "Bonificado (Bonificação)"])
        
        # --- LÓGICA DE PRECIFICAÇÃO DINÂMICA ---
        cli_selecionado = c_opts[cliente_sel]
        nome_cliente = cli_selecionado['nome']
        df_cli_grp = fetch_all("SELECT grupo_lojas FROM clientes WHERE id=?", (cli_selecionado['id'],))
        grupo_cliente = df_cli_grp.iloc[0]['grupo_lojas'] if not df_cli_grp.empty else None
        rede_cliente = cli_selecionado['rede_clientes']
        prod_id = p_opts[produto_sel]['id']
        
        preco_tabela = None
        origem_preco = "Preço Base de Balcão"
        pct_contrato = 0.0
        pct_auxiliar = 0.0
        pct_logistica = 0.0
        
        tb_cli = fetch_all("SELECT preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='CLIENTE' AND entidade_nome=? AND status='ATIVO'", (prod_id, nome_cliente))
        if not tb_cli.empty:
            preco_tabela = float(tb_cli.iloc[0]['preco'])
            pct_contrato = float(tb_cli.iloc[0]['pct_contrato'] or 0.0)
            pct_auxiliar = float(tb_cli.iloc[0]['pct_comissao_auxiliar'] or 0.0)
            pct_logistica = float(tb_cli.iloc[0]['pct_acordo_logistico'] or 0.0)
            origem_preco = "Tabela Individual (Acordo Cliente)"
        else:
            if grupo_cliente:
                tb_grp = fetch_all("SELECT preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='GRUPO' AND entidade_nome=? AND status='ATIVO'", (prod_id, grupo_cliente))
                if not tb_grp.empty:
                    preco_tabela = float(tb_grp.iloc[0]['preco'])
                    pct_contrato = float(tb_grp.iloc[0]['pct_contrato'] or 0.0)
                    pct_auxiliar = float(tb_grp.iloc[0]['pct_comissao_auxiliar'] or 0.0)
                    pct_logistica = float(tb_grp.iloc[0]['pct_acordo_logistico'] or 0.0)
                    origem_preco = "Tabela de Sub-Grupo"
            
            if preco_tabela is None and rede_cliente:
                tb_red = fetch_all("SELECT preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='REDE' AND entidade_nome=? AND status='ATIVO'", (prod_id, rede_cliente))
                if not tb_red.empty:
                    preco_tabela = float(tb_red.iloc[0]['preco'])
                    pct_contrato = float(tb_red.iloc[0]['pct_contrato'] or 0.0)
                    pct_auxiliar = float(tb_red.iloc[0]['pct_comissao_auxiliar'] or 0.0)
                    pct_logistica = float(tb_red.iloc[0]['pct_acordo_logistico'] or 0.0)
                    origem_preco = "Tabela Matriz (Acordo Rede)"
                    
        if preco_tabela is None:
            preco_tabela = float(p_opts[produto_sel]['preco_venda_base'])
            
        if tipo_item == "Bonificado (Bonificação)":
            preco_tabela = 0.0
            st.info("🎁 **Item Bonificado**: Preço unitário fixado em R$ 0,00.")
            preco = col5.number_input("Preço Unitário Fechado (R$)", min_value=0.0, max_value=0.0, value=0.0, disabled=True, key="preco_bonif")
        else:
            st.info(f"💡 Origem do Preço Aplicado: **{origem_preco}**")
            preco = col5.number_input("Preço Unitário Fechado (R$)", min_value=0.0, value=preco_tabela, step=0.1, key="preco_venda")
        
        if st.button("Aprovar Pedido (Mandar para a Expedição)", type="primary", use_container_width=True):
            cli = c_opts[cliente_sel]
            ven = v_opts[vendedor_sel]
            prod = p_opts[produto_sel]
            v_total = qtd * preco
            
            # Regra de Comissão Dinâmica Multi-Nível
            comissao_perc = 0.0
            if not df_regras.empty:
                rede_c = cli['rede_clientes'] if cli['rede_clientes'] else "TODOS"
                rc = df_regras[(df_regras['vendedor_id'] == ven['id']) & 
                               (df_regras['rede_clientes'] == rede_c)]
                
                if not rc.empty:
                    rc_p = rc[(rc['produto_id'] == prod['id'])]
                    if not rc_p.empty:
                        comissao_perc = rc_p.iloc[0]['percentual']
                    else:
                        rc_todos = rc[rc['produto_id'].isna()]
                        if not rc_todos.empty:
                            comissao_perc = rc_todos.iloc[0]['percentual']
                            
            com_val = v_total * (comissao_perc / 100.0)
            
            # Acordos Comerciais Rede
            custo_acordos = v_total * (pct_contrato + pct_auxiliar + pct_logistica) / 100.0
            
            is_bonif = True if tipo_item == "Bonificado (Bonificação)" else False
            
            run_query("INSERT INTO vendas (data, cliente_id, vendedor_id, produto_id, quantidade, valor_unitario, valor_total, comissao_valor, custo_acordos_rede, is_bonificacao, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APROVADO')",
                      (data_venda, cli['id'], ven['id'], prod['id'], qtd, preco, v_total, com_val, custo_acordos, is_bonif))
                      
            v_id = fetch_all("SELECT MAX(id) as lg FROM vendas").iloc[0]['lg']
            
            st.toast(f"✔️ Pedido #{v_id} lançado com sucesso!", icon="✅")
            st.success(f"✔️ Pedido #{v_id} lançado com sucesso! Ele já está na Fila do módulo de Faturamento aguardando expedição física.")

# ======= 1.2. REMESSA DE DEGUSTAÇÃO & AMOSTRAS =======
with tab_deg:
    st.subheader("🍇 Lançamento de Amostras e Ações de Degustação")
    st.markdown("Esta tela realiza a saída física imediata de mercadorias para ações de degustação ou amostras em clientes, calculando o custo via FIFO e debitando-o automaticamente no caixa na conta `2.2.1 Custo de Degustações e Amostras` vinculando o CNPJ.")

    df_bancos = fetch_all("SELECT id, nome FROM contas_bancarias WHERE status='ATIVO'")
    
    if df_clientes.empty or df_produtos.empty:
        st.warning("Cadastre Clientes e Produtos antes de realizar o lançamento!")
    elif df_bancos.empty:
        st.warning("Cadastre pelo menos uma Conta Bancária ativa em **Financeiro → 🏦 Contas Bancárias** para registrar a movimentação financeira correspondente.")
    else:
        with st.form("form_degustacao", clear_on_submit=True):
            col_d1, col_d2 = st.columns([1, 2])
            data_acao = col_d1.date_input("Data da Ação", value=date.today())
            
            c_opts_deg = {f"{r['nome']}": r for _, r in df_clientes.iterrows()}
            cliente_deg_sel = col_d2.selectbox("Cliente / PDV Beneficiado (CNPJ Obrigatório)", list(c_opts_deg.keys()), key="deg_cli")
            
            col_d3, col_d4, col_d5 = st.columns([2, 1, 1])
            p_opts_deg = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
            prod_deg_sel = col_d3.selectbox("Produto Utilizado na Ação", list(p_opts_deg.keys()), key="deg_prod")
            qtd_deg = col_d4.number_input("Quantidade Utilizada (unidades/Kg)", min_value=1.0, step=1.0, key="deg_qtd")
            
            b_opts = {f"{r['nome']}": r['id'] for _, r in df_bancos.iterrows()}
            banco_sel = col_d5.selectbox("Conta Bancária (Débito)", list(b_opts.keys()), key="deg_banco")
            
            obs_deg = st.text_area("Ocorrências / Relatório da Degustação", placeholder="Escreva aqui detalhes da ação, promotor que executou, etc.")
            
            btn_deg = st.form_submit_button("🏁 Gravar Remessa e Debitar Custo", type="primary", use_container_width=True)
            
        if btn_deg:
            from database import consumir_estoque_fifo
            
            cli_deg = c_opts_deg[cliente_deg_sel]
            prod_deg = p_opts_deg[prod_deg_sel]
            banco_id = b_opts[banco_sel]
            
            doc_ref = f"Amostra/Degustação: {cli_deg['nome']}"
            
            # 1. Rodar FIFO
            custo_total, is_estimado = consumir_estoque_fifo(
                produto_id=int(prod_deg['id']),
                quantidade=float(qtd_deg),
                data_mov=data_acao.strftime("%Y-%m-%d"),
                origem="Degustação_Amostra",
                doc_ref=doc_ref
            )
            
            # 2. Lançar no Fluxo de Caixa (Saída)
            desc_financeira = f"Custo Mercadoria Amostra - {cli_deg['nome']} ({prod_deg['nome']} x {qtd_deg:.0f})"
            if obs_deg:
                desc_financeira += f" | {obs_deg}"
                
            run_query(
                """INSERT INTO fluxo_caixa 
                   (data, tipo, categoria, descricao, valor, conta_bancaria_id, cliente_id, conciliado) 
                   VALUES (?, 'SAÍDA', '2.2.1', ?, ?, ?, ?, 1)""",
                (data_acao.strftime("%Y-%m-%d"), desc_financeira, custo_total, banco_id, int(cli_deg['id']))
            )
            
            st.balloons()
            st.success(f"✔️ Remessa registrada com sucesso! Saída física executada via FIFO.")
            st.info(f"📊 **Custo Real FIFO apurado:** R$ {custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            if is_estimado:
                st.warning("⚠️ **Atenção:** O estoque físico no sistema estava insuficiente/zerado. O custo foi estimado provisoriamente usando o custo de cadastro do produto.")
            st.rerun()

# ======= 2. GESTÃO DE PEDIDOS =======
with tab2:
    st.subheader("📋 Gestão e Acompanhamento de Pedidos")
    df_pedidos = fetch_all('''
        SELECT v.id as 'Pedido', v.data as 'Data Captação', c.nome as 'Cliente', 
               vn.nome as 'Vendedor', p.nome as 'Carga', v.quantidade as 'Qtd', 
               v.valor_total as 'Valor Total', v.status as 'Status do Pedido'
        FROM vendas v 
        JOIN clientes c ON v.cliente_id=c.id
        JOIN funcionarios vn ON v.vendedor_id=vn.id
        JOIN produtos p ON v.produto_id=p.id
        ORDER BY v.id DESC LIMIT 100
    ''')
    if not df_pedidos.empty:
        df_pedidos['Data Captação'] = pd.to_datetime(df_pedidos['Data Captação'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_pedidos['Valor Total'] = df_pedidos['Valor Total'].apply(format_brl)
        
        def highlight_status(row):
            if row['Status do Pedido'] == 'APROVADO':
                return ['background-color: #ffffe0; color: black'] * len(row) # Amarelo claro para pendente
            elif row['Status do Pedido'] == 'FATURADO':
                return ['background-color: #e6ffe6; color: black'] * len(row) # Verde claro para faturado
            return [''] * len(row)

        st.dataframe(df_pedidos.style.apply(highlight_status, axis=1), hide_index=True, width="stretch")
    else:
        st.info("Nenhum pedido registrado no banco de dados.")

# ======= 5. TABELAS DE PREÇOS =======
with tab5:
    st.subheader("Gerenciamento de Tabelas de Preços")
    st.markdown("Crie regras de preço por Cliente, Grupo ou Rede. O sistema priorizará a regra mais específica na hora da venda.")
    
    col_t1, col_t2 = st.columns(2)
    
    p_opts_tab = {f"{r['nome']}": r['id'] for _, r in df_produtos.iterrows()}
    if p_opts_tab:
        prod_selecionado = col_t1.selectbox("1. Selecione o Produto", list(p_opts_tab.keys()), key="tab_prod")
        
        tipo_entidade = col_t2.selectbox("2. Nível da Regra (Hierarquia)", ["CLIENTE", "GRUPO", "REDE"], key="tab_tipo")
        
        col_t3, col_t4 = st.columns(2)
        
        if tipo_entidade == "CLIENTE":
            lista_entidades = df_clientes['nome'].tolist() if not df_clientes.empty else []
        elif tipo_entidade == "GRUPO":
            df_g = fetch_all("SELECT nome FROM grupos_clientes")
            lista_entidades = df_g['nome'].tolist() if not df_g.empty else []
        else:
            df_r = fetch_all("SELECT nome FROM redes_clientes")
            lista_entidades = df_r['nome'].tolist() if not df_r.empty else []
            
        entidade_nome = col_t3.selectbox("3. Vínculo (Selecione o Cliente/Grupo/Rede)", ["(Selecione)"] + lista_entidades, key="tab_ent")
        
        preco_tabela = col_t4.number_input("4. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco")
        
        st.markdown("##### Acordos e Rebates (%)")
        col_r1, col_r2, col_r3 = st.columns(3)
        pct_contrato = col_r1.number_input("% Contrato", min_value=0.0, step=0.1, value=0.0)
        pct_auxiliar = col_r2.number_input("% Comissões Auxiliares", min_value=0.0, step=0.1, value=0.0)
        pct_logistica = col_r3.number_input("% Acordo Logístico", min_value=0.0, step=0.1, value=0.0)
        
        if st.button("Salvar Tabela Ativa", type="primary"):
            if entidade_nome == "(Selecione)" or not lista_entidades:
                st.error("Selecione um vínculo válido.")
            else:
                prod_id = p_opts_tab[prod_selecionado]
                
                check_conflito = fetch_all("SELECT id FROM tabelas_preco WHERE produto_id=? AND tipo_entidade=? AND entidade_nome=? AND status='ATIVO'", 
                                           (prod_id, tipo_entidade, entidade_nome))
                
                if not check_conflito.empty:
                    st.error(f"🛑 ERRO: Já existe uma tabela ATIVA para {tipo_entidade} '{entidade_nome}' neste produto. Inative a tabela anterior primeiro no Histórico abaixo.")
                else:
                    run_query("INSERT INTO tabelas_preco (produto_id, tipo_entidade, entidade_nome, preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (prod_id, tipo_entidade, entidade_nome, preco_tabela, pct_contrato, pct_auxiliar, pct_logistica))
                    st.success("Tabela de Preços criada com sucesso!")
                    import time; time.sleep(1); st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Tabelas e Auditoria")
    df_tabelas = fetch_all('''
        SELECT t.id as ID, p.nome as Produto, t.tipo_entidade as Nível, t.entidade_nome as Vínculo, 
               t.preco as 'Preço (R$)', 
               t.pct_contrato as '% Contrato', t.pct_comissao_auxiliar as '% Auxiliar', t.pct_acordo_logistico as '% Logist',
               t.data_criacao as 'Data', t.status as Status
        FROM tabelas_preco t
        JOIN produtos p ON t.produto_id = p.id
        ORDER BY t.status ASC, t.id DESC
    ''')
    
    if not df_tabelas.empty:
        df_tabelas['Data'] = pd.to_datetime(df_tabelas['Data']).dt.strftime('%d/%m/%Y %H:%M')
        df_tabelas['Preço (R$)'] = df_tabelas['Preço (R$)'].apply(format_brl)
        
        def color_status(row):
            if row['Status'] == 'ATIVO': return ['background-color: #e6ffe6; color: black'] * len(row)
            return ['background-color: #ffe6e6; color: black'] * len(row)
            
        st.dataframe(df_tabelas.style.apply(color_status, axis=1), hide_index=True, width="stretch")
        
        with st.expander("🚫 Inativar Tabela Definitivamente"):
            st.markdown("Uma tabela inativada sai de circulação imediatamente, mas seu registro permanece para fins de auditoria antifraude.")
            opts_inativar = {}
            for _, r in df_tabelas[df_tabelas['Status'] == 'ATIVO'].iterrows():
                opts_inativar[f"ID {r['ID']} - {r['Vínculo']} ({r['Produto']})"] = r['ID']
                
            if opts_inativar:
                t_sel = st.selectbox("Selecione a tabela para inativar:", list(opts_inativar.keys()))
                if st.button("Inativar Regra", type="primary"):
                    run_query("UPDATE tabelas_preco SET status='INATIVO' WHERE id=?", (opts_inativar[t_sel],))
                    st.success("Tabela inativada! Ela não será mais sugerida nas novas vendas.")
                    import time; time.sleep(1); st.rerun()
            else:
                st.info("Nenhuma tabela ativa no momento.")
    else:
        st.info("Nenhuma tabela de preço customizada foi cadastrada ainda.")
