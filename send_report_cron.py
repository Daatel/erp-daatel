import os
import sys

# Garante que a pasta atual está no path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock de st.secrets do Streamlit para rodar em linha de comando (GitHub Actions)
import streamlit as st
if "DATABASE_URL" in os.environ:
    st.secrets = {"DATABASE_URL": os.environ["DATABASE_URL"]}
else:
    print("Aviso: DATABASE_URL não encontrada no ambiente. Usando SQLite local.")
    st.secrets = {}

from database import enviar_relatorio_resumo_executivo

def run():
    print("🚀 [CRON] Iniciando disparo automático do Resumo Executivo...")
    res, err_msg = enviar_relatorio_resumo_executivo()
    if res:
        print("✅ [CRON] Relatório diário disparado com sucesso via Telegram!")
    else:
        print(f"❌ [CRON] Falha no envio do relatório: {err_msg}")

if __name__ == "__main__":
    run()
