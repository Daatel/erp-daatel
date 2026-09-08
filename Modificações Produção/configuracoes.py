# components/selecao/configuracoes.py
# Aba 3 — Configurações (restrito ao perfil ADMIN)

import streamlit as st
from datetime import date, timedelta
import calendar
import numpy as np

from .queries import (
    SQL_METAS_NIVEL,
    SQL_UPSERT_META_NIVEL,
    SQL_PARAMETROS_MES,
    SQL_UPSERT_PARAMETROS,
    SQL_EXCECOES_MES,
    SQL_INSERIR_EXCECAO,
    SQL_REMOVER_EXCECAO,
)

NIVEL_DESC = {
    "A":     "Alta performance / assídua",
    "B":     "Rendimento padrão",
    "Teste": "Em treinamento / avaliação",
}

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def _dias_uteis_mes(mes_ano: date, excecoes: list) -> tuple[int, int]:
    """Retorna (dias_calculados, dias_efetivos) para o mês."""
    _, n_dias = calendar.monthrange(mes_ano.year, mes_ano.month)
    todas = [date(mes_ano.year, mes_ano.month, d) for d in range(1, n_dias + 1)]

    # Dias calculados: sem sábado e domingo
    dias_calc = sum(1 for d in todas if d.weekday() < 5)

    # Aplicar exceções
    remover  = sum(1 for e in excecoes if e["tipo"] == "REMOVER")
    adicionar = sum(1 for e in excecoes if e["tipo"] == "ADICIONAR")
    dias_ef  = dias_calc - remover + adicionar

    return dias_calc, max(dias_ef, 0)


def render_configuracoes():
    conn  = st.connection("supabase", type="sql")
    uid   = st.session_state.get("usuario_id")
    hoje  = date.today()
    mes_ano = date(hoje.year, hoje.month, 1)

    st.markdown("#### Configurações de produção")
    st.caption("Alterações aqui afetam os cálculos de meta e capacidade em todo o módulo.")
    st.divider()

    # -------------------------------------------------------------------------
    # 1. Metas por nível
    # -------------------------------------------------------------------------
    st.markdown("##### Metas por nível de selecionadora")

    df_metas = conn.query(SQL_METAS_NIVEL, ttl=60)
    novas_metas = {}

    if df_metas.empty:
        st.warning("Tabela selecao_metas_nivel sem dados. Executar migration.")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(df_metas.iterrows()):
            with cols[i]:
                val = st.number_input(
                    f"Nível {row['nivel']} — {NIVEL_DESC.get(row['nivel'], '')}",
                    min_value=0.0,
                    value=float(row["meta_kg_dia"]),
                    step=5.0,
                    format="%.0f",
                    key=f"meta_nivel_{row['nivel']}",
                    help=f"kg/dia para selecionadoras de nível {row['nivel']}",
                )
                novas_metas[row["nivel"]] = val
                st.caption(f"Atual: {row['meta_kg_dia']:.0f} kg/dia")

    if st.button("Salvar metas por nível", key="salvar_metas_nivel"):
        for nivel, val in novas_metas.items():
            conn.execute(SQL_UPSERT_META_NIVEL, params={
                "nivel": nivel,
                "meta_kg_dia": val,
                "descricao": NIVEL_DESC.get(nivel, ""),
                "usuario_id": uid,
            })
        st.success("Metas por nível salvas.")

    st.divider()

    # -------------------------------------------------------------------------
    # 2. Meta da casa
    # -------------------------------------------------------------------------
    st.markdown(f"##### Meta mínima da casa — {MESES_PT[mes_ano.month-1]} {mes_ano.year}")

    df_params = conn.query(SQL_PARAMETROS_MES, params={"mes_ano": mes_ano}, ttl=60)

    meta_casa_atual = float(df_params.iloc[0]["meta_diaria_casa_kg"]) if not df_params.empty else 500.0

    meta_casa = st.number_input(
        "Produção mínima diária para cobrir custos fixos (kg/dia)",
        min_value=0.0,
        value=meta_casa_atual,
        step=10.0,
        format="%.0f",
        key="meta_casa_input",
    )

    st.divider()

    # -------------------------------------------------------------------------
    # 3. Calendário — exceções do mês
    # -------------------------------------------------------------------------
    st.markdown(f"##### Calendário — {MESES_PT[mes_ano.month-1]} {mes_ano.year}")

    df_excecoes = conn.query(SQL_EXCECOES_MES, params={"mes_ano": mes_ano}, ttl=60)
    excecoes_list = df_excecoes.to_dict("records") if not df_excecoes.empty else []

    dias_calc, dias_ef = _dias_uteis_mes(mes_ano, excecoes_list)

    st.info(
        f"Dias úteis calculados automaticamente: **{dias_calc}** "
        f"(sem sábados e domingos) → com exceções: **{dias_ef} dias** — "
        f"meta mensal: **{meta_casa * dias_ef:,.0f} kg**"
    )

    # Listar exceções existentes
    if excecoes_list:
        st.markdown("**Exceções cadastradas:**")
        for exc in excecoes_list:
            tipo_icon = "➖" if exc["tipo"] == "REMOVER" else "➕"
            tipo_label = "Feriado/ponto facultativo" if exc["tipo"] == "REMOVER" else "Sábado trabalhado"
            col_exc, col_del = st.columns([5, 1])
            with col_exc:
                st.caption(f"{tipo_icon} {exc['data']} — {exc.get('descricao', tipo_label)}")
            with col_del:
                if st.button("✕", key=f"del_exc_{exc['id']}"):
                    conn.execute(SQL_REMOVER_EXCECAO, params={"id": exc["id"]})
                    st.rerun()
    else:
        st.caption("Nenhuma exceção cadastrada para este mês.")

    # Adicionar nova exceção
    st.markdown("**Adicionar exceção:**")
    col_data, col_tipo, col_desc, col_add = st.columns([2, 2, 3, 1])

    with col_data:
        data_exc = st.date_input(
            "Data",
            value=hoje,
            min_value=mes_ano,
            max_value=date(mes_ano.year, mes_ano.month,
                           calendar.monthrange(mes_ano.year, mes_ano.month)[1]),
            key="exc_data",
            label_visibility="collapsed",
        )
    with col_tipo:
        tipo_exc = st.selectbox(
            "Tipo",
            options=["REMOVER", "ADICIONAR"],
            format_func=lambda x: "Remover dia (feriado)" if x == "REMOVER" else "Adicionar dia (sáb. trabalhado)",
            key="exc_tipo",
            label_visibility="collapsed",
        )
    with col_desc:
        desc_exc = st.text_input(
            "Descrição",
            placeholder="ex: Feriado municipal",
            key="exc_desc",
            label_visibility="collapsed",
        )
    with col_add:
        if st.button("Adicionar", key="btn_add_exc"):
            conn.execute(SQL_INSERIR_EXCECAO, params={
                "data": data_exc,
                "tipo": tipo_exc,
                "descricao": desc_exc or None,
                "usuario_id": uid,
            })
            st.rerun()

    st.divider()

    # -- Salvar tudo --
    if st.button("💾 Salvar configurações do mês", type="primary", key="salvar_config"):
        _, dias_ef_final = _dias_uteis_mes(mes_ano, excecoes_list)
        conn.execute(SQL_UPSERT_PARAMETROS, params={
            "mes_ano": mes_ano,
            "meta_diaria_casa_kg": meta_casa,
            "dias_uteis_calculados": dias_calc,
            "dias_uteis_efetivos": dias_ef_final,
        })
        st.success("Configurações salvas.")
