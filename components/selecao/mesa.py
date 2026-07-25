# components/selecao/mesa.py
# Aba 2 — Mesa de Seleção (Presença, Pesagem por Selecionadora e Balanço de Descarte)

import streamlit as st
import pandas as pd
from datetime import date
from database import fetch_all, run_query, db_transaction
from .queries import (
    SQL_SELECIONADORAS_ATIVAS,
    SQL_LIMPAR_PRESENCA_DIA,
    SQL_INSERIR_PRESENCA,
    SQL_PRESENCAS_DO_DIA,
    SQL_UPSERT_PESAGEM,
    SQL_PESAGENS_DO_DIA,
    SQL_UPSERT_APROVEITAMENTO,
    SQL_APROVEITAMENTO_DO_DIA,
    SQL_PARAMETROS_MES,
)
from .pdf_folha import gerar_pdf_folha, obter_primeiro_nome


def _garantir_produtos_subprodutos(conn=None):
    """Garante que os produtos Alho 2ª Linha Bombona e Alho Nobre existam no cadastro."""
    df_bombona = fetch_all("SELECT id FROM produtos WHERE nome LIKE '%Bombona%' OR nome LIKE '%2ª Linha%' LIMIT 1")
    if df_bombona.empty:
        run_query("""
            INSERT INTO produtos (nome, unidade_medida, preco_venda_base, is_materia_prima, marca, custo_unidade)
            VALUES ('Alho Descascado 2ª Linha (Bombona)', 'Kg', 8.00, 1, 'Empório do Alho', 4.00)
        """)
        df_bombona = fetch_all("SELECT id FROM produtos WHERE nome LIKE '%Bombona%' OR nome LIKE '%2ª Linha%' LIMIT 1")

    df_nobre = fetch_all("SELECT id FROM produtos WHERE nome LIKE '%Alho Nobre%' OR nome LIKE '%Alho Descascado Nobre%' LIMIT 1")
    if df_nobre.empty:
        run_query("""
            INSERT INTO produtos (nome, unidade_medida, preco_venda_base, is_materia_prima, marca, custo_unidade)
            VALUES ('Alho Descascado Nobre (Mesa)', 'Kg', 18.00, 1, 'Empório do Alho', 12.00)
        """)
        df_nobre = fetch_all("SELECT id FROM produtos WHERE nome LIKE '%Alho Nobre%' OR nome LIKE '%Alho Descascado Nobre%' LIMIT 1")

    id_bombona = int(df_bombona.iloc[0]['id']) if not df_bombona.empty else None
    id_nobre = int(df_nobre.iloc[0]['id']) if not df_nobre.empty else None
    return id_nobre, id_bombona


def render_mesa_selecao():
    hoje = date.today()
    uid = st.session_state.get("user_id", 1)

    # 1. Carrega parâmetros do mês para obter a meta da casa
    str_mes = hoje.strftime("%Y-%m-01")
    df_params = fetch_all(SQL_PARAMETROS_MES, (str_mes, str_mes))
    meta_casa_kg = float(df_params.iloc[0]['meta_diaria_casa_kg']) if not df_params.empty else 500.0

    # -- Cabeçalho com Botão de 1-Click PDF --
    col_tit, col_pdf = st.columns([3, 1])
    with col_tit:
        st.markdown(f"### 🧺 Mesa de Seleção — <span style='color:#01743d'>{hoje.strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
    
    # Carrega presenças gravadas do dia para habilitar o PDF
    df_presencas_salvas = fetch_all(SQL_PRESENCAS_DO_DIA, (hoje.strftime("%Y-%m-%d"),))
    presentes_list = []
    if not df_presencas_salvas.empty:
        for _, r in df_presencas_salvas.iterrows():
            presentes_list.append({
                "id": r['selecionadora_id'],
                "nome": r['nome'],
                "meta_kg_dia": float(r['meta_kg_dia'])
            })

    with col_pdf:
        if presentes_list:
            pdf_bytes = gerar_pdf_folha(hoje, presentes_list, meta_casa_kg)
            st.download_button(
                label="📄 Baixar Folha do Dia (PDF)",
                data=pdf_bytes,
                file_name=f"folha_selecao_{hoje.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key="btn_download_pdf_1click"
            )

    st.divider()

    # -------------------------------------------------------------------------
    # PASSO 1: CONFIRMAÇÃO DE PRESENÇAS DO DIA
    # -------------------------------------------------------------------------
    st.markdown("##### 👥 Passo 1 — Quem está presente hoje?")

    df_sel = fetch_all(SQL_SELECIONADORAS_ATIVAS)

    if df_sel.empty:
        st.warning("⚠️ Nenhuma selecionadora ativa cadastrada no módulo de Pessoas/RH.")
        return

    # Dicionário mapeando nome exibido (apenas Primeiro Nome + ID) -> ID real
    opts_map = {}
    for _, r in df_sel.iterrows():
        p_nome = obter_primeiro_nome(r['nome'])
        label = f"{p_nome} (Nível {r['nivel_classificacao']} • {r['meta_kg_dia']:.0f} kg/dia)"
        opts_map[label] = r

    # Selecionadas previamente gravadas ou escolha atual
    default_selected = []
    if not df_presencas_salvas.empty:
        pres_ids = set(df_presencas_salvas['selecionadora_id'].tolist())
        for lbl, r in opts_map.items():
            if r['id'] in pres_ids:
                default_selected.append(lbl)

    selecionadas_lbl = st.multiselect(
        "Selecione as selecionadoras presentes na mesa:",
        options=list(opts_map.keys()),
        default=default_selected,
        placeholder="Clique para selecionar...",
        key="ms_presenca_multiselect"
    )

    if selecionadas_lbl:
        rows_presentes = [opts_map[lbl] for lbl in selecionadas_lbl]
        cap_total = sum(r['meta_kg_dia'] for r in rows_presentes)

        c1, c2, c3 = st.columns(3)
        c1.metric("Selecionadoras Presentes", f"{len(selecionadas_lbl)}")
        c2.metric("Capacidade do Dia", f"{cap_total:,.0f} kg")
        c3.metric("Meta Mínima da Casa", f"{meta_casa_kg:,.0f} kg")

        if st.button("✅ Confirmar / Salvar Presenças do Dia", type="primary", key="btn_salvar_presencas"):
            try:
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    # Limpa anteriores e insere atuais
                    run_query(SQL_LIMPAR_PRESENCA_DIA, (hoje.strftime("%Y-%m-%d"),))
                    for r in rows_presentes:
                        run_query(SQL_INSERIR_PRESENCA, (hoje.strftime("%Y-%m-%d"), int(r['id']), uid))
                st.success("✔️ Presenças do dia gravadas com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar presenças: {e}")

    st.divider()

    # -------------------------------------------------------------------------
    # PASSO 2: PESAGEM INDIVIDUAL & BALANÇO DE RESÍDUOS
    # -------------------------------------------------------------------------
    if not df_presencas_salvas.empty:
        st.markdown("##### ⚖️ Passo 2 — Pesagem Individual & Balanço de Resíduos")
        
        # Carrega pesagens gravadas do dia
        df_pesagens_salvas = fetch_all(SQL_PESAGENS_DO_DIA, (hoje.strftime("%Y-%m-%d"),))
        pesagens_dict = {}
        if not df_pesagens_salvas.empty:
            for _, r in df_pesagens_salvas.iterrows():
                pesagens_dict[r['selecionadora_id']] = float(r['peso_kg'])

        with st.form("form_pesagem_mesa"):
            st.markdown("###### 1. Produção Individual por Selecionadora (kg)")
            
            novas_pesagens = {}
            cols = st.columns(2)
            for idx, r in enumerate(presentes_list):
                col = cols[idx % 2]
                sid = r['id']
                p_nome = obter_primeiro_nome(r['nome'])
                val_atual = pesagens_dict.get(sid, 0.0)
                peso_in = col.number_input(
                    f"👩‍🌾 {p_nome} (Meta: {r['meta_kg_dia']:.0f} kg)",
                    min_value=0.0,
                    value=val_atual,
                    step=1.0,
                    format="%.1f",
                    key=f"pesagem_input_{sid}"
                )
                novas_pesagens[sid] = (peso_in, r['meta_kg_dia'])

            st.markdown("---")
            st.markdown("###### 2. Balanço do Lote (Alho Nobre, Bombona 2ª Linha e Lixo)")
            
            # Carrega aproveitamento gravado
            df_aprov_salvo = fetch_all(SQL_APROVEITAMENTO_DO_DIA, (hoje.strftime("%Y-%m-%d"),))
            nobre_salvo = float(df_aprov_salvo.iloc[0]['peso_nobre_kg']) if not df_aprov_salvo.empty else 0.0
            bombona_salva = float(df_aprov_salvo.iloc[0]['peso_segunda_linha_kg']) if not df_aprov_salvo.empty else 0.0
            lixo_salvo = float(df_aprov_salvo.iloc[0]['peso_descarte_kg']) if not df_aprov_salvo.empty else 0.0

            ca1, ca2, ca3 = st.columns(3)
            peso_nobre = ca1.number_input("✨ Alho Nobre (kg)", min_value=0.0, value=nobre_salvo, step=1.0, format="%.1f")
            peso_bombona = ca2.number_input("🛢️ Alho 2ª Linha - Bombona (kg)", min_value=0.0, value=bombona_salva, step=1.0, format="%.1f")
            peso_lixo = ca3.number_input("🗑️ Descarte / Lixo (kg)", min_value=0.0, value=lixo_salvo, step=1.0, format="%.1f")

            submit_lote = st.form_submit_button("💾 Cravar Pesagens e Balanço do Dia", type="primary", use_container_width=True)

        if submit_lote:
            try:
                str_hoje = hoje.strftime("%Y-%m-%d")
                with db_transaction() as conn:
                    # 1. Grava pesagens individuais
                    for sid, (peso, meta_exp) in novas_pesagens.items():
                        run_query(SQL_UPSERT_PESAGEM, (str_hoje, sid, peso, meta_exp, uid))
                    
                    # 2. Grava balanço de aproveitamento
                    run_query(SQL_UPSERT_APROVEITAMENTO, (str_hoje, peso_nobre, peso_bombona, peso_lixo, uid))

                    # 3. Dá entrada no Estoque de Alho Nobre e Bombona
                    id_nobre, id_bombona = _garantir_produtos_subprodutos()
                    ref_doc = f"Mesa Seleção {hoje.strftime('%d/%m/%Y')}"

                    if id_bombona and peso_bombona > 0:
                        run_query("""
                            INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia)
                            VALUES (?, ?, 'Entrada', ?, 'Seleção_Mesa_Bombona', ?)
                        """, (str_hoje, id_bombona, peso_bombona, ref_doc))

                    if id_nobre and peso_nobre > 0:
                        run_query("""
                            INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia)
                            VALUES (?, ?, 'Entrada', ?, 'Seleção_Mesa_Nobre', ?)
                        """, (str_hoje, id_nobre, peso_nobre, ref_doc))

                st.success("✔️ Pesagens e Balanço gravados! Estoque de Alho Nobre e Bombona atualizados.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar balanço do lote: {e}")
    else:
        st.info("💡 Selecione e confirme as selecionadoras presentes acima para liberar o lançamento de pesagens do dia.")
