"""
Script para verificar se registros BPA-I têm CNS e/ou CPF
"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='bpa_online',
    user='bpa_user',
    password='bpa_password'
)
cur = conn.cursor()

# Verifica total e quantos têm CNS/CPF
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN prd_cnspac IS NOT NULL AND prd_cnspac != '' THEN 1 END) as com_cns,
        COUNT(CASE WHEN prd_cpf_pcnte IS NOT NULL AND prd_cpf_pcnte != '' THEN 1 END) as com_cpf,
        COUNT(CASE WHEN (prd_cnspac IS NULL OR prd_cnspac = '') AND (prd_cpf_pcnte IS NULL OR prd_cpf_pcnte = '') THEN 1 END) as sem_identificador
    FROM bpa_individualizado 
    WHERE prd_uid = '2755289' AND prd_cmp = '202512'
""")
row = cur.fetchone()
print(f"\n=== RESUMO BPA-I CNES 2755289 COMP 202512 ===")
print(f"Total de registros: {row[0]}")
print(f"Com CNS: {row[1]}")
print(f"Com CPF: {row[2]}")
print(f"Sem identificador (sem CNS e sem CPF): {row[3]}")

# Mostra amostra de registros
print(f"\n=== AMOSTRA DE 5 REGISTROS ===")
cur.execute("""
    SELECT id, prd_nmpac, prd_cnspac, prd_cpf_pcnte, exportado
    FROM bpa_individualizado 
    WHERE prd_uid = '2755289' AND prd_cmp = '202512'
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Nome: {row[1][:30] if row[1] else 'N/A'}, CNS: [{row[2]}], CPF: [{row[3]}], Exportado: {row[4]}")

# Mostra registros pendentes (não exportados)
cur.execute("""
    SELECT COUNT(*) 
    FROM bpa_individualizado 
    WHERE prd_uid = '2755289' AND prd_cmp = '202512' AND exportado = false
""")
print(f"\n=== PENDENTES (não exportados) ===")
print(f"Total pendentes: {cur.fetchone()[0]}")

conn.close()
