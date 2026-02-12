$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $repoRoot '..\.venv\Scripts\python.exe'
$backendManage = Join-Path $repoRoot 'backend_django\manage.py'
$frontendDir = Join-Path $repoRoot 'frontend'

Write-Host "Starting backend (Django)"
Start-Process -FilePath $venvPython -ArgumentList "$backendManage runserver 0.0.0.0:8000" -WorkingDirectory $repoRoot

Write-Host "Starting frontend (React)"
Start-Process -FilePath "powershell" -ArgumentList "-NoProfile", "-Command", "Set-Location '$frontendDir'; npm start" -WorkingDirectory $frontendDir

Write-Host "Done. Backend: http://localhost:8000/api/health | Frontend: http://localhost:3000"
