import firebirdsql

conn = firebirdsql.connect(
    host='localhost', 
    port=3050, 
    database=r'C:\BPA\BPAMAG.GDB', 
    user='SYSDBA', 
    password='masterkey', 
    charset='UTF8'
)
cursor = conn.cursor()

# Ver estrutura da tabela S_PRD
cursor.execute("""
    SELECT RDB$FIELD_NAME 
    FROM RDB$RELATION_FIELDS 
    WHERE RDB$RELATION_NAME = 'S_PRD'
    ORDER BY RDB$FIELD_POSITION
""")
print('=== Campos da tabela S_PRD ===')
for row in cursor.fetchall():
    print(row[0].strip())

# Ver algumas linhas de dados
print('\n=== Primeiros 5 registros da S_PRD ===')
cursor.execute("SELECT FIRST 5 * FROM S_PRD")
cols = [d[0] for d in cursor.description]
print(f'Colunas: {cols}')
for row in cursor.fetchall():
    print(dict(zip(cols, row)))

conn.close()
