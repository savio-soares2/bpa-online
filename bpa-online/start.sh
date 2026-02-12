#!/bin/bash

echo "🚀 Iniciando BPA Online..."
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.11 ou superior."
    exit 1
fi

# Verifica se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Por favor, instale Node.js 18 ou superior."
    exit 1
fi

echo "✅ Python $(python3 --version) encontrado"
echo "✅ Node.js $(node --version) encontrado"
echo ""

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "⚙️ Criando arquivo .env..."
    cp .env.example .env
    echo "⚠️ Configure o arquivo .env com suas credenciais antes de usar em produção!"
    echo ""
fi

# Backend
echo "📦 Instalando dependências do backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Backend configurado"
echo ""

# Inicia backend em background
echo "🔧 Iniciando servidor backend (porta 8000)..."
python main.py &
BACKEND_PID=$!
cd ..

# Frontend
echo "📦 Instalando dependências do frontend..."
cd frontend
npm install > /dev/null 2>&1
echo "✅ Frontend configurado"
echo ""

echo "🎨 Iniciando servidor frontend (porta 3000)..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================================"
echo "✅ BPA Online está rodando!"
echo "================================================"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API:       http://localhost:8000"
echo "📖 API Docs:  http://localhost:8000/docs"
echo ""
echo "Para parar os servidores, pressione Ctrl+C"
echo ""

# Aguarda Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
