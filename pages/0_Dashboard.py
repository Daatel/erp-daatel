import streamlit as st
import pandas as pd
from pathlib import Path
from database import fetch_all

st.set_page_config(
    page_title="Gestão Fábrica de Alho - Dashboard",
    page_icon="🧄",
    layout="wide"
)

from estilo import carregar_estilo
carregar_estilo()

st.title("Visão Global")

st.markdown(f"Bem-vindo, **{st.session_state.get('logged_user', 'Usuário')}**. Abaixo está o resumo da operação.")

# KPIs resumidos
st.subheader("Resumo Geral")

col1, col2, col3, col4 = st.columns(4)

try:
    # Busca fluxo de caixa geral
    df_caixa = fetch_all("SELECT tipo, valor FROM fluxo_caixa")
    if not df_caixa.empty:
        entradas = df_caixa[df_caixa['tipo'] == 'Entrada']['valor'].sum()
        saidas = df_caixa[df_caixa['tipo'] == 'Saída']['valor'].sum()
        saldo = entradas - saidas
    else:
        entradas = 0
        saidas = 0
        saldo = 0

    col1.metric("Saldo em Caixa", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Total Entradas", f"R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Total Saídas", f"R$ {saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Total Funcionários Ativos
    df_func = fetch_all("SELECT COUNT(id) as total FROM funcionarios")
    total_func = df_func.iloc[0]['total'] if not df_func.empty else 0
    col4.metric("Funcionários Cadastrados", total_func)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

st.divider()
st.info("Utilize as opções no menu à esquerda para navegar pelas outras seções do ERP.")
