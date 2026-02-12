"""
Investiga campo SEXO - verifica formato que vem da API
"""
import sys
sys.path.insert(0, '.')

from services.biserver_client import BiServerAPIClient

client = BiServerAPIClient()

print("=" * 80)
print("INVESTIGACAO: CAMPO SEXO")
print("=" * 80)

try:
    data = client.get_bpa_data(cnes="2755289", competencia="2025-12", page=0)
    
    if isinstance(data, dict):
        registros = data.get('registros', [])
        print(f"\nTotal registros: {len(registros)}")
        
        if registros:
            # Analisa valores de sexo
            sexos = {}
            for r in registros[:100]:  # Amostra de 100
                sexo = r.get('prd_sexo')
                sexos[sexo] = sexos.get(sexo, 0) + 1
            
            print("\nVALORES DE SEXO ENCONTRADOS (amostra 100):")
            for sexo, count in sorted(sexos.items()):
                print(f"  {repr(sexo)}: {count} registros")
            
            # Mostra exemplos
            print("\nEXEMPLOS (primeiros 10):")
            for i, r in enumerate(registros[:10], 1):
                print(f"  #{i}: sexo={repr(r.get('prd_sexo'))}, nome={r.get('prd_nmpac')}")

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
