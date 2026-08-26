import os
import sys
import time
import datetime
from playwright.sync_api import sync_playwright

# URL padrao do aplicativo Streamlit da DAATEL
DEFAULT_APP_URL = "https://daatel-erp.streamlit.app"
WAIT_WEBSOCKET_MS = 15000  # Mantem a conexao ativa por ~15s

def log(msg: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

def keep_alive(app_url: str = DEFAULT_APP_URL) -> int:
    log(f"[START] Iniciando verificacao Keep-Alive para: {app_url}")
    
    with sync_playwright() as p:
        # Inicia Chromium headless com configuracoes de performance
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutomateStreamlit/1.0 (DAATEL KeepAlive)"
        )
        page = context.new_page()

        try:
            log("[INFO] Navegando ate o app Streamlit...")
            page.goto(app_url, wait_until="domcontentloaded", timeout=60000)

            # Aguarda renderizacao inicial da pagina
            page.wait_for_timeout(3000)

            # Verificacao 1: O app esta em modo de suspensao ("Zzzz")?
            wake_btn = page.get_by_role("button", name="Yes, get this app back up!")
            
            # Fallback de busca caso o texto mude ligeiramente
            if not wake_btn.is_visible():
                wake_btn = page.locator("button:has-text('get this app back up')")

            if wake_btn.is_visible():
                log("[ALERT] App encontrado em modo de suspensao ('Zzzz'). Clicando para reativar...")
                wake_btn.click()
                log("[INFO] Botao clicado! Aguardando o app acordar e carregar completamente...")
                page.wait_for_selector('[data-testid="stApp"]', timeout=120000)
                log("[SUCCESS] App reativado com sucesso!")
            else:
                log("[INFO] App ja esta ativo (sem tela de suspensao).")

            # Aguarda o elemento principal do Streamlit estar visivel
            try:
                page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
            except Exception:
                log("[AVISO] Elemento stApp nao detectado no tempo limite de 30s. Continuando mantendo sessao...")

            # Mantem a conexao WebSocket ativa por ~15s para garantir registro no Streamlit Cloud
            log(f"[INFO] Mantendo sessao WebSocket ativa por {WAIT_WEBSOCKET_MS / 1000:.0f}s...")
            page.wait_for_timeout(WAIT_WEBSOCKET_MS)

            log("[SUCCESS] Keep-Alive concluido com exito. Conexao mantida ativa!")
            return 0

        except Exception as e:
            log(f"[ERRO] Falha no Keep-Alive: {e}")
            return 1

        finally:
            browser.close()
            log("[FINISHED] Navegador encerrado.")

if __name__ == "__main__":
    target_url = os.getenv("APP_URL", DEFAULT_APP_URL)
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    
    sys.exit(keep_alive(target_url))
