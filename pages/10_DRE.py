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
    margin-bottom: 10px !important;
    color: #1e293b !important;
}
.dre-wrapper {
    max-width: 960px;
    margin: 0 left;
}
.dre-sec-header {
    background-color: #f1f5f9;
    border-left: 4px solid #1e293b;
    padding: 8px 12px;
    font-weight: 700;
    font-size: 1.1rem;
    color: #0f172a;
    margin-top: 18px;
    margin-bottom: 10px;
    border-radius: 0 6px 6px 0;
}
.dre-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.95rem;
    color: #334155;
}
.dre-row:hover {
    background-color: #f8fafc;
}
.dre-row-sub {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px 6px 28px;
    border-bottom: 1px dashed #f1f5f9;
    font-size: 0.90rem;
    color: #475569;
    background-color: #fafafa;
}
.dre-row-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    background-color: #f1f5f9;
    border-top: 2px solid #cbd5e1;
    border-bottom: 2px solid #0f172a;
    font-weight: 700;
    font-size: 1.05rem;
    color: #0f172a;
    margin-top: 4px;
    margin-bottom: 4px;
    border-radius: 4px;
}
.dre-row-subtotal {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 12px;
    background-color: #f8fafc;
    border-top: 1px solid #cbd5e1;
    font-weight: 700;
    font-size: 1.00rem;
    color: #1e293b;
}
.dre-label {
    flex: 1;
}
.dre-tag {
    display: inline-block;
    background-color: #e2e8f0;
    color: #334155;
    font-size: 0.8rem;
    padding: 2px 7px;
    border-radius: 4px;
    margin-left: 8px;
    font-weight: 500;
}
.dre-val {
    font-weight: 600;
    font-size: 0.98rem;
    color: #0f172a;
    text-align: right;
    width: 150px;
    margin-left: 20px;
}
.dre-val-total {
    font-weight: 800;
    font-size: 1.08rem;
    color: #0f172a;
    text-align: right;
    width: 150px;
    margin-left: 20px;
}
.stExpander {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    margin-top: 6px !important;
    margin-bottom: 12px !important;
    max-width: 960px !important;
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

if "sel_mes_ano_tab1" not in st.session_state:
    st.session_state["sel_mes_ano_tab1"] = default_label
if "sel_mes_ano_tab2" not in st.session_state:
    st.session_state["sel_mes_ano_tab2"] = default_label

def sync_tab1():
    st.session_state["sel_mes_ano_tab2"] = st.session_state["sel_mes_ano_tab1"]

def sync_tab2():
    st.session_state["sel_mes_ano_tab1"] = st.session_state["sel_mes_ano_tab2"]

sel_mes_ano = st.session_state.get("sel_mes_ano_tab1", default_label)

nome_mes, ano_sel = sel_mes_ano.split("/")
ano_sel = int(ano_sel)
mes_sel = meses_nomes.index(nome_mes) + 1

p_mes = pd.Period(f"{ano_sel}-{mes_sel:02d}", freq='M')

dt_vd_devol_inicio_str = p_mes.start_time.strftime("%Y-%m-%d")
dt_vd_devol_fim_str = p_mes.end_time.strftime("%Y-%m-%d")

dt_cap_inicio_str = p_mes.start_time.strftime("%Y-%m-%d")
dt_cap_fim_str = (p_mes + 1).end_time.strftime("%Y-%m-%d")

# --- QUERY DAS VENDAS ---
df_vd = fetch_all("""
    SELECT valor_total, quantidade, custo_frete_rateado, comissao_valor, custo_acordos_rede, custo_descarga, custo_cmv_real, data, tipo_documento
    FROM vendas
    WHERE status = 'FATURADO' AND data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if not df_vd.empty:
    df_vd['data'] = pd.to_datetime(df_vd['data'], errors='coerce')
    df_vd['sale_month'] = df_vd['data'].dt.to_period('M')
else:
    df_vd = pd.DataFrame(columns=['valor_total', 'quantidade', 'custo_frete_rateado', 'comissao_valor', 'custo_acordos_rede', 'custo_descarga', 'custo_cmv_real', 'sale_month', 'tipo_documento'])

# --- QUERY DE DEVOLUÇÕES ---
df_devol = fetch_all("""
    SELECT valor_financeiro_abatido, data FROM devolucoes WHERE data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if not df_devol.empty:
    df_devol['data'] = pd.to_datetime(df_devol['data'], errors='coerce')
    df_devol['devol_month'] = df_devol['data'].dt.to_period('M')
else:
    df_devol = pd.DataFrame(columns=['valor_financeiro_abatido', 'devol_month'])

# --- QUERY DE COMPRAS DE MATÉRIA PRIMA ---
df_mp = fetch_all("""
    SELECT data, peso_kg, valor_total FROM compras_materia_prima WHERE data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if not df_mp.empty:
    df_mp['data'] = pd.to_datetime(df_mp['data'], errors='coerce')
    df_mp['mp_month'] = df_mp['data'].dt.to_period('M')
else:
    df_mp = pd.DataFrame(columns=['data', 'peso_kg', 'valor_total', 'mp_month'])

# --- QUERY DO CONTAS A PAGAR ---
df_cap = fetch_all("""
    SELECT c.valor, c.data_vencimento, c.descricao, pc.codigo, pc.categoria as pc_cat, pc.nome as pc_nome
    FROM contas_a_pagar c
    JOIN planos_de_contas pc ON c.plano_conta_id = pc.id
    WHERE c.data_vencimento >= ? AND c.data_vencimento <= ?
""", (dt_cap_inicio_str, dt_cap_fim_str))

if not df_cap.empty:
    df_cap['data_vencimento'] = pd.to_datetime(df_cap['data_vencimento'], errors='coerce')
    df_cap['venc_month'] = df_cap['data_vencimento'].dt.to_period('M')
    
    is_fixed = df_cap['codigo'].str.startswith(('2.3.', '3.1.'), na=False) & ~df_cap['codigo'].str.startswith('2.3.6', na=False)
    
    df_cap['ref_month'] = df_cap['venc_month']
    df_cap.loc[is_fixed, 'ref_month'] = df_cap.loc[is_fixed, 'venc_month'] - 1
else:
    df_cap = pd.DataFrame(columns=['valor', 'descricao', 'codigo', 'pc_cat', 'pc_nome', 'ref_month'])

# --- FILTRAGEM POR MÊS ---
df_vd_mes = df_vd[df_vd['sale_month'] == p_mes]
df_devol_mes = df_devol[df_devol['devol_month'] == p_mes]
df_mp_mes = df_mp[df_mp['mp_month'] == p_mes]
df_cap_mes = df_cap[df_cap['ref_month'] == p_mes]

# --- DESDOBRAMENTO DE VENDAS: NF vs DAV ---
is_nf = df_vd_mes['tipo_documento'].astype(str).str.contains('NF|Nota', case=False, na=False) if not df_vd_mes.empty else pd.Series([], dtype=bool)
df_nf_mes = df_vd_mes[is_nf] if not df_vd_mes.empty else pd.DataFrame()
df_dav_mes = df_vd_mes[~is_nf] if not df_vd_mes.empty else pd.DataFrame()

nf_val_mes = float(df_nf_mes['valor_total'].sum()) if not df_nf_mes.empty else 0.0
nf_kg_mes = float(df_nf_mes['quantidade'].sum()) if not df_nf_mes.empty else 0.0
nf_pm_mes = nf_val_mes / nf_kg_mes if nf_kg_mes > 0 else 0.0

dav_val_mes = float(df_dav_mes['valor_total'].sum()) if not df_dav_mes.empty else 0.0
dav_kg_mes = float(df_dav_mes['quantidade'].sum()) if not df_dav_mes.empty else 0.0
dav_pm_mes = dav_val_mes / dav_kg_mes if dav_kg_mes > 0 else 0.0

rb_mes = nf_val_mes + dav_val_mes
rb_kg_mes = nf_kg_mes + dav_kg_mes
rb_pm_mes = rb_mes / rb_kg_mes if rb_kg_mes > 0 else 0.0

# Nível 2: Deduções
dev_mes = float(df_devol_mes['valor_financeiro_abatido'].sum()) if not df_devol_mes.empty else 0.0
imp_venda_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.3', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

rl_mes = rb_mes - dev_mes - imp_venda_mes
rl_kg_mes = rb_kg_mes
rl_pm_mes = rl_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0

# Nível 3: CMV Remodelado
mp_val_mes = float(df_mp_mes['valor_total'].sum()) if not df_mp_mes.empty else 0.0
mp_kg_mes = float(df_mp_mes['peso_kg'].sum()) if not df_mp_mes.empty else 0.0

if mp_val_mes == 0 and not df_cap_mes.empty:
    mp_val_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.1', na=False)]['valor'].sum())

mp_pm_mes = mp_val_mes / mp_kg_mes if mp_kg_mes > 0 else 0.0

emb_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.2', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
outros_fab_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.', na=False) & ~df_cap_mes['codigo'].str.startswith(('2.1.1', '2.1.2', '2.1.3'), na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

cmv_tot_mes = mp_val_mes + emb_mes + outros_fab_mes

# Nível 4: Despesas Comerciais Variáveis (Separados: Comissões e Fretes)
comi_mes = float(df_vd_mes['comissao_valor'].sum()) if not df_vd_mes.empty else 0.0
frete_mes = float(df_vd_mes['custo_frete_rateado'].sum()) if not df_vd_mes.empty else 0.0
acordos_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.2', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
descarga_mes = float(df_vd_mes['custo_descarga'].sum()) if not df_vd_mes.empty else 0.0
degust_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.1', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
promotores_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.4', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

desp_com_mes = comi_mes + frete_mes + acordos_mes + descarga_mes + degust_mes + promotores_mes

# Margem de Contribuição Líquida
mc_mes = rl_mes - cmv_tot_mes - desp_com_mes
mc_perc = (mc_mes / rl_mes * 100) if rl_mes > 0 else 0.0
mc_kg_mes = mc_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0

# Despesas Fixas
df_mes_val = float(df_cap_mes[df_cap_mes['codigo'].str.startswith(('2.3.', '3.1.'), na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
pro_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('3.1.4', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

# EBITDA
ebitda_mes = mc_mes - df_mes_val
ebitda_perc = (ebitda_mes / rl_mes * 100) if rl_mes > 0 else 0.0

# Fatores Não-Operacionais e Financeiros
depr_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('Depreciação', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
imp_lucro_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('Impostos sobre Lucro|IRPJ|CSLL', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
finan_mes = float(df_cap_mes[(df_cap_mes['codigo'] == '3.2.1') | (df_cap_mes['pc_nome'].str.contains('Financiamento|Empréstimo|Juros|Despesas Financeiras', case=False, na=False))]['valor'].sum()) if not df_cap_mes.empty else 0.0
jcp_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('JCP|Juros sobre Capital Próprio', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

# Lucro Líquido
lucro_mes = ebitda_mes - depr_mes - imp_lucro_mes - finan_mes - jcp_mes
lucro_perc = (lucro_mes / rl_mes * 100) if rl_mes > 0 else 0.0

div_mes = float(df_cap_mes[df_cap_mes['pc_nome'].str.contains('Dividendos|Distribuição de Lucro', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
retido_mes = lucro_mes - div_mes

# CAPEX / Maquinário e Geração Líquida de Caixa
capex_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith(('1.2.', '4.1.'), na=False) | df_cap_mes['pc_nome'].str.contains('Máquina|Equipamento|Imobilizado|CAPEX|Maquinário', case=False, na=False) | df_cap_mes['descricao'].str.contains('Máquina|Equipamento|Maquinário', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
caixa_livre_mes = lucro_mes + depr_mes - capex_mes

# Ponto de Equilíbrio
break_even = (df_mes_val / (mc_perc / 100)) if mc_perc > 0 else 0.0

# --- FUNÇÃO AUXILIAR DE DRILL-DOWN PELO PLANO DE CONTAS ---
def render_drilldown(titulo, prefixos_codigo=None, nomes_filtro=None):
    df_m = df_cap_mes.copy()
    if df_m.empty:
        st.caption("Sem lançamentos no período.")
        return
        
    cond_m = pd.Series([False] * len(df_m), index=df_m.index)
    if prefixos_codigo:
        for pfix in prefixos_codigo:
            cond_m |= df_m['codigo'].str.startswith(pfix, na=False)
            
    if nomes_filtro:
        for nfilt in nomes_filtro:
            cond_m |= df_m['pc_nome'].str.contains(nfilt, case=False, na=False)
            
    res_m = df_m[cond_m].groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index()
    if res_m.empty:
        st.info("Nenhum lançamento no Plano de Contas para este grupo no período.")
        return
        
    res_m = res_m.sort_values(by='codigo')
    res_m.columns = ['Código', 'Plano de Contas', 'Valor (R$)']
    res_m['Valor (R$)'] = res_m['Valor (R$)'].apply(f_br)
    
    st.dataframe(res_m, hide_index=True, use_container_width=True)

# -------- RENDERIZAÇÃO VISUAL ---------

tab1, tab2 = st.tabs(["DRE", "Ponto de Equilíbrio (Break-Even)"])

with tab1:
    st.markdown("<div class='dre-wrapper'>", unsafe_allow_html=True)
    
    col_hdr_title, col_hdr_sel = st.columns([2.2, 1.2])
    with col_hdr_title:
        st.markdown("<div class='dre-sec-header'>I. Faturamento Bruto</div>", unsafe_allow_html=True)
    with col_hdr_sel:
        st.selectbox(
            "Selecione o Mês/Ano:",
            opcoes_meses,
            index=opcoes_meses.index(sel_mes_ano) if sel_mes_ano in opcoes_meses else default_idx,
            key="sel_mes_ano_tab1",
            on_change=sync_tab1
        )
    
    # -------------------------------------------------------------------------
    # I. RECEITA E DEDUÇÕES (Tabela Financeira Executiva Limpa)
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row-subtotal'>
        <div class='dre-label'>
            <b>1. Receita Operacional Bruta ({sel_mes_ano})</b>
            <span class='dre-tag'>Volume: {f_kg(rb_kg_mes)}</span>
            <span class='dre-tag'>Preço Médio: {f_pm(rb_pm_mes)}</span>
        </div>
        <div class='dre-val-total'>{f_br(rb_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'>
            <b>1.1 Vendas por Nota Fiscal (NF)</b>
            <span class='dre-tag'>Volume: {f_kg(nf_kg_mes)}</span>
            <span class='dre-tag'>Preço Médio: {f_pm(nf_pm_mes)}</span>
        </div>
        <div class='dre-val'>{f_br(nf_val_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'>
            <b>1.2 Vendas por DAV (Pedido de Venda)</b>
            <span class='dre-tag'>Volume: {f_kg(dav_kg_mes)}</span>
            <span class='dre-tag'>Preço Médio: {f_pm(dav_pm_mes)}</span>
        </div>
        <div class='dre-val'>{f_br(dav_val_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>2. (-) Devoluções / Abatimentos</b></div>
        <div class='dre-val'>{f_br(dev_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>3. (-) Impostos sobre Venda (Vencimento no Mês - 2.1.3)</b></div>
        <div class='dre-val'>{f_br(imp_venda_mes)}</div>
    </div>
    <div class='dre-row-total'>
        <div class='dre-label'>
            (=) RECEITA LÍQUIDA REAL
            <span class='dre-tag'>Volume Líquido: {f_kg(rl_kg_mes)}</span>
            <span class='dre-tag'>Preço Médio Líquido: {f_pm(rl_pm_mes)}</span>
        </div>
        <div class='dre-val-total'>{f_br(rl_mes)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Detalhar Deduções e Impostos no Plano de Contas"):
        render_drilldown("Deduções e Impostos", prefixos_codigo=['2.1.3'])
        
    st.markdown("<div class='dre-sec-header'>II. Motores de Custo Variável & CMV Fabril</div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # II. CMV FABRIL REMODELADO & CUSTOS VARIÁVEIS
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row-subtotal'>
        <div class='dre-label'><b>4. Custo Total de Fabricação / CMV</b></div>
        <div class='dre-val-total'>{f_br(cmv_tot_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'>
            <b>4.1 (-) Matéria-Prima Comprada (Alho in Natura)</b>
            <span class='dre-tag'>Compras: {f_kg(mp_kg_mes)}</span>
            <span class='dre-tag'>Custo Médio: {f_pm(mp_pm_mes)}</span>
        </div>
        <div class='dre-val'>{f_br(mp_val_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>4.2 (-) Embalagens & Insumos de Acondicionamento (2.1.2)</b></div>
        <div class='dre-val'>{f_br(emb_mes)}</div>
    </div>
    """ + (f"""
    <div class='dre-row-sub'>
        <div class='dre-label'><b>4.3 (-) Outros Custos Fabris Diretos</b></div>
        <div class='dre-val'>{f_br(outros_fab_mes)}</div>
    </div>
    """ if outros_fab_mes > 0 else "") + f"""
    
    <div class='dre-row-subtotal' style='margin-top: 10px;'>
        <div class='dre-label'><b>5. Despesas Comerciais Variáveis</b></div>
        <div class='dre-val-total'>{f_br(desp_com_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>5.1 (-) Comissões de Vendas</b></div>
        <div class='dre-val'>{f_br(comi_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>5.2 (-) Fretes de Entrega (Logística de Saída)</b></div>
        <div class='dre-val'>{f_br(frete_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>5.3 (-) Acordos de Rede & Rebates Comerciais (2.2.2)</b></div>
        <div class='dre-val'>{f_br(acordos_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>5.4 (-) Taxas de Descarga (CD/Redes)</b></div>
        <div class='dre-val'>{f_br(descarga_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>5.5 (-) Degustações e Amostras (2.2.1)</b></div>
        <div class='dre-val'>{f_br(degust_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>5.6 (-) Serviços de Promotores de Vendas (2.2.4)</b></div>
        <div class='dre-val'>{f_br(promotores_mes)}</div>
    </div>
    
    <div class='dre-row-total'>
        <div class='dre-label'>
            (=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA
            <span class='dre-tag'>Margem: {mc_perc:.1f}%</span>
            <span class='dre-tag'>Margem/Kg: {f_pm(mc_kg_mes)}</span>
        </div>
        <div class='dre-val-total'>{f_br(mc_mes)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Detalhar Custos e Despesas Variáveis no Plano de Contas"):
        render_drilldown("Custos Variáveis e Comerciais", prefixos_codigo=['2.1.', '2.2.'])
        
    st.markdown("<div class='dre-sec-header'>III. O Peso Existencial (Despesas Engessadas)</div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # III. DESPESAS FIXAS
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row'>
        <div class='dre-label'><b>6. (-) Desp. Fixas Totais (Vencimento no Mês Seguinte)</b></div>
        <div class='dre-val'>{f_br(df_mes_val)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><i>Dessa Fila: (-) Pró-Labore (Salário Sócio)</i></div>
        <div class='dre-val'><i>{f_br(pro_mes)}</i></div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Detalhar Despesas Fixas no Plano de Contas"):
        render_drilldown("Despesas Fixas", prefixos_codigo=['2.3.', '3.1.'])
        
    st.markdown("<div class='dre-sec-header'>IV. Resultado Operacional (EBITDA)</div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # IV. EBITDA
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row-total'>
        <div class='dre-label'>
            (=) EBITDA (Resultado Operacional)
            <span class='dre-tag'>EBITDA: {ebitda_perc:.1f}%</span>
        </div>
        <div class='dre-val-total'>{f_br(ebitda_mes)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='dre-sec-header'>V. Fatores Não-Operacionais e Financeiros</div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # V. FATORES FINANCEIROS & LUCRO LÍQUIDO
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row'>
        <div class='dre-label'><b>7. (-) Depreciação / Amortização (Gasto Não-Caixa)</b></div>
        <div class='dre-val'>{f_br(depr_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>8. (-) Impostos sobre Lucro (IRPJ/CSLL)</b></div>
        <div class='dre-val'>{f_br(imp_lucro_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>9. (-) Juros e Financiamentos</b></div>
        <div class='dre-val'>{f_br(finan_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>10. (-) JCP (Juros s/ Capital Próprio)</b></div>
        <div class='dre-val'>{f_br(jcp_mes)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Detalhar Fatores Não-Operacionais e Financeiros no Plano de Contas"):
        render_drilldown("Fatores Financeiros", prefixos_codigo=['3.2.'], nomes_filtro=['Depreciação', 'Impostos sobre Lucro', 'IRPJ', 'CSLL', 'Financiamento', 'Juros', 'JCP'])
        
    st.markdown("<div class='dre-sec-header'>VI. Lucratividade do Exercício (Competência)</div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # VI. LUCRO LÍQUIDO & DIVIDENDOS
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row-subtotal'>
        <div class='dre-label'>
            <b>11. (=) LUCRO LÍQUIDO TOTAL GERADO</b>
            <span class='dre-tag'>Lucratividade: {lucro_perc:.1f}%</span>
        </div>
        <div class='dre-val-total'>{f_br(lucro_mes)}</div>
    </div>
    <div class='dre-row-sub'>
        <div class='dre-label'><b>12. (-) Dividendos (Saque/Distribuição do Sócio)</b></div>
        <div class='dre-val'>{f_br(div_mes)}</div>
    </div>
    <div class='dre-row-total'>
        <div class='dre-label'><b>(=) LUCRO RETIDO (PATRIMÔNIO CNPJ)</b></div>
        <div class='dre-val-total'>{f_br(retido_mes)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='dre-sec-header'>VII. Geração Líquida de Caixa & Investimentos (CAPEX / Maquinário)</div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # VII. GERAÇÃO LÍQUIDA DE CAIXA & MAQUINÁRIO (CAPEX)
    # -------------------------------------------------------------------------
    st.markdown(f"""
    <div class='dre-row'>
        <div class='dre-label'>Lucro Líquido Contábil (Competência)</div>
        <div class='dre-val'>{f_br(lucro_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>(+) Reversão de Depreciação</b> *(Gasto Não-Caixa)*</div>
        <div class='dre-val'>+ {f_br(depr_mes)}</div>
    </div>
    <div class='dre-row'>
        <div class='dre-label'><b>(-) Investimentos em Maquinário & Equipamentos</b> *(CAPEX Pago no Mês)*</div>
        <div class='dre-val'>- {f_br(capex_mes)}</div>
    </div>
    <div class='dre-row-total'>
        <div class='dre-label'><b>(=) RESULTADO LÍQUIDO DE CAIXA DA OPERAÇÃO</b></div>
        <div class='dre-val-total'>{f_br(caixa_livre_mes)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Detalhar Compras de Maquinário / CAPEX no Plano de Contas"):
        render_drilldown("Investimentos e Maquinário", prefixos_codigo=['1.2.', '4.1.'], nomes_filtro=['Máquina', 'Equipamento', 'Imobilizado', 'CAPEX', 'Maquinário'])
        
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    col_b_title, col_b_sel = st.columns([2.2, 1.2])
    with col_b_title:
        st.subheader("Ponto de Sobrevivência (Break-Even)")
    with col_b_sel:
        st.selectbox(
            "Selecione o Mês/Ano:",
            opcoes_meses,
            index=opcoes_meses.index(sel_mes_ano) if sel_mes_ano in opcoes_meses else default_idx,
            key="sel_mes_ano_tab2",
            on_change=sync_tab2
        )
        
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
