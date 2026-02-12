"""Verifica quando os registros foram criados"""
import psycopg2

conn = psycopg2.connect('postgresql://bpa_user:bpa_secret_2024@localhost:5433/bpa_online')
cur = conn.cursor()

# Quando foram criados os registros da UPA Norte 202512
cur.execute("""
    SELECT MIN(created_at), MAX(created_at) 
    FROM bpa_individualizado 
    WHERE prd_uid = '2755289' AND prd_cmp = '202512'
""")
result = cur.fetchone()
print(f"=== UPA NORTE 202512 - DATAS DE CRIAÇÃO ===")
print(f"Primeiro registro: {result[0]}")
print(f"Último registro: {result[1]}")

# Verifica se há registros COM bairro em competências anteriores
cur.execute("""
    SELECT prd_cmp, 
           COUNT(*) as total,
           SUM(CASE WHEN prd_bairro_pcnte != '' AND prd_bairro_pcnte IS NOT NULL THEN 1 ELSE 0 END) as com_bairro
    FROM bpa_individualizado 
    WHERE prd_uid = '2755289'
    GROUP BY prd_cmp
    ORDER BY prd_cmp DESC
""")
print(f"\n=== HISTÓRICO POR COMPETÊNCIA ===")
for cmp, total, com_bairro in cur.fetchall():
    pct = (com_bairro/total*100) if total > 0 else 0
    print(f"  {cmp}: {total} registros, {com_bairro} com bairro ({pct:.1f}%)")

conn.close()
