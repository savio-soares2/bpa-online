# 🏥 BPA Online - Sistema de Automação e-SUS → Firebird

Sistema web automatizado para extração, processamento e importação de dados BPA (Boletim de Produção Ambulatorial) do e-SUS para o banco Firebird do software BPA.

## 📋 Visão Geral

O BPA Online substitui o processo manual de execução de scripts Python, oferecendo:

- ✅ Interface web amigável para usuários leigos
- ✅ Seleção visual de CNES através de botões
- ✅ Processamento automatizado de dados
- ✅ Monitoramento em tempo real
- ✅ Painel de controle com estatísticas
- ✅ Sistema de logs detalhado
- ✅ Modo de teste com dados SQL pré-carregados

## 🏗️ Arquitetura

```
┌─────────────────┐
│  Frontend React │  ← Interface do usuário
│  (Port 3000)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Backend FastAPI│  ← API REST
│  (Port 8000)    │
└────────┬────────┘
         │
         ├──→ PostgreSQL (e-SUS) - Futuro
         ├──→ Firebird (BPA)
         └──→ Arquivos SQL (Teste)
```

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- Docker e Docker Compose (opcional)

### Instalação Manual

#### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Configure o arquivo .env
cp ../.env.example .env
# Edite .env com suas credenciais

# Inicie o servidor
python main.py
```

O backend estará disponível em: `http://localhost:8000`

#### 2. Frontend

```bash
cd frontend
npm install

# Inicie o servidor de desenvolvimento
npm start
```

O frontend estará disponível em: `http://localhost:3000`

### Instalação com Docker

```bash
# Copie e configure o .env
cp .env.example .env

# Inicie todos os serviços
docker-compose up -d

# Veja os logs
docker-compose logs -f
```

## 📖 Como Usar

### 1. Dashboard

Acesse `http://localhost:3000` para ver:

- Total de CNES disponíveis
- Total de registros nos dados de teste
- Tarefas ativas e concluídas
- Últimas extrações realizadas

### 2. Nova Extração

1. Clique em **"Nova Extração"**
2. Selecione os CNES desejados (clique nos cards)
3. Defina competência inicial e final
4. Clique em **"Iniciar Extração"**

O sistema irá:
- Processar os dados do arquivo SQL de teste
- Gerar arquivo JSON com os registros
- Disponibilizar para importação no Firebird

### 3. Monitoramento de Tarefas

Na página **"Tarefas"**, você pode:

- Ver progresso em tempo real
- Visualizar logs detalhados
- Importar dados para o Firebird
- Remover tarefas antigas

### 4. Importação para Firebird

Após conclusão da extração:

1. Vá para **"Tarefas"**
2. Clique em **"Importar"** na tarefa concluída
3. Os dados serão inseridos na tabela S_PRD do Firebird

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# PostgreSQL e-SUS (para uso futuro)
DB_HOST=192.168.1.129
DB_PORT=5432
DB_NAME=esus
DB_USER=leitura_esus
DB_PASSWORD=sua_senha

# Firebird BPA
FB_HOST=localhost
FB_PORT=3050
FB_DATABASE=C:\BPA\BPAMAG.GDB
FB_USER=SYSDBA
FB_PASSWORD=masterkey
FB_CHARSET=UTF8
```

### Modo de Operação

#### Modo TEST (Atual)
- Usa dados do arquivo `BPA-main/arquivos_sql/2025116061478.sql`
- Não requer conexão com e-SUS
- Ideal para testes e desenvolvimento

#### Modo ESUS (Futuro)
- Conectará ao banco PostgreSQL do e-SUS
- Executará query SQL dinâmica
- Requer configuração de rede e credenciais

## 📁 Estrutura do Projeto

```
bpa-online/
├── backend/                    # API FastAPI
│   ├── main.py                # Entrada principal
│   ├── models/                # Schemas Pydantic
│   │   └── schemas.py
│   ├── services/              # Lógica de negócio
│   │   ├── bpa_service.py    # Gerenciamento de extrações
│   │   ├── sql_parser.py     # Parse de arquivos SQL
│   │   └── firebird_importer.py  # Importação Firebird
│   ├── config_firebird.py    # Configuração Firebird
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Interface React
│   ├── src/
│   │   ├── App.js            # Componente principal
│   │   ├── App.css           # Estilos globais
│   │   └── pages/
│   │       ├── Dashboard.js  # Painel principal
│   │       ├── ExtractionPage.js  # Página de extração
│   │       └── TasksPage.js  # Gerenciamento de tarefas
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── BPA-main/                   # Scripts originais
│   ├── scripts/               # Scripts Python originais
│   ├── sql/                   # Queries SQL
│   └── arquivos_sql/          # Dados de teste
│
├── docker-compose.yml         # Orquestração Docker
├── .env.example              # Exemplo de configuração
└── README.md                 # Esta documentação
```

## 🔄 Fluxo de Dados

### Extração
```
1. Usuário seleciona CNES e competências
2. Backend busca dados do arquivo SQL
3. Parse dos INSERTs para formato JSON
4. Salvamento em arquivo temporário
5. Atualização de status em tempo real
```

### Importação
```
1. Usuário clica em "Importar"
2. Backend carrega dados JSON
3. Conexão com Firebird via ODBC
4. Inserção em lotes (500 registros)
5. Execução de procedures de correção
6. Relatório de importação
```

## 📊 API Endpoints

### Dashboard
- `GET /api/health` - Verifica saúde da API
- `GET /api/dashboard/stats` - Estatísticas gerais

### CNES
- `GET /api/cnes/list` - Lista CNES disponíveis
- `GET /api/cnes/{cnes}/stats` - Estatísticas de um CNES

### Extração
- `POST /api/extract` - Inicia nova extração
- `GET /api/extract/{task_id}/status` - Status da extração

### Tarefas
- `GET /api/logs/{task_id}` - Logs de uma tarefa
- `DELETE /api/tasks/{task_id}` - Remove tarefa
- `POST /api/firebird/import/{task_id}` - Importa para Firebird

## 🛠️ Desenvolvimento

### Backend

```bash
cd backend

# Instala dependências
pip install -r requirements.txt

# Executa com reload automático
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Instala dependências
npm install

# Executa em modo desenvolvimento
npm start

# Build para produção
npm run build
```

## 🔍 Troubleshooting

### Backend não inicia

1. Verifique Python 3.11+: `python --version`
2. Instale dependências: `pip install -r requirements.txt`
3. Verifique portas em uso: `netstat -ano | findstr :8000`

### Frontend não carrega

1. Verifique Node.js: `node --version`
2. Limpe cache: `npm cache clean --force`
3. Reinstale: `rm -rf node_modules && npm install`

### Erro ao importar para Firebird

1. Verifique driver ODBC instalado
2. Confirme credenciais no .env
3. Teste conexão manualmente
4. Verifique se o banco existe no caminho especificado

## 📝 Dados de Teste

O sistema vem com dados de teste pré-carregados:

- **Arquivo**: `BPA-main/arquivos_sql/2025116061478.sql`
- **CNES**: 6061478
- **Competência**: 2025-11
- **Registros**: ~14.000 inserções

Para adicionar mais dados de teste, coloque arquivos SQL no formato:
`YYYYMMCNES.sql` (ex: `2025116061478.sql`)

## 🚧 Próximas Funcionalidades

- [ ] Integração com API do e-SUS PEC
- [ ] Modo ESUS com conexão PostgreSQL
- [ ] Agendamento de extrações automáticas
- [ ] Notificações por email
- [ ] Exportação de relatórios
- [ ] Multi-tenancy (múltiplos municípios)
- [ ] Autenticação e permissões
- [ ] Histórico de importações

## 📄 Licença

Este projeto é de uso interno. Todos os direitos reservados.

## 👥 Suporte

Para dúvidas ou problemas:

1. Verifique a documentação acima
2. Consulte os logs do sistema
3. Entre em contato com o desenvolvedor

---

**Desenvolvido para automatizar e simplificar o fluxo BPA** 🚀