"""
Script simples para executar ALTER TABLE via database.py existente
"""
import sys
sys.path.append('.')

from database import get_connection

def executar_migracao():
    """Executa a migração para aumentar tamanho dos campos VARCHAR"""
    
    print("\n=== INICIANDO MIGRAÇÃO ===\n")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # 1. Aumentar telefone na tabela pacientes
            print("1. Aumentando campo 'telefone' na tabela 'pacientes'...")
            cursor.execute("ALTER TABLE pacientes ALTER COLUMN telefone TYPE VARCHAR(50);")
            print("   ✓ Campo 'telefone' agora é VARCHAR(50)")
            
            # 2. Aumentar telefone na tabela bpa_individualizado
            print("\n2. Aumentando campo 'prd_tel_pcnte' na tabela 'bpa_individualizado'...")
            cursor.execute("ALTER TABLE bpa_individualizado ALTER COLUMN prd_tel_pcnte TYPE VARCHAR(50);")
            print("   ✓ Campo 'prd_tel_pcnte' agora é VARCHAR(50)")
            
            # 3. Aumentar número de autorização
            print("\n3. Aumentando campo 'prd_naut' na tabela 'bpa_individualizado'...")
            cursor.execute("ALTER TABLE bpa_individualizado ALTER COLUMN prd_naut TYPE VARCHAR(50);")
            print("   ✓ Campo 'prd_naut' agora é VARCHAR(50)")
            
            # Commit
            conn.commit()
            
            # Verificar
            print("\n=== VERIFICANDO ALTERAÇÕES ===\n")
            cursor.execute("""
                SELECT table_name, column_name, character_maximum_length
                FROM information_schema.columns
                WHERE table_name IN ('pacientes', 'bpa_individualizado')
                  AND column_name IN ('telefone', 'prd_tel_pcnte', 'prd_naut')
                ORDER BY table_name, column_name;
            """)
            
            print(f"{'Tabela':<30} {'Coluna':<20} {'Tamanho':>10}")
            print("-" * 65)
            for row in cursor.fetchall():
                print(f"{row[0]:<30} {row[1]:<20} {row[2]:>10}")
            
            print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("\nAgora você pode reprocessar os dados sem perder nenhum registro!\n")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERRO: {e}\n")
            raise
        finally:
            cursor.close()

if __name__ == "__main__":
    executar_migracao()
