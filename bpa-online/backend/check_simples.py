"""
Investiga campos vazios - versão simplificada
"""
import sys
sys.path.insert(0, '.')

from services.biserver_client import BiServerAPIClient
from database import get_connection

output = []
output.append("=" * 80)
output.append("INVESTIGACAO: CAMPOS VAZIOS")
output.append("=" * 80)

client = BiServerAPIClient()

campos = ['prd_cnpj', 'prd_servico', 'prd_classificacao', 'prd_cid', 'prd_naut', 'prd_bairro_pcnte']

try:
    # API
    data = client.get_bpa_data(cnes="2755289", competencia="2025-12", page=0)
    registros = data.get('registros', [])[:100]
    
    output.append("\n[API] Campos na API BiServer (100 registros):")
    for campo in campos:
        com_dados = sum(1 for r in registros if r.get(campo) and str(r.get(campo)).strip())
        output.append(f"  {campo:25} {com_dados:3}/100")
    
    # DB
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT {', '.join(campos)}
            FROM bpa_individualizado
            ORDER BY id DESC
            LIMIT 100
        """)
        registros_db = cursor.fetchall()
        
        output.append("\n[BANCO] Campos no Postgres (100 registros):")
        for i, campo in enumerate(campos):
            com_dados = sum(1 for row in registros_db if row[i] and str(row[i]).strip())
            output.append(f"  {campo:25} {com_dados:3}/100")
        cursor.close()

except Exception as e:
    output.append(f"\nErro: {e}")

# Salva resultado
with open('resultado_investigacao.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('\n'.join(output))
print("\nResultado salvo em: resultado_investigacao.txt")
