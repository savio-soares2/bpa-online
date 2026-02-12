# Sistema BPA Online com Validação CBO/Procedimentos

## 📋 Visão Geral

O sistema BPA Online agora inclui validação automática de CBOs (Classificação Brasileira de Ocupações) versus procedimentos permitidos, usando os arquivos DBF oficiais do Ministério da Saúde.

### ✅ Funcionalidades Implementadas

1. **Carregamento dos DBFs**: Sistema lê automaticamente os arquivos S_PACBO.DBF, S_PA.DBF e S_PROCED.DBF
2. **Sistema de Usuários**: Cadastro de usuários vinculados a CBOs específicos
3. **Validação Automática**: Usuários só podem criar BPAs para procedimentos permitidos ao seu CBO
4. **Cache Inteligente**: Dados DBF são mantidos em cache para performance
5. **API Completa**: Endpoints para gerenciar usuários, consultar procedimentos e validar CBOs

## 🏗️ Arquitetura da Solução

### Componentes Principais

```
backend/
├── services/
│   ├── dbf_manager_service.py     # Gerencia os arquivos DBF
│   ├── user_service.py            # Sistema de usuários e autenticação
│   └── bpa_service.py             # Serviços BPA com validação CBO
├── models/
│   └── user_schemas.py            # Schemas para usuários e CBOs
└── main.py                        # API endpoints
```

### Fluxo de Dados

1. **DBFs** → `DBFManagerService` → Cache em memória/disco
2. **Usuário** → `UserService` → Validação CBO → JWT Token
3. **BPA** → Validação CBO/Procedimento → Criação autorizada

## 📊 Estatísticas dos Dados Carregados

- **291 CBOs únicos** disponíveis
- **5.458 procedimentos** catalogados  
- **193.698 relações** CBO → Procedimento
- **Média de 665 procedimentos por CBO**

## 🚀 Como Usar

### 1. Configuração Inicial

```bash
# Instalar dependências
cd backend
pip install -r requirements.txt
```

### 2. Executar o Servidor

```bash
cd backend
python main.py
```

Acesse: http://localhost:8000/docs

### 3. Fluxo de Uso

#### A) Cadastrar Usuário
```bash
POST /api/auth/register
{
    "username": "psicologo01",
    "email": "psicologo@unidade.com",
    "password": "senha123",
    "nome": "Dr. João Silva",
    "cbo": "251510",          # CBO de Psicólogo
    "cnes": "2269651",        # CNES da unidade
    "perfil": "user"
}
```

#### B) Fazer Login
```bash
POST /api/auth/login
{
    "username": "psicologo01",
    "password": "senha123"
}

# Retorna:
{
    "access_token": "eyJ...",
    "user": {...},
    "procedimentos_permitidos": ["0301080016", "0301080024", ...]
}
```

#### C) Consultar Meus Procedimentos
```bash
GET /api/cbo/my-procedures
Authorization: Bearer eyJ...

# Retorna lista de procedimentos permitidos para o CBO do usuário
```

#### D) Criar BPA com Validação
```bash
POST /api/bpa-i/create-with-cbo
Authorization: Bearer eyJ...
{
    "cnes": "2269651",
    "competencia": "202511",
    "procedimento": "0301080016",  # Deve estar na lista permitida
    "cns_paciente": "700501926845056",
    "nome_paciente": "MARIA DA SILVA",
    # ... outros campos
}
```

## 🛡️ Sistema de Validação

### Middleware de Validação CBO

Toda criação de BPA passa pelo middleware `validate_bpa_cbo_procedure()`:

```python
def validate_bpa_cbo_procedure(user: UsuarioResponse, codigo_procedimento: str):
    """Valida se o usuário pode executar um procedimento"""
    validation = bpa_service.validate_procedure_for_user(user.id, codigo_procedimento)
    if not validation.get('valido'):
        raise HTTPException(403, detail=f"CBO {user.cbo} não autorizado")
```

### Tipos de Validação

1. **CBO existe**: Verificado contra S_PACBO.DBF
2. **Procedimento existe**: Verificado contra S_PA.DBF/S_PROCED.DBF  
3. **Relação válida**: CBO pode executar o procedimento específico
4. **Usuário ativo**: Conta do usuário deve estar ativa

## 🔧 Endpoints da API

### Autenticação
- `POST /api/auth/register` - Cadastrar usuário
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Dados do usuário logado

### CBO/Procedimentos
- `GET /api/cbo/my-procedures` - Meus procedimentos permitidos
- `POST /api/cbo/validate-procedure` - Validar CBO x Procedimento
- `GET /api/procedures/search?q=consulta` - Buscar procedimentos
- `GET /api/procedures/{codigo}/cbos` - CBOs que podem executar procedimento

### BPA com Validação
- `POST /api/bpa-i/create-with-cbo` - Criar BPA-I validado
- `POST /api/bpa-c/create-with-cbo` - Criar BPA-C validado

### Sistema DBF
- `GET /api/dbf/statistics` - Estatísticas dos DBFs
- `POST /api/dbf/refresh` - Atualizar cache (admin)

### Administração
- `GET /api/admin/users` - Listar usuários (admin)
- `PUT /api/admin/users/{id}/status` - Ativar/desativar usuário (admin)

## 🔄 Atualização dos DBFs

### Processo Recomendado

1. **Baixar novos DBFs**: Execute o BDSIA202511a.exe/BDSIA202511b.exe
2. **Substituir arquivos**: Copie os novos DBFs para o diretório configurado
3. **Atualizar cache**: `POST /api/dbf/refresh` ou reiniciar o sistema
4. **Validar**: Teste os endpoints `GET /api/dbf/statistics` e `POST /api/cbo/validate-procedure`

### Automatização

O sistema foi projetado para usar os DBFs como "single source of truth":

```python
# Configuração do caminho dos DBFs
DBF_PATH = r"c:\BPA\Tabelas Nacionais do Kit BPA\202511"

# O sistema carrega automaticamente quando inicializado
dbf_manager = DBFManagerService(DBF_PATH)
```

## 🎯 Casos de Uso Práticos

### Cenário 1: Psicólogo na UBS
- **CBO**: 251510 (Psicólogo)
- **Procedimentos permitidos**: Consultas psicológicas, terapia de grupo, etc.
- **Bloqueios**: Não pode criar procedimentos médicos ou de enfermagem

### Cenário 2: Médico Generalista  
- **CBO**: 225125 (Médico Clínico)
- **Procedimentos permitidos**: Consultas médicas, procedimentos básicos
- **Bloqueios**: Não pode criar procedimentos de especialidades específicas

### Cenário 3: Enfermeiro
- **CBO**: 223505 (Enfermeiro)
- **Procedimentos permitidos**: Procedimentos de enfermagem, educação em saúde
- **Bloqueios**: Não pode criar consultas médicas

## ⚠️ Considerações Importantes

### Segurança
- Tokens JWT expiram em 24 horas
- Senhas são hasheadas com SHA-256
- Validação CBO é obrigatória para BPAs

### Performance
- Cache em memória para consultas frequentes
- Cache em disco para persistência entre reinicializações
- Carregamento lazy dos DBFs

### Manutenção
- Logs detalhados de todas as operações
- Banco SQLite para usuários (fácil backup)
- Estrutura modular para fácil manutenção

## 🔍 Troubleshooting

### Erro: "CBO não encontrado"
- Verificar se o arquivo S_PACBO.DBF está acessível
- Executar `POST /api/dbf/refresh` para recarregar
- Consultar logs do sistema

### Erro: "Token inválido"
- Verificar se o token não expirou
- Fazer novo login
- Verificar se o usuário não foi desativado

### Erro: "Procedimento não autorizado"
- Consultar `/api/cbo/my-procedures` para ver procedimentos permitidos
- Verificar se o código do procedimento está correto
- Confirmar se o CBO do usuário pode executar o procedimento

## 📈 Próximas Melhorias

1. **Interface Web**: Dashboard para gerenciar usuários e visualizar estatísticas
2. **Auditoria**: Log de todas as criações de BPA com usuário responsável
3. **Relatórios**: Relatórios de produtividade por CBO/usuário
4. **Notificações**: Alertas quando novos DBFs estão disponíveis
5. **Backup**: Rotina automática de backup do banco de usuários