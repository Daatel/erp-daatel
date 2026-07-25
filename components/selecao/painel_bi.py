# components/selecao/painel_bi.py
# Aba 1 — Painel de Produção (BI Executivo)

import streamlit as st
import pandas as pd
from datetime import date
import calendar
import plotly.graph_objects as go
from database import fetch_all
from .queries import SQL_BI_PRODUCAO_MES, SQL_PARAMETROS_MES, SQL_EXCECOES_MES


def render_painel_bi():
    st.markdown("### 📊 Painel de Produção & Rendimento da Seleção")
    st.caption("Acompanhamento mensal da produção da mesa de seleção vs metas estabelecidas.")

    hoje = date.today()

    # Seletor de Mês/Ano
    col_mes, col_esp = st.columns([2, 4])
    str_mes_sel = col_mes.date_input("Mês de Referência", value=date(hoje.year, hoje.month, 1), format="MM/YYYY")
    mes_ano = date(str_mes_sel.year, str_mes_sel.month, 1)
    str_mes_db = mes_ano.strftime("%Y-%m")
    str_mes_01 = mes_ano.strftime("%Y-%m-01")

    # 1. Carrega parâmetros do mês
    df_params = fetch_all(SQL_PARAMETROS_MES, (str_mes_01, str_mes_01))
    meta_casa_diaria = float(df_params.iloc[0]['meta_diaria_casa_kg']) if not df_params.empty else 500.0
    dias_efetivos = int(df_params.iloc[0]['dias_uteis_efetivos']) if not df_params.empty else 22

    meta_total_mes = meta_casa_diaria * dias_efetivos

    # 2. Carrega produção diária do mês
    df_prod = fetch_all(SQL_BI_PRODUCAO_MES, (str_mes_db, f"{str_mes_db}%"))

    realizado_mes = float(df_prod['producao_total_kg'].sum()) if not df_prod.empty else 0.0
    dias_trabalhados = len(df_prod) if not df_prod.empty else 0
    dias_restantes = max(dias_efetivos - dias_trabalhados, 0)

    # Projeção até o fim do mês
    media_diaria_atual = (realizado_mes / dias_trabalhados) if dias_trabalhados > 0 else 0.0
    projetado_fim = realizado_mes + (media_diaria_atual * dias_restantes)

    # Dias acima da meta
    dias_acima = int((df_prod['producao_total_kg'] >= meta_casa_diaria).sum()) if not df_prod.empty else 0

    # Necessário por dia para atingir a meta do mês
    necessario_dia = ((meta_total_mes - realizado_mes) / dias_restantes) if dias_restantes > 0 else 0.0

    # Médias gerais
    media_presentes_dia = float(df_prod['n_presentes'].mean()) if not df_prod.empty and 'n_presentes' in df_prod.columns else 0.0
    media_prod_selecionadora = float(df_prod['media_por_selecionadora_kg'].mean()) if not df_prod.empty else 0.0

    # -------------------------------------------------------------------------
    # ROW DE 5 CARDS KPI
    # -------------------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Realizado no Mês",
        f"{realizado_mes:,.0f} kg",
        f"até {hoje.strftime('%d/%m')}" if mes_ano.month == hoje.month else "Mês Fechado"
    )

    c2.metric(
        "Projetado até o Fim",
        f"{projetado_fim:,.0f} kg",
        "no ritmo atual"
    )

    c3.metric(
        "Meta Total do Mês",
        f"{meta_total_mes:,.0f} kg",
        f"{dias_efetivos} dias úteis × {meta_casa_diaria:.0f}kg"
    )

    c4.metric(
        "Dias Acima da Meta",
        f"{dias_acima} de {dias_trabalhados}",
        "dias trabalhados"
    )

    c5.metric(
        "Necessário / Dia",
        f"{necessario_dia:,.0f} kg/dia",
        f"{dias_restantes} dias úteis restantes",
        delta_color="inverse"
    )

    st.divider()

    # -------------------------------------------------------------------------
    # GRÁFICO DE BARRAS: PRODUÇÃO DIÁRIA VS META
    # -------------------------------------------------------------------------
    st.markdown(f"##### 📈 Produção Diária vs Meta — {mes_ano.strftime('%B/%Y').title()}")

    if not df_prod.empty:
        df_prod['data_dt'] = pd.to_datetime(df_prod['data'])
        df_prod['data_fmt'] = df_prod['data_dt'].dt.strftime('%d/%m')

        # Definição das Cores Corporativas (Alinhadas a estilo.py / DAATEL)
        # Verde #01743d (Acima da Meta), Vermelho #dc2626 (Abaixo da Meta)
        cores_barras = [
            "#01743d" if val >= meta_casa_diaria else "#dc2626"
            for val in df_prod['producao_total_kg']
        ]

        fig = go.Figure()

        # Barras de Produção Diária
        fig.add_trace(go.Bar(
            x=df_prod['data_fmt'],
            y=df_prod['producao_total_kg'],
            marker_color=cores_barras,
            name="Produção Realizada (kg)",
            text=[f"{v:,.0f}kg" for v in df_prod['producao_total_kg']],
            textposition="outside"
        ))

        # Linha Horizontal da Meta Mínima da Casa (#0284c7 Sky Blue)
        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=len(df_prod) - 0.5,
            y0=meta_casa_diaria,
            y1=meta_casa_diaria,
            line=dict(color="#0284c7", width=3, dash="solid"),
        )

        fig.add_trace(go.Scatter(
            x=[df_prod['data_fmt'].iloc[0], df_prod['data_fmt'].iloc[-1]],
            y=[meta_casa_diaria, meta_casa_diaria],
            mode="lines",
            name=f"Meta Mínima ({meta_casa_diaria:.0f} kg)",
            line=dict(color="#0284c7", width=3)
        ))

        fig.update_layout(
            font=dict(family="Outfit, sans-serif", size=12, color="#1e293b"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f8fafc",
            margin=dict(l=20, r=20, t=30, b=30),
            xaxis=dict(title="Dia do Mês", showgrid=False),
            yaxis=dict(title="Produção (kg)", showgrid=True, gridcolor="#e2e8f0"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=380
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Nenhuma pesagem gravada no mês selecionado.")

    st.divider()

    # -------------------------------------------------------------------------
    # CARDS INFERIORES: MÉDIAS DE PRESENÇAS E SELECIONADORAS
    # -------------------------------------------------------------------------
    b1, b2 = st.columns(2)

    with b1:
        st.markdown("""
        <div style='background:#ffffff; border-left:5px solid #01743d; padding:15px; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'>
            <div style='font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase;'>Média de Presentes / Dia</div>
            <div style='font-size:24px; color:#0f172a; font-weight:700;'>{:.1f}</div>
            <div style='font-size:11px; color:#94a3b8;'>selecionadoras por dia útil trabalhado</div>
        </div>
        """.format(media_presentes_dia), unsafe_allow_html=True)

    with b2:
        st.markdown("""
        <div style='background:#ffffff; border-left:5px solid #0284c7; padding:15px; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'>
            <div style='font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase;'>Média de Produção por Selecionadora</div>
            <div style='font-size:24px; color:#0f172a; font-weight:700;'>{:.1f} kg</div>
            <div style='font-size:11px; color:#94a3b8;'>média individual diária no mês</div>
        </div>
        """.format(media_prod_selecionadora), unsafe_allow_html=True)
