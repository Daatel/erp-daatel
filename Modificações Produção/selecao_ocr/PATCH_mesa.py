# PATCH — mesa.py
# Alterações necessárias no componente Mesa de Seleção para integrar o OCR.
# Aplicar sobre o mesa.py existente.
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Adicionar import no topo do arquivo
# -----------------------------------------------------------------------------

# ANTES (linha de imports existente):
# from .queries import (...)

# DEPOIS — adicionar linha:
from .ocr_folha import render_importar_folha


# -----------------------------------------------------------------------------
# 2. No início do passo 2 (após renderizar os cards de resumo),
#    adicionar a chamada ao componente OCR ANTES da tabela de pesagem manual.
#    Localizar o trecho:
#
#        st.divider()
#        st.markdown("##### Passo 2 — Pesagem individual")
#
#    e inserir ANTES:
# -----------------------------------------------------------------------------

# -- Importação via foto (opcional) --
render_importar_folha(presentes)

# Se houve importação via OCR, pré-preencher os campos
ocr_ok    = st.session_state.pop("ocr_importacao_ok", False)
ocr_pesos = st.session_state.pop("ocr_pesos_confirmados", {})


# -----------------------------------------------------------------------------
# 3. No loop de pesagem individual, substituir o número de input para
#    usar o valor do OCR como default quando disponível.
#    Localizar:
#
#        peso = st.number_input(
#            "kg",
#            min_value=0.0,
#            step=0.5,
#            key=f"peso_{p['id']}",
#            label_visibility="collapsed",
#        )
#
#    e substituir por:
# -----------------------------------------------------------------------------

default_peso = float(ocr_pesos.get(p["id"], {}).get("peso", 0.0)) if ocr_pesos else 0.0
peso = st.number_input(
    "kg",
    min_value=0.0,
    value=default_peso,
    step=0.5,
    key=f"peso_{p['id']}",
    label_visibility="collapsed",
)


# -----------------------------------------------------------------------------
# 4. No bloco de descarte (st.number_input de nobre/segunda/descarte),
#    usar valores do OCR como default quando disponíveis.
#    Substituir os três number_input por:
# -----------------------------------------------------------------------------

peso_nobre = st.number_input(
    "Alho nobre (kg)",
    min_value=0.0,
    value=float(st.session_state.pop("ocr_nobre_kg", 0.0)),
    step=0.5,
    key="d_nobre",
)

peso_segunda = st.number_input(
    "2ª linha — Bombona (kg)",
    min_value=0.0,
    value=float(st.session_state.pop("ocr_segunda_linha_kg", 0.0)),
    step=0.5,
    key="d_segunda",
)

peso_descarte = st.number_input(
    "Descarte — Lixo (kg)",
    min_value=0.0,
    value=float(st.session_state.pop("ocr_descarte_kg", 0.0)),
    step=0.5,
    key="d_descarte",
)

# =============================================================================
# FIM DO PATCH
# Nenhuma alteração em banco de dados necessária.
# O save final segue o fluxo existente do mesa.py sem modificação.
# =============================================================================
