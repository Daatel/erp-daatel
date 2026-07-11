import streamlit as st


import pandas as pd

st.set_page_config(page_title="Financeiro e Tesouraria", layout="wide")

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

    df_bancos = fetch_all("SELECT id, nome, banco, saldo_inicial, limite_credito FROM contas_bancarias WHERE status='ATIVO'")

    

    opcoes_bancos = {}

    saldo_por_banco = {}

    limites_por_banco = {}

    

    if df_bancos.empty:

        st.error("Nenhuma Conta Bancária Ativa. Vá em Cadastros -> Contas Bancárias e crie pelo menos uma!")

        st.stop()

    else:

        for _, r in df_bancos.iterrows():

            opcoes_bancos[f"{r['nome']}"] = r['id']

            # Saldo começa com o fixo do sistema

            saldo_por_banco[r['id']] = float(r['saldo_inicial'])

            limites_por_banco[r['id']] = float(r['limite_credito'] or 0.0)



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

        # Custom CSS for modern visual layout

        st.markdown("""

        <style>

        .card-disponivel {

            padding: 20px;

            border-radius: 8px;

            background-color: #f8fafc;

            margin-bottom: 20px;

        }

        .conta-card {

            background-color: white;

            border: 1px solid #e2e8f0;

            padding: 15px;

            border-radius: 8px;

            margin-bottom: 10px;

        }

        .text-muted {

            color: #64748b;

            font-size: 0.85rem;

        }

        .item-list-row {

            display: flex;

            justify-content: space-between;

            padding: 8px 0;

            border-bottom: 1px solid #f1f5f9;

        }

        .item-list-desc {

            font-weight: 500;

            color: #1e293b;

        }

        .item-list-plano {

            font-size: 0.8rem;

            color: #64748b;

        }

        .item-list-val {
            font-weight: 600;
            text-align: right;
        }
        </style>
        """, unsafe_allow_html=True)

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
            
        if out_of_tolerance:
            st.error(f"Alerta de segurança: Conciliação financeira pendente! Último registro conciliado: {last_conc_date.strftime('%d/%m/%Y') if last_conc_date else 'nunca'}. A tolerância máxima é de D-1 (ontem). Efetue a conciliação na aba correspondente.")
        else:
            st.success(f"Conciliação em dia: Caixa conciliado até {last_conc_date.strftime('%d/%m/%Y') if last_conc_date else 'nunca'}.")

        # 2. Header and Segmented Control View Toggle
        col_hdr1, col_hdr2 = st.columns([2, 1])
        with col_hdr1:
            st.markdown("### Cockpit Financeiro Diário")
        with col_hdr2:
            default_visao = "Projeção do Dia" if datetime.now().hour < 13 else "Fechamento do Dia"
            visao = st.segmented_control("Visão do Painel", ["Projeção do Dia", "Fechamento do Dia"], default=default_visao, label_visibility="collapsed")

        # 3. KPI Card: Saldo Disponível Hoje (3.1)
        total_limites = sum(limites_por_banco.values())
        if saldo_total_empresa >= 0:
            border_color = "#22c55e" # Green
            situacao = "Situação Favorável"
        elif saldo_total_empresa + total_limites >= 0:
            border_color = "#eab308" # Yellow
            situacao = "Situação Requer Atenção (Utilizando Limite)"
        else:
            border_color = "#ef4444" # Red
            situacao = "Situação Crítica (Saldo Esgotado)"

        def to_brl(v):
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        st.markdown(f"""
        <div style="border-left: 5px solid {border_color}; padding: 15px; background-color: #f8fafc; border-radius: 4px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Saldo Disponível Hoje</span>
                    <h2 style="margin: 5px 0 0 0; color: #1e293b; font-size: 2.2rem; font-weight: 700;">{to_brl(saldo_total_empresa + total_limites)}</h2>
                    <span style="font-size: 0.8rem; color: #64748b; display: block; margin-top: 5px;">Inclui limite de crédito consolidado de {to_brl(total_limites)}</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-weight: 700; color: {border_color}; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em;">{situacao}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. Saldos por Conta (3.2)
        st.markdown("##### Saldos por Conta")
        cols_bancos = st.columns(len(df_bancos))
        for idx_b, (_, r_b) in enumerate(df_bancos.iterrows()):
            bid = r_b['id']
            saldo_atual = saldo_por_banco[bid]
            limite = limites_por_banco[bid]
            with cols_bancos[idx_b]:
                with st.container(border=True):
                    st.markdown(f"**{r_b['nome']}** ({r_b['banco'] or 'Banco'})")
                    st.markdown(f"Saldo: {to_brl(saldo_atual)}")
                    with st.expander("Detalhes da conta"):
                        st.markdown(f"<span class='text-muted'>Limite: {to_brl(limite)}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span class='text-muted'>Saldo com limite: {to_brl(saldo_atual + limite)}</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Calculate values for Yesterday vs Today and Tendency
        df_fluxo_hoje = fetch_all("SELECT tipo, valor FROM fluxo_caixa WHERE data = ?", (hoje.strftime("%Y-%m-%d"),))
        entradas_hoje = df_fluxo_hoje[df_fluxo_hoje['tipo'] == 'Entrada']['valor'].sum() if not df_fluxo_hoje.empty else 0.0
        saidas_hoje = df_fluxo_hoje[df_fluxo_hoje['tipo'] == 'Saída']['valor'].sum() if not df_fluxo_hoje.empty else 0.0
        variacao_hoje = entradas_hoje - saidas_hoje
        saldo_ontem = saldo_total_empresa - variacao_hoje

        # Classification quick dialog helper
        if st.session_state.get("show_class_dialog"):
            tabela, item_id, desc, val = st.session_state["show_class_dialog"]
            @st.dialog("Classificar Lançamento")
            def dialog_classificar():
                st.write(f"Descrição: **{desc}**")
                st.write(f"Valor: **{to_brl(val)}**")
                
                planos = fetch_all("SELECT id, codigo, categoria, nome FROM planos_de_contas ORDER BY codigo")
                opcoes = {f"{r['codigo']} - {r['categoria']} ({r['nome']})": r['id'] for _, r in planos.iterrows()}
                sel_plano = st.selectbox("Selecione o Plano de Contas", list(opcoes.keys()))
                
                col_d1, col_d2 = st.columns(2)
                if col_d1.button("Cancelar"):
                    st.session_state["show_class_dialog"] = None
                    st.rerun()
                if col_d2.button("Salvar Classificação", type="primary"):
                    plano_id = opcoes[sel_plano]
                    run_query(f"UPDATE {tabela} SET plano_conta_id = ? WHERE id = ?", (plano_id, item_id))
                    st.success("Lançamento classificado com sucesso!")
                    st.session_state["show_class_dialog"] = None
                    import time; time.sleep(1); st.rerun()
            dialog_classificar()

        if visao == "Projeção do Dia":
            # Verification of non-reconciled items from previous days
            df_non_conc = fetch_all("SELECT COUNT(*) as count FROM fluxo_caixa WHERE data < ? AND (conciliado = FALSE OR conciliado IS NULL OR conciliado = 0)", (hoje.strftime("%Y-%m-%d"),))
            non_conc_count = int(df_non_conc.iloc[0]['count']) if not df_non_conc.empty else 0
            if non_conc_count > 0:
                st.warning(f"Relatório Requer Posições Conciliadas. Existem {non_conc_count} lançamentos pendentes de conciliação de dias anteriores.")

            # Aging de Atrasados (3.4)
            df_rec_overdue = fetch_all("SELECT valor, data_vencimento FROM contas_a_receber WHERE status='PENDENTE' AND data_vencimento < ?", (hoje.strftime("%Y-%m-%d"),))
            df_pag_overdue = fetch_all("SELECT valor, data_vencimento FROM contas_a_pagar WHERE status='PENDENTE' AND data_vencimento < ?", (hoje.strftime("%Y-%m-%d"),))
            
            total_rec_overdue = 0.0
            total_pag_overdue = 0.0
            rec_aging = {"0-30": 0.0, "31-60": 0.0, "60+": 0.0}
            pag_aging = {"0-30": 0.0, "31-60": 0.0, "60+": 0.0}
            
            if not df_rec_overdue.empty:
                total_rec_overdue = df_rec_overdue['valor'].sum()
                for _, r in df_rec_overdue.iterrows():
                    dias = (hoje - pd.to_datetime(r['data_vencimento']).date()).days
                    val = float(r['valor'])
                    if dias <= 30:
                         rec_aging["0-30"] += val
                    elif dias <= 60:
                         rec_aging["31-60"] += val
                    else:
                         rec_aging["60+"] += val
                         
            if not df_pag_overdue.empty:
                total_pag_overdue = df_pag_overdue['valor'].sum()
                for _, r in df_pag_overdue.iterrows():
                    dias = (hoje - pd.to_datetime(r['data_vencimento']).date()).days
                    val = float(r['valor'])
                    if dias <= 30:
                         pag_aging["0-30"] += val
                    elif dias <= 60:
                         pag_aging["31-60"] += val
                    else:
                         pag_aging["60+"] += val

            st.markdown("##### Aging de Atrasados")
            col_atr1, col_atr2 = st.columns(2)
            with col_atr1:
                st.markdown(f"Total a Receber em Atraso: <span style='color:#ef4444; font-weight:700;'>{to_brl(total_rec_overdue)}</span>", unsafe_allow_html=True)
            with col_atr2:
                st.markdown(f"Total a Pagar em Atraso: <span style='color:#b45309; font-weight:700;'>{to_brl(total_pag_overdue)}</span>", unsafe_allow_html=True)
                
            col_ag1, col_ag2 = st.columns(2)
            with col_ag1:
                st.markdown("**Aging a Receber:**")
                st.markdown(f"- 0 a 30 dias: {to_brl(rec_aging['0-30'])}")
                st.markdown(f"- 31 a 60 dias: {to_brl(rec_aging['31-60'])}")
                st.markdown(f"- Mais de 60 dias: {to_brl(rec_aging['60+'])}")
            with col_ag2:
                st.markdown("**Aging a Pagar:**")
                st.markdown(f"- 0 a 30 dias: {to_brl(pag_aging['0-30'])}")
                st.markdown(f"- 31 a 60 dias: {to_brl(pag_aging['31-60'])}")
                st.markdown(f"- Mais de 60 dias: {to_brl(pag_aging['60+'])}")

            st.markdown("---")

            # Tendência (3.5)
            if variacao_hoje > 0.01:
                tend_char = "▲"
                tend_text = "Alta"
                tend_color = "#22c55e"
            elif variacao_hoje < -0.01:
                tend_char = "▼"
                tend_text = "Queda"
                tend_color = "#ef4444"
            else:
                tend_char = "▬"
                tend_text = "Estável"
                tend_color = "#64748b"
                
            st.markdown(f"Tendência de Caixa: <span style='color:{tend_color}; font-weight:700;'>{tend_char} {tend_text} ({to_brl(abs(variacao_hoje))} em relação a ontem)</span>", unsafe_allow_html=True)

            st.markdown("---")

            # Compromissos do Dia (3.3)
            df_rec_today = fetch_all("""
                SELECT r.id, r.descricao, r.valor, p.codigo, p.categoria
                FROM contas_a_receber r
                LEFT JOIN planos_de_contas p ON r.plano_conta_id = p.id
                WHERE r.status='PENDENTE' AND r.data_vencimento = ?
            """, (hoje.strftime("%Y-%m-%d"),))
            
            df_pag_today = fetch_all("""
                SELECT p.id, p.descricao, p.valor, pc.codigo, pc.categoria
                FROM contas_a_pagar p
                LEFT JOIN planos_de_contas pc ON p.plano_conta_id = pc.id
                WHERE p.status='PENDENTE' AND p.data_vencimento = ?
            """, (hoje.strftime("%Y-%m-%d"),))
            
            soma_rec_today = df_rec_today['valor'].sum() if not df_rec_today.empty else 0.0
            soma_pag_today = df_pag_today['valor'].sum() if not df_pag_today.empty else 0.0

            st.markdown("##### Compromissos do Dia")
            col_comp1, col_comp2 = st.columns(2)
            with col_comp1:
                st.markdown(f"**Entradas Previstas (Hoje):** {to_brl(soma_rec_today)}")
                if df_rec_today.empty:
                    st.info("Nenhuma entrada prevista para hoje.")
                else:
                    for _, r in df_rec_today.iterrows():
                        item_id = r['id']
                        desc = r['descricao']
                        val = r['valor']
                        codigo = r['codigo']
                        cat = r['categoria']
                        
                        col_i1, col_i2 = st.columns([3, 1])
                        with col_i1:
                            st.markdown(f"<span class='item-list-desc'>{desc}</span>", unsafe_allow_html=True)
                            if codigo and cat:
                                st.markdown(f"<span class='item-list-plano'>Plano: {codigo} - {cat}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='color:#ef4444; font-size:0.8rem; font-weight:600;'>Sem categoria - classificar</span>", unsafe_allow_html=True)
                                if st.button("Classificar", key=f"class_rec_{item_id}"):
                                    st.session_state["show_class_dialog"] = ("contas_a_receber", item_id, desc, val)
                                    st.rerun()
                        with col_i2:
                            st.markdown(f"<div class='item-list-val' style='color:#2563eb;'>{to_brl(val)}</div>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:4px 0;'/>", unsafe_allow_html=True)
                        
            with col_comp2:
                st.markdown(f"**Saídas Previstas (Hoje):** {to_brl(soma_pag_today)}")
                if df_pag_today.empty:
                    st.info("Nenhuma saída prevista para hoje.")
                else:
                    for _, r in df_pag_today.iterrows():
                        item_id = r['id']
                        desc = r['descricao']
                        val = r['valor']
                        codigo = r['codigo']
                        cat = r['categoria']
                        
                        col_i1, col_i2 = st.columns([3, 1])
                        with col_i1:
                            st.markdown(f"<span class='item-list-desc'>{desc}</span>", unsafe_allow_html=True)
                            if codigo and cat:
                                st.markdown(f"<span class='item-list-plano'>Plano: {codigo} - {cat}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='color:#ef4444; font-size:0.8rem; font-weight:600;'>Sem categoria - classificar</span>", unsafe_allow_html=True)
                                if st.button("Classificar", key=f"class_pag_{item_id}"):
                                    st.session_state["show_class_dialog"] = ("contas_a_pagar", item_id, desc, val)
                                    st.rerun()
                        with col_i2:
                            st.markdown(f"<div class='item-list-val' style='color:#ef4444;'>{to_brl(val)}</div>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:4px 0;'/>", unsafe_allow_html=True)

            st.markdown("---")

            # 30-Day Cash Flow Projection Chart
            st.markdown("##### Painel de Liquidez Projetado (30 Dias)")
            incluir_atraso = st.checkbox("Considerar contas em atraso no gráfico", value=False, key="inc_atrasados_chk_30d")
            
            df_rec_futuro = fetch_all("SELECT valor, data_vencimento FROM contas_a_receber WHERE status='PENDENTE'")
            df_pag_futuro = fetch_all("SELECT valor, data_vencimento FROM contas_a_pagar WHERE status='PENDENTE'")
            
            fluxo_30d = {}
            for i in range(30):
                d_alvo = hoje + timedelta(days=i)
                fluxo_30d[str(d_alvo)] = {"Entradas": 0.0, "Saídas": 0.0}
                
            if not df_rec_futuro.empty:
                df_rec_futuro['venc_date'] = pd.to_datetime(df_rec_futuro['data_vencimento']).dt.date
                for _, r in df_rec_futuro.iterrows():
                    v_date = r['venc_date']
                    val = float(r['valor'])
                    if v_date < hoje and incluir_atraso:
                        fluxo_30d[str(hoje)]["Entradas"] += val
                    elif str(v_date) in fluxo_30d:
                        fluxo_30d[str(v_date)]["Entradas"] += val
                        
            if not df_pag_futuro.empty:
                df_pag_futuro['venc_date'] = pd.to_datetime(df_pag_futuro['data_vencimento']).dt.date
                for _, r in df_pag_futuro.iterrows():
                    v_date = r['venc_date']
                    val = float(r['valor'])
                    if v_date < hoje and incluir_atraso:
                        fluxo_30d[str(hoje)]["Saídas"] += val
                    elif str(v_date) in fluxo_30d:
                        fluxo_30d[str(v_date)]["Saídas"] += val
                        
            datas_30 = []
            entradas_30 = []
            saidas_30 = []
            saldos_30 = []
            saldo_proj = saldo_total_empresa
            
            for i in range(30):
                d_alvo = hoje + timedelta(days=i)
                ent = fluxo_30d[str(d_alvo)]["Entradas"]
                sai = fluxo_30d[str(d_alvo)]["Saídas"]
                saldo_proj = saldo_proj + ent - sai
                
                datas_30.append(d_alvo.strftime("%d/%m"))
                entradas_30.append(ent)
                saidas_30.append(sai)
                saldos_30.append(saldo_proj)
                
            fig_30 = go.Figure()
            fig_30.add_trace(go.Bar(
                x=datas_30, y=entradas_30,
                name="Entradas Previstas",
                marker_color='#2563eb'
            ))
            fig_30.add_trace(go.Bar(
                x=datas_30, y=[-s for s in saidas_30],
                name="Saídas Previstas",
                marker_color='#ef4444'
            ))
            fig_30.add_trace(go.Scatter(
                x=datas_30, y=saldos_30,
                name="Saldo Acumulado",
                line=dict(color='#10b981', width=3),
                yaxis="y2"
            ))
            fig_30.update_layout(
                barmode='relative',
                title="Fluxo de Caixa Projetado (Próximos 30 Dias)",
                xaxis=dict(title="Dia"),
                yaxis=dict(title="Movimentação Diária (R$)"),
                yaxis2=dict(
                    title="Saldo Acumulado (R$)",
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.01, y=0.99),
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            fig_30.update_yaxes(gridcolor='rgba(128,128,128,0.2)', zerolinecolor='rgba(128,128,128,0.5)', zerolinewidth=1)
            st.plotly_chart(fig_30, use_container_width=True)

        elif visao == "Fechamento do Dia":
            # Comparative yesterday vs today cards (3.6)
            col_cmp1, col_cmp2 = st.columns(2)
            with col_cmp1:
                with st.container(border=True):
                    st.markdown("Saldo de Fechamento de Ontem")
                    st.markdown(f"### {to_brl(saldo_ontem)}")
            with col_cmp2:
                with st.container(border=True):
                    st.markdown("Saldo de Fechamento de Hoje")
                    st.markdown(f"### {to_brl(saldo_total_empresa)}")
                    
            st.markdown(f"Resultado Real de Hoje: **{to_brl(variacao_hoje)}**")
            st.markdown("---")

            # Fetch today's actual cash flow entries mapped to Plano de Contas
            q_mov = """
                SELECT 
                    f.id,
                    f.data,
                    f.tipo,
                    f.categoria as fc_categoria,
                    f.descricao,
                    f.valor,
                    f.conciliado,
                    COALESCE(pc_p.codigo, pc_r.codigo) as plano_codigo,
                    COALESCE(pc_p.categoria, pc_r.categoria) as plano_categoria,
                    COALESCE(pc_p.nome, pc_r.nome) as plano_nome
                FROM fluxo_caixa f
                LEFT JOIN contas_a_pagar cp ON f.tipo = 'Saída' AND f.fonte_id = cp.id AND f.categoria NOT IN ('Transferência', 'Ajuste de saldo')
                LEFT JOIN planos_de_contas pc_p ON cp.plano_conta_id = pc_p.id
                LEFT JOIN contas_a_receber cr ON f.tipo = 'Entrada' AND f.fonte_id = cr.id AND f.categoria NOT IN ('Transferência', 'Ajuste de saldo')
                LEFT JOIN planos_de_contas pc_r ON cr.plano_conta_id = pc_r.id
                WHERE f.data = ?
            """
            df_mov = fetch_all(q_mov, (hoje.strftime("%Y-%m-%d"),))

            st.markdown("##### Movimentações Financeiras Realizadas")
            if df_mov.empty:
                st.info("Nenhuma movimentação realizada hoje.")
            else:
                for _, r in df_mov.iterrows():
                    tipo = r['tipo']
                    desc = r['descricao']
                    val = r['valor']
                    codigo = r['plano_codigo']
                    cat = r['plano_categoria']
                    
                    col_i1, col_i2 = st.columns([3, 1])
                    with col_i1:
                        st.markdown(f"<span class='item-list-desc'>{desc}</span>", unsafe_allow_html=True)
                        if codigo and cat:
                            st.markdown(f"<span class='item-list-plano'>Plano: {codigo} - {cat}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span class='item-list-plano'>Categoria: {r['fc_categoria']}</span>", unsafe_allow_html=True)
                    with col_i2:
                        color = "#2563eb" if tipo == "Entrada" else "#ef4444"
                        st.markdown(f"<div class='item-list-val' style='color:{color};'>{to_brl(val)}</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin:4px 0;'/>", unsafe_allow_html=True)

            st.markdown("---")

            # Conciliação table (3.6)
            st.markdown("##### Conciliação de Caixa")
            if df_mov.empty:
                st.info("Nenhum lançamento hoje para conciliar.")
            else:
                df_editor_input = df_mov[["id", "tipo", "descricao", "valor", "conciliado"]].copy()
                df_editor_input["conciliado"] = df_editor_input["conciliado"].astype(bool)
                
                edited_mov_df = st.data_editor(
                    df_editor_input,
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "tipo": st.column_config.TextColumn("Tipo", disabled=True),
                        "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                        "valor": st.column_config.NumberColumn("Valor", disabled=True, format="R$ %.2f"),
                        "conciliado": st.column_config.CheckboxColumn("Conciliado", default=False)
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="conciliacao_diaria_editor"
                )
                
                if st.button("Salvar Conciliação"):
                    with st.spinner("Salvando conciliação..."):
                        for _, r_ed in edited_mov_df.iterrows():
                            original_row = df_mov[df_mov["id"] == r_ed["id"]].iloc[0]
                            if bool(r_ed["conciliado"]) != bool(original_row["conciliado"]):
                                run_query("UPDATE fluxo_caixa SET conciliado = ? WHERE id = ?", (1 if r_ed["conciliado"] else 0, int(r_ed["id"])))
                    st.success("Conciliação atualizada com sucesso!")
                    import time; time.sleep(1); st.rerun()

            st.markdown("---")

            # Report A4 PDF Generator (3.7)
            def gerar_pdf_fechamento_diario(df_pdf, s_ontem, s_hoje, var_dia, t_ent, t_sai):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(0, 10, "EMPORIO DO ALHO - FECHAMENTO FINANCEIRO DIÁRIO", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"Data do Fechamento: {date.today().strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.ln(5)
                
                # Resumo Financeiro
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Resumo do Dia", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(90, 6, f"Saldo Inicial (Ontem): {to_brl(s_ontem)}", border=1)
                pdf.cell(90, 6, f"Saldo Final (Hoje): {to_brl(s_hoje)}", border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.cell(90, 6, f"Total de Entradas: {to_brl(t_ent)}", border=1)
                pdf.cell(90, 6, f"Total de Saídas: {to_brl(t_sai)}", border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.cell(180, 6, f"Resultado Real: {to_brl(var_dia)}", border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)
                
                # Movimentações
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Movimentações Financeiras Realizadas", new_x="LMARGIN", new_y="NEXT")
                
                # Table headers
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(20, 6, "Tipo", border=1)
                pdf.cell(80, 6, "Descrição", border=1)
                pdf.cell(50, 6, "Categoria", border=1)
                pdf.cell(30, 6, "Valor", border=1, new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("Helvetica", "", 8)
                if df_pdf.empty:
                    pdf.cell(180, 6, "Nenhuma movimentação registrada hoje.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                else:
                    for _, r in df_pdf.iterrows():
                        tipo = r['tipo']
                        desc = str(r['descricao'])
                        cat = str(r['plano_categoria'] or r['fc_categoria'] or "Sem categoria")
                        val = float(r['valor'])
                        
                        def clean_str(s):
                            import unicodedata
                            return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                            
                        pdf.cell(20, 6, clean_str(tipo), border=1)
                        pdf.cell(80, 6, clean_str(desc)[:45], border=1)
                        pdf.cell(50, 6, clean_str(cat)[:28], border=1)
                        pdf.cell(30, 6, to_brl(val), border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                        
                pdf.ln(10)
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 6, "Powered by Daatel | Wisdom into Technology", new_x="LMARGIN", new_y="NEXT", align="C")
                return bytes(pdf.output())

            pdf_bytes = gerar_pdf_fechamento_diario(df_mov, saldo_ontem, saldo_total_empresa, variacao_hoje, entradas_hoje, saidas_hoje)
            st.download_button(
                label="Baixar Fechamento em PDF",
                data=pdf_bytes,
                file_name=f"fechamento_{hoje.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

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

            df_display_view.columns = ['Vencimento', 'Tipo', 'Contato', 'Histórico', 'Valor', 'Status de Prazo']

            

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
            SELECT c.id, f.nome_fantasia as 'Fornecedor', cl.nome as 'Cliente', c.numero_documento as 'N. Doc', p.nome as 'Planta de Custo', 
                   c.descricao as 'Histórico', c.data_vencimento as 'Vencimento', 
                   c.valor as 'Valor', c.status as 'Status', c.data_pagamento as 'Data PGTO',
                   c.comprovante_url as 'Comprovante', c.cliente_id
            FROM contas_a_pagar c
            LEFT JOIN fornecedores f ON c.fornecedor_id = f.id
            LEFT JOIN clientes cl ON c.cliente_id = cl.id
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

            

        def determinar_credor(r):
            forn = r.get('Fornecedor')
            if forn and pd.notna(forn) and str(forn).strip() and str(forn) != 'None':
                return str(forn).strip()
            
            cli = r.get('Cliente')
            if cli and pd.notna(cli) and str(cli).strip() and str(cli) != 'None':
                return str(cli).strip()
                
            desc = r.get('Histórico') or ""
            if " - VT - " in desc:
                return desc.split(" - VT - ")[-1].strip()
            if " - VR - " in desc:
                return desc.split(" - VR - ")[-1].strip()
            if "Repasse de Comissão Consolidada - " in desc:
                try:
                    return desc.split("Repasse de Comissão Consolidada - ")[1].split(" - ")[0].strip()
                except:
                    pass
            return ""

        if not df_all_contas.empty:
            df_all_contas['Bloqueado'] = df_all_contas['Histórico'].apply(checar_trava)
            df_all_contas['Credor'] = df_all_contas.apply(determinar_credor, axis=1)
            df_all_contas['Credor'] = df_all_contas.apply(
                lambda r: f"🔴 [BLOQUEADO FALTAM CANHOTOS] {r['Credor']}" if r.get('Bloqueado', False) else r['Credor'], axis=1
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

                hoje = date.today()

                primeiro_dia = date(hoje.year, hoje.month, 1)

                ultimo_dia = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])

                total_pago_mes_p = float(df_pago[(df_pago['p_date'] >= primeiro_dia) & (df_pago['p_date'] <= ultimo_dia)]['Valor'].sum())



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
            
            def format_doc_p(row):
                d = str(row['N. Doc']).strip()
                doc = f"#{row['id']}" if d == 'None' or d == 'nan' or d == '' else d
                
                import re
                m = re.search(r'\(\s*(\d+/\d+)\s*\)', str(row['Histórico']))
                if m:
                    return f"{doc} - {m.group(1)}"
                return doc
            df_view_p['N. Doc'] = df_view_p.apply(format_doc_p, axis=1)
            
            def clean_fatura_p(row):
                desc = str(row['Histórico'])
                if 'Venda #' in desc and 'Descarga' not in desc and 'Acordo' not in desc:
                     m = re.search(r'\([^)]+-\s*(.*?)\)$', desc)
                     if m:
                         return m.group(1)
                elif 'Acerto Rota/Manifesto' in desc:
                     return 'Acerto Rota/Manifesto'
                return desc
                
            df_view_p['Histórico'] = df_view_p.apply(clean_fatura_p, axis=1)



            if status_filter_p != "TODAS":

                df_view_p = df_view_p[df_view_p['Status'] == status_filter_p]

                

            if busca_txt_p:

                b_p = busca_txt_p.lower()

                df_view_p = df_view_p[

                    df_view_p['Credor'].str.lower().str.contains(b_p, na=False) |

                    df_view_p['Histórico'].str.lower().str.contains(b_p, na=False)

                ]

                

            if df_view_p.empty:

                st.warning("Nenhum registro com este filtro.")

            else:

                df_view_p['Pagar?'] = False

                df_view_p['Vencimento'] = pd.to_datetime(df_view_p['Vencimento']).dt.strftime('%d/%m/%Y')

                df_view_p['Data PGTO'] = pd.to_datetime(df_view_p['Data PGTO']).dt.strftime('%d/%m/%Y').fillna("-")

                

                # Se for pago, desabilitamos o checkbox Pagar?

                is_disabled_p = ["id", "Credor", "Planta de Custo", "Histórico", "Vencimento", "Valor", "Status", "Data PGTO"]

                if status_filter_p == "PAGO":

                    is_disabled_p.append("Pagar?")

                    

                edited_df_p = st.data_editor(

                    df_view_p[['Pagar?', 'id', 'Credor', 'N. Doc', 'Vencimento', 'Valor', 'Histórico', 'Status', 'Data PGTO']],

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

            SELECT c.id, cl.nome as 'Cliente', c.numero_documento as 'N. Doc', c.descricao as 'Histórico', 

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

                hoje = date.today()

                primeiro_dia = date(hoje.year, hoje.month, 1)

                ultimo_dia = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])

                total_recebido_mes_r = float(df_recebido_r[(df_recebido_r['r_date'] >= primeiro_dia) & (df_recebido_r['r_date'] <= ultimo_dia)]['Valor'].sum())



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
            
            def format_doc_r(row):
                d = str(row['N. Doc']).strip()
                doc = f"#{row['id']}" if d == 'None' or d == 'nan' or d == '' else d
                
                # Check for (X/X) in Fatura
                import re
                m = re.search(r'\(\s*(\d+/\d+)\s*\)', str(row['Histórico']))
                if m:
                    return f"{doc} - {m.group(1)}"
                return doc
                
            df_view_r['N. Doc'] = df_view_r.apply(format_doc_r, axis=1)
            
            def clean_fatura_r(row):
                desc = str(row['Histórico'])
                if 'Venda #' in desc:
                    return "-" # Ocultar info redundante para vendas automáticas
                return desc
                
            df_view_r['Histórico'] = df_view_r.apply(clean_fatura_r, axis=1)



            if status_filter_r != "TODAS":

                df_view_r = df_view_r[df_view_r['Status'] == status_filter_r]

                

            if busca_txt_r:

                b_r = busca_txt_r.lower()

                df_view_r = df_view_r[

                    df_view_r['Cliente'].str.lower().str.contains(b_r, na=False) |

                    df_view_r['Histórico'].str.lower().str.contains(b_r, na=False)

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

                    df_view_r[['Receber?', 'id', 'Cliente', 'N. Doc', 'Vencimento', 'Valor', 'Histórico', 'Status', 'Recebido Em']],

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

            SELECT c.id, f.nome_fantasia as 'Fornecedor', c.numero_documento as 'N. Doc', p.nome as 'Planta de Custo', 

                   c.descricao as 'Histórico', c.data_vencimento as 'Vencimento', 

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

            contas_man = df_all_contas[df_all_contas['Histórico'].str.contains("Acerto Rota/Manifesto #", na=False)]

            if not contas_man.empty:

                opcoes_audit = {}

                for _, r in contas_man.iterrows():

                    try:

                        man_id = int(r['Histórico'].split("#")[1].split("-")[0].strip())

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

                df_all_contas['Histórico'].str.contains("Taxa de Descarga", na=False)

            ]

            if df_desc_ag.empty:

                st.info("✅ Nenhuma taxa de descarga pendente de auditoria.")

            else:

                for _, rd in df_desc_ag.iterrows():

                    st.markdown(f"**#{rd['id']} | {rd['Histórico']}**")

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

