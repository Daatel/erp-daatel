# components/selecao/ocr_folha.py
# Importação de Folha Fotografada via Gemini Vision
# Integrar na aba Mesa de Seleção (passo 2)

import json
import io
import streamlit as st
from PIL import Image
import google.generativeai as genai

# --------------------------------------------------------------------------
# Configuração
# --------------------------------------------------------------------------

def _get_gemini():
    """Inicializa o cliente Gemini com a chave do projeto."""
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini_api_key")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY não encontrada. "
            "Adicionar em .streamlit/secrets.toml ou variável de ambiente."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------

PROMPT_OCR = """
Você está lendo uma folha de pesagem de selecionadoras de uma fábrica de alho.

A folha tem duas seções:

SEÇÃO 1 — PESAGEM INDIVIDUAL
Tabela com colunas: #, Nome, Meta (kg), Pesagem 1, Pesagem 2, Total (kg)
Extraia apenas o Nome e o Total (kg) de cada linha preenchida.
Ignore linhas onde o Total estiver em branco ou ilegível.

SEÇÃO 2 — DESCARTE X 2A LINHA
Tabela com linhas: Alho Nobre, 2ª Linha, Descarte
Extraia o Peso (kg) de cada linha.

Retorne APENAS um JSON válido, sem texto antes ou depois, sem markdown,
no seguinte formato exato:

{
  "pesagens": [
    { "nome": "Maria Souza", "total_kg": 88.5 },
    { "nome": "Ana Lima",    "total_kg": 95.0 }
  ],
  "nobre_kg":         420.0,
  "segunda_linha_kg":  85.0,
  "descarte_kg":       32.0,
  "confianca":        "alta",
  "avisos":           []
}

Regras:
- total_kg, nobre_kg, segunda_linha_kg, descarte_kg: número decimal ou null se ilegível
- confianca: "alta" | "media" | "baixa" conforme qualidade de imagem e caligrafia
- avisos: lista de strings descrevendo campos ilegíveis ou suspeitos
- Nunca invente valores. Se ilegível, retorne null.
"""

# --------------------------------------------------------------------------
# Extração via Gemini
# --------------------------------------------------------------------------

def _extrair_dados_folha(imagem: Image.Image) -> dict:
    """
    Envia a imagem para o Gemini e retorna o dict com os dados extraídos.
    Lança exceção em caso de falha de API ou JSON inválido.
    """
    model = _get_gemini()

    # Converter para RGB se necessário (RGBA não é aceito)
    if imagem.mode in ("RGBA", "P"):
        imagem = imagem.convert("RGB")

    resposta = model.generate_content([PROMPT_OCR, imagem])
    texto = resposta.text.strip()

    # Limpar possíveis backticks que o modelo insira mesmo com instrução contrária
    if texto.startswith("```"):
        linhas = texto.splitlines()
        texto = "\n".join(
            l for l in linhas
            if not l.strip().startswith("```")
        )

    dados = json.loads(texto)
    return dados


# --------------------------------------------------------------------------
# Helpers de UI
# --------------------------------------------------------------------------

def _badge_confianca(nivel: str) -> str:
    mapa = {
        "alta":  ("🟢", "Alta confiança"),
        "media": ("🟡", "Confiança média — revisar com atenção"),
        "baixa": ("🔴", "Baixa confiança — foto com problemas"),
    }
    icon, label = mapa.get(nivel, ("⚪", "Desconhecida"))
    return f"{icon} {label}"


def _match_presentes(nome_ocr: str, presentes: list) -> dict | None:
    """
    Tenta associar o nome extraído pelo OCR a um presente confirmado.
    Usa comparação case-insensitive e ignora acentos simples.
    """
    import unicodedata

    def normalizar(s: str) -> str:
        return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()

    nome_norm = normalizar(nome_ocr)
    for p in presentes:
        if normalizar(p["nome"]) == nome_norm:
            return p
        # Match parcial: primeiro nome + primeiro sobrenome
        partes_ocr = nome_norm.split()
        partes_p   = normalizar(p["nome"]).split()
        if len(partes_ocr) >= 1 and len(partes_p) >= 1:
            if partes_ocr[0] == partes_p[0] and (
                len(partes_ocr) == 1 or
                (len(partes_p) > 1 and partes_ocr[-1] == partes_p[-1])
            ):
                return p
    return None


# --------------------------------------------------------------------------
# Render principal
# --------------------------------------------------------------------------

def render_importar_folha(presentes: list):
    """
    Componente de importação via foto.
    Deve ser chamado dentro da aba Mesa de Seleção, passo 2.

    Args:
        presentes: lista de dicts com keys id, nome, meta_kg_dia
                   (mesmo formato do session_state selecao_presencas_confirmadas)
    """
    with st.expander("📷 Importar folha fotografada", expanded=False):

        st.caption(
            "Fotografe a folha preenchida. O sistema tentará extrair os dados "
            "automaticamente. Você poderá revisar antes de salvar."
        )

        # -- Input de imagem --
        col_cam, col_up = st.columns(2)
        with col_cam:
            foto_camera = st.camera_input(
                "Tirar foto agora",
                key="ocr_camera",
                help="Usar câmera do dispositivo (requer HTTPS em produção)",
            )
        with col_up:
            foto_upload = st.file_uploader(
                "Ou enviar arquivo",
                type=["jpg", "jpeg", "png"],
                key="ocr_upload",
                label_visibility="visible",
            )

        imagem_raw = foto_camera or foto_upload
        if not imagem_raw:
            return

        # -- Processar imagem --
        imagem = Image.open(imagem_raw)

        col_img, col_info = st.columns([1, 1])
        with col_img:
            st.image(imagem, caption="Imagem recebida", use_container_width=True)

        with col_info:
            st.markdown("**Enviando para leitura...**")
            with st.spinner("Gemini Vision processando..."):
                try:
                    dados = _extrair_dados_folha(imagem)
                except json.JSONDecodeError:
                    st.error(
                        "Não foi possível interpretar a resposta da IA. "
                        "Tente novamente com melhor iluminação ou ângulo."
                    )
                    return
                except Exception as e:
                    st.error(f"Erro na API Gemini: {e}")
                    st.info("Use o lançamento manual como alternativa.")
                    return

            # Badge de confiança
            confianca = dados.get("confianca", "baixa")
            st.markdown(_badge_confianca(confianca))

            # Avisos
            avisos = dados.get("avisos", [])
            for aviso in avisos:
                st.warning(f"⚠️ {aviso}")

        st.divider()

        # -- Tabela de confirmação: pesagens --
        st.markdown("##### Revisar pesagens extraídas")
        st.caption("Corrija valores incorretos antes de confirmar.")

        pesagens_ocr = dados.get("pesagens", [])
        pesos_confirmados = {}

        if not pesagens_ocr:
            st.warning("Nenhuma pesagem identificada na imagem.")
        else:
            for item in pesagens_ocr:
                nome_ocr  = item.get("nome", "")
                total_ocr = item.get("total_kg")
                presente  = _match_presentes(nome_ocr, presentes)

                col_n, col_p, col_v, col_alerta = st.columns([3, 1, 2, 2])

                with col_n:
                    # Mostrar nome do presente associado (ou o nome bruto do OCR)
                    nome_display = presente["nome"] if presente else nome_ocr
                    st.write(nome_display)

                with col_p:
                    meta = presente["meta_kg_dia"] if presente else None
                    st.caption(f"Meta: {meta:.0f} kg" if meta else "—")

                with col_v:
                    valor_default = float(total_ocr) if total_ocr is not None else 0.0
                    peso_editado = st.number_input(
                        "kg",
                        min_value=0.0,
                        value=valor_default,
                        step=0.5,
                        key=f"ocr_peso_{nome_ocr.replace(' ', '_')}",
                        label_visibility="collapsed",
                    )

                with col_alerta:
                    if not presente:
                        st.caption("⚠️ Nome não encontrado na lista de presentes")
                    elif total_ocr is None:
                        st.caption("⚠️ Valor ilegível — revisar")
                    elif meta and peso_editado > meta * 1.5:
                        st.caption("⚠️ Valor acima do esperado")
                    else:
                        st.caption("✅")

                if presente and peso_editado > 0:
                    pesos_confirmados[presente["id"]] = {
                        "peso":  peso_editado,
                        "meta":  presente["meta_kg_dia"],
                        "nome":  presente["nome"],
                    }

        st.divider()

        # -- Descarte --
        st.markdown("##### Revisar descarte × 2ª linha")

        col_nobre, col_segunda, col_desc = st.columns(3)

        with col_nobre:
            nobre_ocr = dados.get("nobre_kg")
            nobre = st.number_input(
                "Alho nobre (kg)",
                min_value=0.0,
                value=float(nobre_ocr) if nobre_ocr is not None else 0.0,
                step=0.5,
                key="ocr_nobre",
            )
            if nobre_ocr is None:
                st.caption("⚠️ Ilegível")

        with col_segunda:
            segunda_ocr = dados.get("segunda_linha_kg")
            segunda = st.number_input(
                "2ª linha — Bombona (kg)",
                min_value=0.0,
                value=float(segunda_ocr) if segunda_ocr is not None else 0.0,
                step=0.5,
                key="ocr_segunda",
            )
            if segunda_ocr is None:
                st.caption("⚠️ Ilegível")

        with col_desc:
            descarte_ocr = dados.get("descarte_kg")
            descarte = st.number_input(
                "Descarte — Lixo (kg)",
                min_value=0.0,
                value=float(descarte_ocr) if descarte_ocr is not None else 0.0,
                step=0.5,
                key="ocr_descarte",
            )
            if descarte_ocr is None:
                st.caption("⚠️ Ilegível")

        total_lote = nobre + segunda + descarte
        if total_lote > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total do lote", f"{total_lote:,.1f} kg")
            c2.metric("% Nobre",    f"{nobre   / total_lote * 100:.1f}%")
            c3.metric("% 2ª linha", f"{segunda / total_lote * 100:.1f}%")
            c4.metric("% Descarte", f"{descarte/ total_lote * 100:.1f}%")

        st.divider()

        # -- Confirmar importação --
        if not pesos_confirmados:
            st.warning("Nenhuma pesagem válida para importar.")
            return

        n_importar = len(pesos_confirmados)
        n_presentes = len(presentes)

        if n_importar < n_presentes:
            st.info(
                f"{n_importar} de {n_presentes} selecionadoras identificadas. "
                f"As demais precisarão ser lançadas manualmente."
            )

        if st.button(
            f"✅ Confirmar importação — {n_importar} pesagens",
            type="primary",
            key="btn_confirmar_ocr",
        ):
            # Salvar no session_state para o fluxo normal de save do mesa.py
            st.session_state["ocr_pesos_confirmados"]  = pesos_confirmados
            st.session_state["ocr_nobre_kg"]           = nobre
            st.session_state["ocr_segunda_linha_kg"]   = segunda
            st.session_state["ocr_descarte_kg"]        = descarte
            st.session_state["ocr_importacao_ok"]      = True
            st.success(
                f"Dados importados. Confira os campos abaixo e clique em "
                f"'Salvar lançamentos do dia' para gravar no banco."
            )
            st.rerun()
