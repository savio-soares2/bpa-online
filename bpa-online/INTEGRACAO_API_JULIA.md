

## 📊 Fluxo

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   e-SUS / PEC   │───▶│   API Julia     │───▶│   Tratamento    │───▶│  Firebird BPA   │
│   (PostgreSQL)  │    │   (Extração)    │    │   dos Dados     │    │  (BPAMAG.GDB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                      │
                              ▼                      ▼
                       JSON padronizado        INSERT S_PRD
```

**Relatórios são gerados manualmente no software BPA após a importação.**

---

# 📋 PARTE 1: BPA-I (INDIVIDUALIZADO)

Registra cada atendimento de forma individual, identificando o paciente.

---

## 🎯 Endpoint BPA-I

```http
GET /api/extracao/bpa-i?cnes=6061478&competencia=202511
```

| Parâmetro | Tipo | Obrigatório | Exemplo |
|-----------|------|-------------|---------|
| `cnes` | string | ✅ | `6061478` |
| `competencia` | string | ✅ | `202511` (YYYYMM) |

---

## 📤 Resposta JSON BPA-I

```json
{
  "status": "success",
  "tipo": "BPA-I",
  "cnes": "6061478",
  "competencia": "202511",
  "total_registros": 4665,
  "registros": [
    {
      "cns_profissional": "700001016250104",
      "cbo": "223505",
      "procedimento": "0301010048",
      "cns_paciente": "700501926845056",
      "nome_paciente": "VALDONEZ AIRES RIBEIRO",
      "data_nascimento": "1976-03-03",
      "sexo": "M",
      "raca_cor": "01",
      "municipio_ibge": "172100",
      "data_atendimento": "2025-11-21",
      "quantidade": 1,
      "cid": null,
      "carater_atendimento": "01",
      "equipe_ine": "0000041653"
    }
  ]
}
```

---

## 📝 Campos BPA-I → Firebird (S_PRD)

| Campo JSON | Coluna S_PRD | Tamanho | Obrigatório |
|------------|--------------|---------|-------------|
| `cns_profissional` | PRD_CNS | 15 | ✅ |
| `cbo` | PRD_CBO | 6 | ✅ |
| `procedimento` | PRD_PA | 10 | ✅ |
| `cns_paciente` | PRD_CNSPA | 15 | ✅ |
| `nome_paciente` | PRD_NOME | 30 | ✅ |
| `data_nascimento` | PRD_DTNAS | DATE | ✅ |
| `sexo` | PRD_SEXO | 1 | ✅ |
| `raca_cor` | PRD_RACA | 2 | ✅ |
| `municipio_ibge` | PRD_MUN | 6 | ✅ |
| `data_atendimento` | PRD_DT | DATE | ✅ |
| `quantidade` | PRD_QT_P | INT | ✅ |
| `cid` | PRD_CID | 4 | ❌ |
| `carater_atendimento` | PRD_CAR | 2 | ✅ |
| `equipe_ine` | PRD_INE | 10 | ❌ |
| - | PRD_ORG | 3 | `'BPI'` (fixo) |

---

## 🔥 INSERT Firebird BPA-I

```sql
INSERT INTO S_PRD (
    PRD_CNES, PRD_CMP, PRD_CNS, PRD_CBO, PRD_PA,
    PRD_CNSPA, PRD_NOME, PRD_DTNAS, PRD_SEXO, PRD_RACA,
    PRD_MUN, PRD_DT, PRD_QT_P, PRD_CID, PRD_CAR,
    PRD_INE, PRD_ORG
) VALUES (
    '6061478',           -- CNES
    '202511',            -- Competência YYYYMM
    '700001016250104',   -- CNS Profissional
    '223505',            -- CBO
    '0301010048',        -- Procedimento
    '700501926845056',   -- CNS Paciente
    'VALDONEZ AIRES RIBEIRO', -- Nome (máx 30 chars)
    '1976-03-03',        -- Data Nascimento
    'M',                 -- Sexo
    '01',                -- Raça/Cor
    '172100',            -- IBGE Município
    '2025-11-21',        -- Data Atendimento
    1,                   -- Quantidade
    NULL,                -- CID (opcional)
    '01',                -- Caráter Atendimento
    '0000041653',        -- INE Equipe
    'BPI'                -- Origem: BPA Individualizado
);
```

---

# 📋 PARTE 2: BPA-C (CONSOLIDADO)

Agrupa procedimentos por profissional, sem identificar pacientes individualmente.

---

## 🎯 Endpoint BPA-C

```http
GET /api/extracao/bpa-c?cnes=6061478&competencia=202511
```

---

## 📤 Resposta JSON BPA-C

```json
{
  "status": "success",
  "tipo": "BPA-C",
  "cnes": "6061478",
  "competencia": "202511",
  "total_registros": 150,
  "registros": [
    {
      "cns_profissional": "700001016250104",
      "cbo": "223505",
      "procedimento": "0101010010",
      "idade": "999",
      "quantidade": 45
    }
  ]
}
```

---

## 📝 Campos BPA-C → Firebird (S_PRD)

| Campo JSON | Coluna S_PRD | Tamanho | Obrigatório |
|------------|--------------|---------|-------------|
| `cns_profissional` | PRD_CNS | 15 | ✅ |
| `cbo` | PRD_CBO | 6 | ✅ |
| `procedimento` | PRD_PA | 10 | ✅ |
| `idade` | PRD_IDADE | 3 | ✅ (`999` = todas) |
| `quantidade` | PRD_QT_P | INT | ✅ |
| - | PRD_ORG | 3 | `'BPC'` (fixo) |

---

## 🔥 INSERT Firebird BPA-C

```sql
INSERT INTO S_PRD (
    PRD_CNES, PRD_CMP, PRD_CNS, PRD_CBO, PRD_PA,
    PRD_IDADE, PRD_QT_P, PRD_ORG
) VALUES (
    '6061478',           -- CNES
    '202511',            -- Competência YYYYMM
    '700001016250104',   -- CNS Profissional
    '223505',            -- CBO
    '0101010010',        -- Procedimento
    '999',               -- Idade (999 = todas)
    45,                  -- Quantidade TOTAL
    'BPC'                -- Origem: BPA Consolidado
);
```

---

# 📚 REFERÊNCIA

## Códigos Raça/Cor (BPA-I)
| Código | Descrição |
|--------|-----------|
| `01` | Branca |
| `02` | Preta |
| `03` | Parda |
| `04` | Amarela |
| `05` | Indígena |
| `99` | Sem informação |

## Códigos Caráter Atendimento (BPA-I)
| Código | Descrição |
|--------|-----------|
| `01` | Eletivo |
| `02` | Urgência |

## Sexo (BPA-I)
| Código | Descrição |
|--------|-----------|
| `M` | Masculino |
| `F` | Feminino |

---

# 🔄 QUERY e-SUS (PostgreSQL)

## Extração BPA-I
```sql
SELECT 
    p.nu_cns AS cns_profissional,
    p.nu_cbo AS cbo,
    proc.co_procedimento AS procedimento,
    c.nu_cns AS cns_paciente,
    UPPER(UNACCENT(c.no_cidadao)) AS nome_paciente,
    c.dt_nascimento AS data_nascimento,
    c.co_sexo AS sexo,
    COALESCE(c.co_raca_cor, '99') AS raca_cor,
    c.co_municipio_ibge AS municipio_ibge,
    a.dt_atendimento AS data_atendimento,
    1 AS quantidade,
    cid.co_cid AS cid,
    '01' AS carater_atendimento,
    e.nu_ine AS equipe_ine
FROM tb_fat_atendimento_individual a
JOIN tb_fat_cidadao c ON a.co_cidadao = c.co_seq_fat_cidadao
JOIN tb_dim_profissional p ON a.co_profissional = p.co_seq_dim_profissional
JOIN tb_fat_procedimento_atendimento proc ON a.co_seq_fat_atd_ind = proc.co_fat_atd_ind
LEFT JOIN tb_fat_cid cid ON a.co_seq_fat_atd_ind = cid.co_fat_atd_ind
LEFT JOIN tb_dim_equipe e ON a.co_equipe = e.co_seq_dim_equipe
JOIN tb_dim_unidade_saude u ON a.co_unidade_saude = u.co_seq_dim_unidade_saude
WHERE u.nu_cnes = :cnes
  AND a.dt_atendimento BETWEEN :data_inicio AND :data_fim
  AND a.st_registro_valido = 1
ORDER BY p.nu_cns, a.dt_atendimento;
```

## Extração BPA-C
```sql
SELECT 
    p.nu_cns AS cns_profissional,
    p.nu_cbo AS cbo,
    proc.co_procedimento AS procedimento,
    '999' AS idade,
    COUNT(*) AS quantidade
FROM tb_fat_atividade_coletiva a
JOIN tb_dim_profissional p ON a.co_profissional = p.co_seq_dim_profissional
JOIN tb_fat_procedimento_atividade proc ON a.co_seq_fat_atv_col = proc.co_fat_atv_col
JOIN tb_dim_unidade_saude u ON a.co_unidade_saude = u.co_seq_dim_unidade_saude
WHERE u.nu_cnes = :cnes
  AND EXTRACT(YEAR FROM a.dt_atividade) = :ano
  AND EXTRACT(MONTH FROM a.dt_atividade) = :mes
  AND a.st_registro_valido = 1
GROUP BY p.nu_cns, p.nu_cbo, proc.co_procedimento
ORDER BY p.nu_cns, proc.co_procedimento;
```

---

# ⚠️ TRATAMENTOS NECESSÁRIOS

Antes de inserir no Firebird, aplicar:

1. **Nome**: `UPPER(UNACCENT(nome))` - maiúsculo sem acentos, máx 30 chars
2. **CNS**: Validar 15 dígitos numéricos
3. **Procedimento**: 10 dígitos (código SIGTAP)
4. **Data**: Converter de `YYYY-MM-DD` para formato Firebird
5. **Nulos**: Campos opcionais como `NULL`, não string vazia
6. **Duplicados**: Verificar se registro já existe antes de inserir

---

# ✅ CHECKLIST

## API Julia
- [ ] Endpoint BPA-I retorna JSON válido
- [ ] Endpoint BPA-C retorna JSON válido
- [ ] CNS com 15 dígitos
- [ ] Procedimento com 10 dígitos
- [ ] Nome sem acentos, maiúsculo
- [ ] Raça/cor com código válido
- [ ] Sexo apenas M ou F

## Importação Firebird
- [ ] Conexão com BPAMAG.GDB
- [ ] INSERT S_PRD funcionando
- [ ] PRD_ORG = 'BPI' ou 'BPC' conforme tipo
- [ ] Competência no formato YYYYMM

