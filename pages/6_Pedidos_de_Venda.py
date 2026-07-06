# Rebuild trigger: 2026-07-06 07:22
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io
from database import run_query, fetch_all, db_transaction, run_query_tx, fetch_all_tx
from estilo import carregar_estilo

st.set_page_config(page_title="Pedidos de Venda", layout="wide")
carregar_estilo()

# Custom CSS matching the finance visual style and padding
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
</style>
<h1 style='font-size: 2.2rem; font-weight: 700; margin-top: -15px; margin-bottom: 20px; color: #1e293b;'>
Pedidos de Venda
</h1>
""", unsafe_allow_html=True)

# Fetch master data
df_clientes = fetch_all("SELECT id, nome, nome_fantasia, rede_clientes, prazo_pagamento, representante_id, forma_pagamento_id FROM clientes WHERE status='ATIVO'")
df_vendedores = fetch_all("SELECT id, nome, gatilho_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")
df_produtos = fetch_all("SELECT id, nome, preco_venda_base FROM produtos WHERE is_materia_prima = FALSE")
df_regras = fetch_all("SELECT vendedor_id, produto_id, rede_clientes, percentual FROM comissoes_regras")
df_fp = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")

# Helper to format BRL currency
def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Dialog: Lançar Novo Pedido
@st.dialog("Lançar Novo Pedido", width="large")
def modal_lancar_pedido():
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
        return

    carrinho_ativo = len(st.session_state['carrinho_venda']) > 0
    c_opts = {f"{r['nome_fantasia'] or r['nome']}": r for _, r in df_clientes.iterrows()}
    v_opts = {f"{r['nome']}": r for _, r in df_vendedores.iterrows()}
    fp_opts = {r['nome']: r['id'] for _, r in df_fp.iterrows()} if not df_fp.empty else {}
    fp_list = list(fp_opts.keys())

    col1, col2 = st.columns([1, 2])
    if carrinho_ativo:
        data_venda = col1.date_input("Data do Pedido", value=st.session_state['carrinho_data'], disabled=True)
        cliente_sel = col2.selectbox("Cliente Destino", list(c_opts.keys()), index=list(c_opts.keys()).index(st.session_state['carrinho_cliente_nome']), disabled=True)
        
        c_v1, c_v2 = st.columns(2)
        vendedor_sel = c_v1.selectbox("Vendedor / Representante", list(v_opts.keys()), index=list(v_opts.keys()).index(st.session_state['carrinho_vendedor_nome']), disabled=True)
        
        cur_fp_nome = ""
        if st.session_state.get('carrinho_fp_id'):
            df_cur_fp = df_fp[df_fp['id'] == int(st.session_state['carrinho_fp_id'])]
            if not df_cur_fp.empty:
                cur_fp_nome = df_cur_fp.iloc[0]['nome']
        c_v2.selectbox("Forma de Pagamento", [cur_fp_nome] if cur_fp_nome else ["(Padrão)"], disabled=True)
    else:
        data_venda = col1.date_input("Data do Pedido", value=date.today())
        cliente_sel = col2.selectbox("Cliente Destino", list(c_opts.keys()))
        
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
        else:
            venda_direta_matches = [name for name in v_opts.keys() if "VENDA DIRETA" in name.upper()]
            if venda_direta_matches:
                default_index = list(v_opts.keys()).index(venda_direta_matches[0])
                    
        c_v1, c_v2 = st.columns(2)
        vendedor_sel = c_v1.selectbox("Vendedor / Representante", list(v_opts.keys()), index=default_index)
        
        fp_default_index = 0
        if pd.notna(cli_fp_id) and not df_fp.empty:
            df_match_fp = df_fp[df_fp['id'] == int(cli_fp_id)]
            if not df_match_fp.empty:
                fp_match_nome = df_match_fp.iloc[0]['nome']
                if fp_match_nome in fp_opts:
                    fp_default_index = fp_list.index(fp_match_nome)
                    
        fp_sel = c_v2.selectbox("Forma de Pagamento", fp_list, index=fp_default_index)
        st.session_state['carrinho_fp_id'] = fp_opts.get(fp_sel)

    st.markdown("##### Informações do Produto")
    col3, col4, col_tipo, col5 = st.columns([2, 1, 1.2, 1.2])
    p_opts = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
    produto_sel = col3.selectbox("Produto", list(p_opts.keys()))
    qtd = col4.number_input("Quantidade", min_value=1.0, step=1.0)
    if carrinho_ativo:
        carrinho_tipo = st.session_state['carrinho_venda'][0]['tipo_item']
        tipo_item = col_tipo.selectbox("Tipo", ["Venda", "Bonificação"], index=["Venda", "Bonificação"].index(carrinho_tipo), disabled=True)
    else:
        tipo_item = col_tipo.selectbox("Tipo", ["Venda", "Bonificação"])

    # Precificação Dinâmica
    cli_selecionado = c_opts[cliente_sel]
    nome_cliente = cli_selecionado['nome']
    df_cli_grp = fetch_all("SELECT grupo_lojas FROM clientes WHERE id=?", (cli_selecionado['id'],))
    grupo_cliente = df_cli_grp.iloc[0]['grupo_lojas'] if not df_cli_grp.empty else None
    rede_cliente = cli_selecionado['rede_clientes']
    prod_id = p_opts[produto_sel]['id']
    
    preco_tabela = None
    pct_contrato = 0.0
    pct_auxiliar = 0.0
    pct_logistica = 0.0
    
    tb_cli = fetch_all("SELECT preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='CLIENTE' AND entidade_nome=? AND status='ATIVO'", (prod_id, nome_cliente))
    if not tb_cli.empty:
        preco_tabela = float(tb_cli.iloc[0]['preco'])
        pct_contrato = float(tb_cli.iloc[0]['pct_contrato'] or 0.0)
        pct_auxiliar = float(tb_cli.iloc[0]['pct_comissao_auxiliar'] or 0.0)
        pct_logistica = float(tb_cli.iloc[0]['pct_acordo_logistico'] or 0.0)
    else:
        if grupo_cliente:
            tb_grp = fetch_all("SELECT preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='GRUPO' AND entidade_nome=? AND status='ATIVO'", (prod_id, grupo_cliente))
            if not tb_grp.empty:
                preco_tabela = float(tb_grp.iloc[0]['preco'])
                pct_contrato = float(tb_grp.iloc[0]['pct_contrato'] or 0.0)
                pct_auxiliar = float(tb_grp.iloc[0]['pct_comissao_auxiliar'] or 0.0)
                pct_logistica = float(tb_grp.iloc[0]['pct_acordo_logistico'] or 0.0)
        
        if preco_tabela is None and rede_cliente:
            tb_red = fetch_all("SELECT preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='REDE' AND entidade_nome=? AND status='ATIVO'", (prod_id, rede_cliente))
            if not tb_red.empty:
                preco_tabela = float(tb_red.iloc[0]['preco'])
                pct_contrato = float(tb_red.iloc[0]['pct_contrato'] or 0.0)
                pct_auxiliar = float(tb_red.iloc[0]['pct_comissao_auxiliar'] or 0.0)
                pct_logistica = float(tb_red.iloc[0]['pct_acordo_logistico'] or 0.0)
                
    if preco_tabela is None:
        preco_tabela = float(p_opts[produto_sel]['preco_venda_base'])
        
    if tipo_item == "Bonificação":
        preco_tabela = 0.0
        preco = col5.number_input("Preço Unitário", min_value=0.0, max_value=0.0, value=0.0, disabled=True, key="preco_bonif")
    else:
        preco = col5.number_input("Preço Unitário", min_value=0.0, value=preco_tabela, step=0.1, key="preco_venda")
    
    st.markdown("---")
    flag_op_casada = st.checkbox("Operação Casada (ex: Horta do Príncipe para Atacadão)")
    filial_atacadao = ""
    pedido_atacadao_numero = ""
    if flag_op_casada:
        col_op1, col_op2 = st.columns(2)
        filial_atacadao = col_op1.text_input("Filial Destino (Atacadão):", placeholder="Ex: Niterói")
        pedido_atacadao_numero = col_op2.text_input("Nº Pedido Interno (Grade Atacadão):", placeholder="Ex: 88231")

    if st.button("Adicionar ao Pedido", type="secondary", use_container_width=True):
        cli = c_opts[cliente_sel]
        ven = v_opts[vendedor_sel]
        prod = p_opts[produto_sel]
        v_total = qtd * preco
        
        # Comissão Dinâmica
        comissao_perc = 0.0
        if not df_regras.empty:
            rede_c = cli['rede_clientes'] if cli['rede_clientes'] else "TODOS"
            rc = df_regras[(df_regras['vendedor_id'] == ven['id']) & (df_regras['rede_clientes'] == rede_c)]
            if not rc.empty:
                rc_p = rc[(rc['produto_id'] == prod['id'])]
                if not rc_p.empty:
                    comissao_perc = rc_p.iloc[0]['percentual']
                else:
                    rc_todos = rc[rc['produto_id'].isna()]
                    if not rc_todos.empty:
                        comissao_perc = rc_todos.iloc[0]['percentual']
                        
        com_val = v_total * (comissao_perc / 100.0)
        custo_acordos = v_total * (pct_contrato + pct_auxiliar + pct_logistica) / 100.0
        is_bonif = (tipo_item == "Bonificação")
        
        st.session_state['carrinho_venda'].append({
            "produto_id": int(prod['id']),
            "produto_name": produto_sel,
            "quantidade": float(qtd),
            "valor_unitario": float(preco),
            "valor_total": float(v_total),
            "tipo_item": tipo_item,
            "is_bonificacao": is_bonif,
            "comissao_valor": float(com_val),
            "custo_acordos_rede": float(custo_acordos),
            "flag_op_casada": flag_op_casada,
            "filial_atacadao": filial_atacadao,
            "pedido_atacadao_numero": pedido_atacadao_numero
        })
        st.session_state['carrinho_cliente_nome'] = cliente_sel
        st.session_state['carrinho_vendedor_nome'] = vendedor_sel
        st.session_state['carrinho_data'] = data_venda
        st.toast(f"Item {produto_sel} adicionado!", icon="✅")
        st.rerun()

    # Exibição do carrinho
    if carrinho_ativo:
        st.markdown("---")
        st.markdown("##### Itens no Pedido Atual")
        for idx, item in enumerate(st.session_state['carrinho_venda']):
            c_prod, c_tipo, c_qtd, c_tot, c_del = st.columns([3, 1.5, 1, 1.5, 0.6])
            c_prod.write(item['produto_name'])
            c_tipo.write("Bonificação" if item['is_bonificacao'] else "Venda")
            c_qtd.write(f"{item['quantidade']:.0f} UN")
            c_tot.write(format_brl(item['valor_total']))
            if c_del.button("Remover", key=f"del_modal_{idx}"):
                st.session_state['carrinho_venda'].pop(idx)
                if len(st.session_state['carrinho_venda']) == 0:
                    st.session_state['carrinho_cliente_nome'] = None
                    st.session_state['carrinho_vendedor_nome'] = None
                    st.session_state['carrinho_data'] = None
                st.rerun()
                
        total_pedido = sum(item['valor_total'] for item in st.session_state['carrinho_venda'])
        st.markdown(f"**Total do Pedido: {format_brl(total_pedido)}**")
        
        col_action1, col_action2 = st.columns(2)
        if col_action1.button("Limpar Tudo", use_container_width=True):
            st.session_state['carrinho_venda'] = []
            st.session_state['carrinho_cliente_nome'] = None
            st.session_state['carrinho_vendedor_nome'] = None
            st.session_state['carrinho_data'] = None
            st.session_state['carrinho_fp_id'] = None
            st.rerun()
            
        if col_action2.button("Aprovar e Gravar Pedido", type="primary", use_container_width=True):
            cli = c_opts[st.session_state['carrinho_cliente_nome']]
            ven = v_opts[st.session_state['carrinho_vendedor_nome']]
            data_v = st.session_state['carrinho_data']
            fp_id_val = st.session_state['carrinho_fp_id']
            
            df_max = fetch_all("SELECT MAX(id) as max_id FROM vendas")
            next_group_id = int(df_max.iloc[0]['max_id']) + 1 if not df_max.empty and pd.notna(df_max.iloc[0]['max_id']) else 1
            pedido_grupo_val = str(next_group_id)
            
            for item in st.session_state['carrinho_venda']:
                run_query(
                    """INSERT INTO vendas 
                       (data, cliente_id, vendedor_id, produto_id, quantidade, valor_unitario, valor_total, 
                        comissao_valor, custo_acordos_rede, is_bonificacao, status, forma_pagamento_id, 
                        flag_op_casada, filial_atacadao, pedido_atacadao_numero, pedido_grupo) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APROVADO', ?, ?, ?, ?, ?)""",
                    (data_v.strftime("%Y-%m-%d"), cli['id'], ven['id'], item['produto_id'], 
                     item['quantidade'], item['valor_unitario'], item['valor_total'], item['comissao_valor'], 
                     item['custo_acordos_rede'], item['is_bonificacao'], fp_id_val, 
                     item.get('flag_op_casada', False), item.get('filial_atacadao', ''), 
                     item.get('pedido_atacadao_numero', ''), pedido_grupo_val)
                )
            
            st.session_state['carrinho_venda'] = []
            st.session_state['carrinho_cliente_nome'] = None
            st.session_state['carrinho_vendedor_nome'] = None
            st.session_state['carrinho_data'] = None
            st.session_state['carrinho_fp_id'] = None
            st.toast("Pedido gravado com sucesso!", icon="✅")
            st.rerun()

# Dialog: Editar Pedido
@st.dialog("Editar Pedido")
def modal_editar_pedido(v_id):
    v_det = fetch_all('''
        SELECT v.id, v.quantidade, v.valor_unitario, v.vendedor_id, v.produto_id, v.cliente_id,
               v.forma_pagamento_id, v.flag_op_casada, v.filial_atacadao, v.pedido_atacadao_numero, p.nome as produto, c.nome as cliente
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.id = ?
    ''', (v_id,)).iloc[0]

    st.markdown(f"**Pedido #{v_id} | {v_det['cliente']}**")
    st.write(f"Produto: {v_det['produto']}")
    
    new_qtd = st.number_input("Nova Quantidade:", min_value=1.0, value=float(v_det['quantidade']), step=1.0)
    new_price = st.number_input("Novo Preço Unitário (R$):", min_value=0.0, value=float(v_det['valor_unitario']), step=0.1)
    
    fp_opts_edit = {r['nome']: r['id'] for _, r in df_fp.iterrows()} if not df_fp.empty else {}
    fp_list_edit = list(fp_opts_edit.keys())
    current_fp_id = v_det['forma_pagamento_id']
    fp_default_index = 0
    if pd.notna(current_fp_id) and not df_fp.empty:
        df_match = df_fp[df_fp['id'] == int(current_fp_id)]
        if not df_match.empty and df_match.iloc[0]['nome'] in fp_opts_edit:
            fp_default_index = fp_list_edit.index(df_match.iloc[0]['nome'])
            
    new_fp_sel = st.selectbox("Nova Forma de Pagamento:", fp_list_edit, index=fp_default_index)
    new_fp_id = fp_opts_edit.get(new_fp_sel)
    
    edit_op_casada = st.checkbox("Operação Casada", value=bool(v_det.get('flag_op_casada')))
    edit_filial = ""
    edit_pedido_int = ""
    if edit_op_casada:
        edit_filial = st.text_input("Filial Destino:", value=v_det.get('filial_atacadao') or "")
        edit_pedido_int = st.text_input("Nº Pedido Interno:", value=v_det.get('pedido_atacadao_numero') or "")

    if st.button("Salvar Alterações", type="primary", use_container_width=True):
        new_total = new_qtd * new_price
        
        # Recalcular comissão
        df_regras_venda = fetch_all("SELECT percentual FROM comissoes_regras WHERE vendedor_id=? AND produto_id=?", (v_det['vendedor_id'], v_det['produto_id']))
        if df_regras_venda.empty:
            df_regras_venda = fetch_all("SELECT percentual FROM comissoes_regras WHERE vendedor_id=? AND produto_id IS NULL", (v_det['vendedor_id'],))
        comissao_perc = float(df_regras_venda.iloc[0]['percentual']) if not df_regras_venda.empty else 0.0
        new_comissao = new_total * (comissao_perc / 100.0)
        
        # Recalcular acordos
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
        
        run_query('''
            UPDATE vendas 
            SET quantidade = ?, valor_unitario = ?, valor_total = ?, comissao_valor = ?, custo_acordos_rede = ?, forma_pagamento_id = ?, flag_op_casada = ?, filial_atacadao = ?, pedido_atacadao_numero = ?
            WHERE id = ?
        ''', (new_qtd, new_price, new_total, new_comissao, new_acordos, new_fp_id, edit_op_casada, edit_filial, edit_pedido_int, v_id))
        
        st.toast("Pedido atualizado com sucesso!", icon="✅")
        st.rerun()

# Dialog: Cancelar Pedido
@st.dialog("Cancelar Pedido")
def modal_cancelar_pedido(v_id):
    st.write(f"Tem certeza que deseja cancelar definitivamente o Pedido #{v_id}?")
    st.warning("Esta ação é definitiva e removerá o pedido da fila de faturamento.")
    if st.button("Confirmar Cancelamento", type="primary", use_container_width=True):
        run_query("UPDATE vendas SET status = 'CANCELADO' WHERE id = ?", (v_id,))
        st.toast(f"Pedido #{v_id} cancelado com sucesso!", icon="🛑")
        st.rerun()


tab_pedidos, tab_degustacao = st.tabs(["Pedidos de Venda", "Degustações e Amostras"])

# ======= ABA 1: PEDIDOS DE VENDA =======
with tab_pedidos:
    # Ação de Novo Pedido no topo
    col_btn, col_empty = st.columns([1, 4])
    if col_btn.button("Lançar Novo Pedido", type="primary", use_container_width=True):
        modal_lancar_pedido()
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    # Filtros
    if 'vendas_dt_inicio' not in st.session_state:
        st.session_state['vendas_dt_inicio'] = date.today() - timedelta(days=30)
    if 'vendas_dt_fim' not in st.session_state:
        st.session_state['vendas_dt_fim'] = date.today()
        
    col_f1, col_f2, col_f3, col_f4 = st.columns([0.8, 0.8, 1.4, 2.0])
    dt_inicio = col_f1.date_input("Data de Início", value=st.session_state['vendas_dt_inicio'], key="vendas_dt_inicio_input")
    dt_fim = col_f2.date_input("Data de Fim", value=st.session_state['vendas_dt_fim'], key="vendas_dt_fim_input")
    st.session_state['vendas_dt_inicio'] = dt_inicio
    st.session_state['vendas_dt_fim'] = dt_fim
    
    opcoes_clientes = {"-- TODOS --": None}
    if not df_clientes.empty:
        for _, r in df_clientes.iterrows():
            nome_display = r['nome_fantasia'] if r['nome_fantasia'] else r['nome']
            opcoes_clientes[nome_display] = r['id']
            
    cli_filtrado_nome = col_f3.selectbox("Filtrar por Cliente", list(opcoes_clientes.keys()))
    cli_id_filtro = opcoes_clientes[cli_filtrado_nome]
    
    filtro_status = col_f4.radio(
        "Filtrar por Situação",
        ["Todos", "Pendentes", "Em Faturamento", "Faturados"],
        horizontal=True,
        key="filtro_vendas_gestao"
    )
    
    # Query de busca
    query_pedidos = '''
        SELECT v.id as 'pedido_id', v.data as 'data_pedido', 
               COALESCE(c.nome_fantasia, c.nome) as 'cliente_name', 
               vn.nome as 'vendedor_name', p.nome as 'produto_name', v.quantidade as 'quantidade', 
               v.valor_total as 'valor_total', fp.nome as 'forma_pagamento', v.status as 'status_pedido',
               v.tipo_documento, v.numero_documento, v.pedido_grupo,
               v.flag_op_casada, v.filial_atacadao, v.pedido_atacadao_numero
        FROM vendas v 
        JOIN clientes c ON v.cliente_id=c.id
        LEFT JOIN funcionarios vn ON v.vendedor_id=vn.id
        JOIN produtos p ON v.produto_id=p.id
        LEFT JOIN formas_pagamento fp ON v.forma_pagamento_id=fp.id
        WHERE v.data BETWEEN ? AND ?
    '''
    
    params_pedidos = [dt_inicio.strftime("%Y-%m-%d"), dt_fim.strftime("%Y-%m-%d")]
    if cli_id_filtro is not None:
        query_pedidos += " AND v.cliente_id = ?"
        params_pedidos.append(cli_id_filtro)
        
    if filtro_status == "Pendentes":
        query_pedidos += " AND v.status = 'APROVADO'"
    elif filtro_status == "Em Faturamento":
        query_pedidos += " AND v.status = 'FATURADO' AND v.tipo_documento = 'Nota Fiscal (NF)' AND (v.numero_documento LIKE 'Bling #%' OR v.numero_documento IS NULL OR v.numero_documento = '')"
    elif filtro_status == "Faturados":
        query_pedidos += " AND v.status = 'FATURADO' AND (v.tipo_documento LIKE '%DAV%' OR (v.tipo_documento = 'Nota Fiscal (NF)' AND v.numero_documento NOT LIKE 'Bling #%' AND v.numero_documento IS NOT NULL AND v.numero_documento != ''))"
        
    query_pedidos += " ORDER BY CASE WHEN v.pedido_grupo IS NULL THEN 0 ELSE 1 END DESC, v.pedido_grupo DESC, v.id DESC"
    
    df_raw = fetch_all(query_pedidos, tuple(params_pedidos))
    
    if df_raw.empty:
        st.info("Nenhum pedido encontrado para o filtro selecionado.")
    else:
        # Contagem sequencial do pedido_grupo
        grupo_contadores = {}
        pedido_labels = {}
        for _, r in df_raw.iterrows():
            grp = r['pedido_grupo']
            pid = int(r['pedido_id'])
            if grp and pd.notna(grp):
                if grp not in grupo_contadores:
                    grupo_contadores[grp] = 0
                grupo_contadores[grp] += 1
                pedido_labels[pid] = f"{grp}.{grupo_contadores[grp]}"
            else:
                pedido_labels[pid] = f"#{pid}"
                
        # Formata o status
        def format_status_badge(row):
            status = row['status_pedido']
            tipo = row['tipo_documento']
            num = row['numero_documento']
            pid = int(row['pedido_id'])
            
            if status == 'APROVADO':
                return "Pendente (Aguardando Faturamento)"
            elif status == 'CANCELADO':
                return "Cancelado"
            elif status == 'FATURADO':
                if tipo and "DAV" in tipo:
                    num_str = str(num).zfill(10) if num else str(pid)
                    return f"Faturado (DAV #{num_str})"
                else:
                    is_bling = num and str(num).startswith("Bling #")
                    is_empty = not num or str(num).strip() == ""
                    if is_bling or is_empty:
                        return "Em Faturamento (NF-e Sem Número SEFAZ)"
                    else:
                        return f"Faturado (NF-e #{num})"
            return status
            
        # Formata o histórico
        def format_historico(row):
            if bool(row['flag_op_casada']):
                filial = row['filial_atacadao'] or ""
                num_int = row['pedido_atacadao_numero'] or ""
                return f"{filial} - Pedido: {num_int}"
            if row['status_pedido'] == 'APROVADO' and row['valor_total'] == 0:
                return "Bonificação"
            return "Venda padrão"
            
        try:
            df_raw['Pedido'] = df_raw['pedido_id'].apply(lambda x: pedido_labels.get(int(x), f"#{x}"))
            df_raw['Data Captação'] = pd.to_datetime(df_raw['data_pedido']).dt.strftime('%d/%m/%Y')
            df_raw['Cliente'] = df_raw['cliente_name']
            df_raw['Histórico'] = df_raw.apply(format_historico, axis=1)
            df_raw['Carga'] = df_raw['produto_name']
            df_raw['Qtd'] = df_raw['quantidade'].apply(lambda x: f"{x:.0f} UN")
            df_raw['Valor Total'] = df_raw['valor_total'].apply(format_brl)
            df_raw['Forma Pagto'] = df_raw['forma_payment'].fillna("A vista") if 'forma_payment' in df_raw.columns else df_raw['forma_pagamento'].fillna("A vista")
            df_raw['Vendedor'] = df_raw['vendedor_name'].fillna("Venda Direta")
            df_raw['Situação do Pedido'] = df_raw.apply(format_status_badge, axis=1)
        except KeyError as ke:
            st.error(f"ERRO DE COLUNA DETECTADO: {ke}")
            st.write("Colunas que existem no df_raw:", df_raw.columns.tolist())
            raise ke
        
        # Colorir status
        def highlight_status(row):
            sit = df_raw.loc[row.name, 'Situação do Pedido']
            if "Pendente" in sit:
                return ['background-color: #fff9e6; color: #856404'] * len(row)
            elif "Em Faturamento" in sit:
                return ['background-color: #e6f7ff; color: #0050b3'] * len(row)
            elif "Faturado" in sit:
                return ['background-color: #ebfaf0; color: #155724'] * len(row)
            elif "Cancelado" in sit:
                return ['background-color: #f8d7da; color: #721c24'] * len(row)
            return [''] * len(row)
            
        df_exibir = df_raw[['Pedido', 'Data Captação', 'Cliente', 'Histórico', 'Carga', 'Qtd', 'Valor Total', 'Forma Pagto', 'Vendedor', 'Situação do Pedido']]
        
        # Dataframe Interativo com Múltiplas Seleções
        event = st.dataframe(
            df_exibir.style.apply(highlight_status, axis=1),
            hide_index=True,
            width="stretch",
            selection_mode="multi-row",
            on_select="rerun"
        )
        
        selected_indices = event.selection.rows
        
        # Ações em lote e exportação
        if selected_indices:
            df_selecionados_raw = df_raw.iloc[selected_indices]
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            col_act1, col_act2, col_act3 = st.columns([1.5, 1.5, 2.0])
            
            # Botão Exportar Excel
            buffer = io.BytesIO()
            df_export = df_selecionados_raw[['Pedido', 'Data Captação', 'Cliente', 'Histórico', 'Carga', 'Qtd', 'Valor Total', 'Forma Pagto', 'Vendedor', 'Situação do Pedido']]
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Pedidos')
            
            col_act1.download_button(
                label="Exportar para Excel (XLSX)",
                data=buffer.getvalue(),
                file_name=f"pedidos_selecionados_{date.today().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # Se apenas um registro for selecionado, habilitar edição/cancelamento e histórico
            if len(selected_indices) == 1:
                row_sel = df_selecionados_raw.iloc[0]
                vid_sel = int(row_sel['pedido_id'])
                status_sel = row_sel['status_pedido']
                
                # Botões de Alteração
                if status_sel == 'APROVADO':
                    if col_act2.button("Editar Pedido", use_container_width=True):
                        modal_editar_pedido(vid_sel)
                    if col_act3.button("Cancelar Pedido", type="primary", use_container_width=True):
                        modal_cancelar_pedido(vid_sel)
                else:
                    col_act2.info("Pedidos faturados/cancelados não podem ser editados ou cancelados.")
                
                # --- TIMELINE / HISTÓRICO DO PEDIDO SELECIONADO ---
                st.markdown("---")
                st.markdown("### Histórico do Ciclo de Vida do Pedido")
                
                df_det = fetch_all('''
                    SELECT v.id, v.data, v.status, v.tipo_documento, v.numero_documento,
                           v.valor_total, v.comprovante_url,
                           COALESCE(c.nome_fantasia, c.nome) as cliente, c.cidade, c.uf,
                           vn.nome as vendedor,
                           p.nome as produto, v.quantidade,
                           v.manifesto_id,
                           m.motorista_nome, m.placa_veiculo, m.status as manifesto_status, m.data_saida
                    FROM vendas v
                    JOIN clientes c ON v.cliente_id = c.id
                    LEFT JOIN funcionarios vn ON v.vendedor_id = vn.id
                    JOIN produtos p ON v.produto_id = p.id
                    LEFT JOIN manifestos_carga m ON v.manifesto_id = m.id
                    WHERE v.id = ?
                ''', (vid_sel,))
                
                if not df_det.empty:
                    row_det = df_det.iloc[0]
                    comprovante = row_det['comprovante_url']
                    has_comprovante = comprovante and str(comprovante).strip() != ""
                    manifesto_status = row_det['manifesto_status']
                    is_delivered = has_comprovante or (manifesto_status == 'CONCLUÍDO (CANHOTOS OK)')
                    
                    if is_delivered:
                        etapa = 4
                    elif row_det['manifesto_id'] is not None:
                        etapa = 3
                    elif row_det['status'] == 'FATURADO':
                        etapa = 2
                    else:
                        etapa = 1
                        
                    # Stepper limpo sem emojis, usando números
                    etapas_stepper = [
                        {"nome": "Captação", "num": "1", "desc": "Comercial"},
                        {"nome": "Faturamento", "num": "2", "desc": "Estoque & Financeiro"},
                        {"nome": "Expedição", "num": "3", "desc": "Em Trânsito"},
                        {"nome": "Entregue", "num": "4", "desc": "Concluído"}
                    ]
                    
                    html_stepper = '<div style="display: flex; justify-content: space-between; align-items: center; padding: 20px 10px; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">'
                    for i, et in enumerate(etapas_stepper):
                        num_etapa = i + 1
                        is_completed = num_etapa <= etapa
                        is_active = num_etapa == etapa
                        
                        if is_active:
                            bg_color = "#292d77"
                            text_color = "#ffffff"
                            border_style = "border: 2px solid #292d77;"
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
                            
                        html_stepper += f'''
                        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; text-align: center;">
                            <div style="width: 40px; height: 40px; border-radius: 50%; background: {bg_color}; color: {text_color}; display: flex; justify-content: center; align-items: center; font-size: 16px; {border_style} font-weight: bold;">
                                {et['num']}
                            </div>
                            <div style="margin-top: 10px; font-weight: bold; color: {label_color}; font-size: 13px;">{et['nome']}</div>
                            <div style="font-size: 11px; color: #868e96; margin-top: 2px; padding: 0 5px;">{et['desc']}</div>
                        </div>
                        '''
                        if i < 3:
                            line_color = "#01743d" if (num_etapa < etapa) else "#dee2e6"
                            line_style = "solid" if (num_etapa < etapa) else "dashed"
                            html_stepper += f'''
                            <div style="flex: 1.5; height: 3px; background: {line_color}; border-top: 1px {line_style} {line_color}; margin-top: -25px;"></div>
                            '''
                    html_stepper += '</div>'
                    st.markdown(html_stepper, unsafe_allow_html=True)
                    
                    # Detalhes das etapas em texto
                    col_det1, col_det2 = st.columns(2)
                    with col_det1:
                        st.markdown(f"""
                        <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #dee2e6;min-height:180px;'>
                            <h5 style='color:#292d77;margin-top:0;'>Detalhamento Comercial</h5>
                            <b>Pedido ID:</b> #{row_det['id']}<br>
                            <b>Cliente:</b> {row_det['cliente']} ({row_det['cidade']} - {row_det['uf']})<br>
                            <b>Produto:</b> {row_det['produto']} (x {row_det['quantidade']:.0f} UN)<br>
                            <b>Vendedor:</b> {row_det['vendedor'] or "Venda Direta"}<br>
                            <b>Data Captação:</b> {pd.to_datetime(row_det['data']).strftime('%d/%m/%Y')}<br><br>
                            <span style='font-size:16px;font-weight:bold;color:#01743d;'>Total: R$ {row_det['valor_total']:,.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_det2:
                        hist_linhas = []
                        hist_linhas.append(f"• **Etapa 1 (Captação):** Pedido captado em {pd.to_datetime(row_det['data']).strftime('%d/%m/%Y')} pelo vendedor {row_det['vendedor'] or 'Venda Direta'}.")
                        if etapa >= 2:
                            tipo = row_det['tipo_documento'] or "Nota Fiscal (NF)"
                            num_doc = row_det['numero_documento']
                            doc_label = f"DAV #{str(num_doc).zfill(10)}" if "DAV" in tipo else f"NF-e #{num_doc}" if num_doc else "NF-e (Aguardando SEFAZ)"
                            hist_linhas.append(f"• **Etapa 2 (Faturamento):** Baixado de estoque e faturado como {doc_label}.")
                        else:
                            hist_linhas.append("• **Etapa 2 (Faturamento):** Aguardando faturamento no galpão.")
                        if etapa >= 3:
                            dt_s = pd.to_datetime(row_det['data_saida']).strftime('%d/%m/%Y') if row_det['data_saida'] else "Em trânsito"
                            hist_linhas.append(f"• **Etapa 3 (Expedição):** Despachado no manifesto #{row_det['manifesto_id']} em {dt_s} (Motorista: {row_det['motorista_nome']} | Placa: {row_det['placa_veiculo']}).")
                        else:
                            hist_linhas.append("• **Etapa 3 (Expedição):** Aguardando despacho na Logística.")
                        if etapa >= 4:
                            hist_linhas.append("• **Etapa 4 (Entregue):** Entrega concluída e canhotos físicos homologados.")
                        else:
                            hist_linhas.append("• **Etapa 4 (Entregue):** Aguardando retorno de canhoto físico.")
                            
                        st.markdown(f"""
                        <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #dee2e6;min-height:180px;line-height:1.4;'>
                            <h5 style='color:#01743d;margin-top:0;'>Histórico de Rastreabilidade</h5>
                            {"<br>".join(hist_linhas)}
                        </div>
                        """, unsafe_allow_html=True)

# ======= ABA 2: DEGUSTAÇÕES E AMOSTRAS =======
with tab_degustacao:
    st.subheader("Lançamento de Amostras e Degustações")
    st.markdown("Saída física de mercadorias para ações de degustação ou amostras em clientes, debitando-o automaticamente no caixa.")
    
    df_bancos = fetch_all("SELECT id, nome FROM contas_bancarias WHERE status='ATIVO'")
    if df_clientes.empty or df_produtos.empty:
        st.warning("Cadastre Clientes e Produtos antes de realizar o lançamento!")
    elif df_bancos.empty:
        st.warning("Cadastre pelo menos uma Conta Bancária ativa no Financeiro para registrar a movimentação financeira.")
    else:
        with st.form("form_degustacao", clear_on_submit=True):
            col_d1, col_d2 = st.columns([1, 2])
            data_acao = col_d1.date_input("Data da Ação", value=date.today())
            
            c_opts_deg = {f"{r['nome_fantasia'] or r['nome']}": r for _, r in df_clientes.iterrows()}
            cliente_deg_sel = col_d2.selectbox("Cliente PDV Beneficiado", list(c_opts_deg.keys()), key="deg_cli")
            
            col_d3, col_d4, col_d5 = st.columns([2, 1, 1])
            p_opts_deg = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
            prod_deg_sel = col_d3.selectbox("Produto Utilizado", list(p_opts_deg.keys()), key="deg_prod")
            qtd_deg = col_d4.number_input("Quantidade (volumes/Kg)", min_value=1.0, step=1.0, key="deg_qtd")
            
            b_opts = {f"{r['nome']}": r['id'] for _, r in df_bancos.iterrows()}
            banco_sel = col_d5.selectbox("Conta Bancária (Débito)", list(b_opts.keys()), key="deg_banco")
            
            obs_deg = st.text_area("Relatório da Degustação", placeholder="Escreva detalhes da ação, promotor, etc.")
            btn_deg = st.form_submit_button("Gravar Remessa e Debitar Custo", type="primary")
            
        if btn_deg:
            from database import consumir_estoque_fifo
            cli_deg = c_opts_deg[cliente_deg_sel]
            prod_deg = p_opts_deg[prod_deg_sel]
            banco_id = b_opts[banco_sel]
            doc_ref = f"Amostra/Degustação: {cli_deg['nome']}"
            
            # FIFO
            custo_total, is_estimado, cmv_metodo, custo_ausente = consumir_estoque_fifo(
                produto_id=int(prod_deg['id']),
                quantidade=float(qtd_deg),
                data_mov=data_acao.strftime("%Y-%m-%d"),
                origem="Degustação_Amostra",
                doc_ref=doc_ref
            )
            
            # Caixa Saída
            desc_financeira = f"Custo Mercadoria Amostra - {cli_deg['nome']} ({prod_deg['nome']} x {qtd_deg:.0f})"
            if obs_deg:
                desc_financeira += f" | {obs_deg}"
                
            run_query(
                """INSERT INTO fluxo_caixa 
                   (data, tipo, categoria, descricao, valor, conta_bancaria_id, cliente_id, conciliado) 
                   VALUES (?, 'Saída', '2.2.1', ?, ?, ?, ?, TRUE)""",
                (data_acao.strftime("%Y-%m-%d"), desc_financeira, custo_total, banco_id, int(cli_deg['id']))
            )
            
            st.success(f"Remessa registrada com sucesso! Saída física executada via FIFO.")
            st.info(f"Custo Real FIFO apurado: {format_brl(custo_total)}")
            
            if custo_ausente:
                st.warning("O produto selecionado não possui custo cadastrado. Cadastre o custo em Produtos.")
            elif is_estimado and cmv_metodo != 'SIMPLIFICADO':
                st.warning("O estoque físico no sistema estava insuficiente. Custo estimado provisoriamente.")
                
            import time
            time.sleep(2.0)
            st.rerun()
