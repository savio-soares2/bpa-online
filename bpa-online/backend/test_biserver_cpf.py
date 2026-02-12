"""Teste da API BiServer - verificar campos disponíveis incluindo CPF"""
import sys
sys.path.insert(0, '.')

from services.biserver_client import BiServerAPIClient

client = BiServerAPIClient()

print("="*80)
print("TESTE API BISERVER - VERIFICANDO CAMPOS DISPONÍVEIS")
print("="*80)

# Testa conexão
print("\n[1] Testando conexão...")
try:
    result = client.test_connection()
    print(f"Conexão: {result}")
except Exception as e:
    print(f"Erro: {e}")

# Busca dados de BPA
print("\n[2] Buscando dados de BPA...")
try:
    # Usa competência e CNES conhecidos
    data = client.get_bpa_data(cnes="2755289", competencia="2025-12", page=0)
    
    print(f"Tipo resposta: {type(data)}")
    print(f"Chaves: {data.keys() if isinstance(data, dict) else 'N/A'}")
    
    if isinstance(data, dict):
        registros = data.get('registros', [])
        print(f"Total registros: {len(registros)}")
        
        if registros:
            print("\n[3] CAMPOS DO PRIMEIRO REGISTRO:")
            print("-"*50)
            primeiro = registros[0]
            for key, value in sorted(primeiro.items()):
                print(f"  {key}: {repr(value)[:60]}")
            
            # Procura campos relacionados a CPF
            print("\n[4] CAMPOS QUE PODEM CONTER CPF:")
            print("-"*50)
            cpf_fields = [k for k in primeiro.keys() if 'cpf' in k.lower()]
            if cpf_fields:
                for field in cpf_fields:
                    print(f"  ✅ {field}: {primeiro.get(field)}")
            else:
                print("  ❌ Nenhum campo com 'cpf' no nome")
            
            # Verifica campos de identificação do paciente
            print("\n[5] CAMPOS DE IDENTIFICAÇÃO DO PACIENTE:")
            print("-"*50)
            id_fields = ['prd_cnspac', 'prd_cpf_pcnte', 'cpf', 'cpf_paciente', 
                        'prd_nmpac', 'prd_dtnasc', 'cns_paciente', 'documento']
            for field in id_fields:
                if field in primeiro:
                    print(f"  {field}: {primeiro.get(field)}")
            
            # Amostra de 5 registros sem CNS
            print("\n[6] REGISTROS SEM CNS (primeiros 5):")
            print("-"*50)
            sem_cns = [r for r in registros if not (r.get('prd_cnspac') or '').strip()][:5]
            for i, r in enumerate(sem_cns, 1):
                print(f"\n  #{i}")
                print(f"    Nome: {r.get('prd_nmpac')}")
                print(f"    CNS: '{r.get('prd_cnspac')}'")
                print(f"    CPF (se existir): '{r.get('prd_cpf_pcnte', r.get('cpf', 'N/A'))}'")
                # Mostra todos os campos que podem ter CPF
                for k, v in r.items():
                    if 'cpf' in k.lower() or 'doc' in k.lower():
                        print(f"    {k}: '{v}'")

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
