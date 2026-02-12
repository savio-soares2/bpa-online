"""Debug - verifica dados dos registros com CNS vazio"""
import sys
sys.path.insert(0, '.')

from database import BPADatabase

db = BPADatabase()
cnes = "2755289"
competencia = "202512"

# Busca pendentes
pending = db.list_bpa_individualizado(cnes, competencia, exportado=False)

print(f"Total pendentes: {len(pending)}")
print("\n" + "="*80)
print("ANÁLISE DOS REGISTROS PENDENTES")
print("="*80)

# Contadores
cns_vazio = 0
cns_preenchido = 0
tem_nome = 0
tem_dtnasc = 0

for r in pending:
    cnspac = r.get('prd_cnspac', '') or ''
    nome = r.get('prd_nmpac', '') or ''
    dtnasc = r.get('prd_dtnasc', '') or ''
    
    if cnspac.strip():
        cns_preenchido += 1
    else:
        cns_vazio += 1
    
    if nome.strip():
        tem_nome += 1
    if dtnasc.strip():
        tem_dtnasc += 1

print(f"\nCNS Paciente:")
print(f"  - Vazio: {cns_vazio}")
print(f"  - Preenchido: {cns_preenchido}")

print(f"\nOutros campos:")
print(f"  - Com nome: {tem_nome}")
print(f"  - Com data nascimento: {tem_dtnasc}")

# Amostra de registros sem CNS
print("\n" + "-"*80)
print("AMOSTRA DE 10 REGISTROS SEM CNS PACIENTE:")
print("-"*80)

count = 0
for r in pending:
    cnspac = r.get('prd_cnspac', '') or ''
    if not cnspac.strip():
        count += 1
        if count <= 10:
            print(f"\nID: {r['id']}")
            print(f"  PA: {r.get('prd_pa')}")
            print(f"  CNS Paciente: '{r.get('prd_cnspac')}'")
            print(f"  Nome: '{r.get('prd_nmpac')}'")
            print(f"  Data Nasc: '{r.get('prd_dtnasc')}'")
            print(f"  Sexo: '{r.get('prd_sexo')}'")
            print(f"  Data Aten: '{r.get('prd_dtaten')}'")
