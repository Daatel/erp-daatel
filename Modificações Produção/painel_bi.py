# components/selecao/painel_bi.py
# Aba 1 — Painel de Produção (BI mensal)

import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, timedelta
import calendar

from .queries import (
    SQL_PRODUCAO_DIARIA_MES,
    SQL_KPIS_MES,
    SQL_MEDIA_PRESENTES_MES,
)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def _label_mes(d: date) -> str:
    return f"{MESES_PT[d.month - 1]} {d.year}"


def _mes_anterior(d: date) -> date:
    primeiro = d.replace(day=1)
    return (primeiro - timedelta(days=1)).replace(day=1)


def _mes_seguinte(d: date) -> date:
    ultimo = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return (ultimo + timedelta(days=1)).replace(day=1)


def _cor_necessario(necessario: float, meta_casa: float, capacidade_historica: float) -> str:
    """Cor semântica do card Necessário/dia."""
    if necessario <= meta_casa:
        return "normal"        # verde implícito
    if necessario <= capacidade_historica * 1.1:
        return "off"           # laranja
    return "inverse"           # vermelho


# --------------------------------------------------------------------------
# Render principal
# --------------------------------------------------------------------------

def render_painel_bi():
    conn = st.connection("supabase", type="sql")  # ajustar conforme projeto

    # -- Seletor de mês --
    col_prev, col_mes, col_next = st.columns([1, 4, 1])
    mes_ano: date = st.session_state["selecao_mes_ano"]

    with col_prev:
        if st.button("◀", key="bi_prev"):
            st.session_state["selecao_mes_ano"] = _mes_anterior(mes_ano)
            st.rerun()

    with col_mes:
        st.markdown(
            f"<h3 style='text-align:center; margin:0'>{_label_mes(mes_ano)}</h3>",
            unsafe_allow_html=True,
        )

    with col_next:
        if st.button("▶", key="bi_next"):
            st.session_state["selecao_mes_ano"] = _mes_seguinte(mes_ano)
            st.rerun()

    st.divider()

    # -- Buscar KPIs --
    df_kpis = conn.query(SQL_KPIS_MES, params={"mes_ano": mes_ano}, ttl=60)

    if df_kpis.empty:
        st.info(f"Sem dados lançados em {_label_mes(mes_ano)}.")
        return

    kpi = df_kpis.iloc[0]
    realizado       = float(kpi["realizado_kg"] or 0)
    projetado       = float(kpi["projetado_kg"] or 0)
    meta_mensal     = float(kpi["meta_mensal_kg"] or 0)
    meta_diaria     = float(kpi["meta_diaria_casa_kg"] or 0)
    dias_trab       = int(kpi["dias_trabalhados"] or 0)
    dias_uteis      = int(kpi["dias_uteis_efetivos"] or 0)
    dias_acima      = int(kpi["dias_acima_meta"] or 0)
    necessario_dia  = float(kpi["necessario_por_dia_kg"] or 0)

    # -- Cards de KPI --
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "Realizado no mês",
            f"{realizado:,.0f} kg",
            help=f"Até {dias_trab} dias trabalhados"
        )

    with c2:
        delta_proj = projetado - meta_mensal
        st.metric(
            "Projetado até fim",
            f"{projetado:,.0f} kg",
            delta=f"{delta_proj:+,.0f} kg vs meta",
            delta_color="normal" if delta_proj >= 0 else "inverse",
        )

    with c3:
        st.metric(
            "Meta total do mês",
            f"{meta_mensal:,.0f} kg",
            help=f"{dias_uteis} dias úteis × {meta_diaria:,.0f} kg/dia"
        )

    with c4:
        st.metric(
            "Dias acima da meta",
            f"{dias_acima} de {dias_trab}",
            help="Dias em que a produção superou a meta mínima da casa"
        )

    with c5:
        dias_restantes = dias_uteis - dias_trab
        st.metric(
            "Necessário/dia",
            f"{necessario_dia:,.0f} kg/dia",
            delta=f"{dias_restantes} dias restantes",
            delta_color="off",
        )

    st.divider()

    # -- Gráfico de barras diário --
    df_prod = conn.query(
        SQL_PRODUCAO_DIARIA_MES,
        params={"mes_ano": mes_ano},
        ttl=60,
    )

    if df_prod.empty:
        st.info("Nenhum lançamento encontrado para este mês.")
        return

    df_prod["data"] = pd.to_datetime(df_prod["data"])
    df_prod["dia"]  = df_prod["data"].dt.strftime("%d/%m")
    df_prod["cor"]  = df_prod["producao_total_kg"].apply(
        lambda v: "Acima da meta" if v >= meta_diaria else "Abaixo da meta"
    )

    # Linha de meta mínima
    df_meta = df_prod[["dia"]].copy()
    df_meta["valor"] = meta_diaria
    df_meta["tipo"]  = "Meta mínima"

    # Linha de necessário/dia (apenas dias futuros — não há dados futuros no df_prod,
    # mas mantemos a estrutura para quando for usado com dados parciais do mês corrente)
    df_nec = df_prod[["dia"]].iloc[-1:].copy()
    df_nec = pd.DataFrame({
        "dia": [df_prod["dia"].iloc[-1]],
        "valor": [necessario_dia],
        "tipo": ["Necessário/dia"],
    })

    barras = (
        alt.Chart(df_prod)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("dia:O", axis=alt.Axis(labelAngle=-45, title="")),
            y=alt.Y("producao_total_kg:Q", axis=alt.Axis(title="kg"), scale=alt.Scale(domainMin=0)),
            color=alt.Color(
                "cor:N",
                scale=alt.Scale(
                    domain=["Acima da meta", "Abaixo da meta"],
                    range=["#97C459", "#F09595"],
                ),
                legend=alt.Legend(title=""),
            ),
            tooltip=[
                alt.Tooltip("dia:O", title="Data"),
                alt.Tooltip("producao_total_kg:Q", title="Produção (kg)", format=",.0f"),
                alt.Tooltip("n_presentes:Q", title="Presentes"),
                alt.Tooltip("media_por_selecionadora_kg:Q", title="Média/selecionadora (kg)", format=".1f"),
            ],
        )
    )

    linha_meta = (
        alt.Chart(df_meta)
        .mark_line(color="#2a78d6", strokeWidth=1.5)
        .encode(
            x=alt.X("dia:O"),
            y=alt.Y("valor:Q"),
        )
    )

    linha_nec = (
        alt.Chart(df_nec)
        .mark_rule(color="#BA7517", strokeDash=[5, 4], strokeWidth=1.5)
        .encode(y=alt.Y("valor:Q"))
    )

    chart = (barras + linha_meta + linha_nec).properties(
        height=260,
        title=f"Produção diária — {_label_mes(mes_ano)}",
    ).configure_axis(
        grid=True,
        gridColor="#e8e7e0",
    ).configure_view(strokeWidth=0)

    st.altair_chart(chart, use_container_width=True)

    # -- Cards inferiores --
    df_media = conn.query(
        SQL_MEDIA_PRESENTES_MES,
        params={"mes_ano": mes_ano},
        ttl=60,
    )

    if not df_media.empty:
        m = df_media.iloc[0]
        c6, c7 = st.columns(2)
        with c6:
            st.metric("Média de presentes/dia", f"{m['media_presentes_dia']} selecionadoras")
        with c7:
            st.metric("Média de produção por selecionadora", f"{m['media_kg_por_selecionadora']} kg")
