"""
Script para consultar estrutura de dados no Firebird
Analisa campos INE, CATEN, FLH, SEQ
"""
import fdb

# Configuração Firebird
FB_CONFIG = {
    'host': 'localhost',
    'port': 3050,
    'database': r'C:\BPA\BPAMAG.GDB',
    'user': 'SYSDBA',
    'password': 'masterkey',
    'charset': 'UTF8'
}

def main():
    print("Conectando ao Firebird...")
    try:
        conn = fdb.connect(
            host=FB_CONFIG['host'],
            port=FB_CONFIG['port'],
            database=FB_CONFIG['database'],
            user=FB_CONFIG['user'],
            password=FB_CONFIG['password'],
            charset=FB_CONFIG['charset']
        )
        cursor = conn.cursor()
        print("Conectado!\n")
        
        # Consulta para o CAPS AD (6061478)
        print("="*60)
        print("ANÁLISE DE CAMPOS PRD_INE, PRD_CATEN, PRD_FLH, PRD_SEQ")
        print("="*60)
        
        # 1. Verificar valores únicos de PRD_INE
        print("\n📌 PRD_INE (INE Equipe):")
        cursor.execute("""
            SELECT DISTINCT PRD_INE, COUNT(*) as QTD 
            FROM S_PRD 
            WHERE PRD_UID = '6061478'
            GROUP BY PRD_INE
            ORDER BY QTD DESC
        """)
        for row in cursor.fetchall():
            print(f"   INE: '{row[0]}' - {row[1]} registros")
        
        # 2. Verificar valores únicos de PRD_CATEN
        print("\n📌 PRD_CATEN (Caráter Atendimento):")
        cursor.execute("""
            SELECT DISTINCT PRD_CATEN, COUNT(*) as QTD 
            FROM S_PRD 
            WHERE PRD_UID = '6061478'
            GROUP BY PRD_CATEN
            ORDER BY QTD DESC
        """)
        for row in cursor.fetchall():
            print(f"   CATEN: '{row[0]}' - {row[1]} registros")
        
        # 3. Verificar valores de PRD_FLH (Folha)
        print("\n📌 PRD_FLH (Folha):")
        cursor.execute("""
            SELECT DISTINCT PRD_FLH, COUNT(*) as QTD 
            FROM S_PRD 
            WHERE PRD_UID = '6061478'
            GROUP BY PRD_FLH
            ORDER BY PRD_FLH
        """)
        for row in cursor.fetchall():
            print(f"   FLH: '{row[0]}' - {row[1]} registros")
        
        # 4. Verificar valores de PRD_SEQ (Sequência)
        print("\n📌 PRD_SEQ (Sequência) - Min/Max por competência:")
        cursor.execute("""
            SELECT PRD_CMP, MIN(PRD_SEQ) as MIN_SEQ, MAX(PRD_SEQ) as MAX_SEQ, COUNT(*) as QTD
            FROM S_PRD 
            WHERE PRD_UID = '6061478'
            GROUP BY PRD_CMP
            ORDER BY PRD_CMP DESC
            ROWS 5
        """)
        for row in cursor.fetchall():
            print(f"   Competência {row[0]}: SEQ {row[1]} a {row[2]} ({row[3]} registros)")
        
        # 5. Exemplo de registro completo
        print("\n📌 EXEMPLO DE REGISTRO COMPLETO:")
        cursor.execute("""
            SELECT FIRST 1 
                PRD_UID, PRD_CMP, PRD_FLH, PRD_SEQ, PRD_INE, PRD_CATEN,
                PRD_CNSMED, PRD_CBO, PRD_PA, PRD_CNSPAC, PRD_NMPAC
            FROM S_PRD 
            WHERE PRD_UID = '6061478' AND PRD_CMP = '202512'
        """)
        row = cursor.fetchone()
        if row:
            print(f"   CNES: {row[0]}")
            print(f"   Competência: {row[1]}")
            print(f"   Folha: {row[2]}")
            print(f"   Sequência: {row[3]}")
            print(f"   INE: {row[4]}")
            print(f"   CATEN: {row[5]}")
            print(f"   CNS Med: {row[6]}")
            print(f"   CBO: {row[7]}")
            print(f"   PA: {row[8]}")
            print(f"   CNS Pac: {row[9]}")
            print(f"   Nome: {row[10]}")
        
        # 6. Verificar por CNES diferentes
        print("\n📌 COMPARAÇÃO ENTRE ESTABELECIMENTOS:")
        cursor.execute("""
            SELECT PRD_UID, 
                   CAST(MIN(PRD_INE) AS VARCHAR(20)) as INE_MIN,
                   CAST(MAX(PRD_INE) AS VARCHAR(20)) as INE_MAX,
                   CAST(MIN(PRD_CATEN) AS VARCHAR(5)) as CATEN_MIN,
                   CAST(MAX(PRD_CATEN) AS VARCHAR(5)) as CATEN_MAX,
                   COUNT(*) as QTD
            FROM S_PRD 
            GROUP BY PRD_UID
            ORDER BY QTD DESC
            ROWS 10
        """)
        print(f"   {'CNES':<10} {'INE':<25} {'CATEN':<10} {'QTD':<10}")
        print(f"   {'-'*55}")
        for row in cursor.fetchall():
            ine = f"{row[1]}" if row[1] == row[2] else f"{row[1]}-{row[2]}"
            caten = f"{row[3]}" if row[3] == row[4] else f"{row[3]}-{row[4]}"
            print(f"   {row[0]:<10} {ine:<25} {caten:<10} {row[5]:<10}")
        
        conn.close()
        print("\n✅ Análise concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
