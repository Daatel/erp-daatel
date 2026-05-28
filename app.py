import streamlit as st
import pandas as pd
from pathlib import Path
import os
from database import fetch_all, run_query, initialize_database

os.chdir(Path(__file__).parent)
initialize_database()


if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = None
    st.session_state['user_role'] = None

def login_form_page():
    st.set_page_config(page_title="Login - Fábrica de Alho", page_icon="🔐", layout="centered")
    from estilo import carregar_estilo
    carregar_estilo()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=150)
            
        st.markdown("<h2 style='text-align: center; color: #01743d;'>Login - ERP Fábrica de Alho</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Acesse com seu e-mail e senha departamental.</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### Acesso ao Sistema")
            senha = st.text_input("Senha de Acesso", type="password").strip()
            
            if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                if senha == "daatel2026":
                    st.session_state['logged_user'] = 'Administrador'
                    st.session_state['user_role'] = 'ADMIN'
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")

if not st.session_state['logged_user']:
    pg = st.navigation([st.Page(login_form_page, title="Login", icon="🔐")])
    pg.run()
    st.stop()

# --- ROTEAMENTO COM ST.NAVIGATION (SINGLE TASK) ---
p_dash = st.Page("pages/0_Dashboard.py", title="Dashboard", icon="📊", default=True)
p_cadastros = st.Page("pages/1_Cadastros.py", title="Cadastros Básicos", icon="📝")
p_compras = st.Page("pages/2_Compras.py", title="Compras & XML", icon="🛒")
p_pessoas = st.Page("pages/3_Pessoas.py", title="Pessoas", icon="👥")
p_producao = st.Page("pages/4_Producao.py", title="Chão de Fábrica", icon="🏭")
p_estoque = st.Page("pages/5_Estoque.py", title="Controle de Estoque", icon="📦")
p_vendas = st.Page("pages/6_Pedidos_de_Venda.py", title="Pedidos de Venda", icon="🛒")
p_fat = st.Page("pages/7_Faturamento.py", title="Faturamento e Logística", icon="🧾")
p_log = st.Page("pages/8_Logistica.py", title="Logística (Opcional)", icon="🚚")
p_fin = st.Page("pages/9_Financeiro.py", title="Financeiro e Tesouraria", icon="💰")
p_dre = st.Page("pages/10_DRE.py", title="DRE e Lucratividade", icon="🏛️")
p_ativos = st.Page("pages/11_Ativos_Comodatos.py", title="Ativos e Comodatos", icon="❄️")
p_rentabilidade = st.Page("pages/12_Rentabilidade_Cliente.py", title="Rentabilidade por Cliente", icon="📈")

role = st.session_state['user_role']
pages_dict = {}

if role == 'ADMIN':
    pages_dict = {
        "Menu Executivo": [p_dash, p_dre, p_rentabilidade],
        "Comercial": [p_vendas, p_fat, p_ativos],
        "Operação": [p_producao, p_estoque, p_compras],
        "Backoffice": [p_fin, p_cadastros, p_pessoas, p_log]
    }
elif role == 'VENDAS':
    pages_dict = {
        "Minhas Vendas": [p_dash, p_vendas, p_ativos],
        "Consultas": [p_pessoas, p_estoque]
    }
elif role == 'PRODUCAO':
    pages_dict = {
        "Operação": [p_dash, p_producao],
        "Consultas": [p_estoque, p_cadastros]
    }
elif role == 'COMPRAS':
    pages_dict = {
        "Suprimentos": [p_dash, p_compras],
        "Consultas": [p_estoque, p_cadastros, p_pessoas]
    }
elif role == 'FINANCEIRO':
    pages_dict = {
        "Financeiro": [p_dash, p_fin, p_fat, p_dre, p_rentabilidade],
        "Consultas": [p_cadastros, p_pessoas]
    }
else:
    pages_dict = {"Principal": [p_dash]}

pg = st.navigation(pages_dict)

st.sidebar.markdown(f"### 👤 {st.session_state['logged_user']}")
st.sidebar.markdown(f"**Cargo:** {st.session_state['user_role']}")
if st.sidebar.button("Sair / Logout", use_container_width=True):
    st.session_state['logged_user'] = None
    st.session_state['user_role'] = None
    st.rerun()

# Run the selected page
pg.run()
