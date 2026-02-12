# ⚠️ Pontos de Atenção e Riscos

## Riscos Identificados

### 1. Perda de Rastreabilidade
**Risco:** Ao converter BPA-I para BPA-C, perdemos dados do paciente individual.

**Mitigação:**
- Adicionar campos `_converted_from_bpai` e `_original_cnspac` nos registros convertidos
- Manter log de conversões em tabela separada (opcional)
- Campo `prd_org = 'BPC_CONV'` identifica origem

### 2. Agregação Incorreta
**Risco:** Procedimentos com mesma chave mas contextos diferentes sendo agregados.

**Mitigação:**
- Revisar se CID ou outros campos devem fazer parte da chave
- Testar com dados reais antes de produção
- Validar totais antes e depois da conversão

### 3. Inconsistência SIGTAP
**Risco:** Versão do SIGTAP diferente da competência pode classificar errado.

**Mitigação:**
- Sempre usar SIGTAP da mesma competência dos dados
- Validar se competência SIGTAP está carregada antes de converter
- Log de warning se usar SIGTAP de competência diferente

### 4. Performance
**Risco:** Consulta repetida ao SIGTAP pode ser lenta.

**Mitigação:**
- Cache do `registro_map` no início do processo
- Processar em batches se necessário
- Lazy loading do cache SIGTAP

### 5. Duplicação
**Risco:** Reprocessar mesma competência pode duplicar BPA-C.

**Mitigação:**
- Verificar se já existe BPA-C para mesma chave antes de inserir
- Opção de limpar BPA-C antes de reprocessar
- Usar UPSERT em vez de INSERT

---

## Validações Necessárias

### Antes da Conversão
- [ ] SIGTAP da competência está carregado?
- [ ] Existem dados para converter?
- [ ] Usuário tem permissão para o CNES?

### Durante a Conversão
- [ ] Procedimento existe no SIGTAP?
- [ ] Tipos de registro estão corretos?
- [ ] Idade calculada é válida (0-150)?

### Após a Conversão
- [ ] Total de quantidades bate? (Σ BPA-I = Σ BPA-C)
- [ ] Não houve perda de registros?
- [ ] BPA-C foi salvo corretamente?

---

## Casos Especiais

### 1. Procedimento com CID Obrigatório
Alguns procedimentos BPA-I exigem CID. No BPA-C não há CID.

**Decisão:** ⚠️ Verificar se isso impacta o faturamento. Se sim, talvez esses procedimentos devam ficar como BPA-I mesmo sendo dual.

### 2. Procedimento Recém-Adicionado ao SIGTAP
Procedimento pode existir nos dados mas não no SIGTAP carregado.

**Decisão:** Log de warning e manter como BPA-I (fallback seguro).

### 3. Quantidade Zero
Registro com quantidade = 0 após agregação.

**Decisão:** Não deveria acontecer, mas se acontecer, descartar com log.

### 4. Idade Inválida
Paciente sem data de nascimento ou idade inválida.

**Decisão:** Usar idade = '000' (todas as idades) como fallback.

---

## Compatibilidade com Sistema Atual

### Endpoints que NÃO devem ser afetados
- `GET /api/bpa-i/*` - Listagem de BPA-I
- `GET /api/bpa-c/*` - Listagem de BPA-C
- `POST /api/export/*` - Exportação de arquivos

### Endpoints que SERÃO afetados
- `POST /api/biserver/extract` - Comportamento muda se usar nova lógica
- `POST /api/biserver/save-extracted` - Precisa tratar novo formato

### Migração Gradual
1. Criar novo endpoint `/api/biserver/extract-and-convert` (não quebra nada)
2. Testar com competências novas
3. Quando estável, fazer o endpoint antigo chamar o novo

---

## Checklist de Testes

### Testes Unitários
- [ ] `_classify_and_convert_bpa()` com lista vazia
- [ ] `_classify_and_convert_bpa()` com procedimento dual
- [ ] `_classify_and_convert_bpa()` com procedimento apenas BPA-I
- [ ] `_classify_and_convert_bpa()` com procedimento apenas BPA-C
- [ ] `_classify_and_convert_bpa()` com procedimento desconhecido
- [ ] `_convert_record_to_bpac()` com todos os campos
- [ ] `_convert_record_to_bpac()` com campos faltando
- [ ] `_calculate_idade()` com datas válidas
- [ ] `_calculate_idade()` com datas inválidas
- [ ] `_aggregate_bpac_records()` com registros únicos
- [ ] `_aggregate_bpac_records()` com registros para agregar

### Testes de Integração
- [ ] Extração completa de uma competência
- [ ] Salvamento no banco
- [ ] Exportação do arquivo BPA-C
- [ ] Validação do arquivo gerado

### Testes de Regressão
- [ ] Fluxo antigo continua funcionando
- [ ] Exportações anteriores não são afetadas
- [ ] Relatórios existentes continuam corretos

---

## Métricas de Monitoramento

Após deploy, monitorar:
- Tempo médio de conversão por competência
- % de registros convertidos vs mantidos como BPA-I
- Erros de classificação
- Uso de memória durante processo
