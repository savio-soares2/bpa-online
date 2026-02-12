"""Teste da API BiServer - verificar registros sem CNS"""
import sys
sys.path.insert(0, '.')

from services.biserver_client import BiServerAPIClient

client = BiServerAPIClient()

print("="*80)
print("TESTE API BISERVER - REGISTROS SEM CNS")
print("="*80)

try:
    data = client.get_bpa_data(cnes="2755289", competencia="2025-12", page=0)
    registros = data.get('registros', [])
    
    print(f"Total registros: {len(registros)}")
    
    # Conta registros com/sem CNS
    com_cns = 0
    sem_cns = 0
    sem_cns_list = []
    
    for r in registros:
        cns = r.get('prd_cnspac')
        # CNS pode ser int ou string
        cns_str = str(cns) if cns else ''
        
        if cns_str.strip() and cns_str != '0' and cns_str != 'None':
            com_cns += 1
        else:
            sem_cns += 1
            if len(sem_cns_list) < 10:
                sem_cns_list.append(r)
    
    print(f"\nCom CNS: {com_cns}")
    print(f"Sem CNS: {sem_cns}")
    
    if sem_cns_list:
        print("\n" + "-"*60)
        print("REGISTROS SEM CNS (primeiros 10):")
        print("-"*60)
        for i, r in enumerate(sem_cns_list, 1):
            print(f"\n#{i}")
            print(f"  Nome: {r.get('prd_nmpac')}")
            print(f"  CNS: {repr(r.get('prd_cnspac'))}")
            print(f"  Data Nasc: {r.get('prd_dtnasc')}")
            print(f"  Procedimento: {r.get('prd_pa')}")
            print(f"  Telefone: {r.get('prd_ddtel_pcnte')}-{r.get('prd_tel_pcnte')}")
            
            # Mostra TODOS os campos para ver se tem algo com CPF
            print(f"  --- Todos os campos ---")
            for k, v in r.items():
                if v and str(v).strip():
                    print(f"    {k}: {v}")
    else:
        print("\n✅ Todos os registros têm CNS!")

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
