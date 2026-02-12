"""
Investiga campos vazios - compara API BiServer vs Banco vs Exportador
"""
import sys
sys.path.insert(0, '.')

from services.biserver_client import BiServerAPIClient
from database import get_connection

print("=" * 80)
print("INVESTIGACAO: CAMPOS VAZIOS NO EXPORTADOR")
print("=" * 80)

client = BiServerAPIClient()

# Campos a investigar
campos_investigar = {
    'prd_cnpj': 'CNPJ',
    'prd_servico': 'Serviço',
    'prd_classificacao': 'Classificação',
    'prd_cid': 'CID',
    'prd_naut': 'Nº Autorização',
    'prd_ibge': 'IBGE',
    'prd_ine': 'INE',
    'prd_bairro_pcnte': 'Bairro'
}

try:
    # 1. Busca da API
    print("\n[1] BUSCANDO DADOS DA API BISERVER...")
    data = client.get_bpa_data(cnes="2755289", competencia="2025-12", page=0)
    
    if isinstance(data, dict):
        registros = data.get('registros', [])
        print(f"Total registros API: {len(registros)}\n")
        
        if registros:
            # Analisa campos na API
            print("=" * 80)
            print("ANÁLISE DOS CAMPOS NA API (amostra de 100)")
            print("=" * 80)
            
            stats_api = {}
            for campo, nome in campos_investigar.items():
                com_dados = 0
                exemplos = []
                
                for r in registros[:100]:
                    valor = r.get(campo)
                    if valor and str(valor).strip() and str(valor).strip() != '0':
                        com_dados += 1
                        if len(exemplos) < 3:
                            exemplos.append(str(valor)[:30])
                
                stats_api[campo] = {
                    'com_dados': com_dados,
                    'sem_dados': 100 - com_dados,
                    'exemplos': exemplos
                }
                
                status = "✅" if com_dados > 0 else "❌"
                print(f"{status} {nome:20} - Com dados: {com_dados:3}/100")
                if exemplos:
                    print(f"   Exemplos: {', '.join(exemplos[:2])}")
    
    # 2. Verifica no Banco Postgres
    print("\n" + "=" * 80)
    print("ANÁLISE DOS CAMPOS NO BANCO POSTGRES")
    print("=" * 80)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Pega amostra de registros
        cursor.execute("""
            SELECT prd_cnpj, prd_servico, prd_classificacao, prd_cid, 
                   prd_naut, prd_ibge, prd_ine, prd_bairro_pcnte
            FROM bpa_individualizado
            ORDER BY id DESC
            LIMIT 100
        """)
        
        registros_db = cursor.fetchall()
        print(f"Total registros DB: {len(registros_db)}\n")
        
        campos_db = ['prd_cnpj', 'prd_servico', 'prd_classificacao', 'prd_cid', 
                     'prd_naut', 'prd_ibge', 'prd_ine', 'prd_bairro_pcnte']
        
        for i, campo in enumerate(campos_db):
            com_dados = 0
            exemplos = []
            
            for row in registros_db:
                valor = row[i]
                if valor and str(valor).strip():
                    com_dados += 1
                    if len(exemplos) < 3:
                        exemplos.append(str(valor)[:30])
            
            nome = campos_investigar.get(campo, campo)
            status = "✅" if com_dados > 0 else "❌"
            print(f"{status} {nome:20} - Com dados: {com_dados:3}/100")
            if exemplos:
                print(f"   Exemplos: {', '.join(exemplos[:2])}")
        
        cursor.close()
    
    # 3. Comparação
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO")
    print("=" * 80)
    
    print("\nSe API tem dados mas DB não tem:")
    print("  → Problema no mapeamento (main.py)")
    print("\nSe DB tem dados mas exportador não:")
    print("  → Problema no exporter.py")
    print("\nSe API não tem dados:")
    print("  → Campo realmente vazio no BiServer")

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
