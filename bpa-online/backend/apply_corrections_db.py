
import sys
import os
import logging
import traceback
from typing import List, Dict, Set
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

# Constrói DATABASE_URL se não existir mas houver variáveis individuais
if not os.getenv("DATABASE_URL") and os.getenv("DB_USER"):
    # hack para garantir que database.py pegue a url correta
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "bpa_online")
    
    # Monta URL
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    os.environ["DATABASE_URL"] = db_url
    print(f"Configurando DATABASE_URL via .env: postgresql://{user}:***@{host}:{port}/{dbname}")

# Adiciona diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import BPADatabase, get_connection
from services.corrections import BPACorrections

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_distinct_cnes(db: BPADatabase) -> List[str]:
    """Retorna lista de CNES únicos na tabela bpa_individualizado"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT prd_uid FROM bpa_individualizado WHERE prd_uid IS NOT NULL")
            rows = cursor.fetchall()
            return [row[0] for row in rows]

def apply_corrections_to_db():
    logger.info("Iniciando script de correção do banco de dados...")
    
    db = BPADatabase()
    
    # 1. Identificar CNES presentes no banco
    cnes_list = get_distinct_cnes(db)
    print(f"DEBUG: Encontrados {len(cnes_list)} CNES no banco de dados.")
    
    total_corrigidos = 0
    total_deletados = 0
    total_processados = 0
    
    for cnes in cnes_list:
        print(f"DEBUG: Processando CNES: {cnes}...")
        
        # Inicializa corretor para este CNES
        corrector = BPACorrections(cnes)
        
        # Busca todos os registros BPA-I deste CNES
        records = db.list_bpa_individualizado(cnes)
        
        if not records:
            print(f"DEBUG:   - Nenhum registro encontrado para CNES {cnes}.")
            continue
            
        print(f"DEBUG:   - Analisando {len(records)} registros...")
        
        cnes_corrigidos = 0
        cnes_deletados = 0
        
        for record in records:
            total_processados += 1
            record_id = record.get('id')
            
            if not record_id:
                continue
                
            try:
                # Aplica correções
                # O tipo é 'BPI' pois estamos iterando bpa_individualizado
                result = corrector.apply_corrections(record, tipo='BPI')
                
                if result.should_delete:
                    # Deleta registro
                    logger.warning(f"  - [DELETAR] ID {record_id}: {result.delete_reason}")
                    db.delete_bpa_individualizado(record_id)
                    cnes_deletados += 1
                    total_deletados += 1
                    
                elif result.corrections_applied:
                    # Atualiza registro
                    # logger.info(f"  - [CORRIGIR] ID {record_id}: {', '.join(result.corrections_applied)}")
                    
                    # Filtra apenas campos que existem na tabela para evitar erro de coluna inexistente (ex: 'sexo')
                    # Usa as chaves do registro original como lista de colunas válidas
                    valid_keys = set(record.keys())
                    update_data = {k: v for k, v in result.corrected.items() if k in valid_keys}
                    
                    db.update_bpa_individualizado(record_id, update_data)
                    cnes_corrigidos += 1
                    total_corrigidos += 1
                    


            except Exception as e:
                logger.error(f"Erro ao processar registro ID {record_id}: {e}")
                traceback.print_exc()
        
        print(f"DEBUG:   CNES {cnes} concluído: {cnes_corrigidos} corrigidos, {cnes_deletados} deletados.")
        
    logger.info("="*50)
    logger.info("RESUMO FINAL DA CORREÇÃO")
    logger.info("="*50)
    logger.info(f"Total Processados: {total_processados}")
    logger.info(f"Total Corrigidos:  {total_corrigidos}")
    logger.info(f"Total Deletados:   {total_deletados}")
    logger.info("="*50)

if __name__ == "__main__":
    apply_corrections_to_db()
