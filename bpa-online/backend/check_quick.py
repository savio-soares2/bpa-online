"""
Analise simples dos 379 registros pendentes
"""
import sys
sys.path.insert(0, '.')
from database import get_connection

with get_connection() as conn:
    cursor = conn.cursor()
    
    # Total pendentes
    cursor.execute("SELECT COUNT(*) FROM bpa_individualizado WHERE prd_exportado = FALSE")
    total = cursor.fetchone()[0]
    print(f"Total pendentes: {total}")
    
    # Com CNS
    cursor.execute("""
        SELECT COUNT(*) FROM bpa_individualizado 
        WHERE prd_exportado = FALSE 
        AND prd_cnspac IS NOT NULL 
        AND prd_cnspac != '' 
        AND prd_cnspac != '0'
    """)
    com_cns = cursor.fetchone()[0]
    print(f"Com CNS: {com_cns}")
    
    # Com CPF
    cursor.execute("""
        SELECT COUNT(*) FROM bpa_individualizado 
        WHERE prd_exportado = FALSE 
        AND prd_cpf_pcnte IS NOT NULL 
        AND prd_cpf_pcnte != '' 
        AND prd_cpf_pcnte != '0'
        AND LENGTH(prd_cpf_pcnte) >= 11
    """)
    com_cpf = cursor.fetchone()[0]
    print(f"Com CPF (valido >=11 chars): {com_cpf}")
    
    # Com CNS OU CPF
    cursor.execute("""
        SELECT COUNT(*) FROM bpa_individualizado 
        WHERE prd_exportado = FALSE 
        AND (
            (prd_cnspac IS NOT NULL AND prd_cnspac != '' AND prd_cnspac != '0')
            OR
            (prd_cpf_pcnte IS NOT NULL AND prd_cpf_pcnte != '' AND prd_cpf_pcnte != '0' AND LENGTH(prd_cpf_pcnte) >= 11)
        )
    """)
    com_id = cursor.fetchone()[0]
    print(f"Com CNS OU CPF: {com_id}")
    
    # SEM CNS NEM CPF
    sem_id = total - com_id
    print(f"SEM CNS nem CPF: {sem_id}")
    
    # Amostra dos que TEM identificação 
    print("\n" + "="*60)
    print("AMOSTRA: Registros COM identificacao mas PENDENTES (primeiros 5)")
    print("="*60)
    cursor.execute("""
        SELECT id, prd_cnspac, prd_cpf_pcnte, prd_nmpac
        FROM bpa_individualizado 
        WHERE prd_exportado = FALSE 
        AND (
            (prd_cnspac IS NOT NULL AND prd_cnspac != '' AND prd_cnspac != '0')
            OR
            (prd_cpf_pcnte IS NOT NULL AND prd_cpf_pcnte != '' AND prd_cpf_pcnte != '0' AND LENGTH(prd_cpf_pcnte) >= 11)
        )
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\nID: {row[0]}")
        print(f"  CNS: {row[1]}")
        print(f"  CPF: {row[2]} (len={len(row[2]) if row[2] else 0})")
        print(f"  Nome: {row[3]}")
    
    cursor.close()
