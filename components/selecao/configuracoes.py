# components/selecao/configuracoes.py
# Aba 3 — Configurações (Restrito ao perfil ADMIN)

import streamlit as st
import pandas as pd
from datetime import date
import calendar
from database import fetch_all, run_query, db_transaction
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

def _dias_uteis_mes(mes_ano: date, excecoes_df) -> tuple[int, int]:
    """Retorna (dias_calculados, dias_efetivos) para o mês."""
    _, n_dias = calendar.monthrange(mes_ano.year, mes_ano.month)
    todas = [date(mes_ano.year, mes_ano.month, d) for d in range(1, n_dias + 1)]

    # Dias calculados: de segunda a sexta
    dias_calc = sum(1 for d in todas if d.weekday() < 5)

    remover = 0
    adicionar = 0
    if not excecoes_df.empty:
        for _, r in excecoes_df.iterrows():
            dt_exc = pd.to_datetime(r['data']).date() if pd.notnull(r['data']) else None
            if dt_exc and dt_exc.year == mes_ano.year and dt_exc.month == mes_ano.month:
                if r['tipo'] == 'REMOVER':
                    remover += 1
                elif r['tipo'] == 'ADICIONAR':
                    adicionar += 1

    dias_ef = dias_calc - remover + adicionar
    return dias_calc, max(dias_ef, 0)


def render_configuracoes():
    user_role = st.session_state.get("user_role", "OPERADOR")
    if user_role != "ADMIN":
        st.warning("Acesso Restrito: Apenas administradores podem alterar as configurações de metas e calendário.")
        return

    hoje = date.today()
    mes_ano = date(hoje.year, hoje.month, 1)
    str_mes = mes_ano.strftime("%Y-%m-01")

    # -------------------------------------------------------------------------
    # 1. METAS POR NÍVEL
    # -------------------------------------------------------------------------
    st.markdown("##### Metas por Nível de Selecionadora")

    df_metas = fetch_all(SQL_METAS_NIVEL)
    novas_metas = {}

    with st.form("form_metas_nivel"):
        if not df_metas.empty:
            for _, r in df_metas.iterrows():
                nv = r['nivel']
                meta_val = float(r['meta_kg_dia'])
                desc_val = r['descricao']
                c1, c2, c3 = st.columns([1, 3, 2])
                c1.markdown(f"**Nível {nv}**")
                c2.caption(desc_val)
                val = c3.number_input(f"Meta kg/dia ({nv})", min_value=1.0, value=meta_val, step=5.0, format="%.0f", label_visibility="collapsed")
                novas_metas[nv] = (val, desc_val)
        else:
            for nv, desc_val in NIVEL_DESC.items():
                meta_default = 90.0 if nv == 'A' else (70.0 if nv == 'B' else 50.0)
                c1, c2, c3 = st.columns([1, 3, 2])
                c1.markdown(f"**Nível {nv}**")
                c2.caption(desc_val)
                val = c3.number_input(f"Meta kg/dia ({nv})", min_value=1.0, value=meta_default, step=5.0, format="%.0f", label_visibility="collapsed")
                novas_metas[nv] = (val, desc_val)

        salvar_metas = st.form_submit_button("Salvar Metas por Nível", type="primary")

    if salvar_metas:
        try:
            with db_transaction() as conn:
                for nv, (val, desc_val) in novas_metas.items():
                    run_query(SQL_UPSERT_META_NIVEL, (nv, val, desc_val))
            st.success("Metas por nível salvas.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar metas: {e}")

    st.divider()

    # -------------------------------------------------------------------------
    # 2. META MÍNIMA DA CASA
    # -------------------------------------------------------------------------
    st.markdown("##### Meta Mínima da Casa")
    df_params = fetch_all(SQL_PARAMETROS_MES, (str_mes, str_mes))
    meta_casa_atual = float(df_params.iloc[0]['meta_diaria_casa_kg']) if not df_params.empty else 500.0

    with st.form("form_meta_casa"):
        col_m1, col_m2 = st.columns([2, 3])
        nova_meta_casa = col_m1.number_input("Meta Mínima Diária da Fábrica (kg/dia)", min_value=1.0, value=meta_casa_atual, step=50.0, format="%.0f")
        col_m2.caption("Produção mínima diária para cobrir custos fixos.")
        salvar_casa = st.form_submit_button("Salvar Meta da Casa", type="primary")

    df_excecoes = fetch_all(SQL_EXCECOES_MES)
    dias_calc, dias_efetivos = _dias_uteis_mes(mes_ano, df_excecoes)

    if salvar_casa:
        try:
            with db_transaction() as conn:
                run_query(SQL_UPSERT_PARAMETROS, (str_mes, nova_meta_casa, dias_calc, dias_efetivos))
            st.success("Meta da casa salva.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar meta da casa: {e}")

    st.divider()

    # -------------------------------------------------------------------------
    # 3. CALENDÁRIO E EXCEÇÕES DO MÊS
    # -------------------------------------------------------------------------
    st.markdown(f"##### Calendário do Mês — {mes_ano.strftime('%m/%Y')}")
    st.markdown(f"**Dias úteis calculados:** `{dias_calc} dias` *(segunda a sexta)*")

    st.markdown("###### Exceções do Mês (Feriados / Sábados Trabalhados)")

    if not df_excecoes.empty:
        for _, r in df_excecoes.iterrows():
            exc_id = r['id']
            dt_str = pd.to_datetime(r['data']).strftime('%d/%m/%Y')
            t_icon = "Feriado / Folga" if r['tipo'] == 'REMOVER' else "Sábado Trabalhado"
            
            cx1, cx2 = st.columns([4, 1])
            cx1.markdown(f"• `{dt_str}` — **{t_icon}** ({r['descricao'] or 'Sem descrição'})")
            if cx2.button("Remover", key=f"del_exc_{exc_id}"):
                run_query(SQL_REMOVER_EXCECAO, (exc_id,))
                st.rerun()

    with st.form("form_nova_excecao"):
        col_e1, col_e2, col_e3 = st.columns(3)
        dt_exc_in = col_e1.date_input("Data da Exceção", value=hoje)
        tipo_exc_in = col_e2.selectbox("Tipo", ["Remover dia (Feriado)", "Adicionar dia (Sábado trabalhado)"])
        desc_exc_in = col_e3.text_input("Descrição", placeholder="Ex: Feriado Municipal")
        add_exc_btn = st.form_submit_button("Adicionar Exceção")

    if add_exc_btn:
        t_code = "REMOVER" if "Remover" in tipo_exc_in else "ADICIONAR"
        try:
            run_query(SQL_INSERIR_EXCECAO, (dt_exc_in.strftime("%Y-%m-%d"), t_code, desc_exc_in))
            df_excecoes_upd = fetch_all(SQL_EXCECOES_MES)
            d_c, d_e = _dias_uteis_mes(mes_ano, df_excecoes_upd)
            run_query(SQL_UPSERT_PARAMETROS, (str_mes, nova_meta_casa, d_c, d_e))
            st.success("Exceção adicionada.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar exceção: {e}")

    meta_total_mes = nova_meta_casa * dias_efetivos
    st.info(f"Dias úteis efetivos no mês: {dias_efetivos} dias | Meta Total do Mês: {meta_total_mes:,.0f} kg")
