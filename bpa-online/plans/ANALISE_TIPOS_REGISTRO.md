# 📊 Análise Técnica: Tipos de Registro SIGTAP

## Contexto

A tabela SIGTAP `rl_procedimento_registro` define quais tipos de registro um procedimento pode utilizar:
- **01** = BPA Consolidado (BPA-C)
- **02** = BPA Individualizado (BPA-I)
- **03** = APAC
- **04** = AIH
- Outros...

## Cenários de Procedimentos

### Cenário 1: Procedimento APENAS BPA-I
```
Procedimento: 0301010196 (Consulta/Atendimento Domiciliar)
Registros: {02}
Ação: Salva em bpa_individualizado
```

### Cenário 2: Procedimento APENAS BPA-C
```
Procedimento: 0214010015 (Acolhimento com classificação de risco)
Registros: {01}
Ação: Converte e salva em bpa_consolidado
```

### Cenário 3: Procedimento DUAL (BPA-I e BPA-C)
```
Procedimento: 0301010072 (Consulta médica atenção básica)
Registros: {01, 02}
Ação: PREFERE BPA-C → Converte e salva em bpa_consolidado
```

## Tabela de Decisão

| Tem 01 | Tem 02 | Decisão | Tabela Destino |
|--------|--------|---------|----------------|
| ❌ | ✅ | BPA-I | bpa_individualizado |
| ✅ | ❌ | BPA-C | bpa_consolidado |
| ✅ | ✅ | **BPA-C** | bpa_consolidado |
| ❌ | ❌ | Descarta | (não é BPA) |

## Código de Consulta SIGTAP

```python
# Verificar tipos de registro de um procedimento
def get_registro_tipos(procedimento: str) -> set:
    relacoes = sigtap_parser.parse_procedimento_registro()
    tipos = set()
    for rel in relacoes:
        if rel['CO_PROCEDIMENTO'] == procedimento:
            tipos.add(rel['CO_REGISTRO'])
    return tipos

# Exemplo
tipos = get_registro_tipos('0301010072')
# Retorna: {'01', '02'}

is_dual = '01' in tipos and '02' in tipos
# Retorna: True
```

## Procedimentos Comuns DUAL (provável)

Baseado em análise preliminar, procedimentos comuns que provavelmente são dual:
- 0301010072 - Consulta médica atenção básica
- 0301010064 - Consulta nível superior
- 0301010080 - Consulta médica especializada
- 0301060029 - Administração medicamentos via oral
- 0301060010 - Administração medicamentos atenção básica

⚠️ **Importante:** Lista precisa ser validada contra SIGTAP atual.

## Query de Validação

Para identificar todos os procedimentos dual no SIGTAP atual:

```python
def list_dual_procedures():
    """Lista todos os procedimentos que podem ser BPA-I E BPA-C"""
    registro_map = sigtap._get_procedimento_registro_map()
    
    dual_procs = []
    for proc, tipos in registro_map.items():
        if '01' in tipos and '02' in tipos:
            dual_procs.append(proc)
    
    return dual_procs
```

## Impacto Estimado

Se 80% dos procedimentos são dual:
- Antes: 1000 registros BPA-I → 1000 linhas bpa_individualizado
- Depois: 1000 registros BPA-I → 200 linhas bpa_consolidado (agregados) + 200 linhas bpa_individualizado

Benefícios:
- Menos linhas no banco
- Arquivo de exportação menor
- Processamento mais rápido pelo SIA/SUS
