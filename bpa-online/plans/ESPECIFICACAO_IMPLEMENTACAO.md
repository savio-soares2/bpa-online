# 🔧 Especificação de Implementação: Conversão BPA-I → BPA-C

## Arquivo: `biserver_client.py`

### Modificação 1: Adicionar método `_classify_and_convert_bpa()`

**Localização:** Após o método `_separate_bpa_by_sigtap()` (linha ~400)

```python
def _classify_and_convert_bpa(self, records: List[Dict], cnes: str = None) -> Dict[str, List[Dict]]:
    """
    Classifica registros e converte para BPA-C quando procedimento é dual (01+02).
    
    REGRA PRINCIPAL:
    - Se procedimento tem tipo_registro {01, 02}: Converte para BPA-C
    - Se procedimento tem apenas {02}: Mantém como BPA-I
    - Se procedimento tem apenas {01}: BPA-C direto
    
    Args:
        records: Lista de registros extraídos da API
        cnes: Código CNES (usado para logging)
        
    Returns:
        Dict com 'bpa_i', 'bpa_c' e estatísticas
    """
    if not self.enable_sigtap_validation or not records:
        return {
            'bpa_i': records,
            'bpa_c': [],
            'stats': {
                'total': len(records),
                'bpa_i': len(records),
                'bpa_c': 0,
                'converted': 0,
                'removed_sem_registro': 0
            }
        }
    
    # Mapa de procedimento -> tipos de registro permitidos
    registro_map = self.sigtap._get_procedimento_registro_map()
    
    bpa_i_records = []
    bpa_c_raw = []  # Antes de agregar
    removed_sem_registro = 0
    converted_count = 0
    
    for rec in records:
        proc = rec.get('prd_pa', rec.get('procedimento', ''))
        tipos = registro_map.get(proc, set())
        
        has_bpa_c = '01' in tipos
        has_bpa_i = '02' in tipos
        
        if has_bpa_c and has_bpa_i:
            # DUAL: Converte para BPA-C (PREFERÊNCIA)
            converted = self._convert_record_to_bpac(rec)
            bpa_c_raw.append(converted)
            converted_count += 1
        elif has_bpa_i:
            # APENAS BPA-I: Mantém
            bpa_i_records.append(rec)
        elif has_bpa_c:
            # APENAS BPA-C: Converte direto
            converted = self._convert_record_to_bpac(rec)
            bpa_c_raw.append(converted)
        else:
            # Não é BPA (e-SUS, RAAS, etc)
            removed_sem_registro += 1
    
    # Agrega registros BPA-C por chave
    bpa_c_aggregated = self._aggregate_bpac_records(bpa_c_raw)
    
    logger.info(f"📊 Classificação: {len(bpa_i_records)} BPA-I, {len(bpa_c_aggregated)} BPA-C agregados")
    logger.info(f"   🔄 Convertidos (dual): {converted_count}")
    if removed_sem_registro > 0:
        logger.info(f"   ⚠ {removed_sem_registro} sem registro BPA (e-SUS, RAAS, etc)")
    
    return {
        'bpa_i': bpa_i_records,
        'bpa_c': bpa_c_aggregated,
        'stats': {
            'total': len(records),
            'bpa_i': len(bpa_i_records),
            'bpa_c': len(bpa_c_aggregated),
            'bpa_c_before_aggregation': len(bpa_c_raw),
            'converted': converted_count,
            'removed_sem_registro': removed_sem_registro
        }
    }
```

### Modificação 2: Adicionar método `_convert_record_to_bpac()`

```python
def _convert_record_to_bpac(self, record: Dict) -> Dict:
    """
    Converte um registro do formato BPA-I para formato BPA-C.
    
    Remove campos exclusivos de BPA-I (dados do paciente).
    Mantém campos comuns (CNES, competência, procedimento, CBO).
    """
    # Calcula idade se não existir
    idade = record.get('prd_idade', '')
    if not idade and record.get('prd_dtnasc'):
        idade = self._calculate_idade(
            record.get('prd_dtnasc'),
            record.get('prd_dtaten', record.get('prd_cmp', ''))[:6]
        )
    
    return {
        'prd_uid': record.get('prd_uid', ''),
        'prd_cmp': record.get('prd_cmp', ''),
        'prd_cnsmed': record.get('prd_cnsmed', ''),
        'prd_cbo': record.get('prd_cbo', ''),
        'prd_pa': record.get('prd_pa', record.get('procedimento', '')),
        'prd_idade': idade or '000',
        'prd_qt_p': record.get('prd_qt_p', record.get('quantidade', 1)),
        'prd_org': 'BPC_CONV',  # Origem: Conversão de BPA-I
        'prd_exportado': False,
        # Metadata para rastreabilidade
        '_converted_from_bpai': True,
        '_original_cnspac': record.get('prd_cnspac', ''),
    }


def _calculate_idade(self, data_nascimento: str, data_referencia: str) -> str:
    """
    Calcula idade em anos a partir da data de nascimento.
    
    Args:
        data_nascimento: Formato YYYYMMDD ou YYYY-MM-DD
        data_referencia: Formato YYYYMM (competência)
        
    Returns:
        Idade como string de 3 dígitos (ex: "039" para 39 anos)
    """
    try:
        from datetime import datetime
        
        # Normaliza data de nascimento
        dn = data_nascimento.replace('-', '')
        if len(dn) < 8:
            return '000'
        
        ano_nasc = int(dn[:4])
        mes_nasc = int(dn[4:6])
        dia_nasc = int(dn[6:8])
        
        # Normaliza data de referência
        dr = data_referencia.replace('-', '')[:6]
        ano_ref = int(dr[:4])
        mes_ref = int(dr[4:6])
        
        # Calcula idade
        idade = ano_ref - ano_nasc
        if mes_ref < mes_nasc:
            idade -= 1
        
        # Retorna com 3 dígitos
        return f"{max(0, min(idade, 999)):03d}"
        
    except Exception:
        return '000'
```

### Modificação 3: Adicionar método `_aggregate_bpac_records()`

```python
def _aggregate_bpac_records(self, records: List[Dict]) -> List[Dict]:
    """
    Agrega registros BPA-C por chave única.
    
    Chave de agregação: CNES + CMP + CBO + PA + IDADE
    Soma: QT_P (quantidade)
    
    Args:
        records: Lista de registros BPA-C (não agregados)
        
    Returns:
        Lista de registros agregados
    """
    if not records:
        return []
    
    groups = {}
    
    for rec in records:
        # Chave de agrupamento
        key = (
            rec.get('prd_uid', ''),
            rec.get('prd_cmp', ''),
            rec.get('prd_cbo', ''),
            rec.get('prd_pa', ''),
            rec.get('prd_idade', '000')
        )
        
        if key not in groups:
            groups[key] = rec.copy()
            groups[key]['prd_qt_p'] = 0
            groups[key]['_aggregation_count'] = 0
        
        groups[key]['prd_qt_p'] += rec.get('prd_qt_p', 1)
        groups[key]['_aggregation_count'] += 1
    
    return list(groups.values())
```

### Modificação 4: Atualizar `extract_and_separate_bpa()`

Substituir a chamada de `_separate_bpa_by_sigtap()` por `_classify_and_convert_bpa()`:

```python
# ANTES (linha ~570):
separated = self._separate_bpa_by_sigtap(records, cnes=cnes)

# DEPOIS:
separated = self._classify_and_convert_bpa(records, cnes=cnes)
```

---

## Arquivo: `sigtap_filter_service.py`

### Adicionar método `get_dual_procedures()`

**Localização:** Após `_get_procedimento_registro_map()` (~linha 60)

```python
def get_dual_procedures(self, competencia: str = None) -> Set[str]:
    """
    Retorna conjunto de procedimentos que podem ser BPA-I E BPA-C
    
    Returns:
        Set de códigos de procedimentos
    """
    registro_map = self._get_procedimento_registro_map(competencia)
    
    dual = set()
    for proc, tipos in registro_map.items():
        if '01' in tipos and '02' in tipos:
            dual.add(proc)
    
    return dual


def is_dual_procedure(self, procedimento: str, competencia: str = None) -> bool:
    """
    Verifica se um procedimento pode ser tanto BPA-I quanto BPA-C
    """
    registro_map = self._get_procedimento_registro_map(competencia)
    tipos = registro_map.get(procedimento, set())
    return '01' in tipos and '02' in tipos


def get_procedimento_info(self, procedimento: str, competencia: str = None) -> Dict:
    """
    Retorna informações sobre tipos de registro de um procedimento
    
    Returns:
        {
            'codigo': str,
            'tipos': set,
            'bpa_i': bool,
            'bpa_c': bool,
            'dual': bool,
            'preferencia': 'BPA-C' | 'BPA-I' | None
        }
    """
    registro_map = self._get_procedimento_registro_map(competencia)
    tipos = registro_map.get(procedimento, set())
    
    has_i = '02' in tipos
    has_c = '01' in tipos
    is_dual = has_i and has_c
    
    preferencia = None
    if is_dual:
        preferencia = 'BPA-C'  # Regra de negócio: dual prefere BPA-C
    elif has_c:
        preferencia = 'BPA-C'
    elif has_i:
        preferencia = 'BPA-I'
    
    return {
        'codigo': procedimento,
        'tipos': tipos,
        'bpa_i': has_i,
        'bpa_c': has_c,
        'dual': is_dual,
        'preferencia': preferencia
    }
```

---

## Arquivo: `database.py`

### Adicionar método `save_bpa_consolidado_batch()`

```python
def save_bpa_consolidado_batch(self, records: List[Dict], cnes: str, competencia: str) -> Dict:
    """
    Salva múltiplos registros BPA-C, agregando se necessário.
    
    Args:
        records: Lista de registros BPA-C
        cnes: Código CNES
        competencia: Competência YYYYMM
        
    Returns:
        Dict com estatísticas do salvamento
    """
    if not records:
        return {'success': True, 'saved': 0, 'errors': []}
    
    saved = 0
    errors = []
    
    try:
        cursor = self.conn.cursor()
        
        for rec in records:
            try:
                cursor.execute("""
                    INSERT INTO bpa_consolidado (
                        prd_uid, prd_cmp, prd_flh,
                        prd_cnsmed, prd_cbo, prd_pa,
                        prd_qt_p, prd_idade, prd_org,
                        prd_exportado
                    ) VALUES (
                        %s, %s, 1,
                        %s, %s, %s,
                        %s, %s, %s,
                        FALSE
                    )
                """, (
                    rec.get('prd_uid', cnes),
                    rec.get('prd_cmp', competencia),
                    rec.get('prd_cnsmed', ''),
                    rec.get('prd_cbo', ''),
                    rec.get('prd_pa', ''),
                    rec.get('prd_qt_p', 1),
                    rec.get('prd_idade', '000'),
                    rec.get('prd_org', 'BPC_CONV')
                ))
                saved += 1
            except Exception as e:
                errors.append(f"Erro ao salvar registro: {e}")
        
        self.conn.commit()
        
        return {
            'success': True,
            'saved': saved,
            'errors': errors
        }
        
    except Exception as e:
        self.conn.rollback()
        return {
            'success': False,
            'saved': 0,
            'errors': [str(e)]
        }
```

---

## Arquivo: `main.py`

### Adicionar endpoint `/api/biserver/extract-and-convert`

```python
@app.post("/api/biserver/extract-and-convert")
async def extract_and_convert_bpa(
    cnes: str = Query(...),
    competencia: str = Query(...),
    save_immediately: bool = Query(True),
    user: dict = Depends(get_current_user)
):
    """
    Extrai dados do BiServer e converte procedimentos dual para BPA-C.
    
    - Procedimentos dual (BPA-I + BPA-C): Convertidos para BPA-C
    - Procedimentos apenas BPA-I: Mantidos como BPA-I
    - Procedimentos apenas BPA-C: Salvos como BPA-C
    """
    try:
        from services.biserver_client import get_extraction_service
        
        service = get_extraction_service()
        result = service.extract_and_separate_bpa(
            cnes=cnes,
            competencia=competencia
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Erro na extração'))
        
        response = {
            'success': True,
            'stats': result['stats'],
            'message': result['message']
        }
        
        if save_immediately:
            # Salva BPA-I
            if result['bpa_i']:
                for rec in result['bpa_i']:
                    db.save_bpa_individualizado(rec)
                response['bpa_i_saved'] = len(result['bpa_i'])
            
            # Salva BPA-C
            if result['bpa_c']:
                save_result = db.save_bpa_consolidado_batch(
                    result['bpa_c'], cnes, competencia
                )
                response['bpa_c_saved'] = save_result['saved']
                if save_result['errors']:
                    response['bpa_c_errors'] = save_result['errors']
        else:
            # Retorna dados para cache
            cache_key = f"converted_{cnes}_{competencia}"
            response['cache_key'] = cache_key
            response['preview'] = {
                'bpa_i_count': len(result['bpa_i']),
                'bpa_c_count': len(result['bpa_c'])
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Erro em extract-and-convert: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Adicionar endpoint `/api/procedimento/info`

```python
@app.get("/api/procedimento/info/{codigo}")
async def get_procedimento_info(
    codigo: str,
    user: dict = Depends(get_current_user)
):
    """
    Retorna informações sobre tipos de registro de um procedimento
    """
    from services.sigtap_filter_service import get_sigtap_filter_service
    
    sigtap = get_sigtap_filter_service()
    info = sigtap.get_procedimento_info(codigo)
    
    return {
        'success': True,
        'procedimento': info
    }
```

---

## Ordem de Implementação

1. **sigtap_filter_service.py** - Novos métodos de consulta
2. **biserver_client.py** - Lógica de classificação e conversão
3. **database.py** - Método de salvamento em lote
4. **main.py** - Novos endpoints
5. **Testes** - Validação completa
