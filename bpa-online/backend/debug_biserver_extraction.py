
import sys
import json
import logging

# Adiciona diretório backend
sys.path.append(r"c:\Users\60612427358\Documents\bpa-online\bpa-online\backend")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services.biserver_client import BiServerAPIClient

def test_extraction():
    print("=== TESTE CONEXÃO BISERVER ===")
    
    # 1. Inicializar cliente (usa vars de ambiente .env se existirem, ou defaults)
    client = BiServerAPIClient()
    
    print(f"URL: {client.base_url}")
    
    # 2. Testar conexão básica
    try:
        status = client.test_connection()
        print(f"Status Conexão: {status}")
    except Exception as e:
        print(f"Erro Conexão: {e}")
        return

    # 3. Tentar extrair dados de Dezembro/2025 para o CEO
    # CNES CEO: 2492547
    cnes = "2492547"
    comp = "2025-12" # API exige formato com hífen
    page = 0
    
    print(f"\nSolicitando dados -> CNES: {cnes}, Comp: {comp}, Page: {page}")
    
    try:
        # Chama endpoint direto
        response = client.get_bpa_data(cnes=cnes, competencia=comp, page=page)
        
        # Analisa responsta
        # Estrutura esperada: {'content': [...], 'totalPages': X, 'totalElements': Y} ou similar
        # O código biserver_client.py não mostrou a estrutura exata do return do get_bpa_data, mas é o json da response.
        
        print("Resposta recebida!")
        print(f"Keys na resposta: {list(response.keys())}")
        
        # Tenta identificar lista de registros
        records = []
        if 'content' in response:
            records = response['content']
        elif 'data' in response:
            records = response['data']
        elif isinstance(response, list):
            records = response
            
        print(f"Total registros na página: {len(records)}")
        
        if records:
            print("Exemplo de registro:")
            print(json.dumps(records[0], indent=2, default=str))
            
            # Checar procedimetnos
            procs = [r.get('procedimento', r.get('prd_pa')) for r in records]
            print(f"Procedimentos encontrados: {procs[:10]}...")
            
    except Exception as e:
        print(f"Erro na extração: {e}")

if __name__ == "__main__":
    test_extraction()
