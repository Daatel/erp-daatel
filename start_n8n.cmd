@echo off
REM Script de Inicialização Única (Singleton) do n8n
netstat -ano | findstr ":5678" >nul
if %ERRORLEVEL% EQU 0 (
    echo [CHECK] n8n ja esta rodando na porta 5678. Nenhuma nova instancia iniciada.
    exit /b 0
)
echo [START] Iniciando n8n com N8N_WEBHOOK_URL...
set N8N_WEBHOOK_URL=https://constitutes-camera-cardiac-appendix.trycloudflare.com/
set WEBHOOK_URL=https://constitutes-camera-cardiac-appendix.trycloudflare.com/
npx n8n start
