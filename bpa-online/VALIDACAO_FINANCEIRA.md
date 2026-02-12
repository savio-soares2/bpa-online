# 💰 Validação Financeira - BPA Online

## Rastreabilidade do Valor Financeiro

Este documento detalha como cada centavo é calculado no sistema, garantindo auditabilidade total.

---

## 🔍 Origem do Valor: Tabela SIGTAP (S_PA.DBF)

### Estrutura do Arquivo S_PA.DBF
```
Localização: BPA-main/RELATORIOS/S_PA.DBF
Tamanho: ~3 MB
Registros: ~11.000 procedimentos
Atualização: Mensal pelo DATASUS
```

### Campos Relevantes para Valor
| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `PA_CMP` | Char(6) | Competência de vigência | `202511` |
| `PA_ID` | Char(9) | Código do procedimento | `030101004` |
| `PA_DV` | Char(1) | Dígito verificador | `8` |
| `PA_TOTAL` | Numeric(10,2) | **VALOR FINANCEIRO** | `6.30` |
| `PA_DC` | Char(250) | Descrição | `CONSULTA MED...` |

### Como o Valor é Consultado
```python
# backend/services/report_generator.py

class DBFReader:
    def get_procedimento_valor(self, pa_cod: str) -> float:
        """
        Busca valor financeiro de um procedimento.
        
        Fluxo:
        1. Recebe código completo: "0301010048"
        2. Extrai PA_ID: "030101004" (9 primeiros dígitos)
        3. Busca no S_PA.DBF pelo PA_ID
        4. Retorna PA_TOTAL (valor em reais)
        """
        if not pa_cod:
            return 0.0
        
        # Remove formatação e pega só o ID
        pa_id = pa_cod.replace('.', '').replace('-', '')[:9]
        
        # Busca no DBF
        for rec in self._load_dbf('S_PA.DBF'):
            if rec.get('PA_ID') == pa_id:
                return rec.get('PA_TOTAL', 0.0)
        
        return 0.0
```

---

## 📊 Exemplos de Valores Reais

### Procedimentos Comuns na APS
| Código | Descrição | Valor (R$) |
|--------|-----------|------------|
| 03.01.01.003-0 | Consulta de enfermagem | 0,00 |
| 03.01.01.004-8 | Consulta médica em atenção básica | 6,30 |
| 02.14.01.005-8 | Hemograma completo | 1,00 |
| 02.14.01.007-4 | Dosagem de glicose | 1,00 |

### Verificação Manual
```powershell
# Consultar valor via API
Invoke-RestMethod -Uri "http://localhost:8000/api/dbf/procedimento/030101004"

# Resposta:
# {
#   "codigo": "030101004",
#   "valor": 6.30,
#   "descricao": "CONSULTA MEDICA EM ATENCAO BASICA"
# }
```

---

## 🧮 Cálculo do Valor Total

### Fórmula
```
VALOR_TOTAL = Σ (PA_TOTAL[i] × PRD_QT_P[i])

Onde:
- PA_TOTAL[i] = Valor unitário do procedimento i (do S_PA.DBF)
- PRD_QT_P[i] = Quantidade realizada do procedimento i (do Firebird)
```

### Exemplo Prático
```
Registro 1: Consulta médica (03.01.01.004-8), Qtd: 1
  → 6,30 × 1 = R$ 6,30

Registro 2: Hemograma (02.14.01.005-8), Qtd: 1
  → 1,00 × 1 = R$ 1,00

Registro 3: Consulta enfermagem (03.01.01.003-0), Qtd: 3
  → 0,00 × 3 = R$ 0,00

TOTAL = 6,30 + 1,00 + 0,00 = R$ 7,30
```

### Código de Cálculo
```python
# backend/main.py - endpoint /api/reports/generate

# Calcula valor total
dbf_reader = DBFReader(DBF_PATH)
total_value = 0.0

for record in records:
    pa = record.get('PRD_PA') or ''      # Código procedimento
    qt = record.get('PRD_QT_P') or 0     # Quantidade
    
    valor_unitario = dbf_reader.get_procedimento_valor(pa)
    valor_registro = valor_unitario * int(qt)
    
    total_value += valor_registro

# total_value = valor financeiro total da competência
```

---

## ✅ Pontos de Validação

### 1. Consistência DBF ↔ Relatório
```sql
-- Query no Firebird para conferir
SELECT 
    PRD_PA,
    SUM(PRD_QT_P) as total_qtd
FROM S_PRD 
WHERE PRD_UID = '6061478' 
  AND PRD_CMP = '202511'
  AND PRD_ORG = 'BPI'
GROUP BY PRD_PA
ORDER BY PRD_PA;
```

```python
# Conferência em Python
for proc, qtd in query_result:
    valor_dbf = dbf_reader.get_procedimento_valor(proc)
    subtotal = valor_dbf * qtd
    print(f"{proc}: {qtd} × R$ {valor_dbf:.2f} = R$ {subtotal:.2f}")
```

### 2. Validação de Competência
```
⚠️ CRÍTICO: O S_PA.DBF tem valores por competência!

Verificar:
- Campo PA_CMP no DBF = competência do relatório
- Se PA_CMP > competência → procedimento não existia
- Se PA_CMP < competência → pode ter valor diferente
```

### 3. Procedimentos sem Valor
```
Procedimentos com PA_TOTAL = 0.00 são VÁLIDOS!

Exemplos:
- Consultas de enfermagem
- Alguns procedimentos coletivos
- Ações educativas

NÃO são erros, devem ser reportados normalmente.
```

---

## 🔄 Fluxo de Auditoria

### Passo a Passo para Conferir um Valor

1. **Identificar o registro no relatório**
   ```
   01 700501926845056 03/03/1976 M    01  172100 21/11/2025 03.01.01.004-8     1      01          6,30 Sem Erros
   ```

2. **Extrair informações**
   ```
   CNS Paciente: 700501926845056
   Procedimento: 03.01.01.004-8 (código: 0301010048)
   Quantidade: 1
   Valor: 6,30
   ```

3. **Verificar no DBF**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/api/dbf/procedimento/030101004"
   # Deve retornar valor: 6.30
   ```

4. **Verificar no Firebird**
   ```sql
   SELECT PRD_PA, PRD_QT_P 
   FROM S_PRD 
   WHERE PRD_CNSPAC = '700501926845056'
     AND PRD_PA = '0301010048'
     AND PRD_DTATEN = '20251121';
   ```

5. **Conferir cálculo**
   ```
   6.30 (DBF) × 1 (Firebird) = 6,30 (Relatório) ✓
   ```

---

## 📋 Checklist de Validação Financeira

### Antes de Gerar Relatório
- [ ] DBFs atualizados para a competência
- [ ] Verificar data de modificação do S_PA.DBF
- [ ] Conferir amostra de valores no DBF

### Após Gerar Relatório
- [ ] Total de registros confere com Firebird
- [ ] Valor total está coerente
- [ ] Nenhum procedimento com valor inesperado
- [ ] Formato do valor correto (vírgula decimal)

### Mensal
- [ ] Baixar novos DBFs do DATASUS
- [ ] Comparar valores alterados
- [ ] Documentar procedimentos novos/removidos

---

## 🚨 Alertas de Inconsistência

### Valor Diferente do Esperado
```
Possíveis causas:
1. DBF desatualizado
2. Procedimento com valor alterado na competência
3. Erro no código do procedimento
4. Quantidade incorreta no Firebird
```

### Procedimento Não Encontrado
```
Se get_procedimento_valor() retorna 0.0 para código válido:
1. Verificar se PA_ID está correto (9 dígitos)
2. Verificar encoding do DBF (latin-1)
3. Verificar se procedimento existe na competência
```

### Diferença no Total
```
Se soma manual ≠ total do sistema:
1. Verificar se todos os registros foram incluídos
2. Verificar filtro PRD_ORG = 'BPI'
3. Verificar arredondamento (2 casas decimais)
```

---

## 📊 Relatório de Conferência

### Modelo de Relatório de Auditoria
```
═══════════════════════════════════════════════════════════
RELATÓRIO DE CONFERÊNCIA FINANCEIRA - BPA INDIVIDUALIZADO
═══════════════════════════════════════════════════════════
CNES: 6061478
Competência: 11/2025
Data Geração: 15/12/2025

RESUMO:
- Total de Registros: 1.234
- Total de Profissionais: 15
- Total de Procedimentos Distintos: 45

VALORES:
- Valor Bruto Calculado: R$ 12.345,67
- Procedimentos com valor: 890
- Procedimentos sem valor: 344

TOP 5 PROCEDIMENTOS POR VALOR:
1. 03.01.01.004-8: 500 × R$ 6,30 = R$ 3.150,00
2. 02.14.01.005-8: 200 × R$ 1,00 = R$ 200,00
3. ...

VALIDAÇÕES:
[✓] Todos procedimentos encontrados no SIGTAP
[✓] Valores conferem com S_PA.DBF
[✓] Nenhuma quantidade negativa
[✓] Total calculado = Total reportado

ASSINATURA DIGITAL: SHA256-abc123...
═══════════════════════════════════════════════════════════
```

---

## 🔐 Garantias do Sistema

### Integridade
- Valores lidos diretamente do DBF oficial
- Sem modificação nos valores originais
- Log de todas as operações

### Rastreabilidade
- Cada valor pode ser rastreado até o DBF
- Registro de data/hora de geração
- Identificação de versão dos DBFs

### Auditabilidade
- Código fonte aberto e documentado
- Fórmulas de cálculo explícitas
- Possibilidade de conferência manual

---

**Versão**: 1.0  
**Data**: 15/12/2025  
**Responsável Técnico**: Sistema BPA Online
