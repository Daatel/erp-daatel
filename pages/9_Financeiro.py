import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import traceback
import calendar
from database import fetch_all, run_query, gerar_comissao_se_necessario
from estilo import carregar_estilo
from fpdf import FPDF

def gerar_pdf_financeiro(df_pdf, dt_ini, dt_fim, t_ent, t_sai, s_liq, banco_filtro, cat_filtro):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho da Empresa
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EMPORIO DO ALHO - RELATORIO FINANCEIRO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Periodo Analisado: {dt_ini.strftime('%d/%m/%Y')} ate {dt_fim.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    
    # Filtros Aplicados
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Filtros Aplicados:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"- Banco: {banco_filtro}  |  - Categoria: {cat_filtro}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Resumo Financeiro do Período
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "RESUMO FINANCEIRO:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"Total de Entradas: R$ {t_ent:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total de Saidas:  R$ {t_sai:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, f"Saldo Liquido:      R$ {s_liq:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    
    # Tabela de Lançamentos
    pdf.set_font("Helvetica", "B", 9)
    w_data = 20
    w_tipo = 22
    w_banco = 25
    w_desc = 85
    w_val = 32
    
    pdf.cell(w_data, 7, "Data", border=1, align="C")
    pdf.cell(w_tipo, 7, "Movimento", border=1, align="C")
    pdf.cell(w_banco, 7, "Banco", border=1, align="C")
    pdf.cell(w_desc, 7, "Historico/Descricao", border=1, align="L")
    pdf.cell(w_val, 7, "Valor", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8.5)
    for _, r in df_pdf.iterrows():
        hist = str(r['Histórico'])[:45]
        # Remove non-ascii or accent characters for FPDF standard helvetica compatibility
        import unicodedata
        hist = "".join(ch for ch in unicodedata.normalize('NFKD', hist) if unicodedata.category(ch) != 'Mn')
        mov = str(r['Movimentação'])
        banco = "".join(ch for ch in unicodedata.normalize('NFKD', str(r['Banco'])) if unicodedata.category(ch) != 'Mn')
        val_str = f"R$ {float(r['Valor']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        pdf.cell(w_data, 6, str(r['Data']), border=1, align="C")
        pdf.cell(w_tipo, 6, mov, border=1, align="C")
        pdf.cell(w_banco, 6, banco[:13], border=1, align="C")
        pdf.cell(w_desc, 6, hist, border=1, align="L")
        pdf.cell(w_val, 6, val_str, border=1, align="R", new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "Relatorio oficial gerado eletronicamente pelo ERP Fabrica de Alho.", new_x="LMARGIN", new_y="NEXT", align="C")
    
    return bytes(pdf.output())

st.set_page_config(page_title="Tesouraria Oficial", page_icon="💸", layout="wide")
carregar_estilo()

st.title("💸 Tesouraria e Inteligência Financeira")
st.markdown("O Centro de Comando com previsão de 30 dias, Múltiplas Contas Bancárias e Inadimplência.")

try:
    hoje = date.today()
    mes_str = hoje.strftime("%Y-%m")

    # ----- DADOS BANCÁRIOS BASE -----
    df_bancos = fetch_all("SELECT id, nome, banco, saldo_inicial FROM contas_bancarias WHERE status='ATIVO'")
    
    opcoes_bancos = {}
    saldo_por_banco = {}
    
    if df_bancos.empty:
        st.error("Nenhuma Conta Bancária Ativa. Vá em Cadastros -> Contas Bancárias e crie pelo menos uma!")
        st.stop()
    else:
        for _, r in df_bancos.iterrows():
            opcoes_bancos[f"{r['nome']}"] = r['id']
            # Saldo começa com o fixo do sistema
            saldo_por_banco[r['id']] = float(r['saldo_inicial'])

    # ----- CÁLCULO DE SALDO REAL HOJE (SOMANDO FLUXO DE CAIXA) -----
    df_fluxo_global = fetch_all("SELECT tipo, valor, conta_bancaria_id, conciliado FROM fluxo_caixa")
    for _, f in df_fluxo_global.iterrows():
        tipo = f['tipo']
        val = float(f['valor']) if pd.notna(f['valor']) else 0.0
        cid = f['conta_bancaria_id']
        
        if cid in saldo_por_banco:
            if tipo == "Entrada":
                saldo_por_banco[cid] += val
            elif tipo == "Saída":
                saldo_por_banco[cid] -= val
                
    saldo_total_empresa = sum(saldo_por_banco.values())

    # ================== GUIAS ==================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard 30 Dias", 
        "🔻 Contas a Pagar (Saída)", 
        "🟢 Contas a Receber (Entrada)", 
        "🏦 Conciliação Bancária",
        "🔄 Transferência entre Contas",
        "🚚 Auditoria Logística"
    ])

    # ------------------ ABA 1: DASHBOARD E PROJEÇÃO 30D ------------------
    with tab1:
        st.subheader("Radar Executivo (Saldos e Projeções)")
        
        # 1. CÁLCULO DE VALORIZAÇÃO DE ESTOQUE (Preço de Custo Realista)
        query_est = """
            SELECT
                p.custo_unidade,
                SUM(CASE WHEN e.tipo_movimento = 'Entrada' THEN e.quantidade ELSE 0 END) - 
                SUM(CASE WHEN e.tipo_movimento = 'Saída' THEN e.quantidade ELSE 0 END) as saldo_fisico
            FROM estoque_movimentos e
            JOIN produtos p ON e.produto_id = p.id
            GROUP BY p.id, p.custo_unidade
        """
        df_est = fetch_all(query_est)
        valor_estoque = 0.0
        if not df_est.empty:
            for _, rp in df_est.iterrows():
                # Nota: Custos não preenchidos no cadastro virão como 0, forçando o Gestor a alimentar seus custos
                c = float(rp['custo_unidade']) if pd.notnull(rp['custo_unidade']) else 0.0
                sf = float(rp['saldo_fisico']) if pd.notnull(rp['saldo_fisico']) else 0.0
                if sf > 0:
                    valor_estoque += sf * c

        capital_global = saldo_total_empresa + valor_estoque

        # 1.1 PLACAR MÁXIMO DE PATRIMÔNIO CROSSEOVER
        st.markdown("### 🏆 Posição de Capital Acumulado da Fábrica")
        cTot1, cTot2, cTot3 = st.columns(3)
        cTot1.metric("💰 DISPONIBILIDADE/CAIXA", f"R$ {saldo_total_empresa:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        cTot2.metric("📦 PATRIMÔNIO (Dinheiro Físico)", f"R$ {valor_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        cTot3.metric("💎 CAPITAL GLOBAL BLINDADO", f"R$ {capital_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        with st.expander("📍 Ver Distribuição do Dinheiro Vivo (Liquidez Diária) Pelos Bancos:"):
            cols_b = st.columns(len(saldo_por_banco) if len(saldo_por_banco) > 0 else 1)
            for idx, (bid,_s) in enumerate(saldo_por_banco.items()):
                b_name = df_bancos[df_bancos['id'] == bid].iloc[0]['nome']
                cols_b[idx].metric(f"🏦 {b_name}", f"R$ {_s:,.2f}".replace('.',','))
                
        st.markdown("---")
        
        # 2. CONSTRUINDO A RÉGUA DE PREVISÃO DE 30 DIAS
        # Precisamos das Contas a Receber PENDENTES
        df_rec_pendente = fetch_all("SELECT valor, data_vencimento FROM contas_a_receber WHERE status='PENDENTE'")
        inadimplentes = 0.0
        recebe_hoje = 0.0
        
        df_pag_pendente = fetch_all("SELECT valor, data_vencimento FROM contas_a_pagar WHERE status='PENDENTE'")
        atrasadas_pagar = 0.0
        pagar_hoje = 0.0
        
        fluxo_projetado = {}
        for i in range(31):
            d_alvo = hoje + timedelta(days=i)
            fluxo_projetado[str(d_alvo)] = {"Entradas": 0.0, "Saidas": 0.0}
            
        if not df_rec_pendente.empty:
            df_rec_pendente['data_vencimento_dt'] = pd.to_datetime(df_rec_pendente['data_vencimento']).dt.date
            inadimplentes = df_rec_pendente[df_rec_pendente['data_vencimento_dt'] < hoje]['valor'].sum()
            recebe_hoje = df_rec_pendente[df_rec_pendente['data_vencimento_dt'] == hoje]['valor'].sum()
            
            # Somar nas janelas de 30 dias
            for _, rp in df_rec_pendente.iterrows():
                dt_str = str(rp['data_vencimento_dt'])
                if dt_str in fluxo_projetado:
                    fluxo_projetado[dt_str]['Entradas'] += float(rp['valor'])

        if not df_pag_pendente.empty:
            df_pag_pendente['data_vencimento_dt'] = pd.to_datetime(df_pag_pendente['data_vencimento']).dt.date
            atrasadas_pagar = df_pag_pendente[df_pag_pendente['data_vencimento_dt'] < hoje]['valor'].sum()
            pagar_hoje = df_pag_pendente[df_pag_pendente['data_vencimento_dt'] == hoje]['valor'].sum()
            
            for _, pp in df_pag_pendente.iterrows():
                dt_str = str(pp['data_vencimento_dt'])
                if dt_str in fluxo_projetado:
                    fluxo_projetado[dt_str]['Saidas'] += float(pp['valor'])

        # Placas de Risco
        cA, cB, cC, cD = st.columns(4)
        cA.metric("🔴 Atrasadas a Pagar (Fogo)", f"R$ {atrasadas_pagar:,.2f}".replace('.',','))
        cB.metric("🟡 Contas a Pagar Hoje", f"R$ {pagar_hoje:,.2f}".replace('.',','))
        cC.error(f"⚠️ Inadimplência na Praça: R$ {inadimplentes:,.2f}")
        cD.success(f"🟩 Entradas Previstas Hoje: R$ {recebe_hoje:,.2f}")
        
        st.markdown("---")
        
        # 3. GRÁFICO PROJETADO
        st.subheader("Painel de Liquidez Misto (Barras vs Linha Flutuante)")
        datas_eixo = []
        entradas_eixo = []
        saidas_eixo = []
        saldos_eixo = []
        
        saldo_andando = saldo_total_empresa
        
        for i in range(31):
            d_alvo = hoje + timedelta(days=i)
            d_str = str(d_alvo)[8:10] + "/" + str(d_alvo)[5:7] # Display like 15/04
            
            ent = fluxo_projetado[str(d_alvo)]["Entradas"]
            sai = fluxo_projetado[str(d_alvo)]["Saidas"]
            
            saldo_andando = saldo_andando + ent - sai
            
            datas_eixo.append(d_str)
            entradas_eixo.append(ent)
            saidas_eixo.append(sai)
            saldos_eixo.append(saldo_andando)
            
        fig = go.Figure()
        
        # Barras de Contas a Receber
        fig.add_trace(go.Bar(
            x=datas_eixo, y=entradas_eixo,
            name="A Receber (Entradas)",
            marker_color='#2563eb'  # Azul corporativo RoyalBlue
        ))
        
        # Barras de Contas a Pagar (Para baixo da linha zero)
        fig.add_trace(go.Bar(
            x=datas_eixo, y=[-s for s in saidas_eixo],
            name="A Pagar (Saídas)",
            marker_color='#ef4444'  # Vermelho Vivo
        ))
        
        # Linha Curva com de Saldo Flutuante
        fig.add_trace(go.Scatter(
            x=datas_eixo, y=saldos_eixo,
            mode='lines+markers',
            name="💰 SALDO DO DIA",
            line=dict(color='#10b981', width=4, shape='spline'), # Verde vivo para a linha teto
            marker=dict(size=8, color='white', line=dict(width=2, color='#10b981'))
        ))
        
        fig.update_layout(
            title="DRE Financeiro Evolutivo (Acumulado de 30 Dias)",
            xaxis_title="Linha do Tempo Diária",
            yaxis_title="R$ Volume Circulante",
            barmode='relative', # Relativo empilha o vermelho pra baixo da linha zero
            hovermode="x unified",
            height=500,
            plot_bgcolor='rgba(0,0,0,0)'
        )
        fig.update_yaxes(gridcolor='rgba(128,128,128,0.2)', zerolinecolor='rgba(128,128,128,0.5)', zerolinewidth=2)
        st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        st.subheader("🔍 Detalhamento e Auditoria de Lançamentos por Período")
        st.markdown("Filtre o fluxo de caixa histórico por período e contas para conciliação ou exportação oficial em Excel ou PDF.")
        
        # Inicializar datas no session state se não existirem
        if 'det_dt_inicio' not in st.session_state:
            st.session_state['det_dt_inicio'] = date.today() - timedelta(days=7)
        if 'det_dt_fim' not in st.session_state:
            st.session_state['det_dt_fim'] = date.today()

        col_b1, col_b2, col_b3, _ = st.columns([1, 1.3, 1.3, 4.4])
        if col_b1.button("📅 Hoje", use_container_width=True, key="btn_shortcut_hoje"):
            st.session_state['det_dt_inicio'] = date.today()
            st.session_state['det_dt_fim'] = date.today()
            st.rerun()
        if col_b2.button("📅 Últimos 7 Dias", use_container_width=True, key="btn_shortcut_7d"):
            st.session_state['det_dt_inicio'] = date.today() - timedelta(days=7)
            st.session_state['det_dt_fim'] = date.today()
            st.rerun()
        if col_b3.button("📅 Últimos 30 Dias", use_container_width=True, key="btn_shortcut_30d"):
            st.session_state['det_dt_inicio'] = date.today() - timedelta(days=30)
            st.session_state['det_dt_fim'] = date.today()
            st.rerun()

        # Filtros interativos
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        dt_inicio = col_f1.date_input("Data de Início", value=st.session_state['det_dt_inicio'])
        dt_fim = col_f2.date_input("Data de Fim", value=st.session_state['det_dt_fim'])
        
        # Sincronizar alterações manuais de volta ao session_state
        st.session_state['det_dt_inicio'] = dt_inicio
        st.session_state['det_dt_fim'] = dt_fim
        
        bancos_det_opts = ["TODOS"] + list(opcoes_bancos.keys())
        banco_filtro = col_f3.selectbox("Filtrar por Conta/Banco", bancos_det_opts, key="det_banco")
        
        # Categorias de Lançamento (Filtrando vazios e Nulos)
        df_todas_cats = fetch_all("SELECT DISTINCT categoria FROM fluxo_caixa WHERE categoria IS NOT NULL AND categoria != ''")
        cats_list = sorted([str(c) for c in df_todas_cats['categoria'].tolist()]) if not df_todas_cats.empty else []
        cats_opts = ["TODAS"] + cats_list
        cat_filtro = col_f4.selectbox(
            "Filtrar por Categoria", 
            cats_opts, 
            key="det_cat",
            help="Selecione uma classificação contábil (Ex: Receita Com Vendas, Comissões, etc.) para isolar esses lançamentos no período."
        )
        
        # Query de lançamentos no período
        query_detalhe = """
            SELECT fc.data as 'Data', fc.tipo as 'Movimentação', 
                   fc.categoria as 'Categoria', fc.descricao as 'Histórico', fc.valor as 'Valor', 
                   cb.nome as 'Banco'
            FROM fluxo_caixa fc
            LEFT JOIN contas_bancarias cb ON fc.conta_bancaria_id = cb.id
            WHERE fc.data BETWEEN ? AND ?
            ORDER BY fc.data DESC, fc.id DESC
        """
        
        df_det = fetch_all(query_detalhe, (dt_inicio.strftime("%Y-%m-%d"), dt_fim.strftime("%Y-%m-%d")))
        
        if not df_det.empty:
            # Aplicar filtros adicionais em pandas
            if banco_filtro != "TODOS":
                df_det = df_det[df_det['Banco'] == banco_filtro]
            if cat_filtro != "TODAS":
                df_det = df_det[df_det['Categoria'] == cat_filtro]
                
            if df_det.empty:
                st.warning("Nenhum lançamento encontrado para os filtros selecionados.")
            else:
                # Sumarização
                entradas = df_det[df_det['Movimentação'] == 'Entrada']['Valor'].sum()
                saidas = df_det[df_det['Movimentação'] == 'Saída']['Valor'].sum()
                saldo_liq = entradas - saidas
                
                c_det1, c_det2, c_det3 = st.columns(3)
                c_det1.metric("🟢 Total de Entradas", f"R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                c_det2.metric("🔴 Total de Saídas", f"R$ {saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                # Cor do Saldo Líquido
                if saldo_liq >= 0:
                    c_det3.success(f"💎 Saldo Líquido: R$ {saldo_liq:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                else:
                    c_det3.error(f"💎 Saldo Líquido: R$ {saldo_liq:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                # Formatação para visualização
                df_det_view = df_det.copy()
                df_det_view['Data'] = pd.to_datetime(df_det_view['Data']).dt.strftime('%d/%m/%Y')
                df_det_view['Valor (R$)'] = df_det_view['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(df_det_view[['Data', 'Movimentação', 'Banco', 'Categoria', 'Histórico', 'Valor (R$)']], hide_index=True, width="stretch")
                
                # Ações de Exportação
                col_exp1, col_exp2 = st.columns(2)
                
                # 1. Export Excel (CSV)
                csv_data = df_det.to_csv(index=False, sep=";").encode('utf-8-sig')
                col_exp1.download_button(
                    label="📥 Exportar Planilha (Excel/CSV)",
                    data=csv_data,
                    file_name=f"extrato_financeiro_{dt_inicio.strftime('%d-%m-%Y')}_a_{dt_fim.strftime('%d-%m-%Y')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="btn_det_csv"
                )
                
                # 2. Export PDF
                try:
                    pdf_data = gerar_pdf_financeiro(df_det_view, dt_inicio, dt_fim, entradas, saidas, saldo_liq, banco_filtro, cat_filtro)
                    col_exp2.download_button(
                        label="📄 Exportar Relatório Oficial (PDF)",
                        data=pdf_data,
                        file_name=f"relatorio_financeiro_{dt_inicio.strftime('%d-%m-%Y')}_a_{dt_fim.strftime('%d-%m-%Y')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_det_pdf"
                    )
                except Exception as pdf_err:
                    col_exp2.error(f"Erro ao gerar PDF: {pdf_err}")
        else:
            st.info("Nenhum lançamento no período selecionado.")

    # ------------------ ABA 2: CONTAS A PAGAR ------------------
    with tab2:
        st.subheader("Contas a Pagar (Passivo e Relacionamento)")
        
        # --- LANÇADOR MANUAL DE DUPLICATA A PAGAR ---
        with st.expander("➕ Lançar uma Duplicata a Pagar (Despesa / Passivo)"):
            df_forn = fetch_all("SELECT id, nome_fantasia FROM fornecedores ORDER BY nome_fantasia")
            op_forn = {"-- SELECIONE O FORNECEDOR --": None}
            if not df_forn.empty:
                for _, r in df_forn.iterrows():
                    op_forn[f"{r['nome_fantasia']}"] = r['id']
            
            df_pc = fetch_all("SELECT id, codigo, nome FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') ORDER BY codigo")
            op_pc = {"-- SELECIONE O PLANO DE CONTAS --": (None, None)}
            if not df_pc.empty:
                for _, r in df_pc.iterrows():
                    op_pc[f"{r['codigo']} - {r['nome']}"] = (r['id'], r['codigo'])
                    
            df_cli = fetch_all("SELECT id, nome, cnpj_cpf FROM clientes ORDER BY nome")
            op_cli = {"-- SELECIONE O CLIENTE --": None}
            if not df_cli.empty:
                for _, r in df_cli.iterrows():
                    op_cli[f"{r['nome']} ({r['cnpj_cpf']})"] = r['id']
                    
            # CSS para estilização fina de botões e alinhamento/estado do selectbox
            st.markdown("""
            <style>
            /* Botão primário verde */
            div.stButton > button[kind="primary"] {
                background-color: #28a745 !important;
                color: white !important;
                border: 1px solid #28a745 !important;
            }
            div.stButton > button[kind="primary"]:hover {
                background-color: #218838 !important;
                border-color: #1e7e34 !important;
            }
            div.stButton > button[kind="primary"]:active {
                background-color: #1e7e34 !important;
                border-color: #1c7430 !important;
            }
            
            /* Ajuste de margem do checkbox para alinhar o selectbox com o date_input */
            div[data-testid="stCheckbox"] {
                margin-bottom: -12px !important;
            }
            
            /* Estilo para Selectbox desabilitado (cinza claro) */
            div[data-baseweb="select"]:has(input:disabled) > div {
                background-color: #f1f5f9 !important;
                border-color: #cbd5e1 !important;
                color: #94a3b8 !important;
                cursor: not-allowed !important;
            }
            div[data-baseweb="select"]:has(input:disabled) * {
                color: #94a3b8 !important;
            }
            </style>
            """, unsafe_allow_html=True)

            col_m1, col_m2 = st.columns(2)
            forn_sel = col_m1.selectbox("Fornecedor", list(op_forn.keys()))
            pc_sel = col_m2.selectbox("Plano de Contas (Planta de Custo)", list(op_pc.keys()))
            
            col_m3, col_m4 = st.columns([2, 1])
            desc_p = col_m3.text_input("Descrição / Fatura (Ex: Nota Fiscal nº 123)")
            val_p = col_m4.number_input("Valor da Duplicata (R$)", min_value=0.01, step=50.0)
            
            col_m5, col_m6 = st.columns(2)
            venc_p = col_m5.date_input("Vencimento", date.today() + timedelta(days=30))
            with col_m6:
                is_vinc = st.checkbox("É Cliente Vinculado (CNPJ) ?", value=False)
                cli_sel = st.selectbox("Cliente Vinculado (CNPJ)", list(op_cli.keys()), disabled=not is_vinc, label_visibility="collapsed")
            
            if st.button("Salvar Duplicata a Pagar", type="primary", use_container_width=False):
                if forn_sel == "-- SELECIONE O FORNECEDOR --":
                    st.error("Por favor, selecione um Fornecedor.")
                elif pc_sel == "-- SELECIONE O PLANO DE CONTAS --":
                    st.error("Por favor, selecione um Plano de Contas.")
                elif not desc_p:
                    st.error("Preencha a descrição do lançamento.")
                else:
                    pc_id, pc_codigo = op_pc[pc_sel]
                    forn_id = op_forn[forn_sel]
                    cli_id = op_cli[cli_sel] if is_vinc else None
                    
                    # Validação de Cliente Obrigatório para 2.2.1, 2.2.2, 2.2.4
                    if pc_codigo in ('2.2.1', '2.2.2', '2.2.4') and cli_id is None:
                        st.error(f"⚠️ A conta selecionada ({pc_sel}) exige a vinculação obrigatória de um Cliente (CNPJ) para cálculo de rentabilidade. Por favor, marque a caixa e selecione o cliente correspondente.")
                    else:
                        run_query(
                            "INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, cliente_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                            (forn_id, pc_id, cli_id, desc_p, val_p, venc_p.strftime("%Y-%m-%d"))
                        )
                        st.success("✅ Duplicata a Pagar lançada com sucesso!")
                        import time; time.sleep(1); st.rerun()

        df_all_contas = fetch_all("""
            SELECT c.id, f.nome_fantasia as 'Fornecedor', p.nome as 'Planta de Custo', 
                   c.descricao as 'Descrição/Fatura', c.data_vencimento as 'Vencimento', 
                   c.valor as 'Valor', c.status as 'Status', c.data_pagamento as 'Data PGTO',
                   c.comprovante_url as 'Comprovante', c.cliente_id
            FROM contas_a_pagar c
            LEFT JOIN fornecedores f ON c.fornecedor_id = f.id
            LEFT JOIN planos_de_contas p ON c.plano_conta_id = p.id
            ORDER BY c.data_vencimento ASC
        """)
        
        # --- TRAVA DE CANHOTOS LOGÍSTICA ---
        df_man_bloqueados = fetch_all("SELECT id FROM manifestos_carga WHERE status='EM TRÂNSITO'")
        ids_bloqueados = df_man_bloqueados['id'].tolist() if not df_man_bloqueados.empty else []
        
        def checar_trava(desc):
            if pd.isna(desc): return False
            if "Acerto Rota/Manifesto #" in desc:
                try:
                    man_id = int(desc.split("#")[1].split("-")[0].strip())
                    if man_id in ids_bloqueados:
                        return True
                except:
                    pass
            return False
            
        if not df_all_contas.empty:
            df_all_contas['Bloqueado'] = df_all_contas['Descrição/Fatura'].apply(checar_trava)
            # Aplicar tag visual no grid de leitura
            df_all_contas['Fornecedor'] = df_all_contas.apply(
                lambda r: f"🔴 [BLOQUEADO FALTAM CANHOTOS] {r['Fornecedor']}" if r.get('Bloqueado', False) else r['Fornecedor'], axis=1
            )
        # -----------------------------------
        
        if df_all_contas.empty:
            st.info("Nenhuma conta a pagar encontrada. Paz de espírito.")
        else:
            status_filter = st.selectbox("Filtro de Status:", ["PENDENTE", "AGUARDANDO BAIXA", "PAGO", "TODAS"], key="pag_filt")
            
            df_view = df_all_contas.copy()
            if status_filter != "TODAS":
                df_view = df_view[df_view['Status'] == status_filter]
                
            if df_view.empty:
                st.warning("Nenhum registro com este filtro.")
            else:
                df_view['Vencimento'] = pd.to_datetime(df_view['Vencimento']).dt.strftime('%d/%m/%Y')
                df_view['Data PGTO'] = pd.to_datetime(df_view['Data PGTO']).dt.strftime('%d/%m/%Y').fillna("-")
                df_view['Valor (R$)'] = df_view['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.dataframe(df_view[['id', 'Fornecedor', 'Planta de Custo', 'Descrição/Fatura', 'Vencimento', 'Valor (R$)', 'Status', 'Data PGTO']], hide_index=True, width="stretch")
            
            # (Note: Visualizador de Canhotos e Recibos de Descarga foram movidos para a guia 'Auditoria Logística')
            
            # Executar Baixa Multi-Conta (Lote)
            if "PENDENTE" in df_view['Status'].values or "AGUARDANDO BAIXA" in df_view['Status'].values:
                with st.expander("💸 Efetuar Liquidação de Boleto / Pagar Fornecedores (Em Lote)"):
                    # Inclui contas PENDENTE (não bloqueadas) + AGUARDANDO BAIXA (comprovante já anexado pela logística)
                    df_pend = df_all_contas[
                        ((df_all_contas['Status'] == "PENDENTE") & (df_all_contas['Bloqueado'] == False)) |
                        (df_all_contas['Status'] == "AGUARDANDO BAIXA")
                    ].copy()
                    
                    if df_pend.empty:
                        st.info("Nenhum boleto pendente está liberado para pagamento (ou os existentes aguardam canhotos da logística).")
                    else:
                        df_pend['Pagar?'] = False
                        
                        df_view_edit = df_pend[['Pagar?', 'id', 'Fornecedor', 'Descrição/Fatura', 'Vencimento', 'Valor', 'Planta de Custo']]
                        
                        st.markdown("**Marque os fornecedores que você pagou hoje (Boletos bloqueados por falta de canhotos estão ocultos):**")
                    edited_df = st.data_editor(df_view_edit, hide_index=True, width="stretch",
                                               column_config={"Pagar?": st.column_config.CheckboxColumn("Pagar?", default=False),
                                                              "Valor": st.column_config.NumberColumn("Valor Base (R$)", format="%.2f")})
                    
                    selecionados = edited_df[edited_df['Pagar?'] == True]
                    
                    if not selecionados.empty:
                        st.markdown("---")
                        colA, colB, colC = st.columns(3)
                        d_pgto = colA.date_input("Data real do Pagamento (Lote)", date.today())
                        conta_saida = colB.selectbox("DE QUAL BANCO/CONTA SAIU O LOTE?", list(opcoes_bancos.keys()))
                        
                        if colC.button("💸 Confirmar Baixa em Lote", type="primary", use_container_width=True):
                            conta_id = opcoes_bancos[conta_saida]
                            
                            for _, r in selecionados.iterrows():
                                c_id = int(r['id'])
                                v_base = float(r['Valor'])
                                forn = r['Fornecedor'] if pd.notna(r['Fornecedor']) else ""
                                fat = r['Descrição/Fatura']
                                plant = r['Planta de Custo'] if pd.notna(r['Planta de Custo']) else "Gasto"
                                
                                # Buscar o cliente_id da contas_a_pagar para propagar
                                df_cap_cli = fetch_all("SELECT cliente_id FROM contas_a_pagar WHERE id=?", (c_id,))
                                cap_cli_id = int(df_cap_cli.iloc[0]['cliente_id']) if not df_cap_cli.empty and pd.notna(df_cap_cli.iloc[0]['cliente_id']) else None

                                # Atualiza Pagar
                                run_query("UPDATE contas_a_pagar SET status='PAGO', data_pagamento=?, conta_bancaria_id=? WHERE id=?", 
                                          (d_pgto.strftime("%Y-%m-%d"), conta_id, c_id))
                                
                                # Injeta no Caixa com a Fonte Certa e o cliente_id propagado
                                run_query("INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, fonte_id, conta_bancaria_id, conciliado, cliente_id) VALUES (?, 'Saída', ?, ?, ?, ?, ?, TRUE, ?)",
                                          (d_pgto.strftime("%Y-%m-%d"), plant, f"PGTO Forn. {forn}: {fat}", v_base, c_id, conta_id, cap_cli_id))
                                          
                            st.success(f"✔️ {len(selecionados)} contas liquidadas e debitadas do banco {conta_saida} com sucesso!")
                            import time; time.sleep(2); st.rerun()

            # --- RENEGOCIAÇÃO / EDIÇÃO DE DUPLICATA ---
            with st.expander("✏️ Renegociar / Editar Duplicata"):
                df_pend_edit = fetch_all("""
                    SELECT c.id, f.nome_fantasia, c.descricao, c.valor, c.data_vencimento, c.status 
                    FROM contas_a_pagar c 
                    LEFT JOIN fornecedores f ON c.fornecedor_id = f.id 
                    WHERE c.status='PENDENTE' ORDER BY c.data_vencimento
                """)
                if df_pend_edit.empty:
                    st.info("Nenhuma duplicata pendente para editar.")
                else:
                    opts_edit_fin = {}
                    for _, r in df_pend_edit.iterrows():
                        lbl = f"#{r['id']} | {r['nome_fantasia']} | {r['descricao']} | R$ {r['valor']:,.2f} | Venc: {pd.to_datetime(r['data_vencimento']).strftime('%d/%m/%Y')}"
                        opts_edit_fin[lbl] = r['id']
                    sel_edit = st.selectbox("Selecione a duplicata:", list(opts_edit_fin.keys()), key="edit_dup_sel")
                    if sel_edit:
                        dup_id = opts_edit_fin[sel_edit]
                        dup_data = fetch_all("SELECT * FROM contas_a_pagar WHERE id=?", (dup_id,)).iloc[0]
                        valor_original = float(dup_data['valor'])

                        acao = st.radio("O que deseja fazer?", ["Alterar Vencimento/Valor", "Aplicar Juros / Desconto", "Reparcelar"], horizontal=True, key="acao_dup")

                        if acao == "Alterar Vencimento/Valor":
                            with st.form("form_edit_dup"):
                                ed1, ed2 = st.columns(2)
                                novo_venc = ed1.date_input("Novo Vencimento", value=pd.to_datetime(dup_data['data_vencimento']).date())
                                novo_valor = ed2.number_input("Novo Valor (R$)", value=valor_original, min_value=0.01)
                                nova_desc = st.text_input("Descrição", value=dup_data['descricao'])
                                if st.form_submit_button("Salvar Alteração"):
                                    run_query("UPDATE contas_a_pagar SET data_vencimento=?, valor=?, descricao=? WHERE id=?",
                                              (novo_venc.strftime("%Y-%m-%d"), novo_valor, nova_desc, dup_id))
                                    st.success("Duplicata atualizada!")
                                    import time; time.sleep(1); st.rerun()

                        elif acao == "Aplicar Juros / Desconto":
                            st.markdown(f"**Valor original:** R$ {valor_original:,.2f}")
                            jd1, jd2, jd3 = st.columns(3)
                            juros_pct = jd1.number_input("Juros (%)", min_value=0.0, value=0.0, step=0.5, key="juros_pct")
                            desconto_rs = jd2.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=0.01, key="desconto_rs")
                            valor_juros = valor_original * (juros_pct / 100)
                            valor_final = valor_original + valor_juros - desconto_rs
                            jd3.metric("Valor Final", f"R$ {valor_final:,.2f}")

                            if valor_final <= 0:
                                st.error("O valor final não pode ser zero ou negativo.")
                            else:
                                novo_venc_jd = st.date_input("Novo Vencimento", value=pd.to_datetime(dup_data['data_vencimento']).date(), key="venc_jd")
                                obs_juros = f" [Juros {juros_pct}%: +R${valor_juros:,.2f}]" if juros_pct > 0 else ""
                                obs_desc = f" [Desc: -R${desconto_rs:,.2f}]" if desconto_rs > 0 else ""
                                if st.button("Aplicar Juros/Desconto", type="primary"):
                                    nova_descricao = dup_data['descricao'] + obs_juros + obs_desc
                                    run_query("UPDATE contas_a_pagar SET data_vencimento=?, valor=?, descricao=? WHERE id=?",
                                              (novo_venc_jd.strftime("%Y-%m-%d"), valor_final, nova_descricao, dup_id))
                                    st.success(f"Duplicata atualizada! Novo valor: R$ {valor_final:,.2f}")
                                    import time; time.sleep(1); st.rerun()

                        elif acao == "Reparcelar":
                            st.markdown(f"**Valor original a reparcelar:** R$ {valor_original:,.2f}")
                            rp1, rp2 = st.columns(2)
                            n_parc = rp1.number_input("Nº de Parcelas", min_value=2, value=2, step=1, key="n_repar")
                            dias_entre = rp2.number_input("Dias entre Parcelas", min_value=1, value=30, step=1, key="dias_repar")
                            data_inicio = st.date_input("Data da 1ª Parcela", value=date.today(), key="dt_repar")

                            valor_parc = round(valor_original / n_parc, 2)
                            diff_parc = round(valor_original - valor_parc * n_parc, 2)
                            preview = []
                            for i in range(n_parc):
                                v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                                d = data_inicio + timedelta(days=dias_entre * i)
                                preview.append({"Parcela": f"{i+1}/{n_parc}", "Vencimento": d.strftime("%d/%m/%Y"), "Valor": f"R$ {v:,.2f}"})
                            st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

                            if st.button("Confirmar Reparcelamento", type="primary"):
                                run_query("UPDATE contas_a_pagar SET status='CANCELADO', descricao = descricao || ' [REPARCELADO]' WHERE id=?", (dup_id,))
                                for i in range(n_parc):
                                    v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                                    d = data_inicio + timedelta(days=dias_entre * i)
                                    nova_desc_rp = f"{dup_data['descricao']} (Repar. {i+1}/{n_parc})"
                                    run_query(
                                        "INSERT INTO contas_a_pagar (fornecedor_id, compra_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                        (int(dup_data['fornecedor_id']) if pd.notna(dup_data['fornecedor_id']) else None,
                                         int(dup_data['compra_id']) if pd.notna(dup_data['compra_id']) else None,
                                         int(dup_data['plano_conta_id']) if pd.notna(dup_data['plano_conta_id']) else None,
                                         nova_desc_rp, v, d.strftime("%Y-%m-%d")))
                                st.success(f"Reparcelamento concluído! {n_parc} novas duplicatas criadas.")
                                import time; time.sleep(1); st.rerun()

    # ------------------ ABA 3: CONTAS A RECEBER ------------------
    with tab3:
        st.subheader("Contas a Receber (Vendas e Calotes)")
        st.markdown("Onde controlamos quem nos deve e qual data cobrar.")
        
        # Opcional manual input (Já que as vendas futuras deveriam alimentar isso, mas pode surgir algo rápido)
        with st.expander("➕ Lançar uma Duplicata a Receber"):
            # Buscar clientes
            df_cli = fetch_all("SELECT id, nome FROM clientes ORDER BY nome")
            op_cli = {"-- SELECIONE O CLIENTE --": "placeholder", "Genérico / Não Cadastrado": None}
            if not df_cli.empty:
                for _,r in df_cli.iterrows(): op_cli[r['nome']] = r['id']
                
            # Planos
            df_planos = fetch_all("SELECT id, nome FROM planos_de_contas WHERE categoria LIKE '%Receita%'")
            op_plan = {}
            if not df_planos.empty:
                for _,r in df_planos.iterrows(): op_plan[r['nome']] = r['id']
                
            with st.form("lancar_receber", clear_on_submit=True):
                c1, c2 = st.columns(2)
                cli_nome = c1.selectbox("Cliente", list(op_cli.keys()))
                venc = c2.date_input("Vencimento", date.today() + timedelta(days=15))
                
                c3, c4 = st.columns([2, 1])
                desc = c3.text_input("Fatura (No. NF, Parcela, Referência)")
                val_r = c4.number_input("Valor da Fatura (R$)", min_value=0.01)
                
                if st.form_submit_button("Lançar Promessa de Faturamento"):
                    if cli_nome == "-- SELECIONE O CLIENTE --":
                        st.error("Por favor, selecione um Cliente (ou 'Genérico / Não Cadastrado').")
                    elif not desc:
                        st.error("Preencha a descrição.")
                    else:
                        run_query("INSERT INTO contas_a_receber (cliente_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
                                  (op_cli[cli_nome], desc, val_r, venc.strftime("%Y-%m-%d")))
                        st.success("Boleto emitido (pendente)")
                        import time; time.sleep(1); st.rerun()

        # ======= FECHAMENTO DE CARTEIRA =======
        st.markdown("---")
        with st.expander("📔 Fechamento Semanal de Carteira (Gerador de Extrato / Fiado)"):
            st.markdown("Gere um relatório consolidado de todas as faturas pendentes de um cliente específico para cobrar de uma vez só.")
            
            df_clientes_pendentes = fetch_all("""
                SELECT DISTINCT cl.id, cl.nome 
                FROM contas_a_receber c
                JOIN clientes cl ON c.cliente_id = cl.id
                WHERE c.status = 'PENDENTE'
            """)
            
            if df_clientes_pendentes.empty:
                st.info("Não há nenhum cliente com saldo devedor/faturas pendentes.")
            else:
                opcoes_cli_pend = {r['nome']: r['id'] for _, r in df_clientes_pendentes.iterrows()}
                cli_fechamento = st.selectbox("Selecione o Cliente para Fechamento:", ["-- SELECIONE --"] + list(opcoes_cli_pend.keys()))
                
                if cli_fechamento != "-- SELECIONE --":
                    c_id_fech = opcoes_cli_pend[cli_fechamento]
                    df_fat_cli = fetch_all("SELECT id, descricao, valor, data_vencimento FROM contas_a_receber WHERE cliente_id=? AND status='PENDENTE' ORDER BY data_vencimento ASC", (c_id_fech,))
                    
                    st.markdown(f"**Títulos Pendentes: {cli_fechamento}**")
                    df_fat_cli['Gerar no Relatório?'] = True
                    df_fat_cli['data_vencimento_original'] = pd.to_datetime(df_fat_cli['data_vencimento']).dt.strftime('%d/%m/%Y')
                    
                    df_view_fech = df_fat_cli[['Gerar no Relatório?', 'id', 'descricao', 'data_vencimento_original', 'valor']]
                    
                    edited_fech = st.data_editor(df_view_fech, hide_index=True, width="stretch",
                                                 column_config={
                                                     "Gerar no Relatório?": st.column_config.CheckboxColumn("Incluir?", default=True),
                                                     "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")
                                                 })
                    
                    selecionados_fech = edited_fech[edited_fech['Gerar no Relatório?'] == True]
                    
                    if not selecionados_fech.empty:
                        total_fech = selecionados_fech['valor'].sum()
                        
                        col_fa, col_fb = st.columns([1, 1])
                        dt_pgto_estimada = col_fa.date_input("Data de Vencimento/Acerto Combinada para o Extrato:", date.today())
                        
                        if col_fb.button("🖨️ Gerar Extrato de Fechamento (A4)", type="primary", use_container_width=True):
                            from utils_carteira import gerar_html_carteira
                            import streamlit.components.v1 as components
                            
                            faturas_list = selecionados_fech.to_dict('records')
                            
                            html_carteira = gerar_html_carteira(
                                cliente_nome=cli_fechamento,
                                dados_faturas=faturas_list,
                                total_faturas=total_fech,
                                data_pagamento_estimada=dt_pgto_estimada.strftime('%d/%m/%Y')
                            )
                            components.html(html_carteira, height=800, scrolling=True)
                            st.success(f"Extrato gerado com sucesso! Total: R$ {total_fech:,.2f}")

        st.markdown("---")
        # Exibir Recibos
        df_receber = fetch_all("""
            SELECT c.id, c.descricao as 'Fatura', cl.nome as 'Cliente', 
                   c.data_vencimento as 'Vencimento', c.valor as 'Valor', 
                   c.status as 'Status', c.data_recebimento as 'Recebido Em'
            FROM contas_a_receber c
            LEFT JOIN clientes cl ON c.cliente_id = cl.id
            ORDER BY c.data_vencimento ASC
        """)
        
        if df_receber.empty:
             st.info("Nenhuma fatura lançada na vida financeira da empresa ainda.")
        else:
             stat_f = st.selectbox("Filtro:", ["PENDENTE", "RECEBIDO", "TODAS"], key="filt_rec")
             df_rv = df_receber.copy()
             if stat_f != "TODAS":
                 df_rv = df_rv[df_rv['Status'] == stat_f]
                 
             if df_rv.empty:
                 st.warning("Vazio neste status.")
             else:
                 df_rv['Vencimento'] = pd.to_datetime(df_rv['Vencimento']).dt.strftime('%d/%m/%Y')
                 df_rv['Recebido Em'] = pd.to_datetime(df_rv['Recebido Em']).dt.strftime('%d/%m/%Y').fillna("-")
                 df_rv['Valor (R$)'] = df_rv['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                 st.dataframe(df_rv, hide_index=True, width="stretch")
                 
             if "PENDENTE" in df_rv['Status'].values:
                 with st.expander("🟩 Acusar Recebimento de Clientes (Lote)"):
                     df_rd = df_receber[df_receber['Status'] == "PENDENTE"].copy()
                     df_rd['Receber?'] = False
                     
                     df_view_rec = df_rd[['Receber?', 'id', 'Cliente', 'Fatura', 'Vencimento', 'Valor']]
                     
                     st.markdown("**Marque as faturas que os clientes pagaram hoje (mantém valor base):**")
                     edited_rec = st.data_editor(df_view_rec, hide_index=True, width="stretch",
                                                 column_config={"Receber?": st.column_config.CheckboxColumn("Receber?", default=False),
                                                                "Valor": st.column_config.NumberColumn("Valor Base (R$)", format="%.2f")})
                     
                     selec_rec = edited_rec[edited_rec['Receber?'] == True]
                     
                     if not selec_rec.empty:
                         st.markdown("---")
                         rA, rB, rC = st.columns(3)
                         dt_rec = rA.date_input("Data que o dinheiro caiu (Lote)", date.today())
                         banco_destino = rB.selectbox("PAGO EM QUAL BANCO (Lote)?", list(opcoes_bancos.keys()))
                         
                         if rC.button("💸 Confirmar Recebimento em Lote", type="primary", use_container_width=True):
                             bCid = opcoes_bancos[banco_destino]
                             
                             for _, r in selec_rec.iterrows():
                                 rr_id = int(r['id'])
                                 v_base = float(r['Valor'])
                                 cli = r['Cliente'] if pd.notna(r['Cliente']) else "Diversos"
                                 fat = r['Fatura']
                                 
                                 run_query("UPDATE contas_a_receber SET status='RECEBIDO', data_recebimento=?, conta_bancaria_id=? WHERE id=?",
                                           (dt_rec.strftime("%Y-%m-%d"), bCid, rr_id))
                                 
                                 # Gatilho de repasse de comissão se for no momento de LIQUIDAÇÃO DE TITULO
                                 df_v = fetch_all("SELECT venda_id FROM contas_a_receber WHERE id = ?", (rr_id,))
                                 if not df_v.empty and pd.notna(df_v.iloc[0]['venda_id']):
                                     vid = int(df_v.iloc[0]['venda_id'])
                                     gerar_comissao_se_necessario(vid, 'LIQUIDAÇÃO', cli)
                                 desc_final = f"REC. Cliente {cli}: {fat}"
                                 run_query("INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, fonte_id, conta_bancaria_id, conciliado) VALUES (?, 'Entrada', 'Receita Com Vendas', ?, ?, ?, ?, TRUE)",
                                           (dt_rec.strftime("%Y-%m-%d"), desc_final, v_base, rr_id, bCid))
                                           
                             st.success(f"✔️ {len(selec_rec)} recebimentos injetados no Fluxo do banco {banco_destino}!")
                             import time; time.sleep(2); st.rerun()

             # --- RENEGOCIAÇÃO / EDIÇÃO DE RECEBÍVEL ---
             with st.expander("✏️ Renegociar / Editar Recebível"):
                 df_rec_edit = fetch_all("""
                     SELECT c.id, cl.nome as cliente_nome, c.descricao, c.valor, c.data_vencimento, c.status, c.venda_id 
                     FROM contas_a_receber c 
                     LEFT JOIN clientes cl ON c.cliente_id = cl.id 
                     WHERE c.status='PENDENTE' ORDER BY c.data_vencimento
                 """)
                 if df_rec_edit.empty:
                     st.info("Nenhuma duplicata a receber pendente para editar.")
                 else:
                     opts_edit_rec = {}
                     for _, r in df_rec_edit.iterrows():
                         cli_lbl = r['cliente_nome'] if pd.notna(r['cliente_nome']) else "Genérico/Sem Cliente"
                         lbl = f"#{r['id']} | {cli_lbl} | {r['descricao']} | R$ {r['valor']:,.2f} | Venc: {pd.to_datetime(r['data_vencimento']).strftime('%d/%m/%Y')}"
                         opts_edit_rec[lbl] = r['id']
                     
                     sel_edit_rec = st.selectbox("Selecione o recebível:", list(opts_edit_rec.keys()), key="edit_rec_sel")
                     if sel_edit_rec:
                         rec_id = opts_edit_rec[sel_edit_rec]
                         rec_data = fetch_all("SELECT * FROM contas_a_receber WHERE id=?", (rec_id,)).iloc[0]
                         valor_original = float(rec_data['valor'])
                         venda_id = rec_data['venda_id']

                         if pd.notna(venda_id):
                             st.warning(f"⚠️ **Atenção:** Este recebível está vinculado à **Venda #{int(venda_id)}**.")

                         acao_rec = st.radio("O que deseja fazer?", ["Alterar Vencimento/Valor", "Aplicar Juros / Desconto", "Reparcelar", "Excluir/Cancelar"], horizontal=True, key="acao_rec")

                         if acao_rec == "Alterar Vencimento/Valor":
                             with st.form("form_edit_rec"):
                                 ed1, ed2 = st.columns(2)
                                 novo_venc = ed1.date_input("Novo Vencimento", value=pd.to_datetime(rec_data['data_vencimento']).date())
                                 
                                 if pd.notna(venda_id):
                                     st.info("ℹ️ Para títulos de vendas, a alteração de valor é bloqueada aqui para evitar descompasso. Edite o valor pago diretamente na tabela de Baixa (recebimento) para lançar descontos/acréscimos no DRE.")
                                     novo_valor = st.number_input("Valor Original (R$)", value=valor_original, disabled=True, key="dis_val_rec")
                                 else:
                                     novo_valor = ed2.number_input("Novo Valor (R$)", value=valor_original, min_value=0.01)
                                     
                                 nova_desc = st.text_input("Descrição", value=rec_data['descricao'])
                                 if st.form_submit_button("Salvar Alteração"):
                                     run_query("UPDATE contas_a_receber SET data_vencimento=?, valor=?, descricao=? WHERE id=?",
                                               (novo_venc.strftime("%Y-%m-%d"), novo_valor, nova_desc, rec_id))
                                     st.success("Recebível atualizado!")
                                     import time; time.sleep(1); st.rerun()

                         elif acao_rec == "Aplicar Juros / Desconto":
                             if pd.notna(venda_id):
                                 st.warning("⚠️ Esta duplicata está vinculada a uma Venda. Para aplicar descontos ou juros em títulos de vendas comerciais de forma que conste no DRE, digite o valor final pago diretamente na tabela de recebimento (Lote) ao confirmar o pagamento.")
                             else:
                                 st.markdown(f"**Valor original:** R$ {valor_original:,.2f}")
                                 jd1, jd2, jd3 = st.columns(3)
                                 juros_pct = jd1.number_input("Juros (%)", min_value=0.0, value=0.0, step=0.5, key="rec_juros_pct")
                                 desconto_rs = jd2.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=0.01, key="rec_desconto_rs")
                                 valor_juros = valor_original * (juros_pct / 100)
                                 valor_final = valor_original + valor_juros - desconto_rs
                                 jd3.metric("Valor Final", f"R$ {valor_final:,.2f}")

                                 if valor_final <= 0:
                                     st.error("O valor final não pode ser zero ou negativo.")
                                 else:
                                     novo_venc_jd = st.date_input("Novo Vencimento", value=pd.to_datetime(rec_data['data_vencimento']).date(), key="rec_venc_jd")
                                     obs_juros = f" [Juros {juros_pct}%: +R${valor_juros:,.2f}]" if juros_pct > 0 else ""
                                     obs_desc = f" [Desc: -R${desconto_rs:,.2f}]" if desconto_rs > 0 else ""
                                     if st.button("Aplicar Juros/Desconto", type="primary", key="btn_rec_jd"):
                                         nova_descricao = rec_data['descricao'] + obs_juros + obs_desc
                                         run_query("UPDATE contas_a_receber SET data_vencimento=?, valor=?, descricao=? WHERE id=?",
                                                   (novo_venc_jd.strftime("%Y-%m-%d"), valor_final, nova_descricao, rec_id))
                                         st.success(f"Recebível atualizado! Novo valor: R$ {valor_final:,.2f}")
                                         import time; time.sleep(1); st.rerun()

                         elif acao_rec == "Reparcelar":
                             st.markdown(f"**Valor original a reparcelar:** R$ {valor_original:,.2f}")
                             rp1, rp2 = st.columns(2)
                             n_parc = rp1.number_input("Nº de Parcelas", min_value=2, value=2, step=1, key="rec_n_repar")
                             dias_entre = rp2.number_input("Dias entre Parcelas", min_value=1, value=30, step=1, key="rec_dias_repar")
                             data_inicio = st.date_input("Data da 1ª Parcela", value=date.today(), key="rec_dt_repar")

                             valor_parc = round(valor_original / n_parc, 2)
                             diff_parc = round(valor_original - valor_parc * n_parc, 2)
                             preview = []
                             for i in range(n_parc):
                                 v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                                 d = data_inicio + timedelta(days=dias_entre * i)
                                 preview.append({"Parcela": f"{i+1}/{n_parc}", "Vencimento": d.strftime("%d/%m/%Y"), "Valor": f"R$ {v:,.2f}"})
                             st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

                             if st.button("Confirmar Reparcelamento", type="primary", key="btn_rec_rep"):
                                 run_query("UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ' [REPARCELADO]' WHERE id=?", (rec_id,))
                                 for i in range(n_parc):
                                     v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                                     d = data_inicio + timedelta(days=dias_entre * i)
                                     nova_desc_rp = f"{rec_data['descricao']} (Repar. {i+1}/{n_parc})"
                                     run_query(
                                         "INSERT INTO contas_a_receber (cliente_id, venda_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                         (int(rec_data['cliente_id']) if pd.notna(rec_data['cliente_id']) else None,
                                          int(rec_data['venda_id']) if pd.notna(rec_data['venda_id']) else None,
                                          int(rec_data['plano_conta_id']) if pd.notna(rec_data['plano_conta_id']) else None,
                                          nova_desc_rp, v, d.strftime("%Y-%m-%d")))
                                 st.success(f"Reparcelamento concluído! {n_parc} novos recebíveis criados.")
                                 import time; time.sleep(1); st.rerun()

                         elif acao_rec == "Excluir/Cancelar":
                             if pd.notna(venda_id):
                                 st.error("❌ Não é permitido cancelar/excluir recebíveis de vendas faturadas por aqui. Para excluir, você deve desfazer o faturamento do pedido correspondente na tela de Faturamento.")
                             else:
                                 st.markdown("⚠️ **Tem certeza que deseja cancelar/excluir este recebível?**")
                                 st.markdown("Esta ação mudará o status do recebível para `'CANCELADO'` e ele não aparecerá mais nos recebimentos pendentes.")
                                 if st.button("Confirmar Cancelamento/Exclusão", type="primary", key="btn_rec_del"):
                                     run_query("UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ' [CANCELADO]' WHERE id=?", (rec_id,))
                                     st.success("Recebível cancelado com sucesso!")
                                     import time; time.sleep(1); st.rerun()

    # ------------------ ABA 4: CONCILIAÇÃO BANCÁRIA ------------------
    with tab4:
        st.subheader("Auditoria e Conciliação Financeira c/ Inteligência de Dados")
        # Filtros de Conta
        conta_con = st.selectbox("Filtrar para verificar:", ["TODAS AS CONTAS"] + list(opcoes_bancos.keys()))
        
        # ----------------- IMPORTADOR UPLOADER CSV -----------------
        with st.expander("📂 Robô de Conciliação em Lote (Importar CSV do Banco)"):
            st.info('''
            **Regra de Ouro do Arquivo CSV:** Seu CSV precisa ter exatamente 3 colunas (Data, Historico, Valor). 
            Se a saída foi paga, o valor no CSV deve estar com um sinal negativo (Ex: -500.00).
            ''')
            b_alvo = st.selectbox("O CSV pertence a qual Banco/Conta?", list(opcoes_bancos.keys()), key="csv_banco")
            
            uploaded_file = st.file_uploader("Suba a planilha extrato.csv padrão aqui:", type=["csv"])
            if uploaded_file is not None:
                try:
                    df_csv = pd.read_csv(uploaded_file, sep=None, engine='python')
                    st.write("Visão Raio-X do seu arquivo no sistema:")
                    st.dataframe(df_csv.head(5), width="stretch")
                    
                    if st.button("💥 Iniciar Mapeamento Mágico de Lotes"):
                        # Heurística Mágica: Vamos achar no ERP o que bate cravado com o Valor ABSOLUTO do CSV
                        df_b_alvo = fetch_all(f"SELECT id, valor, conciliado FROM fluxo_caixa WHERE conta_bancaria_id={opcoes_bancos[b_alvo]} AND conciliado=FALSE")
                        
                        if df_b_alvo.empty:
                            st.warning("Não há nenhuma fatura pendente de conciliação no ERP para este banco. Tudo perfeitamente limpo!")
                        else:
                            # A mágica: Array de valores do ERP para comparar
                            sucessos = 0
                            lote_ids_para_conciliar = []
                            
                            # Simulação Mágica Progressiva: (Itera sobre o CSV, e tenta achar matching de valor exato não pareado ainda)
                            if 'Valor' in df_csv.columns or 'valor' in df_csv.columns:
                                col_v = 'Valor' if 'Valor' in df_csv.columns else 'valor'
                                for _, row_csv in df_csv.iterrows():
                                    val_csv = abs(float(row_csv[col_v]))
                                    
                                    # Procura no dataframe do banco alvo o match perfeito que não pegamos ainda
                                    match_idx = df_b_alvo.index[(df_b_alvo['valor'] == val_csv) & (~df_b_alvo['id'].isin(lote_ids_para_conciliar))].tolist()
                                    if match_idx:
                                        lote_ids_para_conciliar.append(int(df_b_alvo.loc[match_idx[0], 'id']))
                                        sucessos += 1
                                        
                            st.success(f"🤖 O Robô localizou exatamente **{sucessos}** operações fiduciárias (valores perfeitos) que constam no seu ERP e não estavam conciliados.")
                            
                            if sucessos > 0:
                                if st.button(f"Acato. Conciliar os {sucessos} itens agora!", type="primary"):
                                    for lid in lote_ids_para_conciliar:
                                        run_query("UPDATE fluxo_caixa SET conciliado=TRUE WHERE id=?", (lid,))
                                    st.success("Milagre Financeiro Efetuado. Extrato rebatido!")
                                    import time; time.sleep(1); st.rerun()
                except Exception as e:
                    st.error(f"Seu arquivo CSV parece corrompido ou fora dos padrões do Pandas: {e}")
                    
        st.markdown("---")

        query_con = """
            SELECT fc.id, fc.data as 'Data', fc.tipo as 'Movimentação', 
                   fc.descricao as 'Histórico', fc.valor as 'Valor', 
                   cb.nome as 'Banco', fc.conciliado as 'Revisado'
            FROM fluxo_caixa fc
            LEFT JOIN contas_bancarias cb ON fc.conta_bancaria_id = cb.id
            ORDER BY fc.data ASC, fc.id ASC
        """
        
        df_ext = fetch_all(query_con)
        if df_ext.empty:
            st.info("O livro de extratos está impecavelmente vazio.")
        else:
            if conta_con != "TODAS AS CONTAS":
                df_ext = df_ext[df_ext['Banco'] == conta_con]
                
            if df_ext.empty:
                st.warning(f"O banco {conta_con} está limpo sem histórico!")
            else:
                # ----------------- SALDO PROGRESSIVO -----------------
                saldo_inicial_conta = 0.0
                if conta_con != "TODAS AS CONTAS":
                    saldo_inicial_conta = float(df_bancos[df_bancos['nome'] == conta_con]['saldo_inicial'].iloc[0])
                else:
                    saldo_inicial_conta = sum([float(s) for s in df_bancos['saldo_inicial']])
                    
                saldos_acumulados = []
                acc = saldo_inicial_conta
                for _, r in df_ext.iterrows():
                    val = float(r['Valor'])
                    if r['Movimentação'] == 'Entrada':
                        acc += val
                    else:
                        acc -= val
                    saldos_acumulados.append(acc)
                    
                df_ext['Saldo Após Linha'] = saldos_acumulados
                
                # Exibir Resumo no Topo do Grid
                st.info(f"Saldo Inicial Configurado: R$ {saldo_inicial_conta:,.2f} |  **Saldo Acumulado Atual (Fim da Linha): R$ {acc:,.2f}**")
                
                # Prepara para exibir de cima para baixo reverso (mais novo prrimeiro)
                df_ext = df_ext.sort_values(by=['Data', 'id'], ascending=[False, False])
                df_ext['Data'] = pd.to_datetime(df_ext['Data']).dt.strftime('%d/%m/%Y')
                
                # Formatação
                df_edt = df_ext.copy()
                df_edt['Revisado'] = df_edt['Revisado'].astype(bool)
                df_edt['Valor Físico'] = df_edt['Valor'].apply(lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_edt['Saldo Bancário Acumulado'] = df_edt['Saldo Após Linha'].apply(lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    
                st.markdown("**Grid Auditável Diário** (Marque como CONCILIADO as linhas conferidas)")
                
                edited_df = st.data_editor(
                    df_edt[['id', 'Data', 'Banco', 'Movimentação', 'Histórico', 'Valor Físico', 'Saldo Bancário Acumulado', 'Revisado']],
                    hide_index=True,
                    disabled=["id", "Data", "Banco", "Movimentação", "Histórico", "Valor Físico", "Saldo Bancário Acumulado"],
                    width="stretch",
                    column_config={
                        "Revisado": st.column_config.CheckboxColumn("Tique se Bateu ✅", help="Marque se confirmou na conta do banco.", default=False)
                    }
                )
                
                if st.button("Salvar Modificações de Conciliação"):
                    for _, row in edited_df.iterrows():
                        n_c = True if row['Revisado'] else False
                        db_c = bool(df_ext[df_ext['id'] == row['id']].iloc[0]['Revisado'])
                        if n_c != db_c:
                            run_query("UPDATE fluxo_caixa SET conciliado=? WHERE id=?", (n_c, row['id']))
                    st.success("Extrato Oficializado pela Gerência!")
                    import time; time.sleep(1); st.rerun()

    # ------------------ ABA 5: TRANSFERÊNCIA ENTRE CONTAS ------------------
    with tab5:
        st.subheader("🔄 Transferência de Recursos entre Contas e Tesouraria")
        st.markdown("""
        Utilize este formulário para registrar a transferência de fundos entre suas contas bancárias e o caixa físico (Tesouraria).
        Isso registrará automaticamente um lançamento de saída na conta de origem e um lançamento de entrada na conta de destino.
        """)
        
        with st.form("form_transferencia_contas", clear_on_submit=True):
            col_t1, col_t2 = st.columns(2)
            
            # Conta Origem
            opcoes_origem = {f"{r['nome']}": r['id'] for _, r in df_bancos.iterrows()}
            conta_origem_lbl = col_t1.selectbox("Conta de Origem (De onde sai o dinheiro)", list(opcoes_origem.keys()))
            
            # Conta Destino
            opcoes_destino = {f"{r['nome']}": r['id'] for _, r in df_bancos.iterrows() if f"{r['nome']}" != conta_origem_lbl}
            if opcoes_destino:
                conta_destino_lbl = col_t2.selectbox("Conta de Destino (Para onde vai o dinheiro)", list(opcoes_destino.keys()))
            else:
                conta_destino_lbl = col_t2.selectbox("Conta de Destino (Para onde vai o dinheiro)", ["Cadastre outra conta ativa para realizar transferências"])
                
            col_t3, col_t4 = st.columns([1, 2])
            valor_transf = col_t3.number_input("Valor da Transferência (R$)", min_value=0.00, value=0.00, step=50.0, format="%.2f")
            data_transf = col_t4.date_input("Data da Transferência", date.today())
            
            obs_transf = st.text_input("Observação / Histórico", value="Transferência Interna de Recursos")
            
            btn_transf = st.form_submit_button("🔄 Confirmar Transferência", type="primary", use_container_width=True)
            
        if btn_transf:
            if not opcoes_destino or conta_destino_lbl == "Cadastre outra conta ativa para realizar transferências":
                st.error("Erro: Você precisa de pelo menos duas contas ativas para realizar uma transferência.")
            elif conta_origem_lbl == conta_destino_lbl:
                st.error("Erro: A conta de origem e destino devem ser diferentes.")
            elif valor_transf <= 0.0:
                st.error("Erro: O valor da transferência deve ser maior que zero (R$ 0,00).")
            else:
                id_origem = opcoes_origem[conta_origem_lbl]
                id_destino = opcoes_destino[conta_destino_lbl]
                
                # 1. Registrar Saída na Conta de Origem
                desc_saida = f"Transf. p/ {conta_destino_lbl} | {obs_transf}"
                run_query(
                    "INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, conta_bancaria_id, conciliado) VALUES (?, 'Saída', 'Transferência', ?, ?, ?, TRUE)",
                    (data_transf.strftime("%Y-%m-%d"), desc_saida, valor_transf, id_origem)
                )
                
                # 2. Registrar Entrada na Conta de Destino
                desc_entrada = f"Transf. de {conta_origem_lbl} | {obs_transf}"
                run_query(
                    "INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, conta_bancaria_id, conciliado) VALUES (?, 'Entrada', 'Transferência', ?, ?, ?, TRUE)",
                    (data_transf.strftime("%Y-%m-%d"), desc_entrada, valor_transf, id_destino)
                )
                
                st.success(f"✔️ Transferência de R$ {valor_transf:,.2f} realizada com sucesso de '{conta_origem_lbl}' para '{conta_destino_lbl}'!")
                import time; time.sleep(1.5); st.rerun()

    # ------------------ Guia 6: AUDITORIA LOGÍSTICA ------------------
    with tab6:
        st.subheader("🚚 Auditoria de Comprovantes Logísticos")
        st.markdown("""
        Utilize esta área para auditar os comprovantes de entrega (Canhotos de Viagem) e de descarga (Taxa de CD) 
        antes de efetuar o pagamento correspondente de fretes e tarifas.
        """)
        
        # Recarregar df_all_contas para garantir que esteja atualizado na aba de auditoria
        df_all_contas = fetch_all("""
            SELECT c.id, f.nome_fantasia as 'Fornecedor', p.nome as 'Planta de Custo', 
                   c.descricao as 'Descrição/Fatura', c.data_vencimento as 'Vencimento', 
                   c.valor as 'Valor', c.status as 'Status', c.data_pagamento as 'Data PGTO',
                   c.comprovante_url as 'Comprovante', c.cliente_id
            FROM contas_a_pagar c
            LEFT JOIN fornecedores f ON c.fornecedor_id = f.id
            LEFT JOIN planos_de_contas p ON c.plano_conta_id = p.id
            ORDER BY c.data_vencimento ASC
        """)
        
        # --- VISUALIZADOR DE CANHOTOS ---
        with st.expander("🔍 Auditar Canhotos de Viagens (Transportadoras)", expanded=True):
            st.markdown("Verifique os comprovantes anexados pela expedição antes de autorizar o pagamento.")
            contas_man = df_all_contas[df_all_contas['Descrição/Fatura'].str.contains("Acerto Rota/Manifesto #", na=False)]
            if not contas_man.empty:
                opcoes_audit = {}
                for _, r in contas_man.iterrows():
                    try:
                        man_id = int(r['Descrição/Fatura'].split("#")[1].split("-")[0].strip())
                        opcoes_audit[f"Manifesto #{man_id} ({r['Fornecedor']})"] = man_id
                    except:
                        pass
                
                if opcoes_audit:
                    aud_selecionado = st.selectbox("Selecione a fatura de frete para auditar:", ["-- SELECIONE --"] + list(opcoes_audit.keys()))
                    if aud_selecionado != "-- SELECIONE --":
                        mid = opcoes_audit[aud_selecionado]
                        df_v_audit = fetch_all("SELECT id, comprovante_url FROM vendas WHERE manifesto_id=?", (mid,))
                        
                        if not df_v_audit.empty:
                            cols = st.columns(3)
                            for idx, row_v in df_v_audit.iterrows():
                                v_id = row_v['id']
                                url = row_v['comprovante_url']
                                with cols[idx % 3]:
                                    st.markdown(f"**NF/Pedido #{v_id}**")
                                    if pd.notna(url) and url != "":
                                        if str(url).lower().endswith(".pdf"):
                                            st.info(f"📄 Arquivo PDF (Acesse a pasta local): `{url}`")
                                        else:
                                            try:
                                                st.image(url, caption=f"Canhoto NF #{v_id}", use_container_width=True)
                                            except:
                                                st.error(f"Erro ao ler imagem: `{url}`")
                                    else:
                                        st.warning("Pendente")
                        else:
                            st.info("Não há pedidos atrelados a este manifesto.")
            else:
                st.info("Nenhuma fatura de frete com manifesto associado para auditar.")
        
        # --- AUDITORIA DE RECIBOS DE DESCARGA ---
        with st.expander("🧾 Auditar Recibos de Descarga (Taxa de CD) — Comprovantes da Logística", expanded=True):
            st.markdown("Revise os comprovantes de descarga enviados pela equipe logística antes de liquidar no Financeiro.")
            df_desc_ag = df_all_contas[
                df_all_contas['Descrição/Fatura'].str.contains("Taxa de Descarga", na=False)
            ]
            if df_desc_ag.empty:
                st.info("✅ Nenhuma taxa de descarga pendente de auditoria.")
            else:
                for _, rd in df_desc_ag.iterrows():
                    st.markdown(f"**#{rd['id']} | {rd['Descrição/Fatura']}**")
                    col_d1, col_d2 = st.columns([2, 1])
                    col_d2.metric("Valor", f"R$ {rd['Valor']:,.2f}".replace(',','X').replace('.',',').replace('X','.'))
                    col_d2.markdown(f"**Status:** `{rd['Status']}`")
                    comprov = rd.get('Comprovante', None)
                    if pd.notna(comprov) and comprov != "":
                        with col_d1:
                            if str(comprov).lower().endswith(".pdf"):
                                    st.info(f"📄 Recibo PDF salvo em: `{comprov}`")
                            else:
                                try:
                                    st.image(comprov, caption=f"Recibo de Descarga — #{rd['id']}", use_container_width=True)
                                except:
                                    st.warning(f"Arquivo salvo em: `{comprov}`")
                    else:
                        col_d1.warning("⏳ Recibo ainda não enviado pela Logística.")
                    st.markdown("---")

except Exception as e:
    st.error(f"Erro Crítico de Tela Bancária: {e}")
    st.code(traceback.format_exc())
