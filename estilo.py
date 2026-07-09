import streamlit as st

def carregar_estilo():
    st.markdown("""
    <style>
        .stTextInput label p, .stSelectbox label p, .stNumberInput label p, .stDateInput label p {
            color: #01743d !important;
            font-weight: 600 !important;
        }
        /* --- CORREÇÃO GERAL DE ENTRADAS DE DADOS (INPUTS CLAROS E LEGÍVEIS) --- */
        .stTextInput > div, .stNumberInput > div, .stDateInput > div, .stTextArea > div {
            background-color: #ffffff !important;
            border-radius: 6px !important;
        }
        .stTextInput div, .stNumberInput div, .stDateInput div, .stTextArea div {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }
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
        /* Caixas de Seleção (Selectbox / Dropdown / Multiselect) */
        .stSelectbox > div, .stMultiSelect > div {
            background-color: #ffffff !important;
            border-radius: 6px !important;
        }
        .stSelectbox div, .stMultiSelect div {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        div[data-baseweb="select"] > div {
            border-color: #01743d40 !important;
            background-color: #ffffff !important;
        }
        div[data-baseweb="select"] div {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        div[data-baseweb="select"] * {
            color: #0f172a !important;
        }
        div[data-baseweb="select"] svg {
            fill: #0f172a !important;
            color: #0f172a !important;
        }
        /* Ajuste do dropdown (popover de opções quando aberto) */
        div[role="listbox"], div[data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        div[role="listbox"] ul, div[data-baseweb="menu"] ul {
            background-color: #ffffff !important;
        }
        div[role="listbox"] li, div[data-baseweb="menu"] li {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        div[role="listbox"] li:hover, div[data-baseweb="menu"] li:hover,
        div[role="listbox"] [aria-selected="true"], div[data-baseweb="menu"] [aria-selected="true"] {
            background-color: #f1f5f9 !important;
            color: #01743d !important;
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


def carregar_estilo_login(error_msg=None, logo_html="", fundo_base64="", fundo_largo_base64="", session_token=None):
    """
    Aplica estilo glassmorphic a tela de login via CSS puro.
    O formulario nativo do Streamlit e estilizado diretamente.
    Zero ponte JavaScript, maxima confiabilidade de login.
    """
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
* {{ font-family: 'Outfit', sans-serif !important; }}
header[data-testid="stHeader"] {{ visibility: hidden !important; }}
div[data-testid="stDecoration"] {{ display: none !important; }}
footer {{ visibility: hidden !important; }}
section[data-testid="stSidebar"] {{ display: none !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="collapsedSidebar"] {{ display: none !important; }}
.daatel-brand-footer-native {{ display: none !important; }}
[data-testid="stAppViewContainer"] {{
    background-image: url('data:image/png;base64,{fundo_base64}') !important;
    background-size: cover !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
    min-height: 100vh !important;
}}
@media (min-width: 1024px) {{
    [data-testid="stAppViewContainer"] {{
        background-image: url('data:image/png;base64,{fundo_largo_base64}') !important;
    }}
}}
[data-testid="stMainBlockContainer"], .block-container {{
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    min-height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    background: transparent !important;
}}
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
div[data-testid="stForm"] {{
    background-image:
        linear-gradient(180deg, rgba(255,255,255,0.12) 0%, transparent 25%),
        radial-gradient(circle at bottom left, rgba(70,255,140,0.10) 0%, transparent 45%),
        radial-gradient(circle at top right, rgba(180,110,255,0.12) 0%, transparent 45%),
        linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%) !important;
    background-color: rgba(15,30,65,0.55) !important;
    backdrop-filter: blur(22px) !important;
    -webkit-backdrop-filter: blur(22px) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 32px !important;
    padding: 35px 30px 25px 30px !important;
    box-shadow:
        inset 0 0 1px rgba(255,255,255,0.35),
        0 0 25px rgba(70,255,140,0.08),
        0 0 35px rgba(180,110,255,0.08),
        0 10px 40px rgba(0,0,0,0.25) !important;
    box-sizing: border-box !important;
    position: relative !important;
    width: 100% !important;
    left: auto !important;
    top: auto !important;
    height: auto !important;
    opacity: 1 !important;
    transition: all 0.3s ease !important;
    max-width: 420px !important;
    margin: 0 auto !important;
}}
div[data-testid="stForm"]:hover {{
    border-color: rgba(255,255,255,0.25) !important;
    box-shadow:
        inset 0 0 2px rgba(255,255,255,0.45),
        0 0 35px rgba(70,255,140,0.12),
        0 0 45px rgba(180,110,255,0.12),
        0 15px 50px rgba(0,0,0,0.3) !important;
}}
div[data-testid="stForm"] label p {{
    color: #5ae893 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] {{
    background: transparent !important;
    border-radius: 12px !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div {{
    background: rgba(0,0,0,0.35) !important;
    border-color: rgba(255,255,255,0.4) !important;
    border-radius: 12px !important;
    height: 50px !important;
    transition: all 0.3s ease !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within {{
    border-color: rgba(255,255,255,0.8) !important;
    background: rgba(0,0,0,0.45) !important;
    box-shadow: 0 0 12px rgba(255,255,255,0.15) !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] input {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: transparent !important;
    font-size: 15px !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] input::placeholder {{
    color: rgba(255,255,255,0.45) !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] input:-webkit-autofill,
div[data-testid="stForm"] div[data-baseweb="input"] input:-webkit-autofill:hover,
div[data-testid="stForm"] div[data-baseweb="input"] input:-webkit-autofill:focus {{
    -webkit-box-shadow: 0 0 0 1000px rgba(10,20,45,0.75) inset !important;
    -webkit-text-fill-color: #ffffff !important;
    transition: background-color 5000s ease-in-out 0s !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
}}
div[data-testid="stForm"] div[data-testid="stCheckbox"] label p,
div[data-testid="stForm"] div[data-testid="stCheckbox"] label span {{
    color: rgba(255,255,255,0.7) !important;
    font-size: 13.5px !important;
}}
div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {{
    background: linear-gradient(90deg, #40d97a, #8854ff) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    letter-spacing: 1px !important;
    height: 52px !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(64,217,122,0.2) !important;
    transition: all 0.3s ease !important;
    margin-top: 10px !important;
    cursor: pointer !important;
}}
div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(136,84,255,0.35) !important;
    filter: brightness(1.05) !important;
}}
div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:active {{
    transform: translateY(0) !important;
}}
div[data-testid="stForm"] div[data-testid="stAlert"] {{
    background: rgba(239,68,68,0.12) !important;
    border: 1px solid rgba(239,68,68,0.25) !important;
    border-radius: 12px !important;
    color: #fca5a5 !important;
}}
div[data-testid="stForm"] div[data-testid="stAlert"] p,
div[data-testid="stForm"] div[data-testid="stAlert"] span {{
    color: #fca5a5 !important;
}}
div.st-key-esqueci_btn {{ text-align: right !important; margin-top: -4px !important; }}
div.st-key-esqueci_btn button {{
    background: transparent !important;
    color: #a78bfa !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    padding: 4px 0 !important;
    width: auto !important;
}}
div.st-key-esqueci_btn button:hover {{
    color: #c084fc !important;
    background: transparent !important;
    box-shadow: none !important;
}}
.login-logo-container {{ text-align: center !important; margin-bottom: 15px !important; }}
.login-logo-container img {{ width: 190px !important; filter: drop-shadow(0 0 12px rgba(255,255,255,0.15)) !important; margin-bottom: 12px !important; display: inline-block !important; }}
.login-subtitle {{ color: #d7d7d7 !important; font-size: 15px !important; text-align: center !important; margin: 0 0 8px 0 !important; font-weight: 500 !important; }}
.color-divider {{ height: 2px !important; width: 60px !important; margin: 0 auto 15px auto !important; background: linear-gradient(90deg, #40d97a 0%, #8854ff 100%) !important; border-radius: 2px !important; }}
.modules-bar {{ display: flex !important; justify-content: center !important; align-items: center !important; gap: 6px !important; color: #dcdcdc !important; font-size: 11px !important; margin-bottom: 10px !important; background: transparent !important; border: none !important; flex-wrap: wrap !important; letter-spacing: 0.5px !important; }}
.module-item {{ display: flex !important; align-items: center !important; gap: 3px !important; font-weight: 500 !important; color: #dcdcdc !important; }}
.module-dot {{ color: rgba(255,255,255,0.35) !important; font-size: 12px !important; }}
.card-footer {{ display: flex !important; flex-direction: column !important; align-items: center !important; gap: 6px !important; margin-top: 24px !important; font-size: 11px !important; color: rgba(255,255,255,0.45) !important; border-top: 1px solid rgba(255,255,255,0.08) !important; padding-top: 16px !important; width: 100% !important; box-sizing: border-box !important; }}
.footer-signature strong {{ color: #ffffff !important; letter-spacing: 0.5px !important; }}
</style>""", unsafe_allow_html=True)


def carregar_cabecalho_usuario(logged_user, user_role):
    pass


def limpar_session_storage_js():
    import streamlit.components.v1 as components
    components.html("""
<script>
    sessionStorage.removeItem('logged_email');
    sessionStorage.removeItem('logged_password');
    sessionStorage.removeItem('last_active');
    sessionStorage.removeItem('session_token');
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
                sessionStorage.removeItem('session_token');
                
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

