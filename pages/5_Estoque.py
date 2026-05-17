import streamlit as st
import pandas as pd
from database import fetch_all, run_query
from datetime import date
from estilo import carregar_estilo

st.set_page_config(page_title="Controle de Estoque", page_icon="📦", layout="wide")
carregar_estilo()

st.title("📦 Controle de Estoque")
st.markdown("Gestão unificada de Matéria-Prima, Produtos Acabados e Rastreabilidade Contábil.")

# Dicionário de Motivos de Ajuste (Amarrados ao Plano de Contas)
MOTIVOS_AJUSTE = {
    "Amostras e Brindes (Comercial)": {
        "categoria": "Despesa Fixa", 
        "nome": "Despesas com Marketing e Brindes", 
        "tipo": "Saída"
    },
    "Perda por Vencimento (Validade)": {
        "categoria": "Custo Variável", 
        "nome": "Custo com Perdas e Vencimentos", 
        "tipo": "Saída"
    },
    "Avaria / Quebra no Manuseio": {
        "categoria": "Custo Variável", 
        "nome": "Custo com Perdas e Avarias", 
        "tipo": "Saída"
    },
    "Consumo Interno (Uso da Empresa)": {
        "categoria": "Despesa Fixa", 
        "nome": "Despesas Administrativas (Consumo Interno)", 
        "tipo": "Saída"
    },
    "Ajuste Negativo (Falta em Inventário)": {
        "categoria": "Custo Variável", 
        "nome": "Ajuste Negativo de Inventário", 
        "tipo": "Saída"
    },
    "Ajuste Positivo (Sobra em Inventário)": {
        "categoria": "Receita Operacional", 
        "nome": "Ajuste Positivo de Inventário", 
        "tipo": "Entrada"
    }
}

def garantir_plano_conta(categoria, nome):
    """Busca o ID da conta pelo nome. Se não existir, cria a conta no DRE."""
    df = fetch_all("SELECT id FROM planos_de_contas WHERE nome = ?", (nome,))
    if not df.empty:
        return int(df.iloc[0]['id'])
    else:
        run_query("INSERT INTO planos_de_contas (categoria, nome) VALUES (?, ?)", (categoria, nome))
        df_new = fetch_all("SELECT id FROM planos_de_contas WHERE nome = ?", (nome,))
        return int(df_new.iloc[0]['id'])

tab1, tab4, tab2, tab3 = st.tabs(["📊 Posição do Estoque", "🕵️ Rastreabilidade (PEPS)", "✍️ Lançamentos Manuais", "📜 Extrato e Histórico"])

# =========================================================
# TAB 1: POSIÇÃO DO ESTOQUE E ALERTAS
# =========================================================
with tab1:
    st.subheader("Posição Atual de Estoque e Indicadores")

    query_estoque = '''
    SELECT p.id, p.nome as Produto, p.unidade_medida as Unidade, p.is_materia_prima as "Matéria Prima",
           p.custo_unidade, COALESCE(p.estoque_minimo, 0) as estoque_minimo,
           SUM(CASE WHEN m.tipo_movimento = 'Entrada' THEN m.quantidade ELSE 0 END) as Total_Entradas,
           SUM(CASE WHEN m.tipo_movimento = 'Saída' THEN m.quantidade ELSE 0 END) as Total_Saidas
    FROM produtos p
    LEFT JOIN estoque_movimentos m ON p.id = m.produto_id
    GROUP BY p.id, p.nome, p.unidade_medida, p.is_materia_prima, p.custo_unidade, p.estoque_minimo
    '''
    df_estoque = fetch_all(query_estoque)

    if not df_estoque.empty:
        df_estoque['Em Estoque'] = df_estoque['Total_Entradas'] - df_estoque['Total_Saidas']
        df_estoque['Matéria Prima'] = df_estoque['Matéria Prima'].map({1: 'Sim', 0: 'Não'})
        df_estoque['Valor Financeiro'] = df_estoque['Em Estoque'] * df_estoque['custo_unidade']
        
        # Alertas de Estoque Crítico
        df_critico = df_estoque[df_estoque['Em Estoque'] <= df_estoque['estoque_minimo']]
        if not df_critico.empty:
            st.error(f"⚠️ Atenção: Há {len(df_critico)} produto(s) com estoque abaixo do mínimo estabelecido ou negativo!")
            with st.expander("Ver Produtos em Nível Crítico"):
                view_critico = df_critico[['Produto', 'Em Estoque', 'estoque_minimo', 'Unidade']].copy()
                view_critico.columns = ['Produto', 'Estoque Atual', 'Estoque Mínimo (Alerta)', 'Unidade']
                st.dataframe(view_critico.style.highlight_max(subset=['Estoque Atual'], color='lightcoral'), hide_index=True, use_container_width=True)
                
        # KPIs Gerais
        col1, col2 = st.columns(2)
        mp_total = df_estoque[df_estoque['Matéria Prima'] == 'Sim']['Em Estoque'].sum()
        pf_total = df_estoque[df_estoque['Matéria Prima'] == 'Não']['Em Estoque'].sum()
        
        col1.metric("Qtd Matéria-Prima (Total)", f"{mp_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Qtd Produtos Finais (Total)", f"{pf_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.markdown("---")
        
        # Tabela Visão Geral
        filtro = st.radio("Filtrar Visão", ["Todos", "Matéria-Prima", "Produtos Finais"], horizontal=True)
        if filtro == "Matéria-Prima":
            view_df = df_estoque[df_estoque['Matéria Prima'] == 'Sim']
        elif filtro == "Produtos Finais":
            view_df = df_estoque[df_estoque['Matéria Prima'] == 'Não']
        else:
            view_df = df_estoque

        mostrar_zerados = st.checkbox("Mostrar produtos com estoque zerado", value=False)
        if not mostrar_zerados:
            view_df = view_df[view_df['Em Estoque'] != 0]
            
        view_df = view_df[['id', 'Produto', 'Matéria Prima', 'Unidade', 'Total_Entradas', 'Total_Saidas', 'Em Estoque', 'estoque_minimo']]
        
        def highlight_stock(row):
            if row['Em Estoque'] <= row['estoque_minimo']:
                return ['background-color: #ffcccc; color: black'] * len(row)
            return [''] * len(row)
            
        st.dataframe(view_df.style.apply(highlight_stock, axis=1).format({
            'Total_Entradas': '{:.2f}', 'Total_Saidas': '{:.2f}', 'Em Estoque': '{:.2f}'
        }), width="stretch", hide_index=True)
        
    else:
        st.info("Nenhum produto cadastrado no sistema.")

# =========================================================
# TAB 4: RASTREABILIDADE DE LOTES (FIFO/PEPS)
# =========================================================
with tab4:
    st.subheader("Rastreabilidade de Lotes Físicos (Método PEPS)")
    st.markdown("Como o faturamento é independente, esta inteligência calcula matematicamente quais lotes físicos originais compõem o seu saldo atual, presumindo que o estoque mais velho saiu primeiro (FIFO).")
    
    # 1. Obter Saldo de Estoque (Apenas Produtos Finais, pois MP vem de compra e precisaríamos mapear NFs, mas podemos focar no Produto Acabado primeiro)
    df_saldos_pf = fetch_all('''
        SELECT p.id, p.nome, SUM(CASE WHEN m.tipo_movimento = 'Entrada' THEN m.quantidade ELSE -m.quantidade END) as saldo_atual 
        FROM produtos p
        LEFT JOIN estoque_movimentos m ON p.id = m.produto_id
        WHERE p.is_materia_prima = 0
        GROUP BY p.id
        HAVING saldo_atual > 0
    ''')
    
    if df_saldos_pf.empty:
        st.info("Nenhum produto acabado com saldo positivo no estoque para rastrear lotes.")
    else:
        dados_rastreio = []
        for _, row in df_saldos_pf.iterrows():
            pid = row['id']
            nome_p = row['nome']
            saldo_restante = float(row['saldo_atual'])
            
            # Buscar os lotes gerados (do mais novo pro mais velho)
            lotes = fetch_all("SELECT id, data, data_validade, produto_final_kg FROM producao_diaria WHERE produto_id=? ORDER BY id DESC", (pid,))
            for _, lote in lotes.iterrows():
                if saldo_restante <= 0:
                    break
                qtd_lote = float(lote['produto_final_kg'])
                lote_id = lote['id']
                data_fab = lote['data']
                data_val = lote['data_validade']
                
                qtd_atribuida = min(saldo_restante, qtd_lote)
                
                dados_rastreio.append({
                    "Produto Final": nome_p,
                    "Origem (Lote Sistema)": f"OP #{lote_id}",
                    "Saldo Físico Retido (Kg/Un)": qtd_atribuida,
                    "Data Fabricação": pd.to_datetime(data_fab).strftime('%d/%m/%Y') if pd.notnull(data_fab) else "-",
                    "Data Validade": pd.to_datetime(data_val).strftime('%d/%m/%Y') if pd.notnull(data_val) else "-"
                })
                
                saldo_restante -= qtd_atribuida
                
            if saldo_restante > 0:
                # Saldo excedente que não possui lote de OP correspondente (Ajustes manuais)
                dados_rastreio.append({
                    "Produto Final": nome_p,
                    "Origem (Lote Sistema)": "Avulso / Ajuste Manual",
                    "Saldo Físico Retido (Kg/Un)": saldo_restante,
                    "Data Fabricação": "-",
                    "Data Validade": "-"
                })
                
        df_rastreio = pd.DataFrame(dados_rastreio)
        st.dataframe(df_rastreio, hide_index=True, width="stretch")

# =========================================================
# TAB 2: LANÇAMENTOS MANUAIS (AJUSTES)
# =========================================================
with tab2:
    st.subheader("Ajuste de Estoque e Lançamentos Manuais")
    st.markdown("Todos os ajustes são **automaticamente vinculados ao Plano de Contas** para o DRE.")
    
    df_prods = fetch_all("SELECT id, nome, unidade_medida, custo_unidade FROM produtos ORDER BY nome")
    
    if df_prods.empty:
        st.warning("Cadastre produtos antes de fazer movimentações.")
    else:
        with st.form("form_ajuste_estoque", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            
            # Select de Produto
            prod_dict = {f"{r['nome']} ({r['unidade_medida']})": r['id'] for _, r in df_prods.iterrows()}
            prod_nome = col_m1.selectbox("Selecione o Produto", list(prod_dict.keys()))
            
            # Select de Motivo
            motivo_selecionado = col_m2.selectbox("Motivo do Lançamento (Vinculado ao DRE)", list(MOTIVOS_AJUSTE.keys()))
            
            info_motivo = MOTIVOS_AJUSTE[motivo_selecionado]
            st.info(f"💡 **Impacto Contábil:** Este lançamento gerará uma **{info_motivo['tipo']}** no estoque, e será lançado na conta **{info_motivo['nome']}** (Categoria: {info_motivo['categoria']}).")
            
            col_m3, col_m4, col_m5 = st.columns(3)
            qtd = col_m3.number_input("Quantidade", min_value=0.01, step=1.0)
            data_mov = col_m4.date_input("Data da Ocorrência", value=date.today())
            obs = col_m5.text_input("Observações / Justificativa")
            
            if st.form_submit_button("Registrar Lançamento"):
                prod_id = prod_dict[prod_nome]
                tipo_mov = info_motivo['tipo']
                origem_text = f"Ajuste_Manual: {motivo_selecionado}"
                if obs: origem_text += f" | {obs}"
                
                # Garante que a conta contábil exista e pega o ID
                conta_id = garantir_plano_conta(info_motivo['categoria'], info_motivo['nome'])
                
                # Insere no Banco
                query_insert = """
                INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem, plano_conta_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                run_query(query_insert, (data_mov, prod_id, tipo_mov, qtd, origem_text, conta_id))
                
                st.success(f"Lançamento de {qtd} salvo com sucesso! O estoque foi atualizado.")
                import time; time.sleep(1); st.rerun()

# =========================================================
# TAB 3: EXTRATO E HISTÓRICO
# =========================================================
with tab3:
    st.subheader("Extrato Detalhado de Movimentações")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if not df_estoque.empty:
            filtro_prod_extrato = st.selectbox("Filtrar por Produto", ["Todos"] + df_estoque['Produto'].tolist())
        else:
            filtro_prod_extrato = "Todos"
            
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por Tipo de Movimento", ["Todos", "Entrada", "Saída"])
        
    query_hist = '''
    SELECT m.data as Data, p.nome as Produto, m.tipo_movimento as Movimento, 
           m.quantidade as Quantidade, m.origem as Origem, 
           pc.nome as "Conta DRE", m.documento_referencia as Documento
    FROM estoque_movimentos m
    JOIN produtos p ON m.produto_id = p.id
    LEFT JOIN planos_de_contas pc ON m.plano_conta_id = pc.id
    WHERE 1=1
    '''
    params = []
    
    if filtro_prod_extrato != "Todos":
        query_hist += " AND p.nome = ?"
        params.append(filtro_prod_extrato)
        
    if filtro_tipo != "Todos":
        query_hist += " AND m.tipo_movimento = ?"
        params.append(filtro_tipo)
        
    query_hist += " ORDER BY m.data DESC, m.id DESC LIMIT 500"
    
    df_hist = fetch_all(query_hist, tuple(params))
    
    if not df_hist.empty:
        df_hist['Data'] = pd.to_datetime(df_hist['Data']).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(df_hist, width="stretch", hide_index=True)
        
        # Download
        csv = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar Extrato (CSV)", data=csv, file_name="extrato_estoque.csv", mime="text/csv")
    else:
        st.info("Nenhuma movimentação encontrada para o filtro atual.")
