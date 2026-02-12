# Paginação BiServer - Evitando Dados Duplicados

## Problema Resolvido

Ao extrair grandes volumes de dados do BiServer (ex: 15.000 registros), fazer múltiplas requisições de 5.000 em 5.000 sem controle poderia trazer dados repetidos.

## Solução Implementada

Sistema de paginação com **offset** que controla exatamente quais registros já foram baixados.

## Como Funciona

### Parâmetros Disponíveis

```typescript
{
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i",  // ou "bpa_c"
  "limit": 5000,    // Quantos registros por vez
  "offset": 0       // Quantos registros pular
}
```

### Exemplo de Uso Sequencial

#### Primeira Extração (0 a 4.999)
```bash
POST /api/biserver/extract
{
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i",
  "limit": 5000,
  "offset": 0
}
```
**Retorna:** Registros de 0 a 4.999

#### Segunda Extração (5.000 a 9.999)
```bash
POST /api/biserver/extract
{
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i",
  "limit": 5000,
  "offset": 5000  ← Pula os primeiros 5.000
}
```
**Retorna:** Registros de 5.000 a 9.999

#### Terceira Extração (10.000 a 14.999)
```bash
POST /api/biserver/extract
{
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i",
  "limit": 5000,
  "offset": 10000  ← Pula os primeiros 10.000
}
```
**Retorna:** Registros de 10.000 a 14.999

## Fluxo Completo de Extração

### Opção 1: Extrair Tudo Manualmente

```typescript
const extractAll = async (cnes: string, competencia: string) => {
  let offset = 0;
  const limit = 5000;
  let hasMore = true;
  
  while (hasMore) {
    const response = await fetch('/api/biserver/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cnes,
        competencia,
        tipo: 'bpa_i',
        limit,
        offset
      })
    });
    
    const data = await response.json();
    
    // Se retornou menos que o limit, acabaram os registros
    if (data.total_records < limit) {
      hasMore = false;
    }
    
    // Salva os dados no banco
    await fetch('/api/biserver/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cnes,
        competencia,
        tipo: 'bpa_i'
      })
    });
    
    offset += limit;
  }
};
```

### Opção 2: UI com Botão "Carregar Mais"

```typescript
const [offset, setOffset] = useState(0);
const [hasMore, setHasMore] = useState(true);

const loadMore = async () => {
  const response = await fetch('/api/biserver/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cnes: currentCnes,
      competencia: currentCompetencia,
      tipo: 'bpa_i',
      limit: 5000,
      offset
    })
  });
  
  const data = await response.json();
  
  if (data.total_records < 5000) {
    setHasMore(false);
  }
  
  setOffset(offset + 5000);
};
```

## Cache Interno

Cada extração é cacheada internamente com chave única incluindo o offset:

```python
# BPA-I com offset 0
cache_key = "bpa_i_6061478_202512_0"

# BPA-I com offset 5000
cache_key = "bpa_i_6061478_202512_5000"

# BPA-C com offset 10000
cache_key = "bpa_c_6061478_202512_10000"
```

Isso garante que cada "página" de dados tem seu próprio cache.

## Modo Mock

No modo de desenvolvimento (MOCK_MODE=True), o sistema:

1. Gera 5.000 registros simulados por vez
2. Respeita o offset: `all_mock_records[offset:offset + limit]`
3. Simula comportamento real da API

## Boas Práticas

### ✅ Fazer

- Incrementar offset em múltiplos de limit (0, 5000, 10000...)
- Verificar `total_records < limit` para detectar fim dos dados
- Salvar cada lote no banco antes de buscar o próximo
- Usar limit entre 1000 e 5000 para performance ideal

### ❌ Evitar

- Usar offset aleatórios (ex: 1234, 7890)
- Buscar todos os dados sem salvar antes
- Usar limit muito pequeno (< 100) ou muito grande (> 10000)
- Ignorar verificação de fim de dados

## Monitoramento

Cada extração retorna informações úteis:

```json
{
  "success": true,
  "message": "Extraídos 5000 registros de BPA-I (offset=5000)",
  "total_records": 5000,
  "records": [...],
  "errors": []
}
```

**Observe:**
- `message` mostra o offset usado
- `total_records` indica quantos registros vieram nesta página
- Se `total_records < limit`, acabaram os dados

## Exemplo Prático Completo

### Cenário: Extrair 12.347 registros de BPA-I

```bash
# Lote 1: offset=0 → 5.000 registros
POST /api/biserver/extract { offset: 0, limit: 5000 }
→ Retorna 5.000 registros

# Lote 2: offset=5000 → 5.000 registros
POST /api/biserver/extract { offset: 5000, limit: 5000 }
→ Retorna 5.000 registros

# Lote 3: offset=10000 → 2.347 registros (último lote)
POST /api/biserver/extract { offset: 10000, limit: 5000 }
→ Retorna 2.347 registros (menos que limit, então acabou)
```

**Total extraído:** 5.000 + 5.000 + 2.347 = **12.347 registros** ✅  
**Sem duplicatas:** Cada offset garante registros únicos ✅

## Integração com Frontend

Exemplo de componente React:

```tsx
const BiServerExtraction: React.FC = () => {
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [complete, setComplete] = useState(false);

  const extractBatch = async () => {
    setLoading(true);
    
    const response = await fetch('/api/biserver/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cnes: '6061478',
        competencia: '202512',
        tipo: 'bpa_i',
        limit: 5000,
        offset
      })
    });
    
    const data = await response.json();
    
    // Salva no banco
    await fetch('/api/biserver/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cnes: '6061478',
        competencia: '202512',
        tipo: 'bpa_i'
      })
    });
    
    if (data.total_records < 5000) {
      setComplete(true);
    } else {
      setOffset(offset + 5000);
    }
    
    setLoading(false);
  };

  return (
    <div>
      <p>Registros extraídos: {offset}</p>
      <button onClick={extractBatch} disabled={loading || complete}>
        {loading ? 'Extraindo...' : complete ? 'Completo' : 'Extrair Próximos 5.000'}
      </button>
    </div>
  );
};
```

## Troubleshooting

### Problema: Dados duplicados mesmo com offset

**Solução:** Verificar se está incrementando offset corretamente
```typescript
// ❌ Errado
offset = 5000; // sempre o mesmo valor

// ✅ Certo
offset = offset + limit; // incrementa a cada lote
```

### Problema: Cache mostrando dados antigos

**Solução:** Cada offset tem cache separado. Para limpar:
```bash
# Reiniciar servidor limpa cache
# Ou usar endpoints de debug para limpar cache específico
```

### Problema: Não sei quantos registros existem no total

**Solução:** Continue extraindo até `total_records < limit`
```python
if data['total_records'] < limit:
    print("Fim dos dados alcançado!")
```

## Migração de Código Antigo

### Antes (sem paginação)
```typescript
fetch('/api/biserver/extract', {
  body: JSON.stringify({ cnes, competencia, tipo: 'bpa_i' })
})
```

### Depois (com paginação)
```typescript
fetch('/api/biserver/extract', {
  body: JSON.stringify({ 
    cnes, 
    competencia, 
    tipo: 'bpa_i',
    limit: 5000,
    offset: 0  // adicionar offset
  })
})
```

**Compatibilidade:** O parâmetro `offset` é opcional e usa 0 por padrão, então código antigo continua funcionando!
