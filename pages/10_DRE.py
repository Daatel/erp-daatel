import streamlit as st
import pandas as pd
import calendar
from datetime import timedelta, date
from database import fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="DRE Fabril", page_icon="🏛️", layout="wide")
carregar_estilo()

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
h1 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    margin-top: -15px !important;
    margin-bottom: 0px !important;
    color: #1e293b !important;
}
.stExpander {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    margin-top: 6px !important;
    margin-bottom: 6px !important;
}
</style>
<h1>Demonstrativo do Resultado do Exercício (DRE)</h1>
""", unsafe_allow_html=True)

def f_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_kg(valor):
    return f"{valor:,.1f} Kg".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pm(valor):
    return f"R$ {valor:,.2f}/Kg".replace(",", "X").replace(".", ",").replace("X", ".")

# 1. Filtro de Calendário no Topo
hoje = date.today()
meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

opcoes_meses = []
for ano in [hoje.year - 1, hoje.year, hoje.year + 1]:
    for m in range(1, 13):
        opcoes_meses.append(f"{meses_nomes[m-1]}/{ano}")

default_label = f"{meses_nomes[hoje.month-1]}/{hoje.year}"
default_idx = opcoes_meses.index(default_label) if default_label in opcoes_meses else len(opcoes_meses) // 2

# Sync states for DRE tabs selectbox
if "sel_mes_ano_tab1" not in st.session_state:
    st.session_state["sel_mes_ano_tab1"] = default_label
if "sel_mes_ano_tab2" not in st.session_state:
    st.session_state["sel_mes_ano_tab2"] = default_label

def sync_tab1():
    st.session_state["sel_mes_ano_tab2"] = st.session_state["sel_mes_ano_tab1"]

def sync_tab2():
    st.session_state["sel_mes_ano_tab1"] = st.session_state["sel_mes_ano_tab2"]

# Determine current active selection
sel_mes_ano = st.session_state.get("sel_mes_ano_tab1", default_label)

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

# --- QUERY DE COMPRAS DE MATÉRIA PRIMA (para M-2, M-1, M) ---
df_mp = fetch_all("""
    SELECT data, peso_kg, valor_total FROM compras_materia_prima WHERE data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if not df_mp.empty:
    df_mp['data'] = pd.to_datetime(df_mp['data'], errors='coerce')
    df_mp['mp_month'] = df_mp['data'].dt.to_period('M')
else:
    df_mp = pd.DataFrame(columns=['data', 'peso_kg', 'valor_total', 'mp_month'])

# --- QUERY DO CONTAS A PAGAR (para M-2, M-1, M, M+1) ---
df_cap = fetch_all("""
    SELECT c.valor, c.data_vencimento, c.descricao, pc.codigo, pc.categoria as pc_cat, pc.nome as pc_nome
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
    df_cap.loc[is_fixed, 'ref_month'] = df_cap.loc[is_fixed, 'venc_month'] - 1
else:
    df_cap = pd.DataFrame(columns=['valor', 'descricao', 'codigo', 'pc_cat', 'pc_nome', 'ref_month'])

# --- FILTRAGEM POR MÊS E 90 DIAS ---
df_vd_mes = df_vd[df_vd['sale_month'] == p_mes]
df_vd_90 = df_vd[df_vd['sale_month'].isin(p_90)]

df_devol_mes = df_devol[df_devol['devol_month'] == p_mes]
df_devol_90 = df_devol[df_devol['devol_month'].isin(p_90)]

df_mp_mes = df_mp[df_mp['mp_month'] == p_mes]
df_mp_90 = df_mp[df_mp['mp_month'].isin(p_90)]

df_cap_mes = df_cap[df_cap['ref_month'] == p_mes]
df_cap_90 = df_cap[df_cap['ref_month'].isin(p_90)]

# --- CALCULADORA CONTÁBIL (REGIME DE COMPETÊNCIA + INDICADORES POR KG) ---

# Nível 1: Receita Operacional Bruta
rb_mes = float(df_vd_mes['valor_total'].sum()) if not df_vd_mes.empty else 0.0
rb_90 = float(df_vd_90['valor_total'].sum() / 3) if not df_vd_90.empty else 0.0

rb_kg_mes = float(df_vd_mes['quantidade'].sum()) if not df_vd_mes.empty else 0.0
rb_kg_90 = float(df_vd_90['quantidade'].sum() / 3) if not df_vd_90.empty else 0.0

rb_pm_mes = rb_mes / rb_kg_mes if rb_kg_mes > 0 else 0.0
rb_pm_90 = rb_90 / rb_kg_90 if rb_kg_90 > 0 else 0.0

# Nível 2: Deduções (Devoluções e Impostos sobre Venda)
dev_mes = float(df_devol_mes['valor_financeiro_abatido'].sum()) if not df_devol_mes.empty else 0.0
dev_90 = float(df_devol_90['valor_financeiro_abatido'].sum() / 3) if not df_devol_90.empty else 0.0

imp_venda_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.3', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
imp_venda_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.1.3', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

rl_mes = rb_mes - dev_mes - imp_venda_mes
rl_90 = rb_90 - dev_90 - imp_venda_90

rl_kg_mes = rb_kg_mes
rl_kg_90 = rb_kg_90

rl_pm_mes = rl_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0
rl_pm_90 = rl_90 / rl_kg_90 if rl_kg_90 > 0 else 0.0

# Nível 3: CMV Remodelado (Opção B Fabril: Matéria-Prima em Kg & R$ + Embalagens + Insumos)
mp_val_mes = float(df_mp_mes['valor_total'].sum()) if not df_mp_mes.empty else 0.0
mp_kg_mes = float(df_mp_mes['peso_kg'].sum()) if not df_mp_mes.empty else 0.0

if mp_val_mes == 0 and not df_cap_mes.empty:
    mp_val_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.1', na=False)]['valor'].sum())

mp_val_90 = float(df_mp_90['valor_total'].sum() / 3) if not df_mp_90.empty else 0.0
mp_kg_90 = float(df_mp_90['peso_kg'].sum() / 3) if not df_mp_90.empty else 0.0

if mp_val_90 == 0 and not df_cap_90.empty:
    mp_val_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.1.1', na=False)]['valor'].sum() / 3)

mp_pm_mes = mp_val_mes / mp_kg_mes if mp_kg_mes > 0 else 0.0
mp_pm_90 = mp_val_90 / mp_kg_90 if mp_kg_90 > 0 else 0.0

emb_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.2', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
emb_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.1.2', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

outros_fab_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.', na=False) & ~df_cap_mes['codigo'].str.startswith(('2.1.1', '2.1.2', '2.1.3'), na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
outros_fab_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('2.1.', na=False) & ~df_cap_90['codigo'].str.startswith(('2.1.1', '2.1.2', '2.1.3'), na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

cmv_tot_mes = mp_val_mes + emb_mes + outros_fab_mes
cmv_tot_90 = mp_val_90 + emb_90 + outros_fab_90

# Nível 4: Despesas Comerciais Variáveis
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

# Margem de Contribuição Líquida
mc_mes = rl_mes - cmv_tot_mes - desp_com_mes
mc_90 = rl_90 - cmv_tot_90 - desp_com_90
mc_perc = (mc_mes / rl_mes * 100) if rl_mes > 0 else 0.0
mc_kg_mes = mc_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0
mc_kg_90 = mc_90 / rl_kg_90 if rl_kg_90 > 0 else 0.0

# Despesas Fixas (plano de contas 2.3 e 3.1 com vencimento em M+1)
df_mes_val = float(df_cap_mes[df_cap_mes['codigo'].str.startswith(('2.3.', '3.1.'), na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
df_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith(('2.3.', '3.1.'), na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

pro_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('3.1.4', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
pro_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith('3.1.4', na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

# Resultado Operacional (EBITDA)
ebitda_mes = mc_mes - df_mes_val
ebitda_90 = mc_90 - df_90
ebitda_perc = (ebitda_mes / rl_mes * 100) if rl_mes > 0 else 0.0

# Fatores Não-Operacionais e Financeiros
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

# CAPEX / Maquinário e Geração Líquida de Caixa
capex_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith(('1.2.', '4.1.'), na=False) | df_cap_mes['pc_nome'].str.contains('Máquina|Equipamento|Imobilizado|CAPEX|Maquinário', case=False, na=False) | df_cap_mes['descricao'].str.contains('Máquina|Equipamento|Maquinário', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
capex_90 = float(df_cap_90[df_cap_90['codigo'].str.startswith(('1.2.', '4.1.'), na=False) | df_cap_90['pc_nome'].str.contains('Máquina|Equipamento|Imobilizado|CAPEX|Maquinário', case=False, na=False) | df_cap_90['descricao'].str.contains('Máquina|Equipamento|Maquinário', case=False, na=False)]['valor'].sum() / 3) if not df_cap_90.empty else 0.0

caixa_livre_mes = lucro_mes + depr_mes - capex_mes
caixa_livre_90 = lucro_90 + depr_90 - capex_90

# Ponto de Equilíbrio
break_even = (df_mes_val / (mc_perc / 100)) if mc_perc > 0 else 0.0

# --- FUNÇÃO AUXILIAR DE DRILL-DOWN PELO PLANO DE CONTAS ---
def render_drilldown(titulo, prefixos_codigo=None, nomes_filtro=None, is_negativo=True):
    df_m = df_cap_mes.copy()
    df_q = df_cap_90.copy()
    
    if df_m.empty:
        st.caption("Sem lançamentos no período.")
        return
        
    cond_m = pd.Series([False] * len(df_m), index=df_m.index)
    cond_q = pd.Series([False] * len(df_q), index=df_q.index)
    
    if prefixos_codigo:
        for pfix in prefixos_codigo:
            cond_m |= df_m['codigo'].str.startswith(pfix, na=False)
            cond_q |= df_q['codigo'].str.startswith(pfix, na=False)
            
    if nomes_filtro:
        for nfilt in nomes_filtro:
            cond_m |= df_m['pc_nome'].str.contains(nfilt, case=False, na=False)
            cond_q |= df_q['pc_nome'].str.contains(nfilt, case=False, na=False)
            
    res_m = df_m[cond_m].groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index()
    res_q = df_q[cond_q].groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index()
    
    if res_m.empty and res_q.empty:
        st.info("Nenhum lançamento no Plano de Contas para este grupo no período.")
        return
        
    merged = pd.merge(res_m, res_q, on=['codigo', 'pc_nome'], how='outer', suffixes=('_mes', '_90')).fillna(0.0)
    merged['valor_90'] = merged['valor_90'] / 3.0
    merged = merged.sort_values(by='codigo')
    
    merged.columns = ['Código', 'Plano de Contas', 'Mês Atual (R$)', 'Média 90d (R$)']
    merged['Mês Atual (R$)'] = merged['Mês Atual (R$)'].apply(f_br)
    merged['Média 90d (R$)'] = merged['Média 90d (R$)'].apply(f_br)
    
    st.dataframe(merged, hide_index=True, use_container_width=True)

# -------- RENDERIZAÇÃO VISUAL ---------

tab1, tab2 = st.tabs(["DRE Tático de Fábrica", "Ponto de Equilíbrio (Break-Even)"])

with tab1:
    st.selectbox(
        "Selecione o Mês/Ano de Referência do DRE:",
        opcoes_meses,
        index=opcoes_meses.index(sel_mes_ano) if sel_mes_ano in opcoes_meses else default_idx,
        key="sel_mes_ano_tab1",
        on_change=sync_tab1
    )
    
    # -------------------------------------------------------------------------
    # I. RECEITA E DEDUÇÕES
    # -------------------------------------------------------------------------
    st.subheader("I. Faturamento Bruto & Volume de Vendas")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown(f"**1. Receita Operacional Bruta ({sel_mes_ano})**\n> 📦 Volume: **{f_kg(rb_kg_mes)}** | Preço Médio: **{f_pm(rb_pm_mes)}**")
    c2.metric("Mês Atual", f_br(rb_mes))
    c3.metric("Média 90 Dias", f_br(rb_90), delta=f"{(rb_mes - rb_90)/rb_90*100:.1f}%" if rb_90>0 else "0%")
    
    c4, c5, c6 = st.columns([2, 1, 1])
    c4.markdown("**2. (-) Devoluções / Abatimentos**")
    c5.metric(" ", f_br(dev_mes), label_visibility="collapsed")
    c6.metric(" ", f_br(dev_90), label_visibility="collapsed")
    
    c_imp1, c_imp2, c_imp3 = st.columns([2, 1, 1])
    c_imp1.markdown("**3. (-) Impostos sobre Venda (Vencimento no Mês - 2.1.3)**")
    c_imp2.metric(" ", f_br(imp_venda_mes), label_visibility="collapsed")
    c_imp3.metric(" ", f_br(imp_venda_90), label_visibility="collapsed")
    
    c7, c8, c9 = st.columns([2, 1, 1])
    c7.markdown(f"#### (=) RECEITA LÍQUIDA REAL\n> 📦 Volume Líquido: **{f_kg(rl_kg_mes)}** | Preço Médio Líquido: **{f_pm(rl_pm_mes)}**")
    c8.markdown(f"#### {f_br(rl_mes)}")
    c9.markdown(f"#### {f_br(rl_90)}")
    
    with st.expander("🔍 Detalhar Deduções e Impostos no Plano de Contas"):
        render_drilldown("Deduções e Impostos", prefixos_codigo=['2.1.3'])
        
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # II. CMV FABRIL REMODELADO & CUSTOS VARIÁVEIS
    # -------------------------------------------------------------------------
    st.subheader("II. Motores de Custo Variável & CMV Fabril")
    
    ca, cb, cc = st.columns([2, 1, 1])
    ca.markdown(f"**4.1 (-) Matéria-Prima Comprada (Alho in Natura / Insumo Principal)**\n> 🧄 Compras no Mês: **{f_kg(mp_kg_mes)}** | Custo Médio: **{f_pm(mp_pm_mes)}**")
    cb.metric("Mês Atual", f_br(mp_val_mes), delta="Saída Insumos", delta_color="inverse")
    cc.metric("Média Trimestral", f_br(mp_val_90), delta=f"Custo 90d: {f_pm(mp_pm_90)}", delta_color="off")
    
    c_e1, c_e2, c_e3 = st.columns([2, 1, 1])
    c_e1.markdown("**4.2 (-) Embalagens & Insumos de Acondicionamento (2.1.2)**")
    c_e2.metric(" ", f_br(emb_mes), label_visibility="collapsed")
    c_e3.metric(" ", f_br(emb_90), label_visibility="collapsed")
    
    if outros_fab_mes > 0 or outros_fab_90 > 0:
        c_o1, c_o2, c_o3 = st.columns([2, 1, 1])
        c_o1.markdown("**4.3 (-) Outros Custos Fabris Diretos**")
        c_o2.metric(" ", f_br(outros_fab_mes), label_visibility="collapsed")
        c_o3.metric(" ", f_br(outros_fab_90), label_visibility="collapsed")
        
    c_cmv_t1, c_cmv_t2, c_cmv_t3 = st.columns([2, 1, 1])
    c_cmv_t1.markdown("**(=) CUSTO TOTAL DE FABRICAÇÃO / CMV**")
    c_cmv_t2.markdown(f"**{f_br(cmv_tot_mes)}**")
    c_cmv_t3.markdown(f"**{f_br(cmv_tot_90)}**")
    
    st.markdown("#### 🚚 Despesas Comerciais Variáveis")
    
    c_c1, c_c2, c_c3 = st.columns([2, 1, 1])
    c_c1.markdown("**5.1 (-) Fretes de Entrega & Comissões de Venda**")
    c_c2.metric(" ", f_br(frete_mes + comi_mes), label_visibility="collapsed")
    c_c3.metric(" ", f_br(frete_90 + comi_90), label_visibility="collapsed")
    
    c_a1, c_a2, c_a3 = st.columns([2, 1, 1])
    c_a1.markdown("**5.2 (-) Acordos de Rede & Rebates Comerciais (2.2.2)**")
    c_a2.metric(" ", f_br(acordos_mes), label_visibility="collapsed")
    c_a3.metric(" ", f_br(acordos_90), label_visibility="collapsed")
    
    c_d1, c_d2, c_d3 = st.columns([2, 1, 1])
    c_d1.markdown("**5.3 (-) Taxas de Descarga (CD/Redes)**")
    c_d2.metric(" ", f_br(descarga_mes), label_visibility="collapsed")
    c_d3.metric(" ", f_br(descarga_90), label_visibility="collapsed")
    
    c_deg1, c_deg2, c_deg3 = st.columns([2, 1, 1])
    c_deg1.markdown("**5.4 (-) Degustações e Amostras (2.2.1)**")
    c_deg2.metric(" ", f_br(degust_mes), label_visibility="collapsed")
    c_deg3.metric(" ", f_br(degust_90), label_visibility="collapsed")
    
    c_prm1, c_prm2, c_prm3 = st.columns([2, 1, 1])
    c_prm1.markdown("**5.5 (-) Serviços de Promotores de Vendas (2.2.4)**")
    c_prm2.metric(" ", f_br(promotores_mes), label_visibility="collapsed")
    c_prm3.metric(" ", f_br(promotores_90), label_visibility="collapsed")
    
    cd, ce, cf = st.columns([2, 1, 1])
    cd.markdown(f"#### (=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA   🛡️ `{mc_perc:.1f}%` \n> 🎯 Margem por Kg: **{f_pm(mc_kg_mes)}**")
    ce.markdown(f"#### {f_br(mc_mes)}")
    cf.markdown(f"#### {f_br(mc_90)}")
    
    with st.expander("🔍 Detalhar Custos e Despesas Variáveis no Plano de Contas"):
        render_drilldown("Custos Variáveis e Comerciais", prefixos_codigo=['2.1.', '2.2.'])
        
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # III. DESPESAS FIXAS
    # -------------------------------------------------------------------------
    st.subheader("III. O Peso Existencial (Despesas Engessadas)")
    
    cg, ch, ci = st.columns([2, 1, 1])
    cg.markdown("**6. (-) Desp. Fixas Totais (Vencimento no Mês Seguinte)**")
    ch.metric("Mês Atual", f_br(df_mes_val), delta="Saída", delta_color="inverse")
    ci.metric("Média Trimestral", f_br(df_90), delta="Base", delta_color="off")
    
    c_pro1, c_pro2, c_pro3 = st.columns([2, 1, 1])
    c_pro1.markdown(">*Dessa Fila: (-) Pró-Labore (Salário Sócio)*")
    c_pro2.markdown(f">*{f_br(pro_mes)}*")
    c_pro3.markdown(f">*{f_br(pro_90)}*")
    
    with st.expander("🔍 Detalhar Despesas Fixas no Plano de Contas"):
        render_drilldown("Despesas Fixas", prefixos_codigo=['2.3.', '3.1.'])
        
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # IV. EBITDA
    # -------------------------------------------------------------------------
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
    
    # -------------------------------------------------------------------------
    # V. FATORES FINANCEIROS & LUCRO LÍQUIDO
    # -------------------------------------------------------------------------
    st.subheader("V. Fatores Não-Operacionais e Financeiros")
    
    cm1, cm2, cm3 = st.columns([2, 1, 1])
    cm1.markdown("**7. (-) Depreciação / Amortização (Não-Caixa)**")
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
    
    with st.expander("🔍 Detalhar Fatores Não-Operacionais e Financeiros no Plano de Contas"):
        render_drilldown("Fatores Financeiros", prefixos_codigo=['3.2.'], nomes_filtro=['Depreciação', 'Impostos sobre Lucro', 'IRPJ', 'CSLL', 'Financiamento', 'Juros', 'JCP'])
        
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # VI. LUCRO LÍQUIDO & DIVIDENDOS
    # -------------------------------------------------------------------------
    st.subheader("👑 VI. Lucratividade do Exercício (Competência)")
    
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
    
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # VII. NOVO BLOCO: GERAÇÃO LÍQUIDA DE CAIXA & MAQUINÁRIO (CAPEX)
    # -------------------------------------------------------------------------
    st.subheader("⚙️ VII. Geração Líquida de Caixa & Investimentos (CAPEX / Maquinário)")
    st.markdown("> **Conciliação Executiva (Bolso da Fábrica):** Ajusta o Lucro Líquido contábil pela reversão da depreciação (não-caixa) e deduce os desembolsos reais de parcelas/compras de máquinas e equipamentos no período.")
    
    cx1, cx2, cx3 = st.columns([2, 1, 1])
    cx1.markdown("Lucro Líquido Contábil (Competência)")
    cx2.markdown(f"**{f_br(lucro_mes)}**")
    cx3.markdown(f"**{f_br(lucro_90)}**")
    
    cx4, cx5, cx6 = st.columns([2, 1, 1])
    cx4.markdown("(+) Reversão de Depreciação *(Gasto Não-Caixa)*")
    cx5.markdown(f"+ {f_br(depr_mes)}")
    cx6.markdown(f"+ {f_br(depr_90)}")
    
    cx7, cx8, cx9 = st.columns([2, 1, 1])
    cx7.markdown("(-) Investimentos em Maquinário & Equipamentos *(CAPEX Pago no Mês)*")
    cx8.markdown(f"- {f_br(capex_mes)}")
    cx9.markdown(f"- {f_br(capex_90)}")
    
    cxf1, cxf2, cxf3 = st.columns([2, 1, 1])
    cxf1.markdown("### 💰 (=) RESULTADO LÍQUIDO DE CAIXA DA OPERAÇÃO")
    if caixa_livre_mes < 0:
        str_cx = f"🛑 {f_br(caixa_livre_mes)}"
    else:
        str_cx = f"🚀 {f_br(caixa_livre_mes)}"
    cxf2.markdown(f"### {str_cx}")
    cxf3.markdown(f"### {f_br(caixa_livre_90)}")
    
    with st.expander("🔍 Detalhar Compras de Maquinário / CAPEX no Plano de Contas"):
        render_drilldown("Investimentos e Maquinário", prefixos_codigo=['1.2.', '4.1.'], nomes_filtro=['Máquina', 'Equipamento', 'Imobilizado', 'CAPEX', 'Maquinário'])

with tab2:
    st.selectbox(
        "Selecione o Mês/Ano de Referência do DRE:",
        opcoes_meses,
        index=opcoes_meses.index(sel_mes_ano) if sel_mes_ano in opcoes_meses else default_idx,
        key="sel_mes_ano_tab2",
        on_change=sync_tab2
    )
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
