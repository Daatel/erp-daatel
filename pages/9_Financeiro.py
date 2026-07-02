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

@st.dialog("Lançamento Direto Bloqueado")
def mostrar_mensagem_bloqueio(username):
    st.markdown(f"""
    ### Olá, **{username}**!
    
    Pedimos desculpas pelo inconveniente, mas não é possível realizar um lançamento direto por aqui.
    
    Para manter a consistência e a exatidão do seu **DRE** (Demonstrativo do Resultado do Exercício), todos os lançamentos operacionais de entrada ou saída devem ser registrados obrigatoriamente através dos módulos de **Contas a Receber** e **Contas a Pagar**.
    
    Agradecemos imensamente a sua compreensão!
    """)
    if st.button("Entendido", use_container_width=True):
        st.rerun()

@st.dialog("Ajuste de saldo")
def mostrar_ajuste_saldo_modal(opcoes_bancos):
    st.write("Selecione a conta em que será realizado o ajuste:")
    
    # 1. Seleção de Conta
    conta_sel = st.selectbox("Conta *", list(opcoes_bancos.keys()), key="ajuste_conta_sel")
    
    st.write("Informe o valor desejado de saldo e a data correspondente a esse ajuste:")
    
    # 2. Entrada de Saldo Desejado e Data
    col1, col2 = st.columns(2)
    saldo_desejado = col1.number_input("Saldo desejado", min_value=0.00, value=0.00, step=100.0, format="%.2f", key="ajuste_saldo_desejado")
    data_ajuste = col2.date_input("Data de ajuste", date.today(), key="ajuste_data")
    
    # 3. Calcular o saldo atual da conta selecionada até a data informada
    b_id = opcoes_bancos[conta_sel]
    
    # Recupera o saldo inicial da conta
    df_b = fetch_all("SELECT saldo_inicial FROM contas_bancarias WHERE id=?", (b_id,))
    saldo_inicial = float(df_b.iloc[0]['saldo_inicial']) if not df_b.empty else 0.0
    
    # Soma todas as transações até a data selecionada
    df_f = fetch_all("SELECT tipo, valor FROM fluxo_caixa WHERE conta_bancaria_id = ? AND data <= ?", (b_id, data_ajuste.strftime("%Y-%m-%d")))
    saldo_atual_na_data = saldo_inicial
    for _, f in df_f.iterrows():
        val = float(f['valor'])
        if f['tipo'] == 'Entrada':
            saldo_atual_na_data += val
        else:
            saldo_atual_na_data -= val
            
    diferenca = saldo_desejado - saldo_atual_na_data
    
    col1.caption(f"Diferença do saldo atual: **R$ {diferenca:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.info("ℹ️ O ajuste será realizado por meio de um lançamento no dia selecionado para 'Data de ajuste'.")
    
    # 4. Gravação do Ajuste
    col_btn1, col_btn2 = st.columns(2)
    cancelar = col_btn1.button("Cancelar", use_container_width=True, key="ajuste_cancel_btn")
    salvar = col_btn2.button("Salvar Ajuste", type="primary", use_container_width=True, key="ajuste_save_btn")
    
    if cancelar:
        st.rerun()
        
    if salvar:
        if abs(diferenca) < 0.01:
            st.warning("O saldo desejado já é igual ao saldo atual nesta data. Nenhum ajuste necessário.")
        else:
            tipo_ajuste = "Entrada" if diferenca > 0 else "Saída"
            valor_ajuste = abs(diferenca)
            desc_ajuste = f"Ajuste de saldo (Saldo desejado: R$ {saldo_desejado:,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
            
            run_query(
                "INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, conta_bancaria_id, conciliado) VALUES (?, ?, 'Ajuste de saldo', ?, ?, ?, TRUE)",
                (data_ajuste.strftime("%Y-%m-%d"), tipo_ajuste, desc_ajuste, valor_ajuste, b_id)
            )
            st.success("Ajuste de saldo registrado com sucesso!")
            import time; time.sleep(1); st.rerun()

@st.dialog("Transferência entre contas")
def mostrar_transferencia_modal(opcoes_bancos, df_bancos):
    st.write("Utilize este formulário para registrar a transferência de fundos entre suas contas bancárias:")
    
    col_t1, col_t2 = st.columns(2)
    
    # 1. Conta Origem
    opcoes_origem = {f"{r['nome']}": r['id'] for _, r in df_bancos.iterrows()}
    conta_origem_lbl = col_t1.selectbox("Conta de Origem (De onde sai o dinheiro) *", list(opcoes_origem.keys()), key="transf_origem_sel")
    
    # 2. Conta Destino
    opcoes_destino = {f"{r['nome']}": r['id'] for _, r in df_bancos.iterrows() if f"{r['nome']}" != conta_origem_lbl}
    if opcoes_destino:
        conta_destino_lbl = col_t2.selectbox("Conta de Destino (Para onde vai o dinheiro) *", list(opcoes_destino.keys()), key="transf_destino_sel")
    else:
        conta_destino_lbl = col_t2.selectbox("Conta de Destino (Para onde vai o dinheiro) *", ["Cadastre outra conta ativa para realizar transferências"], key="transf_destino_sel")
        
    col_t3, col_t4 = st.columns([1, 2])
    valor_transf = col_t3.number_input("Valor (R$) *", min_value=0.00, value=0.00, step=50.0, format="%.2f", key="transf_valor")
    data_transf = col_t4.date_input("Data da Transferência *", date.today(), key="transf_data")
    
    obs_transf = st.text_input("Observação / Histórico", value="Transferência Interna de Recursos", key="transf_obs")
    
    # 3. Gravação da Transferência
    col_btn1, col_btn2 = st.columns(2)
    cancelar = col_btn1.button("Cancelar", use_container_width=True, key="transf_cancel_btn")
    salvar = col_btn2.button("Confirmar Transferência", type="primary", use_container_width=True, key="transf_save_btn")
    
    if cancelar:
        st.rerun()
        
    if salvar:
        if not opcoes_destino or conta_destino_lbl == "Cadastre outra conta ativa para realizar transferências":
            st.error("Erro: Você precisa de pelo menos duas contas ativas para realizar uma transferência.")
        elif conta_origem_lbl == conta_destino_lbl:
            st.error("Erro: A conta de origem e destino devem ser diferentes.")
        elif valor_transf <= 0.0:
            st.error("Erro: O valor da transferência deve ser maior que zero (R$ 0,00).")
        else:
            id_origem = opcoes_origem[conta_origem_lbl]
            id_destino = opcoes_destino[conta_destino_lbl]
            
            with st.spinner("Registrando transferência..."):
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
                
            st.success(f"Transferência de R$ {valor_transf:,.2f} realizada com sucesso!")
            import time; time.sleep(1); st.rerun()

st.set_page_config(page_title="Financeiro e Tesouraria", layout="wide")
carregar_estilo()

st.markdown("""
<style>
/* Remove padding do topo da página do Streamlit para subir tudo de forma limpa e sem cortar o texto */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
</style>
<h1 style='font-size: 2.2rem; font-weight: 700; margin-top: -15px; margin-bottom: 20px; color: #1e293b;'>
Financeiro e Tesouraria
</h1>
""", unsafe_allow_html=True)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Painel Executivo", 
        "Contas a Pagar (Saída)", 
        "Contas a Receber (Entrada)", 
        "Caixas e Bancos",
        "Auditoria Logística"
    ])
    
    # ------------------ ABA 1: DASHBOARD E PROJEÇÃO 30D ------------------
    with tab1:
        # 1. Verification of Last Reconciliation (Tolerance D-1)
        df_max_conc = fetch_all("SELECT MAX(data) as max_data FROM fluxo_caixa WHERE conciliado = TRUE")
        last_conc_date = None
        out_of_tolerance = False
        if not df_max_conc.empty and pd.notna(df_max_conc.iloc[0]['max_data']):
            last_conc_date = pd.to_datetime(df_max_conc.iloc[0]['max_data']).date()
            if last_conc_date < hoje - timedelta(days=1):
                out_of_tolerance = True
        else:
            out_of_tolerance = True
            
        # Display dynamic reconciliation status badge using native Streamlit banners
        if out_of_tolerance:
            st.error(f"🚨 **ALERTA DE SEGURANÇA:** Conciliação financeira pendente! Último registro conciliado: {last_conc_date.strftime('%d/%m/%Y') if last_conc_date else 'nunca'}. A tolerância máxima é de D-1 (ontem). Efetue a conciliação na aba correspondente.")
        else:
            st.success(f"🟢 **CONCILIAÇÃO EM DIA:** Caixa conciliado até {last_conc_date.strftime('%d/%m/%Y') if last_conc_date else 'nunca'}.")
            
        # Header area
        st.markdown("### 🏆 Cockpit Financeiro Diário - Empório do Alho")
        
        # 2. TOP ROW CARDS (KPIs): Entra hoje, Sai hoje, Resultado do dia
        # Query planned receivables due today (PENDENTE)
        df_rec_hoje = fetch_all("SELECT SUM(valor) as total FROM contas_a_receber WHERE status='PENDENTE' AND data_vencimento=?", (hoje.strftime("%Y-%m-%d"),))
        entra_hoje_val = float(df_rec_hoje.iloc[0]['total'] or 0.0) if not df_rec_hoje.empty else 0.0
        
        # Query planned payables due today (PENDENTE)
        df_pag_hoje = fetch_all("SELECT SUM(valor) as total FROM contas_a_pagar WHERE status='PENDENTE' AND data_vencimento=?", (hoje.strftime("%Y-%m-%d"),))
        sai_hoje_val = float(df_pag_hoje.iloc[0]['total'] or 0.0) if not df_pag_hoje.empty else 0.0
        
        resultado_dia_val = entra_hoje_val - sai_hoje_val
        
        c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
        
        # Format values to BRL
        def to_brl(v):
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        c_kpi1.metric("Entra hoje", to_brl(entra_hoje_val))
        c_kpi2.metric("Sai hoje", to_brl(sai_hoje_val))
        c_kpi3.metric("Resultado do dia", to_brl(resultado_dia_val), 
                     delta=to_brl(resultado_dia_val) if resultado_dia_val != 0 else None,
                     delta_color="normal" if resultado_dia_val >= 0 else "inverse")
        
        st.markdown("---")
        
        # 3. MIDDLE ROW: A cobrar (vencido) & A pagar (vencido) tables
        c_mid_left, c_mid_right = st.columns(2)
        
        # --- LEFT: A COBRAR (VENCIDO) ---
        with c_mid_left:
            # Query pending overdue receivables
            df_vencidos_rec = fetch_all("""
                SELECT c.valor, c.data_vencimento, cl.nome as cliente_nome
                FROM contas_a_receber c
                JOIN clientes cl ON c.cliente_id = cl.id
                WHERE c.status = 'PENDENTE' AND c.data_vencimento < ?
            """, (hoje.strftime("%Y-%m-%d"),))
            
            total_vencido_rec = 0.0
            df_grouped_rec = pd.DataFrame()
            if not df_vencidos_rec.empty:
                total_vencido_rec = df_vencidos_rec['valor'].sum()
                df_vencidos_rec['dias'] = (hoje - pd.to_datetime(df_vencidos_rec['data_vencimento']).dt.date).apply(lambda x: x.days)
                df_grouped_rec = df_vencidos_rec.groupby('cliente_nome').agg(
                    dias_atraso=('dias', 'max'),
                    total_valor=('valor', 'sum')
                ).reset_index().sort_values('total_valor', ascending=False).head(5)
                
            st.markdown(f"#### 📅 A cobrar (vencido): **<span style='color:#ef4444;'>{to_brl(total_vencido_rec)}</span>**", unsafe_allow_html=True)
            
            if df_grouped_rec.empty:
                st.info("Nenhum valor vencido a cobrar. Excelente!")
            else:
                df_grouped_rec_view = df_grouped_rec.copy()
                df_grouped_rec_view['dias_atraso'] = df_grouped_rec_view['dias_atraso'].apply(lambda x: f"{x} dias")
                df_grouped_rec_view['total_valor'] = df_grouped_rec_view['total_valor'].apply(to_brl)
                df_grouped_rec_view.columns = ['Cliente', 'Maior Atraso', 'Saldo Total Devido']
                st.dataframe(df_grouped_rec_view, hide_index=True, use_container_width=True)
                
            st.caption("Ver todos os clientes na aba **Contas a Receber (Entrada)**")
            
        # --- RIGHT: A PAGAR (VENCIDO) ---
        with c_mid_right:
            # Query pending overdue payables
            df_vencidos_pag = fetch_all("""
                SELECT c.valor, c.data_vencimento, f.nome_fantasia as fornecedor_nome
                FROM contas_a_pagar c
                JOIN fornecedores f ON c.fornecedor_id = f.id
                WHERE c.status = 'PENDENTE' AND c.data_vencimento < ?
            """, (hoje.strftime("%Y-%m-%d"),))
            
            total_vencido_pag = 0.0
            df_grouped_pag = pd.DataFrame()
            if not df_vencidos_pag.empty:
                total_vencido_pag = df_vencidos_pag['valor'].sum()
                df_vencidos_pag['dias'] = (hoje - pd.to_datetime(df_vencidos_pag['data_vencimento']).dt.date).apply(lambda x: x.days)
                df_grouped_pag = df_vencidos_pag.groupby('fornecedor_nome').agg(
                    dias_atraso=('dias', 'max'),
                    total_valor=('valor', 'sum')
                ).reset_index().sort_values('total_valor', ascending=False).head(5)
                
            st.markdown(f"#### 📅 A pagar (vencido): **<span style='color:#b45309;'>{to_brl(total_vencido_pag)}</span>**", unsafe_allow_html=True)
            
            if df_grouped_pag.empty:
                st.info("Nenhuma conta vencida a pagar. Excelente!")
            else:
                df_grouped_pag_view = df_grouped_pag.copy()
                df_grouped_pag_view['dias_atraso'] = df_grouped_pag_view['dias_atraso'].apply(lambda x: f"{x} dias")
                df_grouped_pag_view['total_valor'] = df_grouped_pag_view['total_valor'].apply(to_brl)
                df_grouped_pag_view.columns = ['Fornecedor', 'Maior Atraso', 'Saldo Total a Pagar']
                st.dataframe(df_grouped_pag_view, hide_index=True, use_container_width=True)
                
            st.caption("Ver todos os fornecedores na aba **Contas a Pagar (Saída)**")
            
        st.markdown("---")
        
        # 4. CHART SECTION (14-Day Flow chart)
        st.subheader("📊 Painel de Liquidez Projetado (14 Dias)")
        
        # Checkbox to include overdue accounts in today's calculation
        incluir_atraso = st.checkbox("Considerar contas em atraso no gráfico", value=False, key="inc_atrasados_chk")
        
        # Fetch expected receivables and payables for the next 14 days (D0 to D13)
        df_rec_futuro = fetch_all("SELECT valor, data_vencimento FROM contas_a_receber WHERE status='PENDENTE'")
        df_pag_futuro = fetch_all("SELECT valor, data_vencimento FROM contas_a_pagar WHERE status='PENDENTE'")
        
        fluxo_14d = {}
        for i in range(14):
            d_alvo = hoje + timedelta(days=i)
            fluxo_14d[str(d_alvo)] = {"Entradas": 0.0, "Saidas": 0.0}
            
        # Distribute expected receivables (inputs)
        if not df_rec_futuro.empty:
            df_rec_futuro['venc_date'] = pd.to_datetime(df_rec_futuro['data_vencimento']).dt.date
            for _, r in df_rec_futuro.iterrows():
                v_date = r['venc_date']
                if v_date < hoje and incluir_atraso:
                    # Overdue added to D0 (today)
                    fluxo_14d[str(hoje)]["Entradas"] += float(r['valor'])
                elif str(v_date) in fluxo_14d:
                    fluxo_14d[str(v_date)]["Entradas"] += float(r['valor'])
                    
        # Distribute expected payables (outputs)
        if not df_pag_futuro.empty:
            df_pag_futuro['venc_date'] = pd.to_datetime(df_pag_futuro['data_vencimento']).dt.date
            for _, r in df_pag_futuro.iterrows():
                v_date = r['venc_date']
                if v_date < hoje and incluir_atraso:
                    # Overdue added to D0 (today)
                    fluxo_14d[str(hoje)]["Saidas"] += float(r['valor'])
                elif str(v_date) in fluxo_14d:
                    fluxo_14d[str(v_date)]["Saidas"] += float(r['valor'])
                    
        # Prepare Plotly chart data
        datas_14 = []
        entradas_14 = []
        saidas_14 = []
        saldos_14 = []
        
        saldo_proj = saldo_total_empresa
        
        for i in range(14):
            d_alvo = hoje + timedelta(days=i)
            d_str = "Hoje" if i == 0 else f"D+{i}"
            
            ent = fluxo_14d[str(d_alvo)]["Entradas"]
            sai = fluxo_14d[str(d_alvo)]["Saidas"]
            
            saldo_proj = saldo_proj + ent - sai
            
            datas_14.append(d_str)
            entradas_14.append(ent)
            saidas_14.append(sai)
            saldos_14.append(saldo_proj)
            
        fig_14 = go.Figure()
        
        # Receivables (positive columns)
        fig_14.add_trace(go.Bar(
            x=datas_14, y=entradas_14,
            name="Entradas Previstas",
            marker_color='#2563eb' # Royal Blue
        ))
        
        # Payables (negative columns)
        fig_14.add_trace(go.Bar(
            x=datas_14, y=[-s for s in saidas_14],
            name="Saídas Previstas",
            marker_color='#ef4444' # Red
        ))
        
        # Cumulative Cash line
        fig_14.add_trace(go.Scatter(
            x=datas_14, y=saldos_14,
            mode='lines+markers',
            name="💰 Saldo Acumulado",
            line=dict(color='#10b981', width=3, shape='spline'), # Emerald Green
            marker=dict(size=8, color='white', line=dict(width=2, color='#10b981'))
        ))
        
        fig_14.update_layout(
            xaxis_title="Período de Projeção",
            yaxis_title="R$ Valor",
            barmode='relative',
            hovermode="x unified",
            height=450,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        fig_14.update_yaxes(gridcolor='rgba(128,128,128,0.2)', zerolinecolor='rgba(128,128,128,0.5)', zerolinewidth=1)
        st.plotly_chart(fig_14, width="stretch")
        
        st.markdown("---")
        
        # 5. BOTTOM SECTION: Gerador de Relatórios
        st.subheader("📋 Gerador de Relatórios de Clientes e Fornecedores")
        st.markdown("Filtre e visualize a carteira pendente ou quitada de contas a receber (Clientes) e a pagar (Fornecedores) para exportar em lote.")
        
        # Initialize dates
        if 'rep_dt_inicio' not in st.session_state:
            st.session_state['rep_dt_inicio'] = date.today() - timedelta(days=30)
        if 'rep_dt_fim' not in st.session_state:
            st.session_state['rep_dt_fim'] = date.today() + timedelta(days=30)
            
        st.markdown("##### 📅 Filtro por Período de Vencimento")
        col_rf1, col_rf2, col_rf3, col_rf4, col_rf5 = st.columns([1, 1.3, 1.3, 2, 2])
        
        col_rf1.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if col_rf1.button("📅 Hoje", use_container_width=True, key="btn_rep_hoje"):
            st.session_state['rep_dt_inicio'] = date.today()
            st.session_state['rep_dt_fim'] = date.today()
            st.rerun()
            
        col_rf2.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if col_rf2.button("📅 Últimos 7 Dias", use_container_width=True, key="btn_rep_7d"):
            st.session_state['rep_dt_inicio'] = date.today() - timedelta(days=7)
            st.session_state['rep_dt_fim'] = date.today()
            st.rerun()
            
        col_rf3.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if col_rf3.button("📅 Últimos 30 Dias", use_container_width=True, key="btn_rep_30d"):
            st.session_state['rep_dt_inicio'] = date.today() - timedelta(days=30)
            st.session_state['rep_dt_fim'] = date.today()
            st.rerun()
            
        r_dt_inicio = col_rf4.date_input("Data de Início", value=st.session_state['rep_dt_inicio'], key="rep_start_date_input")
        r_dt_fim = col_rf5.date_input("Data de Fim", value=st.session_state['rep_dt_fim'], key="rep_end_date_input")
        
        # Update session states
        st.session_state['rep_dt_inicio'] = r_dt_inicio
        st.session_state['rep_dt_fim'] = r_dt_fim
        
        col_r3, col_r4 = st.columns(2)
        # Multi-select options
        status_opts = ["Vencido", "Em Dia", "Atraso", "Risco"]
        status_selected = col_r3.multiselect("Status do Título", status_opts, default=["Vencido", "Em Dia"], help="Escolha quais tipos de vencimento incluir no relatório.")
        
        tipo_selected = col_r4.multiselect("Tipo de Contato", ["Cliente", "Fornecedor"], default=["Cliente", "Fornecedor"])
        
        # Filtro de Contatos Específicos (Clientes/Fornecedores)
        contatos_opts = []
        if "Cliente" in tipo_selected:
            df_cl_opt = fetch_all("SELECT nome FROM clientes ORDER BY nome")
            if not df_cl_opt.empty:
                contatos_opts.extend([f"👤 Cliente: {n}" for n in df_cl_opt['nome'].tolist()])
        if "Fornecedor" in tipo_selected:
            df_forn_opt = fetch_all("SELECT nome_fantasia FROM fornecedores ORDER BY nome_fantasia")
            if not df_forn_opt.empty:
                contatos_opts.extend([f"🏭 Fornecedor: {n}" for n in df_forn_opt['nome_fantasia'].tolist()])
                
        contatos_selecionados = st.multiselect(
            "Filtrar por Clientes / Fornecedores específicos (Deixe vazio para trazer todos)", 
            options=contatos_opts, 
            default=None,
            key="rep_contatos_filter"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action button using the same standard green buttons as ERP (from estilo.py)
        if st.button("📊 Gerar Relatório de Clientes / Fornecedores", type="primary", use_container_width=False):
            # Clear previous report preview immediately to avoid displaying stale data on empty results
            if 'relatorio_preview' in st.session_state:
                del st.session_state['relatorio_preview']
            if 'relatorio_filtros' in st.session_state:
                del st.session_state['relatorio_filtros']
                
            # Fetch all possible receivables and payables in the period
            df_recs_rep = pd.DataFrame()
            df_pags_rep = pd.DataFrame()
            
            if "Cliente" in tipo_selected:
                df_recs_rep = fetch_all("""
                    SELECT c.id, c.data_vencimento, cl.nome as nome_contato, c.descricao, c.valor, c.status, 'Cliente' as tipo
                    FROM contas_a_receber c
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE c.data_vencimento BETWEEN ? AND ?
                """, (r_dt_inicio.strftime("%Y-%m-%d"), r_dt_fim.strftime("%Y-%m-%d")))
                
            if "Fornecedor" in tipo_selected:
                df_pags_rep = fetch_all("""
                    SELECT c.id, c.data_vencimento, f.nome_fantasia as nome_contato, c.descricao, c.valor, c.status, 'Fornecedor' as tipo
                    FROM contas_a_pagar c
                    JOIN fornecedores f ON c.fornecedor_id = f.id
                    WHERE c.data_vencimento BETWEEN ? AND ?
                """, (r_dt_inicio.strftime("%Y-%m-%d"), r_dt_fim.strftime("%Y-%m-%d")))
                
            # Combine
            df_combined = pd.concat([df_recs_rep, df_pags_rep], ignore_index=True)
            
            # Filtrar por Contatos Específicos
            if not df_combined.empty and contatos_selecionados:
                pares_filtrar = []
                for c_sel in contatos_selecionados:
                    if c_sel.startswith("👤 Cliente: "):
                        pares_filtrar.append(("Cliente", c_sel.replace("👤 Cliente: ", "")))
                    elif c_sel.startswith("🏭 Fornecedor: "):
                        pares_filtrar.append(("Fornecedor", c_sel.replace("🏭 Fornecedor: ", "")))
                
                df_combined = df_combined[df_combined.apply(lambda r: (r['tipo'], r['nome_contato']) in pares_filtrar, axis=1)]
            
            if df_combined.empty:
                st.warning("Nenhum registro encontrado para o período e tipo selecionados.")
            else:
                # Add extra dynamic statuses
                df_combined['venc_date'] = pd.to_datetime(df_combined['data_vencimento']).dt.date
                df_combined['dias_atraso'] = (hoje - df_combined['venc_date']).apply(lambda x: x.days)
                
                # Classify according to selected status tags
                def classificar_status(row):
                    if row['status'] == 'PENDENTE':
                        if row['venc_date'] < hoje:
                            if row['dias_atraso'] > 30:
                                return 'Risco'
                            else:
                                return 'Atraso' # Or Vencido
                        else:
                            return 'Em Dia'
                    elif row['status'] in ('RECEBIDO', 'PAGO'):
                        return 'Quitado'
                    return 'Outro'
                    
                df_combined['status_financeiro'] = df_combined.apply(classificar_status, axis=1)
                
                # Map selected filters
                mapped_status = []
                for s in status_selected:
                    if s == "Vencido":
                        mapped_status.append("Atraso")
                        mapped_status.append("Risco")
                    else:
                        mapped_status.append(s)
                        
                # Filter by status
                df_filtered = df_combined[df_combined['status_financeiro'].isin(mapped_status)].copy()
                
                if df_filtered.empty:
                    st.warning("Nenhum registro corresponde aos filtros de Status selecionados.")
                else:
                    filtro_contatos_str = f" | Contatos: {len(contatos_selecionados)} selecionados" if contatos_selecionados else ""
                    st.session_state['relatorio_preview'] = df_filtered
                    st.session_state['relatorio_filtros'] = f"Período: {r_dt_inicio.strftime('%d/%m/%Y')} a {r_dt_fim.strftime('%d/%m/%Y')} | Tipos: {', '.join(tipo_selected)}{filtro_contatos_str}"
                    
        # Render the Preview & Export Buttons if the report has been generated
        if 'relatorio_preview' in st.session_state:
            df_prev = st.session_state['relatorio_preview']
            st.markdown("---")
            st.markdown(f"#### 🔎 Visualização do Relatório Gerado")
            st.caption(st.session_state.get('relatorio_filtros', ''))
            
            # Show summary KPIs of the generated report
            col_res1, col_res2, col_res3 = st.columns(3)
            tot_cli_val = df_prev[df_prev['tipo'] == 'Cliente']['valor'].sum()
            tot_for_val = df_prev[df_prev['tipo'] == 'Fornecedor']['valor'].sum()
            
            col_res1.metric("Total de Clientes (A Receber)", to_brl(tot_cli_val))
            col_res2.metric("Total de Fornecedores (A Pagar)", to_brl(tot_for_val))
            col_res3.metric("Saldo Líquido", to_brl(tot_cli_val - tot_for_val))
            
            # Format display dataframe
            df_display_prev = df_prev.copy()
            df_display_prev['Vencimento'] = pd.to_datetime(df_display_prev['data_vencimento']).dt.strftime('%d/%m/%Y')
            df_display_prev['Valor (R$)'] = df_display_prev['valor'].apply(to_brl)
            df_display_prev['Status Interno'] = df_display_prev['status_financeiro'].map({
                'Atraso': '🔴 Atraso (<30 dias)',
                'Risco': '🔥 Risco (>30 dias)',
                'Em Dia': '🟢 Em Dia'
            })
            
            df_display_view = df_display_prev[['Vencimento', 'tipo', 'nome_contato', 'descricao', 'Valor (R$)', 'Status Interno']]
            df_display_view.columns = ['Vencimento', 'Tipo', 'Contato', 'Descrição/Fatura', 'Valor', 'Status de Prazo']
            
            st.dataframe(df_display_view, hide_index=True, width="stretch")
            
            # Export Buttons side-by-side
            col_dwn1, col_dwn2 = st.columns(2)
            
            # 1. Excel/CSV Download
            csv_rep = df_prev[['data_vencimento', 'tipo', 'nome_contato', 'descricao', 'valor', 'status_financeiro']].to_csv(index=False, sep=";").encode('utf-8-sig')
            col_dwn1.download_button(
                label="📥 Baixar Planilha Excel (CSV)",
                data=csv_rep,
                file_name=f"relatorio_financeiro_{hoje.strftime('%d_%m_%Y')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_dwn_csv"
            )
            
            # 2. PDF Download
            try:
                pdf_rep = FPDF()
                pdf_rep.add_page()
                pdf_rep.set_font("Helvetica", "B", 15)
                pdf_rep.cell(0, 10, "EMPORIO DO ALHO - RELATORIO FINANCEIRO CONSOLIDADO", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf_rep.set_font("Helvetica", "", 10)
                pdf_rep.cell(0, 6, st.session_state.get('relatorio_filtros', ''), new_x="LMARGIN", new_y="NEXT", align="C")
                pdf_rep.ln(5)
                
                pdf_rep.set_font("Helvetica", "B", 10)
                pdf_rep.cell(20, 7, "Venc.", border=1)
                pdf_rep.cell(20, 7, "Tipo", border=1)
                pdf_rep.cell(50, 7, "Contato/Parceiro", border=1)
                pdf_rep.cell(65, 7, "Descricao/Fatura", border=1)
                pdf_rep.cell(35, 7, "Valor", border=1, new_x="LMARGIN", new_y="NEXT")
                
                pdf_rep.set_font("Helvetica", "", 8.5)
                import unicodedata
                for _, r in df_prev.iterrows():
                    v_dt = pd.to_datetime(r['data_vencimento']).strftime('%d/%m/%Y')
                    tp = r['tipo']
                    cont = "".join(ch for ch in unicodedata.normalize('NFKD', str(r['nome_contato'])) if unicodedata.category(ch) != 'Mn')
                    desc = "".join(ch for ch in unicodedata.normalize('NFKD', str(r['descricao'])) if unicodedata.category(ch) != 'Mn')[:38]
                    v_str = f"R$ {float(r['valor']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    
                    pdf_rep.cell(20, 6, v_dt, border=1)
                    pdf_rep.cell(20, 6, tp, border=1)
                    pdf_rep.cell(50, 6, cont[:28], border=1)
                    pdf_rep.cell(65, 6, desc, border=1)
                    pdf_rep.cell(35, 6, v_str, border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                    
                pdf_data_rep = bytes(pdf_rep.output())
                
                col_dwn2.download_button(
                    label="📄 Baixar Relatório Oficial (PDF)",
                    data=pdf_data_rep,
                    file_name=f"relatorio_financeiro_{hoje.strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_dwn_pdf"
                )
            except Exception as pdf_ex:
                col_dwn2.error(f"Erro ao gerar PDF: {pdf_ex}")
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

            if st.session_state.get("cap_limpar_formulario", False):
                st.session_state["cap_forn_sel"] = list(op_forn.keys())[0]
                st.session_state["cap_pc_sel"] = list(op_pc.keys())[0]
                st.session_state["cap_desc_p"] = ""
                st.session_state["cap_val_p"] = 0.01
                st.session_state["cap_venc_p"] = date.today() + timedelta(days=30)
                st.session_state["cap_is_vinc"] = False
                st.session_state["cap_cli_sel"] = list(op_cli.keys())[0]
                st.session_state["cap_num_parcelas"] = 1
                st.session_state["cap_periodicidade"] = "Mensal (Mesmo dia do mês)"
                st.session_state["cap_dias_intervalo"] = 30
                st.session_state["cap_limpar_formulario"] = False

            col_m1, col_m2 = st.columns(2)
            forn_sel = col_m1.selectbox("Fornecedor", list(op_forn.keys()), key="cap_forn_sel")
            pc_sel = col_m2.selectbox("Plano de Contas (Planta de Custo)", list(op_pc.keys()), key="cap_pc_sel")
            
            col_m3, col_m4 = st.columns([2, 1])
            desc_p = col_m3.text_input("Descrição / Fatura (Ex: Nota Fiscal nº 123)", key="cap_desc_p")
            val_p = col_m4.number_input("Valor da Duplicata (R$)", min_value=0.01, step=50.0, key="cap_val_p")
            
            col_m5, col_m6 = st.columns(2)
            venc_p = col_m5.date_input("Vencimento (ou da 1ª Parcela)", date.today() + timedelta(days=30), key="cap_venc_p")
            with col_m6:
                is_vinc = st.checkbox("É Cliente Vinculado (CNPJ) ?", value=False, key="cap_is_vinc")
                cli_sel = st.selectbox("Cliente Vinculado (CNPJ)", list(op_cli.keys()), disabled=not is_vinc, label_visibility="collapsed", key="cap_cli_sel")
            
            st.markdown("##### 📅 Opções de Parcelamento / Recorrência")
            col_p1, col_p2, col_p3 = st.columns([1, 1.5, 1.5])
            n_parcelas = col_p1.number_input("Nº de Parcelas", min_value=1, max_value=36, value=1, step=1, key="cap_num_parcelas")
            
            periodicidade = "Mensal (Mesmo dia do mês)"
            dias_intervalo = 30
            if n_parcelas > 1:
                periodicidade = col_p2.selectbox("Periodicidade", ["Mensal (Mesmo dia do mês)", "A cada X dias"], key="cap_periodicidade")
                if periodicidade == "A cada X dias":
                    dias_intervalo = col_p3.number_input("Dias entre parcelas", min_value=1, max_value=365, value=30, step=1, key="cap_dias_intervalo")
                
                # Exibe a prévia das parcelas
                import calendar
                def add_months(sourcedate, months):
                    month = sourcedate.month - 1 + months
                    year = sourcedate.year + month // 12
                    month = month % 12 + 1
                    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
                    return date(year, month, day)
                
                preview_data = []
                for i in range(n_parcelas):
                    if periodicidade == "Mensal (Mesmo dia do mês)":
                        dt_venc = add_months(venc_p, i)
                    else:
                        dt_venc = venc_p + timedelta(days=dias_intervalo * i)
                    preview_data.append({
                        "Parcela": f"{i+1}/{n_parcelas}",
                        "Vencimento": dt_venc.strftime("%d/%m/%Y"),
                        "Valor": f"R$ {val_p:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    })
                
                st.info(f"💰 **Total a ser lançado:** {n_parcelas} parcelas de R$ {val_p:,.2f} = **R$ {val_p * n_parcelas:,.2f}**")
                st.markdown("**Prévia das Parcelas:**")
                st.dataframe(pd.DataFrame(preview_data), hide_index=True, use_container_width=True)
            
            if st.button("Salvar Duplicata a Pagar", type="primary", use_container_width=False):
                if st.session_state.get("cap_clique_bloqueado", False):
                    st.warning("Gravação já em andamento. Aguarde...")
                elif forn_sel == "-- SELECIONE O FORNECEDOR --":
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
                        st.error(f"A conta selecionada ({pc_sel}) exige a vinculação obrigatória de um Cliente (CNPJ) para cálculo de rentabilidade. Por favor, marque a caixa e selecione o cliente correspondente.")
                    else:
                        st.session_state["cap_clique_bloqueado"] = True
                        
                        import calendar
                        def add_months(sourcedate, months):
                            month = sourcedate.month - 1 + months
                            year = sourcedate.year + month // 12
                            month = month % 12 + 1
                            day = min(sourcedate.day, calendar.monthrange(year, month)[1])
                            return date(year, month, day)
                            
                        with st.spinner("Registrando duplicatas a pagar..."):
                            for i in range(n_parcelas):
                                if periodicidade == "Mensal (Mesmo dia do mês)":
                                    dt_venc = add_months(venc_p, i)
                                else:
                                    dt_venc = venc_p + timedelta(days=dias_intervalo * i)
                                    
                                desc_final = f"{desc_p} ({i+1}/{n_parcelas})" if n_parcelas > 1 else desc_p
                                
                                run_query(
                                    "INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, cliente_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                    (forn_id, pc_id, cli_id, desc_final, val_p, dt_venc.strftime("%Y-%m-%d"))
                                )
                        
                        st.session_state["cap_clique_bloqueado"] = False
                        
                        # Define flag para limpar os campos na próxima execução (antes da renderização dos widgets)
                        st.session_state["cap_limpar_formulario"] = True
                        
                        if n_parcelas > 1:
                            st.success(f"✅ {n_parcelas} duplicatas a pagar lançadas com sucesso!")
                        else:
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

            # ======= RENEGOCIAÇÃO DE DÍVIDAS COM FORNECEDORES (CONSOLIDAR E REPARCELAR) =======
            with st.expander("🤝 Renegociar Contas a Pagar com Fornecedor (Consolidar e Reparcelar)"):
                st.markdown("Consolide múltiplos boletos pendentes/atrasados de um fornecedor em um novo acordo de parcelamento.")
                
                # Buscar fornecedores com contas pendentes
                df_forn_devedores = fetch_all("""
                    SELECT DISTINCT f.id, f.nome_fantasia, f.nome 
                    FROM contas_a_pagar c
                    JOIN fornecedores f ON c.fornecedor_id = f.id
                    WHERE c.status = 'PENDENTE'
                    ORDER BY f.nome_fantasia
                """)
                
                if df_forn_devedores.empty:
                    st.info("Não há fornecedores com contas pendentes para renegociação.")
                else:
                    opcoes_forn_devedores = {}
                    for _, r in df_forn_devedores.iterrows():
                        lbl = r['nome_fantasia'] if pd.notna(r['nome_fantasia']) and r['nome_fantasia'].strip() else r['nome']
                        opcoes_forn_devedores[lbl] = r['id']
                        
                    forn_renome = st.selectbox("Selecione o Fornecedor para Renegociar:", ["-- SELECIONE --"] + list(opcoes_forn_devedores.keys()), key="reneg_forn_sel")
                    
                    if forn_renome != "-- SELECIONE --":
                        f_id_reneg = opcoes_forn_devedores[forn_renome]
                        # Buscar faturas pendentes do fornecedor
                        df_pend_reneg_f = fetch_all("""
                            SELECT id, descricao, valor, data_vencimento, plano_conta_id, compra_id 
                            FROM contas_a_pagar 
                            WHERE fornecedor_id=? AND status='PENDENTE' 
                            ORDER BY data_vencimento ASC
                        """, (f_id_reneg,))
                        
                        if df_pend_reneg_f.empty:
                            st.info("Este fornecedor não possui contas pendentes.")
                        else:
                            # Criar rótulos legíveis para o multiselect
                            df_pend_reneg_f['venc_f'] = pd.to_datetime(df_pend_reneg_f['data_vencimento']).dt.strftime('%d/%m/%Y')
                            opts_titulos_f = {}
                            for _, r in df_pend_reneg_f.iterrows():
                                lbl = f"ID #{r['id']} | {r['descricao']} | Venc: {r['venc_f']} | R$ {r['valor']:,.2f}"
                                opts_titulos_f[lbl] = r
                            
                            selec_titulos_lbls_f = st.multiselect(
                                "Selecione os boletos a consolidar no acordo:",
                                options=list(opts_titulos_f.keys()),
                                default=list(opts_titulos_f.keys()),
                                key="reneg_titulos_forn_sel"
                            )
                            
                            if not selec_titulos_lbls_f:
                                st.warning("Selecione pelo menos um boleto para realizar a renegociação.")
                            else:
                                # Calcular soma original
                                titulos_para_acordo_f = [opts_titulos_f[lbl] for lbl in selec_titulos_lbls_f]
                                soma_original_f = sum(float(t['valor']) for t in titulos_para_acordo_f)
                                
                                st.metric("Total da Dívida Consolidada (Original)", f"R$ {soma_original_f:,.2f}")
                                
                                col_ref1, col_ref2 = st.columns(2)
                                novo_valor_acordo_f = col_ref1.number_input(
                                    "Novo Valor Acordado (R$)",
                                    min_value=0.01,
                                    value=soma_original_f,
                                    step=0.01,
                                    key="reneg_novo_valor_forn"
                                )
                                
                                # Carregar formas de pagamento cadastradas
                                df_fps = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
                                fps_dict = {r['nome']: r for _, r in df_fps.iterrows()}
                                
                                forma_pag_acordo_f = col_ref2.selectbox(
                                    "Nova Condição de Pagamento:",
                                    list(fps_dict.keys()),
                                    key="reneg_forma_pag_forn"
                                )
                                
                                rule_str_f = fps_dict[forma_pag_acordo_f]['parcelas']
                                import re
                                dias_list_f = [int(n) for n in re.findall(r'\d+', rule_str_f)]
                                if not dias_list_f:
                                    dias_list_f = [0]
                                
                                N_f = len(dias_list_f)
                                val_pf = round(novo_valor_acordo_f / N_f, 2)
                                diff_pf = round(novo_valor_acordo_f - val_pf * N_f, 2)
                                
                                data_base_acordo_f = st.date_input("Data Base para Vencimento das Parcelas:", value=date.today(), key="reneg_data_base_forn")
                                
                                # Gerar prévia das novas parcelas
                                preview_reneg_f = []
                                for i, dias in enumerate(dias_list_f):
                                    v_p = val_pf + (diff_pf if i == N_f - 1 else 0.0)
                                    dt_v = data_base_acordo_f + timedelta(days=dias)
                                    preview_reneg_f.append({
                                        "Parcela": f"{i+1}/{N_f}",
                                        "Vencimento": dt_v.strftime("%d/%m/%Y"),
                                        "Valor": f"R$ {v_p:,.2f}",
                                        "valor_num": v_p,
                                        "venc_date": dt_v
                                    })
                                
                                st.markdown("**Prévia do Novo Parcelamento:**")
                                st.dataframe(pd.DataFrame(preview_reneg_f)[["Parcela", "Vencimento", "Valor"]], hide_index=True, use_container_width=True)
                                
                                # Input da descrição/observações do acordo
                                desc_acordo_f = st.text_input("Descrição / Motivo do Acordo (opcional):", value="Acordo de Renegociação de Contas a Pagar", key="reneg_desc_obs_forn")
                                
                                if st.button("Confirmar Acordo de Renegociação com Fornecedor", type="primary", use_container_width=True, key="reneg_confirm_btn_forn"):
                                    with st.spinner("Processando renegociação de contas a pagar..."):
                                        import uuid
                                        acordo_id_f = str(uuid.uuid4())[:8].upper()
                                        
                                        ids_cancelar_f = [int(t['id']) for t in titulos_para_acordo_f]
                                        nota_cancelamento_f = f" [RENEGOCIADO - Acordo #{acordo_id_f}]"
                                        
                                        for t_id in ids_cancelar_f:
                                            run_query(
                                                "UPDATE contas_a_pagar SET status='CANCELADO', descricao = descricao || ? WHERE id=?",
                                                (nota_cancelamento_f, t_id)
                                            )
                                        
                                        # Inserir novos títulos
                                        for i, p_info in enumerate(preview_reneg_f):
                                            nova_desc = f"{desc_acordo_f} (Acordo #{acordo_id_f} - Parcela {p_info['Parcela']})"
                                            venc_str = p_info['venc_date'].strftime("%Y-%m-%d")
                                            val_num = p_info['valor_num']
                                            
                                            p_c_id_default = titulos_para_acordo_f[0].get('plano_conta_id')
                                            if not p_c_id_default or pd.isna(p_c_id_default):
                                                # Buscar do fornecedor
                                                df_forn_pc = fetch_all("SELECT plano_conta_id FROM fornecedores WHERE id = ?", (f_id_reneg,))
                                                if not df_forn_pc.empty and pd.notna(df_forn_pc.iloc[0]['plano_conta_id']):
                                                    p_c_id_default = int(df_forn_pc.iloc[0]['plano_conta_id'])
                                            if not p_c_id_default or pd.isna(p_c_id_default):
                                                # Fallback para o primeiro plano de custo/despesa
                                                p_c_acordo = fetch_all("SELECT id FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') LIMIT 1")
                                                p_c_id_default = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None
                                                
                                            compra_id_default = titulos_para_acordo_f[0].get('compra_id')
                                            
                                            run_query(
                                                "INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, compra_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                                (f_id_reneg,
                                                 int(p_c_id_default) if pd.notna(p_c_id_default) else None,
                                                 int(compra_id_default) if pd.notna(compra_id_default) else None,
                                                 nova_desc, val_num, venc_str)
                                            )
                                            
                                    st.success(f"🤝 Renegociação com fornecedor concluída com sucesso! Acordo #{acordo_id_f} registrado com {N_f} novas parcelas.")
                                    import time; time.sleep(1.5); st.rerun()

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
                            data_inicio = st.date_input("Data da 1ª Parcela", value=date.today(), key="dt_repar")
                            
                            rp3, rp4 = st.columns(2)
                            periodicidade_rp = rp3.selectbox("Periodicidade", ["Mensal (Mesmo dia do mês)", "A cada X dias"], key="periodicidade_repar")
                            dias_entre = 30
                            if periodicidade_rp == "A cada X dias":
                                dias_entre = rp4.number_input("Dias entre Parcelas", min_value=1, value=30, step=1, key="dias_repar")

                            valor_parc = round(valor_original / n_parc, 2)
                            diff_parc = round(valor_original - valor_parc * n_parc, 2)
                            
                            import calendar
                            def add_months(sourcedate, months):
                                month = sourcedate.month - 1 + months
                                year = sourcedate.year + month // 12
                                month = month % 12 + 1
                                day = min(sourcedate.day, calendar.monthrange(year, month)[1])
                                return date(year, month, day)

                            preview = []
                            for i in range(n_parc):
                                v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                                if periodicidade_rp == "Mensal (Mesmo dia do mês)":
                                    d = add_months(data_inicio, i)
                                else:
                                    d = data_inicio + timedelta(days=dias_entre * i)
                                preview.append({"Parcela": f"{i+1}/{n_parc}", "Vencimento": d.strftime("%d/%m/%Y"), "Valor": f"R$ {v:,.2f}"})
                            st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

                            if st.button("Confirmar Reparcelamento", type="primary"):
                                run_query("UPDATE contas_a_pagar SET status='CANCELADO', descricao = descricao || ' [REPARCELADO]' WHERE id=?", (dup_id,))
                                for i in range(n_parc):
                                    v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                                    if periodicidade_rp == "Mensal (Mesmo dia do mês)":
                                        d = add_months(data_inicio, i)
                                    else:
                                        d = data_inicio + timedelta(days=dias_entre * i)
                                    nova_desc_rp = f"{dup_data['descricao']} (Repar. {i+1}/{n_parc})"
                                    p_c_id_rp = int(dup_data['plano_conta_id']) if pd.notna(dup_data['plano_conta_id']) else None
                                    if not p_c_id_rp:
                                        if pd.notna(dup_data['fornecedor_id']):
                                            df_forn_pc = fetch_all("SELECT plano_conta_id FROM fornecedores WHERE id=?", (int(dup_data['fornecedor_id']),))
                                            if not df_forn_pc.empty and pd.notna(df_forn_pc.iloc[0]['plano_conta_id']):
                                                p_c_id_rp = int(df_forn_pc.iloc[0]['plano_conta_id'])
                                    if not p_c_id_rp:
                                        p_c_acordo = fetch_all("SELECT id FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') LIMIT 1")
                                        p_c_id_rp = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None

                                    run_query(
                                        "INSERT INTO contas_a_pagar (fornecedor_id, compra_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                        (int(dup_data['fornecedor_id']) if pd.notna(dup_data['fornecedor_id']) else None,
                                         int(dup_data['compra_id']) if pd.notna(dup_data['compra_id']) else None,
                                         p_c_id_rp,
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
            df_planos = fetch_all("SELECT id, codigo, nome FROM planos_de_contas WHERE categoria IN ('RECEITA', 'RECEITA_NAO_OP') ORDER BY codigo")
            op_plan = {"-- SELECIONE O PLANO DE CONTAS --": None}
            if not df_planos.empty:
                for _,r in df_planos.iterrows():
                    op_plan[f"{r['codigo']} - {r['nome']}"] = r['id']
                
            with st.form("lancar_receber", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                cli_nome = c1.selectbox("Cliente", list(op_cli.keys()))
                plan_sel = c2.selectbox("Plano de Contas", list(op_plan.keys()))
                venc = c3.date_input("Vencimento", date.today() + timedelta(days=15))
                
                c4, c5 = st.columns([2, 1])
                desc = c4.text_input("Fatura (No. NF, Parcela, Referência)")
                val_r = c5.number_input("Valor da Fatura (R$)", min_value=0.01)
                
                if st.form_submit_button("Lançar Promessa de Faturamento"):
                    if cli_nome == "-- SELECIONE O CLIENTE --":
                        st.error("Por favor, selecione um Cliente (ou 'Genérico / Não Cadastrado').")
                    elif plan_sel == "-- SELECIONE O PLANO DE CONTAS --":
                        st.error("Por favor, selecione um Plano de Contas.")
                    elif not desc:
                        st.error("Preencha a descrição.")
                    else:
                        with st.spinner("Registrando recebível..."):
                            run_query("INSERT INTO contas_a_receber (cliente_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, 'PENDENTE')",
                                      (op_cli[cli_nome], op_plan[plan_sel], desc, val_r, venc.strftime("%Y-%m-%d")))
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

        # ======= RENEGOCIAÇÃO DE DÍVIDAS EM LOTE (CONSOLIDAR E REPARCELAR) =======
        with st.expander("🤝 Renegociar Dívida de Cliente em Atraso (Consolidar e Reparcelar)"):
            st.markdown("Consolide múltiplos títulos pendentes/atrasados de um cliente em um novo acordo de parcelamento.")
            
            # Buscar clientes com faturas pendentes
            df_clientes_devedores = fetch_all("""
                SELECT DISTINCT cl.id, cl.nome 
                FROM contas_a_receber c
                JOIN clientes cl ON c.cliente_id = cl.id
                WHERE c.status = 'PENDENTE'
                ORDER BY cl.nome
            """)
            
            if df_clientes_devedores.empty:
                st.info("Não há clientes com faturas pendentes para renegociação.")
            else:
                opcoes_devedores = {r['nome']: r['id'] for _, r in df_clientes_devedores.iterrows()}
                cli_renome = st.selectbox("Selecione o Cliente para Renegociar:", ["-- SELECIONE --"] + list(opcoes_devedores.keys()), key="reneg_cli_sel")
                
                if cli_renome != "-- SELECIONE --":
                    c_id_reneg = opcoes_devedores[cli_renome]
                    # Buscar faturas pendentes do cliente
                    df_pend_reneg = fetch_all("""
                        SELECT id, descricao, valor, data_vencimento, plano_conta_id 
                        FROM contas_a_receber 
                        WHERE cliente_id=? AND status='PENDENTE' 
                        ORDER BY data_vencimento ASC
                    """, (c_id_reneg,))
                    
                    if df_pend_reneg.empty:
                        st.info("Este cliente não possui faturas pendentes.")
                    else:
                        # Criar rótulos legíveis para o multiselect
                        df_pend_reneg['venc_f'] = pd.to_datetime(df_pend_reneg['data_vencimento']).dt.strftime('%d/%m/%Y')
                        opts_titulos = {}
                        for _, r in df_pend_reneg.iterrows():
                            lbl = f"ID #{r['id']} | {r['descricao']} | Venc: {r['venc_f']} | R$ {r['valor']:,.2f}"
                            opts_titulos[lbl] = r
                        
                        selec_titulos_lbls = st.multiselect(
                            "Selecione as faturas a consolidar no acordo:",
                            options=list(opts_titulos.keys()),
                            default=list(opts_titulos.keys()),
                            key="reneg_titulos_sel"
                        )
                        
                        if not selec_titulos_lbls:
                            st.warning("Selecione pelo menos um título para realizar a renegociação.")
                        else:
                            # Calcular soma original
                            titulos_para_acordo = [opts_titulos[lbl] for lbl in selec_titulos_lbls]
                            soma_original = sum(float(t['valor']) for t in titulos_para_acordo)
                            
                            st.metric("Total da Dívida Consolidada (Original)", f"R$ {soma_original:,.2f}")
                            
                            col_re1, col_re2 = st.columns(2)
                            novo_valor_acordo = col_re1.number_input(
                                "Novo Valor Acordado (R$)",
                                min_value=0.01,
                                value=soma_original,
                                step=0.01,
                                key="reneg_novo_valor"
                            )
                            
                            # Carregar formas de pagamento cadastradas
                            df_fps = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
                            fps_dict = {r['nome']: r for _, r in df_fps.iterrows()}
                            
                            forma_pag_acordo = col_re2.selectbox(
                                "Nova Condição de Pagamento:",
                                list(fps_dict.keys()),
                                key="reneg_forma_pag"
                            )
                            
                            rule_str = fps_dict[forma_pag_acordo]['parcelas']
                            import re
                            dias_list = [int(n) for n in re.findall(r'\d+', rule_str)]
                            if not dias_list:
                                dias_list = [0]
                            
                            N = len(dias_list)
                            val_p = round(novo_valor_acordo / N, 2)
                            diff_p = round(novo_valor_acordo - val_p * N, 2)
                            
                            data_base_acordo = st.date_input("Data Base para Vencimento das Parcelas:", value=date.today(), key="reneg_data_base")
                            
                            # Gerar prévia das novas parcelas
                            preview_reneg = []
                            for i, dias in enumerate(dias_list):
                                v_p = val_p + (diff_p if i == N - 1 else 0.0)
                                dt_v = data_base_acordo + timedelta(days=dias)
                                preview_reneg.append({
                                    "Parcela": f"{i+1}/{N}",
                                    "Vencimento": dt_v.strftime("%d/%m/%Y"),
                                    "Valor": f"R$ {v_p:,.2f}",
                                    "valor_num": v_p,
                                    "venc_date": dt_v
                                })
                            
                            st.markdown("**Prévia do Novo Parcelamento:**")
                            st.dataframe(pd.DataFrame(preview_reneg)[["Parcela", "Vencimento", "Valor"]], hide_index=True, use_container_width=True)
                            
                            # Input da descrição/observações do acordo
                            desc_acordo = st.text_input("Descrição / Motivo do Acordo (opcional):", value="Acordo de Renegociação de Dívida", key="reneg_desc_obs")
                            
                            if st.button("Confirmar Acordo de Renegociação", type="primary", use_container_width=True, key="reneg_confirm_btn"):
                                with st.spinner("Processando renegociação de dívida..."):
                                    import uuid
                                    acordo_id = str(uuid.uuid4())[:8].upper()
                                    
                                    ids_cancelar = [int(t['id']) for t in titulos_para_acordo]
                                    nota_cancelamento = f" [RENEGOCIADO - Acordo #{acordo_id}]"
                                    
                                    for t_id in ids_cancelar:
                                        run_query(
                                            "UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ? WHERE id=?",
                                            (nota_cancelamento, t_id)
                                        )
                                    
                                    p_c_id_default_r = titulos_para_acordo[0].get('plano_conta_id') if hasattr(titulos_para_acordo[0], 'get') else None
                                    if not p_c_id_default_r or pd.isna(p_c_id_default_r):
                                        # Buscar padrão
                                        p_c_rec = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                                        p_c_id_default_r = int(p_c_rec.iloc[0]['id']) if not p_c_rec.empty else None

                                    for i, p_info in enumerate(preview_reneg):
                                        nova_desc = f"{desc_acordo} (Acordo #{acordo_id} - Parcela {p_info['Parcela']})"
                                        venc_str = p_info['venc_date'].strftime("%Y-%m-%d")
                                        val_num = p_info['valor_num']
                                        
                                        run_query(
                                            "INSERT INTO contas_a_receber (cliente_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                            (c_id_reneg, p_c_id_default_r, nova_desc, val_num, venc_str)
                                        )
                                        
                                st.success(f"🤝 Renegociação concluída com sucesso! Acordo #{acordo_id} registrado com {N} novas parcelas.")
                                import time; time.sleep(1.5); st.rerun()

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
                             st.warning(f"**Atenção:** Este recebível está vinculado à **Venda #{int(venda_id)}**.")

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
                                 st.warning("Esta duplicata está vinculada a uma Venda. Para aplicar descontos ou juros em títulos de vendas comerciais de forma que conste no DRE, digite o valor final pago diretamente na tabela de recebimento (Lote) ao confirmar o pagamento.")
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
                                     
                                     p_c_id_rp_r = int(rec_data['plano_conta_id']) if pd.notna(rec_data['plano_conta_id']) else None
                                     if not p_c_id_rp_r:
                                         p_c_rec = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                                         p_c_id_rp_r = int(p_c_rec.iloc[0]['id']) if not p_c_rec.empty else None
                                     
                                     run_query(
                                         "INSERT INTO contas_a_receber (cliente_id, venda_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                         (int(rec_data['cliente_id']) if pd.notna(rec_data['cliente_id']) else None,
                                          int(rec_data['venda_id']) if pd.notna(rec_data['venda_id']) else None,
                                          p_c_id_rp_r,
                                          nova_desc_rp, v, d.strftime("%Y-%m-%d")))
                                 st.success(f"Reparcelamento concluído! {n_parc} novos recebíveis criados.")
                                 import time; time.sleep(1); st.rerun()

                         elif acao_rec == "Excluir/Cancelar":
                             if pd.notna(venda_id):
                                 st.error("Não é permitido cancelar/excluir recebíveis de vendas faturadas por aqui. Para excluir, você deve desfazer o faturamento do pedido correspondente na tela de Faturamento.")
                             else:
                                 st.markdown("**Tem certeza que deseja cancelar/excluir este recebível?**")
                                 st.markdown("Esta ação mudará o status do recebível para `'CANCELADO'` e ele não aparecerá mais nos recebimentos pendentes.")
                                 if st.button("Confirmar Cancelamento/Exclusão", type="primary", key="btn_rec_del"):
                                     run_query("UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ' [CANCELADO]' WHERE id=?", (rec_id,))
                                     st.success("Recebível cancelado com sucesso!")
                                     import time; time.sleep(1); st.rerun()

    # ------------------ ABA 4: CAIXAS E BANCOS ------------------
    with tab4:
        # Estilos CSS específicos para Caixas e Bancos
        st.markdown("""
        <style>
        /* Estilização para o botão desabilitado de Inserir Lançamento */
        div.st-key-btn_incluir_lanc_disabled button {
            background-color: #f1f5f9 !important;
            color: #94a3b8 !important;
            border: 1px solid #cbd5e1 !important;
            cursor: not-allowed !important;
            border-radius: 6px !important;
            width: 100% !important;
            height: 42px !important;
            font-weight: bold !important;
        }
        div.st-key-btn_incluir_lanc_disabled button:hover {
            background-color: #e2e8f0 !important;
            color: #64748b !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Reservar espaço para a barra de métricas discreta no topo (logo abaixo das abas)
        container_metricas = st.container()
        
        # Linha Única de Filtros e Botões (Colunas de proporções compactas)
        col_f1, col_f2, col_f3, col_b1, col_b2, col_b3 = st.columns([1.0, 1.4, 1.0, 1.2, 1.0, 1.2])
        
        with col_f1:
            conta_con = st.selectbox(
                "Conta", 
                ["Todas as contas"] + list(opcoes_bancos.keys()), 
                key="cx_conta_filter"
            )
            
        with col_f2:
            busca_txt = st.text_input(
                "Pesquisa - Nome/Histórico", 
                placeholder="Buscar lançamento...", 
                key="cx_search_filter"
            )
            
        with col_f3:
            periodo_sel = st.selectbox(
                "Período", 
                ["Este mês", "Hoje", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"], 
                key="cx_periodo_filter"
            )
            
        with col_b1:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Transferência", key="btn_placeholder_transf", use_container_width=True):
                mostrar_transferencia_modal(opcoes_bancos, df_bancos)
                
        with col_b2:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Ajustar saldo", key="btn_placeholder_ajuste", use_container_width=True):
                mostrar_ajuste_saldo_modal(opcoes_bancos)
                
        with col_b3:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("+ Lançamento", key="btn_incluir_lanc_disabled", use_container_width=True):
                username = st.session_state.get('logged_user', 'Usuário')
                mostrar_mensagem_bloqueio(username)
                
        # Cálculo de datas baseados no filtro de Período
        dt_ini, dt_fi = date.today(), date.today()
        if periodo_sel == "Este mês":
            import calendar
            dt_ini = date(hoje.year, hoje.month, 1)
            dt_fi = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
        elif periodo_sel == "Hoje":
            dt_ini = hoje
            dt_fi = hoje
        elif periodo_sel == "Últimos 7 dias":
            dt_ini = hoje - timedelta(days=7)
            dt_fi = hoje
        elif periodo_sel == "Últimos 30 dias":
            dt_ini = hoje - timedelta(days=30)
            dt_fi = hoje
        elif periodo_sel == "Personalizado":
            col_d1, col_d2 = st.columns(2)
            dt_ini = col_d1.date_input("De", hoje - timedelta(days=30), key="cx_dt_ini")
            dt_fi = col_d2.date_input("Até", hoje, key="cx_dt_fi")
        
        # 1. Carregar todo o extrato em ordem cronológica (para cálculo de saldo correto)
        query_con = """
            SELECT fc.id, fc.data as 'Data', fc.tipo as 'Movimentação', 
                   fc.descricao as 'Histórico', fc.valor as 'Valor', 
                   cb.nome as 'Banco', fc.conciliado as 'Revisado',
                   fc.categoria as 'Categoria'
            FROM fluxo_caixa fc
            LEFT JOIN contas_bancarias cb ON fc.conta_bancaria_id = cb.id
            ORDER BY fc.data ASC, fc.id ASC
        """
        df_ext = fetch_all(query_con)
        
        # 2. Filtrar por Conta antes do cálculo de saldo progressivo
        if conta_con != "Todas as contas":
            df_ext = df_ext[df_ext['Banco'] == conta_con]
            
        # 3. Calcular saldo progressivo (acumulado histórico)
        saldo_inicial_conta = 0.0
        if not df_ext.empty:
            if conta_con != "Todas as contas":
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
        else:
            df_ext['Saldo Após Linha'] = []
            
        # 4. Filtrar por período de data para visualização
        if not df_ext.empty:
            df_ext['data_parsed'] = pd.to_datetime(df_ext['Data']).dt.date
            df_ext = df_ext[(df_ext['data_parsed'] >= dt_ini) & (df_ext['data_parsed'] <= dt_fi)]
            
        # 5. Filtrar por busca textual
        if not df_ext.empty and busca_txt:
            busca_txt_lower = busca_txt.lower()
            df_ext = df_ext[
                df_ext['Histórico'].str.lower().str.contains(busca_txt_lower, na=False) |
                df_ext['Categoria'].str.lower().str.contains(busca_txt_lower, na=False)
            ]
            
        # 6. Alinhar em duas colunas separadas (Entrada e Saída)
        if not df_ext.empty:
            df_ext['Entrada'] = df_ext.apply(lambda r: float(r['Valor']) if r['Movimentação'] == 'Entrada' else None, axis=1)
            df_ext['Saída'] = df_ext.apply(lambda r: float(r['Valor']) if r['Movimentação'] == 'Saída' else None, axis=1)
        else:
            df_ext['Entrada'] = []
            df_ext['Saída'] = []
            
        # 7. Resumos e Saldos do Período
        if df_ext.empty:
            total_entradas_periodo = 0.0
            total_saidas_periodo = 0.0
        else:
            total_entradas_periodo = float(df_ext[df_ext['Movimentação'] == 'Entrada']['Valor'].sum())
            total_saidas_periodo = float(df_ext[df_ext['Movimentação'] == 'Saída']['Valor'].sum())

        if conta_con == "Todas as contas":
            saldo_atual_conta = saldo_total_empresa
        else:
            saldo_atual_conta = saldo_por_banco.get(opcoes_bancos[conta_con], 0.0)

        # 8. Barra Discreta de Métricas Financeiras no Topo (Renderizada no Container reservado)
        resultado_periodo = total_entradas_periodo - total_saidas_periodo
        color_res = "#16a34a" if resultado_periodo >= 0 else "#dc2626"
        
        def formatar_moeda(val):
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        with container_metricas:
            st.markdown(f"""
            <div style="display: flex; gap: 20px; font-size: 0.95rem; color: #475569; margin-top: 5px; margin-bottom: 15px; background-color: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <div>Saldo Atual: <strong style="color: #1e293b;">{formatar_moeda(saldo_atual_conta)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Entradas (Período): <strong style="color: #16a34a;">{formatar_moeda(total_entradas_periodo)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Saídas (Período): <strong style="color: #dc2626;">{formatar_moeda(total_saidas_periodo)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Resultado: <strong style="color: {color_res};">{formatar_moeda(resultado_periodo)}</strong></div>
            </div>
            """, unsafe_allow_html=True)
            
        # Renderização da Tabela/Grid principal
        if df_ext.empty:
            st.info("Nenhuma movimentação encontrada para os filtros selecionados.")
        else:
            # Exibir mais novos primeiro para visualização confortável
            df_display = df_ext.sort_values(by=['data_parsed', 'id'], ascending=[False, False]).copy()
            df_display['Data'] = pd.to_datetime(df_display['Data']).dt.strftime('%d/%m/%Y')
            df_display['Revisado'] = df_display['Revisado'].astype(bool)
            
            edited_df = st.data_editor(
                df_display[['id', 'Revisado', 'Data', 'Banco', 'Histórico', 'Entrada', 'Saída', 'Saldo Após Linha', 'Categoria']],
                hide_index=True,
                disabled=["id", "Data", "Banco", "Histórico", "Entrada", "Saída", "Saldo Após Linha", "Categoria"],
                width="stretch",
                column_config={
                    "id": None, # Oculta a coluna ID
                    "Revisado": st.column_config.CheckboxColumn("Ok", help="Marque se confirmou na conta do banco.", default=False),
                    "Entrada": st.column_config.NumberColumn("Entrada (R$)", format="R$ %.2f"),
                    "Saída": st.column_config.NumberColumn("Saída (R$)", format="R$ %.2f"),
                    "Saldo Após Linha": st.column_config.NumberColumn("Saldo Acumulado (R$)", format="R$ %.2f")
                }
            )
            
            # Botão de salvar alterações da conciliação
            if st.button("Salvar Modificações de Conciliação", type="primary", use_container_width=True):
                for _, row in edited_df.iterrows():
                    n_c = bool(row['Revisado'])
                    db_c = bool(df_ext[df_ext['id'] == row['id']].iloc[0]['Revisado'])
                    if n_c != db_c:
                        run_query("UPDATE fluxo_caixa SET conciliado=? WHERE id=?", (n_c, row['id']))
                st.success("Extrato Oficializado pela Gerência!")
                import time; time.sleep(1); st.rerun()

    # ------------------ Guia 5: AUDITORIA LOGÍSTICA ------------------
    with tab5:
        st.subheader("Auditoria de Comprovantes Logísticos")
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
        with st.expander("Auditar Canhotos de Viagens (Transportadoras)", expanded=True):
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
