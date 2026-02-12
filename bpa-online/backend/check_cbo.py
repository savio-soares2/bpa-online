from dbfread import DBF

# Check S_PACBO.DBF for unique CBOs
pacbo = DBF(r'c:\BPA\Tabelas Nacionais do Kit BPA\202511\S_PACBO.DBF', encoding='latin1')

cbos = set()
for r in pacbo:
    cbo = r.get('PACBO_CBO', '').strip()
    if cbo:
        cbos.add(cbo)

print(f"Total CBOs únicos em S_PACBO: {len(cbos)}")
print(f"Primeiros 10: {sorted(cbos)[:10]}")
print(f"Exemplo formato: {list(cbos)[0]}")
