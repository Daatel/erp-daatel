# components/selecao/mesa.py
# Aba 2 — Mesa de Seleção (presença + pesagem + descarte)

import streamlit as st
from datetime import date

from .queries import (
    SQL_SELECIONADORAS_ATIVAS,
    SQL_INSERIR_PRESENCA,
    SQL_LIMPAR_PRESENCA_DIA,
    SQL_PRESENCAS_DO_DIA,
    SQL_UPSERT_PESAGEM,
    SQL_UPSERT_APROVEITAMENTO,
    SQL_APROVEITAMENTO_DO_DIA,
)
from .pdf_folha import gerar_pdf_folha


def render_mesa_selecao():
    conn   = st.connection("supabase", type="sql")
    hoje   = date.today()
    uid    = st.session_state.get("usuario_id")
    passo  = st.session_state.get("selecao_passo", 1)

    # -- Cabeçalho --
    col_titulo, col_pdf = st.columns([3, 1])
    with col_titulo:
        st.markdown(f"**Mesa de seleção** — {hoje.strftime('%d/%m/%Y')}")

    # Botão PDF só aparece no passo 2
    with col_pdf:
        if passo == 2:
            presentes = st.session_state.get("selecao_presencas_confirmadas", [])
            if presentes and st.button("📄 Gerar folha do dia", key="btn_pdf"):
                pdf_bytes = gerar_pdf_folha(hoje, presentes)
                st.download_button(
                    label="⬇ Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"folha_selecao_{hoje.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key="dl_pdf",
                )

    st.divider()

    # -------------------------------------------------------------------------
    # PASSO 1 — Seleção de presentes
    # -------------------------------------------------------------------------
    if passo == 1:
        st.markdown("##### Passo 1 — Quem está presente hoje?")

        df_sel = conn.query(SQL_SELECIONADORAS_ATIVAS, ttl=300)

        if df_sel.empty:
            st.warning("Nenhuma selecionadora ativa cadastrada.")
            return

        opcoes = df_sel["nome"].tolist()
        selecionadas = st.multiselect(
            "Selecione as selecionadoras presentes",
            options=opcoes,
            key="selecao_multiselect",
            placeholder="Clique para selecionar...",
        )

        if selecionadas:
            df_presentes = df_sel[df_sel["nome"].isin(selecionadas)]
            cap_total = df_presentes["meta_kg_dia"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Presentes", f"{len(selecionadas)}")
            c2.metric("Capacidade do dia", f"{cap_total:,.0f} kg")
            c3.metric("Meta da casa", "500 kg")  # buscar de selecao_parametros

            st.divider()

            if st.button("✅ Confirmar presença", type="primary", key="btn_confirmar"):
                # Limpar presenças anteriores do dia e reinserir
                conn.execute(SQL_LIMPAR_PRESENCA_DIA, params={"data": hoje})
                for _, row in df_presentes.iterrows():
                    conn.execute(SQL_INSERIR_PRESENCA, params={
                        "data": hoje,
                        "selecionadora_id": int(row["id"]),
                        "usuario_id": uid,
                    })

                # Salvar na session_state para uso no PDF e pesagem
                st.session_state["selecao_presencas_confirmadas"] = df_presentes.to_dict("records")
                st.session_state["selecao_passo"] = 2
                st.rerun()
        else:
            st.info("Selecione ao menos uma selecionadora para continuar.")

    # -------------------------------------------------------------------------
    # PASSO 2 — Pesagem + Descarte
    # -------------------------------------------------------------------------
    elif passo == 2:
        presentes = st.session_state.get("selecao_presencas_confirmadas", [])

        if not presentes:
            st.warning("Presença não confirmada. Refaça o passo 1.")
            if st.button("↩ Refazer presença"):
                st.session_state["selecao_passo"] = 1
                st.rerun()
            return

        cap_total = sum(p["meta_kg_dia"] for p in presentes)
        c1, c2, c3 = st.columns(3)
        c1.metric("Presentes hoje", len(presentes))
        c2.metric("Capacidade do dia", f"{cap_total:,.0f} kg")
        c3.metric("Meta da casa", "500 kg")

        st.divider()

        # -- Passo 2a: Pesagem individual --
        st.markdown("##### Passo 2 — Pesagem individual")

        pesos = {}
        for p in presentes:
            col_nome, col_meta, col_peso, col_pct = st.columns([3, 1, 2, 2])
            with col_nome:
                st.write(p["nome"])
            with col_meta:
                st.caption(f"Meta: {p['meta_kg_dia']:.0f} kg")
            with col_peso:
                peso = st.number_input(
                    "kg",
                    min_value=0.0,
                    step=0.5,
                    key=f"peso_{p['id']}",
                    label_visibility="collapsed",
                )
                pesos[p["id"]] = {"peso": peso, "meta": p["meta_kg_dia"]}
            with col_pct:
                if peso > 0:
                    pct = peso / p["meta_kg_dia"] * 100
                    cor = "🟢" if pct >= 100 else "🟡" if pct >= 80 else "🔴"
                    st.caption(f"{cor} {pct:.0f}%")
                else:
                    st.caption("—")

        st.divider()

        # -- Passo 2b: Descarte x 2ª Linha --
        st.markdown("##### Passo 3 — Descarte × 2ª linha")

        col_nobre, col_segunda, col_descarte = st.columns(3)
        with col_nobre:
            peso_nobre = st.number_input("Alho nobre (kg)", min_value=0.0, step=0.5, key="d_nobre")
        with col_segunda:
            peso_segunda = st.number_input("2ª linha — Bombona (kg)", min_value=0.0, step=0.5, key="d_segunda")
        with col_descarte:
            peso_descarte = st.number_input("Descarte — Lixo (kg)", min_value=0.0, step=0.5, key="d_descarte")

        peso_total_lote = peso_nobre + peso_segunda + peso_descarte
        if peso_total_lote > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total do lote", f"{peso_total_lote:,.1f} kg")
            c2.metric("% Nobre",   f"{peso_nobre / peso_total_lote * 100:.1f}%")
            c3.metric("% 2ª linha", f"{peso_segunda / peso_total_lote * 100:.1f}%")
            c4.metric("% Descarte", f"{peso_descarte / peso_total_lote * 100:.1f}%")

        st.divider()

        # -- Ações --
        col_refazer, col_spacer, col_salvar = st.columns([2, 4, 2])

        with col_refazer:
            if st.button("↩ Refazer presença", key="btn_refazer"):
                st.session_state["selecao_passo"] = 1
                st.session_state["selecao_presencas_confirmadas"] = []
                st.rerun()

        with col_salvar:
            if st.button("💾 Salvar lançamentos", type="primary", key="btn_salvar"):
                erros = []

                # Salvar pesagens
                for sid, dados in pesos.items():
                    if dados["peso"] > 0:
                        try:
                            conn.execute(SQL_UPSERT_PESAGEM, params={
                                "data": hoje,
                                "selecionadora_id": sid,
                                "peso_kg": dados["peso"],
                                "meta_esperada_kg": dados["meta"],
                                "usuario_id": uid,
                            })
                        except Exception as e:
                            erros.append(f"Pesagem selecionadora {sid}: {e}")

                # Salvar aproveitamento
                if peso_total_lote > 0:
                    try:
                        conn.execute(SQL_UPSERT_APROVEITAMENTO, params={
                            "data": hoje,
                            "peso_nobre_kg": peso_nobre,
                            "peso_segunda_linha_kg": peso_segunda,
                            "peso_descarte_kg": peso_descarte,
                            "usuario_id": uid,
                        })
                    except Exception as e:
                        erros.append(f"Aproveitamento: {e}")

                if erros:
                    for err in erros:
                        st.error(err)
                else:
                    st.success("Lançamentos do dia salvos com sucesso.")
