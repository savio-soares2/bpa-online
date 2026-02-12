"""
Script para corrigir tamanho dos campos VARCHAR(20) que estavam causando perda de dados
"""
import psycopg2
import os

# Configuração do banco
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "bpa_online"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

def executar_migracao():
    """Executa a migração para aumentar tamanho dos campos VARCHAR"""
    
    conn = None
    try:
        print("Conectando ao banco de dados...")
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        
        print("\n=== INICIANDO MIGRAÇÃO ===\n")
        
        # 1. Aumentar telefone na tabela pacientes
        print("1. Aumentando campo 'telefone' na tabela 'pacientes'...")
        cursor.execute("""
            ALTER TABLE pacientes 
            ALTER COLUMN telefone TYPE VARCHAR(50);
        """)
        print("   ✓ Campo 'telefone' agora é VARCHAR(50)")
        
        # 2. Aumentar telefone na tabela bpa_individualizado
        print("\n2. Aumentando campo 'prd_tel_pcnte' na tabela 'bpa_individualizado'...")
        cursor.execute("""
            ALTER TABLE bpa_individualizado 
            ALTER COLUMN prd_tel_pcnte TYPE VARCHAR(50);
        """)
        print("   ✓ Campo 'prd_tel_pcnte' agora é VARCHAR(50)")
        
        # 3. Aumentar número de autorização
        print("\n3. Aumentando campo 'prd_naut' na tabela 'bpa_individualizado'...")
        cursor.execute("""
            ALTER TABLE bpa_individualizado 
            ALTER COLUMN prd_naut TYPE VARCHAR(50);
        """)
        print("   ✓ Campo 'prd_naut' agora é VARCHAR(50)")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar mudanças
        print("\n=== VERIFICANDO ALTERAÇÕES ===\n")
        cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type, 
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name IN ('pacientes', 'bpa_individualizado')
              AND column_name IN ('telefone', 'prd_tel_pcnte', 'prd_naut')
            ORDER BY table_name, column_name;
        """)
        
        resultados = cursor.fetchall()
        print(f"{'Tabela':<25} {'Coluna':<20} {'Tipo':<15} {'Tamanho':>10}")
        print("-" * 75)
        for row in resultados:
            print(f"{row[0]:<25} {row[1]:<20} {row[2]:<15} {row[3]:>10}")
        
        print("\n=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===")
        print("\nAgora você pode reprocessar os dados sem perder nenhum registro!")
        
        cursor.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ ERRO durante a migração: {e}")
        if conn:
            conn.rollback()
        raise
    
    finally:
        if conn:
            conn.close()
            print("\nConexão fechada.")

if __name__ == "__main__":
    executar_migracao()
