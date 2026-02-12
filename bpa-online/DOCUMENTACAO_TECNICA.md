# 📋 Documentação Técnica - BPA Online

## Visão Geral do Sistema

O **BPA Online** é um sistema que automatiza o fluxo de produção ambulatorial (BPA - Boletim de Produção Ambulatorial) do SUS, eliminando a necessidade do software BPA do DATASUS para geração de relatórios.

### Objetivo Principal
Extrair dados de produção do e-SUS/PEC, processar e gerar relatórios BPA no formato oficial do DATASUS, garantindo **consistência financeira** e **conformidade** com as tabelas SIGTAP.

---

## 🔄 Fluxo Completo do Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   e-SUS / PEC   │───▶│    Extração     │───▶│    Firebird     │───▶│   Relatórios    │
│   (PostgreSQL)  │    │   (SQL Parser)  │    │   (BPAMAG.GDB)  │    │   (TXT/PDF)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │   DBFs SIGTAP   │
                                              │  (Validação +   │
                                              │   Valores $)    │
                                              └─────────────────┘
```

---

## 📊 Arquitetura de Dados

### 1. Fonte de Dados: e-SUS/PEC (PostgreSQL)
- **Localização**: Servidor local ou remoto do e-SUS
- **Dados extraídos**: Atendimentos individuais, procedimentos, pacientes
- **Script**: `BPA-main/scripts/extracao_pec.py`

### 2. Banco Intermediário: Firebird (BPAMAG.GDB)
- **Localização**: `C:\BPA\BPAMAG.GDB`
- **Função**: Armazena produção processada para validação
- **Tabela principal**: `S_PRD` (produção)

### 3. Tabelas de Referência: DBFs SIGTAP
- **Localização**: `BPA-main/RELATORIOS/`
- **Atualização**: Mensal via executáveis do DATASUS
- **Função**: Validação de procedimentos e **valores financeiros**

---

## 💰 Fluxo Financeiro - Como os Valores são Calculados

### Passo 1: Identificação do Procedimento
```
Dado no Firebird (S_PRD):
  PRD_PA = "0301010048" (código do procedimento)
```

### Passo 2: Busca no DBF de Procedimentos (S_PA.DBF)
```python
# Arquivo: backend/services/report_generator.py

def get_procedimento_valor(self, pa_cod: str) -> float:
    """Retorna valor (PA_TOTAL) de um procedimento"""
    if not pa_cod:
        return 0.0
    proc = self.get_procedimento(pa_cod)
    if proc:
        return proc.get('PA_TOTAL', 0.0)  # ← VALOR FINANCEIRO
    return 0.0
```

### Passo 3: Campos do S_PA.DBF
| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `PA_ID` | Código do procedimento (9 dígitos) | `030101004` |
| `PA_DV` | Dígito verificador | `8` |
| `PA_TOTAL` | **Valor financeiro (PREVIA)** | `6.30` |
| `PA_DC` | Descrição do procedimento | `CONSULTA MEDICA...` |
| `PA_CMP` | Competência de vigência | `202501` |

### Passo 4: Cálculo do Valor Total
```python
# Fórmula:
valor_total = Σ (PA_TOTAL × PRD_QT_P)

# Onde:
# - PA_TOTAL = valor unitário do procedimento (do DBF)
# - PRD_QT_P = quantidade realizada (do Firebird)
```

---

## 📁 Estrutura dos Arquivos DBF (SIGTAP)

### Arquivos Críticos para Validação

| Arquivo | Função | Campos Principais |
|---------|--------|-------------------|
| `S_PA.DBF` | **Procedimentos + Valores** | PA_ID, PA_TOTAL, PA_DC |
| `S_PACBO.DBF` | Procedimento × CBO | Valida se CBO pode fazer procedimento |
| `S_PACID.DBF` | Procedimento × CID | Valida CID obrigatório |
| `S_CID.DBF` | Tabela de CIDs | CD_COD, CD_DSC |
| `CADMUN.DBF` | Municípios IBGE | CODUF, CODMUNIC |
| `S_PROCED.DBF` | Descrições procedimentos | PA_CODPR, PA_DSC |

### Atualização dos DBFs
```
Os DBFs são atualizados MENSALMENTE pelo DATASUS.
Executar os arquivos .EXE em BPA-main/RELATORIOS/ para atualizar.
⚠️ CRÍTICO: DBFs desatualizados = valores incorretos!
```

---

## 🗄️ Estrutura do Firebird (S_PRD)

### Campos Principais da Tabela de Produção

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `PRD_UID` | VARCHAR | CNES do estabelecimento |
| `PRD_CMP` | VARCHAR | Competência (YYYYMM) |
| `PRD_CNSMED` | VARCHAR | CNS do profissional |
| `PRD_CBO` | VARCHAR | CBO do profissional |
| `PRD_PA` | VARCHAR | Código do procedimento (10 dígitos) |
| `PRD_CNSPAC` | VARCHAR | CNS do paciente |
| `PRD_NMPAC` | VARCHAR | Nome do paciente |
| `PRD_DTNASC` | VARCHAR | Data nascimento (YYYYMMDD) |
| `PRD_SEXO` | CHAR | Sexo (M/F) |
| `PRD_RACA` | VARCHAR | Código raça/cor |
| `PRD_IBGE` | VARCHAR | Código IBGE município |
| `PRD_DTATEN` | VARCHAR | Data atendimento (YYYYMMDD) |
| `PRD_QT_P` | INTEGER | **Quantidade realizada** |
| `PRD_CATEN` | VARCHAR | Caráter atendimento |
| `PRD_ORG` | VARCHAR | Origem: `BPI` (individualizado) ou `BPC` (consolidado) |
| `PRD_FL*` | CHAR | Flags de erro (FLPA, FLCBO, FLCID, etc.) |

### Flags de Validação
```
PRD_FLPA  = '0' → Procedimento OK
PRD_FLCBO = '0' → CBO válido para o procedimento
PRD_FLCID = '0' → CID válido
PRD_FLMUN = '0' → Município OK
PRD_FLIDA = '0' → Idade OK para o procedimento
PRD_FLQT  = '0' → Quantidade OK

Se qualquer flag ≠ '0' → Registro "Com Erros"
```

---

## 📄 Formato do Relatório TXT (BPAI_REL.TXT)

### Estrutura do Arquivo
```
┌────────────────────────────────────────────────────────────────────────────────┐
│ CABEÇALHO DA PÁGINA                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│     Folha:   1******************************************************Versao: 04.10│
│     MS/SAS/DATASUS/BPA  SISTEMA DE INFORMACOES AMBULATORIAIS       Data Comp   │
│     15/12/2025           RELATORIO DE BPA INDIVIDUALIZADO          NOV/2025    │
│     ***************************************************************************│
├────────────────────────────────────────────────────────────────────────────────┤
│ CABEÇALHO DO PROFISSIONAL                                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│     CNES  : 6061478                                                            │
│     CNS PROFISSIONAL 700001016250104  CBO : 223505                             │
│     COMPETENCIA : 11/2025 FOLHA : 001                                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ LINHA DE TÍTULOS                                                               │
├────────────────────────────────────────────────────────────────────────────────┤
│     SQ CNS PACIENTE/NOME  DT.NASC SEXO RACA MUNIC. DT.ATEND.  PROCEDIMENTO...  │
├────────────────────────────────────────────────────────────────────────────────┤
│ REGISTROS (2 linhas cada)                                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│     01 700501926845056 03/03/1976 M    01  172100 21/11/2025 02.14.01.005-8... │
│        VALDONEZ AIRES RIBEIRO                                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│ RODAPÉ (FORMALIZAÇÃO)                                                          │
├────────────────────────────────────────────────────────────────────────────────┤
│     FORMALIZACAO ----------- Valores sujeitos a criticas/alteração pelo gestor │
│     RESP.UNIDADE :           RESP.GESTOR MUNICIPAL :      RESP.GESTOR ESTADUAL │
│     Carimbo     Rubrica      Carimbo     Rubrica          Carimbo     Rubrica  │
│     Data:___/___/___         Data:___/___/___             Data:___/___/___     │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Layout da Linha de Dados (113 caracteres)
```
Posição  Campo         Tamanho  Exemplo
──────────────────────────────────────────────────
0-3      Indent        4        "    "
4-5      Sequencial    2        "01"
6        Espaço        1        " "
7-21     CNS Paciente  15       "700501926845056"
22       Espaço        1        " "
23-32    Dt Nascimento 10       "03/03/1976"
33       Espaço        1        " "
34       Sexo          1        "M"
35-38    Espaços       4        "    "
39-40    Raça          2        "01"
41-42    Espaços       2        "  "
43-48    IBGE          6        "172100"
49       Espaço        1        " "
50-59    Dt Atendimento 10      "21/11/2025"
60       Espaço        1        " "
61-74    Procedimento  14       "02.14.01.005-8"
75-79    Espaços       5        "     "
80       Quantidade    1        "1"
81-86    Espaços       6        "      "
87-88    Car. Atend.   2        "01"
89-98    Espaços       10       "          "
99-102   Valor (PREVIA) 4       "1,00"
103      Espaço        1        " "
104-112  Situação      9        "Sem Erros"
```

---

## 🔌 API Endpoints

### Relatórios
```http
POST /api/reports/generate
Content-Type: application/json

{
  "cnes": "6061478",
  "competencia": "202511",
  "tipo_relatorio": "BPA-I"
}

Response:
{
  "status": "success",
  "message": "Relatório gerado com sucesso",
  "filename": "BPAI_6061478_202511.TXT",
  "content": "...",
  "total_records": 1234,
  "total_professionals": 15,
  "total_value": 12345.67  ← VALOR FINANCEIRO TOTAL
}
```

### Consulta de Procedimento
```http
GET /api/dbf/procedimento/030101004

Response:
{
  "codigo": "030101004",
  "pa_id": "030101004",
  "pa_dv": "8",
  "valor": 6.30,           ← VALOR UNITÁRIO
  "descricao": "CONSULTA MEDICA EM ATENCAO BASICA",
  "competencia": "202511"
}
```

### Registros do Firebird
```http
GET /api/firebird/records/6061478/202511

Response:
{
  "cnes": "6061478",
  "competencia": "202511",
  "total": 1234,
  "records": [...]
}
```

---

## ✅ Validações de Consistência

### 1. Validação de Procedimento
```python
# Verifica se procedimento existe no SIGTAP
proc = dbf_reader.get_procedimento(codigo)
if not proc:
    # PRD_FLPA = '1' (erro)
```

### 2. Validação CBO × Procedimento
```python
# Verifica se CBO pode executar o procedimento
# Arquivo: S_PACBO.DBF
```

### 3. Validação de Valor
```python
# Valor deve ser >= 0
# Procedimentos com valor 0 são válidos (ex: 03.01.01.003-0)
valor = dbf_reader.get_procedimento_valor(codigo)
```

### 4. Conferência de Totais
```python
# No relatório, soma de valores deve bater:
total_calculado = sum(valor_unitario * quantidade for each registro)
```

---

## ⚠️ Pontos Críticos para Auditoria

### 1. Atualização dos DBFs
```
⚠️ DBFs devem estar na competência correta!

Verificar:
- Data de modificação dos arquivos
- Competência nos registros (PA_CMP)
- Executar atualização mensal
```

### 2. Valores Zerados
```
Alguns procedimentos têm valor R$ 0,00 propositalmente:
- 03.01.01.003-0 (Consulta de enfermagem) = R$ 0,00
- São válidos e devem ser reportados
```

### 3. Duplicidade de Registros
```
Verificar no Firebird:
SELECT PRD_CNSPAC, PRD_PA, PRD_DTATEN, COUNT(*)
FROM S_PRD
WHERE PRD_CMP = '202511'
GROUP BY PRD_CNSPAC, PRD_PA, PRD_DTATEN
HAVING COUNT(*) > 1
```

### 4. Diferença entre Relatórios
```
Se houver diferença entre relatório gerado e oficial:
1. Verificar versão dos DBFs
2. Verificar competência
3. Comparar registros no Firebird
4. Verificar flags de erro
```

---

## 🔧 Manutenção

### Atualização Mensal
1. Baixar novos DBFs do DATASUS
2. Executar os .EXE em `BPA-main/RELATORIOS/`
3. Verificar data de modificação dos .DBF
4. Testar geração de relatório

### Backup
```powershell
# Backup do Firebird
copy C:\BPA\BPAMAG.GDB C:\BPA\backup\BPAMAG_%date%.GDB

# Backup dos DBFs
xcopy BPA-main\RELATORIOS\*.DBF backup\dbf\ /Y
```

### Logs
```
Os logs do backend mostram:
[LOG] Iniciando geração de relatório...
[LOG] CNES: 6061478, Competência: 202511
[LOG] Registros encontrados: 1234
[LOG] Valor total: 12345.67
```

---

## 📈 Métricas de Validação

### Conferência Rápida
```
✓ Total de registros = quantidade no Firebird
✓ Total de profissionais = CNS únicos
✓ Valor total = Σ(valor × quantidade)
✓ Formato do TXT = 113 chars por linha de dados
✓ Competência = formato correto (NOV/2025)
✓ Valores = vírgula decimal (6,30)
```

### Query de Verificação
```sql
-- Total esperado no relatório
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT PRD_CNSMED) as total_profissionais,
    SUM(PRD_QT_P) as total_procedimentos
FROM S_PRD 
WHERE PRD_UID = '6061478' 
  AND PRD_CMP = '202511'
  AND PRD_ORG = 'BPI';
```

---

## 📞 Suporte

### Problemas Comuns

| Problema | Causa Provável | Solução |
|----------|----------------|---------|
| Valor zerado incorreto | DBF desatualizado | Atualizar DBFs |
| Registro "Com Erros" | Flag de validação | Verificar PRD_FL* |
| Relatório vazio | Filtro PRD_ORG | Verificar se é BPI ou BPC |
| Layout diferente | Versão do gerador | Comparar com original |

---

**Versão do Documento**: 1.0  
**Data**: 15/12/2025  
**Sistema**: BPA Online v1.0
