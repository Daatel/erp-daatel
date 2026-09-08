@echo off
chcp 65001 >nul
title Backup Versionado - ERP Fabrica de Alho

set "ORIGEM=C:\Users\MARCIO\Gestao_Fabrica_Alho"
set "DESTINO=C:\Users\MARCIO\OneDrive\Backups_ERP"

:: Cria pasta de backups se não existir
if not exist "%DESTINO%" mkdir "%DESTINO%"

echo =============================================
echo   BACKUP VERSIONADO - ERP FABRICA DE ALHO
echo =============================================
echo.

:: Mostra versões existentes
echo --- Versões existentes no OneDrive ---
dir /b /o-d "%DESTINO%\ERP_Backup_*.zip" 2>nul || echo   (nenhuma versão encontrada)
echo.

:: Gera nome com timestamp
for /f "tokens=1-6 delims=/:. " %%a in ("%date% %time%") do (
    set "TIMESTAMP=%%a-%%b-%%c_%%d%%e%%f"
)
set "ARQUIVO=%DESTINO%\ERP_Backup_%TIMESTAMP%.zip"

echo Criando backup: %ARQUIVO%
echo.

:: Comprime usando PowerShell
powershell -Command "Compress-Archive -Path '%ORIGEM%\*' -DestinationPath '%ARQUIVO%' -Force"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Backup criado com sucesso!
    echo    Arquivo: %ARQUIVO%
    echo.
    
    :: Limpa versões antigas (mantém as últimas 10)
    powershell -Command "$files = Get-ChildItem '%DESTINO%\ERP_Backup_*.zip' | Sort-Object LastWriteTime -Descending; if ($files.Count -gt 10) { $files | Select-Object -Skip 10 | Remove-Item -Force; Write-Host '   Versões antigas removidas (mantidas as últimas 10).' }"
    
    echo.
    echo --- Versões disponíveis agora ---
    dir /b /o-d "%DESTINO%\ERP_Backup_*.zip" 2>nul
) else (
    echo ❌ Erro ao criar o backup!
)

echo.
echo =============================================
pause
