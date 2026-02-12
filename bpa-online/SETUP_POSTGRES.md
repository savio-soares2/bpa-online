# BPA Online - Setup PostgreSQL

## Opção 1: Docker (Recomendado)

### Windows com Docker Desktop
1. Instale o Docker Desktop: https://www.docker.com/products/docker-desktop
2. Execute:
```powershell
cd bpa-online
docker compose up -d postgres
```

### Verificar se está rodando:
```powershell
docker compose ps
docker compose logs postgres
```

## Opção 2: PostgreSQL Local (Windows)

### 1. Instalar PostgreSQL
- Download: https://www.postgresql.org/download/windows/
- Versão recomendada: 15 ou superior
- Durante instalação, defina a senha do usuário `postgres`

### 2. Criar banco e usuário
Abra o pgAdmin ou psql e execute:

```sql
-- Criar usuário
CREATE USER bpa_user WITH PASSWORD 'bpa_secret_2024';

-- Criar banco
CREATE DATABASE bpa_online OWNER bpa_user;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE bpa_online TO bpa_user;

-- Conectar ao banco bpa_online e criar extensão
\c bpa_online
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 3. Configurar .env
Edite o arquivo `.env`:
```env
DATABASE_URL=postgresql://bpa_user:bpa_secret_2024@localhost:5432/bpa_online
```

## Opção 3: PostgreSQL na nuvem

### Supabase (Gratuito)
1. Crie uma conta em https://supabase.com
2. Crie um novo projeto
3. Vá em Settings > Database > Connection String
4. Copie a URL e coloque no `.env`:
```env
DATABASE_URL=postgresql://postgres:[SENHA]@db.[REF].supabase.co:5432/postgres
```

### Neon (Gratuito)
1. Crie uma conta em https://neon.tech
2. Crie um novo projeto
3. Copie a connection string para o `.env`

## Testar conexão

```powershell
cd backend
python -c "from database import db; print('Conexão OK!')"
```

## Iniciar o sistema

```powershell
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```
