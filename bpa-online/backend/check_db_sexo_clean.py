
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Constrói DATABASE_URL se não existir mas houver variáveis individuais
if not os.getenv("DATABASE_URL") and os.getenv("DB_USER"):
    os.environ["DATABASE_URL"] = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'bpa_online')}"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import BPADatabase, get_connection

def check_sexo_clean():
    print("Verificando se ainda existem valores incorretos de sexo (0 ou 1) no banco...")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT count(*) as total FROM bpa_individualizado WHERE prd_sexo IN ('0', '1')")
            row = cursor.fetchone()
            total = row[0] if row else 0
            
            if total == 0:
                print("SUCESSO: Nenhum registro com sexo 0 ou 1 encontrado.")
                print("O banco de dados foi corrigido corretamente.")
            else:
                print(f"FALHA: Ainda existem {total} registros com sexo 0 ou 1.")
                
            # Verifica verificação de amostra
            cursor.execute("SELECT prd_sexo, count(*) FROM bpa_individualizado GROUP BY prd_sexo")
            print("\nDistribuição atual de Sexo:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    check_sexo_clean()
