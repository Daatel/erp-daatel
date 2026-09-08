# components/theme.py
# Sistema de design centralizado — ERP Daatel / Empório do Alho
#
# USO:
#   from components.theme import apply_theme
#   apply_theme()   ← chamar UMA VEZ no início de cada página
#
# Nunca usar st.markdown com CSS diretamente nas páginas.
# Toda customização visual vai aqui.

import streamlit as st


def apply_theme():
    """Injeta o CSS global do sistema. Chamar no topo de cada página."""
    st.markdown(_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Paleta de cores (referência para uso em Python quando necessário)
# --------------------------------------------------------------------------

class Cores:
    # Primária
    VERDE          = "#01743d"
    VERDE_LIGHT    = "#e6f4ed"
    VERDE_DARK     = "#015a30"

    # Neutros
    GRAFITE        = "#1a1a18"
    CINZA_TEXTO    = "#52514e"
    CINZA_MUTED    = "#888780"
    CINZA_BORDA    = "#d3d1c7"
    CINZA_BG       = "#f1efe8"
    BRANCO         = "#ffffff"
    OFF_WHITE      = "#f9f8f4"

    # Semânticas
    SUCESSO        = "#3b6d11"
    SUCESSO_BG     = "#eaf3de"
    ALERTA         = "#854f0b"
    ALERTA_BG      = "#faeeda"
    ERRO           = "#a32d2d"
    ERRO_BG        = "#fcebeb"
    INFO           = "#185fa5"
    INFO_BG        = "#e6f1fb"

    # Níveis de selecionadora
    NIVEL_A_BG     = "#e1f5ee"
    NIVEL_A_TEXT   = "#0f6e56"
    NIVEL_B_BG     = "#e6f1fb"
    NIVEL_B_TEXT   = "#185fa5"
    NIVEL_T_BG     = "#f1efe8"
    NIVEL_T_TEXT   = "#5f5e5a"


# --------------------------------------------------------------------------
# Helpers de badge (retornam HTML pronto para st.markdown)
# --------------------------------------------------------------------------

def badge_nivel(nivel: str) -> str:
    """Retorna HTML de badge colorido por nível."""
    config = {
        "A":     (Cores.NIVEL_A_BG,  Cores.NIVEL_A_TEXT,  "Nível A"),
        "B":     (Cores.NIVEL_B_BG,  Cores.NIVEL_B_TEXT,  "Nível B"),
        "Teste": (Cores.NIVEL_T_BG,  Cores.NIVEL_T_TEXT,  "Teste"),
    }
    bg, color, label = config.get(nivel, (Cores.CINZA_BG, Cores.CINZA_TEXTO, nivel))
    return (
        f'<span style="background:{bg}; color:{color}; '
        f'font-size:11px; font-weight:500; padding:2px 8px; '
        f'border-radius:10px; white-space:nowrap">{label}</span>'
    )


def badge_vinculo(vinculo: str) -> str:
    """Retorna HTML de badge de vínculo CLT/Diarista."""
    config = {
        "CLT":      ("#eeedfe", "#3c3489"),
        "Diarista": ("#faeeda", "#854f0b"),
    }
    bg, color = config.get(vinculo, (Cores.CINZA_BG, Cores.CINZA_TEXTO))
    return (
        f'<span style="background:{bg}; color:{color}; '
        f'font-size:11px; font-weight:500; padding:2px 8px; '
        f'border-radius:10px; white-space:nowrap">{vinculo}</span>'
    )


def badge_status(pct: float) -> str:
    """Badge de % atingimento de meta."""
    if pct >= 100:
        bg, color, label = Cores.SUCESSO_BG, Cores.SUCESSO, "Atingido"
    elif pct >= 80:
        bg, color, label = Cores.ALERTA_BG,  Cores.ALERTA,  f"{pct:.0f}%"
    else:
        bg, color, label = Cores.ERRO_BG,    Cores.ERRO,    f"{pct:.0f}%"
    return (
        f'<span style="background:{bg}; color:{color}; '
        f'font-size:11px; font-weight:500; padding:2px 8px; '
        f'border-radius:10px; white-space:nowrap">{label}</span>'
    )


def badge_tendencia(tendencia: str) -> str:
    """Badge de tendência com ícone."""
    config = {
        "subindo": ("↑", Cores.SUCESSO),
        "estavel": ("→", Cores.CINZA_MUTED),
        "caindo":  ("↓", Cores.ERRO),
        "neutro":  ("—", Cores.CINZA_MUTED),
    }
    icon, color = config.get(tendencia, ("—", Cores.CINZA_MUTED))
    return (
        f'<span style="color:{color}; font-size:16px; '
        f'font-weight:600; line-height:1">{icon}</span>'
    )


def metric_card(label: str, value: str, sub: str = "", cor_value: str = "") -> str:
    """Card de KPI compacto em HTML puro (usar dentro de st.markdown)."""
    cor = cor_value or Cores.GRAFITE
    sub_html = (
        f'<div style="font-size:11px; color:{Cores.CINZA_MUTED}; margin-top:2px">{sub}</div>'
        if sub else ""
    )
    return f"""
    <div style="background:{Cores.BRANCO}; border:0.5px solid {Cores.CINZA_BORDA};
                border-radius:8px; padding:12px 14px; height:100%">
      <div style="font-size:11px; color:{Cores.CINZA_TEXTO}; margin-bottom:4px">{label}</div>
      <div style="font-size:20px; font-weight:500; color:{cor}; line-height:1.2">{value}</div>
      {sub_html}
    </div>"""


def section_title(texto: str) -> str:
    """Título de seção compacto."""
    return (
        f'<div style="font-size:11px; font-weight:600; color:{Cores.CINZA_MUTED}; '
        f'text-transform:uppercase; letter-spacing:0.06em; '
        f'margin:16px 0 6px 0">{texto}</div>'
    )


def divider_line() -> str:
    """Divisor fino."""
    return f'<hr style="border:none; border-top:0.5px solid {Cores.CINZA_BORDA}; margin:12px 0">'


# --------------------------------------------------------------------------
# CSS Global
# --------------------------------------------------------------------------

_CSS = f"""
<style>

/* ── Reset de margens da página ─────────────────────────────────────── */
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1100px !important;
}}

/* ── Inputs compactos ───────────────────────────────────────────────── */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input {{
    height: 36px !important;
    min-height: 36px !important;
    padding: 0 10px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    background: {Cores.BRANCO} !important;
}}

div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextInput"] input:focus {{
    border-color: {Cores.VERDE} !important;
    box-shadow: 0 0 0 2px {Cores.VERDE_LIGHT} !important;
    outline: none !important;
}}

/* ── Selectbox compacto ─────────────────────────────────────────────── */
div[data-testid="stSelectbox"] > div > div {{
    height: 36px !important;
    min-height: 36px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
}}

/* ── Multiselect compacto ───────────────────────────────────────────── */
div[data-testid="stMultiSelect"] > div > div {{
    min-height: 36px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
}}

/* ── Botões ─────────────────────────────────────────────────────────── */
div[data-testid="stButton"] > button {{
    height: 36px !important;
    padding: 0 16px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    background: {Cores.BRANCO} !important;
    color: {Cores.GRAFITE} !important;
    font-weight: 400 !important;
    transition: background 0.15s, border-color 0.15s !important;
}}

div[data-testid="stButton"] > button:hover {{
    background: {Cores.CINZA_BG} !important;
    border-color: {Cores.CINZA_TEXTO} !important;
}}

div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[data-testid*="primary"] {{
    background: {Cores.VERDE} !important;
    color: {Cores.BRANCO} !important;
    border-color: {Cores.VERDE} !important;
    font-weight: 500 !important;
}}

div[data-testid="stButton"] > button[kind="primary"]:hover {{
    background: {Cores.VERDE_DARK} !important;
    border-color: {Cores.VERDE_DARK} !important;
}}

/* ── Tabs ───────────────────────────────────────────────────────────── */
div[data-testid="stTabs"] button[role="tab"] {{
    font-size: 13px !important;
    padding: 8px 16px !important;
    font-weight: 400 !important;
    color: {Cores.CINZA_TEXTO} !important;
}}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    font-weight: 500 !important;
    color: {Cores.GRAFITE} !important;
}}

/* ── Métricas compactas ─────────────────────────────────────────────── */
div[data-testid="stMetric"] {{
    background: {Cores.BRANCO} !important;
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}}

div[data-testid="stMetric"] label {{
    font-size: 11px !important;
    color: {Cores.CINZA_TEXTO} !important;
    font-weight: 400 !important;
}}

div[data-testid="stMetricValue"] {{
    font-size: 20px !important;
    font-weight: 500 !important;
    color: {Cores.GRAFITE} !important;
    line-height: 1.3 !important;
}}

div[data-testid="stMetricDelta"] {{
    font-size: 11px !important;
}}

/* ── Expander ───────────────────────────────────────────────────────── */
div[data-testid="stExpander"] {{
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    border-radius: 8px !important;
    background: {Cores.BRANCO} !important;
}}

div[data-testid="stExpander"] summary {{
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
}}

/* ── Dataframe ──────────────────────────────────────────────────────── */
div[data-testid="stDataFrame"] {{
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    font-size: 13px !important;
}}

/* ── Alertas compactos ──────────────────────────────────────────────── */
div[data-testid="stAlert"] {{
    padding: 10px 14px !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}}

/* ── Labels menores ─────────────────────────────────────────────────── */
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stDateInput"] label {{
    font-size: 12px !important;
    font-weight: 500 !important;
    color: {Cores.CINZA_TEXTO} !important;
    margin-bottom: 3px !important;
}}

/* ── Sidebar ────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {Cores.GRAFITE} !important;
}}

section[data-testid="stSidebar"] * {{
    color: #d3d1c7 !important;
}}

section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] input {{
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: #f1efe8 !important;
}}

/* ── Cabeçalho de página ────────────────────────────────────────────── */
h1 {{
    font-size: 22px !important;
    font-weight: 500 !important;
    color: {Cores.GRAFITE} !important;
    margin-bottom: 0.25rem !important;
}}

h2 {{
    font-size: 17px !important;
    font-weight: 500 !important;
    color: {Cores.GRAFITE} !important;
}}

h3 {{
    font-size: 15px !important;
    font-weight: 500 !important;
    color: {Cores.GRAFITE} !important;
}}

/* ── Divisores ──────────────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 0.5px solid {Cores.CINZA_BORDA} !important;
    margin: 12px 0 !important;
}}

/* ── Remover padding excessivo entre elementos ──────────────────────── */
div[data-testid="element-container"] {{
    margin-bottom: 0 !important;
}}

.stMarkdown p {{
    margin-bottom: 0.3rem !important;
}}

/* ── Camera input ───────────────────────────────────────────────────── */
div[data-testid="stCameraInput"] {{
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}

/* ── File uploader ──────────────────────────────────────────────────── */
div[data-testid="stFileUploader"] {{
    border: 0.5px solid {Cores.CINZA_BORDA} !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-size: 13px !important;
}}

/* ── Spinner ────────────────────────────────────────────────────────── */
div[data-testid="stSpinner"] p {{
    font-size: 13px !important;
    color: {Cores.CINZA_TEXTO} !important;
}}

</style>
"""
