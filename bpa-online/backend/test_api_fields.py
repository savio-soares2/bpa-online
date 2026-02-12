"""
Script para testar quais campos a API do BiServer retorna
"""
from services.biserver_client import BiServerAPIClient
import json

def main():
    print("Conectando à API do BiServer...")
    client = BiServerAPIClient()
    
    print("Buscando dados do CAPS AD (6061478) - Competência 2025-12...")
    result = client.get_bpa_data(
        cnes='6061478', 
        competencia='2025-12', 
        page=0, 
        timeout=120
    )
    
    # Tenta encontrar os registros
    registros = result.get('registros', result.get('data', result.get('records', [])))
    
    print(f"\n{'='*60}")
    print(f"RESULTADO DA API")
    print(f"{'='*60}")
    
    if registros:
        print(f"\nTotal de registros: {len(registros)}")
        print(f"Total de campos por registro: {len(registros[0].keys())}")
        
        print(f"\n{'='*60}")
        print("CAMPOS DISPONÍVEIS NA API:")
        print(f"{'='*60}")
        
        exemplo = registros[0]
        for key in sorted(exemplo.keys()):
            valor = exemplo[key]
            tipo = type(valor).__name__
            print(f"  {key:<30} = {str(valor)[:50]:<50} ({tipo})")
        
        # Salva exemplo completo em arquivo
        with open('api_response_example.json', 'w', encoding='utf-8') as f:
            json.dump({
                "total_registros": len(registros),
                "campos": list(exemplo.keys()),
                "exemplo_registro": exemplo
            }, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nExemplo salvo em: api_response_example.json")
        
    else:
        print("\nNenhum registro encontrado!")
        print("\nResposta completa da API:")
        print(json.dumps(result, indent=2, default=str)[:3000])

if __name__ == "__main__":
    main()
