"""
Script para importar dados do SIGTAP para o PostgreSQL
"""
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
from services.sigtap_parser import SigtapParser
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
    'database': os.getenv('DB_NAME', 'bpa_online'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Caminho para os arquivos SIGTAP
SIGTAP_DIR = r'C:\Users\60612427358\Documents\bpa-online\bpa-online\BPA-main\TabelaUnificada_202512_v2601161858'


def create_tables(conn):
    """Cria as tabelas SIGTAP no banco"""
    print("Criando tabelas SIGTAP...")
    
    script_path = Path(__file__).parent / 'init_sigtap.sql'
    with open(script_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with conn.cursor() as cur:
        cur.execute(sql)
    
    conn.commit()
    print("✓ Tabelas criadas com sucesso")


def import_procedimentos(conn, parser: SigtapParser):
    """Importa tabela de procedimentos"""
    print("Importando procedimentos...")
    
    procedimentos = parser.parse_procedimentos()
    
    sql = """
        INSERT INTO sigtap_procedimento (
            co_procedimento, no_procedimento, tp_complexidade, tp_sexo,
            qt_maxima_execucao, qt_dias_permanencia, qt_pontos,
            vl_idade_minima, vl_idade_maxima,
            vl_sh, vl_sa, vl_sp, co_financiamento, co_rubrica,
            qt_tempo_permanencia, dt_competencia
        ) VALUES (
            %(CO_PROCEDIMENTO)s, %(NO_PROCEDIMENTO)s, %(TP_COMPLEXIDADE)s, %(TP_SEXO)s,
            NULLIF(%(QT_MAXIMA_EXECUCAO)s, '')::INT,
            NULLIF(%(QT_DIAS_PERMANENCIA)s, '')::INT,
            NULLIF(%(QT_PONTOS)s, '')::INT,
            NULLIF(%(VL_IDADE_MINIMA)s, '')::INT,
            NULLIF(%(VL_IDADE_MAXIMA)s, '')::INT,
            NULLIF(%(VL_SH)s, '')::DECIMAL,
            NULLIF(%(VL_SA)s, '')::DECIMAL,
            NULLIF(%(VL_SP)s, '')::DECIMAL,
            %(CO_FINANCIAMENTO)s, %(CO_RUBRICA)s,
            NULLIF(%(QT_TEMPO_PERMANENCIA)s, '')::INT,
            %(DT_COMPETENCIA)s
        )
        ON CONFLICT (co_procedimento) DO UPDATE SET
            no_procedimento = EXCLUDED.no_procedimento,
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, procedimentos, page_size=1000)
    
    conn.commit()
    print(f"✓ {len(procedimentos)} procedimentos importados")


def import_ocupacoes(conn, parser: SigtapParser):
    """Importa tabela de ocupações (CBO)"""
    print("Importando ocupações (CBO)...")
    
    ocupacoes = parser.parse_ocupacoes()
    
    sql = """
        INSERT INTO sigtap_ocupacao (co_ocupacao, no_ocupacao, dt_competencia)
        VALUES (%(CO_OCUPACAO)s, %(NO_OCUPACAO)s, %(DT_COMPETENCIA)s)
        ON CONFLICT (co_ocupacao) DO UPDATE SET
            no_ocupacao = EXCLUDED.no_ocupacao,
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, ocupacoes, page_size=1000)
    
    conn.commit()
    print(f"✓ {len(ocupacoes)} ocupações importadas")


def import_servicos(conn, parser: SigtapParser):
    """Importa tabela de serviços"""
    print("Importando serviços...")
    
    servicos = parser.parse_servicos()
    
    sql = """
        INSERT INTO sigtap_servico (co_servico, co_classificacao, no_servico_classificacao, dt_competencia)
        VALUES (%(CO_SERVICO)s, %(CO_CLASSIFICACAO)s, %(NO_SERVICO_CLASSIFICACAO)s, %(DT_COMPETENCIA)s)
        ON CONFLICT (co_servico, co_classificacao) DO UPDATE SET
            no_servico_classificacao = EXCLUDED.no_servico_classificacao,
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, servicos, page_size=1000)
    
    conn.commit()
    print(f"✓ {len(servicos)} serviços importados")


def import_registros(conn, parser: SigtapParser):
    """Importa tabela de instrumentos de registro"""
    print("Importando instrumentos de registro...")
    
    registros = parser.parse_registros()
    
    sql = """
        INSERT INTO sigtap_registro (co_registro, no_registro, dt_competencia)
        VALUES (%(CO_REGISTRO)s, %(NO_REGISTRO)s, %(DT_COMPETENCIA)s)
        ON CONFLICT (co_registro) DO UPDATE SET
            no_registro = EXCLUDED.no_registro,
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, registros, page_size=100)
    
    conn.commit()
    print(f"✓ {len(registros)} instrumentos importados")


def import_procedimento_ocupacao(conn, parser: SigtapParser):
    """Importa relação procedimento x ocupação"""
    print("Importando relação procedimento x CBO...")
    
    relacoes = parser.parse_procedimento_ocupacao()
    
    sql = """
        INSERT INTO sigtap_proc_cbo (co_procedimento, co_ocupacao, dt_competencia)
        VALUES (%(CO_PROCEDIMENTO)s, %(CO_OCUPACAO)s, %(DT_COMPETENCIA)s)
        ON CONFLICT (co_procedimento, co_ocupacao) DO UPDATE SET
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, relacoes, page_size=1000)
    
    conn.commit()
    print(f"✓ {len(relacoes)} relações procedimento-CBO importadas")


def import_procedimento_servico(conn, parser: SigtapParser):
    """Importa relação procedimento x serviço"""
    print("Importando relação procedimento x serviço...")
    
    relacoes = parser.parse_procedimento_servico()
    
    sql = """
        INSERT INTO sigtap_proc_servico (co_procedimento, co_servico, co_classificacao, dt_competencia)
        VALUES (%(CO_PROCEDIMENTO)s, %(CO_SERVICO)s, %(CO_CLASSIFICACAO)s, %(DT_COMPETENCIA)s)
        ON CONFLICT (co_procedimento, co_servico, co_classificacao) DO UPDATE SET
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, relacoes, page_size=1000)
    
    conn.commit()
    print(f"✓ {len(relacoes)} relações procedimento-serviço importadas")


def import_procedimento_registro(conn, parser: SigtapParser):
    """Importa relação procedimento x instrumento de registro"""
    print("Importando relação procedimento x registro...")
    
    relacoes = parser.parse_procedimento_registro()
    
    sql = """
        INSERT INTO sigtap_proc_registro (co_procedimento, co_registro, dt_competencia)
        VALUES (%(CO_PROCEDIMENTO)s, %(CO_REGISTRO)s, %(DT_COMPETENCIA)s)
        ON CONFLICT (co_procedimento, co_registro) DO UPDATE SET
            dt_competencia = EXCLUDED.dt_competencia
    """
    
    with conn.cursor() as cur:
        execute_batch(cur, sql, relacoes, page_size=1000)
    
    conn.commit()
    print(f"✓ {len(relacoes)} relações procedimento-registro importadas")


def main():
    """Executa importação completa"""
    print("=" * 60)
    print("IMPORTAÇÃO DE DADOS SIGTAP PARA POSTGRESQL")
    print("=" * 60)
    print()
    
    # Conectar ao banco
    print("Conectando ao banco de dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"✓ Conectado a {DB_CONFIG['database']} em {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    try:
        # Criar tabelas
        create_tables(conn)
        print()
        
        # Inicializar parser
        parser = SigtapParser(SIGTAP_DIR)
        
        # Importar tabelas base (sem foreign keys)
        import_procedimentos(conn, parser)
        import_ocupacoes(conn, parser)
        import_servicos(conn, parser)
        import_registros(conn, parser)
        print()
        
        # Importar tabelas de relacionamento (com foreign keys)
        import_procedimento_ocupacao(conn, parser)
        import_procedimento_servico(conn, parser)
        import_procedimento_registro(conn, parser)
        print()
        
        print("=" * 60)
        print("✓ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
