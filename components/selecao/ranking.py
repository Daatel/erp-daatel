# components/selecao/ranking.py
# Aba de Ranking de Selecionadoras + Raio-X / Histórico Individual

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from database import fetch_all
from .queries_ranking import SQL_RANKING_SELECIONADORAS, SQL_HISTORICO_INDIVIDUAL, SQL_PRESENCA_INDIVIDUAL
from .pdf_folha import obter_primeiro_nome

PERIODOS = {
    "Mês Atual":       "mes",
    "Últimos 30 dias": 30,
    "Últimos 60 dias": 60,
    "Últimos 90 dias": 90,
}

TENDENCIA_TEXTO = {
    "subindo": "Subindo (+)",
    "estavel": "Estável (=)",
    "caindo":  "Caindo (-)",
    "neutro":  "Sem Histórico",
}

TENDENCIA_COR = {
    "subindo": "color: #01743d; font-weight: 600;",
    "estavel": "color: #64748b;",
    "caindo":  "color: #dc2626; font-weight: 600;",
    "neutro":  "color: #94a3b8;",
}


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


def _badge_nivel_html(nivel: str) -> str:
    cls = "badge-nivel-a" if nivel == "A" else ("badge-nivel-b" if nivel == "B" else "badge-nivel-teste")
    return f"<span class='{cls}'>Nível {nivel}</span>"


def _render_historico_individual(selecionadora: dict, inicio: date, fim: date):
    p_nome = obter_primeiro_nome(selecionadora['nome'])
    st.markdown(f"#### Histórico Individual: {p_nome}")
    st.caption(f"Nível {selecionadora['nivel_classificacao']} | Vínculo: {selecionadora.get('vinculo') or 'CLT'} | Meta: {selecionadora['meta_kg_dia']:.0f} kg/dia")

    str_ini = inicio.strftime("%Y-%m-%d")
    str_fim = fim.strftime("%Y-%m-%d")

    df = fetch_all(SQL_HISTORICO_INDIVIDUAL, (selecionadora["id"], str_ini, str_fim))
    df_pres = fetch_all(SQL_PRESENCA_INDIVIDUAL, (selecionadora["id"], str_ini, str_fim))

    if df.empty:
        st.info("Sem lançamentos de pesagem registrados no período selecionado.")
        return

    df["data_dt"] = pd.to_datetime(df["data"])
    df["dia_fmt"] = df["data_dt"].dt.strftime("%d/%m")
    meta = float(selecionadora["meta_kg_dia"])

    total_prod = float(df["peso_kg"].sum())
    media_dia = float(df["peso_kg"].mean())
    media_pct = float(df["pct_atingimento"].astype(float).mean())
    dias_acima = int((df["pct_atingimento"].astype(float) >= 100).sum())
    dias_presentes = len(df_pres) if not df_pres.empty else len(df)

    # 5 Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dias Presentes", f"{dias_presentes}")
    c2.metric("Produção Total", f"{total_prod:,.0f} kg")
    c3.metric("Média / Dia", f"{media_dia:.1f} kg")
    c4.metric("Atingimento Médio", f"{media_pct:.1f}%")
    c5.metric("Dias Acima da Meta", f"{dias_acima} de {len(df)}")

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Gráfico Plotly Individual
    cores = ["#01743d" if val >= meta else "#dc2626" for val in df["peso_kg"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["dia_fmt"],
        y=df["peso_kg"],
        marker_color=cores,
        name="Produção (kg)",
        text=[f"{v:,.0f}kg" for v in df["peso_kg"]],
        textposition="outside"
    ))

    # Linha de Meta do Nível
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(df) - 0.5,
        y0=meta,
        y1=meta,
        line=dict(color="#0284c7", width=2, dash="solid")
    )

    fig.update_layout(
        font=dict(family="Outfit, sans-serif", size=11, color="#1e293b"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8fafc",
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="kg", showgrid=True, gridcolor="#e2e8f0"),
        height=260,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhe
    with st.expander("Ver detalhe das pesagens dia a dia"):
        df_det = df[["dia_fmt", "peso_kg", "meta_esperada_kg", "pct_atingimento"]].copy()
        df_det.columns = ["Data", "Produção (kg)", "Meta (kg)", "Atingimento (%)"]
        df_det["Atingimento (%)"] = df_det["Atingimento (%)"].apply(lambda v: f"{float(v):.1f}%" if pd.notnull(v) else "—")
        st.dataframe(df_det, use_container_width=True, hide_index=True)


def render_ranking():
    col_p, col_v, col_o = st.columns(3)
    with col_p:
        p_label = st.selectbox("Período", list(PERIODOS.keys()), key="rk_periodo")
        periodo = PERIODOS[p_label]
    with col_v:
        v_filtro = st.selectbox("Vínculo", ["Todos", "CLT", "Diarista"], key="rk_vinculo")
    with col_o:
        o_filtro = st.selectbox(
            "Ordenar por",
            ["% Atingimento Médio", "Produção Total (kg)", "Média/dia (kg)", "Dias Presentes"],
            key="rk_ordem"
        )

    inicio, meio, fim = _intervalo(periodo)
    str_ini = inicio.strftime("%Y-%m-%d")
    str_meio = meio.strftime("%Y-%m-%d")
    str_fim = fim.strftime("%Y-%m-%d")

    df = fetch_all(SQL_RANKING_SELECIONADORAS, (str_ini, str_fim, str_meio, str_fim, str_ini, str_meio))

    if df.empty:
        st.info("Sem dados de pesagem no período selecionado.")
        return

    if v_filtro != "Todos":
        df = df[df["vinculo"] == v_filtro]

    # Ordenação
    order_col = "media_atingimento_pct" if "Atingimento" in o_filtro else (
        "producao_total_kg" if "Total" in o_filtro else (
            "media_dia_kg" if "Média" in o_filtro else "dias_presentes"
        )
    )
    df = df.sort_values(order_col, ascending=False).reset_index(drop=True)

    # 4 Cards do Grupo
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selecionadoras", len(df))
    c2.metric("Atingimento Médio", f"{df['media_atingimento_pct'].mean():.1f}%")
    c3.metric("Maior Produção", f"{df['producao_total_kg'].max():,.0f} kg")
    c4.metric("Média Geral/Dia", f"{df['media_dia_kg'].mean():.1f} kg")

    st.divider()

    st.markdown("##### Ranking do Período")

    for i, row in df.iterrows():
        p_nome = obter_primeiro_nome(row["nome"])
        tend_txt = TENDENCIA_TEXTO.get(row["tendencia"], "—")
        tend_style = TENDENCIA_COR.get(row["tendencia"], "")
        pct_atg = float(row["media_atingimento_pct"] or 0)

        badge_html = _badge_nivel_html(row["nivel_classificacao"])

        with st.container():
            c_pos, c_nome, c_nivel, c_dias, c_prod, c_media, c_atg, c_tend, c_act = st.columns([0.4, 2.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.2, 1.2])

            c_pos.markdown(f"**#{i+1}**")
            c_nome.markdown(f"**{p_nome}**")
            c_nivel.markdown(badge_html, unsafe_allow_html=True)
            c_dias.caption(f"{int(row['dias_presentes'])} dias")
            c_prod.markdown(f"**{row['producao_total_kg']:,.0f} kg**")
            c_media.caption(f"{float(row['media_dia_kg']):.1f} kg/dia")

            cor_atg = "#01743d" if pct_atg >= 100 else ("#b45309" if pct_atg >= 80 else "#dc2626")
            c_atg.markdown(f"<span style='color:{cor_atg}; font-weight:700;'>{pct_atg:.1f}%</span>", unsafe_allow_html=True)
            c_tend.markdown(f"<span style='{tend_style}'>{tend_txt}</span>", unsafe_allow_html=True)

            with c_act:
                if st.button("Ver Histórico", key=f"btn_hist_{row['id']}"):
                    st.session_state["selecionadora_hist"] = row.to_dict()

            st.markdown("<hr style='margin:4px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)

    # Exibe Histórico Individual se selecionado
    sel_hist = st.session_state.get("selecionadora_hist")
    if sel_hist:
        st.divider()
        col_close, _ = st.columns([1, 5])
        if col_close.button("Fechar Histórico", key="btn_close_hist"):
            st.session_state.pop("selecionadora_hist", None)
            st.rerun()
        _render_historico_individual(sel_hist, inicio, fim)
