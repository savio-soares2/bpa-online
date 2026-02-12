"""
Teste rápido da extração BiServer com secret correta
"""
from services.biserver_client import BiServerExtractionService
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Cria serviço de extração SEM validação SIGTAP (para teste rápido)
print("Criando serviço...")
service = BiServerExtractionService(enable_sigtap_validation=False)

# Testa BPA-I
print('\n===== TESTANDO BPA-I =====')
result = service.extract_bpa_individualizado(
    cnes='2492555',
    competencia='202512',
    limit=10,
    offset=0
)

print(f'\n✅ Success: {result.success}')
print(f'✅ Total: {result.total_records}')
print(f'✅ Message: {result.message}')

if result.records:
    print(f'\n✅ Registros retornados: {len(result.records)}')
    print(f'✅ Primeiro registro keys: {list(result.records[0].keys())[:15]}')
    print(f'\n✅ Primeiro registro completo:')
    for key, value in list(result.records[0].items())[:10]:
        print(f'   {key}: {value}')
else:
    print('❌ Nenhum registro retornado!')
    if result.errors:
        print(f'❌ Erros: {result.errors}')
