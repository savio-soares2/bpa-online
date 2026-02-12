# ===========================================
#   BPA Online + Firebird Sync - Start All
#   Executa nos terminais do VS Code
# ===========================================

$ROOT = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Iniciando BPA Online + Firebird Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. BPA Online Backend (porta 8000)
Write-Host "[1/4] BPA Online Backend (porta 8000)..." -ForegroundColor Yellow
$bpaBackendScript = @"
cd '$ROOT'
.\.venv\Scripts\Activate.ps1
cd backend
Write-Host '=== BPA Online Backend ===' -ForegroundColor Green
uvicorn main:app --host localhost --port 8000 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $bpaBackendScript

Start-Sleep -Seconds 2

# 2. BPA Online Frontend (porta 3000)
Write-Host "[2/4] BPA Online Frontend (porta 3000)..." -ForegroundColor Yellow
$bpaFrontendScript = @"
cd '$ROOT\frontend'
Write-Host '=== BPA Online Frontend ===' -ForegroundColor Green
npm start
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $bpaFrontendScript

Start-Sleep -Seconds 2

# 3. Firebird Sync Backend (porta 8001)
Write-Host "[3/4] Firebird Sync Backend (porta 8001)..." -ForegroundColor Yellow
$fbBackendScript = @"
cd '$ROOT\firebird-sync\backend'
Write-Host '=== Firebird Sync Backend ===' -ForegroundColor Green
python main.py
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $fbBackendScript

Start-Sleep -Seconds 2

# 4. Firebird Sync Frontend (porta 3001)
Write-Host "[4/4] Firebird Sync Frontend (porta 3001)..." -ForegroundColor Yellow
$fbFrontendScript = @"
cd '$ROOT\firebird-sync\frontend'
Write-Host '=== Firebird Sync Frontend ===' -ForegroundColor Green
npm start
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $fbFrontendScript

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Todos os servicos iniciados!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  BPA Online:    http://localhost:3000" -ForegroundColor White
Write-Host "  BPA API:       http://localhost:8000" -ForegroundColor White
Write-Host "  Firebird Sync: http://localhost:3001" -ForegroundColor White
Write-Host "  Firebird API:  http://localhost:8001" -ForegroundColor White
Write-Host ""
