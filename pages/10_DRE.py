import streamlit as st
import pandas as pd
from datetime import timedelta
from database import fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="DRE Fabril", page_icon="🏛️", layout="wide")
carregar_estilo()

st.title("🏛️ Demonstrativo do Resultado do Exercício (DRE)")
st.markdown("A Verdade Nua e Crua: Sua fábrica dá lucro ou prejuízo faturando o que fatura hoje?")

def f_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# 1. Puxar Dados Brutos (Caixa)
df_fc = fetch_all("SELECT * FROM fluxo_caixa")
hoje = pd.to_datetime('today')

if not df_fc.empty:
    df_fc['data'] = pd.to_datetime(df_fc['data'], errors='coerce')
    
    # Corte Temporal
    df_mes = df_fc[df_fc['data'] >= (hoje - timedelta(days=30))]
    df_90d = df_fc[df_fc['data'] >= (hoje - timedelta(days=90))]
    
    # --- CALCULADORA CONTÁBIL ---
    
    # Nível 1: Bruto
    rb_mes = float(df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum())
    rb_90 = float(df_90d[df_90d['tipo'] == 'Entrada']['valor'].sum()) / 3
    
    # Nível 2: Deduções (Devoluções e Impostos sobre Venda)
    dev_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].str.contains('devolução|reembolso|estorno', case=False, na=False))]['valor'].sum())
    dev_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].str.contains('devolução|reembolso|estorno', case=False, na=False))]['valor'].sum()) / 3
    
    imp_venda_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].str.contains('imposto.*venda|simples|icms|pis|cofins|das', case=False, na=False))]['valor'].sum())
    imp_venda_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].str.contains('imposto.*venda|simples|icms|pis|cofins|das', case=False, na=False))]['valor'].sum()) / 3
    
    rl_mes = rb_mes - dev_mes - imp_venda_mes
    rl_90 = rb_90 - dev_90 - imp_venda_90
    
    # Nível 2: Custo Variável (Fornecedores e Matéria Prima)
    # Aqui assumimos que qualquer saída categorizada como MP, Fornecedor, Insumo ou Compra é Custo Direto (CMV/CPV)
    chaves_cmv = ['Fornecedor', 'Fornecedores', 'Insumos', 'Matéria Prima', 'Matérias Primas', 'Compras', 'Materia Prima']
    
    cv_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].isin(chaves_cmv))]['valor'].sum())
    cv_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].isin(chaves_cmv))]['valor'].sum()) / 3
    
    # Nível 2.5: Despesas Comerciais Variáveis (Comissões, Logística, Acordos e Descargas)
    df_vd = fetch_all("SELECT data, custo_frete_rateado, comissao_valor, custo_acordos_rede, custo_descarga FROM vendas")
    df_vd['data'] = pd.to_datetime(df_vd['data'], errors='coerce')
    df_vd_mes = df_vd[df_vd['data'] >= (hoje - timedelta(days=30))]
    df_vd_90 = df_vd[df_vd['data'] >= (hoje - timedelta(days=90))]
    
    frete_mes = df_vd_mes['custo_frete_rateado'].sum() if not df_vd_mes.empty else 0.0
    frete_90 = (df_vd_90['custo_frete_rateado'].sum() / 3) if not df_vd_90.empty else 0.0
    
    comi_mes = df_vd_mes['comissao_valor'].sum() if not df_vd_mes.empty else 0.0
    comi_90 = (df_vd_90['comissao_valor'].sum() / 3) if not df_vd_90.empty else 0.0
    
    acordos_mes = df_vd_mes['custo_acordos_rede'].sum() if not df_vd_mes.empty else 0.0
    acordos_90 = (df_vd_90['custo_acordos_rede'].sum() / 3) if not df_vd_90.empty else 0.0
    
    descarga_mes = df_vd_mes['custo_descarga'].sum() if not df_vd_mes.empty else 0.0
    descarga_90 = (df_vd_90['custo_descarga'].sum() / 3) if not df_vd_90.empty else 0.0
    
    desp_com_mes = frete_mes + comi_mes + acordos_mes + descarga_mes
    desp_com_90 = frete_90 + comi_90 + acordos_90 + descarga_90
    
    # Nível 3: Margem de Contribuição (O Negócio "Alho" se paga tirando a Produção e a Entrega?)
    mc_mes = rl_mes - cv_mes - desp_com_mes
    mc_90 = rl_90 - cv_90 - desp_com_90
    mc_perc = (mc_mes / rl_mes * 100) if rl_mes > 0 else 0.0
    
    # Nível 4: Despesas Fixas (O peso Administrativo ANTES do EBITDA)
    # Excluímos também as categorias de Nível 5 (Abaixo do EBITDA)
    chaves_abaixo_ebitda = ['Depreciação', 'Impostos sobre Lucro', 'IRPJ', 'CSLL', 'Financiamento', 'Empréstimos', 'Juros', 'Despesas Financeiras', 'JCP', 'Juros sobre Capital Próprio', 'Dividendos', 'Distribuição de Lucros', 'Distribuição de Lucro']
    
    # Excluímos despesas comerciais para evitar dupla contagem com Nível 2.5
    regex_comercial = 'frete|logística|transporte|comissão|comissoes|venda'
    
    # Filtragem robusta para Mês Atual
    df_saidas_mes = df_mes[df_mes['tipo'] == 'Saída'].copy()
    df_s1 = df_saidas_mes[~df_saidas_mes['categoria'].isin(chaves_cmv + chaves_abaixo_ebitda)]
    df_fixas_mes = df_s1[~df_s1['categoria'].str.contains(regex_comercial, case=False, na=False)]
    df_mes_val = float(df_fixas_mes['valor'].sum()) if not df_fixas_mes.empty else 0.0
    
    # Filtragem robusta para 90 Dias
    df_saidas_90 = df_90d[df_90d['tipo'] == 'Saída'].copy()
    df_s90 = df_saidas_90[~df_saidas_90['categoria'].isin(chaves_cmv + chaves_abaixo_ebitda)]
    df_fixas_90 = df_s90[~df_s90['categoria'].str.contains(regex_comercial, case=False, na=False)]
    df_90 = float(df_fixas_90['valor'].sum() / 3) if not df_fixas_90.empty else 0.0
    
    # Rastreio Direcionado do Pró-labore (Apenas para exibir, pois já está dentro de df_mes_val)
    pro_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'] == 'Pró-Labore')]['valor'].sum())
    pro_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'] == 'Pró-Labore')]['valor'].sum()) / 3

    # Nível 5: O Check-Mate Estrutural (EBITDA Operacional)
    ebitda_mes = mc_mes - df_mes_val
    ebitda_90 = mc_90 - df_90
    ebitda_perc = (ebitda_mes / rl_mes * 100) if rl_mes > 0 else 0.0
    
    # Nível 6: Além do EBITDA (Depreciação, Impostos, Financiamentos)
    depr_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'] == 'Depreciação')]['valor'].sum())
    depr_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'] == 'Depreciação')]['valor'].sum()) / 3
    
    imp_lucro_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].isin(['Impostos sobre Lucro', 'IRPJ', 'CSLL']))]['valor'].sum())
    imp_lucro_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].isin(['Impostos sobre Lucro', 'IRPJ', 'CSLL']))]['valor'].sum()) / 3
    
    finan_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].isin(['Financiamento', 'Empréstimos', 'Juros', 'Despesas Financeiras']))]['valor'].sum())
    finan_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].isin(['Financiamento', 'Empréstimos', 'Juros', 'Despesas Financeiras']))]['valor'].sum()) / 3
    
    jcp_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].isin(['JCP', 'Juros sobre Capital Próprio']))]['valor'].sum())
    jcp_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].isin(['JCP', 'Juros sobre Capital Próprio']))]['valor'].sum()) / 3
    
    # Nível 7: O Dinheiro Total Gerado (Lucro Líquido Real)
    lucro_mes = ebitda_mes - depr_mes - imp_lucro_mes - finan_mes - jcp_mes
    lucro_90 = ebitda_90 - depr_90 - imp_lucro_90 - finan_90 - jcp_90
    lucro_perc = (lucro_mes / rl_mes * 100) if rl_mes > 0 else 0.0
    
    # Nível 8: Divisão Sócio vs Indústria
    div_mes = float(df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['categoria'].isin(['Dividendos', 'Distribuição de Lucros', 'Distribuição de Lucro']))]['valor'].sum())
    div_90 = float(df_90d[(df_90d['tipo'] == 'Saída') & (df_90d['categoria'].isin(['Dividendos', 'Distribuição de Lucros', 'Distribuição de Lucro']))]['valor'].sum()) / 3

    retido_mes = lucro_mes - div_mes
    retido_90 = lucro_90 - div_90
    
    # Calculadora Break-even usa as Despesas Operacionais Fixas
    break_even = (df_mes_val / (mc_perc / 100)) if mc_perc > 0 else 0.0
    
    # -------- RENDERIZAÇÃO VISUAL ---------
    
    tab1, tab2 = st.tabs(["🗺️ DRE Tático de Fábrica", "📊 Ponto de Equilíbrio (Break-Even)"])
    
    with tab1:
        st.subheader("I. Faturamento Bruto (Tração)")
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown("**1. Receita Operacional Bruta (Entradas Totais)**")
        c2.metric("Mês Atual", f_br(rb_mes))
        c3.metric("Média Últ. 90 Dias", f_br(rb_90), delta=f"{(rb_mes - rb_90)/rb_90*100:.1f}%" if rb_90>0 else "0%")
        
        c4, c5, c6 = st.columns([2, 1, 1])
        c4.markdown("**2. (-) Devoluções / Abatimentos**")
        c5.metric(" ", f_br(dev_mes), label_visibility="collapsed")
        c6.metric(" ", f_br(dev_90), label_visibility="collapsed")
        
        c_imp1, c_imp2, c_imp3 = st.columns([2, 1, 1])
        c_imp1.markdown("**3. (-) Impostos sobre Venda (Simples/ICMS/DAS)**")
        c_imp2.metric(" ", f_br(imp_venda_mes), label_visibility="collapsed")
        c_imp3.metric(" ", f_br(imp_venda_90), label_visibility="collapsed")
        
        c7, c8, c9 = st.columns([2, 1, 1])
        c7.markdown("#### (=) Receita Líquida Real")
        c8.markdown(f"#### {f_br(rl_mes)}")
        c9.markdown(f"#### {f_br(rl_90)}")
        
        st.markdown("---")
        st.subheader("II. Motores de Custo Variável (O Chão de Fábrica)")
        
        ca, cb, cc = st.columns([2, 1, 1])
        ca.markdown("**4. (-) Custos do Produto (CPV/CMV)** *(Compras de Alho)*")
        cb.metric("Mês Atual", f_br(cv_mes), delta="Saída", delta_color="inverse")
        cc.metric("Média Trimestral", f_br(cv_90), delta="Base", delta_color="off")
        
        c_c1, c_c2, c_c3 = st.columns([2, 1, 1])
        c_c1.markdown("**5. (-) Despesas Comerciais** *(Comissões & Logística/Fretes)*")
        c_c2.metric(" ", f_br(frete_mes + comi_mes), label_visibility="collapsed")
        c_c3.metric(" ", f_br(frete_90 + comi_90), label_visibility="collapsed")
        
        c_a1, c_a2, c_a3 = st.columns([2, 1, 1])
        c_a1.markdown("**5.1 (-) Acordos Comerciais (Rebates de Rede)**")
        c_a2.metric(" ", f_br(acordos_mes), label_visibility="collapsed")
        c_a3.metric(" ", f_br(acordos_90), label_visibility="collapsed")
        
        c_d1, c_d2, c_d3 = st.columns([2, 1, 1])
        c_d1.markdown("**5.2 (-) Taxas de Descarga (CD/Redes)**")
        c_d2.metric(" ", f_br(descarga_mes), label_visibility="collapsed")
        c_d3.metric(" ", f_br(descarga_90), label_visibility="collapsed")
        
        cd, ce, cf = st.columns([2, 1, 1])
        cd.markdown(f"#### (=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA   🛡️ `{mc_perc:.1f}%`")
        ce.markdown(f"#### {f_br(mc_mes)}")
        cf.markdown(f"#### {f_br(mc_90)}")
        
        st.markdown("---")
        st.subheader("III. O Peso Existencial (Despesas Engessadas)")
        
        cg, ch, ci = st.columns([2, 1, 1])
        cg.markdown("**6. (-) Desp. Fixas Totais (RH, Energia, Adm)**")
        ch.metric("Mês Atual", f_br(df_mes_val), delta="Saída", delta_color="inverse")
        ci.metric("Média Trimestral", f_br(df_90), delta="Base", delta_color="off")
        
        c_pro1, c_pro2, c_pro3 = st.columns([2, 1, 1])
        c_pro1.markdown(">*Dessa Fila: (-) Pró-Labore (Salário Sócio)*")
        c_pro2.markdown(f">*{f_br(pro_mes)}*")
        c_pro3.markdown(f">*{f_br(pro_90)}*")
        
        st.markdown("---")
        st.subheader("IV. Resultado Operacional (EBITDA)")
        cj, ck, cl = st.columns([2, 1, 1])
        cj.markdown(f"### 🛡️ EBITDA `{ebitda_perc:.1f}%`")
        if ebitda_mes < 0:
            str_ebitda = f"🛑 {f_br(ebitda_mes)}"
        else:
            str_ebitda = f"✔️ {f_br(ebitda_mes)}"
        ck.markdown(f"### {str_ebitda}")
        cl.markdown(f"### {f_br(ebitda_90)}")
        
        st.markdown("---")
        st.subheader("V. Fatores Não-Operacionais e Financeiros")
        
        cm1, cm2, cm3 = st.columns([2, 1, 1])
        cm1.markdown("**7. (-) Depreciação / Amortização**")
        cm2.metric(" ", f_br(depr_mes), label_visibility="collapsed")
        cm3.metric(" ", f_br(depr_90), label_visibility="collapsed")
        
        cn1, cn2, cn3 = st.columns([2, 1, 1])
        cn1.markdown("**8. (-) Impostos sobre Lucro (IRPJ/CSLL)**")
        cn2.metric(" ", f_br(imp_lucro_mes), label_visibility="collapsed")
        cn3.metric(" ", f_br(imp_lucro_90), label_visibility="collapsed")
        
        co1, co2, co3 = st.columns([2, 1, 1])
        co1.markdown("**9. (-) Juros e Financiamentos**")
        co2.metric(" ", f_br(finan_mes), label_visibility="collapsed")
        co3.metric(" ", f_br(finan_90), label_visibility="collapsed")
        
        cq1, cq2, cq3 = st.columns([2, 1, 1])
        cq1.markdown("**10. (-) JCP (Juros s/ Capital Próprio)**")
        cq2.metric(" ", f_br(jcp_mes), label_visibility="collapsed")
        cq3.metric(" ", f_br(jcp_90), label_visibility="collapsed")
        
        st.markdown("---")
        st.subheader("👑 VI. Lucratividade (Empresa vs Sócio)")
        
        cr1, cr2, cr3 = st.columns([2, 1, 1])
        cr1.markdown(f"#### 11.(=) LUCRO LÍQUIDO TOTAL GERADO `{lucro_perc:.1f}%`")
        cr2.markdown(f"#### {f_br(lucro_mes)}")
        cr3.markdown(f"#### {f_br(lucro_90)}")
        
        cs1, cs2, cs3 = st.columns([2, 1, 1])
        cs1.markdown("**12. (-) Dividendos (Saque/Distrib. do Sócio)**")
        cs2.metric(" ", f_br(div_mes), label_visibility="collapsed")
        cs3.metric(" ", f_br(div_90), label_visibility="collapsed")
        
        ct1, ct2, ct3 = st.columns([2, 1, 1])
        ct1.markdown(f"### 💎 LUCRO RETIDO (PATRIMÔNIO CNPJ)")
        if retido_mes < 0:
            str_ret = f"🛑 {f_br(retido_mes)}"
        else:
            str_ret = f"🚀 {f_br(retido_mes)}"
        ct2.markdown(f"### {str_ret}")
        ct3.markdown(f"### {f_br(retido_90)}")

    with tab2:
        st.subheader("Ponto de Sobrevivência (Break-Even)")
        
        st.markdown(f"> **O que é isso?** É o ponto exato de faturamento onde a sua fábrica zera todas as contas operacionais (EBITDA Zero) e passa a ter fluxo positivo para pagar bancos e lucros. Vender abaixo disso significa tirar dinheiro do próprio bolso para a fábrica abrir as portas.")
        
        colB1, colB2 = st.columns(2)
        colB1.metric("Faturamento Mínimo para Sobrevivência (Mês)", f_br(break_even))
        faltante = break_even - rl_mes
        if faltante > 0:
            colB2.metric("Ainda Faltam Vender (Neste Mês):", f_br(faltante), delta="Risco de Sangria", delta_color="inverse")
            st.warning(f"⚠️ Atenção! Você faturou apenas {f_br(rl_mes)} esse mês. A sua margem atual não cobre os R$ {df_mes_val:,.2f} de despesas fixas. Desperte a área comercial ou enxugue o RH e o aluguel.")
        else:
            lucro_acima = rl_mes - break_even
            colB2.metric("Oceano Azul (Faturamento Acima do Ponto):", f_br(lucro_acima), delta="Zona de Lucro", delta_color="normal")
            st.success(f"🥳 Parabéns Máquina! Você já estourou o teto e pagou todas das despesas desse mês. As próximas vendas são lucro quase líquido pro caixa!")
            
else:
    st.info("A Fábrica não possui histórico financeiro (Fluxo de Caixa Vazio). O DRE Comercial exige dados para ser calculado.")
