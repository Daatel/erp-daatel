import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from database import fetch_all
from estilo import carregar_estilo

st.set_page_config(
    page_title="Rentabilidade por Cliente",
    page_icon="📈",
    layout="wide"
)
carregar_estilo()

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
</style>
<h1 style='font-size: 2.2rem; font-weight: 700; margin-top: -15px; margin-bottom: 20px; color: #1e293b;'>
Rentabilidade e DRE por Cliente / Rede (CNPJ)
</h1>
""", unsafe_allow_html=True)
st.markdown("Audite e rastreie a Margem de Contribuição Líquida real de cada canal de venda, considerando CMV FIFO, bonificações, acordos comerciais, degustações e promotores.")

# ================= SIDEBAR FILTERS =================
st.sidebar.header("🎯 Filtros e Parâmetros")

# 1. Filtro Temporal
opcoes_tempo = ["Últimos 30 Dias", "Últimos 90 Dias", "Mês Atual", "Ano Corrente", "Personalizado"]
sel_tempo = st.sidebar.selectbox("Período de Análise:", opcoes_tempo, index=1)

hoje = date.today()
if sel_tempo == "Últimos 30 Dias":
    data_inicio = hoje - timedelta(days=30)
    data_fim = hoje
elif sel_tempo == "Últimos 90 Dias":
    data_inicio = hoje - timedelta(days=90)
    data_fim = hoje
elif sel_tempo == "Mês Atual":
    data_inicio = date(hoje.year, hoje.month, 1)
    data_fim = hoje
elif sel_tempo == "Ano Corrente":
    data_inicio = date(hoje.year, 1, 1)
    data_fim = hoje
else:
    c_col1, c_col2 = st.sidebar.columns(2)
    data_inicio = c_col1.date_input("Início:", hoje - timedelta(days=90))
    data_fim = c_col2.date_input("Fim:", hoje)

st.sidebar.markdown(f"🗓️ **Intervalo:** `{data_inicio.strftime('%d/%m/%Y')}` até `{data_fim.strftime('%d/%m/%Y')}`")

# 2. Detecção e Configuração de Impostos
try:
    df_global_fc = fetch_all("""
        SELECT fc.tipo, fc.valor, pc.codigo, fc.categoria 
        FROM fluxo_caixa fc
        LEFT JOIN planos_de_contas pc ON fc.categoria = pc.nome
        WHERE fc.data >= ? AND fc.data <= ?
    """, (data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
except Exception:
    df_global_fc = pd.DataFrame()

global_gross = 0.0
global_tax = 0.0
detected_tax_pct = 6.0 # Fallback default

if not df_global_fc.empty:
    global_gross = df_global_fc[df_global_fc['tipo'] == 'Entrada']['valor'].sum()
    # Impostos (código 2.1.3 ou regex simples)
    global_tax = df_global_fc[
        (df_global_fc['tipo'] == 'Saída') & 
        ((df_global_fc['codigo'] == '2.1.3') | (df_global_fc['categoria'].str.contains('imposto.*venda|simples|icms|pis|cofins|das', case=False, na=False)))
    ]['valor'].sum()
    
    if global_gross > 0:
        detected_tax_pct = (global_tax / global_gross) * 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("🧾 Alíquota de Impostos s/ Vendas")
st.sidebar.markdown(f"📊 Detectado proporcional no caixa: **{detected_tax_pct:.2f}%**")
tax_pct = st.sidebar.slider("Alíquota Simulada (%):", min_value=0.0, max_value=25.0, value=float(round(detected_tax_pct, 2)), step=0.1)

# ================= BUSCA DE DADOS BASE =================
# Buscar todos os clientes ativos com faturamentos
df_clientes = fetch_all("SELECT id, nome, cnpj_cpf as cnpj, rede_clientes, representante_id FROM clientes")

# Vendas Faturadas no período
q_vendas = """
    SELECT v.cliente_id, v.valor_total, v.custo_cmv_real, v.custo_descarga, v.is_bonificacao, v.id as venda_id
    FROM vendas v
    WHERE v.status = 'FATURADO' AND v.data >= ? AND v.data <= ?
"""
df_v_periodo = fetch_all(q_vendas, (data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))

# Devoluções no período
df_dev_periodo = fetch_all("""
    SELECT cliente_id, valor_financeiro_abatido 
    FROM devolucoes
    WHERE data >= ? AND data <= ?
""", (data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))

# Despesas Financeiras Mapeadas por Cliente (Contratos 2.2.2, Degustações 2.2.1, Promotores 2.2.4)
df_despesas_fin = fetch_all("""
    SELECT fc.cliente_id, pc.codigo, fc.categoria, fc.valor
    FROM fluxo_caixa fc
    LEFT JOIN planos_de_contas pc ON fc.categoria = pc.nome
    WHERE fc.tipo = 'Saída' AND fc.cliente_id IS NOT NULL AND fc.data >= ? AND fc.data <= ?
""", (data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))

# ================= PROCESSAMENTO DE RENTABILIDADE POR CLIENTE =================
consolidado = []

for _, cli in df_clientes.iterrows():
    c_id = int(cli['id'])
    
    # 1. Faturamento e CMV
    vendas_cli = df_v_periodo[df_v_periodo['cliente_id'] == c_id]
    receita_bruta = vendas_cli['valor_total'].sum()
    cmv_real = vendas_cli['custo_cmv_real'].sum()
    taxa_descarga = vendas_cli['custo_descarga'].sum()
    
    # 2. Devoluções
    dev_cli = df_dev_periodo[df_dev_periodo['cliente_id'] == c_id]
    devolucoes = dev_cli['valor_financeiro_abatido'].sum()
    
    # 3. Impostos calculados pela alíquota simulada
    impostos = receita_bruta * (tax_pct / 100.0)
    
    # 4. Receita Líquida
    receita_liquida = receita_bruta - devolucoes - impostos
    
    # 5. Despesas Diretas de Fluxo de Caixa vinculadas a esse cliente
    desp_cli = df_despesas_fin[df_despesas_fin['cliente_id'] == c_id]
    
    # 2.2.2 Contratos Comerciais
    contratos = desp_cli[
        (desp_cli['codigo'] == '2.2.2') | 
        (desp_cli['categoria'].str.contains('acordo|contrato|listing|rapel|enxoval', case=False, na=False))
    ]['valor'].sum()
    
    # 2.2.1 Degustações e Amostras
    degustacoes = desp_cli[
        (desp_cli['codigo'] == '2.2.1') | 
        (desp_cli['categoria'].str.contains('degustação|amostra', case=False, na=False))
    ]['valor'].sum()
    
    # 2.2.4 Promotores
    promotores = desp_cli[
        (desp_cli['codigo'] == '2.2.4') | 
        (desp_cli['categoria'].str.contains('promotor', case=False, na=False))
    ]['valor'].sum()
    
    # 6. Lucro Líquido do Cliente e Margem
    lucro_liquido = receita_liquida - cmv_real - contratos - degustacoes - promotores - taxa_descarga
    margem_contrib = (lucro_liquido / receita_liquida * 100.0) if receita_liquida > 0 else 0.0
    
    consolidado.append({
        "id": c_id,
        "Cliente": cli['nome'],
        "CNPJ": cli['cnpj'] or "Não Informado",
        "Rede / Grupo": cli['rede_clientes'] or "Independente",
        "Receita Bruta": receita_bruta,
        "Devoluções": devolucoes,
        "Impostos": impostos,
        "Receita Líquida": receita_liquida,
        "CMV FIFO": cmv_real,
        "Contratos (2.2.2)": contratos,
        "Degustações (2.2.1)": degustacoes,
        "Promotores (2.2.4)": promotores,
        "Taxa Descarga": taxa_descarga,
        "Lucro Líquido": lucro_liquido,
        "Margem (%)": margem_contrib
    })

df_consolidado = pd.DataFrame(consolidado)

# Filtra apenas clientes que tiveram faturamento ou alguma despesa/movimentação no período para não sujar o painel
df_consolidado = df_consolidado[
    (df_consolidado['Receita Bruta'] > 0) | 
    (df_consolidado['Contratos (2.2.2)'] > 0) | 
    (df_consolidado['Degustações (2.2.1)'] > 0) | 
    (df_consolidado['Promotores (2.2.4)'] > 0) | 
    (df_consolidado['Devoluções'] > 0)
]

# ================= RENDER KPIs GLOBAIS DE CLIENTES =================
if df_consolidado.empty:
    st.info("ℹ️ Nenhuma venda faturada ou movimentação financeira por cliente registrada no período selecionado.")
else:
    total_rb = df_consolidado['Receita Bruta'].sum()
    total_dev = df_consolidado['Devoluções'].sum()
    total_imp = df_consolidado['Impostos'].sum()
    total_rl = df_consolidado['Receita Líquida'].sum()
    total_cmv = df_consolidado['CMV FIFO'].sum()
    total_contr = df_consolidado['Contratos (2.2.2)'].sum()
    total_deg = df_consolidado['Degustações (2.2.1)'].sum()
    total_prom = df_consolidado['Promotores (2.2.4)'].sum()
    total_desc = df_consolidado['Taxa Descarga'].sum()
    total_lucro = df_consolidado['Lucro Líquido'].sum()
    global_margin = (total_lucro / total_rl * 100.0) if total_rl > 0 else 0.0

    st.subheader("📊 Painel Executivo Consolidado")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Receita Bruta Total", format_brl(total_rb))
    kpi2.metric("Receita Líquida Total", format_brl(total_rl))
    kpi3.metric("CMV FIFO Real Acumulado", format_brl(total_cmv), delta="Dedução física", delta_color="inverse")
    
    if total_lucro >= 0:
        kpi4.metric("Lucro Líquido Canal (Clientes)", format_brl(total_lucro), delta=f"MC: {global_margin:.1f}%")
    else:
        kpi4.metric("Lucro Líquido Canal (Clientes)", format_brl(total_lucro), delta=f"MC: {global_margin:.1f}%", delta_color="inverse")

    st.markdown("---")

    # ================= SELEÇÃO DE VISUALIZAÇÃO =================
    st.sidebar.markdown("---")
    opcoes_visualizacao = ["Resumo de Todos os Clientes", "Deep-Dive por Cliente Específico"]
    visualizacao = st.sidebar.radio("Selecione a Visualização:", opcoes_visualizacao)

    if visualizacao == "Resumo de Todos os Clientes":
        st.subheader("📋 Demonstrativo de Rentabilidade Comparativo")
        
        # Formata DataFrame para exibição premium
        df_display = df_consolidado.copy()
        
        # Farol de Status
        def check_status(row):
            if row['Lucro Líquido'] < 0: return "🔴 Prejuízo"
            elif row['Margem (%)'] < 10: return "🟡 Alerta"
            return "🟢 Lucrativo"
            
        df_display['Status'] = df_display.apply(check_status, axis=1)
        
        df_formatted = pd.DataFrame()
        df_formatted['Cliente'] = df_display['Cliente']
        df_formatted['Rede / Grupo'] = df_display['Rede / Grupo']
        df_formatted['Status'] = df_display['Status']
        df_formatted['Faturamento Bruto'] = df_display['Receita Bruta'].apply(format_brl)
        df_formatted['Devoluções'] = df_display['Devoluções'].apply(format_brl)
        df_formatted['Impostos'] = df_display['Impostos'].apply(format_brl)
        df_formatted['Receita Líquida'] = df_display['Receita Líquida'].apply(format_brl)
        df_formatted['CMV FIFO'] = df_display['CMV FIFO'].apply(format_brl)
        df_formatted['Contratos (Listing)'] = df_display['Contratos (2.2.2)'].apply(format_brl)
        df_formatted['Amostras / Degust.'] = df_display['Degustações (2.2.1)'].apply(format_brl)
        df_formatted['Promotores'] = df_display['Promotores (2.2.4)'].apply(format_brl)
        df_formatted['Taxa Descarga'] = df_display['Taxa Descarga'].apply(format_brl)
        df_formatted['Lucro Líquido'] = df_display['Lucro Líquido'].apply(format_brl)
        df_formatted['Margem MC'] = df_display['Margem (%)'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_formatted, hide_index=True, width="stretch")
        
        # ================= CHARTS BLOCK =================
        st.markdown("---")
        st.subheader("📊 Rankings e Comparações de Canais")
        
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.markdown("##### Margem de Contribuição por Cliente (%)")
            # Ordena por margem
            df_sorted = df_consolidado.sort_values(by="Margem (%)", ascending=True)
            
            fig_margin = go.Figure()
            fig_margin.add_trace(go.Bar(
                y=df_sorted['Cliente'],
                x=df_sorted['Margem (%)'],
                orientation='h',
                marker=dict(
                    color=df_sorted['Margem (%)'].apply(lambda val: '#ef4444' if val < 0 else ('#fbbf24' if val < 10 else '#10b981')),
                    line=dict(width=1, color='white')
                ),
                text=df_sorted['Margem (%)'].apply(lambda val: f"{val:.1f}%"),
                textposition='inside'
            ))
            
            fig_margin.update_layout(
                xaxis_title="Margem de Contribuição (%)",
                yaxis_title="Clientes",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=150, r=20, t=20, b=20)
            )
            fig_margin.update_xaxes(gridcolor='rgba(128,128,128,0.2)', zerolinecolor='rgba(128,128,128,0.5)', zerolinewidth=1)
            st.plotly_chart(fig_margin, use_container_width=True)

        with c_right:
            st.markdown("##### Peso dos Custos na Receita Bruta Global (%)")
            labels = ['Lucro Líquido', 'CMV FIFO', 'Impostos', 'Contratos/Listing', 'Devoluções', 'Amostras/Degustações', 'Promotores', 'Taxa Descarga']
            values = [total_lucro, total_cmv, total_imp, total_contr, total_dev, total_deg, total_prom, total_desc]
            
            # Filtra valores negativos para o gráfico de pizza (caso o Lucro Líquido global seja negativo)
            clean_labels = []
            clean_values = []
            for lbl, val in zip(labels, values):
                if val > 0:
                    clean_labels.append(lbl)
                    clean_values.append(val)
                    
            fig_donut = go.Figure(data=[go.Pie(
                labels=clean_labels, 
                values=clean_values, 
                hole=.4,
                marker=dict(colors=['#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#ef4444', '#8b5cf6', '#06b6d4', '#6b7280'])
            )])
            fig_donut.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    else:
        st.subheader("🔍 Deep-Dive Analítico por Cliente")
        
        # Seletor de Cliente específico
        opts_cli_deep = {f"{r['Cliente']}": r['id'] for _, r in df_consolidado.iterrows()}
        cli_deep_sel = st.selectbox("Selecione o Cliente para detalhamento:", list(opts_cli_deep.keys()))
        
        if cli_deep_sel:
            cli_id_sel = opts_cli_deep[cli_deep_sel]
            row_cli = df_consolidado[df_consolidado['id'] == cli_id_sel].iloc[0]
            
            # KPIs Rápidos do Cliente
            st.markdown(f"### 🛡️ Diagnóstico de Conta: **{row_cli['Cliente']}**")
            st.markdown(f"🧾 **CNPJ/CPF:** `{row_cli['CNPJ']}` | ⛓️ **Rede:** `{row_cli['Rede / Grupo']}`")
            
            colC1, colC2, colC3, colC4 = st.columns(4)
            colC1.metric("Faturamento Bruto", format_brl(row_cli['Receita Bruta']))
            colC2.metric("Receita Líquida", format_brl(row_cli['Receita Líquida']))
            colC3.metric("Lucro Líquido Gerado", format_brl(row_cli['Lucro Líquido']))
            
            margin_cli = row_cli['Margem (%)']
            if margin_cli < 0:
                colC4.error(f"Margem de Contribuição: {margin_cli:.1f}%")
            elif margin_cli < 10:
                colC4.warning(f"Margem de Contribuição: {margin_cli:.1f}%")
            else:
                colC4.success(f"Margem de Contribuição: {margin_cli:.1f}%")
                
            # Bloco de Análise e Advisory Inteligente
            st.markdown("---")
            st.subheader("💡 Relatório de Margem e Ações Recomendadas")
            
            lucro = row_cli['Lucro Líquido']
            faturamento = row_cli['Receita Bruta']
            contracts = row_cli['Contratos (2.2.2)']
            tastings = row_cli['Degustações (2.2.1)']
            promoters = row_cli['Promotores (2.2.4)']
            cmv = row_cli['CMV FIFO']
            descarga = row_cli['Taxa Descarga']
            devolutions = row_cli['Devoluções']
            
            if margin_cli < 0:
                st.error(
                    f"⚠️ **CONTA NO VERMELHO:** Esta conta está gerando prejuízo líquido de **{format_brl(abs(lucro))}** para a fábrica! "
                    "A margem líquida é negativa. Isso significa que a operação comercial nesse PDV custa mais caro do que o faturamento traz. "
                    "Considere as seguintes ações de urgência imediata:\n"
                    f"1. **Rever Contratos Comerciais (R$ {contracts:,.2f}):** Os rebates e rebates fixos (Listing Fee / Enxoval) estão incompatíveis com a tração de venda.\n"
                    f"2. **Auditar Ações Físicas (Degustações: R$ {tastings:,.2f} | Promotores: R$ {promoters:,.2f}):** As despesas comerciais extras estão drenando a contribuição líquida da conta.\n"
                    f"3. **Analisar Devoluções / Trocas (R$ {devolutions:,.2f}):** Trocas por mofo ou quebras na gôndola precisam ser controladas com inteligência logística.\n"
                    f"4. **Revisar Custo de Descarga (CD):** Taxas de descarga abusivas acumuladas em **R$ {descarga:,.2f}** no CD do cliente devem ser rateadas ou cobradas de volta no preço base."
                )
            elif margin_cli < 10:
                st.warning(
                    f"🟡 **MARGEM CRÍTICA ({margin_cli:.1f}%):** O cliente é lucrativo, mas opera sob margem muito apertada (abaixo do patamar saudável de 10%). "
                    "Qualquer oscilação no custo das matérias-primas ou aumento de taxa de CD colocará esta operação no prejuízo contábil.\n"
                    "**Ação Recomendada:** Reduzir ações temporais de degustação e acompanhar se o giro orgânico se sustenta no PDV sem custos agressivos."
                )
            else:
                st.success(
                    f"🟢 **CLIENTE ALTAMENTE LUCRATIVO ({margin_cli:.1f}%):** Esta é uma conta estratégica e saudável! O faturamento líquido absorve com maestria o custo CMV FIFO "
                    f"e todas as despesas dedicadas de promotor e acordos de rede. Parabéns! Ações de expansão de mix e sell-in devem ser priorizadas aqui."
                )
                
            # Gráfico de Cascata de Rentabilidade (Waterfall Chart)
            st.markdown("---")
            st.subheader("📊 Cascata de Composição da Margem (BRL)")
            
            # Dados para a cascata
            w_labels = ["Receita Bruta", "Devoluções", "Impostos", "CMV FIFO Real", "Contratos (Listing)", "Degustações / Amostras", "Promotores PDV", "Taxa de Descarga", "Resultado Líquido"]
            w_values = [faturamento, -devolutions, -row_cli['Impostos'], -cmv, -contracts, -tastings, -promoters, -descarga, lucro]
            
            # Formata medidas
            w_measure = ["relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"]
            
            fig_waterfall = go.Figure(go.Waterfall(
                name="Composição",
                orientation="v",
                measure=w_measure,
                x=w_labels,
                textposition="outside",
                text=[f"R$ {val:,.0f}" if val != 0 else "" for val in w_values],
                y=w_values,
                connector=dict(line=dict(color="rgba(128, 128, 128, 0.5)")),
                decreasing=dict(marker=dict(color="#ef4444")),
                increasing=dict(marker=dict(color="#10b981")),
                totals=dict(marker=dict(color="#3b82f6"))
            ))
            
            fig_waterfall.update_layout(
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=40, t=40, b=40)
            )
            fig_waterfall.update_yaxes(gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig_waterfall, use_container_width=True)

            # Detalhamento Físico de Pedidos (Vendas Faturadas)
            st.markdown("---")
            st.subheader("📦 Vendas Faturadas e CMV FIFO Associado")
            df_v_cli = fetch_all("""
                SELECT v.id as 'Pedido', v.data as 'Data', p.nome as 'Produto', 
                       v.quantidade as 'Quantidade', v.valor_unitario as 'Preço Unit.',
                       v.valor_total as 'Faturamento Bruto', v.custo_cmv_real as 'CMV FIFO Real',
                       v.custo_acordos_rede as 'Acordo Comercial', v.custo_descarga as 'Taxa Descarga',
                       v.is_bonificacao as 'Bonificado?'
                FROM vendas v
                JOIN produtos p ON v.produto_id = p.id
                WHERE v.cliente_id = ? AND v.status = 'FATURADO' AND v.data >= ? AND v.data <= ?
                ORDER BY v.data DESC
            """, (cli_id_sel, data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
            
            if df_v_cli.empty:
                st.info("Nenhum pedido faturado para este cliente no período.")
            else:
                df_v_cli['Data'] = pd.to_datetime(df_v_cli['Data']).dt.strftime('%d/%m/%Y')
                df_v_cli['Faturamento Bruto'] = df_v_cli['Faturamento Bruto'].apply(format_brl)
                df_v_cli['CMV FIFO Real'] = df_v_cli['CMV FIFO Real'].apply(format_brl)
                df_v_cli['Acordo Comercial'] = df_v_cli['Acordo Comercial'].apply(format_brl)
                df_v_cli['Taxa Descarga'] = df_v_cli['Taxa Descarga'].apply(format_brl)
                df_v_cli['Preço Unit.'] = df_v_cli['Preço Unit.'].apply(format_brl)
                df_v_cli['Bonificado?'] = df_v_cli['Bonificado?'].apply(lambda x: "🎁 Sim" if x == 1 or x is True else "❌ Não")
                
                st.dataframe(df_v_cli, hide_index=True, width="stretch")

            # Detalhamento de Despesas Financeiras Mapeadas (Fluxo de Caixa)
            st.markdown("---")
            st.subheader("💸 Lançamentos Financeiros (Saídas do Caixa) Mapeados p/ Cliente")
            df_fc_cli = fetch_all("""
                SELECT fc.data as 'Data Lançamento', pc.codigo as 'Código Conta', 
                       fc.categoria as 'Planta de Custo', fc.descricao as 'Descrição/Fatura', 
                       fc.valor as 'Valor Debitado'
                FROM fluxo_caixa fc
                JOIN planos_de_contas pc ON fc.categoria = pc.nome
                WHERE fc.cliente_id = ? AND fc.tipo = 'Saída' AND fc.data >= ? AND fc.data <= ?
                ORDER BY fc.data DESC
            """, (cli_id_sel, data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
            
            if df_fc_cli.empty:
                st.info("Nenhuma despesa ou repasse financeiro debitado para este cliente no período.")
            else:
                df_fc_cli['Data Lançamento'] = pd.to_datetime(df_fc_cli['Data Lançamento']).dt.strftime('%d/%m/%Y')
                df_fc_cli['Valor Debitado'] = df_fc_cli['Valor Debitado'].apply(format_brl)
                st.dataframe(df_fc_cli, hide_index=True, width="stretch")
