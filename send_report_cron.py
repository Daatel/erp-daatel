import os
import sys

# Garante que a pasta atual está no path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock de st.secrets do Streamlit para rodar em linha de comando (GitHub Actions ou local)
import streamlit as st

database_url = None

# 1. Tenta carregar a partir das variáveis de ambiente (GitHub Actions)
if "DATABASE_URL" in os.environ:
    database_url = os.environ["DATABASE_URL"]

# 2. Se não estiver no ambiente, tenta ler o arquivo local .streamlit/secrets.toml
if not database_url:
    secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL") and "=" in line:
                        val = line.split("=", 1)[1].strip()
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        database_url = val
                        break
        except Exception as e:
            print(f"Aviso: Erro ao ler .streamlit/secrets.toml: {e}")

if database_url:
    st.secrets = {"DATABASE_URL": database_url}
    print("[OK] Conexao com PostgreSQL (Supabase) configurada para a execucao do relatorio.")
else:
    print("[AVISO] DATABASE_URL nao encontrada. Usando SQLite local (fallback).")
    st.secrets = {}

from database import enviar_relatorio_resumo_executivo

def run():
    print("[START] [CRON] Iniciando disparo automatico do Resumo Executivo...")
    res, err_msg = enviar_relatorio_resumo_executivo()
    if res:
        print("[OK] [CRON] Resumo Executivo enviado com sucesso via Telegram!")
    else:
        print(f"[ERRO] [CRON] Falha no envio do Resumo: {err_msg}")

    # Determina a hora atual calculada em Brasília (UTC - 3)
    import datetime
    hora_brasilia = (datetime.datetime.utcnow().hour - 3) % 24
    print(f"[INFO] [CRON] Horario de Brasilia calculado: {hora_brasilia}:00")

    # Se for o disparo da noite (a partir das 17:00 de Brasília) ou manual de fim do dia
    if hora_brasilia >= 17 or hora_brasilia <= 2:
        print("[START] [CRON] Iniciando disparo automatico da Profilaxia Financeira...")
        from database import enviar_relatorio_profilaxia
        res_prof, err_prof = enviar_relatorio_profilaxia()
        if res_prof:
            print("[OK] [CRON] Relatorio de Profilaxia enviado com sucesso via Telegram!")
        else:
            print(f"[ERRO] [CRON] Falha no envio da Profilaxia: {err_prof}")

if __name__ == "__main__":
    run()
