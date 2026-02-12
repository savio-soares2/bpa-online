# 🔄 Sistema de Consolidação BPA-I → BPA-C

## 📋 Visão Geral

Este sistema automatiza a consolidação de registros BPA Individualizado (BPA-I) em BPA Consolidado (BPA-C), baseado em listas oficiais de procedimentos faturáveis.

---

## 🎯 Fluxo Completo

### **1. Extração do BiServer (CNES/eSUS)**
```
BiServer API → Backend Local (BPA-I)
```
- Baixa **TODOS** os registros do BiServer sem filtro
- Salva na tabela `bpa_individualizado`
- **Não faz distinção** entre tipos de procedimento nesta etapa

**Endpoint:**
```http
POST /api/biserver/extract
{
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i",
  "limit": 1000
}
```

### **2. Salvamento no Banco Local**
```
Cache (BiServer) → PostgreSQL (bpa_individualizado)
```
**Endpoint:**
```http
POST /api/biserver/save-extracted?cache_key=bpa_i_6061478_202512
```

### **3. Consolidação (Filtro por Procedimento)**
```
bpa_individualizado → [Análise] → bpa_consolidado
                              ↓
                        (Remove BPA-I convertidos)
```

**Endpoint:**
```http
POST /api/consolidation/execute?cnes=6061478&competencia=202512
```

---

## 📊 Tipos de Consolidação

### **Tipo 1: BPA-C Geral (≈800 procedimentos)**
- **Idade**: `000` (todas as idades juntas)
- **Agrupa por**: CNES + CBO + Procedimento + Competência
- **Exemplos**: Consultas, exames, procedimentos coletivos

### **Tipo 2: BPA-C com Idade (7 procedimentos específicos)**
- **Idade**: Mantém faixa etária original
- **Agrupa por**: CNES + CBO + Procedimento + Competência + **Idade**
- **Conversão automática na produção (todos os CNES)**:
  - `0301010064` → `0301010072`
  - `0301010030` → `0301010048`
- **Procedimentos**:
  - `0301010110` - Atendimento médico
  - `0301010030` - Consulta nível superior (exceto médico)
  - `0301010048` - Consulta médica atenção especializada
  - `0301010072` - Consulta nível superior atenção especializada
  - `0301010056` - Consulta médica atenção primária
  - `0301010064` - Consulta domiciliar médica
  - `0301010137` - Atendimento urgência atenção primária

### **Tipo 3: BPA-I (Procedimentos não listados)**
- **Mantém como está** no `bpa_individualizado`
- Não são consolidados

---

## 🔧 Endpoints da API

### **1. Verificar Procedimento**
```http
GET /api/consolidation/verify-procedure/0301010048
```

**Resposta:**
```json
{
  "codigo": "0301010048",
  "tipo": "BPA-C",
  "subtipo": "idade",
  "idade": "mantém",
  "descricao": "Deve ser consolidado COM separação por faixa etária"
}
```

### **2. Estatísticas Pré-Consolidação**
```http
GET /api/consolidation/stats?cnes=6061478&competencia=202512
```

**Resposta:**
```json
{
  "total_bpai": 450,
  "pode_consolidar_geral": 320,
  "pode_consolidar_idade": 100,
  "manter_bpai": 30,
  "procedimentos_geral": ["0101010010", "0102010056", ...],
  "procedimentos_idade": ["0301010048", "0301010056"],
  "procedimentos_manter": ["0201010020", ...]
}
```

### **3. Executar Consolidação**
```http
POST /api/consolidation/execute?cnes=6061478&competencia=202512
```

**Resposta:**
```json
{
  "success": true,
  "message": "Consolidação concluída para 6061478/202512",
  "stats": {
    "cnes": "6061478",
    "competencia": "202512",
    "bpai_analisados": 450,
    "bpac_geral_criados": 85,
    "bpac_idade_criados": 12,
    "bpai_removidos": 420,
    "bpai_mantidos": 30,
    "erros": []
  }
}
```

---

## 📁 Arquivos de Configuração

### **`backend/data/procedimentos_bpa_c.json`**
```json
{
  "bpa_c_geral": {
    "descricao": "SEM separação por idade",
    "procedimentos": ["0101010010", "0101010028", ...]
  },
  "bpa_c_idade": {
    "descricao": "COM separação por idade", 
    "procedimentos": ["0301010110", "0301010030", ...]
  }
}
```

---

## 💡 Exemplo de Uso Completo

```bash
# 1. Extrair do BiServer
POST /api/biserver/extract
{
  "cnes": "6061478",
  "competencia": "202512",
  "tipo": "bpa_i"
}

# 2. Salvar no banco
POST /api/biserver/save-extracted?cache_key=bpa_i_6061478_202512

# 3. Verificar estatísticas
GET /api/consolidation/stats?cnes=6061478&competencia=202512

# 4. Executar consolidação
POST /api/consolidation/execute?cnes=6061478&competencia=202512

# 5. Verificar resultados
GET /api/bpa/consolidado?competencia=202512  # BPA-C criados
GET /api/bpa/individualizado?competencia=202512  # BPA-I mantidos
```

---

## 🔍 Lógica de Consolidação

### **BPA-C Geral**
```python
# Agrupa por: (CNES, Competência, CBO, Procedimento)
# Soma quantidades
# Idade = '000'

Exemplo:
  5 registros BPA-I do mesmo profissional, mesmo procedimento
  → 1 registro BPA-C com quantidade = 5
```

### **BPA-C com Idade**
```python
# Agrupa por: (CNES, Competência, CBO, Procedimento, Idade)
# Soma quantidades
# Mantém faixa etária

Exemplo:
  3 consultas médicas, faixa 30-39 anos
  2 consultas médicas, faixa 40-49 anos
  → 2 registros BPA-C (um por faixa etária)
```

---

## 📦 Estrutura do Banco

### **Antes da Consolidação**
```
bpa_individualizado (450 registros)
├── Procedimento 0101010010 (5 registros) → Vira BPA-C
├── Procedimento 0301010048 (3 registros) → Vira BPA-C com idade
└── Procedimento 0201010020 (30 registros) → Mantém BPA-I
```

### **Depois da Consolidação**
```
bpa_consolidado (97 registros novos)
├── Procedimento 0101010010, QTD=5, IDADE=000
└── Procedimento 0301010048, QTD=3, IDADE=035

bpa_individualizado (30 registros restantes)
└── Procedimento 0201010020 (não convertidos)
```

---

## ⚠️ Observações Importantes

1. **Processo Irreversível**: BPA-I são **deletados** após consolidação
2. **Execute por Competência**: Consolide uma competência por vez
3. **Verifique Antes**: Use `/stats` para ver o que será consolidado
4. **Backup**: Sempre faça backup antes de consolidar
5. **Faturamento**: Apenas procedimentos **listados** são faturáveis

---

## 🚀 Roadmap

- [ ] Interface web para consolidação
- [ ] Agendamento automático por competência
- [ ] Relatórios de consolidação em PDF
- [ ] Validação cruzada com tabela SIGTAP
- [ ] Histórico de consolidações realizadas

---

**Desenvolvido para**: Sistema BPA Online  
**Baseado em**: Procedures Firebird do BPA Magnético  
**Última atualização**: 21/01/2026
