# Extração Automática BiServer - Guia Completo

## Novo Sistema de Extração Automática

Agora o sistema baixa **automaticamente** todos os registros de uma competência, dividindo em lotes e parando quando terminar.

## 📊 Endpoints Disponíveis

### 1. Contar Registros (Antes de Extrair)

```bash
GET /api/biserver/count?cnes=6061478&competencia=202512&tipo=bpa_i
```

**Retorna:**
```json
{
  "success": true,
  "total": 12347,
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i",
  "mock": false
}
```

Útil para saber o tamanho do arquivo antes de baixar.

---

### 2. Extração Automática Completa (NOVO! ⭐)

```bash
POST /api/biserver/extract-all?cnes=6061478&competencia=202512&tipo=bpa_i&batch_size=5000&auto_save=true
```

**Parâmetros:**
- `cnes`: Código CNES (obrigatório)
- `competencia`: YYYYMM (obrigatório)
- `tipo`: `bpa_i` ou `bpa_c` (padrão: bpa_i)
- `batch_size`: Tamanho de cada lote (padrão: 5000)
- `auto_save`: Salvar automaticamente cada lote no banco (padrão: true)

**O que acontece:**
1. ✅ Conta o total de registros
2. ✅ Calcula quantos lotes serão necessários
3. ✅ Extrai lote por lote (5000 em 5000)
4. ✅ Salva cada lote automaticamente (se `auto_save=true`)
5. ✅ Para automaticamente quando acabar
6. ✅ Retorna estatísticas completas

**Retorna:**
```json
{
  "success": true,
  "total_records": 12347,
  "expected_records": 12347,
  "batches_processed": 3,
  "batch_size": 5000,
  "auto_saved": true,
  "tipo": "bpa_i",
  "message": "Extraídos 12347 de 12347 registros em 3 lotes",
  "errors": []
}
```

---

### 3. Extração Manual (Antiga)

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

Ainda disponível para controle manual.

---

## 🚀 Exemplos de Uso

### Exemplo 1: Extração Completa Automática

```javascript
// Frontend - um único clique baixa tudo!
const extractirTudo = async () => {
  const response = await fetch('/api/biserver/extract-all?' + new URLSearchParams({
    cnes: '6061478',
    competencia: '202512',
    tipo: 'bpa_i',
    batch_size: '5000',
    auto_save: 'true'
  }), {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const result = await response.json();
  
  console.log(`✅ Extraídos ${result.total_records} registros em ${result.batches_processed} lotes`);
};
```

### Exemplo 2: Contar Antes de Extrair

```javascript
// 1. Primeiro, veja quantos registros existem
const count = await fetch('/api/biserver/count?cnes=6061478&competencia=202512&tipo=bpa_i')
  .then(r => r.json());

console.log(`Existem ${count.total} registros para baixar`);

// 2. Se quiser, extraia tudo
if (count.total > 0) {
  const result = await fetch('/api/biserver/extract-all?' + new URLSearchParams({
    cnes: '6061478',
    competencia: '202512',
    tipo: 'bpa_i'
  }), { method: 'POST' }).then(r => r.json());
  
  console.log(result.message);
}
```

### Exemplo 3: Python - Extração Automática

```python
import requests

# Token JWT
headers = {"Authorization": f"Bearer {token}"}

# Extração automática
response = requests.post(
    "http://localhost:8000/api/biserver/extract-all",
    params={
        "cnes": "6061478",
        "competencia": "202512",
        "tipo": "bpa_i",
        "batch_size": 5000,
        "auto_save": True
    },
    headers=headers
)

result = response.json()
print(f"✅ {result['message']}")
print(f"   Lotes processados: {result['batches_processed']}")
print(f"   Total extraído: {result['total_records']}")
```

---

## 🎯 Fluxos de Trabalho

### Fluxo 1: Extração Rápida (Recomendado)

```bash
# Um único comando baixa e salva tudo
POST /api/biserver/extract-all?cnes=6061478&competencia=202512&tipo=bpa_i&auto_save=true
```

**Vantagens:**
- ✅ Automático
- ✅ Salva cada lote no banco
- ✅ Para sozinho quando acabar
- ✅ Sem risco de perder dados

### Fluxo 2: Verificar Antes de Extrair

```bash
# 1. Quantos registros existem?
GET /api/biserver/count?cnes=6061478&competencia=202512&tipo=bpa_i

# 2. Extrair tudo
POST /api/biserver/extract-all?cnes=6061478&competencia=202512&tipo=bpa_i
```

### Fluxo 3: Controle Manual Fino

```bash
# Extrair lote por lote manualmente
POST /api/biserver/extract { offset: 0, limit: 5000 }
POST /api/biserver/save-extracted

POST /api/biserver/extract { offset: 5000, limit: 5000 }
POST /api/biserver/save-extracted

# etc...
```

---

## 📈 Monitoramento em Tempo Real

### Logs do Backend

Durante a extração automática, você verá logs assim:

```
[INFO] Iniciando extração COMPLETA de BPA-I: CNES=6061478, Comp=202512, BatchSize=5000
[INFO] Total de registros disponíveis: 12347
[INFO] Extraindo lote 1/3 (offset=0)
[INFO] Auto-salvando lote 1/3 (5000 registros)
[INFO] Extraindo lote 2/3 (offset=5000)
[INFO] Auto-salvando lote 2/3 (5000 registros)
[INFO] Extraindo lote 3/3 (offset=10000)
[INFO] Auto-salvando lote 3/3 (2347 registros)
[INFO] Último lote retornou 2347 registros, finalizando
```

### Frontend com Progress Bar

```typescript
const [progress, setProgress] = useState(0);

const extractWithProgress = async () => {
  // 1. Conta total
  const count = await fetch('/api/biserver/count?cnes=6061478&competencia=202512&tipo=bpa_i')
    .then(r => r.json());
  
  const total = count.total;
  
  // 2. Extrai (simula progresso)
  const batchSize = 5000;
  const totalBatches = Math.ceil(total / batchSize);
  
  setProgress(0);
  
  // Chama extração automática
  const result = await fetch('/api/biserver/extract-all?...', { method: 'POST' })
    .then(r => r.json());
  
  setProgress(100);
  
  console.log(`✅ Completo: ${result.total_records} registros`);
};
```

---

## ⚙️ Configurações Recomendadas

### Para Volumes Pequenos (< 1000 registros)

```bash
batch_size=1000
auto_save=true
```

### Para Volumes Médios (1.000 - 10.000)

```bash
batch_size=5000
auto_save=true
```

### Para Volumes Grandes (> 10.000)

```bash
batch_size=5000
auto_save=true
# Considere dividir por competência
```

---

## 🔧 Troubleshooting

### Problema: Demora muito tempo

**Solução:** Aumente o `batch_size` para 10000

```bash
POST /api/biserver/extract-all?batch_size=10000
```

### Problema: Erros de memória

**Solução:** Diminua o `batch_size` para 1000 ou 2000

```bash
POST /api/biserver/extract-all?batch_size=1000
```

### Problema: Não sei quantos registros faltam

**Solução:** Use o endpoint de contagem primeiro

```bash
GET /api/biserver/count?cnes=6061478&competencia=202512&tipo=bpa_i
```

### Problema: Quero salvar depois, não durante

**Solução:** Desabilite auto_save

```bash
POST /api/biserver/extract-all?auto_save=false
# Depois salve manualmente:
POST /api/biserver/save-extracted
```

---

## 🆚 Comparação: Manual vs Automático

### Antes (Manual)

```javascript
// Tinha que fazer loop manualmente
let offset = 0;
while (true) {
  const result = await extract({ offset, limit: 5000 });
  if (result.total_records < 5000) break;
  offset += 5000;
}
```

**Problemas:**
- ❌ Você gerencia o loop
- ❌ Não sabe quando parar
- ❌ Pode esquecer de salvar lotes
- ❌ Código complexo

### Agora (Automático)

```javascript
// Um comando só!
const result = await fetch('/api/biserver/extract-all?cnes=6061478&competencia=202512&tipo=bpa_i', {
  method: 'POST'
}).then(r => r.json());

console.log(result.message); // "Extraídos 12347 de 12347 registros em 3 lotes"
```

**Vantagens:**
- ✅ Sistema gerencia tudo
- ✅ Para automaticamente
- ✅ Salva cada lote
- ✅ Código simples

---

## 📝 Modo Mock (Desenvolvimento)

No modo mock (`MOCK_MODE=True`), o sistema simula:

- **BPA-I:** 10.000 registros fictícios
- **BPA-C:** 500 registros fictícios

Útil para testar a paginação sem API real.

```python
# backend/.env
BISERVER_MOCK_MODE=True
```

---

## 🎓 Resumo

| Endpoint | Uso | Quando Usar |
|----------|-----|-------------|
| `/count` | Conta registros | Antes de extrair, para saber o tamanho |
| `/extract-all` | Extração automática | **RECOMENDADO** - baixa tudo sozinho |
| `/extract` | Extração manual | Controle fino, casos especiais |

**Regra de ouro:** Use `/extract-all` para 99% dos casos! 🚀
