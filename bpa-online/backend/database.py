"""
BPA Online - Banco de Dados PostgreSQL
Usa nomes de colunas compatíveis com Firebird (PRD_*)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Configuração do banco PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://bpa_user:bpa_secret_2024@localhost:5433/bpa_online"
)

def parse_database_url(url: str) -> Dict:
    """Parse DATABASE_URL para componentes"""
    url = url.replace("postgresql://", "")
    user_pass, host_db = url.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_db.split("/")
    
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "5432"
    
    return {
        "host": host,
        "port": int(port),
        "database": database,
        "user": user,
        "password": password
    }

DB_CONFIG = parse_database_url(DATABASE_URL)

# Pool de conexões
connection_pool = None

def init_pool():
    """Inicializa pool de conexões"""
    global connection_pool
    try:
        connection_pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        print(f"[DB] Pool PostgreSQL inicializado: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    except Exception as e:
        print(f"[DB] Erro ao criar pool: {e}")
        connection_pool = None

@contextmanager
def get_connection():
    """Context manager para conexão PostgreSQL do pool"""
    global connection_pool
    
    if connection_pool is None:
        init_pool()
    
    conn = None
    try:
        if connection_pool:
            conn = connection_pool.getconn()
        else:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )
        yield conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
        raise
    finally:
        if conn:
            if connection_pool:
                connection_pool.putconn(conn)
            else:
                conn.close()


def init_database():
    """Inicializa as tabelas do banco de dados - Nomes compatíveis com Firebird"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
                
                # Tabela de profissionais
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS profissionais (
                        id SERIAL PRIMARY KEY,
                        cnes VARCHAR(7) NOT NULL,
                        cns VARCHAR(15) NOT NULL,
                        cpf VARCHAR(11),
                        nome VARCHAR(255) NOT NULL,
                        cbo VARCHAR(6) NOT NULL,
                        ine VARCHAR(10),
                        vinculo VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(cnes, cns)
                    )
                ''')
                
                # Tabela de pacientes
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pacientes (
                        id SERIAL PRIMARY KEY,
                        cns VARCHAR(15) UNIQUE NOT NULL,
                        cpf VARCHAR(11),
                        nome VARCHAR(255) NOT NULL,
                        data_nascimento VARCHAR(8),
                        sexo VARCHAR(1),
                        raca_cor VARCHAR(2),
                        nacionalidade VARCHAR(3) DEFAULT '010',
                        municipio_ibge VARCHAR(6),
                        cep VARCHAR(8),
                        logradouro_codigo VARCHAR(10),
                        endereco VARCHAR(255),
                        numero VARCHAR(10),
                        complemento VARCHAR(100),
                        bairro VARCHAR(100),
                        telefone VARCHAR(20),
                        email VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela BPA Individualizado - Nomes compatíveis com Firebird S_PRD
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bpa_individualizado (
                        id SERIAL PRIMARY KEY,
                        prd_uid VARCHAR(7),
                        prd_cmp VARCHAR(6),
                        prd_flh INTEGER DEFAULT 1,
                        prd_seq INTEGER DEFAULT 1,
                        
                        prd_cnsmed VARCHAR(15),
                        prd_cbo VARCHAR(6),
                        prd_ine VARCHAR(10),
                        
                        prd_cnspac VARCHAR(15),
                        prd_cpf_pcnte VARCHAR(11),
                        prd_nmpac VARCHAR(255),
                        prd_dtnasc VARCHAR(8),
                        prd_sexo VARCHAR(1),
                        prd_raca VARCHAR(2) DEFAULT '99',
                        prd_nac VARCHAR(3) DEFAULT '010',
                        prd_ibge VARCHAR(6),
                        prd_idade VARCHAR(3),
                        
                        prd_cep_pcnte VARCHAR(8),
                        prd_lograd_pcnte VARCHAR(10),
                        prd_end_pcnte VARCHAR(255),
                        prd_num_pcnte VARCHAR(10),
                        prd_compl_pcnte VARCHAR(100),
                        prd_bairro_pcnte VARCHAR(100),
                        prd_ddtel_pcnte VARCHAR(2),
                        prd_tel_pcnte VARCHAR(20),
                        prd_email_pcnte VARCHAR(255),
                        
                        prd_dtaten VARCHAR(8),
                        prd_pa VARCHAR(10),
                        prd_qt_p INTEGER DEFAULT 1,
                        prd_cid VARCHAR(10),
                        prd_caten VARCHAR(2) DEFAULT '01',
                        prd_naut VARCHAR(20),
                        prd_cnpj VARCHAR(14),
                        prd_servico VARCHAR(3),
                        prd_classificacao VARCHAR(3),
                        prd_etnia VARCHAR(4),
                        prd_eqp_area VARCHAR(10),
                        prd_eqp_seq VARCHAR(10),
                        
                        prd_mvm VARCHAR(6),
                        prd_advqt VARCHAR(2) DEFAULT '00',
                        prd_flpa VARCHAR(1) DEFAULT '0',
                        prd_flcbo VARCHAR(1) DEFAULT '0',
                        prd_flca VARCHAR(1) DEFAULT '0',
                        prd_flida VARCHAR(1) DEFAULT '0',
                        prd_flqt VARCHAR(1) DEFAULT '0',
                        prd_fler VARCHAR(1) DEFAULT '0',
                        prd_flmun VARCHAR(1) DEFAULT '0',
                        prd_flcid VARCHAR(1) DEFAULT '0',
                        
                        prd_org VARCHAR(10) DEFAULT 'BPI',
                        prd_exportado BOOLEAN DEFAULT FALSE,
                        data_exportacao TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Índices BPA-I
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_uid ON bpa_individualizado(prd_uid)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_cmp ON bpa_individualizado(prd_cmp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_uid_cmp ON bpa_individualizado(prd_uid, prd_cmp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_exportado ON bpa_individualizado(prd_exportado)')
                
                # Tabela BPA Consolidado
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bpa_consolidado (
                        id SERIAL PRIMARY KEY,
                        prd_uid VARCHAR(7),
                        prd_cmp VARCHAR(6),
                        prd_flh INTEGER DEFAULT 1,
                        prd_cnsmed VARCHAR(15),
                        prd_cbo VARCHAR(6),
                        prd_pa VARCHAR(10),
                        prd_qt_p INTEGER DEFAULT 1,
                        prd_idade VARCHAR(3),
                        prd_org VARCHAR(10) DEFAULT 'BPC',
                        prd_exportado BOOLEAN DEFAULT FALSE,
                        data_exportacao TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Índices BPA-C
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpac_uid ON bpa_consolidado(prd_uid)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpac_cmp ON bpa_consolidado(prd_cmp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpac_exportado ON bpa_consolidado(prd_exportado)')
                
                # Tabela de exportações
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exportacoes (
                        id SERIAL PRIMARY KEY,
                        cnes VARCHAR(7) NOT NULL,
                        competencia VARCHAR(6) NOT NULL,
                        tipo VARCHAR(10) NOT NULL,
                        arquivo VARCHAR(255),
                        total_registros INTEGER DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'pendente',
                        erro TEXT,
                        usuario_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("[DB] Tabelas PostgreSQL inicializadas com sucesso")
    except Exception as e:
        # Silencia erros de inicialização para evitar loops
        logger.warning(f"[DB] Aviso durante inicialização: {e}")
        pass  # Não propaga o erro


class BPADatabase:
    """Classe para acesso ao banco de dados BPA"""
    
    def __init__(self):
        # Apenas inicializa o pool, não recria tabelas toda vez
        if connection_pool is None:
            init_pool()
        # Garante inicialização sob demanda
        ensure_database_initialized()
    
    # ========== PROFISSIONAIS ==========
    
    def save_profissional(self, data: Dict) -> int:
        """Salva profissional"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO profissionais (cnes, cns, cpf, nome, cbo, ine, vinculo)
                    VALUES (%(cnes)s, %(cns)s, %(cpf)s, %(nome)s, %(cbo)s, %(ine)s, %(vinculo)s)
                    ON CONFLICT (cnes, cns) DO UPDATE SET
                        nome = EXCLUDED.nome, cbo = EXCLUDED.cbo, ine = EXCLUDED.ine,
                        vinculo = EXCLUDED.vinculo, updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                ''', data)
                result = cursor.fetchone()
                conn.commit()
                return result['id']
    
    def get_profissional(self, cnes: str, cns: str) -> Optional[Dict]:
        """Busca profissional por CNES e CNS"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM profissionais WHERE cnes = %s AND cns = %s",
                    (cnes, cns)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def list_profissionais(self, cnes: str) -> List[Dict]:
        """Lista profissionais de um CNES"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM profissionais WHERE cnes = %s ORDER BY nome",
                    (cnes,)
                )
                return [dict(row) for row in cursor.fetchall()]
    
    # ========== PACIENTES ==========
    
    def save_paciente(self, data: Dict) -> int:
        """Salva paciente (cache)"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO pacientes (
                        cns, cpf, nome, data_nascimento, sexo, raca_cor,
                        nacionalidade, municipio_ibge, cep, logradouro_codigo,
                        endereco, numero, complemento, bairro, telefone, email
                    ) VALUES (
                        %(cns)s, %(cpf)s, %(nome)s, %(data_nascimento)s, %(sexo)s, %(raca_cor)s,
                        %(nacionalidade)s, %(municipio_ibge)s, %(cep)s, %(logradouro_codigo)s,
                        %(endereco)s, %(numero)s, %(complemento)s, %(bairro)s, %(telefone)s, %(email)s
                    )
                    ON CONFLICT (cns) DO UPDATE SET
                        nome = EXCLUDED.nome, data_nascimento = EXCLUDED.data_nascimento,
                        sexo = EXCLUDED.sexo, telefone = EXCLUDED.telefone,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                ''', {
                    'cns': data.get('cns'),
                    'cpf': data.get('cpf'),
                    'nome': data.get('nome'),
                    'data_nascimento': data.get('data_nascimento'),
                    'sexo': data.get('sexo'),
                    'raca_cor': data.get('raca_cor', '99'),
                    'nacionalidade': data.get('nacionalidade', '010'),
                    'municipio_ibge': data.get('municipio_ibge'),
                    'cep': data.get('cep'),
                    'logradouro_codigo': data.get('logradouro_codigo'),
                    'endereco': data.get('endereco'),
                    'numero': data.get('numero'),
                    'complemento': data.get('complemento'),
                    'bairro': data.get('bairro'),
                    'telefone': data.get('telefone'),
                    'email': data.get('email')
                })
                result = cursor.fetchone()
                conn.commit()
                return result['id'] if result else 0
    
    def get_paciente(self, cns: str) -> Optional[Dict]:
        """Busca paciente pelo CNS"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM pacientes WHERE cns = %s", (cns,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def get_paciente_by_nome_nascimento(self, nome: str, data_nascimento: str) -> Optional[Dict]:
        """Busca paciente pelo nome e data de nascimento"""
        if not nome or not data_nascimento:
            return None
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Normaliza nome para busca (maiúsculo, sem espaços extras)
                nome_norm = ' '.join(nome.upper().split())
                cursor.execute('''
                    SELECT * FROM pacientes 
                    WHERE UPPER(TRIM(nome)) = %s AND data_nascimento = %s
                    LIMIT 1
                ''', (nome_norm, data_nascimento))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def search_pacientes(self, termo: str, limit: int = 20) -> List[Dict]:
        """Busca pacientes por nome ou CNS"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT * FROM pacientes 
                    WHERE nome ILIKE %s OR cns LIKE %s
                    ORDER BY nome LIMIT %s
                ''', (f'%{termo}%', f'%{termo}%', limit))
                return [dict(row) for row in cursor.fetchall()]
    
    # ========== BPA INDIVIDUALIZADO ==========
    
    def save_bpa_individualizado(self, data: Dict) -> int:
        """Salva registro BPA-I usando nomes compatíveis com Firebird"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO bpa_individualizado (
                        prd_uid, prd_cmp, prd_flh, prd_seq,
                        prd_cnsmed, prd_cbo, prd_ine,
                        prd_cnspac, prd_cpf_pcnte, prd_nmpac, prd_dtnasc,
                        prd_sexo, prd_raca, prd_nac, prd_ibge, prd_idade,
                        prd_cep_pcnte, prd_lograd_pcnte, prd_end_pcnte, prd_num_pcnte, 
                        prd_compl_pcnte, prd_bairro_pcnte, prd_ddtel_pcnte, prd_tel_pcnte, prd_email_pcnte,
                        prd_dtaten, prd_pa, prd_qt_p, prd_cid, prd_caten,
                        prd_naut, prd_cnpj, prd_servico, prd_classificacao,
                        prd_etnia, prd_eqp_area, prd_eqp_seq, prd_mvm, prd_org
                    ) VALUES (
                        %(prd_uid)s, %(prd_cmp)s, %(prd_flh)s, %(prd_seq)s,
                        %(prd_cnsmed)s, %(prd_cbo)s, %(prd_ine)s,
                        %(prd_cnspac)s, %(prd_cpf_pcnte)s, %(prd_nmpac)s, %(prd_dtnasc)s,
                        %(prd_sexo)s, %(prd_raca)s, %(prd_nac)s, %(prd_ibge)s, %(prd_idade)s,
                        %(prd_cep_pcnte)s, %(prd_lograd_pcnte)s, %(prd_end_pcnte)s, %(prd_num_pcnte)s,
                        %(prd_compl_pcnte)s, %(prd_bairro_pcnte)s, %(prd_ddtel_pcnte)s, %(prd_tel_pcnte)s, %(prd_email_pcnte)s,
                        %(prd_dtaten)s, %(prd_pa)s, %(prd_qt_p)s, %(prd_cid)s, %(prd_caten)s,
                        %(prd_naut)s, %(prd_cnpj)s, %(prd_servico)s, %(prd_classificacao)s,
                        %(prd_etnia)s, %(prd_eqp_area)s, %(prd_eqp_seq)s, %(prd_mvm)s, %(prd_org)s
                    )
                    RETURNING id
                ''', {
                    'prd_uid': data.get('prd_uid'),
                    'prd_cmp': data.get('prd_cmp'),
                    'prd_flh': data.get('prd_flh', 1),
                    'prd_seq': data.get('prd_seq', 1),
                    'prd_cnsmed': data.get('prd_cnsmed'),
                    'prd_cbo': data.get('prd_cbo'),
                    'prd_ine': data.get('prd_ine', ''),
                    'prd_cnspac': data.get('prd_cnspac'),
                    'prd_cpf_pcnte': data.get('prd_cpf_pcnte'),
                    'prd_nmpac': data.get('prd_nmpac'),
                    'prd_dtnasc': data.get('prd_dtnasc'),
                    'prd_sexo': data.get('prd_sexo'),
                    'prd_raca': data.get('prd_raca', '99'),
                    'prd_nac': data.get('prd_nac', '010'),
                    'prd_ibge': data.get('prd_ibge'),
                    'prd_idade': data.get('prd_idade'),
                    'prd_cep_pcnte': data.get('prd_cep_pcnte'),
                    'prd_lograd_pcnte': data.get('prd_lograd_pcnte'),
                    'prd_end_pcnte': data.get('prd_end_pcnte'),
                    'prd_num_pcnte': data.get('prd_num_pcnte'),
                    'prd_compl_pcnte': data.get('prd_compl_pcnte'),
                    'prd_bairro_pcnte': data.get('prd_bairro_pcnte'),
                    'prd_ddtel_pcnte': data.get('prd_ddtel_pcnte'),
                    'prd_tel_pcnte': data.get('prd_tel_pcnte'),
                    'prd_email_pcnte': data.get('prd_email_pcnte'),
                    'prd_dtaten': data.get('prd_dtaten'),
                    'prd_pa': data.get('prd_pa'),
                    'prd_qt_p': data.get('prd_qt_p', 1),
                    'prd_cid': data.get('prd_cid'),
                    'prd_caten': data.get('prd_caten', '01'),
                    'prd_naut': data.get('prd_naut', ''),
                    'prd_cnpj': data.get('prd_cnpj', ''),
                    'prd_servico': data.get('prd_servico', ''),
                    'prd_classificacao': data.get('prd_classificacao', ''),
                    'prd_etnia': data.get('prd_etnia', ''),
                    'prd_eqp_area': data.get('prd_eqp_area', ''),
                    'prd_eqp_seq': data.get('prd_eqp_seq', ''),
                    'prd_mvm': data.get('prd_mvm') or data.get('prd_cmp'),  # MVM = competência
                    'prd_org': data.get('prd_org', 'BPI')
                })
                result = cursor.fetchone()
                conn.commit()
                
                # Salva paciente no cache
                try:
                    self.save_paciente({
                        'cns': data.get('prd_cnspac'),
                        'cpf': data.get('prd_cpf_pcnte'),
                        'nome': data.get('prd_nmpac'),
                        'data_nascimento': data.get('prd_dtnasc'),
                        'sexo': data.get('prd_sexo'),
                        'raca_cor': data.get('prd_raca', '99'),
                        'nacionalidade': data.get('prd_nac', '010'),
                        'municipio_ibge': data.get('prd_ibge'),
                        'cep': data.get('prd_cep_pcnte'),
                        'logradouro_codigo': data.get('prd_lograd_pcnte'),
                        'endereco': data.get('prd_end_pcnte'),
                        'numero': data.get('prd_num_pcnte'),
                        'complemento': data.get('prd_compl_pcnte'),
                        'bairro': data.get('prd_bairro_pcnte'),
                        'telefone': data.get('prd_tel_pcnte'),
                        'email': data.get('prd_email_pcnte')
                    })
                except Exception as e:
                    logger.warning(f"Erro ao salvar paciente no cache: {e}")
                
                return result['id']
    
    def get_bpa_individualizado(self, id: int) -> Optional[Dict]:
        """Busca BPA-I pelo ID"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM bpa_individualizado WHERE id = %s", (id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def list_bpa_individualizado(self, cnes: str, competencia: str = None, 
                                  exportado: bool = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """Lista registros BPA-I com filtros"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM bpa_individualizado WHERE prd_uid = %s"
                params = [cnes]
                
                if competencia:
                    query += " AND prd_cmp = %s"
                    params.append(competencia)
                
                if exportado is not None:
                    query += " AND prd_exportado = %s"
                    params.append(exportado)
                
                query += " ORDER BY id"
                
                if limit is not None:
                    query += " LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def update_bpa_individualizado(self, id: int, data: Dict) -> bool:
        """Atualiza registro BPA-I"""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                fields = []
                values = []
                for key, value in data.items():
                    if key != 'id':
                        fields.append(f"{key} = %s")
                        values.append(value)
                
                values.append(id)
                query = f"UPDATE bpa_individualizado SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
    
    def delete_bpa_individualizado(self, id: int) -> bool:
        """Remove registro BPA-I"""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM bpa_individualizado WHERE id = %s", (id,))
                conn.commit()
                return cursor.rowcount > 0
    
    def mark_exported_bpai(self, ids: List[int]) -> int:
        """Marca registros BPA-I como exportados"""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE bpa_individualizado 
                    SET prd_exportado = TRUE, data_exportacao = CURRENT_TIMESTAMP
                    WHERE id = ANY(%s)
                ''', (ids,))
                conn.commit()
                return cursor.rowcount
    
    # ========== BPA CONSOLIDADO ==========
    
    def save_bpa_consolidado(self, data: Dict) -> int:
        """Salva registro BPA-C"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO bpa_consolidado (
                        prd_uid, prd_cmp, prd_flh,
                        prd_cnsmed, prd_cbo,
                        prd_pa, prd_qt_p, prd_idade, prd_org
                    ) VALUES (
                        %(prd_uid)s, %(prd_cmp)s, %(prd_flh)s,
                        %(prd_cnsmed)s, %(prd_cbo)s,
                        %(prd_pa)s, %(prd_qt_p)s, %(prd_idade)s, %(prd_org)s
                    )
                    RETURNING id
                ''', {
                    'prd_uid': data.get('prd_uid'),
                    'prd_cmp': data.get('prd_cmp'),
                    'prd_flh': data.get('prd_flh', 1),
                    'prd_cnsmed': data.get('prd_cnsmed'),
                    'prd_cbo': data.get('prd_cbo'),
                    'prd_pa': data.get('prd_pa'),
                    'prd_qt_p': data.get('prd_qt_p', 1),
                    'prd_idade': data.get('prd_idade'),
                    'prd_org': data.get('prd_org', 'BPC')
                })
                result = cursor.fetchone()
                conn.commit()
                return result['id']

    def save_bpa_consolidado_batch(self, records: List[Dict]) -> Dict[str, Any]:
        """Salva múltiplos registros BPA-C agregando e evitando duplicações"""
        if not records:
            return {'success': True, 'saved': 0, 'inserted': 0, 'updated': 0, 'errors': []}

        # Agrega por chave para evitar duplicações no lote
        grouped: Dict[tuple, Dict] = {}
        for rec in records:
            key = (
                rec.get('prd_uid', ''),
                rec.get('prd_cmp', ''),
                rec.get('prd_cbo', ''),
                rec.get('prd_pa', ''),
                rec.get('prd_idade', '000') or '000'
            )
            if key not in grouped:
                grouped[key] = rec.copy()
                grouped[key]['prd_qt_p'] = 0
            grouped[key]['prd_qt_p'] += int(rec.get('prd_qt_p', 1) or 1)

        inserted = 0
        updated = 0
        errors: List[str] = []

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for rec in grouped.values():
                    try:
                        cursor.execute('''
                            SELECT id, prd_qt_p, prd_exportado
                            FROM bpa_consolidado
                            WHERE prd_uid = %s
                              AND prd_cmp = %s
                              AND prd_cbo = %s
                              AND prd_pa = %s
                              AND prd_idade = %s
                              AND prd_exportado = FALSE
                            LIMIT 1
                        ''', (
                            rec.get('prd_uid'),
                            rec.get('prd_cmp'),
                            rec.get('prd_cbo'),
                            rec.get('prd_pa'),
                            rec.get('prd_idade') or '000'
                        ))
                        existing = cursor.fetchone()

                        if existing:
                            cursor.execute('''
                                UPDATE bpa_consolidado
                                SET prd_qt_p = prd_qt_p + %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            ''', (
                                int(rec.get('prd_qt_p', 1) or 1),
                                existing['id']
                            ))
                            updated += 1
                        else:
                            cursor.execute('''
                                INSERT INTO bpa_consolidado (
                                    prd_uid, prd_cmp, prd_flh,
                                    prd_cnsmed, prd_cbo,
                                    prd_pa, prd_qt_p, prd_idade, prd_org
                                ) VALUES (
                                    %(prd_uid)s, %(prd_cmp)s, %(prd_flh)s,
                                    %(prd_cnsmed)s, %(prd_cbo)s,
                                    %(prd_pa)s, %(prd_qt_p)s, %(prd_idade)s, %(prd_org)s
                                )
                            ''', {
                                'prd_uid': rec.get('prd_uid'),
                                'prd_cmp': rec.get('prd_cmp'),
                                'prd_flh': rec.get('prd_flh', 1),
                                'prd_cnsmed': rec.get('prd_cnsmed'),
                                'prd_cbo': rec.get('prd_cbo'),
                                'prd_pa': rec.get('prd_pa'),
                                'prd_qt_p': rec.get('prd_qt_p', 1),
                                'prd_idade': rec.get('prd_idade') or '000',
                                'prd_org': rec.get('prd_org', 'BPC')
                            })
                            inserted += 1
                    except Exception as e:
                        errors.append(str(e))

                conn.commit()

        return {
            'success': len(errors) == 0,
            'saved': inserted + updated,
            'inserted': inserted,
            'updated': updated,
            'errors': errors
        }
    
    def list_bpa_consolidado(self, cnes: str, competencia: str = None,
                              exportado: bool = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """Lista registros BPA-C com filtros"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM bpa_consolidado WHERE prd_uid = %s"
                params = [cnes]
                
                if competencia:
                    query += " AND prd_cmp = %s"
                    params.append(competencia)
                
                if exportado is not None:
                    query += " AND prd_exportado = %s"
                    params.append(exportado)
                
                query += " ORDER BY id"
                
                if limit is not None:
                    query += " LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def mark_exported_bpac(self, ids: List[int]) -> int:
        """Marca registros BPA-C como exportados"""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE bpa_consolidado 
                    SET prd_exportado = TRUE, data_exportacao = CURRENT_TIMESTAMP
                    WHERE id = ANY(%s)
                ''', (ids,))
                conn.commit()
                return cursor.rowcount

    def reset_export_status(self, cnes: str, competencia: str, tipo: str = "all") -> Dict:
        """Reseta status de exportação (prd_exportado/data_exportacao)"""
        results = {
            "bpai_reset": 0,
            "bpac_reset": 0
        }

        if not cnes or not competencia:
            return results

        with get_connection() as conn:
            with conn.cursor() as cursor:
                if tipo in ("all", "bpai", "individualizado", "bpa-i"):
                    cursor.execute('''
                        UPDATE bpa_individualizado
                        SET prd_exportado = FALSE, data_exportacao = NULL
                        WHERE prd_uid = %s AND prd_cmp = %s
                    ''', (cnes, competencia))
                    results["bpai_reset"] = cursor.rowcount

                if tipo in ("all", "bpac", "consolidado", "bpa-c"):
                    cursor.execute('''
                        UPDATE bpa_consolidado
                        SET prd_exportado = FALSE, data_exportacao = NULL
                        WHERE prd_uid = %s AND prd_cmp = %s
                    ''', (cnes, competencia))
                    results["bpac_reset"] = cursor.rowcount

                conn.commit()

        return results
    
    # ========== ESTATÍSTICAS ==========
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas gerais"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                stats = {}
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_individualizado")
                stats['bpai_total'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_individualizado WHERE prd_exportado = FALSE")
                stats['bpai_pendente'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_individualizado WHERE prd_exportado = TRUE")
                stats['bpai_exportado'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_consolidado")
                stats['bpac_total'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_consolidado WHERE prd_exportado = FALSE")
                stats['bpac_pendente'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_consolidado WHERE prd_exportado = TRUE")
                stats['bpac_exportado'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM profissionais")
                stats['total_profissionais'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM pacientes")
                stats['total_pacientes'] = cursor.fetchone()['total']
                
                return stats
    
    def get_stats_by_cnes(self, cnes: str) -> Dict:
        """Obtém estatísticas específicas de um CNES"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                stats = {}
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_individualizado WHERE prd_uid = %s', (cnes,))
                stats['bpai_total'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_individualizado WHERE prd_uid = %s AND prd_exportado = FALSE', (cnes,))
                stats['bpai_pendente'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_individualizado WHERE prd_uid = %s AND prd_exportado = TRUE', (cnes,))
                stats['bpai_exportado'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT DISTINCT prd_cmp FROM bpa_individualizado WHERE prd_uid = %s ORDER BY prd_cmp DESC', (cnes,))
                stats['bpai_competencias'] = [row['prd_cmp'] for row in cursor.fetchall()]
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_consolidado WHERE prd_uid = %s', (cnes,))
                stats['bpac_total'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_consolidado WHERE prd_uid = %s AND prd_exportado = FALSE', (cnes,))
                stats['bpac_pendente'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_consolidado WHERE prd_uid = %s AND prd_exportado = TRUE', (cnes,))
                stats['bpac_exportado'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT DISTINCT prd_cmp FROM bpa_consolidado WHERE prd_uid = %s ORDER BY prd_cmp DESC', (cnes,))
                stats['bpac_competencias'] = [row['prd_cmp'] for row in cursor.fetchall()]
                
                cursor.execute('SELECT COUNT(*) as total FROM profissionais WHERE cnes = %s', (cnes,))
                stats['profissionais'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM pacientes')
                stats['pacientes'] = cursor.fetchone()['total']
                
                stats['ultimas_exportacoes'] = []
                
                return stats
    
    def get_competencias(self, cnes: str) -> List[str]:
        """Lista competências disponíveis para um CNES"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT DISTINCT prd_cmp as competencia FROM (
                        SELECT prd_cmp FROM bpa_individualizado WHERE prd_uid = %s
                        UNION
                        SELECT prd_cmp FROM bpa_consolidado WHERE prd_uid = %s
                    ) t ORDER BY prd_cmp DESC
                ''', (cnes, cnes))
                return [row['competencia'] for row in cursor.fetchall()]
    
    # ========== ESTATÍSTICAS ==========
    
    def get_bpa_stats(self, cnes: str, competencia: str = None) -> Dict:
        """
        Obtém estatísticas de BPA para um CNES e competência
        
        Returns:
            Dict com bpai_total, bpai_pendente, bpai_exportado,
            bpac_total, bpac_pendente, bpac_exportado
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Estatísticas BPA-I
                where_i = "WHERE prd_uid = %s"
                params_i = [cnes]
                if competencia:
                    where_i += " AND prd_cmp = %s"
                    params_i.append(competencia)
                
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN prd_exportado = FALSE THEN 1 ELSE 0 END) as pendente,
                        SUM(CASE WHEN prd_exportado = TRUE THEN 1 ELSE 0 END) as exportado
                    FROM bpa_individualizado
                    {where_i}
                ''', params_i)
                
                bpai = cursor.fetchone()
                
                # Estatísticas BPA-C
                where_c = "WHERE prd_uid = %s"
                params_c = [cnes]
                if competencia:
                    where_c += " AND prd_cmp = %s"
                    params_c.append(competencia)
                
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN prd_exportado = FALSE THEN 1 ELSE 0 END) as pendente,
                        SUM(CASE WHEN prd_exportado = TRUE THEN 1 ELSE 0 END) as exportado
                    FROM bpa_consolidado
                    {where_c}
                ''', params_c)
                
                bpac = cursor.fetchone()
                
                return {
                    'bpai_total': bpai['total'] or 0,
                    'bpai_pendente': bpai['pendente'] or 0,
                    'bpai_exportado': bpai['exportado'] or 0,
                    'bpac_total': bpac['total'] or 0,
                    'bpac_pendente': bpac['pendente'] or 0,
                    'bpac_exportado': bpac['exportado'] or 0
                }

    def get_production_for_dashboard(
        self,
        competencia_inicio: str = None,
        competencia_fim: str = None,
        cnes_list: List[str] = None,
        tipo_bpa: str = None,
        cbo: str = None,
        procedimento: str = None
    ) -> List[Dict]:
        """Agrega produção para dashboard financeiro (BPA-I/BPA-C)"""
        tipo_norm = (tipo_bpa or '').strip().upper()
        only_i = tipo_norm in ['BPA-I', 'BPAI', 'BPI', '02']
        only_c = tipo_norm in ['BPA-C', 'BPAC', 'BPC', '01']

        def build_where() -> tuple[str, List]:
            clauses = []
            params: List[Any] = []
            if competencia_inicio:
                clauses.append("prd_cmp >= %s")
                params.append(competencia_inicio)
            if competencia_fim:
                clauses.append("prd_cmp <= %s")
                params.append(competencia_fim)
            if cnes_list:
                clauses.append("prd_uid = ANY(%s)")
                params.append(cnes_list)
            if cbo:
                clauses.append("prd_cbo = %s")
                params.append(cbo)
            if procedimento:
                clauses.append("prd_pa = %s")
                params.append(procedimento)
            where_sql = " AND ".join(clauses) if clauses else "1=1"
            return where_sql, params

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                where_sql, params = build_where()

                queries = []
                all_params: List[Any] = []

                if not only_c:
                    queries.append(f'''
                        SELECT prd_cmp AS competencia,
                               prd_pa AS procedimento,
                               prd_cbo AS cbo,
                               SUM(prd_qt_p) AS quantidade_total
                        FROM bpa_individualizado
                        WHERE {where_sql}
                        GROUP BY prd_cmp, prd_pa, prd_cbo
                    ''')
                    all_params.extend(params)

                if not only_i:
                    queries.append(f'''
                        SELECT prd_cmp AS competencia,
                               prd_pa AS procedimento,
                               prd_cbo AS cbo,
                               SUM(prd_qt_p) AS quantidade_total
                        FROM bpa_consolidado
                        WHERE {where_sql}
                        GROUP BY prd_cmp, prd_pa, prd_cbo
                    ''')
                    all_params.extend(params)

                if not queries:
                    return []

                if len(queries) == 1:
                    cursor.execute(queries[0], all_params)
                    return [dict(row) for row in cursor.fetchall()]

                union_sql = " UNION ALL ".join(queries)
                final_sql = f'''
                    SELECT competencia, procedimento, cbo, SUM(quantidade_total) AS quantidade_total
                    FROM ({union_sql}) t
                    GROUP BY competencia, procedimento, cbo
                    ORDER BY competencia
                '''
                cursor.execute(final_sql, all_params)
                return [dict(row) for row in cursor.fetchall()]
    
    # ========== EXPORTAÇÃO ==========
    
    def get_bpai_for_export(self, cnes: str, competencia: str) -> List[Dict]:
        """Obtém BPA-I para exportação"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT * FROM bpa_individualizado 
                    WHERE prd_uid = %s AND prd_cmp = %s AND prd_exportado = FALSE
                    ORDER BY prd_flh, prd_seq
                ''', (cnes, competencia))
                return [dict(row) for row in cursor.fetchall()]
    
    def get_bpac_for_export(self, cnes: str, competencia: str) -> List[Dict]:
        """Obtém BPA-C para exportação"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT * FROM bpa_consolidado 
                    WHERE prd_uid = %s AND prd_cmp = %s AND prd_exportado = FALSE
                    ORDER BY prd_flh
                ''', (cnes, competencia))
                return [dict(row) for row in cursor.fetchall()]
    
    def save_exportacao(self, data: Dict) -> int:
        """Registra uma exportação"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO exportacoes (cnes, competencia, tipo, arquivo, total_registros, status, usuario_id)
                    VALUES (%(cnes)s, %(competencia)s, %(tipo)s, %(arquivo)s, %(total_registros)s, %(status)s, %(usuario_id)s)
                    RETURNING id
                ''', data)
                result = cursor.fetchone()
                conn.commit()
                return result['id']
    
    # ========== HISTÓRICO DE EXTRAÇÕES ==========
    
    def save_historico_extracao(self, data: Dict) -> int:
        """Salva histórico de extração"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                import json
                cursor.execute('''
                    INSERT INTO historico_extracoes (
                        cnes, competencia, 
                        total_bpa_i, total_bpa_c, total_removido, total_geral,
                        valor_total_bpa_i, valor_total_bpa_c, valor_total_geral,
                        procedimentos_mais_usados, profissionais_mais_ativos, distribuicao_por_dia,
                        usuario_id, duracao_segundos, status, erro
                    ) VALUES (
                        %(cnes)s, %(competencia)s,
                        %(total_bpa_i)s, %(total_bpa_c)s, %(total_removido)s, %(total_geral)s,
                        %(valor_total_bpa_i)s, %(valor_total_bpa_c)s, %(valor_total_geral)s,
                        %(procedimentos_mais_usados)s, %(profissionais_mais_ativos)s, %(distribuicao_por_dia)s,
                        %(usuario_id)s, %(duracao_segundos)s, %(status)s, %(erro)s
                    )
                    RETURNING id
                ''', {
                    'cnes': data.get('cnes'),
                    'competencia': data.get('competencia'),
                    'total_bpa_i': data.get('total_bpa_i', 0),
                    'total_bpa_c': data.get('total_bpa_c', 0),
                    'total_removido': data.get('total_removido', 0),
                    'total_geral': data.get('total_geral', 0),
                    'valor_total_bpa_i': data.get('valor_total_bpa_i', 0.0),
                    'valor_total_bpa_c': data.get('valor_total_bpa_c', 0.0),
                    'valor_total_geral': data.get('valor_total_geral', 0.0),
                    'procedimentos_mais_usados': json.dumps(data.get('procedimentos_mais_usados', [])),
                    'profissionais_mais_ativos': json.dumps(data.get('profissionais_mais_ativos', [])),
                    'distribuicao_por_dia': json.dumps(data.get('distribuicao_por_dia', {})),
                    'usuario_id': data.get('usuario_id'),
                    'duracao_segundos': data.get('duracao_segundos', 0),
                    'status': data.get('status', 'concluido'),
                    'erro': data.get('erro')
                })
                result = cursor.fetchone()
                conn.commit()
                return result['id']
    
    def list_historico_extracoes(self, cnes: str = None, limit: int = 50, offset: int = 0) -> Dict:
        """Lista histórico de extrações com paginação"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Query base - usar h.cnes para evitar ambiguidade
                where_clause = "WHERE h.cnes = %s" if cnes else ""
                params_count = [cnes] if cnes else []
                params_data = [cnes] if cnes else []
                params_data.extend([limit, offset])
                
                # Conta total
                cursor.execute(f'''
                    SELECT COUNT(*) as total FROM historico_extracoes h {where_clause}
                ''', params_count)
                total = cursor.fetchone()['total']
                
                # Busca dados paginados
                cursor.execute(f'''
                    SELECT 
                        h.*,
                        u.nome as usuario_nome
                    FROM historico_extracoes h
                    LEFT JOIN usuarios u ON h.usuario_id = u.id
                    {where_clause}
                    ORDER BY h.created_at DESC
                    LIMIT %s OFFSET %s
                ''', params_data)
                
                records = []
                for row in cursor.fetchall():
                    record = dict(row)
                    # Converte JSONB para dict
                    import json
                    if record.get('procedimentos_mais_usados'):
                        record['procedimentos_mais_usados'] = json.loads(record['procedimentos_mais_usados']) if isinstance(record['procedimentos_mais_usados'], str) else record['procedimentos_mais_usados']
                    if record.get('profissionais_mais_ativos'):
                        record['profissionais_mais_ativos'] = json.loads(record['profissionais_mais_ativos']) if isinstance(record['profissionais_mais_ativos'], str) else record['profissionais_mais_ativos']
                    if record.get('distribuicao_por_dia'):
                        record['distribuicao_por_dia'] = json.loads(record['distribuicao_por_dia']) if isinstance(record['distribuicao_por_dia'], str) else record['distribuicao_por_dia']
                    records.append(record)
                
                return {
                    'total': total,
                    'records': records,
                    'limit': limit,
                    'offset': offset
                }
    
    def fix_encoding_historico(self, sigtap_parser=None) -> Dict:
        """
        Corrige encoding dos nomes de procedimentos no histórico.
        Se sigtap_parser for fornecido, atualiza os nomes do SIGTAP diretamente.
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                import json
                
                # Se temos parser, monta mapa de nomes corretos
                procs_map = {}
                if sigtap_parser:
                    try:
                        procs_map = {
                            p['CO_PROCEDIMENTO']: p['NO_PROCEDIMENTO']
                            for p in sigtap_parser.parse_procedimentos()
                        }
                    except:
                        pass
                
                # Busca todos os registros com procedimentos
                cursor.execute('''
                    SELECT id, procedimentos_mais_usados 
                    FROM historico_extracoes 
                    WHERE procedimentos_mais_usados IS NOT NULL
                ''')
                
                updated = 0
                for row in cursor.fetchall():
                    procs = row['procedimentos_mais_usados']
                    if isinstance(procs, str):
                        procs = json.loads(procs)
                    
                    modified = False
                    for proc in procs:
                        codigo = proc.get('codigo', '')
                        nome_orig = proc.get('nome', '')
                        
                        # Se temos o nome correto no SIGTAP, usa
                        if codigo in procs_map:
                            nome_correto = procs_map[codigo]
                            if nome_orig != nome_correto:
                                proc['nome'] = nome_correto
                                modified = True
                        # Senão, tenta corrigir caracteres corrompidos
                        elif '�' in nome_orig or '\ufffd' in nome_orig:
                            # Não podemos recuperar, marca como desconhecido
                            proc['nome'] = f"PROCEDIMENTO {codigo}"
                            modified = True
                    
                    if modified:
                        cursor.execute('''
                            UPDATE historico_extracoes 
                            SET procedimentos_mais_usados = %s
                            WHERE id = %s
                        ''', (json.dumps(procs), row['id']))
                        updated += 1
                
                conn.commit()
                return {'updated': updated, 'had_sigtap': bool(procs_map)}


# Flag para garantir inicialização única
_db_initialized = False

def ensure_database_initialized():
    """Garante que banco foi inicializado (chamado sob demanda)"""
    global _db_initialized
    if not _db_initialized:
        init_database()
        _db_initialized = True

# Singleton - inicializado quando importado
db = BPADatabase()
