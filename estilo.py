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


def carregar_estilo_login(error_msg=None, logo_html=""):
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
#root div[data-testid="stForm"] {{
position: absolute !important;
left: -9999px !important;
top: -9999px !important;
width: 1px !important;
height: 1px !important;
opacity: 0 !important;
pointer-events: none !important;
}}
.daatel-brand-footer-native {{
display: none !important;
}}
[data-testid="stAppViewContainer"] {{
background: 
radial-gradient(circle at top left, #133f5e 0%, transparent 40%),
radial-gradient(circle at bottom right, #5d2f8e 0%, transparent 35%),
linear-gradient(135deg,#07172f,#0c2748,#081225) !important;
background-attachment: fixed !important;
position: relative !important;
overflow: hidden !important;
min-height: 100vh !important;
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
background: rgba(18,45,90,0.55) !important;
backdrop-filter: blur(28px) saturate(180%) !important;
-webkit-backdrop-filter: blur(28px) saturate(180%) !important;
border: 1px solid rgba(255,255,255,0.15) !important;
border-radius: 32px !important;
padding: 30px 25px 20px 25px !important;
box-shadow:
0 0 30px rgba(70,255,150,.15),
0 0 40px rgba(140,80,255,.15) !important;
box-sizing: border-box !important;
position: relative !important;
}}
.login-logo-container {{
text-align: center;
margin-bottom: 12px;
}}
.login-logo-container img {{
width: 190px !important;
filter: drop-shadow(0 0 12px rgba(255, 255, 255, 0.15)) !important;
margin-bottom: 10px;
display: inline-block !important;
}}
.login-subtitle {{
color: #d7d7d7 !important;
font-size: 15px !important;
text-align: center !important;
margin: 0 0 4px 0 !important;
font-weight: 500 !important;
}}
.login-version {{
color: #d7d7d7 !important;
font-size: 11px !important;
font-weight: 600 !important;
text-align: center !important;
text-transform: uppercase !important;
letter-spacing: 1px !important;
margin: 0 0 12px 0 !important;
}}
.color-divider {{
height: 2px;
width: 50px;
margin: 0 auto 12px auto;
background: linear-gradient(90deg, #40d97a 0%, #8854ff 100%);
border-radius: 2px;
}}
.modules-bar {{
display: flex !important;
justify-content: center !important;
gap: 16px !important;
color: #dcdcdc !important;
font-size: 13px !important;
margin-bottom: 20px !important;
background: transparent !important;
border: none !important;
padding: 0 !important;
flex-wrap: wrap !important;
}}
.module-item {{
display: flex;
align-items: center;
gap: 4px;
font-size: 13px;
font-weight: 400;
color: #dcdcdc !important;
}}
.custom-input-group {{
position: relative !important;
margin-bottom: 16px !important;
width: 100% !important;
}}
.custom-input-group input {{
width: 100% !important;
height: 55px !important;
padding: 16px 16px 16px 44px !important;
background: rgba(255,255,255,0.08) !important;
border: 1px solid rgba(255,255,255,0.15) !important;
backdrop-filter: blur(12px) !important;
-webkit-backdrop-filter: blur(12px) !important;
border-radius: 12px !important;
color: white !important;
font-size: 15px !important;
outline: none !important;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
box-sizing: border-box !important;
}}
.custom-input-group input:hover,
.custom-input-group input:focus {{
border-color: rgba(85, 255, 170, 0.5) !important;
box-shadow: 
0 0 20px rgba(85,255,170,.2),
0 0 20px rgba(180,120,255,.2) !important;
}}
.custom-input-group label {{
position: absolute !important;
left: 44px !important;
top: 50% !important;
transform: translateY(-50%) !important;
color: rgba(255, 255, 255, 0.4) !important;
font-size: 14px !important;
pointer-events: none !important;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
.custom-input-group input:focus ~ label,
.custom-input-group input:not(:placeholder-shown) ~ label {{
top: -6px !important;
left: 4px !important;
font-size: 11px !important;
color: rgba(64, 217, 122, 0.85) !important;
background: transparent !important;
padding: 0 !important;
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
opacity: 0.35 !important;
transition: all 0.3s ease !important;
}}
.custom-input-group input:focus ~ .input-icon {{
opacity: 0.85 !important;
filter: drop-shadow(0 0 4px rgba(64, 217, 122, 0.4)) !important;
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
opacity: 0.35 !important;
transition: all 0.3s ease !important;
background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>') !important;
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
margin-top: -4px !important;
margin-bottom: 20px !important;
width: 100% !important;
}}
.custom-checkbox-container {{
display: flex !important;
align-items: center !important;
position: relative !important;
padding-left: 26px !important;
cursor: pointer !important;
font-size: 13px !important;
color: rgba(255, 255, 255, 0.65) !important;
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
border: 1px solid rgba(255, 255, 255, 0.15) !important;
border-radius: 4px !important;
transition: all 0.2s ease !important;
}}
.custom-checkbox-container:hover input ~ .checkmark {{
background-color: rgba(255, 255, 255, 0.1) !important;
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
color: #8854ff !important;
font-size: 13px !important;
text-decoration: none !important;
font-weight: 500 !important;
opacity: 0.85 !important;
transition: opacity 0.2s ease !important;
}}
.forgot-password:hover {{
opacity: 1 !important;
}}
.custom-submit-btn {{
background: linear-gradient(90deg, #40d97a, #8854ff) !important;
color: white !important;
border: none !important;
border-radius: 14px !important;
font-weight: 700 !important;
font-size: 20px !important;
height: 58px !important;
width: 100% !important;
box-shadow: 0 4px 20px rgba(64, 217, 122, 0.25) !important;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
cursor: pointer !important;
display: flex !important;
align-items: center !important;
justify-content: center !important;
box-sizing: border-box !important;
margin-top: 5px !important;
}}
.custom-submit-btn:hover {{
transform: translateY(-2px) !important;
box-shadow: 0 6px 24px rgba(136, 84, 255, 0.45) !important;
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
justify-content: center !important;
align-items: center !important;
gap: 10px !important;
margin-top: 20px !important;
font-size: 11px !important;
color: #bfbfbf !important;
border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
padding-top: 15px !important;
width: 100% !important;
box-sizing: border-box !important;
opacity: 0.8 !important;
font-family: Arial, sans-serif !important;
}}
.card-footer span {{
display: flex !important;
align-items: center !important;
gap: 4px !important;
}}
.card-footer strong {{
color: #ffffff !important;
letter-spacing: 1px !important;
}}
</style>
<div class="custom-login-overlay">
<div class="custom-login-container">
<div class="custom-login-card">
<div class="login-logo-container">
{logo_html}
<div class="login-subtitle">Sistema Integrado de Gestão</div>
<div class="login-version">Versão 1.0</div>
<div class="color-divider"></div>
<div class="modules-bar">
<div class="module-item">🌱 Produção</div>
<div class="module-item">📦 Estoque</div>
<div class="module-item">🛒 Comercial</div>
<div class="module-item">📊 Financeiro</div>
</div>
</div>
{error_banner_html}
<form id="custom-login-form" onsubmit="event.preventDefault(); submitLoginForm();">
<div class="custom-input-group">
<span class="input-icon user-icon"></span>
<input type="text" id="custom-email" required placeholder=" " autocomplete="username">
<label for="custom-email">E-mail</label>
</div>
<div class="custom-input-group">
<span class="input-icon lock-icon"></span>
<input type="password" id="custom-password" required placeholder=" " autocomplete="current-password">
<label for="custom-password">Senha</label>
<button type="button" class="password-toggle" onclick="togglePasswordVisibility()"></button>
</div>
<div class="custom-form-options">
<label class="custom-checkbox-container">
<input type="checkbox" id="custom-remember" checked onchange="syncCheckbox()">
<span class="checkmark"></span>
Lembrar-me
</label>
<a href="#" class="forgot-password">Esqueci minha senha</a>
</div>
<button type="submit" class="custom-submit-btn">
<span>→ ENTRAR</span>
</button>
</form>
<div class="card-footer">
<span>🛡️ Ambiente Corporativo</span>
<span>|</span>
<span>Powered by <strong>DAATEL</strong> &bull; Wisdom into Tech</span>
</div>
</div>
</div>
</div>
<script>
function togglePasswordVisibility() {{
const passwordInput = document.getElementById('custom-password');
const toggleButton = document.querySelector('.password-toggle');
if (passwordInput.type === 'password') {{
passwordInput.type = 'text';
toggleButton.classList.add('visible');
}} else {{
passwordInput.type = 'password';
toggleButton.classList.remove('visible');
}}
}}
function syncCheckbox() {{
const customRemember = document.getElementById('custom-remember').checked;
const nativeCheckbox = document.querySelector('div[data-testid="stCheckbox"] input');
if (nativeCheckbox && nativeCheckbox.checked !== customRemember) {{
nativeCheckbox.click();
}}
}}
function setNativeValue(element, value) {{
const valueSetter = Object.getOwnPropertyDescriptor(element, 'value');
const prototype = Object.getPrototypeOf(element);
const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value');
if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {{
prototypeValueSetter.set.call(element, value);
}} else {{
valueSetter.set.call(element, value);
}}
element.dispatchEvent(new Event('input', {{ bubbles: true }}));
element.dispatchEvent(new Event('change', {{ bubbles: true }}));
}}
function submitLoginForm() {{
const customEmail = document.getElementById('custom-email').value;
const customSenha = document.getElementById('custom-password').value;
const nativeEmail = document.querySelector('input[placeholder="Digite seu e-mail"]');
const nativeSenha = document.querySelector('input[placeholder="Digite sua senha"]');
const nativeSubmit = document.querySelector('div[data-testid="stFormSubmitButton"] button');
if (nativeEmail && nativeSenha && nativeSubmit) {{
setNativeValue(nativeEmail, customEmail);
setNativeValue(nativeSenha, customSenha);
syncCheckbox();
setTimeout(() => {{
nativeSubmit.click();
}}, 50);
}} else {{
console.error("Native Streamlit inputs not found for mirroring!");
}}
}}
function syncAutofill() {{
const nativeEmail = document.querySelector('input[placeholder="Digite seu e-mail"]');
const nativeSenha = document.querySelector('input[placeholder="Digite sua senha"]');
const customEmail = document.getElementById('custom-email');
const customSenha = document.getElementById('custom-password');
if (nativeEmail && customEmail && nativeEmail.value && !customEmail.value) {{
customEmail.value = nativeEmail.value;
customEmail.dispatchEvent(new Event('input', {{ bubbles: true }}));
}}
if (nativeSenha && customSenha && nativeSenha.value && !customSenha.value) {{
customSenha.value = nativeSenha.value;
customSenha.dispatchEvent(new Event('input', {{ bubbles: true }}));
}}
}}
const autofillInterval = setInterval(syncAutofill, 200);
document.getElementById('custom-login-form').addEventListener('submit', () => {{
clearInterval(autofillInterval);
}});
</script>""", unsafe_allow_html=True)
