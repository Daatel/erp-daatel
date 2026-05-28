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
        
        csv = df_display.to_csv(index=False, sep=';').encode('utf-8-sig')
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
            
            csv2 = df_pgtos.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(
                label="📥 Exportar Histórico (CSV)",
                data=csv2,
                file_name='historico_pagamentos.csv',
                mime='text/csv',
            )

# ======= 3. COMISSÕES =======
with tab3:
    st.subheader("Malha Contábil: Repasse de Comissões e Representantes")
    st.markdown("""
    > **Políticas de Governança Comercial:** 
    > As comissões são provisionadas dinamicamente à medida que as vendas são faturadas ou liquidadas. 
    > No entanto, para evitar dispersão de caixa, elas **não são pagas individualmente**. 
    > Utilize esta Central de Fechamento para auditar os lançamentos mensais, conferir as travas de recebimento, **abater devoluções/sangrias comerciais** e **autorizar um repasse consolidado único** para a conta de cada representante na data de vencimento acordada.
    """)
    
    hoje = date.today()
    
    col_f1, col_f2 = st.columns(2)
    mes_filtro = col_f1.selectbox("Apontamento Cíclico (Mês Base)", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')], key="com_mes_filtro")
    
    df_vends_list = fetch_all("SELECT id, nome, gatilho_comissao, dia_vencimento_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%' ORDER BY nome")
    if df_vends_list.empty:
        st.warning("Cadastre representantes comerciais no RH primeiro.")
    else:
        vendedor_opts = {r['nome']: r for _, r in df_vends_list.iterrows()}
        vendedor_sel = col_f2.selectbox("Selecione o Vendedor / Rota para Auditoria", list(vendedor_opts.keys()))
        
        vendedor_obj = vendedor_opts[vendedor_sel]
        v_id = vendedor_obj['id']
        vendedor_nome = vendedor_obj['nome']
        v_gatilho = str(vendedor_obj['gatilho_comissao'] or 'FATURAMENTO').upper()
        v_dia_venc = int(vendedor_obj['dia_vencimento_comissao'] or 31)
        
        # Query detalhada de vendas e comissões daquele vendedor no mês selecionado
        q_com = '''
            SELECT v.id as 'Doc', c.nome as 'K-Account', v.data as 'Data Lançada', 
                   COALESCE(cr.status, 'N/A') as 'Tit_Receb', v.valor_total as 'Vendido Bruto R$', 
                   v.comissao_valor as 'Retencao'
            FROM vendas v
            JOIN clientes c ON v.cliente_id=c.id
            LEFT JOIN contas_a_receber cr ON cr.venda_id=v.id
            WHERE v.vendedor_id = ? AND strftime('%Y-%m', v.data) = ? AND v.status = 'FATURADO'
            ORDER BY v.id DESC
        '''
        df_com = fetch_all(q_com, (v_id, mes_filtro))
        
        # --- CÁLCULO DE ESTORNOS POR DEVOLUÇÕES / DESCONTOS ---
        estornos_list = []
        total_estorno_comissao = 0.0
        
        df_devs = fetch_all('''
            SELECT d.id, d.data, c.nome as cliente_nome, p.nome as produto_nome, 
                   d.valor_financeiro_abatido, COALESCE(c.rede_clientes, '') as rede_clientes, 
                   d.produto_id, d.motivo
            FROM devolucoes d
            JOIN clientes c ON d.cliente_id = c.id
            JOIN produtos p ON d.produto_id = p.id
            WHERE c.representante_id = ? AND strftime('%Y-%m', d.data) = ?
        ''', (v_id, mes_filtro))
        
        for idx, r in df_devs.iterrows():
            val_dev = float(r['valor_financeiro_abatido'] or 0.0)
            prod_id = int(r['produto_id'])
            rede_c = r['rede_clientes']
            if not rede_c: rede_c = "TODOS"
            
            # Fetch rule
            df_regra = fetch_all('''
                SELECT percentual 
                FROM comissoes_regras 
                WHERE vendedor_id = ? 
                  AND (produto_id = ? OR produto_id IS NULL)
                  AND (rede_clientes = ? OR rede_clientes = 'TODOS')
                ORDER BY (CASE WHEN produto_id = ? THEN 2 ELSE 1 END) DESC,
                         (CASE WHEN rede_clientes = ? THEN 2 ELSE 1 END) DESC
                LIMIT 1
            ''', (v_id, prod_id, rede_c, prod_id, rede_c))
            
            perc = float(df_regra.iloc[0]['percentual']) if not df_regra.empty else 0.0
            if perc <= 0.0:
                perc = 5.0 # Fallback padrão de segurança
                
            estorno_val = val_dev * (perc / 100.0)
            total_estorno_comissao += estorno_val
            
            estornos_list.append({
                "ID": int(r['id']),
                "Data": pd.to_datetime(r['data']).strftime('%d/%m/%Y'),
                "Cliente": r['cliente_nome'],
                "Produto": r['produto_nome'],
                "Motivo": r['motivo'],
                "Valor Avariado": val_dev,
                "Comissão Estornada": estorno_val
            })
            
        if df_com.empty and len(estornos_list) == 0:
            st.info(f"Nenhuma atividade comercial (vendas ou devoluções) registrada para **{vendedor_nome}** na competência **{mes_filtro}**.")
        else:
            # Determina o status da comissão para cada item
            total_vendido = 0.0
            total_comissao = 0.0
            total_liberado = 0.0
            
            if not df_com.empty:
                df_com['Status Comissão'] = ""
                df_com['Liberada_Float'] = 0.0
                
                for idx, r in df_com.iterrows():
                    val_com = float(r['Retencao'] or 0.0)
                    status_tit = str(r['Tit_Receb']).upper()
                    
                    # Se gatilho for faturamento, libera direto
                    if "LIQUIDAÇÃO" not in v_gatilho:
                        df_com.at[idx, 'Status Comissão'] = "✔️ Liberada (Faturamento)"
                        df_com.at[idx, 'Liberada_Float'] = val_com
                    else:
                        # Se for liquidação de título, depende se o título está RECEBIDO
                        if status_tit == "RECEBIDO":
                            df_com.at[idx, 'Status Comissão'] = "✔️ Liberada (Pago pelo Cliente)"
                            df_com.at[idx, 'Liberada_Float'] = val_com
                        else:
                            df_com.at[idx, 'Status Comissão'] = "🚫 Travada (Aguardando Recebimento)"
                            df_com.at[idx, 'Liberada_Float'] = 0.0
                
                total_vendido = df_com['Vendido Bruto R$'].sum()
                total_comissao = df_com['Retencao'].sum()
                total_liberado = df_com['Liberada_Float'].sum()
            
            total_bloqueado = total_comissao - total_liberado
            repasse_liquido = max(0.0, total_liberado - total_estorno_comissao)
            
            # Exibir resumo em Cards de KPI
            st.markdown("### 🧮 Saldo Consolidado e Auditoria")
            
            kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
            kpi_c1.metric("Vendido Bruto Total", format_brl(total_vendido))
            kpi_c2.metric("Comissão Gross Provisão", format_brl(total_comissao))
            kpi_c3.metric("(-) Estornos p/ Devoluções", f"- {format_brl(total_estorno_comissao)}", delta_color="inverse")
            kpi_c4.metric("SALDO LÍQUIDO LIBERADO", format_brl(repasse_liquido), help="Pronto para repasse (Comissão Liberada menos Estornos de Devoluções)")
            
            # Detalhamento de Comissão Travada (Aguardando Recebimento)
            if total_bloqueado > 0.0:
                st.info(f"💡 **Nota de Caixa:** Além do saldo liberado, o vendedor possui **{format_brl(total_bloqueado)}** em comissões travadas aguardando a liquidação dos boletos pelos clientes.")
            
            # Tabela principal de conferência (Se houver vendas)
            if not df_com.empty:
                st.markdown("#### 🔍 Extrato Detalhado de Títulos e Repasses (Vendas)")
                df_view = df_com.copy()
                df_view['Data Lançada'] = pd.to_datetime(df_view['Data Lançada'], errors='coerce').dt.strftime('%d/%m/%Y')
                df_view['Vendido Bruto R$'] = df_view['Vendido Bruto R$'].apply(format_brl)
                df_view['Comissão R$'] = df_view['Retencao'].apply(format_brl)
                df_view['Tit. Receb.'] = df_view['Tit_Receb'].map({'RECEBIDO': '🟢 PAGO', 'PENDENTE': '🔴 EM ABERTO', 'N/A': '⚪ N/A'})
                
                df_view_final = df_view[['Doc', 'K-Account', 'Data Lançada', 'Tit. Receb.', 'Vendido Bruto R$', 'Comissão R$', 'Status Comissão']]
                st.dataframe(df_view_final, hide_index=True, width="stretch")
            
            # Tabela de Estornos de Devolução (Se houver)
            if len(estornos_list) > 0:
                st.markdown("#### 📉 Extrato Detalhado de Devoluções e Reversões (Deduções)")
                df_view_dev = pd.DataFrame(estornos_list)
                df_view_dev_fmt = df_view_dev.copy()
                df_view_dev_fmt['Valor Avariado'] = df_view_dev_fmt['Valor Avariado'].apply(format_brl)
                df_view_dev_fmt['Comissão Estornada'] = df_view_dev_fmt['Comissão Estornada'].apply(format_brl)
                st.dataframe(df_view_dev_fmt, hide_index=True, width="stretch")
            
            # Painel de Fechamento e Envio para Contas a Pagar
            st.markdown("---")
            st.markdown("### 🔒 Autorização e Repasse Consolidado")
            
            if repasse_liquido <= 0.0:
                st.info("Não há saldo líquido positivo de comissão liberado para fechamento comercial nesta competência.")
            else:
                # 1. Verifica se já existe repasse consolidado no Contas a Pagar
                desc_consolidada_prefix = f"Repasse de Comissão Consolidada - {vendedor_nome} - Ref. {mes_filtro}"
                df_rep_existe = fetch_all("SELECT id, valor, status, data_vencimento FROM contas_a_pagar WHERE descricao LIKE ?", (f"%{desc_consolidada_prefix}%",))
                
                if not df_rep_existe.empty:
                    rep_id = df_rep_existe.iloc[0]['id']
                    rep_val = float(df_rep_existe.iloc[0]['valor'])
                    rep_status = df_rep_existe.iloc[0]['status']
                    rep_venc = df_rep_existe.iloc[0]['data_vencimento']
                    rep_venc_dt = pd.to_datetime(rep_venc).strftime('%d/%m/%Y')
                    
                    st.success(f"✅ **Folha de Comissões Já Autorizada:** Esta competência foi fechada anteriormente. "
                               f"Foi gerada a Obrigação ID #{rep_id} no valor líquido de **{format_brl(rep_val)}**, "
                               f"com status **'{rep_status}'** e vencimento acordado para **{rep_venc_dt}**.")
                else:
                    # Calcula data de vencimento acordada (dia do mês seguinte)
                    import calendar
                    partes = mes_filtro.split('-')
                    ano = int(partes[0])
                    mes = int(partes[1])
                    mes_seg = mes + 1
                    ano_seg = ano
                    if mes_seg > 12:
                        mes_seg = 1
                        ano_seg += 1
                    ultimo_dia = calendar.monthrange(ano_seg, mes_seg)[1]
                    dia_final = min(v_dia_venc, ultimo_dia)
                    venc_consolidado = date(ano_seg, mes_seg, dia_final)
                    
                    st.warning(f"⚠️ **Folha de Comissões Pendente:** O repasse líquido acumulado de **{format_brl(repasse_liquido)}** "
                               f"referente a competência **{mes_filtro}** (já descontados os estornos de devoluções) ainda não foi enviado para o Contas a Pagar.")
                    st.markdown(f"- **Total Bruto Liberado:** {format_brl(total_liberado)}")
                    st.markdown(f"- **Total de Abatimentos/Devoluções:** - {format_brl(total_estorno_comissao)}")
                    st.markdown(f"- **Data acordada de pagamento:** `{venc_consolidado.strftime('%d/%m/%Y')}` (Dia {v_dia_venc} do mês seguinte)")
                    st.markdown(f"- **Regra de Repasse do Representante:** `{v_gatilho}`")
                    
                    if st.button("🔒 Fechar Competência & Autorizar Payout Único", type="primary", use_container_width=True):
                        # Pega plano de conta para repasse de comissão
                        p_c_comissao = fetch_all("SELECT id FROM planos_de_contas WHERE codigo = '2.2.3' OR nome LIKE '%Comiss%' LIMIT 1")
                        pc_com_id = int(p_c_comissao.iloc[0]['id']) if not p_c_comissao.empty else None
                        
                        desc_comissao_final = f"{desc_consolidada_prefix} | Venc. acordado: dia {v_dia_venc}/mês seg. | (Bruto: {format_brl(total_liberado)} - Estornos: {format_brl(total_estorno_comissao)})"
                        
                        run_query('''
                            INSERT INTO contas_a_pagar (plano_conta_id, descricao, valor, data_vencimento, status)
                            VALUES (?, ?, ?, ?, 'PENDENTE')
                        ''', (pc_com_id, desc_comissao_final, repasse_liquido, venc_consolidado.strftime("%Y-%m-%d")))
                        
                        st.success(f"Folha consolidada fechada e autorizada para repasse. Obrigação comercial líquida de {format_brl(repasse_liquido)} enviada ao Contas a Pagar com vencimento em {venc_consolidado.strftime('%d/%m/%Y')}.")
                        import time; time.sleep(2.0); st.rerun()

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
