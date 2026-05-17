import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import run_query, fetch_all

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Pessoas", page_icon="👥", layout="wide")

from estilo import carregar_estilo
carregar_estilo()

st.title("👥 Pessoas e Folha de Pagamento")

df_vendedores = fetch_all("SELECT id, nome, gatilho_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")

tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral (Quadro)", "Folha de Pagamento", "💎 Central de Comissões", "🖨️ Extrato Mensal do Vendedor"])

# ======= QUADRO DE COLABORADORES =======
with tab1:
    st.subheader("Quadro Geral de Colaboradores")
    
    filtro_status = st.radio("Filtrar por Status:", ["Ativos", "Inativos", "Todos"], horizontal=True, index=0)
    
    query_colab = "SELECT id, nome, cargo, status, data_admissao, data_termino, salario_base, ajuda_custo, outros_descricao, outros_valor, regime_contratacao FROM funcionarios WHERE 1=1"
    if filtro_status == "Ativos":
        query_colab += " AND status='ATIVO'"
    elif filtro_status == "Inativos":
        query_colab += " AND status='INATIVO'"
        
    df_func = fetch_all(query_colab)
    
    if not df_func.empty:
        df_display = df_func.rename(columns={
            'nome': 'Nome', 'cargo': 'Cargo', 'status': 'Status',
            'data_admissao': 'Início', 'data_termino': 'Término',
            'salario_base': 'Rem. Fixa', 'ajuda_custo': 'Ajuda Custo', 
            'outros_descricao': 'Outros (Ref)', 'outros_valor': 'Outros (Valor)', 
            'regime_contratacao': 'Regime'
        })
        
        df_display['Início'] = pd.to_datetime(df_display['Início']).dt.strftime('%d/%m/%Y')
        df_display['Término'] = pd.to_datetime(df_display['Término']).dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_display, width='stretch', hide_index=True)
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Lista de Colaboradores (CSV)",
            data=csv,
            file_name='colaboradores.csv',
            mime='text/csv',
        )
    else:
        st.info("Nenhum colaborador encontrado com este filtro.")

# ======= PAGAMENTO =======
with tab2:
    st.subheader("Geração de Pagamento (Folha)")
    
    df_func2 = fetch_all("SELECT id, nome, salario_base, ajuda_custo, outros_valor FROM funcionarios WHERE status='ATIVO'")
    if df_func2.empty:
        st.warning("Cadastre colaboradores ativos primeiro no módulo Cadastros.")
    else:
        func_dict = dict(zip(df_func2['nome'], df_func2['id']))
        salario_dict = dict(zip(df_func2['nome'], df_func2['salario_base']))
        ajuda_dict = dict(zip(df_func2['nome'], df_func2['ajuda_custo']))
        outros_dict = dict(zip(df_func2['nome'], df_func2['outros_valor']))
        
        nome_pgto = st.selectbox("Selecione o Colaborador (Apenas Ativos)", list(func_dict.keys()))
        
        with st.form("form_pagamento", clear_on_submit=False):
            col1, col2, col3 = st.columns(3)
            data_pgto = col1.date_input("Data de Pagamento", value=date.today(), format="DD/MM/YYYY")
            mes_ref = col2.text_input("Mês Referência (Ex: 03/2026)", value=data_pgto.strftime("%m/%Y"))
            
            base_sal = float(salario_dict[nome_pgto] or 0.0)
            base_ajuda = float(ajuda_dict[nome_pgto] or 0.0)
            base_outros = float(outros_dict[nome_pgto] or 0.0)
            
            sal_base = col3.number_input("Rem. Fixa (R$)", min_value=0.0, value=base_sal, step=10.0)
            
            st.markdown("##### Outras Verbas e Encargos")
            col4, col5, col6, col7 = st.columns(4)
            ajuda = col4.number_input("Ajuda de Custo (R$)", min_value=0.0, value=base_ajuda, step=10.0)
            outros = col5.number_input("Outros Valores (R$)", min_value=0.0, value=base_outros, step=10.0)
            refeicao = col6.number_input("Vale Refeição / Alimentação (R$)", min_value=0.0, step=10.0)
            custo_previ = col7.number_input("Custo Previdenciário (R$)", min_value=0.0, step=10.0)
            
            valor_total = sal_base + ajuda + outros + refeicao + custo_previ
            st.info(f"**Total Desembolsado pelo Caixa:** R$ {valor_total:,.2f}".replace('.',','))
            
            if st.form_submit_button("Registrar Pagamento"):
                if valor_total > 0:
                    func_id = func_dict[nome_pgto]
                    run_query(
                        """INSERT INTO rh_pagamentos 
                           (funcionario_id, data_pagamento, mes_referencia, salario_base_pago, passagem, refeicao, custo_previdenciario, valor_total_pago) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (func_id, data_pgto, mes_ref, sal_base, ajuda + outros, refeicao, custo_previ, valor_total)
                    )
                    
                    desc = f"Pagamento Rem. Fixa e Benefícios ({mes_ref}) - {nome_pgto}"
                    run_query(
                        "INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                        (data_pgto, "Saída", "Folha de Pagamento", valor_total, desc)
                    )
                    st.success(f"Pagamento lançado com sucesso e adicionado ao fluxo de caixa!")
                    
        st.markdown("---")
        st.subheader("Histórico de Pagamentos")
        query_pgtos = '''
        SELECT p.id as ID, f.nome as Colaborador, p.data_pagamento as 'Data Pgto', p.mes_referencia as 'Mês',
               p.salario_base_pago as 'Rem. Fixa', p.passagem as 'Ajuda/Outros', p.refeicao as 'Refeição', 
               p.custo_previdenciario as 'Encargos', p.valor_total_pago as 'Total Pago (R$)'
        FROM rh_pagamentos p
        JOIN funcionarios f ON p.funcionario_id = f.id
        ORDER BY p.data_pagamento DESC
        '''
        df_pgtos = fetch_all(query_pgtos)
        if not df_pgtos.empty:
            df_pgtos['Data Pgto'] = pd.to_datetime(df_pgtos['Data Pgto']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_pgtos, width="stretch", hide_index=True)
            
            csv2 = df_pgtos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Histórico (CSV)",
                data=csv2,
                file_name='historico_pagamentos.csv',
                mime='text/csv',
            )

# ======= 3. COMISSÕES =======
with tab3:
    st.subheader("Malha Contábil: Repasse de Comissões e Representantes")
    st.markdown("> **Aviso do RH:** O repasse só é calculado sobre **Pedidos já Faturados** ou Liquidados.")
    
    hoje = date.today()
    
    mes_filtro = st.selectbox("Apontamento Cíclico (Mês Base)", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')])
    
    q_com = '''
        SELECT v.id as 'Doc', vn.nome as 'Rota', vn.gatilho_comissao as 'Gatilho do Repasse Comercial', c.nome as 'K-Account', v.data as 'Data Lançada', cr.status as 'Tít. Receb.', v.valor_total as 'Vendido Bruto R$', v.comissao_valor as 'Retenção'
        FROM vendas v
        JOIN funcionarios vn ON v.vendedor_id=vn.id
        JOIN clientes c ON v.cliente_id=c.id
        LEFT JOIN contas_a_receber cr ON cr.venda_id=v.id
        WHERE strftime('%Y-%m', v.data) = ? AND v.status = 'FATURADO'
    '''
    df_com = fetch_all(q_com, (mes_filtro,))
    
    if not df_com.empty:
        df_com['Comissão Bloqueada'] = "🚫 Pendente Base/Recebimento"
        for i, row in df_com.iterrows():
            g_r = row['Gatilho do Repasse Comercial']
            stat = str(row['Tít. Receb.']).upper()
            if g_r == "LIQUIDAÇÃO DE TITULO" and "PENDENTE" in stat:
                df_com.at[i, 'Comissão Bloqueada'] = "🚫 Aguardando Boleto Sócio"
            else:
                df_com.at[i, 'Comissão Bloqueada'] = "✔️ Módulo Liberado"
                
        df_view = df_com.drop('Gatilho do Repasse Comercial', axis=1)
        df_view['Data Lançada'] = pd.to_datetime(df_view['Data Lançada'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_view['Vendido Bruto R$'] = df_view['Vendido Bruto R$'].apply(format_brl)
        df_view['Retenção'] = df_view['Retenção'].apply(format_brl)
        st.dataframe(df_view, hide_index=True, width="stretch")
        
        st.markdown("### 🧮 Auditoria de Obrigações Comerciais")
        df_liberadas = df_com[df_com['Comissão Bloqueada'].str.contains('✔️')].copy()
        
        if not df_liberadas.empty:
            df_liberadas['Retenção Float'] = df_liberadas['Retenção'].astype(float)
            grp = df_liberadas.groupby('Rota', as_index=False).agg({
                'Vendido Bruto R$': 'sum',
                'Retenção Float': 'sum'
            })
            
            m_c1, m_c2 = st.columns(2)
            m_c1.metric("Volume Geral Faturado (Limpo)", format_brl(grp['Vendido Bruto R$'].sum()))
            m_c2.metric("Passivo RH Gerado (Livre de Travas)", format_brl(grp['Retenção Float'].sum()))
            
            grp['Vendido Bruto R$'] = grp['Vendido Bruto R$'].apply(format_brl)
            grp['Passivo Retido R$'] = grp['Retenção Float'].apply(format_brl)
            grp.drop('Retenção Float', axis=1, inplace=True)
            
            st.dataframe(grp, hide_index=True, width="stretch")
        else:
            st.warning("Nenhuma comissão destravou no mês escolhido.")
    else:
        st.write("Sem faturamento rastreado no período.")

# ======= 4. EXTRATO DO VENDEDOR =======
with tab4:
    st.subheader("🖨️ Emissão de Extrato Mensal Analítico")
    st.markdown("Gere o relatório detalhado para o Vendedor cobrar suas notas (Apenas Pedidos Faturados).")
    
    if not df_vendedores.empty:
        colE1, colE2 = st.columns(2)
        v_opts_ext = {f"{r['nome']}": r for _, r in df_vendedores.iterrows()}
        vend_str = colE1.selectbox("Selecione o Vendedor / Rota", list(v_opts_ext.keys()), key="extrato_vend")
        mes_ext = colE2.selectbox("Mês de Competência", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')], key="extrato_mes")
        
        if st.button("Gerar Extrato Analítico", type="primary"):
            vend_obj = v_opts_ext[vend_str]
            v_id = vend_obj['id']
            v_gatilho = vend_obj['gatilho_comissao']
            
            q_ext = '''
                SELECT v.id as 'Doc ERP', v.tipo_documento as 'Dcto', v.numero_documento as 'Série', v.data as 'Data Emissão', 
                       c.nome as 'Cliente', p.nome as 'Produto', 
                       v.valor_total as 'Valor Faturado (R$)', v.comissao_valor as 'Comissão Bruta (R$)', 
                       cr.data_vencimento as 'Vencimento Título', cr.status as 'Status Título'
                FROM vendas v
                JOIN clientes c ON v.cliente_id=c.id
                JOIN produtos p ON v.produto_id=p.id
                LEFT JOIN contas_a_receber cr ON cr.venda_id=v.id
                WHERE v.vendedor_id = ? AND strftime('%Y-%m', v.data) = ? AND v.status = 'FATURADO'
            '''
            df_ext = fetch_all(q_ext, (v_id, mes_ext))
            
            st.markdown("---")
            st.markdown(f"### 📄 EXTRATO COMERCIAL - {vend_str.upper()}")
            
            if df_ext.empty:
                st.warning("Nenhum faturamento registrado para este vendedor no mês solicitado.")
            else:
                total_faturado = 0.0
                total_bloqueado = 0.0
                total_liberado = 0.0
                
                df_ext['Situação do Pagamento'] = "A PROCESSAR"
                
                for idx, row in df_ext.iterrows():
                    v_fat = float(row['Valor Faturado (R$)'])
                    c_bruta = float(row['Comissão Bruta (R$)'])
                    stat_titulo = str(row['Status Título']).upper()
                    
                    total_faturado += v_fat
                    
                    if v_gatilho == "LIQUIDAÇÃO DE TITULO":
                        if "PENDENTE" in stat_titulo:
                            total_bloqueado += c_bruta
                            df_ext.at[idx, 'Situação do Pagamento'] = "🚫 BLOQUEADO (Aguarda Cliente Pagar)"
                        else:
                            total_liberado += c_bruta
                            df_ext.at[idx, 'Situação do Pagamento'] = "✔️ LIBERADO"
                    else: 
                        total_liberado += c_bruta
                        df_ext.at[idx, 'Situação do Pagamento'] = "✔️ LIBERADO (Faturado)"
                
                df_ext['Data Emissão'] = pd.to_datetime(df_ext['Data Emissão'], errors='coerce').dt.strftime('%d/%m/%Y')
                df_ext['Vencimento Título'] = pd.to_datetime(df_ext['Vencimento Título'], errors='coerce').dt.strftime('%d/%m/%Y')
                
                for col in ['Valor Faturado (R$)', 'Comissão Bruta (R$)']:
                    df_ext[col] = df_ext[col].apply(format_brl)
                
                st.dataframe(df_ext, hide_index=True, width="stretch")
                
                st.markdown("#### ⚖️ Resumo do Extrato")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Carteira Girada", format_brl(total_faturado))
                r2.error(f"Comissão Bloqueada: {format_brl(total_bloqueado)}")
                r3.success(f"Comissão Paga/Pronta: {format_brl(total_liberado)}")
                r4.info(f"Obrigação Total: {format_brl(total_liberado + total_bloqueado)}")
