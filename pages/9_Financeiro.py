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


from utils_financeiro_modals import *

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
            df_all_contas['Fornecedor'] = df_all_contas.apply(
                lambda r: f"🔴 [BLOQUEADO FALTAM CANHOTOS] {r['Fornecedor']}" if r.get('Bloqueado', False) else r['Fornecedor'], axis=1
            )
            
        # Métricas do Contas a Pagar
        total_pendente_p = 0.0
        total_vencido_p = 0.0
        total_pago_mes_p = 0.0
        
        if not df_all_contas.empty:
            df_pend = df_all_contas[df_all_contas['Status'] == 'PENDENTE'].copy()
            total_pendente_p = float(df_pend['Valor'].sum())
            if not df_pend.empty:
                df_pend['v_date'] = pd.to_datetime(df_pend['Vencimento']).dt.date
                total_vencido_p = float(df_pend[df_pend['v_date'] < hoje]['Valor'].sum())
                
            df_pago = df_all_contas[df_all_contas['Status'] == 'PAGO'].copy()
            if not df_pago.empty:
                df_pago['p_date'] = pd.to_datetime(df_pago['Data PGTO']).dt.date
                total_pago_mes_p = float(df_pago[(df_pago['p_date'] >= dt_ini) & (df_pago['p_date'] <= dt_fi)]['Valor'].sum())

        def formatar_moeda(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        container_metricas_p = st.container()
        with container_metricas_p:
            st.markdown(f"""
            <div style="display: flex; gap: 20px; font-size: 0.95rem; color: #475569; margin-top: 5px; margin-bottom: 15px; background-color: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <div>Total Pendente (Global): <strong style="color: #b45309;">{formatar_moeda(total_pendente_p)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Atrasado (Vencido): <strong style="color: #ef4444;">{formatar_moeda(total_vencido_p)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Liquidados (Período): <strong style="color: #10b981;">{formatar_moeda(total_pago_mes_p)}</strong></div>
            </div>
            """, unsafe_allow_html=True)
            
        col_pf1, col_pf2, col_pb1, col_pb2, col_pb3, col_pb4 = st.columns([1.0, 1.4, 0.9, 1.0, 0.9, 0.9])
        
        with col_pf1:
            status_filter_p = st.selectbox("Status", ["PENDENTE", "AGUARDANDO BAIXA", "PAGO", "TODAS"], key="pag_filt_mod")
        with col_pf2:
            busca_txt_p = st.text_input("Pesquisa - Nome/Fatura", placeholder="Buscar fornecedor...", key="pag_search_mod")
            
        with col_pb1:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("+ Lançamento", use_container_width=True, key="btn_lancar_p"):
                dialog_lancar_pagar()
                
        with col_pb2:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Renegociar", use_container_width=True, key="btn_reneg_p"):
                dialog_renegociar_pagar()
                
        with col_pb3:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Editar", use_container_width=True, key="btn_edit_p"):
                df_editables = df_all_contas[df_all_contas['Status'] == 'PENDENTE']
                if df_editables.empty:
                    st.warning("Nenhuma conta pendente para editar.")
                else:
                    if 'selecionados_ids_p' in st.session_state and len(st.session_state['selecionados_ids_p']) == 1:
                        dialog_editar_pagar(st.session_state['selecionados_ids_p'][0])
                    else:
                        st.warning("Selecione EXATAMENTE UMA conta pendente na tabela abaixo para editar.")

        with col_pb4:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            btn_baixar_p = st.button("💸 Baixar", type="primary", use_container_width=True, key="btn_baixar_p")

        if df_all_contas.empty:
            st.info("Nenhuma conta a pagar encontrada. Paz de espírito.")
        else:
            df_view_p = df_all_contas.copy()
            if status_filter_p != "TODAS":
                df_view_p = df_view_p[df_view_p['Status'] == status_filter_p]
                
            if busca_txt_p:
                b_p = busca_txt_p.lower()
                df_view_p = df_view_p[
                    df_view_p['Fornecedor'].str.lower().str.contains(b_p, na=False) |
                    df_view_p['Descrição/Fatura'].str.lower().str.contains(b_p, na=False)
                ]
                
            if df_view_p.empty:
                st.warning("Nenhum registro com este filtro.")
            else:
                df_view_p['Pagar?'] = False
                df_view_p['Vencimento'] = pd.to_datetime(df_view_p['Vencimento']).dt.strftime('%d/%m/%Y')
                df_view_p['Data PGTO'] = pd.to_datetime(df_view_p['Data PGTO']).dt.strftime('%d/%m/%Y').fillna("-")
                
                # Se for pago, desabilitamos o checkbox Pagar?
                is_disabled_p = ["id", "Fornecedor", "Planta de Custo", "Descrição/Fatura", "Vencimento", "Valor", "Status", "Data PGTO"]
                if status_filter_p == "PAGO":
                    is_disabled_p.append("Pagar?")
                    
                edited_df_p = st.data_editor(
                    df_view_p[['Pagar?', 'id', 'Fornecedor', 'Planta de Custo', 'Descrição/Fatura', 'Vencimento', 'Valor', 'Status', 'Data PGTO']],
                    hide_index=True,
                    disabled=is_disabled_p,
                    width="stretch",
                    height=500,
                    column_config={
                        "Pagar?": st.column_config.CheckboxColumn("Pagar?", help="Marque para liquidar"),
                        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                    },
                    key="editor_pagar"
                )
                
                selecionados_p = edited_df_p[edited_df_p['Pagar?'] == True]
                st.session_state['selecionados_ids_p'] = selecionados_p['id'].tolist() if not selecionados_p.empty else []
                
                if btn_baixar_p:
                    if selecionados_p.empty:
                        st.warning("Selecione pelo menos uma duplicata marcando a caixinha 'Pagar?'.")
                    else:
                        dialog_confirmar_baixa_lote_pagar(selecionados_p['id'].tolist(), df_all_contas, opcoes_bancos)


    # ------------------ ABA 3: CONTAS A RECEBER ------------------
    with tab3:
        df_receber = fetch_all("""
            SELECT c.id, c.descricao as 'Fatura', cl.nome as 'Cliente', 
                   c.data_vencimento as 'Vencimento', c.valor as 'Valor', 
                   c.status as 'Status', c.data_recebimento as 'Recebido Em'
            FROM contas_a_receber c
            LEFT JOIN clientes cl ON c.cliente_id = cl.id
            ORDER BY c.data_vencimento ASC
        """)
        
        # Métricas do Contas a Receber
        total_a_receber_r = 0.0
        total_vencido_r = 0.0
        total_recebido_mes_r = 0.0
        
        if not df_receber.empty:
            df_pend_r = df_receber[df_receber['Status'] == 'PENDENTE'].copy()
            total_a_receber_r = float(df_pend_r['Valor'].sum())
            if not df_pend_r.empty:
                df_pend_r['v_date'] = pd.to_datetime(df_pend_r['Vencimento']).dt.date
                total_vencido_r = float(df_pend_r[df_pend_r['v_date'] < hoje]['Valor'].sum())
                
            df_recebido_r = df_receber[df_receber['Status'] == 'RECEBIDO'].copy()
            if not df_recebido_r.empty:
                df_recebido_r['r_date'] = pd.to_datetime(df_recebido_r['Recebido Em']).dt.date
                total_recebido_mes_r = float(df_recebido_r[(df_recebido_r['r_date'] >= dt_ini) & (df_recebido_r['r_date'] <= dt_fi)]['Valor'].sum())

        def formatar_moeda(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        container_metricas_r = st.container()
        with container_metricas_r:
            st.markdown(f"""
            <div style="display: flex; gap: 20px; font-size: 0.95rem; color: #475569; margin-top: 5px; margin-bottom: 15px; background-color: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <div>Total a Receber (Global): <strong style="color: #2563eb;">{formatar_moeda(total_a_receber_r)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Atrasado (Vencido): <strong style="color: #ef4444;">{formatar_moeda(total_vencido_r)}</strong></div>
                <div style="color: #cbd5e1;">|</div>
                <div>Recebidos (Período): <strong style="color: #10b981;">{formatar_moeda(total_recebido_mes_r)}</strong></div>
            </div>
            """, unsafe_allow_html=True)
            
        col_rf1, col_rf2, col_rb1, col_rb2, col_rb3, col_rb4, col_rb5 = st.columns([1.0, 1.4, 0.9, 0.9, 0.9, 0.8, 0.9])
        
        with col_rf1:
            status_filter_r = st.selectbox("Status", ["PENDENTE", "RECEBIDO", "TODAS"], key="rec_filt_mod")
        with col_rf2:
            busca_txt_r = st.text_input("Pesquisa - Nome/Fatura", placeholder="Buscar cliente...", key="rec_search_mod")
            
        with col_rb1:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("+ Lançamento", use_container_width=True, key="btn_lancar_r"):
                dialog_lancar_receber()
                
        with col_rb2:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Gerar Extrato", use_container_width=True, key="btn_extrato_r"):
                dialog_fechamento_carteira()
                
        with col_rb3:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Renegociar", use_container_width=True, key="btn_reneg_r"):
                dialog_renegociar_receber()
                
        with col_rb4:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("Editar", use_container_width=True, key="btn_edit_r"):
                df_editables_r = df_receber[df_receber['Status'] == 'PENDENTE']
                if df_editables_r.empty:
                    st.warning("Nenhuma conta a receber pendente.")
                else:
                    if 'selecionados_ids_r' in st.session_state and len(st.session_state['selecionados_ids_r']) == 1:
                        dialog_editar_receber(st.session_state['selecionados_ids_r'][0])
                    else:
                        st.warning("Selecione EXATAMENTE UMA conta pendente na tabela abaixo para editar.")

        with col_rb5:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            btn_baixar_r = st.button("💸 Receber", type="primary", use_container_width=True, key="btn_baixar_r")

        if df_receber.empty:
            st.info("Nenhuma fatura lançada na vida financeira da empresa ainda.")
        else:
            df_view_r = df_receber.copy()
            if status_filter_r != "TODAS":
                df_view_r = df_view_r[df_view_r['Status'] == status_filter_r]
                
            if busca_txt_r:
                b_r = busca_txt_r.lower()
                df_view_r = df_view_r[
                    df_view_r['Cliente'].str.lower().str.contains(b_r, na=False) |
                    df_view_r['Fatura'].str.lower().str.contains(b_r, na=False)
                ]
                
            if df_view_r.empty:
                st.warning("Nenhum registro com este filtro.")
            else:
                df_view_r['Receber?'] = False
                df_view_r['Vencimento'] = pd.to_datetime(df_view_r['Vencimento']).dt.strftime('%d/%m/%Y')
                df_view_r['Recebido Em'] = pd.to_datetime(df_view_r['Recebido Em']).dt.strftime('%d/%m/%Y').fillna("-")
                
                is_disabled_r = ["id", "Cliente", "Fatura", "Vencimento", "Valor", "Status", "Recebido Em"]
                if status_filter_r == "RECEBIDO":
                    is_disabled_r.append("Receber?")
                    
                edited_df_r = st.data_editor(
                    df_view_r[['Receber?', 'id', 'Cliente', 'Fatura', 'Vencimento', 'Valor', 'Status', 'Recebido Em']],
                    hide_index=True,
                    disabled=is_disabled_r,
                    width="stretch",
                    height=500,
                    column_config={
                        "Receber?": st.column_config.CheckboxColumn("Receber?", help="Marque para acusar recebimento"),
                        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                    },
                    key="editor_receber"
                )
                
                selecionados_r = edited_df_r[edited_df_r['Receber?'] == True]
                st.session_state['selecionados_ids_r'] = selecionados_r['id'].tolist() if not selecionados_r.empty else []
                
                if btn_baixar_r:
                    if selecionados_r.empty:
                        st.warning("Selecione pelo menos uma fatura marcando a caixinha 'Receber?'.")
                    else:
                        dialog_confirmar_baixa_lote_receber(selecionados_r['id'].tolist(), df_receber, opcoes_bancos)


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
