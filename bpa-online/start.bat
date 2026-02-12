@echo off
echo 🚀 Iniciando BPA Online...
echo.

set "ROOT_DIR=%~dp0"

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Instale Python 3.11 ou superior.
    pause
    exit /b 1
)

REM Verifica Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js não encontrado. Instale Node.js 18 ou superior.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo ✅ Node.js encontrado
echo.

REM Backend
echo 🔧 Iniciando servidor backend (porta 8000)...
cd /d "%ROOT_DIR%backend"
start "BPA Backend" cmd /k "cd /d %ROOT_DIR%backend && %ROOT_DIR%.venv\Scripts\activate.bat && python main.py"

REM Aguarda backend iniciar
timeout /t 3 /nobreak >nul

REM Frontend
echo 🎨 Iniciando servidor frontend (porta 3000)...
cd /d "%ROOT_DIR%frontend"
start "BPA Frontend" cmd /k "cd /d %ROOT_DIR%frontend && npm start"

cd /d "%ROOT_DIR%"

echo.
echo ================================================
echo ✅ BPA Online está rodando!
echo ================================================
echo.
echo 📊 Dashboard: http://localhost:3000
echo 🔌 API:       http://localhost:8000
echo 📖 API Docs:  http://localhost:8000/docs
echo.
echo Feche as janelas de comando para parar os servidores
echo.
pause
