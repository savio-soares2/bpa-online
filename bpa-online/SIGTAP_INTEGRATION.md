# Integração SIGTAP - Filtragem Dinâmica de Procedimentos

## Visão Geral

O sistema agora utiliza as **tabelas SIGTAP (Sistema de Gerenciamento da Tabela de Procedimentos)** diretamente dos arquivos TXT fornecidos pelo DATASUS para filtrar procedimentos de forma inteligente baseado em:

1. **Tipo de Instrumento** - BPA-I (02) vs BPA-C (01)
2. **CBO do Profissional** - Ocupação que define quais procedimentos pode executar
3. **Tipo de Estabelecimento** - Serviço/classificação que define procedimentos permitidos

## Arquivos SIGTAP

Localização: `BPA-main/TabelaUnificada_202512_v2601161858/`

### Arquivos Principais

| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `tb_procedimento.txt` | Procedimentos do SUS | ~4.957 |
| `tb_ocupacao.txt` | Códigos CBO (ocupações) | ~2.718 |
| `tb_servico.txt` | Tipos de serviço/estabelecimento | ~73 |
| `tb_registro.txt` | Instrumentos de registro | 10 |
| `rl_procedimento_ocupacao.txt` | Procedimento ↔ CBO | ~193.315 |
| `rl_procedimento_servico.txt` | Procedimento ↔ Serviço | ~4.086 |
| `rl_procedimento_registro.txt` | Procedimento ↔ Instrumento | ~7.439 |

### Instrumentos de Registro

```
01 - BPA (Consolidado)
02 - BPA (Individualizado)
03 - AIH (Proc. Principal)
04 - AIH (Proc. Especial)
05 - AIH (Proc. Secundário)
06 - APAC (Proc. Principal)
07 - APAC (Proc. Secundário)
08 - RAAS (Atenção Domiciliar)
09 - RAAS (Atenção Psicossocial)
10 - e-SUS APS (Atenção Primária à Saúde)
```

## Arquitetura da Solução

### Vantagens de Usar TXTs Diretamente

✅ **Sem necessidade de importação** - Não requer PostgreSQL para SIGTAP  
✅ **Atualização simples** - Basta substituir a pasta com nova competência  
✅ **Performance adequada** - Cache LRU mantém dados em memória  
✅ **Menor complexidade** - Menos componentes para gerenciar  
✅ **Versionamento natural** - Cada pasta é uma competência/versão  

### Componentes

1. **SigtapParser** (`services/sigtap_parser.py`)
   - Lê arquivos TXT em formato fixed-width
   - Usa layouts CSV para extrair colunas
   - Métodos para cada tabela principal

2. **SigtapFilterService** (`services/sigtap_filter_service.py`)
   - Filtragem inteligente de procedimentos
   - Cache LRU para performance
   - Validação de procedimento x CBO
   - Singleton global

3. **Endpoints API** (`main.py`)
   - 7 endpoints REST para consulta
   - Autenticação integrada
   - Filtros combinados (AND)

## Endpoints da API

### 1. Listar Procedimentos Filtrados

```http
GET /api/sigtap/procedimentos
```

**Query Parameters:**
- `tipo_registro` - 01=BPA-C, 02=BPA-I
- `cbo` - Código CBO (6 dígitos)
- `servico` - Código do serviço (3 dígitos)
- `classificacao` - Código da classificação (3 dígitos)
- `termo_busca` - Busca no nome do procedimento
- `limit` - Máximo de resultados (padrão: 100)

**Exemplos:**

```bash
# BPA-I para médico clínico (CBO 225125)
GET /api/sigtap/procedimentos?tipo_registro=02&cbo=225125&limit=10

# BPA-C com termo "CONSULTA"
GET /api/sigtap/procedimentos?tipo_registro=01&termo_busca=CONSULTA

# Todos os procedimentos BPA-I
GET /api/sigtap/procedimentos?tipo_registro=02&limit=1000
```

**Resposta:**
```json
{
  "total": 1337,
  "limit": 10,
  "filtros": {
    "tipo_registro": "02",
    "cbo": "225125",
    "servico": null,
    "classificacao": null,
    "termo_busca": null
  },
  "procedimentos": [
    {
      "CO_PROCEDIMENTO": "0301010064",
      "NO_PROCEDIMENTO": "CONSULTA MEDICA EM ATENÇÃO PRIMÁRIA",
      "TP_COMPLEXIDADE": "1",
      "TP_SEXO": "I",
      "VL_SH": "0000000500",
      ...
    }
  ]
}
```

### 2. Procedimentos do Usuário Logado

```http
GET /api/sigtap/procedimentos/por-usuario
Authorization: Bearer {token}
```

**Query Parameters:**
- `tipo_bpa` - 01=BPA-C, 02=BPA-I (padrão: 02)
- `termo_busca` - Filtro por nome
- `limit` - Máximo de resultados

**Exemplo:**
```bash
# Procedimentos BPA-I que o usuário pode registrar
GET /api/sigtap/procedimentos/por-usuario?tipo_bpa=02&termo_busca=CONSULTA
```

**Resposta:**
```json
{
  "usuario_cbo": "225125",
  "tipo_bpa": "02",
  "total": 26,
  "procedimentos": [...]
}
```

### 3. Listar CBOs

```http
GET /api/sigtap/cbos
```

**Resposta:**
```json
{
  "total": 2718,
  "cbos": [
    {
      "CO_OCUPACAO": "225125",
      "NO_OCUPACAO": "Médico clínico",
      "DT_COMPETENCIA": "202512"
    }
  ]
}
```

### 4. Listar Serviços

```http
GET /api/sigtap/servicos
```

### 5. Listar Instrumentos de Registro

```http
GET /api/sigtap/registros
```

### 6. Validar Procedimento

```http
GET /api/sigtap/validar-procedimento
```

**Query Parameters:**
- `co_procedimento` - Código do procedimento (obrigatório)
- `cbo` - Código CBO (obrigatório)
- `tipo_bpa` - 01 ou 02 (padrão: 02)

**Exemplo:**
```bash
GET /api/sigtap/validar-procedimento?co_procedimento=0301010064&cbo=225125&tipo_bpa=02
```

**Resposta:**
```json
{
  "valido": true,
  "procedimento": "0301010064",
  "cbo": "225125",
  "tipo_bpa": "02"
}
```

### 7. Estatísticas

```http
GET /api/sigtap/estatisticas
```

**Resposta:**
```json
{
  "total_procedimentos": 4957,
  "total_cbos": 2718,
  "total_servicos": 73,
  "total_instrumentos": 10,
  "total_relacoes_cbo": 193315,
  "total_relacoes_servico": 4086,
  "total_relacoes_registro": 7439
}
```

## Uso no Frontend

### Auto-Complete de Procedimentos

```typescript
// Buscar procedimentos enquanto o usuário digita
const searchProcedimentos = async (termo: string) => {
  const response = await fetch(
    `/api/sigtap/procedimentos/por-usuario?termo_busca=${termo}&limit=20`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  const data = await response.json();
  return data.procedimentos;
};
```

### Validação em Tempo Real

```typescript
// Validar procedimento antes de salvar
const validarProcedimento = async (codigo: string, cbo: string) => {
  const response = await fetch(
    `/api/sigtap/validar-procedimento?co_procedimento=${codigo}&cbo=${cbo}&tipo_bpa=02`
  );
  const data = await response.json();
  
  if (!data.valido) {
    alert('Este procedimento não é permitido para o seu CBO!');
    return false;
  }
  return true;
};
```

## Performance

### Cache LRU

O serviço usa `@lru_cache` do Python para manter dados em memória:

```python
@lru_cache(maxsize=1)
def _get_all_procedimentos(self):
    # Carregado uma vez, mantido em memória
    return self.parser.parse_procedimentos()
```

### Benchmarks

- **Primeira carga**: ~0.1s (parsing dos arquivos)
- **Consultas subsequentes**: <0.01s (cache)
- **Filtragem complexa**: ~0.14s (primeira vez), <0.01s (cache)
- **Memória**: ~50MB (todos os dados em cache)

## Atualização de Competência

Para atualizar para uma nova competência do SIGTAP:

1. Baixar nova pasta `TabelaUnificada_YYYYMM_*` do DATASUS
2. Substituir a pasta em `BPA-main/`
3. Atualizar constante em `sigtap_filter_service.py`:

```python
SIGTAP_DIR = Path(__file__).parent.parent.parent / 'BPA-main' / 'TabelaUnificada_202601_vXXXXXXXXXX'
```

4. Reiniciar backend (cache será limpo automaticamente)

## Testes

Execute o script de testes:

```bash
cd backend
python test_sigtap_service.py
```

**Saída esperada:**
```
✓ 4,957 procedimentos carregados
✓ 2,718 CBOs disponíveis
✓ 1,846 procedimentos BPA-I
✓ 1,090 procedimentos BPA-C
✓ 1,337 procedimentos para CBO 225125
✓ Validação funcional
```

## Próximos Passos

### Frontend

- [ ] Criar componente `ProcedimentoAutocomplete`
- [ ] Integrar em `BPAIndividualizadoPage`
- [ ] Integrar em `BPAConsolidadoPage`
- [ ] Mostrar apenas procedimentos válidos para o CBO do usuário
- [ ] Exibir descrição completa ao selecionar procedimento

### Backend

- [ ] Adicionar filtro por tipo de estabelecimento (usando CNES)
- [ ] Endpoint para buscar detalhes de um procedimento específico
- [ ] Cache Redis para ambientes de produção
- [ ] Logging de consultas para auditoria

## Documentação DATASUS

- **SIGTAP**: http://sigtap.datasus.gov.br/
- **Downloads**: ftp://ftp.datasus.gov.br/
- **Manuais**: http://tabnet.datasus.gov.br/

## Suporte

Para dúvidas sobre códigos SIGTAP, consultar:
- Tabela Unificada do SUS
- Manual do SIGTAP
- Documentação BPA do DATASUS
