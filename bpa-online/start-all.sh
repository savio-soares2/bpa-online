#!/bin/bash
# ===========================================
#   BPA Online + Firebird Sync - Start All
#   Para Git Bash no Windows
# ===========================================

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "   Iniciando BPA Online + Firebird Sync"
echo "========================================"
echo ""

# Converte caminho para Windows se necessário
WIN_ROOT=$(cygpath -w "$ROOT" 2>/dev/null || echo "$ROOT")

echo "[1/4] BPA Online Backend (porta 8000)..."
echo "[2/4] BPA Online Frontend (porta 3000)..."
echo "[3/4] Firebird Sync Backend (porta 8001)..."
echo "[4/4] Firebird Sync Frontend (porta 3001)..."

echo ""
echo "Execute cada comando em um terminal separado:"
echo ""
echo "Terminal 1 - BPA Backend:"
echo "  cd $WIN_ROOT && .venv\\Scripts\\activate && cd backend && python main.py"
echo ""
echo "Terminal 2 - BPA Frontend:"
echo "  cd $WIN_ROOT\\frontend && npm start"
echo ""
echo "Terminal 3 - Firebird Backend:"
echo "  cd $WIN_ROOT\\firebird-sync\\backend && python main.py"
echo ""
echo "Terminal 4 - Firebird Frontend:"
echo "  cd $WIN_ROOT\\firebird-sync\\frontend && npm start"
echo ""
echo "========================================"
echo "URLs:"
echo "  BPA Online:    http://localhost:3000"
echo "  BPA API:       http://localhost:8000"
echo "  Firebird Sync: http://localhost:3001"
echo "  Firebird API:  http://localhost:8001"
echo "========================================"
