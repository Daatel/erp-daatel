@echo off
REM Script de Inicialização Única (Singleton) do Voice Bridge ERP DAATEL
netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [CHECK] Voice Bridge ja esta rodando na porta 8000. Nenhuma nova instancia iniciada.
    exit /b 0
)
echo [START] Iniciando Voice Bridge na porta 8000...
python -u api_voice_bridge.py
