"""
Script para verificar registros BPA-I com CID vazio
"""
import sys
sys.path.append('.')

from database import get_connection

def check_cid():
    """Verifica status do campo prd_cid nos registros BPA-I"""
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Total de registros BPA-I
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM bpa_individualizado
        """)
        total = cursor.fetchone()[0]
        
        # Registros com CID vazio/null
        cursor.execute("""
            SELECT COUNT(*) as total_vazio
            FROM bpa_individualizado
            WHERE prd_cid IS NULL OR prd_cid = '' OR TRIM(prd_cid) = ''
        """)
        total_vazio = cursor.fetchone()[0]
        
        # Registros com CID preenchido
        cursor.execute("""
            SELECT COUNT(*) as total_preenchido
            FROM bpa_individualizado
            WHERE prd_cid IS NOT NULL AND TRIM(prd_cid) != ''
        """)
        total_preenchido = cursor.fetchone()[0]
        
        print("=" * 70)
        print("ANÁLISE DO CAMPO PRD_CID (CID) - BPA INDIVIDUALIZADO")
        print("=" * 70)
        print(f"Total de registros BPA-I: {total:,}")
        print(f"Registros com CID VAZIO:  {total_vazio:,} ({total_vazio/total*100:.1f}%)")
        print(f"Registros com CID OK:     {total_preenchido:,} ({total_preenchido/total*100:.1f}%)")
        print()
        
        if total_vazio > 0:
            print("⚠️ AMOSTRAS DE REGISTROS COM CID VAZIO:")
            print("-" * 70)
            cursor.execute("""
                SELECT 
                    id,
                    prd_cnspac as cns_paciente,
                    prd_nmpac as nome_paciente,
                    prd_pa as procedimento,
                    prd_cid as cid,
                    prd_dtaten as data_atendimento
                FROM bpa_individualizado
                WHERE prd_cid IS NULL OR prd_cid = '' OR TRIM(prd_cid) = ''
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                print(f"ID: {row[0]}")
                print(f"  Paciente: {row[2]} (CNS: {row[1]})")
                print(f"  Procedimento: {row[3]}")
                print(f"  CID: '{row[4]}' (vazio/null)")
                print(f"  Data: {row[5]}")
                print()
        
        if total_preenchido > 0:
            print("✅ AMOSTRAS DE REGISTROS COM CID PREENCHIDO:")
            print("-" * 70)
            cursor.execute("""
                SELECT 
                    id,
                    prd_cnspac as cns_paciente,
                    prd_nmpac as nome_paciente,
                    prd_pa as procedimento,
                    prd_cid as cid,
                    prd_dtaten as data_atendimento
                FROM bpa_individualizado
                WHERE prd_cid IS NOT NULL AND TRIM(prd_cid) != ''
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                print(f"ID: {row[0]}")
                print(f"  Paciente: {row[2]} (CNS: {row[1]})")
                print(f"  Procedimento: {row[3]}")
                print(f"  CID: '{row[4]}'")
                print(f"  Data: {row[5]}")
                print()
        
        # Estatísticas por CID
        print("📊 TOP 10 CIDs MAIS USADOS:")
        print("-" * 70)
        cursor.execute("""
            SELECT 
                prd_cid,
                COUNT(*) as quantidade
            FROM bpa_individualizado
            WHERE prd_cid IS NOT NULL AND TRIM(prd_cid) != ''
            GROUP BY prd_cid
            ORDER BY quantidade DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"  CID {row[0]}: {row[1]:,} registros")
        
        print()
        print("=" * 70)

if __name__ == '__main__':
    check_cid()
