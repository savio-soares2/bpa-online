"""Verifica pacientes cadastrados"""
import sys
sys.path.insert(0, '.')

from database import BPADatabase, get_connection

db = BPADatabase()

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM pacientes')
    total = cur.fetchone()[0]
    print(f'Total pacientes cadastrados: {total}')
    
    if total > 0:
        cur.execute('SELECT cns, cpf, nome, data_nascimento FROM pacientes LIMIT 5')
        print("\nAmostra de pacientes:")
        for row in cur.fetchall():
            print(f"  CNS={row[0]}, CPF={row[1]}, Nome={row[2]}, Nasc={row[3]}")
