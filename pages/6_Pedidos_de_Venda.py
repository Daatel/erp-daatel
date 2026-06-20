import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
from database import run_query, fetch_all, gerar_comissao_se_necessario
from estilo import carregar_estilo

st.set_page_config(page_title="Pedidos de Venda", page_icon="📝", layout="wide")
carregar_estilo()

st.title("📝 Captação de Pedidos de Venda")
st.markdown("Registre a intenção de compra do cliente. **Atenção:** Isso gera apenas um Pedido em Aberto. A baixa de estoque e o título financeiro só ocorrem no módulo de **Faturamento**.")

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

df_clientes = fetch_all("SELECT id, nome, rede_clientes, prazo_pagamento, representante_id, forma_pagamento_id FROM clientes WHERE status='ATIVO'")
df_vendedores = fetch_all("SELECT id, nome, gatilho_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")
df_produtos = fetch_all("SELECT id, nome, preco_venda_base FROM produtos WHERE is_materia_prima = FALSE")
df_regras = fetch_all("SELECT vendedor_id, produto_id, rede_clientes, percentual FROM comissoes_regras")
df_fp = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")

tab1, tab_deg, tab2, tab_rastrear = st.tabs(["🛒 Lançar Novo Pedido", "🍇 Degustação & Amostras", "📋 Meus Pedidos Abertos", "🔍 Rastrear Pedido"])

# ======= 1. CAPTAÇÃO DE PEDIDO =======
with tab1:
    if 'carrinho_venda' not in st.session_state:
        st.session_state['carrinho_venda'] = []
    if 'carrinho_cliente_nome' not in st.session_state:
        st.session_state['carrinho_cliente_nome'] = None
    if 'carrinho_vendedor_nome' not in st.session_state:
        st.session_state['carrinho_vendedor_nome'] = None
    if 'carrinho_data' not in st.session_state:
        st.session_state['carrinho_data'] = None
    if 'carrinho_fp_id' not in st.session_state:
        st.session_state['carrinho_fp_id'] = None

    if df_clientes.empty or df_vendedores.empty or df_produtos.empty:
        st.warning("Cadastre Clientes, Vendedores e Produtos antes de iniciar as vendas!")
    else:
        carrinho_ativo = len(st.session_state['carrinho_venda']) > 0
        c_opts = {f"{r['nome']}": r for _, r in df_clientes.iterrows()}
        v_opts = {f"{r['nome']}": r for _, r in df_vendedores.iterrows()}
        
        col1, col2 = st.columns([1, 2])
        
        fp_opts = {r['nome']: r['id'] for _, r in df_fp.iterrows()} if not df_fp.empty else {}
        fp_list = list(fp_opts.keys())
        
        if carrinho_ativo:
            data_venda = col1.date_input("Data do Pedido", value=st.session_state['carrinho_data'], disabled=True)
            cliente_sel = col2.selectbox("Cliente Destino (Ativos)", list(c_opts.keys()), index=list(c_opts.keys()).index(st.session_state['carrinho_cliente_nome']), disabled=True)
            
            c_v1, c_v2 = st.columns(2)
            vendedor_sel = c_v1.selectbox("Vendedor / Representante", list(v_opts.keys()), index=list(v_opts.keys()).index(st.session_state['carrinho_vendedor_nome']), disabled=True)
            
            cur_fp_nome = ""
            if st.session_state.get('carrinho_fp_id'):
                df_cur_fp = df_fp[df_fp['id'] == int(st.session_state['carrinho_fp_id'])]
                if not df_cur_fp.empty:
                    cur_fp_nome = df_cur_fp.iloc[0]['nome']
            c_v2.selectbox("Forma de Pagamento acordada", [cur_fp_nome] if cur_fp_nome else ["(Padrão)"], disabled=True)
            st.info("💡 **Informação:** Para alterar o cliente, vendedor, forma de pagamento ou data do pedido, limpe o carrinho atual abaixo.")
        else:
            data_venda = col1.date_input("Data do Pedido", value=date.today())
            cliente_sel = col2.selectbox("Cliente Destino (Ativos)", list(c_opts.keys()))
            
            cli_selecionado = c_opts[cliente_sel]
            rep_id = cli_selecionado['representante_id']
            cli_fp_id = cli_selecionado['forma_pagamento_id']
            
            default_index = 0
            if pd.notna(rep_id) and not df_vendedores.empty:
                df_rep = df_vendedores[df_vendedores['id'] == int(rep_id)]
                if not df_rep.empty:
                    rep_nome = df_rep.iloc[0]['nome']
                    if rep_nome in v_opts:
                        default_index = list(v_opts.keys()).index(rep_nome)
                        
            c_v1, c_v2 = st.columns(2)
            vendedor_sel = c_v1.selectbox("Vendedor / Representante", list(v_opts.keys()), index=default_index)
            
            fp_default_index = 0
            if pd.notna(cli_fp_id) and not df_fp.empty:
                df_match_fp = df_fp[df_fp['id'] == int(cli_fp_id)]
                if not df_match_fp.empty:
                    fp_match_nome = df_match_fp.iloc[0]['nome']
                    if fp_match_nome in fp_opts:
                        fp_default_index = fp_list.index(fp_match_nome)
                        
            fp_sel = c_v2.selectbox("Forma de Pagamento acordada", fp_list, index=fp_default_index)
            st.session_state['carrinho_fp_id'] = fp_opts.get(fp_sel)
        
        st.markdown("##### Informações do Produto")
        col3, col4, col_tipo, col5 = st.columns([2, 1, 1.2, 1.2])
        p_opts = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
        produto_sel = col3.selectbox("Produto Final Solicitado", list(p_opts.keys()))
        qtd = col4.number_input("Quantidade Negociada (Volumes/Kg)", min_value=1.0, step=1.0)
        if carrinho_ativo:
            carrinho_tipo = st.session_state['carrinho_venda'][0]['tipo_item']
            tipo_item = col_tipo.selectbox("Tipo de Lançamento", ["Comercial (Venda)", "Bonificado (Bonificação)"], index=["Comercial (Venda)", "Bonificado (Bonificação)"].index(carrinho_tipo), disabled=True)
        else:
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
        
        if st.button("➕ Adicionar ao Pedido", type="secondary", use_container_width=True):
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
            
            st.session_state['carrinho_venda'].append({
                "produto_id": int(prod['id']),
                "produto_nome": produto_sel,
                "quantidade": float(qtd),
                "valor_unitario": float(preco),
                "valor_total": float(v_total),
                "tipo_item": tipo_item,
                "is_bonificacao": is_bonif,
                "comissao_valor": float(com_val),
                "custo_acordos_rede": float(custo_acordos)
            })
            
            st.session_state['carrinho_cliente_nome'] = cliente_sel
            st.session_state['carrinho_vendedor_nome'] = vendedor_sel
            st.session_state['carrinho_data'] = data_venda
            
            st.toast(f"✔️ {produto_sel} adicionado!", icon="🛒")
            st.rerun()

        # === EXIBIÇÃO DO CARRINHO ===
        if carrinho_ativo:
            st.markdown("---")
            st.markdown("### 🛒 Itens no Pedido Atual")
            
            col_h_prod, col_h_tipo, col_h_qtd, col_h_unit, col_h_tot, col_h_del = st.columns([3, 1.5, 1, 1.2, 1.2, 0.6])
            col_h_prod.markdown("**Produto**")
            col_h_tipo.markdown("**Tipo**")
            col_h_qtd.markdown("**Qtd**")
            col_h_unit.markdown("**Unitário**")
            col_h_tot.markdown("**Total**")
            col_h_del.markdown("**Ação**")
            
            para_remover = None
            for idx, item in enumerate(st.session_state['carrinho_venda']):
                c_prod, c_tipo, c_qtd, c_unit, c_tot, c_del = st.columns([3, 1.5, 1, 1.2, 1.2, 0.6])
                c_prod.write(item['produto_nome'])
                
                if item['is_bonificacao']:
                    c_tipo.markdown("<span style='background-color:#ffe6e6;color:#cc0000;padding:2px 6px;border-radius:4px;font-size:12px;'>🎁 Bonificação</span>", unsafe_allow_html=True)
                else:
                    c_tipo.markdown("<span style='background-color:#e6f7ff;color:#0050b3;padding:2px 6px;border-radius:4px;font-size:12px;'>🛒 Venda</span>", unsafe_allow_html=True)
                    
                c_qtd.write(f"{item['quantidade']:.0f} UN")
                c_unit.write(format_brl(item['valor_unitario']))
                c_tot.write(f"**{format_brl(item['valor_total'])}**")
                
                if c_del.button("🗑️", key=f"del_item_{idx}", help="Remover este item"):
                    para_remover = idx
                    
            if para_remover is not None:
                st.session_state['carrinho_venda'].pop(para_remover)
                if len(st.session_state['carrinho_venda']) == 0:
                    st.session_state['carrinho_cliente_nome'] = None
                    st.session_state['carrinho_vendedor_nome'] = None
                    st.session_state['carrinho_data'] = None
                st.toast("Item removido!", icon="🗑️")
                st.rerun()
                
            total_volumes = sum(item['quantidade'] for item in st.session_state['carrinho_venda'])
            total_pedido = sum(item['valor_total'] for item in st.session_state['carrinho_venda'])
            
            st.markdown("---")
            col_sum1, col_sum2 = st.columns([2, 1])
            with col_sum1:
                st.markdown("##### Resumo do Pedido de Venda")
                st.markdown(f"👤 **Cliente:** {st.session_state['carrinho_cliente_nome']}")
                st.markdown(f"💼 **Vendedor:** {st.session_state['carrinho_vendedor_nome']}")
                st.markdown(f"📅 **Data de Captação:** {st.session_state['carrinho_data'].strftime('%d/%m/%Y')}")
            with col_sum2:
                st.markdown(f"""
                <div style='background-color:#f9f9f9;padding:12px;border-radius:8px;border:1px solid #eee;text-align:right;'>
                    <span style='font-size:13px;color:#666;'>VALOR TOTAL DO PEDIDO</span><br>
                    <span style='font-size:22px;font-weight:bold;color:#292d77;'>{format_brl(total_pedido)}</span><br>
                    <span style='font-size:12px;color:#888;'>Volumes totais: {total_volumes:.0f} UN</span>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            col_action1, col_action2 = st.columns(2)
            
            if col_action1.button("🗑️ Esvaziar Pedido", type="secondary", use_container_width=True):
                st.session_state['carrinho_venda'] = []
                st.session_state['carrinho_cliente_nome'] = None
                st.session_state['carrinho_vendedor_nome'] = None
                st.session_state['carrinho_data'] = None
                st.session_state['carrinho_fp_id'] = None
                st.toast("Carrinho esvaziado!", icon="🗑️")
                st.rerun()
                
            if col_action2.button("🏁 Aprovar e Enviar Pedido Completo", type="primary", use_container_width=True):
                cli = c_opts[st.session_state['carrinho_cliente_nome']]
                ven = v_opts[st.session_state['carrinho_vendedor_nome']]
                data_v = st.session_state['carrinho_data']
                fp_id_val = st.session_state['carrinho_fp_id']
                
                vids_criados = []
                for item in st.session_state['carrinho_venda']:
                    run_query(
                        """INSERT INTO vendas 
                           (data, cliente_id, vendedor_id, produto_id, quantidade, valor_unitario, valor_total, comissao_valor, custo_acordos_rede, is_bonificacao, status, forma_pagamento_id) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APROVADO', ?)""",
                        (data_v.strftime("%Y-%m-%d"), cli['id'], ven['id'], item['produto_id'], item['quantidade'], item['valor_unitario'], item['valor_total'], item['comissao_valor'], item['custo_acordos_rede'], item['is_bonificacao'], fp_id_val)
                    )
                    v_id_df = fetch_all("SELECT MAX(id) as lg FROM vendas")
                    vids_criados.append(str(int(v_id_df.iloc[0]['lg'])))
                
                st.success(f"✔️ Pedido gravado com sucesso! Lançamentos de item (#{', #'.join(vids_criados)}) já estão na Fila do módulo de Faturamento aguardando expedição física.")
                
                st.session_state['carrinho_venda'] = []
                st.session_state['carrinho_cliente_nome'] = None
                st.session_state['carrinho_vendedor_nome'] = None
                st.session_state['carrinho_data'] = None
                st.session_state['carrinho_fp_id'] = None
                
                import time
                time.sleep(2)
                st.rerun()

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
                   VALUES (?, 'Saída', '2.2.1', ?, ?, ?, ?, TRUE)""",
                (data_acao.strftime("%Y-%m-%d"), desc_financeira, custo_total, banco_id, int(cli_deg['id']))
            )
            
            st.success(f"✔️ Remessa registrada com sucesso! Saída física executada via FIFO.")
            st.info(f"📊 **Custo Real FIFO apurado:** R$ {custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            if is_estimado:
                st.warning("⚠️ **Atenção:** O estoque físico no sistema estava insuficiente/zerado. O custo foi estimado provisoriamente usando o custo de cadastro do produto.")
            st.rerun()

# ======= 2. GESTÃO DE PEDIDOS =======
with tab2:
    st.subheader("📋 Gestão e Acompanhamento de Pedidos")
    st.markdown("Acompanhe o andamento dos seus pedidos. Utilize os filtros para separar rapidamente os pendentes de faturamento.")
    
    # Inicializar datas no session state se não existirem
    if 'vendas_dt_inicio' not in st.session_state:
        st.session_state['vendas_dt_inicio'] = date.today() - timedelta(days=30)
    if 'vendas_dt_fim' not in st.session_state:
        st.session_state['vendas_dt_fim'] = date.today()

    st.markdown("##### 📅 Filtro por Período de Captação")
    col_b1, col_b2, col_b3, _ = st.columns([1, 1.3, 1.3, 4.4])
    if col_b1.button("📅 Hoje", use_container_width=True, key="btn_vendas_hoje"):
        st.session_state['vendas_dt_inicio'] = date.today()
        st.session_state['vendas_dt_fim'] = date.today()
        st.rerun()
    if col_b2.button("📅 Últimos 7 Dias", use_container_width=True, key="btn_vendas_7d"):
        st.session_state['vendas_dt_inicio'] = date.today() - timedelta(days=7)
        st.session_state['vendas_dt_fim'] = date.today()
        st.rerun()
    if col_b3.button("📅 Últimos 30 Dias", use_container_width=True, key="btn_vendas_30d"):
        st.session_state['vendas_dt_inicio'] = date.today() - timedelta(days=30)
        st.session_state['vendas_dt_fim'] = date.today()
        st.rerun()

    # Filtros interativos
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    
    dt_inicio = col_f1.date_input("Data de Início", value=st.session_state['vendas_dt_inicio'], key="vendas_dt_inicio_input")
    dt_fim = col_f2.date_input("Data de Fim", value=st.session_state['vendas_dt_fim'], key="vendas_dt_fim_input")
    
    # Sincronizar de volta
    st.session_state['vendas_dt_inicio'] = dt_inicio
    st.session_state['vendas_dt_fim'] = dt_fim

    filtro_status = col_f3.radio(
        "Filtrar por Situação:",
        ["Todos", "🟡 Pendentes de Faturamento", "🟢 Faturados"],
        horizontal=True,
        key="filtro_vendas_gestao"
    )
    
    query_pedidos = '''
        SELECT v.id as 'Pedido', v.data as 'Data Captação', c.nome as 'Cliente', 
               vn.nome as 'Vendedor', p.nome as 'Carga', v.quantidade as 'Qtd', 
               v.valor_total as 'Valor Total', v.status as 'Status do Pedido',
               v.tipo_documento, v.numero_documento
        FROM vendas v 
        JOIN clientes c ON v.cliente_id=c.id
        JOIN funcionarios vn ON v.vendedor_id=vn.id
        JOIN produtos p ON v.produto_id=p.id
        WHERE v.data BETWEEN ? AND ?
    '''
    
    if filtro_status == "🟡 Pendentes de Faturamento":
        query_pedidos += " AND v.status = 'APROVADO'"
    elif filtro_status == "🟢 Faturados":
        query_pedidos += " AND v.status = 'FATURADO'"
        
    query_pedidos += " ORDER BY v.id DESC"
    
    df_pedidos = fetch_all(query_pedidos, (dt_inicio.strftime("%Y-%m-%d"), dt_fim.strftime("%Y-%m-%d")))
    
    if not df_pedidos.empty:
        df_pedidos['Data Captação'] = pd.to_datetime(df_pedidos['Data Captação'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_pedidos['Valor Total'] = df_pedidos['Valor Total'].apply(format_brl)
        
        def format_status_badge(row):
            status = row['Status do Pedido']
            tipo = row['tipo_documento'] or "Nota Fiscal (NF)"
            num = row['numero_documento']
            
            if status == 'APROVADO':
                return "🟡 Pendente (Aguardando Faturamento)"
            elif status == 'FATURADO':
                if "DAV" in tipo:
                    num_str = str(num).zfill(10) if num else str(row['Pedido'])
                    return f"🟢 Faturado (DAV #{num_str})"
                else:
                    return f"🟢 Faturado (NF-e #{num})" if (num and str(num).strip() != "") else "🟢 Faturado (NF-e Sem Número SEFAZ)"
            return status
            
        df_pedidos['Situação do Pedido'] = df_pedidos.apply(format_status_badge, axis=1)
        
        def highlight_status(row):
            status = df_pedidos.loc[row.name, 'Status do Pedido']
            if status == 'APROVADO':
                return ['background-color: #fff9e6; color: #856404'] * len(row) # Amarelo escuro elegante
            elif status == 'FATURADO':
                return ['background-color: #ebfaf0; color: #155724'] * len(row) # Verde elegante
            return [''] * len(row)
            
        df_exibir = df_pedidos[['Pedido', 'Data Captação', 'Cliente', 'Vendedor', 'Carga', 'Qtd', 'Valor Total', 'Situação do Pedido']]
        st.dataframe(df_exibir.style.apply(highlight_status, axis=1), hide_index=True, width="stretch")
        
        # ======= CENTRAL DE ALTERAÇÕES E CANCELAMENTO =======
        st.markdown("---")
        st.subheader("🛠️ Central de Correções e Cancelamento (Apenas Pedidos Pendentes)")
        
        # Filtra apenas vendas da lista obtida cujo status real seja 'APROVADO'
        # Buscamos diretamente do banco para garantir consistência
        df_aprovados_raw = fetch_all("SELECT v.id, c.nome as cliente, p.nome as produto FROM vendas v JOIN clientes c ON v.cliente_id=c.id JOIN produtos p ON v.produto_id=p.id WHERE v.status='APROVADO'")
        
        if df_aprovados_raw.empty:
            st.info("Nenhum pedido pendente de faturamento (Aguardando Estoque) disponível para edição ou cancelamento no momento.")
        else:
            opts_aprovados = {f"Pedido #{r['id']} - {r['cliente']} ({r['produto']})": r['id'] for _, r in df_aprovados_raw.iterrows()}
            venda_sel_id = st.selectbox("Selecione o pedido pendente para corrigir ou cancelar:", ["-- SELECIONE --"] + list(opts_aprovados.keys()), key="sel_venda_corrigir")
            
            if venda_sel_id != "-- SELECIONE --":
                v_id = opts_aprovados[venda_sel_id]
                
                # Puxa informações detalhadas dessa venda
                v_det = fetch_all('''
                    SELECT v.id, v.quantidade, v.valor_unitario, v.valor_total, v.vendedor_id, v.produto_id, v.cliente_id,
                           p.nome as produto, c.nome as cliente
                    FROM vendas v
                    JOIN produtos p ON v.produto_id = p.id
                    JOIN clientes c ON v.cliente_id = c.id
                    WHERE v.id = ?
                ''', (v_id,)).iloc[0]
                
                col_c1, col_c2 = st.columns(2)
                
                with col_c1:
                    st.markdown("#### ✍️ Editar Quantidade ou Preço")
                    new_qtd = st.number_input("Nova Quantidade (UN/Kg):", min_value=1.0, value=float(v_det['quantidade']), step=1.0, key=f"edit_qtd_{v_id}")
                    new_price = st.number_input("Novo Preço Unitário (R$):", min_value=0.0, value=float(v_det['valor_unitario']), step=0.1, key=f"edit_preco_{v_id}")
                    
                    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True, key=f"btn_save_edit_{v_id}"):
                        new_total = new_qtd * new_price
                        
                        # Recalcular comissão dinamicamente baseado na regra cadastrada
                        # 1. Puxar percentual de comissão
                        df_regras_venda = fetch_all("SELECT percentual FROM comissoes_regras WHERE vendedor_id=? AND produto_id=?", (v_det['vendedor_id'], v_det['produto_id']))
                        if df_regras_venda.empty:
                            # Tentar regra geral
                            df_regras_venda = fetch_all("SELECT percentual FROM comissoes_regras WHERE vendedor_id=? AND produto_id IS NULL", (v_det['vendedor_id'],))
                        
                        comissao_perc = float(df_regras_venda.iloc[0]['percentual']) if not df_regras_venda.empty else 0.0
                        new_comissao = new_total * (comissao_perc / 100.0)
                        
                        # Recalcular acordos comerciais
                        df_tabela_acordos = fetch_all('''
                            SELECT pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico 
                            FROM tabelas_preco 
                            WHERE produto_id = ? AND status = 'ATIVO' 
                              AND (entidade_nome = ? OR entidade_nome = (SELECT rede_clientes FROM clientes WHERE id = ?))
                            LIMIT 1
                        ''', (v_det['produto_id'], v_det['cliente'], v_det['cliente_id']))
                        
                        pct_contrato = float(df_tabela_acordos.iloc[0]['pct_contrato'] or 0.0) if not df_tabela_acordos.empty else 0.0
                        pct_auxiliar = float(df_tabela_acordos.iloc[0]['pct_comissao_auxiliar'] or 0.0) if not df_tabela_acordos.empty else 0.0
                        pct_logist = float(df_tabela_acordos.iloc[0]['pct_acordo_logistico'] or 0.0) if not df_tabela_acordos.empty else 0.0
                        
                        new_acordos = new_total * (pct_contrato + pct_auxiliar + pct_logist) / 100.0
                        
                        # Executa atualização no banco
                        run_query('''
                            UPDATE vendas 
                            SET quantidade = ?, valor_unitario = ?, valor_total = ?, comissao_valor = ?, custo_acordos_rede = ?
                            WHERE id = ?
                        ''', (new_qtd, new_price, new_total, new_comissao, new_acordos, v_id))
                        
                        st.success(f"✅ Pedido #{v_id} atualizado com sucesso! Novo total: {format_brl(new_total)}")
                        import time; time.sleep(1.5); st.rerun()
                        
                with col_c2:
                    st.markdown("#### ❌ Cancelamento Definitivo")
                    st.markdown(f"Tem certeza que deseja cancelar o **Pedido #{v_id}** do cliente **{v_det['cliente']}**?")
                    st.warning("Isso removerá o pedido da fila de faturamento permanentemente, arquivando-o com a marca de cancelamento.")
                    
                    if st.button("❌ Cancelar Pedido Permanentemente", type="primary", use_container_width=True, key=f"btn_cancel_{v_id}"):
                        run_query("UPDATE vendas SET status = 'CANCELADO' WHERE id = ?", (v_id,))
                        st.success(f"🛑 Pedido #{v_id} cancelado com sucesso!")
                        import time; time.sleep(1.5); st.rerun()
    else:
        st.info("Nenhum pedido registrado no banco de dados para este filtro.")

# ======= 3. RASTREADOR VISUAL DE PEDIDOS =======
with tab_rastrear:
    st.subheader("🔍 Rastreador Visual de Linha do Tempo do Pedido")
    st.markdown("Busque e rastreie o andamento do ciclo de vida de qualquer venda registrada no ERP em tempo real.")

    df_vendas_todas = fetch_all('''
        SELECT v.id, c.nome as cliente_nome
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.id DESC LIMIT 100
    ''')

    if df_vendas_todas.empty:
        st.info("Nenhum pedido cadastrado no sistema para ser rastreado.")
    else:
        venda_opcoes = {f"Pedido #{r['id']} - {r['cliente_nome']}": r['id'] for _, r in df_vendas_todas.iterrows()}
        pedido_sel = st.selectbox("Selecione um pedido recente para rastrear:", ["-- SELECIONE --"] + list(venda_opcoes.keys()))
        
        def exibir_stepper(etapa_atual):
            etapas = [
                {"nome": "Captação", "icon": "📝", "desc": "Pedido Comercial"},
                {"nome": "Faturamento", "icon": "📦", "desc": "Estoque & Financeiro"},
                {"nome": "Expedição", "icon": "🚛", "desc": "Carga Despachada"},
                {"nome": "Entregue", "icon": "🏁", "desc": "Canhoto Confirmado"}
            ]
            
            html = '<div style="display: flex; justify-content: space-between; align-items: center; padding: 25px 10px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;">'
            for i, et in enumerate(etapas):
                num = i + 1
                is_completed = num <= etapa_atual
                is_active = num == etapa_atual
                
                if is_active:
                    bg_color = "#292d77"
                    text_color = "#ffffff"
                    border_style = "border: 2px solid #292d77; box-shadow: 0 0 10px rgba(41, 45, 119, 0.4);"
                    label_color = "#292d77"
                elif is_completed:
                    bg_color = "#01743d"
                    text_color = "#ffffff"
                    border_style = "border: 2px solid #01743d;"
                    label_color = "#01743d"
                else:
                    bg_color = "#f1f3f5"
                    text_color = "#adb5bd"
                    border_style = "border: 2px dashed #dee2e6;"
                    label_color = "#6c757d"
                    
                html += f'''
                <div style="flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; text-align: center;">
                    <div style="width: 50px; height: 50px; border-radius: 50%; background: {bg_color}; color: {text_color}; display: flex; justify-content: center; align-items: center; font-size: 20px; {border_style} font-weight: bold; transition: all 0.3s ease;">
                        {et['icon']}
                    </div>
                    <div style="margin-top: 10px; font-weight: bold; color: {label_color}; font-size: 13px;">{et['nome']}</div>
                    <div style="font-size: 11px; color: #868e96; margin-top: 2px; padding: 0 5px;">{et['desc']}</div>
                </div>
                '''
                
                if i < 3:
                    line_color = "#01743d" if (num < etapa_atual) else "#dee2e6"
                    line_style = "solid" if (num < etapa_atual) else "dashed"
                    html += f'''
                    <div style="flex: 1.5; height: 4px; background: {line_color}; border-top: 1px {line_style} {line_color}; margin-top: -30px; transition: all 0.3s ease;"></div>
                    '''
                    
            html += '</div>'
            return html

        if pedido_sel != "-- SELECIONE --":
            vid = venda_opcoes[pedido_sel]
            
            # Puxa informações detalhadas do pedido
            df_det = fetch_all('''
                SELECT v.id, v.data, v.status, v.tipo_documento, v.numero_documento,
                       v.valor_total, v.comprovante_url,
                       c.nome as cliente, c.cidade, c.uf,
                       vn.nome as vendedor,
                       p.nome as produto, v.quantidade,
                       v.manifesto_id,
                       m.motorista_nome, m.placa_veiculo, m.status as manifesto_status, m.data_saida
                FROM vendas v
                JOIN clientes c ON v.cliente_id = c.id
                JOIN funcionarios vn ON v.vendedor_id = vn.id
                JOIN produtos p ON v.produto_id = p.id
                LEFT JOIN manifestos_carga m ON v.manifesto_id = m.id
                WHERE v.id = ?
            ''', (vid,))
            
            if not df_det.empty:
                row = df_det.iloc[0]
                
                comprovante = row['comprovante_url']
                has_comprovante = comprovante and str(comprovante).strip() != ""
                manifesto_status = row['manifesto_status']
                is_delivered = has_comprovante or (manifesto_status == 'CONCLUÍDO (CANHOTOS OK)')
                
                if is_delivered:
                    etapa = 4
                elif row['manifesto_id'] is not None:
                    etapa = 3
                elif row['status'] == 'FATURADO':
                    etapa = 2
                else:
                    etapa = 1
                    
                # Renderiza stepper visual
                st.markdown(exibir_stepper(etapa), unsafe_allow_html=True)
                
                # Detalhes em cards estruturados
                st.markdown("#### 📋 Histórico do Ciclo de Vida do Pedido")
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    st.markdown(f"""
                    <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #dee2e6;min-height:220px;'>
                        <h5 style='color:#292d77;margin-top:0;'>🛒 Detalhes Comerciais</h5>
                        <b>Pedido ID:</b> #{row['id']}<br>
                        <b>Cliente:</b> {row['cliente']} ({row['cidade']} - {row['uf']})<br>
                        <b>Produto Comercial:</b> {row['produto']} (x {row['quantidade']:.0f} UN)<br>
                        <b>Vendedor:</b> {row['vendedor']}<br>
                        <b>Data de Captação:</b> {pd.to_datetime(row['data']).strftime('%d/%m/%Y')}<br><br>
                        <span style='font-size:16px;font-weight:bold;color:#01743d;'>Total: R$ {row['valor_total']:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_t2:
                    # Construção dos detalhes das etapas
                    etapa_detalhes = []
                    
                    # Etapa 1: Captação
                    etapa_detalhes.append(f"🟢 **[Etapa 1] Captação:** Pedido registrado e aprovado comercialmente em {pd.to_datetime(row['data']).strftime('%d/%m/%Y')} pelo vendedor {row['vendedor']}.")
                    
                    # Etapa 2: Faturamento
                    if etapa >= 2:
                        tipo = row['tipo_documento'] or "Nota Fiscal (NF)"
                        num = row['numero_documento']
                        if "DAV" in tipo:
                            doc_label = f"DAV #{str(num).zfill(10)}" if num else f"DAV #{row['id']}"
                        else:
                            doc_label = f"NF-e #{num}" if (num and str(num).strip() != "") else "NF-e (Pendente de número SEFAZ)"
                        etapa_detalhes.append(f"🟢 **[Etapa 2] Faturamento:** Baixado do estoque físico e faturado como **{doc_label}**.")
                    else:
                        etapa_detalhes.append("⏳ **[Etapa 2] Faturamento:** Pendente na Fila de Faturamento. Aguardando baixa física do estoque.")
                        
                    # Etapa 3: Roteirização
                    if etapa >= 3:
                        dt_s = pd.to_datetime(row['data_saida']).strftime('%d/%m/%Y') if row['data_saida'] else "Em trânsito"
                        etapa_detalhes.append(f"🟢 **[Etapa 3] Expedição:** Despachado no manifesto **#{row['manifesto_id']}** em {dt_s}. Motorista: **{row['motorista_nome']}** | Placa: **{row['placa_veiculo']}**.")
                    else:
                        etapa_detalhes.append("⏳ **[Etapa 3] Expedição:** Aguardando roteirização no galpão.")
                        
                    # Etapa 4: Entrega
                    if etapa >= 4:
                        etapa_detalhes.append("🟢 **[Etapa 4] Entrega:** Carga entregue e canhoto físico assinado/confirmado pelo motorista no galpão.")
                    else:
                        etapa_detalhes.append("⏳ **[Etapa 4] Entrega:** Aguardando encerramento da viagem e upload do comprovante.")
                        
                    detalhes_str = "<br><br>".join(etapa_detalhes)
                    st.markdown(f"""
                    <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #dee2e6;font-size:12.5px;min-height:220px;line-height:1.4;'>
                        <h5 style='color:#01743d;margin-top:0;'>⚙️ Rastreabilidade de Etapas</h5>
                        {detalhes_str}
                    </div>
                    """, unsafe_allow_html=True)


