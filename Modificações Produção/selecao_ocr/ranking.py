# components/selecao/ranking.py
# Aba 4 — Ranking de Selecionadoras + Histórico Individual

import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, timedelta

from .queries import SQL_RANKING_SELECIONADORAS, SQL_HISTORICO_INDIVIDUAL, SQL_PRESENCA_INDIVIDUAL

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

PERIODOS = {
    "Mês atual":    "mes",
    "Últimos 30 dias": 30,
    "Últimos 60 dias": 60,
    "Últimos 90 dias": 90,
}

TENDENCIA_ICON = {
    "subindo": "↑",
    "estavel": "→",
    "caindo":  "↓",
    "neutro":  "—",
}

TENDENCIA_COR = {
    "subindo": "color: #3B6D11",
    "estavel": "color: #888780",
    "caindo":  "color: #A32D2D",
    "neutro":  "color: #888780",
}

NIVEL_LABEL = {"A": "Nível A", "B": "Nível B", "Teste": "Teste"}


def _intervalo(periodo) -> tuple[date, date, date]:
    """Retorna (data_inicio, data_meio, data_fim)."""
    hoje = date.today()
    if periodo == "mes":
        inicio = hoje.replace(day=1)
        meio   = inicio + timedelta(days=14)
        fim    = hoje
    else:
        fim    = hoje
        inicio = hoje - timedelta(days=int(periodo))
        meio   = inicio + timedelta(days=int(periodo) // 2)
    return inicio, meio, fim


def _badge_nivel(nivel: str) -> str:
    cores = {"A": "🟢", "B": "🔵", "Teste": "⚪"}
    return f"{cores.get(nivel, '⚪')} {NIVEL_LABEL.get(nivel, nivel)}"


def _colorir_pct(val):
    """Estilo condicional para coluna de atingimento."""
    try:
        v = float(str(val).replace("%", ""))
        if v >= 100: return "color: #3B6D11; font-weight: 500"
        if v >= 80:  return "color: #854F0B"
        return "color: #A32D2D"
    except Exception:
        return ""


def _colorir_tendencia(val):
    icon = str(val)
    if "↑" in icon: return "color: #3B6D11; font-weight: 500"
    if "↓" in icon: return "color: #A32D2D; font-weight: 500"
    return "color: #888780"


# --------------------------------------------------------------------------
# Histórico individual
# --------------------------------------------------------------------------

def _render_historico(conn, selecionadora: dict, inicio: date, fim: date):
    st.markdown(f"### {selecionadora['nome']}")
    st.caption(
        f"{_badge_nivel(selecionadora['nivel_classificacao'])} · "
        f"{selecionadora['vinculo']} · "
        f"Meta: {selecionadora['meta_kg_dia']:.0f} kg/dia"
    )
    st.divider()

    df = conn.query(
        SQL_HISTORICO_INDIVIDUAL,
        params={
            "selecionadora_id": selecionadora["id"],
            "data_inicio": inicio,
            "data_fim": fim,
        },
        ttl=60,
    )

    df_pres = conn.query(
        SQL_PRESENCA_INDIVIDUAL,
        params={
            "selecionadora_id": selecionadora["id"],
            "data_inicio": inicio,
            "data_fim": fim,
        },
        ttl=60,
    )

    if df.empty:
        st.info("Sem lançamentos no período selecionado.")
        return

    df["data"] = pd.to_datetime(df["data"])
    df["dia"]  = df["data"].dt.strftime("%d/%m")
    df["cor"]  = df["pct_atingimento"].apply(
        lambda v: "Acima da meta" if float(v or 0) >= 100 else "Abaixo da meta"
    )
    meta = float(selecionadora["meta_kg_dia"])

    # -- KPIs individuais --
    total_prod   = df["peso_kg"].sum()
    media_dia    = df["peso_kg"].mean()
    media_pct    = df["pct_atingimento"].astype(float).mean()
    dias_acima   = (df["pct_atingimento"].astype(float) >= 100).sum()
    dias_present = len(df_pres) if not df_pres.empty else len(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dias presentes",     dias_present)
    c2.metric("Produção total",     f"{total_prod:,.0f} kg")
    c3.metric("Média/dia",          f"{media_dia:.1f} kg")
    c4.metric("Atingimento médio",  f"{media_pct:.1f}%")
    c5.metric("Dias acima da meta", f"{dias_acima} de {len(df)}")

    st.divider()

    # -- Gráfico de barras individual --
    df_meta = df[["dia"]].copy()
    df_meta["meta"] = meta

    barras = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("dia:O", axis=alt.Axis(labelAngle=-45, title="")),
            y=alt.Y("peso_kg:Q", axis=alt.Axis(title="kg"), scale=alt.Scale(domainMin=0)),
            color=alt.Color(
                "cor:N",
                scale=alt.Scale(
                    domain=["Acima da meta", "Abaixo da meta"],
                    range=["#97C459", "#F09595"],
                ),
                legend=alt.Legend(title=""),
            ),
            tooltip=[
                alt.Tooltip("dia:O",              title="Data"),
                alt.Tooltip("peso_kg:Q",          title="Produção (kg)", format=",.1f"),
                alt.Tooltip("pct_atingimento:Q",  title="Atingimento (%)", format=".1f"),
            ],
        )
    )

    linha_meta = (
        alt.Chart(df_meta)
        .mark_line(color="#2a78d6", strokeWidth=1.5)
        .encode(
            x=alt.X("dia:O"),
            y=alt.Y("meta:Q"),
        )
    )

    chart = (barras + linha_meta).properties(
        height=220,
        title=f"Produção diária — {selecionadora['nome']}",
    ).configure_axis(
        grid=True, gridColor="#e8e7e0",
    ).configure_view(strokeWidth=0)

    st.altair_chart(chart, use_container_width=True)

    # -- Tabela de detalhe --
    with st.expander("Ver detalhe dia a dia"):
        df_show = df[["dia", "peso_kg", "meta_esperada_kg", "pct_atingimento"]].copy()
        df_show.columns = ["Data", "Produção (kg)", "Meta (kg)", "Atingimento (%)"]
        df_show["Atingimento (%)"] = df_show["Atingimento (%)"].apply(
            lambda v: f"{float(v):.1f}%" if v is not None else "—"
        )
        st.dataframe(df_show, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------
# Render principal — Ranking
# --------------------------------------------------------------------------

def render_ranking():
    conn = st.connection("supabase", type="sql")

    # -- Filtros --
    col_periodo, col_vinculo, col_order = st.columns([2, 2, 2])

    with col_periodo:
        periodo_label = st.selectbox(
            "Período",
            options=list(PERIODOS.keys()),
            key="ranking_periodo",
        )
        periodo = PERIODOS[periodo_label]

    with col_vinculo:
        vinculo_filtro = st.selectbox(
            "Vínculo",
            options=["Todos", "CLT", "Diarista"],
            key="ranking_vinculo",
        )

    with col_order:
        ordenar_por = st.selectbox(
            "Ordenar por",
            options=[
                "% Atingimento médio",
                "Produção total (kg)",
                "Média/dia (kg)",
                "Dias presentes",
                "% Assiduidade",
            ],
            key="ranking_order",
        )

    inicio, meio, fim = _intervalo(periodo)

    # -- Buscar dados --
    df = conn.query(
        SQL_RANKING_SELECIONADORAS,
        params={
            "data_inicio": inicio,
            "data_meio":   meio,
            "data_fim":    fim,
        },
        ttl=60,
    )

    if df.empty:
        st.info("Sem dados no período selecionado.")
        return

    # -- Filtro de vínculo --
    if vinculo_filtro != "Todos":
        df = df[df["vinculo"] == vinculo_filtro]

    # -- Calcular assiduidade --
    n_dias_periodo = (fim - inicio).days + 1
    dias_uteis = max(1, sum(
        1 for i in range(n_dias_periodo)
        if (inicio + timedelta(days=i)).weekday() < 5
    ))
    df["pct_assiduidade"] = (df["dias_presentes"] / dias_uteis * 100).clip(upper=100)

    # -- Ordenação --
    order_map = {
        "% Atingimento médio":  ("media_atingimento_pct", False),
        "Produção total (kg)":  ("producao_total_kg",     False),
        "Média/dia (kg)":       ("media_dia_kg",          False),
        "Dias presentes":       ("dias_presentes",        False),
        "% Assiduidade":        ("pct_assiduidade",       False),
    }
    col_sort, asc = order_map[ordenar_por]
    df = df.sort_values(col_sort, ascending=asc).reset_index(drop=True)

    st.divider()

    # -- Cards de resumo do grupo --
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selecionadoras",      len(df))
    c2.metric("Média de atingimento", f"{df['media_atingimento_pct'].mean():.1f}%")
    c3.metric("Maior produção",      f"{df['producao_total_kg'].max():,.0f} kg")
    c4.metric("Assiduidade média",   f"{df['pct_assiduidade'].mean():.1f}%")

    st.divider()

    # -- Tabela de ranking --
    st.markdown("##### Ranking do período")

    for i, row in df.iterrows():
        tend_icon = TENDENCIA_ICON.get(row["tendencia"], "—")
        tend_cor  = TENDENCIA_COR.get(row["tendencia"], "")
        pct_atg   = float(row["media_atingimento_pct"] or 0)
        pct_ass   = float(row["pct_assiduidade"] or 0)
        cor_atg   = "#3B6D11" if pct_atg >= 100 else "#854F0B" if pct_atg >= 80 else "#A32D2D"
        cor_ass   = "#3B6D11" if pct_ass >= 90  else "#854F0B" if pct_ass >= 70  else "#A32D2D"

        with st.container():
            c_pos, c_nome, c_nivel, c_dias, c_ass, c_prod, c_media, c_atg, c_tend, c_acao = st.columns(
                [0.5, 2.5, 1, 1, 1, 1.2, 1, 1, 0.7, 1]
            )

            c_pos.markdown(f"**{i+1}**")
            c_nome.markdown(f"**{row['nome']}**")
            c_nivel.caption(_badge_nivel(row["nivel_classificacao"]))
            c_dias.metric("", f"{int(row['dias_presentes'])} dias", label_visibility="collapsed")
            c_ass.markdown(
                f"<span style='font-size:14px; {f'color:{cor_ass}'}; font-weight:500'>"
                f"{pct_ass:.0f}%</span>",
                unsafe_allow_html=True,
            )
            c_prod.markdown(
                f"<span style='font-size:14px; font-weight:500'>"
                f"{row['producao_total_kg']:,.0f} kg</span>",
                unsafe_allow_html=True,
            )
            c_media.caption(f"{float(row['media_dia_kg']):.1f} kg/dia")
            c_atg.markdown(
                f"<span style='font-size:14px; color:{cor_atg}; font-weight:500'>"
                f"{pct_atg:.0f}%</span>",
                unsafe_allow_html=True,
            )
            c_tend.markdown(
                f"<span style='font-size:18px; {tend_cor}'>{tend_icon}</span>",
                unsafe_allow_html=True,
            )
            with c_acao:
                if st.button("Ver histórico", key=f"hist_{row['id']}"):
                    st.session_state["ranking_selecionada"] = row.to_dict()

            st.markdown(
                "<hr style='margin:4px 0; border:none; border-top:0.5px solid var(--border)'>",
                unsafe_allow_html=True,
            )

    # -- Histórico individual (abre abaixo ao clicar) --
    sel = st.session_state.get("ranking_selecionada")
    if sel:
        st.divider()
        with st.container():
            col_fechar, _ = st.columns([1, 5])
            with col_fechar:
                if st.button("✕ Fechar histórico", key="fechar_hist"):
                    st.session_state.pop("ranking_selecionada", None)
                    st.rerun()
            _render_historico(conn, sel, inicio, fim)
