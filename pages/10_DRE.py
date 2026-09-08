import streamlit as st
import pandas as pd
import calendar
from datetime import timedelta, date
from database import fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="Relatório Gerencial de Caixa", page_icon="🏛️", layout="wide")
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
    border-bottom: 1px dashed #e2e8f0;
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
</style>
<h1>Relatório Gerencial de Caixa (RGC)</h1>
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

if "sel_mes_ano" not in st.session_state:
    st.session_state["sel_mes_ano"] = default_label

sel_mes_ano = st.session_state.get("sel_mes_ano", default_label)

nome_mes, ano_sel = sel_mes_ano.split("/")
ano_sel = int(ano_sel)
mes_sel = meses_nomes.index(nome_mes) + 1

p_mes = pd.Period(f"{ano_sel}-{mes_sel:02d}", freq='M')

dt_vd_devol_inicio_str = p_mes.start_time.strftime("%Y-%m-%d")
dt_vd_devol_fim_str = p_mes.end_time.strftime("%Y-%m-%d")

dt_cap_inicio_str = p_mes.start_time.strftime("%Y-%m-%d")
dt_cap_fim_str = p_mes.end_time.strftime("%Y-%m-%d")

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

# --- QUERY DO CONTAS A PAGAR (REGIME DE CAIXA - APENAS TÍTULOS EFETIVAMENTE PAGOS) ---
df_cap = fetch_all("""
    SELECT c.valor, c.data_vencimento, c.data_pagamento, c.descricao, c.status, pc.codigo, pc.categoria as pc_cat, pc.nome as pc_nome
    FROM contas_a_pagar c
    JOIN planos_de_contas pc ON c.plano_conta_id = pc.id
    WHERE UPPER(c.status) = 'PAGO' AND c.data_vencimento >= ? AND c.data_vencimento <= ?
""", (dt_cap_inicio_str, dt_cap_fim_str))

if not df_cap.empty:
    df_cap['data_vencimento'] = pd.to_datetime(df_cap['data_vencimento'], errors='coerce')
    df_cap['ref_month'] = df_cap['data_vencimento'].dt.to_period('M')
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
outros_fab_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.', na=False) & ~df_cap_mes['codigo'].str.startswith(('2.1.1', '2.1.2', '2.1.3', '2.1.4', '2.1.5'), na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

cmv_tot_mes = mp_val_mes + emb_mes + outros_fab_mes

# Nível 4: Despesas Comerciais Variáveis
comi_vd_val = float(df_vd_mes['comissao_valor'].sum()) if not df_vd_mes.empty else 0.0
comi_cap_val = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.1.4', na=False) | df_cap_mes['pc_nome'].str.contains('Comissão|Comissões', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
comi_mes = max(comi_vd_val, comi_cap_val)

frete_vd_val = float(df_vd_mes['custo_frete_rateado'].sum()) if not df_vd_mes.empty else 0.0
frete_cap_val = float(df_cap_mes[df_cap_mes['codigo'].str.startswith(('2.1.5', '2.2.3', '2.2.5'), na=False) | df_cap_mes['pc_nome'].str.contains('Frete', case=False, na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
frete_mes = max(frete_vd_val, frete_cap_val)

acordos_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.2', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
descarga_mes = float(df_vd_mes['custo_descarga'].sum()) if not df_vd_mes.empty else 0.0
degust_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.1', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0
promotores_mes = float(df_cap_mes[df_cap_mes['codigo'].str.startswith('2.2.4', na=False)]['valor'].sum()) if not df_cap_mes.empty else 0.0

desp_com_mes = comi_mes + frete_mes + acordos_mes + descarga_mes + degust_mes + promotores_mes

# Margem de Contribuição Líquida
mc_mes = rl_mes - cmv_tot_mes - desp_com_mes
mc_perc = (mc_mes / rl_mes * 100) if rl_mes > 0 else 0.0
mc_kg_mes = mc_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0

# Custos Fixos
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
is_capex = (df_cap_mes['codigo'].str.startswith(('3.3.', '1.2.', '4.1.'), na=False) | (df_cap_mes['pc_nome'].str.contains('Compra de Máquinas|Imobilizado|CAPEX', case=False, na=False) & ~df_cap_mes['codigo'].str.startswith('2.', na=False))) if not df_cap_mes.empty else pd.Series([], dtype=bool)
capex_mes = float(df_cap_mes[is_capex]['valor'].sum()) if not df_cap_mes.empty else 0.0
caixa_livre_mes = lucro_mes - capex_mes

# Saldo Inicial e Saldo Final Consolidado de Caixa
saldo_ini_df = fetch_all("""
    SELECT SUM(CASE WHEN tipo IN ('ENTRADA', 'Entrada') THEN valor ELSE -valor END) as saldo_ini
    FROM fluxo_caixa
    WHERE data < ?
""", (dt_vd_devol_inicio_str,))
saldo_inicial_caixa = float(saldo_ini_df['saldo_ini'].iloc[0]) if (not saldo_ini_df.empty and pd.notnull(saldo_ini_df['saldo_ini'].iloc[0])) else 0.0
saldo_final_caixa = saldo_inicial_caixa + caixa_livre_mes

# Ponto de Equilíbrio
break_even = (df_mes_val / (mc_perc / 100)) if mc_perc > 0 else 0.0

# --- FUNÇÃO AUXILIAR DE RENDERIZAÇÃO E DETALHAMENTO INLINE PELO PLANO DE CONTAS ---
def render_html(html_str):
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

def get_inline_rows_html(prefixos_codigo=None, nomes_filtro=None, ignorar_codigos=None):
    if df_cap_mes.empty:
        return ""
    cond = pd.Series([False] * len(df_cap_mes), index=df_cap_mes.index)
    if prefixos_codigo:
        for pfix in prefixos_codigo:
            cond |= df_cap_mes['codigo'].str.startswith(pfix, na=False)
    if nomes_filtro:
        for nfilt in nomes_filtro:
            cond |= df_cap_mes['pc_nome'].str.contains(nfilt, case=False, na=False)
            
    if ignorar_codigos:
        for icod in ignorar_codigos:
            cond &= ~df_cap_mes['codigo'].str.startswith(icod, na=False)
            
    df_filtered = df_cap_mes[cond]
    if df_filtered.empty:
        return ""
        
    grouped = df_filtered.groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index().sort_values(by='codigo')
    
    rows_html = ""
    for _, r in grouped.iterrows():
        cod = r['codigo']
        nome = r['pc_nome']
        val = float(r['valor'])
        rows_html += f"<div class='dre-row-sub'><div class='dre-label'><b>{cod} - {nome}</b></div><div class='dre-val'>{f_br(val)}</div></div>"
    return rows_html

# --- MODAL DE AUDITORIA DE LANÇAMENTOS (INSPEÇÃO DE NÚMEROS) ---
@st.dialog("🔍 Auditoria de Lançamentos Contábeis", width="large")
def modal_auditoria_lancamentos(conta_label, sel_mes_ano):
    st.caption(f"Exibindo extrato analítico com todos os títulos e registros que compõem **{conta_label}** em **{sel_mes_ano}**.")
    
    dt_inc = dt_vd_devol_inicio_str
    dt_fim = dt_vd_devol_fim_str
    
    if "1.1" in conta_label and "NF" in conta_label:
        df_a = fetch_all("""
            SELECT data AS "Emissão", id AS "Nº Venda", cliente_id AS "Cliente ID",
                   quantidade AS "Volume (Kg)", valor_total AS "Valor (R$)"
            FROM vendas
            WHERE status = 'FATURADO' AND data >= ? AND data <= ?
              AND (tipo_documento LIKE '%NF%' OR tipo_documento LIKE '%Nota%')
            ORDER BY data DESC
        """, (dt_inc, dt_fim))
    elif "1.2" in conta_label and "DAV" in conta_label:
        df_a = fetch_all("""
            SELECT data AS "Emissão", id AS "Nº Venda", cliente_id AS "Cliente ID",
                   quantidade AS "Volume (Kg)", valor_total AS "Valor (R$)"
            FROM vendas
            WHERE status = 'FATURADO' AND data >= ? AND data <= ?
              AND (tipo_documento NOT LIKE '%NF%' AND tipo_documento NOT LIKE '%Nota%')
            ORDER BY data DESC
        """, (dt_inc, dt_fim))
    elif "Devoluções" in conta_label:
        df_a = fetch_all("""
            SELECT data AS "Data", motivo AS "Motivo", cliente_id AS "Cliente ID",
                   valor_financeiro_abatido AS "Valor (R$)"
            FROM devolucoes
            WHERE data >= ? AND data <= ?
            ORDER BY data DESC
        """, (dt_inc, dt_fim))
    elif "4.1" in conta_label and "Matéria-Prima" in conta_label:
        df_a = fetch_all("""
            SELECT data AS "Data", fornecedor_id AS "Fornecedor ID",
                   peso_kg AS "Volume (Kg)", valor_total AS "Valor (R$)"
            FROM compras_materia_prima
            WHERE data >= ? AND data <= ?
            ORDER BY data DESC
        """, (dt_inc, dt_fim))
    else:
        cod_alvo = conta_label.split(' - ')[0].strip()
        df_a = fetch_all("""
            SELECT c.data_vencimento AS "Vencimento", c.data_pagamento AS "Data Pgto",
                   c.numero_documento AS "Doc / Título", c.descricao AS "Descrição",
                   c.status AS "Status", c.valor AS "Valor (R$)"
            FROM contas_a_pagar c
            JOIN planos_de_contas pc ON c.plano_conta_id = pc.id
            WHERE UPPER(c.status) = 'PAGO' AND c.data_vencimento >= ? AND c.data_vencimento <= ?
              AND pc.codigo LIKE ?
            ORDER BY c.data_vencimento ASC
        """, (dt_inc, dt_fim, f"{cod_alvo}%"))
        
    if df_a is None or df_a.empty:
        st.info(f"Nenhum lançamento individual encontrado para **{conta_label}** no período de {sel_mes_ano}.")
    else:
        tot_val = float(df_a['Valor (R$)'].sum()) if 'Valor (R$)' in df_a.columns else 0.0
        tot_reg = len(df_a)
        
        mc1, mc2 = st.columns(2)
        mc1.metric("Qtd. Lançamentos", tot_reg)
        mc2.metric("Soma Total Auditada", f_br(tot_val))
        
        df_disp = df_a.copy()
        if 'Valor (R$)' in df_disp.columns:
            df_disp['Valor (R$)'] = df_disp['Valor (R$)'].apply(lambda x: f_br(float(x)) if pd.notnull(x) else "R$ 0,00")
        if 'Volume (Kg)' in df_disp.columns:
            df_disp['Volume (Kg)'] = df_disp['Volume (Kg)'].apply(lambda x: f_kg(float(x)) if pd.notnull(x) else "0,0 Kg")
            
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        
        csv_data = df_a.to_csv(index=False).encode('utf-8')
        cod_clean = conta_label.split(' - ')[0].replace('.', '_')
        st.download_button(
            label="📥 Baixar Extrato de Auditoria (CSV)",
            data=csv_data,
            file_name=f"auditoria_{cod_clean}_{sel_mes_ano.replace('/', '_')}.csv",
            mime="text/csv"
        )

# -------- RENDERIZAÇÃO VISUAL ---------

st.markdown("<div class='dre-wrapper'>", unsafe_allow_html=True)

col_hdr_title, col_hdr_sel, col_hdr_audit = st.columns([1.5, 0.9, 1.2])
with col_hdr_title:
    st.markdown("<div class='dre-sec-header' style='margin-top: 0px;'>Demostrativo Gerencial de Caixa (RGC)</div>", unsafe_allow_html=True)
with col_hdr_sel:
    st.selectbox(
        "Selecione o Mês/Ano:",
        opcoes_meses,
        index=opcoes_meses.index(sel_mes_ano) if sel_mes_ano in opcoes_meses else default_idx,
        key="sel_mes_ano"
    )
with col_hdr_audit:
    opcoes_audit = [
        "🔍 Auditar Rubrica / Conta...",
        "1.1 - Vendas por Nota Fiscal (NF)",
        "1.2 - Vendas por DAV (Pedido)",
        "2 - Devoluções e Abatimentos",
        "4.1 - Matéria-Prima (Alho in Natura)"
    ]
    if not df_cap_mes.empty:
        pcs_mes = df_cap_mes[['codigo', 'pc_nome']].drop_duplicates().sort_values('codigo')
        for _, r in pcs_mes.iterrows():
            lbl = f"{r['codigo']} - {r['pc_nome']}"
            if lbl not in opcoes_audit:
                opcoes_audit.append(lbl)
                
    rubrica_sel = st.selectbox(
        "🔍 Inspecionar Conta:",
        opcoes_audit,
        key="sel_audit_rubrica"
    )
    if rubrica_sel and rubrica_sel != "🔍 Auditar Rubrica / Conta...":
        modal_auditoria_lancamentos(rubrica_sel, sel_mes_ano)

# -------------------------------------------------------------------------
# ABERTURA DO CAIXA (SALDO INICIAL)
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row-total' style='background-color: #e0f2fe; border-top: 2px solid #0284c7; border-bottom: 2px solid #0284c7; color: #0369a1; margin-top: 10px; margin-bottom: 20px;'>
    <div class='dre-label'>
        <b style='font-size: 1.1rem;'>(+) SALDO INICIAL CONSOLIDADO DE CAIXA (Abertura do Mês)</b>
    </div>
    <div class='dre-val-total' style='color: #0369a1; font-size: 1.15rem;'>{f_br(saldo_inicial_caixa)}</div>
</div>
""")

st.markdown("<div class='dre-sec-header'>I. Entradas de Caixa (Faturamento Líquido Real)</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# I. RECEITA E DEDUÇÕES (Tabela Financeira Executiva Limpa)
# -------------------------------------------------------------------------
render_html(f"""
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
    <div class='dre-label'><b>3. (-) Impostos sobre Venda (2.1.3)</b></div>
    <div class='dre-val'>{f_br(imp_venda_mes)}</div>
</div>
{get_inline_rows_html(prefixos_codigo=['2.1.3'])}
<div class='dre-row-total'>
    <div class='dre-label'>
        (=) RECEITA LÍQUIDA REAL REALIZADA
        <span class='dre-tag'>Volume Líquido: {f_kg(rl_kg_mes)}</span>
        <span class='dre-tag'>Preço Médio Líquido: {f_pm(rl_pm_mes)}</span>
    </div>
    <div class='dre-val-total'>{f_br(rl_mes)}</div>
</div>
""")

st.markdown("<div class='dre-sec-header'>II. Custos Fabris e Despesas Variáveis</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# II. CMV FABRIL REMODELADO & CUSTOS VARIÁVEIS
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row-subtotal'>
    <div class='dre-label'><b>4. Custo Total de Fabricação / CMV Realizado</b></div>
    <div class='dre-val-total'>{f_br(cmv_tot_mes)}</div>
</div>
<div class='dre-row-sub'>
    <div class='dre-label'>
        <b>4.1 (-) Matéria-Prima Paga (Alho in Natura)</b>
        <span class='dre-tag'>Compras: {f_kg(mp_kg_mes)}</span>
        <span class='dre-tag'>Custo Médio: {f_pm(mp_pm_mes)}</span>
    </div>
    <div class='dre-val'>{f_br(mp_val_mes)}</div>
</div>
<div class='dre-row-sub'>
    <div class='dre-label'><b>4.2 (-) Embalagens & Insumos Paga (2.1.2)</b></div>
    <div class='dre-val'>{f_br(emb_mes)}</div>
</div>
{"<div class='dre-row-sub'><div class='dre-label'><b>4.3 (-) Outros Custos Fabris Diretos Pagos</b></div><div class='dre-val'>" + f_br(outros_fab_mes) + "</div></div>" if outros_fab_mes > 0 else ""}
{get_inline_rows_html(prefixos_codigo=['2.1.'], ignorar_codigos=['2.1.1', '2.1.2', '2.1.3', '2.1.4', '2.1.5'])}
<div class='dre-row-subtotal' style='margin-top: 10px;'>
    <div class='dre-label'><b>5. Despesas Comerciais Variáveis Pagas</b></div>
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
{get_inline_rows_html(prefixos_codigo=['2.2.'], ignorar_codigos=['2.2.1', '2.2.2', '2.2.4', '2.1.4', '2.1.5'])}
<div class='dre-row-total'>
    <div class='dre-label'>
        (=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA DE CAIXA
        <span class='dre-tag'>Margem: {mc_perc:.1f}%</span>
        <span class='dre-tag'>Margem/Kg: {f_pm(mc_kg_mes)}</span>
    </div>
    <div class='dre-val-total'>{f_br(mc_mes)}</div>
</div>
""")

st.markdown("<div class='dre-sec-header'>III. Custos Fixos Pagos</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# III. CUSTOS FIXOS (Abertura direta pelo Plano de Contas)
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row-subtotal'>
    <div class='dre-label'><b>6. (-) Custos Fixos Totais Pagos</b></div>
    <div class='dre-val-total'>{f_br(df_mes_val)}</div>
</div>
{get_inline_rows_html(prefixos_codigo=['2.3.', '3.1.'])}
""")

st.markdown("<div class='dre-sec-header'>IV. EBITDA de Caixa (Resultado Operacional Real)</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# IV. EBITDA
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row-total'>
    <div class='dre-label'>
        (=) EBITDA DE CAIXA (Resultado Operacional)
        <span class='dre-tag'>Margem EBITDA: {ebitda_perc:.1f}%</span>
    </div>
    <div class='dre-val-total'>{f_br(ebitda_mes)}</div>
</div>
""")

st.markdown("<div class='dre-sec-header'>V. Fatores Não-Operacionais e Financeiros Pagos</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# V. FATORES FINANCEIROS & LUCRO LÍQUIDO
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row'>
    <div class='dre-label'><b>7. (-) Depreciação / Amortização</b></div>
    <div class='dre-val'>{f_br(depr_mes)}</div>
</div>
<div class='dre-row'>
    <div class='dre-label'><b>8. (-) Impostos sobre Lucro (IRPJ/CSLL Pagos)</b></div>
    <div class='dre-val'>{f_br(imp_lucro_mes)}</div>
</div>
<div class='dre-row'>
    <div class='dre-label'><b>9. (-) Juros e Financiamentos Pagos</b></div>
    <div class='dre-val'>{f_br(finan_mes)}</div>
</div>
<div class='dre-row'>
    <div class='dre-label'><b>10. (-) JCP (Juros s/ Capital Próprio Pagos)</b></div>
    <div class='dre-val'>{f_br(jcp_mes)}</div>
</div>
{get_inline_rows_html(prefixos_codigo=['3.2.'], nomes_filtro=['Depreciação', 'Impostos sobre Lucro', 'IRPJ', 'CSLL', 'Financiamento', 'Juros', 'JCP'])}
""")

st.markdown("<div class='dre-sec-header'>VI. Geração Líquida de Caixa Operacional</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# VI. LUCRO LÍQUIDO & DIVIDENDOS
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row-subtotal'>
    <div class='dre-label'>
        <b>11. (=) GERAÇÃO LÍQUIDA DE CAIXA OPERACIONAL</b>
        <span class='dre-tag'>Lucratividade: {lucro_perc:.1f}%</span>
    </div>
    <div class='dre-val-total'>{f_br(lucro_mes)}</div>
</div>
<div class='dre-row-sub'>
    <div class='dre-label'><b>12. (-) Dividendos (Saque/Distribuição Efetivada ao Sócio)</b></div>
    <div class='dre-val'>{f_br(div_mes)}</div>
</div>
<div class='dre-row-total'>
    <div class='dre-label'><b>(=) GERAÇÃO RETIDA DE CAIXA OPERACIONAL</b></div>
    <div class='dre-val-total'>{f_br(retido_mes)}</div>
</div>
""")

st.markdown("<div class='dre-sec-header'>VII. Desembolsos de Investimentos (CAPEX)</div>", unsafe_allow_html=True)

render_html(f"""
<div class='dre-row'>
    <div class='dre-label'>Geração Líquida de Caixa Operacional</div>
    <div class='dre-val'>{f_br(lucro_mes)}</div>
</div>
<div class='dre-row'>
    <div class='dre-label'><b>(-) Desembolsos de Investimentos Pagos</b> *(Compra de Máquinas, Equipamentos e Imobilizado)*</div>
    <div class='dre-val'>- {f_br(capex_mes)}</div>
</div>
{get_inline_rows_html(prefixos_codigo=['3.3.', '1.2.', '4.1.'], nomes_filtro=['Compra de Máquinas', 'Imobilizado', 'CAPEX'], ignorar_codigos=['2.3.3', '2.3.'])}
<div class='dre-row-total' style='background-color: #fef08a; border-top: 2px solid #eab308; border-bottom: 2px solid #ca8a04; color: #854d0e;'>
    <div class='dre-label'><b style='font-size: 1.05rem;'>(=) GERAÇÃO / REDUÇÃO LÍQUIDA DE CAIXA NO MÊS</b></div>
    <div class='dre-val-total' style='color: #854d0e; font-size: 1.1rem;'>{f_br(caixa_livre_mes)}</div>
</div>
""")

# -------------------------------------------------------------------------
# FECHAMENTO DO CAIXA (SALDO FINAL)
# -------------------------------------------------------------------------
render_html(f"""
<div class='dre-row-total' style='background-color: #dcfce7; border-top: 2px solid #16a34a; border-bottom: 2px solid #16a34a; color: #15803d; margin-top: 25px; margin-bottom: 20px;'>
    <div class='dre-label'>
        <b style='font-size: 1.15rem;'>(=) SALDO FINAL CONSOLIDADO DE CAIXA (Fechamento do Mês)</b>
        <span class='dre-tag' style='background-color: #bbf7d0; color: #166534;'>Geração Líquida no Mês: {f_br(caixa_livre_mes)}</span>
    </div>
    <div class='dre-val-total' style='color: #15803d; font-size: 1.2rem;'>{f_br(saldo_final_caixa)}</div>
</div>
""")

st.caption("📌 **Visão Gerencial:** Relatório 100% sob Regime de Caixa. Do caixa gerado operacionalmente são deduzidos os desembolsos efetivamente pagos em investimentos (compra de máquinas, equipamentos, etc.) no mês.")

st.markdown("---")

# -------------------------------------------------------------------------
# VIII. PONTO DE EQUILÍBRIO (BREAK-EVEN) EM EXPANDER
# -------------------------------------------------------------------------
with st.expander("🎯 Ponto de Equilíbrio (Break-Even Operacional)", expanded=False):
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

st.markdown("</div>", unsafe_allow_html=True)

