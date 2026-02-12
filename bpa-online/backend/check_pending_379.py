"""
Verifica registros pendentes sem CPF/CNS
Analisa os 379 registros que nao foram exportados
"""
import sys
sys.path.insert(0, '.')

from database import get_connection

print("=" * 80)
print("VERIFICACAO DE REGISTROS PENDENTES SEM CPF/CNS")
print("=" * 80)

try:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Busca registros pendentes (nao exportados)
        cursor.execute("""
            SELECT 
                id,
                prd_cnspac,
                prd_cpf_pcnte,
                prd_nmpac,
                prd_dtnasc,
                prd_pa,
                prd_cbo
            FROM bpa_individualizado
            WHERE prd_exportado = FALSE
            ORDER BY id
        """)
        
        pendentes = cursor.fetchall()
        total = len(pendentes)
        
        print(f"\nTotal de registros pendentes: {total}")
        
        # Analise
        com_cns = 0
        com_cpf = 0
        com_ambos = 0
        sem_nenhum = 0
        
        sem_nenhum_list = []
        
        for row in pendentes:
            id, cns, cpf, nome, dt_nasc, proc, cbo = row
            
            has_cns = cns and str(cns).strip() and str(cns).strip() != '0'
            has_cpf = cpf and str(cpf).strip() and str(cpf).strip() != '0'
            
            if has_cns and has_cpf:
                com_ambos += 1
            elif has_cns:
                com_cns += 1
            elif has_cpf:
                com_cpf += 1
            else:
                sem_nenhum += 1
                if len(sem_nenhum_list) < 20:
                    sem_nenhum_list.append({
                        'id': id,
                        'nome': nome,
                        'dt_nasc': dt_nasc,
                        'cns': cns,
                        'cpf': cpf,
                        'proc': proc,
                        'cbo': cbo
                    })
        
        print("\n" + "=" * 80)
        print("RESUMO DA ANALISE")
        print("=" * 80)
        print(f"Total pendentes:     {total}")
        print(f"Com CNS e CPF:       {com_ambos}")
        print(f"Apenas CNS:          {com_cns}")
        print(f"Apenas CPF:          {com_cpf}")
        print(f"Sem CNS nem CPF:     {sem_nenhum}")
        
        if sem_nenhum > 0:
            print("\n" + "=" * 80)
            print(f"AMOSTRA DOS {min(20, sem_nenhum)} PRIMEIROS SEM CPF/CNS")
            print("=" * 80)
            
            for i, r in enumerate(sem_nenhum_list, 1):
                print(f"\n#{i} - ID: {r['id']}")
                print(f"  Nome: {r['nome']}")
                print(f"  Data Nasc: {r['dt_nasc']}")
                print(f"  CNS: {repr(r['cns'])}")
                print(f"  CPF: {repr(r['cpf'])}")
                print(f"  Procedimento: {r['proc']}")
                print(f"  CBO: {r['cbo']}")
        
        # Verifica se ha algum padrao nos pendentes
        if com_cns > 0 or com_cpf > 0 or com_ambos > 0:
            print("\n" + "=" * 80)
            print("ATENCAO!")
            print("=" * 80)
            print(f"Existem {com_cns + com_cpf + com_ambos} registros COM identificacao!")
            print("Esses deveriam ter sido exportados. Pode haver um problema no filtro.")
            
            # Mostra amostra dos que tem identificacao
            cursor.execute("""
                SELECT 
                    id,
                    prd_cnspac,
                    prd_cpf_pcnte,
                    prd_nmpac,
                    prd_exportado
                FROM bpa_individualizado
                WHERE prd_exportado = FALSE
                  AND (
                    (prd_cnspac IS NOT NULL AND prd_cnspac != '' AND prd_cnspac != '0')
                    OR
                    (prd_cpf_pcnte IS NOT NULL AND prd_cpf_pcnte != '' AND prd_cpf_pcnte != '0')
                  )
                LIMIT 10
            """)
            
            com_id = cursor.fetchall()
            print(f"\nAmostra de {len(com_id)} registros COM identificacao mas PENDENTES:")
            for row in com_id:
                print(f"  ID {row[0]}: CNS={repr(row[1])}, CPF={repr(row[2])}, Nome={row[3]}, Exportado={row[4]}")
        
        cursor.close()

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
