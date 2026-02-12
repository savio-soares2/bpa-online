"""
Teste do novo método de separação automática BPA-I / BPA-C
"""
from services.biserver_client import BiServerExtractionService
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Cria serviço com validação SIGTAP
service = BiServerExtractionService(enable_sigtap_validation=True)

# Extrai e separa automaticamente
print('\n===== TESTANDO SEPARAÇÃO AUTOMÁTICA =====\n')
result = service.extract_and_separate_bpa(
    cnes='2492555',
    competencia='202512',
    limit=1000,
    offset=0
)

if result['success']:
    stats = result['stats']
    print(f'\n✅ SUCESSO!')
    print(f'\n📊 ESTATÍSTICAS:')
    print(f'   Total extraído da API: {stats["total"]}')
    print(f'   BPA-I (Individualizado): {stats["bpa_i"]} registros')
    print(f'   BPA-C (Consolidado): {stats["bpa_c"]} registros')
    print(f'   Removidos (inválidos): {stats["removed"]} registros')
    
    print(f'\n💾 Cache Keys:')
    print(f'   BPA-I: {result["cache_keys"]["bpa_i"]}')
    print(f'   BPA-C: {result["cache_keys"]["bpa_c"]}')
    
    # Mostra alguns procedimentos de cada tipo
    if result['bpa_i']:
        print(f'\n📋 Exemplos BPA-I:')
        for rec in result['bpa_i'][:3]:
            print(f'   Procedimento: {rec.get("prd_pa")} | CBO: {rec.get("prd_cbo")}')
    
    if result['bpa_c']:
        print(f'\n📋 Exemplos BPA-C:')
        for rec in result['bpa_c'][:3]:
            print(f'   Procedimento: {rec.get("prd_pa")} | CBO: {rec.get("prd_cbo")}')
else:
    print(f'❌ ERRO: {result.get("error")}')
