# pages/Selecao.py
# Módulo de Seleção, Metas e Rendimento de Alho
# Substitui pages/Producao.py

import streamlit as st
from datetime import date
import calendar

# Importar sub-módulos (ajustar path conforme estrutura do projeto)
from components.selecao.painel_bi import render_painel_bi
from components.selecao.mesa import render_mesa_selecao
from components.selecao.configuracoes import render_configuracoes

# --------------------------------------------------------------------------
# Configuração da página
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Seleção — ERP Alho",
    layout="wide",
)

# --------------------------------------------------------------------------
# Inicializar session_state
# --------------------------------------------------------------------------
if "selecao_mes_ano" not in st.session_state:
    hoje = date.today()
    st.session_state["selecao_mes_ano"] = date(hoje.year, hoje.month, 1)

if "selecao_presencas_confirmadas" not in st.session_state:
    st.session_state["selecao_presencas_confirmadas"] = []

if "selecao_passo" not in st.session_state:
    st.session_state["selecao_passo"] = 1  # 1 = presença | 2 = pesagem

# --------------------------------------------------------------------------
# Abas
# --------------------------------------------------------------------------
aba_bi, aba_mesa, aba_config = st.tabs([
    "📊 Painel de produção",
    "🧄 Mesa de seleção",
    "⚙️ Configurações",
])

with aba_bi:
    render_painel_bi()

with aba_mesa:
    render_mesa_selecao()

with aba_config:
    # Restrito ao perfil ADMIN
    perfil = st.session_state.get("perfil", "")
    if perfil != "ADMIN":
        st.warning("Acesso restrito ao perfil Administrador.")
        st.stop()
    render_configuracoes()
