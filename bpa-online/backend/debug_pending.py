"""Verifica dados dos registros pendentes"""
import sys
sys.path.insert(0, '.')

from database import BPADatabase

db = BPADatabase()
pending = db.list_bpa_individualizado('2755289', '202512', exportado=False)[:5]

print("="*80)
print("AMOSTRA DE REGISTROS PENDENTES")
print("="*80)

for i, r in enumerate(pending, 1):
    print(f"\n#{i}")
    print(f"  Nome: {r.get('prd_nmpac')}")
    print(f"  CNS:  '{r.get('prd_cnspac')}'")
    print(f"  CPF:  '{r.get('prd_cpf_pcnte')}'")
    print(f"  Tel:  {r.get('prd_ddtel_pcnte')}-{r.get('prd_tel_pcnte')}")
    print(f"  Nasc: {r.get('prd_dtnasc')}")
    print(f"  Sexo: {r.get('prd_sexo')}")
