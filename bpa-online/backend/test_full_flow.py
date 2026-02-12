"""
Teste do fluxo completo: Extração → Cache → Salvamento
"""
from services.biserver_client import get_extraction_service
from database import BPADatabase
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Usa o singleton
service = get_extraction_service()

print('\n===== 1. EXTRAINDO E SEPARANDO =====')
result = service.extract_and_separate_bpa(
    cnes='2492555',
    competencia='202601',
    limit=100,
    offset=0
)

print(f'✅ Success: {result["success"]}')
print(f'📊 Stats: BPA-I={result["stats"]["bpa_i"]}, BPA-C={result["stats"]["bpa_c"]}, Removidos={result["stats"]["removed"]}')
print(f'💾 Cache Keys: {result["cache_keys"]}')

# Verifica o cache
print('\n===== 2. VERIFICANDO CACHE =====')
cache_key_i = result['cache_keys']['bpa_i']
cached_data = service.get_cached_data(cache_key_i)
print(f'✅ Dados no cache: {len(cached_data) if cached_data else 0} registros')

if cached_data and len(cached_data) > 0:
    print(f'\n📋 Primeiro registro:')
    for key, value in list(cached_data[0].items())[:15]:
        print(f'   {key}: {value}')
    
    # Testa salvamento
    print('\n===== 3. SALVANDO NO BANCO =====')
    db = BPADatabase()
    
    # Salva primeiro registro como teste
    test_record = cached_data[0]
    bpa_data = {
        "prd_uid": "2492555",
        "prd_cmp": "202601",
        "prd_flh": 1,
        "prd_seq": 1,
        "prd_cnsmed": str(test_record.get("prd_cnsmed", "")),
        "prd_cbo": str(test_record.get("prd_cbo", "")),
        "prd_ine": "",
        "prd_cnspac": str(test_record.get("prd_cnspac", "")),
        "prd_cpf_pcnte": "",
        "prd_nmpac": test_record.get("prd_nmpac", ""),
        "prd_dtnasc": test_record.get("prd_dtnasc", ""),
        "prd_sexo": str(test_record.get("prd_sexo", "M")),
        "prd_raca": str(test_record.get("prd_raca", "99")).zfill(2),
        "prd_idade": str(test_record.get("prd_idade", "")),
        "prd_ibge": "",
        "prd_cep_pcnte": str(test_record.get("prd_cep_pcnte", "")),
        "prd_lograd_pcnte": str(test_record.get("prd_lograd_pcnte", "")),
        "prd_end_pcnte": str(test_record.get("prd_end_pcnte", "")),
        "prd_num_pcnte": str(test_record.get("prd_num_pcnte", "")),
        "prd_compl_pcnte": str(test_record.get("prd_compl_pcnte", "")),
        "prd_bairro_pcnte": "",
        "prd_tel_pcnte": str(test_record.get("prd_tel_pcnte", "")),
        "prd_ddtel_pcnte": str(test_record.get("prd_ddtel_pcnte", "")),
        "prd_email_pcnte": str(test_record.get("prd_email_pcnte", "") or ""),
        "prd_dtaten": test_record.get("prd_dtaten", ""),
        "prd_pa": test_record.get("prd_pa", ""),
        "prd_qt_p": test_record.get("prd_qt_p", 1),
        "prd_cid": test_record.get("prd_cid", ""),
        "prd_caten": "02",  # UPA
        "prd_naut": "",
        "prd_servico": "",
        "prd_classificacao": "",
        "prd_cnpj": "",
        "prd_nac": "010",
        "prd_etnia": "",
        "prd_eqp_area": "",
        "prd_eqp_seq": "",
        "prd_mvm": "202601",
        "prd_org": "BPI",
    }
    
    try:
        result_id = db.save_bpa_individualizado(bpa_data)
        print(f'✅ Registro salvo com ID: {result_id}')
    except Exception as e:
        print(f'❌ Erro ao salvar: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ Nenhum dado no cache!')
