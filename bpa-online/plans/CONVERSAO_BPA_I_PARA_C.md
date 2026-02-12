# 📋 Plano de Implementação: Conversão BPA-I → BPA-C no Fluxo BiServer

## 📖 Resumo Executivo

**Objetivo:** Modificar o fluxo de extração do BiServer para que, ao baixar dados, procedimentos que podem ser **tanto BPA-I quanto BPA-C** sejam automaticamente convertidos e salvos como **BPA-C**.

---

## 🎯 Regra de Negócio

```
┌────────────────────────────────────────────────────────────────────┐
│  REGRA DE CONVERSÃO NA EXTRAÇÃO                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Se procedimento pode ser BPA-I E BPA-C:                           │
│      → Converter para BPA-C e salvar em bpa_consolidado            │
│                                                                    │
│  Se procedimento pode ser APENAS BPA-I:                            │
│      → Manter como BPA-I e salvar em bpa_individualizado           │
│                                                                    │
│  Se procedimento pode ser APENAS BPA-C:                            │
│      → Salvar diretamente em bpa_consolidado                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Estrutura do BPA-C (Ficha de Preenchimento)

Baseado na ficha de BPA Consolidado do DATASUS:

| Campo      | Descrição                | Fonte no BPA-I          |
|------------|--------------------------|-------------------------|
| CNES       | Código da unidade        | prd_uid                 |
| Mês/Ano    | Competência              | prd_cmp                 |
| Folha      | Número da folha          | Calculado               |
| SEQ        | Sequência (01-20)        | Calculado               |
| PROC.AMB.  | Código procedimento      | prd_pa                  |
| CBO        | Código ocupação          | prd_cbo                 |
| IDADE      | Idade paciente           | prd_idade               |
| QTD.       | Quantidade               | SUM(prd_qt_p)           |

**Nota:** No BPA-C, cada linha pode ter de 01 a 20 registros por folha (20 linhas × 2 colunas na tela).

---

## 🔄 Fluxo Atual vs Fluxo Proposto

### Fluxo Atual
```
BiServer API → extract_and_separate_bpa() → _separate_bpa_by_sigtap()
                    ↓
     ┌──────────────┴──────────────┐
     ↓                             ↓
 BPA-I (tipo=02)             BPA-C (tipo=01)
     ↓                             ↓
 bpa_individualizado         bpa_consolidado
```

### Fluxo Proposto
```
BiServer API → extract_and_separate_bpa() → _classify_and_convert_bpa()
                    ↓
     ┌──────────────┼──────────────┐
     ↓              ↓              ↓
APENAS BPA-I   BPA-I E BPA-C   APENAS BPA-C
(tipo=02 só)   (tipo=01+02)    (tipo=01 só)
     ↓              ↓              ↓
 BPA-I         CONVERTER      BPA-C direto
     ↓         para BPA-C          ↓
     ↓              ↓              ↓
bpa_individualizado    bpa_consolidado
```

---

## 🧩 Componentes a Modificar

### 1. `biserver_client.py` - Serviço de Extração

#### 1.1 Novo Método: `_classify_and_convert_bpa()`
```python
def _classify_and_convert_bpa(self, records: List[Dict], cnes: str = None) -> Dict[str, List[Dict]]:
    """
    Classifica e converte registros:
    - Procedimentos com tipo_registro = {01, 02}: Converte para BPA-C
    - Procedimentos com tipo_registro = {02} apenas: Mantém como BPA-I
    - Procedimentos com tipo_registro = {01} apenas: BPA-C direto
    
    Returns:
        {
            'bpa_i': [registros que ficam como BPA-I],
            'bpa_c': [registros para BPA-C (convertidos + diretos)],
            'stats': {...}
        }
    """
```

#### 1.2 Novo Método: `_convert_bpai_to_bpac()`
```python
def _convert_bpai_to_bpac(self, record: Dict) -> Dict:
    """
    Converte um registro de formato BPA-I para formato BPA-C
    
    Mapeamento:
    - prd_uid: mantém
    - prd_cmp: mantém
    - prd_pa: mantém
    - prd_cbo: mantém
    - prd_idade: extrai de prd_dtnasc ou usa existente
    - prd_qt_p: mantém
    
    Remove campos exclusivos de BPA-I:
    - prd_cnspac, prd_nmpac, prd_dtnasc, prd_sexo, etc.
    """
```

#### 1.3 Modificar: `extract_and_separate_bpa()`
Substituir chamada de `_separate_bpa_by_sigtap()` por `_classify_and_convert_bpa()`

### 2. `sigtap_filter_service.py` - Consultas SIGTAP

#### 2.1 Novo Método: `get_procedimentos_dual_registro()`
```python
def get_procedimentos_dual_registro(self, competencia: str = None) -> Set[str]:
    """
    Retorna códigos de procedimentos que podem ser TANTO BPA-I QUANTO BPA-C
    (possuem tipo_registro = {01, 02})
    """
```

#### 2.2 Novo Método: `get_procedimento_tipo_registro()`
```python
def get_procedimento_tipo_registro(self, procedimento: str, competencia: str = None) -> Dict:
    """
    Retorna tipos de registro permitidos para um procedimento
    
    Returns:
        {
            'codigo': '0301010072',
            'tipos': {'01', '02'},
            'dual': True,  # True se pode ser BPA-I e BPA-C
            'preferencia': 'BPA-C'  # Se dual, preferência é sempre BPA-C
        }
    """
```

### 3. `database.py` - Funções de Banco

#### 3.1 Novo Método: `save_bpa_consolidado_batch()`
```python
def save_bpa_consolidado_batch(self, records: List[Dict]) -> int:
    """
    Salva múltiplos registros BPA-C de uma vez
    Agrupa registros com mesma chave (CNES + CMP + CBO + PA + IDADE)
    somando quantidades
    """
```

### 4. `main.py` - Endpoints da API

#### 4.1 Novo Endpoint: `POST /api/biserver/extract-and-convert`
```python
@app.post("/api/biserver/extract-and-convert")
async def extract_and_convert_bpa(
    cnes: str,
    competencia: str,
    save_immediately: bool = True
):
    """
    Extrai dados do BiServer e já converte/salva no banco
    com a lógica de preferência BPA-C
    """
```

#### 4.2 Modificar: `POST /api/biserver/save-extracted`
Adaptar para tratar o novo formato de retorno com registros já convertidos

---

## 📁 Estrutura de Dados

### Registro BPA-I (Entrada do BiServer)
```json
{
    "prd_uid": "6061478",
    "prd_cmp": "202512",
    "prd_cnsmed": "700501234567890",
    "prd_cbo": "225125",
    "prd_cnspac": "700601234567890",
    "prd_nmpac": "MARIA DA SILVA",
    "prd_dtnasc": "19850315",
    "prd_sexo": "F",
    "prd_idade": "039",
    "prd_pa": "0301010072",
    "prd_qt_p": 1,
    "prd_dtaten": "20251210",
    "prd_cid": "Z000"
}
```

### Registro BPA-C (Após Conversão)
```json
{
    "prd_uid": "6061478",
    "prd_cmp": "202512",
    "prd_cnsmed": "700501234567890",
    "prd_cbo": "225125",
    "prd_pa": "0301010072",
    "prd_idade": "039",
    "prd_qt_p": 1,
    "prd_org": "BPC_CONV"
}
```

---

## 📐 Algoritmo de Conversão

```python
def classify_and_convert(records, registro_map):
    bpa_i_final = []
    bpa_c_raw = []
    
    for record in records:
        proc = record['prd_pa']
        tipos = registro_map.get(proc, set())
        
        if '01' in tipos and '02' in tipos:
            # DUAL: Converte para BPA-C
            bpa_c_raw.append(convert_to_bpac(record))
        elif '02' in tipos:
            # APENAS BPA-I
            bpa_i_final.append(record)
        elif '01' in tipos:
            # APENAS BPA-C
            bpa_c_raw.append(convert_to_bpac(record))
        else:
            # Não é BPA (e-SUS, RAAS, etc) - descarta ou log
            pass
    
    # Agrupa BPA-C por chave
    bpa_c_final = aggregate_bpac(bpa_c_raw)
    
    return bpa_i_final, bpa_c_final
```

### Função de Agregação BPA-C
```python
def aggregate_bpac(records):
    """
    Agrupa por: CNES + CMP + CBO + PA + IDADE
    Soma: QT_P (quantidade)
    """
    groups = {}
    
    for rec in records:
        key = (rec['prd_uid'], rec['prd_cmp'], rec['prd_cbo'], 
               rec['prd_pa'], rec['prd_idade'])
        
        if key not in groups:
            groups[key] = rec.copy()
            groups[key]['prd_qt_p'] = 0
        
        groups[key]['prd_qt_p'] += rec.get('prd_qt_p', 1)
    
    return list(groups.values())
```

---

## 🧪 Testes Necessários

### Casos de Teste

| Cenário | Procedimento | Tipo Registro SIGTAP | Resultado Esperado |
|---------|--------------|---------------------|-------------------|
| 1 | 0301010072 | {01, 02} | Converte para BPA-C |
| 2 | 0301010196 | {02} | Mantém como BPA-I |
| 3 | 0214010015 | {01} | BPA-C direto |
| 4 | Não existe | {} | Descarta com log |

### Teste de Agregação

```
Entrada:
- Paciente A, Proc X, Idade 30, Qtd 1
- Paciente B, Proc X, Idade 30, Qtd 1
- Paciente C, Proc X, Idade 45, Qtd 1

Saída BPA-C:
- Proc X, Idade 030, Qtd 2
- Proc X, Idade 045, Qtd 1
```

---

## 📝 Checklist de Implementação

### Fase 1: Core Logic (biserver_client.py)
- [ ] Criar método `_get_dual_procedures()` para cache
- [ ] Criar método `_classify_record()` para classificar 1 registro
- [ ] Criar método `_convert_bpai_to_bpac()` para conversão
- [ ] Criar método `_aggregate_bpac_records()` para agregação
- [ ] Criar método `_classify_and_convert_bpa()` principal
- [ ] Modificar `extract_and_separate_bpa()` para usar nova lógica

### Fase 2: SIGTAP Service (sigtap_filter_service.py)
- [ ] Criar `get_procedimentos_dual_registro()`
- [ ] Criar `is_dual_registro(procedimento)`
- [ ] Criar `get_registro_info(procedimento)`

### Fase 3: Database (database.py)
- [ ] Criar `save_bpa_consolidado_batch()` com agregação
- [ ] Modificar `save_extracted_bpa()` para tratar conversão

### Fase 4: API Endpoints (main.py)
- [ ] Criar endpoint `/api/biserver/extract-and-convert`
- [ ] Modificar endpoint `/api/biserver/save-extracted`
- [ ] Adicionar endpoint de verificação de procedimento

### Fase 5: Testes
- [ ] Testes unitários de classificação
- [ ] Testes de conversão
- [ ] Testes de agregação
- [ ] Teste de integração completo

---

## 🔍 Considerações Importantes

### 1. Idade no BPA-C
- **Formato:** 3 dígitos (ex: "039" para 39 anos)
- **Cálculo:** Se não existir `prd_idade`, calcular de `prd_dtnasc`
- **Agrupamento:** Idade faz parte da chave de agregação

### 2. CNS Profissional
- No BPA-C atual, `prd_cnsmed` pode ser mantido ou omitido
- Verificar se a ficha BPA-C exige CNS do profissional

### 3. Folha e Sequência
- Serão calculados na hora da exportação/geração do arquivo
- Não armazenar no banco durante a conversão

### 4. Rollback
- Manter log de quais registros foram convertidos
- Possibilidade de reverter (se necessário)

### 5. Compatibilidade
- O fluxo antigo deve continuar funcionando
- Nova funcionalidade é opt-in ou configurável

---

## 📈 Métricas de Sucesso

- [ ] 100% dos procedimentos dual são convertidos para BPA-C
- [ ] Nenhum procedimento exclusivo BPA-I é convertido incorretamente
- [ ] Quantidades agregadas corretamente
- [ ] Performance: conversão não aumenta tempo de extração > 10%
- [ ] Todos os testes passando

---

## 🗓️ Próximos Passos

1. **Validar** lista de procedimentos dual no SIGTAP atual
2. **Implementar** fase 1 (core logic)
3. **Testar** com dados reais de uma competência
4. **Revisar** e ajustar conforme feedback
5. **Deploy** em ambiente de teste
6. **Homologação** com usuário final
