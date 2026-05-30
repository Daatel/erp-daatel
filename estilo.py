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
    </style>
    <div class="daatel-footer notranslate" translate="no">
        <span style="display: block; font-size: 9px; text-align: left; opacity: 0.7; margin-bottom: -2px; letter-spacing: 0.5px;">Powered by</span>
        Daatel : Wisdom into Tech
    </div>
    """, unsafe_allow_html=True)


def carregar_estilo_login():
    st.markdown("""
    <style>
        /* Habilita fontes modernas do Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Outfit', sans-serif !important;
        }

        /* 1. Ocultar cabeçalhos, barras decorativas e rodapés padrão do Streamlit */
        header[data-testid="stHeader"] { 
            visibility: hidden !important; 
        }
        div[data-testid="stDecoration"] { 
            display: none !important; 
        }
        footer { 
            visibility: hidden !important; 
        }

        /* 2. Configuração do Background (Escuro com luzes Neon Verde e Roxa) */
        [data-testid="stAppViewContainer"] {
            background-color: #060913 !important;
            background-image: 
                radial-gradient(circle at 10% 85%, rgba(16, 185, 129, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 90% 15%, rgba(139, 92, 246, 0.1) 0%, transparent 40%) !important;
            background-attachment: fixed !important;
        }
        
        /* 3. Limitação do Container Principal (Filosofia Mobile-First a 420px) */
        [data-testid="stMainBlockContainer"] {
            max-width: 450px !important;
            padding: 3rem 1rem !important;
            margin: 0 auto !important;
        }

        /* 4. O Card Glassmorphism (Formulário) */
        div[data-testid="stForm"] {
            background: rgba(11, 17, 33, 0.45) !important;
            backdrop-filter: blur(24px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.14) !important; /* Brilho superior */
            border-radius: 24px !important;
            padding: 35px 25px 25px 25px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5) !important;
            width: 100% !important;
            margin: 0 auto !important;
        }
        
        /* Remove o espaçamento extra padrão do Streamlit dentro do form */
        div[data-testid="stForm"] > div {
            padding: 0 !important;
            border: none !important;
        }

        /* 5. Estilização dos Text Inputs (E-mail e Senha) */
        .stTextInput label p {
            color: rgba(255, 255, 255, 0.5) !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            margin-bottom: 6px !important;
            margin-left: 2px !important;
        }
        
        div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 6px 8px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        div[data-baseweb="input"]:focus-within {
            border-color: rgba(16, 185, 129, 0.6) !important;
            background-color: rgba(255, 255, 255, 0.06) !important;
            box-shadow: 0 0 14px rgba(16, 185, 129, 0.25) !important;
        }
        
        div[data-baseweb="input"] input {
            color: #ffffff !important;
            background-color: transparent !important;
            font-size: 14px !important;
        }
        
        div[data-baseweb="input"] input::placeholder {
            color: rgba(255, 255, 255, 0.3) !important;
        }

        /* 6. Checkbox 'Lembrar-me' */
        div[data-testid="stCheckbox"] {
            margin-top: 10px !important;
            margin-bottom: 10px !important;
        }
        div[data-testid="stCheckbox"] label p {
            color: rgba(255, 255, 255, 0.65) !important;
            font-size: 13px !important;
            font-weight: 400 !important;
        }
        div[data-testid="stCheckbox"] [data-checked="true"] {
            background-color: #10b981 !important;
            border-color: #10b981 !important;
        }

        /* 7. O Botão Degradê de Login */
        div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #10b981 0%, #7c3aed 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            padding: 14px 20px !important;
            width: 100% !important;
            box-shadow: 0 4px 20px rgba(16, 185, 129, 0.25) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: pointer !important;
            margin-top: 20px !important;
        }
        
        div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 24px rgba(124, 58, 237, 0.45) !important;
        }
        
        div[data-testid="stFormSubmitButton"] button:active {
            transform: translateY(0) !important;
        }

        /* 8. Estilos Personalizados das Estruturas HTML */
        .login-logo-container {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .login-logo-container img {
            width: 90px !important;
            height: 90px !important;
            background: #ffffff !important;
            border-radius: 50% !important;
            padding: 8px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35) !important;
            object-fit: contain !important;
            margin-bottom: 12px !important;
            display: inline-block !important;
        }
        
        .login-title {
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            text-align: center !important;
            margin: 0 !important;
            letter-spacing: 0.5px !important;
        }
        
        .login-subtitle {
            color: rgba(255, 255, 255, 0.45) !important;
            font-size: 13px !important;
            text-align: center !important;
            margin-top: 4px !important;
            margin-bottom: 22px !important;
        }
        
        /* Linha decorativa de divisão de cor */
        .color-divider {
            height: 2px;
            width: 50px;
            margin: 0 auto 15px auto;
            background: linear-gradient(90deg, #10b981 0%, #7c3aed 100%);
            border-radius: 2px;
        }

        /* Ícones dos módulos */
        .modules-bar {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 28px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }
        
        .module-item {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            padding: 4px 6px;
            border-radius: 6px;
        }
        
        .mod-prod { color: #10b981; }
        .mod-est { color: #a78bfa; }
        .mod-com { color: #f59e0b; }
        .mod-fin { color: #3b82f6; }

        /* Rodapé interno do card */
        .card-footer {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 25px;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.35);
            letter-spacing: 0.5px;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
            padding-top: 15px;
        }
        
        .card-footer span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Rodapé externo - Powered by Daatel */
        .daatel-brand-footer {
            position: fixed;
            bottom: 20px;
            right: 25px;
            text-align: right;
            opacity: 0.8;
            z-index: 9999;
            transition: opacity 0.3s ease;
        }
        .daatel-brand-footer:hover {
            opacity: 1;
        }
        .daatel-brand-footer span {
            display: block;
            font-size: 8px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgba(255, 255, 255, 0.35);
            margin-bottom: 2px;
        }
        .daatel-brand-footer h4 {
            margin: 0;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            color: #ffffff;
        }
        .daatel-brand-footer p {
            margin: 2px 0 0 0;
            font-size: 9px;
            color: rgba(255, 255, 255, 0.45);
            letter-spacing: 0.5px;
        }
    </style>
    """, unsafe_allow_html=True)

