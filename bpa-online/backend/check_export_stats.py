"""Script para verificar estatísticas de exportação"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import psycopg2

dsn = "postgresql://bpa_user:bpa_pass@localhost:5433/bpa_online"
conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("="*60)
print("ESTATÍSTICAS DE EXPORTAÇÃO BPA-I")
print("="*60)

cur.execute('''
    SELECT prd_uid, prd_cmp, 
           COUNT(*) as total, 
           SUM(CASE WHEN prd_exportado THEN 1 ELSE 0 END) as exportados, 
           SUM(CASE WHEN NOT prd_exportado THEN 1 ELSE 0 END) as pendentes 
    FROM bpa_individualizado 
    GROUP BY prd_uid, prd_cmp
    ORDER BY prd_uid, prd_cmp
''')

rows = cur.fetchall()
print(f"{'CNES':^10} | {'COMP':^8} | {'TOTAL':^8} | {'EXPORT':^8} | {'PEND':^8}")
print("-"*60)
for r in rows:
    print(f"{r[0]:^10} | {r[1]:^8} | {r[2]:^8} | {r[3]:^8} | {r[4]:^8}")

# Verifica alguns registros pendentes
print("\n" + "="*60)
print("AMOSTRA DE 5 REGISTROS PENDENTES")
print("="*60)
cur.execute('''
    SELECT id, prd_uid, prd_cmp, prd_pa, prd_cnsmed, prd_exportado 
    FROM bpa_individualizado 
    WHERE NOT prd_exportado
    LIMIT 5
''')
for r in cur.fetchall():
    print(f"ID={r[0]}, CNES={r[1]}, COMP={r[2]}, PA={r[3]}, CNS={r[4]}, EXP={r[5]}")

conn.close()
