import streamlit as st

def carregar_estilo():
    st.markdown("""
    <style>
        .stTextInput label p, .stSelectbox label p, .stNumberInput label p, .stDateInput label p {
            color: #01743d !important;
            font-weight: 600 !important;
        }
        /* --- CORREÇÃO GERAL DE ENTRADAS DE DADOS (INPUTS CLAROS E LEGÍVEIS) --- */
        div[data-baseweb="input"] {
            background-color: #ffffff !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="input"] > div {
            border-color: #01743d40 !important;
            background-color: #ffffff !important;
        }
        div[data-baseweb="input"] input {
            background-color: #ffffff !important;
            color: #0f172a !important; /* Slate 900 */
            -webkit-text-fill-color: #0f172a !important;
        }
        /* Caixas de Seleção (Selectbox / Dropdown) */
        div[data-baseweb="select"] > div {
            border-color: #01743d40 !important;
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        div[data-baseweb="select"] * {
            color: #0f172a !important;
        }
        /* Textareas (Áreas de texto longo) */
        div[data-baseweb="textarea"] textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        /* Botões de incremento/decremento nos inputs numéricos */
        div[data-testid="stNumberInputStepDown"], div[data-testid="stNumberInputStepUp"] {
            background-color: #f1f5f9 !important; /* Slate 100 */
            border-color: #cbd5e1 !important;
        }
        div[data-testid="stNumberInputStepDown"] svg, div[data-testid="stNumberInputStepUp"] svg {
            fill: #475569 !important; /* Slate 600 */
        }
        h1, h2, h3 {
            color: #292d77 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-left: 5px solid #01743d;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        /* --- ESTILIZAÇÃO DO SIDEBAR CORPORATIVO (DARK MODE PREMIUM) --- */
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important; /* Slate 900 */
            border-right: 1px solid #1e293b !important;
            position: relative !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background-color: #0f172a !important;
        }
        section[data-testid="stSidebar"] * {
            color: #f1f5f9 !important; /* Slate 100 */
        }
        /* Título dos Grupos de Menu (Ex: GERENCIAL, COMERCIAL, OPERAÇÃO) */
        section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {
            border-color: #1e293b !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] span {
            color: #38bdf8 !important; /* Sky 400 */
            font-weight: 700 !important;
            font-size: 11px !important;
            letter-spacing: 0.8px !important;
            text-transform: uppercase !important;
        }
        /* Links de páginas ativos e inativos */
        section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
            background-color: transparent !important;
            transition: all 0.2s ease-in-out !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover {
            background-color: #1e293b !important; /* Slate 800 */
            border-radius: 6px !important;
        }
        /* Indicador de página ativa */
        section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a[aria-current="page"] {
            background-color: #0284c7 !important; /* Sky 600 */
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        /* Sobrescrita de componentes da página principal para manter o tema claro e elegante */
        div[data-testid="stExpander"] {
            background-color: #f8fafc !important; /* Slate 50 */
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stExpander"] label p, div[data-testid="stExpander"] p, div[data-testid="stExpander"] span {
            color: #1e293b !important; /* Slate 800 */
        }
        div[data-testid="stExpander"] svg {
            fill: #64748b !important;
        }
        .stTabs [role="tablist"] {
            border-bottom: 2px solid #e2e8f0 !important;
        }
        .stTabs [role="tab"] p {
            color: #64748b !important;
            font-weight: 500 !important;
        }
        .stTabs [role="tab"][aria-selected="true"] p {
            color: #01743d !important;
            font-weight: 700 !important;
        }
        .daatel-footer {
            position: fixed;
            bottom: 10px;
            right: 15px;
            color: #666666;
            font-size: 11px;
            font-weight: 500;
            z-index: 9999;
            background-color: rgba(255, 255, 255, 0.7);
            padding: 2px 8px;
            border-radius: 4px;
        }
        /* --- ESTILO DO BOTÃO DE LOGOUT NA BARRA LATERAL --- */
        div.st-key-logout_btn button {
            background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%) !important; /* Tema azul turquesa */
            color: #ffffff !important;
            border: 1px solid #0284c7 !important;
            border-bottom: 3px solid #014c73 !important; /* Efeito 3D sutil */
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            height: 38px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
            transition: all 0.1s ease !important;
            margin-top: 5px !important;
        }
        div.st-key-logout_btn button:hover {
            background: linear-gradient(180deg, #40c4ff 0%, #0284c7 100%) !important;
            border-bottom: 3px solid #014c73 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 12px rgba(2, 132, 199, 0.3) !important;
        }
        div.st-key-logout_btn button:active {
            transform: translateY(1px) !important;
            border-bottom: 1px solid #014c73 !important;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        }
        /* --- ESTILO DA LOGO E IDENTIFICAÇÃO FIXADAS NO TOPO DO SIDEBAR --- */
        section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sidebar-top-container) {
            position: static !important;
        }
        .sidebar-top-container {
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            text-align: center;
            padding: 0 20px;
            z-index: 99;
            background-color: #0f172a; /* Slate 900 */
        }
        .sidebar-logo-img {
            max-width: 100%;
            height: auto;
            object-fit: contain;
            max-height: 75px;
        }
        .sidebar-user-id {
            margin-top: 8px;
            line-height: 1.3;
            text-align: center;
        }
        .sidebar-user-id .user-name {
            font-size: 13px;
            font-weight: 600;
            color: #f1f5f9;
        }
        .sidebar-user-id .user-role {
            font-size: 10px;
            color: #94a3b8;
            text-transform: uppercase;
            font-weight: 500;
            letter-spacing: 0.5px;
        }
        /* Empurra o menu de navegação nativo para baixo */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            padding-top: 165px !important;
            background-color: #0f172a !important;
        }
        /* Reduz a margem de cabeçalho (padding-top) em todas as telas em 50% */
        [data-testid="stMainBlockContainer"], .block-container {
            padding-top: 3rem !important;
        }
        /* --- CORREÇÃO DE CONTRASTE DO CALENDÁRIO (st.date_input) --- */
        /* Month/Year dropdown text and icon in header */
        div[data-baseweb="calendar"] [data-baseweb="select"] * {
            color: #ffffff !important;
        }
        div[data-baseweb="calendar"] [data-baseweb="select"] svg {
            fill: #ffffff !important;
        }
        /* Navigation arrows (prev/next month) */
        div[data-baseweb="calendar"] > div:first-child button svg {
            fill: #ffffff !important;
        }
        div[data-baseweb="calendar"] > div:first-child button {
            color: #ffffff !important;
        }
        /* Weekday headers (Su, Mo, Tu, We, Th, Fr, Sa) */
        div[data-baseweb="calendar"] [role="columnheader"] {
            color: #ffffff !important;
        }
    </style>
    </div>
    """, unsafe_allow_html=True)


def carregar_estilo_login(error_msg=None, logo_html="", fundo_base64="", fundo_largo_base64=""):
    error_banner_html = ""
    if error_msg:
        error_banner_html = f"""<div class="login-error-banner"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg><span>{error_msg}</span></div>"""

    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
* {{
font-family: 'Outfit', sans-serif !important;
}}
header[data-testid="stHeader"] {{ 
visibility: hidden !important; 
}}
div[data-testid="stDecoration"] {{ 
display: none !important; 
}}
footer {{ 
visibility: hidden !important; 
}}
section[data-testid="stSidebar"] {{
display: none !important;
}}
[data-testid="collapsedControl"] {{
display: none !important;
}}
[data-testid="collapsedSidebar"] {{
display: none !important;
}}
div[data-testid="stForm"], div.st-key-esqueci_btn {{
position: absolute !important;
left: -9999px !important;
top: -9999px !important;
width: 1px !important;
height: 1px !important;
opacity: 0 !important;
}}
.daatel-brand-footer-native {{
display: none !important;
}}
[data-testid="stAppViewContainer"] {{
background-image: url('data:image/png;base64,{fundo_base64}') !important;
background-size: cover !important;
background-position: center !important;
background-repeat: no-repeat !important;
background-attachment: fixed !important;
position: relative !important;
overflow: hidden !important;
min-height: 100vh !important;
}}
@media (min-width: 1024px) {{
[data-testid="stAppViewContainer"] {{
background-image: url('data:image/png;base64,{fundo_largo_base64}') !important;
background-size: cover !important;
background-position: center !important;
}}
}}
[data-testid="stAppViewContainer"]::before {{
content: "" !important;
position: absolute !important;
top: 0 !important;
right: 0 !important;
width: 50% !important;
height: 100% !important;
background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" fill="none" stroke="%238b5cf6" stroke-width="0.5" stroke-opacity="0.02" stroke-dasharray="4 4"><path d="M0 100h800M0 200h800M0 300h800M0 400h800M0 500h800M0 600h800M0 700h800M100 0v800M200 0v800M300 0v800M400 0v800M500 0v800M600 0v800M700 0v800"/><path d="M0 0l800 800M800 0L0 800"/></svg>') !important;
background-size: cover !important;
background-position: right center !important;
pointer-events: none !important;
opacity: 0.8 !important;
z-index: 0 !important;
}}
[data-testid="stMainBlockContainer"], 
[data-testid="stVerticalBlock"], 
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stCustomComponentContainer"] {{
background-color: transparent !important;
background: transparent !important;
border: none !important;
box-shadow: none !important;
}}
.custom-login-overlay {{
position: fixed !important;
top: 0 !important;
left: 0 !important;
width: 100vw !important;
height: 100vh !important;
z-index: 99999 !important;
display: flex !important;
justify-content: center !important;
align-items: center !important;
overflow-y: auto !important;
box-sizing: border-box !important;
padding: 20px !important;
}}
.custom-login-container {{
width: 100% !important;
max-width: 420px !important;
margin: auto !important;
box-sizing: border-box !important;
}}
.custom-login-card {{
width: 420px !important;
background-image: 
    linear-gradient(180deg, rgba(255, 255, 255, 0.12) 0%, transparent 25%),
    radial-gradient(circle at bottom left, rgba(70, 255, 140, 0.10) 0%, transparent 45%),
    radial-gradient(circle at top right, rgba(180, 110, 255, 0.12) 0%, transparent 45%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%) !important;
background-color: rgba(15, 30, 65, 0.55) !important;
backdrop-filter: blur(22px) !important;
-webkit-backdrop-filter: blur(22px) !important;
border: 1px solid rgba(255, 255, 255, 0.18) !important;
border-radius: 32px !important;
padding: 35px 30px 25px 30px !important;
box-shadow:
    inset 0 0 1px rgba(255, 255, 255, 0.35),
    0 0 25px rgba(70, 255, 140, 0.08),
    0 0 35px rgba(180, 110, 255, 0.08),
    0 10px 40px rgba(0, 0, 0, 0.25) !important;
box-sizing: border-box !important;
position: relative !important;
transition: all 0.3s ease !important;
}}
.custom-login-card:hover {{
border-color: rgba(255, 255, 255, 0.25) !important;
box-shadow:
    inset 0 0 2px rgba(255, 255, 255, 0.45),
    0 0 35px rgba(70, 255, 140, 0.12),
    0 0 45px rgba(180, 110, 255, 0.12),
    0 15px 50px rgba(0, 0, 0, 0.3) !important;
}}
.login-logo-container {{
text-align: center;
margin-bottom: 15px;
}}
.login-logo-container img {{
width: 190px !important;
filter: drop-shadow(0 0 12px rgba(255, 255, 255, 0.15)) !important;
margin-bottom: 12px;
display: inline-block !important;
}}
.login-subtitle {{
color: #d7d7d7 !important;
font-size: 15px !important;
text-align: center !important;
margin: 0 0 8px 0 !important;
font-weight: 500 !important;
}}
.color-divider {{
height: 2px;
width: 60px;
margin: 0 auto 15px auto;
background: linear-gradient(90deg, #40d97a 0%, #8854ff 100%);
border-radius: 2px;
}}
.modules-bar {{
display: flex !important;
justify-content: center !important;
align-items: center !important;
gap: 6px !important;
color: #dcdcdc !important;
font-size: 11px !important;
margin-bottom: 10px !important;
background: transparent !important;
border: none !important;
padding: 0 !important;
flex-wrap: wrap !important;
letter-spacing: 0.5px !important;
}}
.module-item {{
display: flex;
align-items: center;
gap: 3px;
font-weight: 500;
color: #dcdcdc !important;
}}
.module-dot {{
color: rgba(255, 255, 255, 0.35) !important;
font-size: 12px !important;
}}
.custom-input-group {{
position: relative !important;
margin-bottom: 20px !important;
width: 100% !important;
}}
.custom-input-label {{
display: block !important;
text-align: left !important;
color: #5ae893 !important;
font-size: 13.5px !important;
font-weight: 500 !important;
margin-bottom: 6px !important;
letter-spacing: 0.5px !important;
}}
.input-wrapper {{
position: relative !important;
width: 100% !important;
}}
.input-wrapper input {{
width: 100% !important;
height: 50px !important;
padding: 12px 16px 12px 46px !important;
background: rgba(0, 0, 0, 0.35) !important;
border: 1px solid rgba(255, 255, 255, 0.4) !important;
border-radius: 12px !important;
color: #ffffff !important;
font-size: 15px !important;
outline: none !important;
transition: all 0.3s ease !important;
box-sizing: border-box !important;
}}
.input-wrapper input::placeholder {{
color: rgba(255, 255, 255, 0.45) !important;
}}
.input-wrapper input:focus, .input-wrapper input:hover {{
border-color: rgba(255, 255, 255, 0.8) !important;
background: rgba(0, 0, 0, 0.45) !important;
box-shadow: 0 0 12px rgba(255, 255, 255, 0.15) !important;
}}
.input-wrapper input:-webkit-autofill,
.input-wrapper input:-webkit-autofill:hover, 
.input-wrapper input:-webkit-autofill:focus, 
.input-wrapper input:-webkit-autofill:active {{
-webkit-box-shadow: 0 0 0 1000px rgba(10, 20, 45, 0.75) inset !important;
-webkit-text-fill-color: #ffffff !important;
transition: background-color 5000s ease-in-out 0s !important;
border: 1px solid rgba(255, 255, 255, 0.4) !important;
}}
.input-icon {{
position: absolute !important;
left: 14px !important;
top: 50% !important;
transform: translateY(-50%) !important;
width: 18px !important;
height: 18px !important;
background-size: contain !important;
background-repeat: no-repeat !important;
pointer-events: none !important;
opacity: 0.65 !important;
transition: all 0.3s ease !important;
}}
.input-wrapper input:focus ~ .input-icon {{
opacity: 0.95 !important;
filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.4)) !important;
}}
.user-icon {{
background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>') !important;
}}
.lock-icon {{
background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>') !important;
}}
.password-toggle {{
position: absolute !important;
right: 14px !important;
top: 50% !important;
transform: translateY(-50%) !important;
width: 20px !important;
height: 20px !important;
background-size: contain !important;
background-repeat: no-repeat !important;
background-color: transparent !important;
border: none !important;
cursor: pointer !important;
opacity: 0.45 !important;
transition: all 0.3s ease !important;
background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>') !important;
z-index: 100 !important;
pointer-events: auto !important;
}}
.password-toggle:hover {{
opacity: 0.8 !important;
}}
.password-toggle.visible {{
background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 19c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>') !important;
}}
.custom-form-options {{
display: flex !important;
justify-content: space-between !important;
align-items: center !important;
margin-top: 10px !important;
margin-bottom: 24px !important;
width: 100% !important;
}}
.custom-checkbox-container {{
display: flex !important;
align-items: center !important;
position: relative !important;
padding-left: 24px !important;
cursor: pointer !important;
font-size: 13.5px !important;
color: rgba(255, 255, 255, 0.7) !important;
user-select: none !important;
}}
.custom-checkbox-container input {{
position: absolute !important;
opacity: 0 !important;
cursor: pointer !important;
height: 0 !important;
width: 0 !important;
}}
.checkmark {{
position: absolute !important;
left: 0 !important;
top: 50% !important;
transform: translateY(-50%) !important;
height: 16px !important;
width: 16px !important;
background-color: rgba(255, 255, 255, 0.05) !important;
border: 1px solid rgba(255, 255, 255, 0.25) !important;
border-radius: 4px !important;
transition: all 0.2s ease !important;
}}
.custom-checkbox-container:hover input ~ .checkmark {{
background-color: rgba(255, 255, 255, 0.1) !important;
border-color: rgba(255, 255, 255, 0.35) !important;
}}
.custom-checkbox-container input:checked ~ .checkmark {{
background-color: #40d97a !important;
border-color: #40d97a !important;
}}
.checkmark:after {{
content: "" !important;
position: absolute !important;
display: none !important;
}}
.custom-checkbox-container input:checked ~ .checkmark:after {{
display: block !important;
}}
.custom-checkbox-container .checkmark:after {{
left: 5px !important;
top: 2px !important;
width: 4px !important;
height: 8px !important;
border: solid white !important;
border-width: 0 2px 2px 0 !important;
transform: rotate(45deg) !important;
}}
.forgot-password {{
color: #a78bfa !important;
font-size: 13.5px !important;
text-decoration: none !important;
font-weight: 500 !important;
opacity: 0.85 !important;
transition: opacity 0.2s ease, color 0.2s ease !important;
}}
.forgot-password:hover {{
opacity: 1 !important;
color: #c084fc !important;
}}
.custom-submit-btn {{
background: linear-gradient(90deg, #40d97a, #8854ff) !important;
color: white !important;
border: none !important;
border-radius: 14px !important;
font-weight: 700 !important;
font-size: 16px !important;
letter-spacing: 1px !important;
height: 52px !important;
width: 100% !important;
box-shadow: 0 4px 15px rgba(64, 217, 122, 0.2) !important;
transition: all 0.3s ease !important;
cursor: pointer !important;
display: flex !important;
align-items: center !important;
justify-content: center !important;
box-sizing: border-box !important;
margin-top: 10px !important;
}}
.custom-submit-btn:hover {{
transform: translateY(-2px) !important;
box-shadow: 0 6px 20px rgba(136, 84, 255, 0.35) !important;
filter: brightness(1.05) !important;
}}
.custom-submit-btn:active {{
transform: translateY(0) !important;
}}
.login-error-banner {{
background: rgba(239, 68, 68, 0.12) !important;
border: 1px solid rgba(239, 68, 68, 0.25) !important;
border-radius: 12px !important;
padding: 12px 16px !important;
margin-bottom: 20px !important;
color: #fca5a5 !important;
font-size: 13px !important;
display: flex !important;
align-items: center !important;
gap: 10px !important;
box-sizing: border-box !important;
text-align: left !important;
}}
.login-error-banner svg {{
flex-shrink: 0 !important;
width: 18px !important;
height: 18px !important;
stroke: #f87171 !important;
}}
.card-footer {{
display: flex !important;
flex-direction: column !important;
align-items: center !important;
gap: 6px !important;
margin-top: 24px !important;
font-size: 11px !important;
color: rgba(255, 255, 255, 0.45) !important;
border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
padding-top: 16px !important;
width: 100% !important;
box-sizing: border-box !important;
}}
.footer-row {{
display: flex !important;
justify-content: center !important;
align-items: center !important;
gap: 8px !important;
color: #5ae893 !important;
font-weight: 500 !important;
}}
.footer-row svg {{
stroke: #5ae893 !important;
}}
.footer-signature {{
color: rgba(255, 255, 255, 0.6) !important;
font-size: 11px !important;
margin-top: 2px !important;
}}
.footer-signature strong {{
color: #ffffff !important;
letter-spacing: 0.5px !important;
}}
</style>
<div class="custom-login-overlay">
<div class="custom-login-container">
<div class="custom-login-card">
<div class="login-logo-container">
{logo_html}
<div class="login-subtitle">Sistema Integrado de Gestão</div>
<div class="color-divider"></div>
<div class="modules-bar">
<div class="module-item">🌱 PRODUÇÃO</div>
<span class="module-dot">&bull;</span>
<div class="module-item">📦 ESTOQUE</div>
<span class="module-dot">&bull;</span>
<div class="module-item">🛒 COMERCIAL</div>
<span class="module-dot">&bull;</span>
<div class="module-item">📊 FINANCEIRO</div>
</div>
</div>
{error_banner_html}
<form id="custom-login-form">
<div class="custom-input-group">
<span class="custom-input-label">E-mail</span>
<div class="input-wrapper">
<input type="text" id="custom-email" required placeholder="Digite seu e-mail" autocomplete="username">
<span class="input-icon user-icon"></span>
</div>
</div>
<div class="custom-input-group">
<span class="custom-input-label">Senha</span>
<div class="input-wrapper">
<input type="password" id="custom-password" required placeholder="Digite sua senha" autocomplete="current-password">
<span class="input-icon lock-icon"></span>
<button type="button" class="password-toggle" id="custom-password-toggle"></button>
</div>
</div>
<div class="custom-form-options">
<label class="custom-checkbox-container">
<input type="checkbox" id="custom-remember" checked>
<span class="checkmark"></span>
Lembrar-me
</label>
<a href="#" class="forgot-password">Esqueci minha senha</a>
</div>
<button type="submit" class="custom-submit-btn">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 20px; height: 20px; margin-right: 8px; display: inline-block; vertical-align: middle;"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
<span>ENTRAR</span>
</button>
</form>
<div class="card-footer">
<div class="footer-row">
<span><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; margin-right: 4px; display: inline-block; vertical-align: middle;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Ambiente Corporativo</span>
<span>|</span>
<span>Versão 1.7</span>
</div>
<div class="footer-signature">
Powered by <strong>DAATEL</strong> &bull; Wisdom into Tech
</div>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    # JavaScript executado diretamente no contexto do pai (parent DOM) via injeção por onerror (evita bloqueios de CORS do iframe components.html)
    st.markdown("""
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onerror="
    if (!window.__loginScriptInjected) {
        window.__loginScriptInjected = true;
        const script = document.createElement('script');
        script.textContent = `
            (function() {
                const doc = document;

                function togglePasswordVisibility() {
                    const passwordInput = doc.getElementById('custom-password');
                    const toggleButton = doc.getElementById('custom-password-toggle') || doc.querySelector('.password-toggle');
                    if (passwordInput && toggleButton) {
                        if (passwordInput.type === 'password') {
                            passwordInput.type = 'text';
                            toggleButton.classList.add('visible');
                        } else {
                            passwordInput.type = 'password';
                            toggleButton.classList.remove('visible');
                        }
                    }
                }

                function getNativeForm() {
                    const allInputs = doc.querySelectorAll('input[placeholder=\\'Digite seu e-mail\\']');
                    for (let i = 0; i < allInputs.length; i++) {
                        if (!allInputs[i].closest('.custom-login-container')) {
                            const form = allInputs[i].closest('[data-testid=\\'stForm\\']');
                            if (form) return form;
                        }
                    }
                    return doc.querySelector('div[data-testid=\\'stForm\\']');
                }

                function getNativeEmail(nativeForm) {
                    if (!nativeForm) return null;
                    return nativeForm.querySelector('input[placeholder=\\'Digite seu e-mail\\']') ||
                        nativeForm.querySelector('input[type=\\'text\\']');
                }

                function getNativeSenha(nativeForm) {
                    if (!nativeForm) return null;
                    return nativeForm.querySelector('input[placeholder=\\'Digite sua senha\\']') ||
                        nativeForm.querySelector('input[type=\\'password\\']');
                }

                function getNativeSubmit(nativeForm) {
                    if (!nativeForm) return null;
                    return nativeForm.querySelector('div[data-testid=\\'stFormSubmitButton\\'] button') ||
                        nativeForm.querySelector('button[kind=\\'formSubmit\\']') ||
                        nativeForm.querySelector('button[type=\\'submit\\']') ||
                        nativeForm.querySelector('button') ||
                        doc.querySelector('div[data-testid=\\'stFormSubmitButton\\'] button');
                }

                function getNativeCheckbox(nativeForm) {
                    if (!nativeForm) return null;
                    return nativeForm.querySelector('input[type=\\'checkbox\\']') ||
                        doc.querySelector('div[data-testid=\\'stCheckbox\\'] input');
                }

                function syncCheckbox() {
                    const customRemember = doc.getElementById('custom-remember');
                    const nativeForm = getNativeForm();
                    const nativeCheckbox = getNativeCheckbox(nativeForm);
                    if (customRemember && nativeCheckbox && nativeCheckbox.checked !== customRemember.checked) {
                        nativeCheckbox.click();
                    }
                }

                function setNativeValue(element, value) {
                    try {
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(element, value);
                    } catch(e) {
                        try {
                            const proto = Object.getPrototypeOf(element);
                            const setter = Object.getOwnPropertyDescriptor(proto, 'value');
                            if (setter && setter.set) {
                                setter.set.call(element, value);
                            } else {
                                element.value = value;
                            }
                        } catch(e2) {
                            element.value = value;
                        }
                    }
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new Event('blur', { bubbles: true }));
                }

                function submitLoginForm() {
                    const customEmail = doc.getElementById('custom-email');
                    const customSenha = doc.getElementById('custom-password');
                    if (!customEmail || !customSenha) {
                        console.error('[LOGIN] Campos customizados nao encontrados');
                        return;
                    }
                    const emailVal = customEmail.value;
                    const senhaVal = customSenha.value;
                    if (!emailVal || !senhaVal) {
                        console.error('[LOGIN] Campos vazios');
                        return;
                    }

                    sessionStorage.setItem('logged_email', emailVal);
                    sessionStorage.setItem('logged_password', senhaVal);
                    sessionStorage.setItem('last_active', Date.now().toString());

                    const nativeForm = getNativeForm();
                    if (!nativeForm) {
                        console.error('[LOGIN] Form nativo nao encontrado');
                        return;
                    }

                    const nativeEmail = getNativeEmail(nativeForm);
                    const nativeSenha = getNativeSenha(nativeForm);
                    const nativeSubmit = getNativeSubmit(nativeForm);

                    if (nativeEmail && nativeSenha && nativeSubmit) {
                        setNativeValue(nativeEmail, emailVal);
                        setNativeValue(nativeSenha, senhaVal);
                        syncCheckbox();

                        setTimeout(function() {
                            nativeSubmit.focus();
                            nativeSubmit.click();
                            console.log('[LOGIN] Submit clicado');
                        }, 150);
                    } else {
                        console.error('[LOGIN] Campos nativos nao encontrados');
                    }
                }

                function disableNativeAutofill() {
                    const nativeForm = getNativeForm();
                    if (!nativeForm) return;
                    const inputs = nativeForm.querySelectorAll('input');
                    inputs.forEach(function(input) {
                        input.setAttribute('autocomplete', 'off');
                        input.setAttribute('readonly', 'readonly');
                        setTimeout(function() { input.removeAttribute('readonly'); }, 200);
                    });
                }

                function waitAndSetup() {
                    if (doc.getElementById('custom-login-form')) {
                        disableNativeAutofill();

                        const customEmail = doc.getElementById('custom-email');
                        const customSenha = doc.getElementById('custom-password');
                        if (customEmail) {
                            customEmail.setAttribute('autocomplete', 'off');
                        }
                        if (customSenha) {
                            customSenha.setAttribute('autocomplete', 'new-password');
                        }

                        const savedEmail = sessionStorage.getItem('logged_email');
                        const savedPassword = sessionStorage.getItem('logged_password');
                        const lastActive = sessionStorage.getItem('last_active');

                        if (savedEmail && savedPassword && lastActive) {
                            const TIMEOUT_MS = 60 * 60 * 1000;
                            const idleTime = Date.now() - parseInt(lastActive, 10);
                            if (idleTime < TIMEOUT_MS) {
                                sessionStorage.setItem('last_active', Date.now().toString());
                                if (customEmail) customEmail.value = savedEmail;
                                if (customSenha) customSenha.value = savedPassword;
                                setTimeout(submitLoginForm, 200);
                                return;
                            } else {
                                sessionStorage.removeItem('logged_email');
                                sessionStorage.removeItem('logged_password');
                                sessionStorage.removeItem('last_active');
                            }
                        }

                        if (customEmail) customEmail.value = '';
                        if (customSenha) customSenha.value = '';

                        console.log('[LOGIN] Setup completo');
                    } else {
                        setTimeout(waitAndSetup, 100);
                    }
                }
                waitAndSetup();

                if (!doc.__loginListenersAttached) {
                    doc.addEventListener('submit', function(event) {
                        const form = event.target.closest('#custom-login-form');
                        if (form) {
                            event.preventDefault();
                            submitLoginForm();
                        }
                    });

                    doc.addEventListener('click', function(event) {
                        const toggleBtn = event.target.closest('#custom-password-toggle') || event.target.closest('.password-toggle');
                        if (toggleBtn) {
                            event.preventDefault();
                            event.stopPropagation();
                            togglePasswordVisibility();
                        }

                        const forgotPwd = event.target.closest('.forgot-password');
                        if (forgotPwd) {
                            event.preventDefault();
                            event.stopPropagation();
                            const nativeForgotBtn = doc.querySelector('div.st-key-esqueci_btn button');
                            if (nativeForgotBtn) {
                                nativeForgotBtn.click();
                            }
                        }
                    });

                    doc.addEventListener('change', function(event) {
                        const rememberCheckbox = event.target.closest('#custom-remember');
                        if (rememberCheckbox) {
                            syncCheckbox();
                        }
                    });
                    doc.__loginListenersAttached = true;
                }
            })();
        `;
        document.body.appendChild(script);
    }
" style="display:none;">
    """, unsafe_allow_html=True)


def carregar_cabecalho_usuario(logged_user, user_role):
    pass


def limpar_session_storage_js():
    import streamlit.components.v1 as components
    components.html("""
<script>
    sessionStorage.removeItem('logged_email');
    sessionStorage.removeItem('logged_password');
    sessionStorage.removeItem('last_active');
    console.log('[SESSION] sessionStorage limpo com sucesso.');
</script>
""", height=0)


def carregar_rastreador_inatividade():
    import streamlit.components.v1 as components
    components.html("""
<script>
(function() {
    const doc = window.parent.document;
    const TIMEOUT_MS = 60 * 60 * 1000; // 60 minutos em milissegundos
    
    // Atualiza a última atividade no sessionStorage
    function registrarAtividade() {
        sessionStorage.setItem('last_active', Date.now().toString());
    }
    
    // Configura os escutadores de eventos para detectar interação do usuário
    doc.addEventListener('mousemove', registrarAtividade);
    doc.addEventListener('mousedown', registrarAtividade);
    doc.addEventListener('keypress', registrarAtividade);
    doc.addEventListener('scroll', registrarAtividade);
    doc.addEventListener('touchstart', registrarAtividade);
    
    // Registra a atividade inicial na carga da página
    if (!sessionStorage.getItem('last_active')) {
        registrarAtividade();
    }
    
    // Verifica inatividade periodicamente (a cada 10 segundos)
    const checkInterval = setInterval(function() {
        const lastActive = parseInt(sessionStorage.getItem('last_active') || "0", 10);
        if (lastActive > 0) {
            const idleTime = Date.now() - lastActive;
            if (idleTime >= TIMEOUT_MS) {
                console.log('[SESSION] Inatividade detectada! Expulso por timeout de 60 minutos.');
                clearInterval(checkInterval);
                
                // Limpa os dados de login
                sessionStorage.removeItem('logged_email');
                sessionStorage.removeItem('logged_password');
                sessionStorage.removeItem('last_active');
                
                // Procura e clica no botão "Sair" do Streamlit
                const buttons = doc.querySelectorAll('button');
                let clicked = false;
                for (let btn of buttons) {
                    if (btn.textContent && btn.textContent.trim() === 'Sair') {
                        btn.click();
                        clicked = true;
                        break;
                    }
                }
                if (!clicked) {
                    window.parent.location.reload();
                }
            }
        }
    }, 10000);
})();
</script>
""", height=0)

