"""
Teste de debugging da extração BiServer
"""
import requests
import jwt
from time import time
import json

# Configuração
API_URL = 'https://biserver.rb.adm.br'
SECRET_KEY = 'qvrSub&0i?#/NJ^h[UO$!7,[TnXyqIGCjI=XqFICZs&gW2V6a'
KID = 'bpaclient'

print("=" * 80)
print("DEBUG: TESTE DIRETO DA API BISERVER")
print("=" * 80)
print()

# 1. Gerar token JWT
print("1. Gerando token JWT...")
payload = {
    'iss': KID,
    'iat': int(time()),
    'exp': int(time()) + 3600
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256', headers={'kid': KID})
print(f"✓ Token gerado: {token[:50]}...")
print()

# 2. Testar endpoint /api/bpa/data
print("2. Testando endpoint /api/bpa/data")
print("-" * 80)

headers = {'Authorization': f'Bearer {token}'}
params = {
    'cnes': '2492555',
    'competencia': '2025-12',
    'page': 0,  # API usa 'page' não 'offset'
    'limit': 10
}

print(f"URL: {API_URL}/api/bpa/data")
print(f"Params: {params}")
print()

try:
    response = requests.get(
        f"{API_URL}/api/bpa/data",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✓ RESPOSTA RECEBIDA COM SUCESSO!")
        print()
        print("Estrutura da resposta:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
        print()
        
        # Analisar estrutura
        print("=" * 80)
        print("ANÁLISE DA RESPOSTA:")
        print("=" * 80)
        print(f"Tipo: {type(data)}")
        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        if isinstance(data, dict):
            if 'total_registros' in data:
                print(f"Total de registros: {data['total_registros']}")
            if 'data' in data:
                print(f"Campo 'data': {type(data['data'])}, tamanho: {len(data['data']) if isinstance(data['data'], list) else 'N/A'}")
            if 'registros' in data:
                print(f"Campo 'registros': {type(data['registros'])}, tamanho: {len(data['registros']) if isinstance(data['registros'], list) else 'N/A'}")
            if 'records' in data:
                print(f"Campo 'records': {type(data['records'])}, tamanho: {len(data['records']) if isinstance(data['records'], list) else 'N/A'}")
        
    else:
        print(f"❌ ERRO: {response.status_code}")
        print(f"Resposta: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ EXCEÇÃO: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("FIM DO TESTE")
print("=" * 80)
