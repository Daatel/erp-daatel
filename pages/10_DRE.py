import streamlit as st
import pandas as pd
import calendar
from datetime import timedelta, date
from database import fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="DRE Fabril", page_icon="🏛️", layout="wide")
carregar_estilo()

st.title("🏛️ Demonstrativo do Resultado do Exercício (DRE)")
st.markdown("A Verdade Nua e Crua: Sua fábrica dá lucro ou prejuízo faturando o que fatura hoje?")

def f_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# 1. Filtro de Calendário no Topo
hoje = date.today()
meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

opcoes_meses = []
for ano in [hoje.year - 1, hoje.year, hoje.year + 1]:
    for m in range(1, 13):
        opcoes_meses.append(f"{meses_nomes[m-1]}/{ano}")

default_label = f"{meses_nomes[hoje.month-1]}/{hoje.year}"
default_idx = opcoes_meses.index(default_label) if default_label in opcoes_meses else len(opcoes_meses) // 2

sel_mes_ano = st.selectbox("Selecione o Mês/Ano de Referência do DRE:", opcoes_meses, index=default_idx)

nome_mes, ano_sel = sel_mes_ano.split("/")
ano_sel = int(ano_sel)
mes_sel = meses_nomes.index(nome_mes) + 1

# Pandas period for selected month
p_mes = pd.Period(f"{ano_sel}-{mes_sel:02d}", freq='M')
p_90 = [p_mes - 2, p_mes - 1, p_mes]

# Dates for DB query ranges
dt_vd_devol_inicio_str = (p_mes - 2).start_time.strftime("%Y-%m-%d")
dt_vd_devol_fim_str = p_mes.end_time.strftime("%Y-%m-%d")

dt_cap_inicio_str = (p_mes - 2).start_time.strftime("%Y-%m-%d")
dt_cap_fim_str = (p_mes + 1).end_time.strftime("%Y-%m-%d")

# --- QUERY DAS VENDAS (para M-2, M-1, M) ---
df_vd = fetch_all("""
    SELECT valor_total, quantidade, custo_frete_rateado, comissao_valor, custo_acordos_rede, custo_descarga, custo_cmv_real, data
    FROM vendas
    WHERE status = 'FATURADO' AND data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if not df_vd.empty:
    df_vd['data'] = pd.to_datetime(df_vd['data'], errors='coerce')
    df_vd['sale_month'] = df_vd['data'].dt.to_period('M')
else:
    df_vd = pd.DataFrame(columns=['valor_total', 'quantidade', 'custo_frete_rateado', 'comissao_valor', 'custo_acordos_rede', 'custo_descarga', 'custo_cmv_real', 'sale_month'])

# --- QUERY DE DEVOLUÇÕES (para M-2, M-1, M) ---
df_devol = fetch_all("""
    SELECT valor_financeiro_abatido, data FROM devolucoes WHERE data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if not df_devol.empty:
    df_devol['data'] = pd.to_datetime(df_devol['data'], errors='coerce')
    df_devol['devol_month'] = df_devol['data'].dt.to_period('M')
else:
    df_devol = pd.DataFrame(columns=['valor_financeiro_abatido', 'devol_month'])

# --- QUERY DO CONTAS A PAGAR (para M-2, M-1, M, M+1) ---
df_cap = fetch_all("""
    SELECT c.valor, c.data_vencimento, pc.codigo, pc.categoria as pc_cat, pc.nome as pc_nome
    FROM contas_a_pagar c
    JOIN planos_de_contas pc ON c.plano_conta_id = pc.id
    WHERE c.data_vencimento >= ? AND c.data_vencimento <= ?
""", (dt_cap_inicio_str, dt_cap_fim_str))

if not df_cap.empty:
    df_cap['data_vencimento'] = pd.to_datetime(df_cap['data_vencimento'], errors='coerce')
    df_cap['venc_month'] = df_cap['data_vencimento'].dt.to_period('M')
    
    # Define reference month based on whether it is a fixed expense or not
    is_fixed = df_cap['codigo'].str.startswith(('2.3.', '3.1.'), na=False) & ~df_cap['codigo'].str.startswith('2.3.6', na=False)
    
    df_cap['ref_month'] = df_cap['venc_month']
    # If it is a fixed expense (starting with 2.3. or 3.1. except 2.3.6), the reference month is the month before the due date's month (venc_month - 1)
    df_cap.loc[is_fixed, 'ref_month'] = df_cap.loc[is_fixed, 'venc_month'] - 1
else:
    df_cap = pd.DataFrame(columns=['valor', 'codigo', 'pc_cat', 'pc_nome', 'ref_month'])

# --- FILTRAGEM POR MÊS E 90 DIAS ---
df_vd_mes = df_vd[df_vd['sale_month'] == p_mes]
df_vd_90 = df_vd[df_vd['sale_month'].isin(p_90)]

df_devol_mes = df_devol[df_devol['devol_month'] == p_mes]
df_devol_90 = df_devol[df_devol['devol_month'].isin(p_90)]

df_cap_mes = df_cap[df_cap['ref_month'] == p_mes]
df_cap_90 = df_cap[df_cap['ref_month'].isin(p_90)]

# --- CALCULADORA CONTÁBIL (REGIME DE COMPETÊNCIA) ---

# Nível 1: Receita Operacional Bruta
rb_mes = float(df_vd_mes['valor_total'].sum()) if not df_vd_mes.empty else 0.0
rb_90 = float(df_vd_90['valor_total'].sum() / 3) if not df_vd_90.empty else 0.0

# Nível 2: Deduções (Devoluções e Impostos sobre Venda)
dev_mes = float(df_devol_mes['valor_financeiro_abatido'].sum()) if not df_devol_mes.empty else 0.0
dev_90 = float(df_devol_90['valor_financeiro_abatido'].sum() / 3) if not df_devol_90.empty else 0.0

imp_venda_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.3', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
imp_venda_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.1.3', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

rl_mes = rb_mes - dev_mes - imp_venda_mes
rl_90 = rb_90 - dev_90 - imp_venda_90

# Nível CMV
cv_mes = float(df_vd_mes['custo_cmv_real'].sum()) if not df_vd_mes.empty else 0.0
cv_90 = float(df_vd_90['custo_cmv_real'].sum() / 3) if not df_vd_90.empty else 0.0

# Despesas Comerciais Variáveis
frete_mes = float(df_vd_mes['custo_frete_rateado'].sum()) if not df_vd_mes.empty else 0.0
frete_90 = float(df_vd_90['custo_frete_rateado'].sum() / 3) if not df_vd_90.empty else 0.0

comi_mes = float(df_vd_mes['comissao_valor'].sum()) if not df_vd_mes.empty else 0.0
comi_90 = float(df_vd_90['comissao_valor'].sum() / 3) if not df_vd_90.empty else 0.0

acordos_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.2', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
acordos_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.2.2', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

descarga_mes = float(df_vd_mes['custo_descarga'].sum()) if not df_vd_mes.empty else 0.0
descarga_90 = float(df_vd_90['custo_descarga'].sum() / 3) if not df_vd_90.empty else 0.0

degust_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.1', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
degust_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.2.1', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

promotores_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.4', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
promotores_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.2.4', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

desp_com_mes = frete_mes + comi_mes + acordos_mes + descarga_mes + degust_mes + promotores_mes
desp_com_90 = frete_90 + comi_90 + acordos_90 + descarga_90 + degust_90 + promotores_90

# Margem de Contribuição
mc_mes = rl_mes - cv_mes - desp_com_mes
mc_90 = rl_90 - cv_90 - desp_com_90
mc_perc = (mc_mes / rl_mes * 100) if rl_mes > 0 else 0.0

# Despesas Fixas (plano de contas 2.3 e 3.1 com vencimento em M+1)
df_mes_val = float(df_cap_mes[df_cap_mes['codigo'].str.startswith(('2.3.', '3.1.'), na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
df_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith(('2.3.', '3.1.'), na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

# Pró-Labore (3.1.4)
pro_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('3.1.4', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
pro_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('3.1.4', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

# Resultado Operacional (EBITDA)
ebitda_mes = mc_mes - df_mes_val
ebitda_90 = mc_90 - df_90
ebitda_perc = (ebitda_mes / rl_mes * 100) if rl_mes > 0 else 0.0

# Fatores Não-Operacionais e Financeiros (Vencimento em M+1 se fixo, senão em M)
depr_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('Depreciação', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
depr_90 = float(df_cap_90[df_cap_90['pc_nome'].str.contains('Depreciação', case=False, na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

imp_lucro_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('Impostos sobre Lucro|IRPJ|CSLL', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
imp_lucro_90 = float(df_cap_90[df_cap_90['pc_nome'].str.contains('Impostos sobre Lucro|IRPJ|CSLL', case=False, na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

finan_mes = float(df_cap_mes[(df_cap_mes['codigo'] == '3.2.1') | (df_cap_mes['pc_nome'].str.contains('Financiamento|Empréstimo|Juros|Despesas Financeiras', case=False, na=False))]['valor'].sum()) if not df_cap_mes.empty else 0.0
finan_90 = float(df_cap_90[(df_cap_90['codigo'] == '3.2.1') | (df_cap_90['pc_nome'].str.contains('Financiamento|Empréstimo|Juros|Despesas Financeiras', case=False, na=False))]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

jcp_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('JCP|Juros sobre Capital Próprio', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
jcp_90 = float(df_cap_90[df_cap_90['pc_nome'].str.contains('JCP|Juros sobre Capital Próprio', case=False, na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

# Lucro Líquido
lucro_mes = ebitda_mes - depr_mes - imp_lucro_mes - finan_mes - jcp_mes
lucro_90 = ebitda_90 - depr_90 - imp_lucro_90 - finan_90 - jcp_90
lucro_perc = (lucro_mes / rl_mes * 100) if rl_mes > 0 else 0.0

div_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('Dividendos|Distribuição de Lucro', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
div_90 = float(df_cap_90[df_cap_90['pc_nome'].str.contains('Dividendos|Distribuição de Lucro', case=False, na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

retido_mes = lucro_mes - div_mes
retido_90 = lucro_90 - div_90

# Ponto de Equilíbrio
break_even = (df_mes_val / (mc_perc / 100)) if mc_perc > 0 else 0.0

# -------- RENDERIZAÇÃO VISUAL ---------

tab1, tab2 = st.tabs(["🗺️ DRE Tático de Fábrica", "📊 Ponto de Equilíbrio (Break-Even)"])

with tab1:
    st.subheader("I. Faturamento Bruto (Tração)")
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown(f"**1. Receita Operacional Bruta (Entradas Totais de {sel_mes_ano})**")
    c2.metric("Mês Atual", f_br(rb_mes))
    c3.metric("Média Últ. 90 Dias", f_br(rb_90), delta=f"{(rb_mes - rb_90)/rb_90*100:.1f}%" if rb_90>0 else "0%")
    
    c4, c5, c6 = st.columns([2, 1, 1])
    c4.markdown("**2. (-) Devoluções / Abatimentos**")
    c5.metric(" ", f_br(dev_mes), label_visibility="collapsed")
    c6.metric(" ", f_br(dev_90), label_visibility="collapsed")
    
    c_imp1, c_imp2, c_imp3 = st.columns([2, 1, 1])
    c_imp1.markdown("**3. (-) Impostos sobre Venda (Vencimento no Mês)**")
    c_imp2.metric(" ", f_br(imp_venda_mes), label_visibility="collapsed")
    c_imp3.metric(" ", f_br(imp_venda_90), label_visibility="collapsed")
    
    c7, c8, c9 = st.columns([2, 1, 1])
    c7.markdown("#### (=) Receita Líquida Real")
    c8.markdown(f"#### {f_br(rl_mes)}")
    c9.markdown(f"#### {f_br(rl_90)}")
    
    st.markdown("---")
    st.subheader("II. Motores de Custo Variável (O Chão de Fábrica)")
    
    ca, cb, cc = st.columns([2, 1, 1])
    ca.markdown("**4. (-) Custo de Mercadorias Vendidas (CMV FIFO Real)**")
    cb.metric("Mês Atual", f_br(cv_mes), delta="Saída", delta_color="inverse")
    cc.metric("Média Trimestral", f_br(cv_90), delta="Base", delta_color="off")
    
    c_c1, c_c2, c_c3 = st.columns([2, 1, 1])
    c_c1.markdown("**5. (-) Despesas Comerciais Variáveis** *(Comissões & Logística/Fretes)*")
    c_c2.metric(" ", f_br(frete_mes + comi_mes), label_visibility="collapsed")
    c_c3.metric(" ", f_br(frete_90 + comi_90), label_visibility="collapsed")
    
    c_a1, c_a2, c_a3 = st.columns([2, 1, 1])
    c_a1.markdown("**5.1 (-) Contratos Comerciais & Rebates (Acordos de Rede - 2.2.2)**")
    c_a2.metric(" ", f_br(acordos_mes), label_visibility="collapsed")
    c_a3.metric(" ", f_br(acordos_90), label_visibility="collapsed")
    
    c_d1, c_d2, c_d3 = st.columns([2, 1, 1])
    c_d1.markdown("**5.2 (-) Taxas de Descarga (CD/Redes)**")
    c_d2.metric(" ", f_br(descarga_mes), label_visibility="collapsed")
    c_d3.metric(" ", f_br(descarga_90), label_visibility="collapsed")
    
    c_deg1, c_deg2, c_deg3 = st.columns([2, 1, 1])
    c_deg1.markdown("**5.3 (-) Degustações e Amostras (Ações Comerciais - 2.2.1)**")
    c_deg2.metric(" ", f_br(degust_mes), label_visibility="collapsed")
    c_deg3.metric(" ", f_br(degust_90), label_visibility="collapsed")
    
    c_prm1, c_prm2, c_prm3 = st.columns([2, 1, 1])
    c_prm1.markdown("**5.4 (-) Custos de Promotores de Vendas (Serviços - 2.2.4)**")
    c_prm2.metric(" ", f_br(promotores_mes), label_visibility="collapsed")
    c_prm3.metric(" ", f_br(promotores_90), label_visibility="collapsed")
    
    cd, ce, cf = st.columns([2, 1, 1])
    cd.markdown(f"#### (=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA   🛡️ `{mc_perc:.1f}%`")
    ce.markdown(f"#### {f_br(mc_mes)}")
    cf.markdown(f"#### {f_br(mc_90)}")
    
    st.markdown("---")
    st.subheader("III. O Peso Existencial (Despesas Engessadas)")
    
    cg, ch, ci = st.columns([2, 1, 1])
    cg.markdown("**6. (-) Desp. Fixas Totais (Vencimento no Mês Seguinte)**")
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
    ct3.markdown(f"### {f_br(lucro_90)}")

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
