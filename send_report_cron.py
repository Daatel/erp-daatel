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
        print("✅ [CRON] Resumo Executivo enviado com sucesso via Telegram!")
    else:
        print(f"❌ [CRON] Falha no envio do Resumo: {err_msg}")

    # Determina a hora atual calculada em Brasília (UTC - 3)
    import datetime
    hora_brasilia = (datetime.datetime.utcnow().hour - 3) % 24
    print(f"ℹ️ [CRON] Horário de Brasília calculado: {hora_brasilia}:00")

    # Se for o disparo da noite (a partir das 17:00 de Brasília) ou manual de fim do dia
    if hora_brasilia >= 17 or hora_brasilia <= 2:
        print("🚀 [CRON] Iniciando disparo automático da Profilaxia Financeira...")
        from database import enviar_relatorio_profilaxia
        res_prof, err_prof = enviar_relatorio_profilaxia()
        if res_prof:
            print("✅ [CRON] Relatório de Profilaxia enviado com sucesso via Telegram!")
        else:
            print(f"❌ [CRON] Falha no envio da Profilaxia: {err_prof}")

if __name__ == "__main__":
    run()
