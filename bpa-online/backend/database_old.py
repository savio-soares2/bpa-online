"""
BPA Online - Banco de Dados PostgreSQL
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
            # Fallback para conexão direta
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
    """Inicializa as tabelas do banco de dados"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Extensão UUID
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
            
            # Tabela BPA Individualizado
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bpa_individualizado (
                    id SERIAL PRIMARY KEY,
                    cnes VARCHAR(7) NOT NULL,
                    competencia VARCHAR(6) NOT NULL,
                    folha INTEGER DEFAULT 1,
                    sequencia INTEGER DEFAULT 1,
                    
                    cns_profissional VARCHAR(15) NOT NULL,
                    cbo VARCHAR(6) NOT NULL,
                    ine VARCHAR(10),
                    
                    cns_paciente VARCHAR(15) NOT NULL,
                    cpf_paciente VARCHAR(11),
                    nome_paciente VARCHAR(255) NOT NULL,
                    data_nascimento VARCHAR(8) NOT NULL,
                    sexo VARCHAR(1) NOT NULL,
                    raca_cor VARCHAR(2) DEFAULT '99',
                    nacionalidade VARCHAR(3) DEFAULT '010',
                    municipio_ibge VARCHAR(6) NOT NULL,
                    
                    cep VARCHAR(8),
                    logradouro_codigo VARCHAR(10),
                    endereco VARCHAR(255),
                    numero VARCHAR(10),
                    complemento VARCHAR(100),
                    bairro VARCHAR(100),
                    telefone VARCHAR(20),
                    email VARCHAR(255),
                    
                    data_atendimento VARCHAR(8) NOT NULL,
                    procedimento VARCHAR(10) NOT NULL,
                    quantidade INTEGER DEFAULT 1,
                    cid VARCHAR(10),
                    carater_atendimento VARCHAR(2) DEFAULT '01',
                    numero_autorizacao VARCHAR(20),
                    cnpj VARCHAR(14),
                    servico VARCHAR(3),
                    classificacao VARCHAR(3),
                    
                    origem VARCHAR(10) DEFAULT 'BPI',
                    exportado BOOLEAN DEFAULT FALSE,
                    data_exportacao TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices BPA-I
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_cnes ON bpa_individualizado(cnes)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_competencia ON bpa_individualizado(competencia)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_cnes_comp ON bpa_individualizado(cnes, competencia)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpai_exportado ON bpa_individualizado(exportado)')
            
            # Tabela BPA Consolidado
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bpa_consolidado (
                    id SERIAL PRIMARY KEY,
                    cnes VARCHAR(7) NOT NULL,
                    competencia VARCHAR(6) NOT NULL,
                    folha INTEGER DEFAULT 1,
                    
                    cns_profissional VARCHAR(15) NOT NULL,
                    cbo VARCHAR(6) NOT NULL,
                    
                    procedimento VARCHAR(10) NOT NULL,
                    quantidade INTEGER DEFAULT 1,
                    idade VARCHAR(3),
                    
                    origem VARCHAR(10) DEFAULT 'BPC',
                    exportado BOOLEAN DEFAULT FALSE,
                    data_exportacao TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices BPA-C
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpac_cnes ON bpa_consolidado(cnes)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpac_competencia ON bpa_consolidado(competencia)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpac_exportado ON bpa_consolidado(exportado)')
            
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
            print("[DB] Tabelas PostgreSQL inicializadas com sucesso")


class BPADatabase:
    """Classe principal de acesso ao banco de dados PostgreSQL"""
    
    def __init__(self):
        init_database()
    
    # ========== PROFISSIONAIS ==========
    
    def save_profissional(self, data: Dict) -> int:
        """Salva ou atualiza profissional"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO profissionais (cnes, cns, cpf, nome, cbo, ine, vinculo)
                    VALUES (%(cnes)s, %(cns)s, %(cpf)s, %(nome)s, %(cbo)s, %(ine)s, %(vinculo)s)
                    ON CONFLICT (cnes, cns) DO UPDATE SET
                        cpf = EXCLUDED.cpf,
                        nome = EXCLUDED.nome,
                        cbo = EXCLUDED.cbo,
                        ine = EXCLUDED.ine,
                        vinculo = EXCLUDED.vinculo,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                ''', {
                    'cnes': data.get('cnes'),
                    'cns': data.get('cns'),
                    'cpf': data.get('cpf'),
                    'nome': data.get('nome'),
                    'cbo': data.get('cbo'),
                    'ine': data.get('ine'),
                    'vinculo': data.get('vinculo')
                })
                result = cursor.fetchone()
                conn.commit()
                return result['id']
    
    def get_profissional(self, cns: str) -> Optional[Dict]:
        """Busca profissional pelo CNS"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM profissionais WHERE cns = %s", (cns,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def list_profissionais(self, cnes: str) -> List[Dict]:
        """Lista profissionais do CNES"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM profissionais WHERE cnes = %s ORDER BY nome",
                    (cnes,)
                )
                return [dict(row) for row in cursor.fetchall()]
    
    # ========== PACIENTES ==========
    
    def save_paciente(self, data: Dict) -> int:
        """Salva ou atualiza paciente"""
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
                        cpf = EXCLUDED.cpf,
                        nome = EXCLUDED.nome,
                        data_nascimento = EXCLUDED.data_nascimento,
                        sexo = EXCLUDED.sexo,
                        raca_cor = EXCLUDED.raca_cor,
                        nacionalidade = EXCLUDED.nacionalidade,
                        municipio_ibge = EXCLUDED.municipio_ibge,
                        cep = EXCLUDED.cep,
                        logradouro_codigo = EXCLUDED.logradouro_codigo,
                        endereco = EXCLUDED.endereco,
                        numero = EXCLUDED.numero,
                        complemento = EXCLUDED.complemento,
                        bairro = EXCLUDED.bairro,
                        telefone = EXCLUDED.telefone,
                        email = EXCLUDED.email,
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
    
    def search_pacientes(self, termo: str, limit: int = 20) -> List[Dict]:
        """Busca pacientes por nome ou CNS"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT * FROM pacientes 
                    WHERE nome ILIKE %s OR cns LIKE %s
                    ORDER BY nome
                    LIMIT %s
                ''', (f'%{termo}%', f'%{termo}%', limit))
                return [dict(row) for row in cursor.fetchall()]
    
    # ========== BPA INDIVIDUALIZADO ==========
    
    def save_bpa_individualizado(self, data: Dict) -> int:
        """Salva registro BPA-I"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    INSERT INTO bpa_individualizado (
                        cnes, competencia, folha, sequencia,
                        cns_profissional, cbo, ine,
                        cns_paciente, cpf_paciente, nome_paciente, data_nascimento,
                        sexo, raca_cor, nacionalidade, municipio_ibge, idade,
                        cep, logradouro_codigo, endereco, numero, complemento, bairro, 
                        telefone, ddd_telefone, email,
                        data_atendimento, procedimento, quantidade, cid, carater_atendimento,
                        numero_autorizacao, cnpj, servico, classificacao, 
                        etnia, equipe_area, equipe_seq, origem
                    ) VALUES (
                        %(cnes)s, %(competencia)s, %(folha)s, %(sequencia)s,
                        %(cns_profissional)s, %(cbo)s, %(ine)s,
                        %(cns_paciente)s, %(cpf_paciente)s, %(nome_paciente)s, %(data_nascimento)s,
                        %(sexo)s, %(raca_cor)s, %(nacionalidade)s, %(municipio_ibge)s, %(idade)s,
                        %(cep)s, %(logradouro_codigo)s, %(endereco)s, %(numero)s, %(complemento)s, 
                        %(bairro)s, %(telefone)s, %(ddd_telefone)s, %(email)s,
                        %(data_atendimento)s, %(procedimento)s, %(quantidade)s, %(cid)s, %(carater_atendimento)s,
                        %(numero_autorizacao)s, %(cnpj)s, %(servico)s, %(classificacao)s,
                        %(etnia)s, %(equipe_area)s, %(equipe_seq)s, %(origem)s
                    )
                    RETURNING id
                ''', {
                    'cnes': data.get('cnes'),
                    'competencia': data.get('competencia'),
                    'folha': data.get('folha', 1),
                    'sequencia': data.get('sequencia', 1),
                    'cns_profissional': data.get('cns_profissional'),
                    'cbo': data.get('cbo'),
                    'ine': data.get('ine'),
                    'cns_paciente': data.get('cns_paciente'),
                    'cpf_paciente': data.get('cpf_paciente'),
                    'nome_paciente': data.get('nome_paciente'),
                    'data_nascimento': data.get('data_nascimento'),
                    'sexo': data.get('sexo'),
                    'raca_cor': data.get('raca_cor', '99'),
                    'nacionalidade': data.get('nacionalidade', '010'),
                    'municipio_ibge': data.get('municipio_ibge'),
                    'idade': data.get('idade'),
                    'cep': data.get('cep'),
                    'logradouro_codigo': data.get('logradouro_codigo'),
                    'endereco': data.get('endereco'),
                    'numero': data.get('numero'),
                    'complemento': data.get('complemento'),
                    'bairro': data.get('bairro'),
                    'telefone': data.get('telefone'),
                    'ddd_telefone': data.get('ddd_telefone'),
                    'email': data.get('email'),
                    'data_atendimento': data.get('data_atendimento'),
                    'procedimento': data.get('procedimento'),
                    'quantidade': data.get('quantidade', 1),
                    'cid': data.get('cid'),
                    'carater_atendimento': data.get('carater_atendimento', '01'),
                    'numero_autorizacao': data.get('numero_autorizacao'),
                    'cnpj': data.get('cnpj'),
                    'servico': data.get('servico'),
                    'classificacao': data.get('classificacao'),
                    'etnia': data.get('etnia'),
                    'equipe_area': data.get('equipe_area'),
                    'equipe_seq': data.get('equipe_seq'),
                    'origem': data.get('origem', 'BPI')
                })
                result = cursor.fetchone()
                conn.commit()
                
                # Salva paciente no cache
                try:
                    self.save_paciente({
                        'cns': data.get('cns_paciente'),
                        'cpf': data.get('cpf_paciente'),
                        'nome': data.get('nome_paciente'),
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
                except Exception as e:
                    logger.warning(f"Erro ao salvar paciente no cache: {e}")
                
                return result['id']
    
    def save_bpa_individualizado_batch(self, records: List[Dict]) -> Dict:
        """Salva múltiplos registros BPA-I em batch"""
        saved = 0
        errors = []
        
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for i, data in enumerate(records):
                    try:
                        cursor.execute('''
                            INSERT INTO bpa_individualizado (
                                cnes, competencia, folha, sequencia,
                                cns_profissional, cbo, ine,
                                cns_paciente, cpf_paciente, nome_paciente, data_nascimento,
                                sexo, raca_cor, nacionalidade, municipio_ibge,
                                cep, logradouro_codigo, endereco, numero, complemento, 
                                bairro, telefone, email,
                                data_atendimento, procedimento, quantidade, cid, carater_atendimento,
                                numero_autorizacao, cnpj, servico, classificacao, origem
                            ) VALUES (
                                %(cnes)s, %(competencia)s, %(folha)s, %(sequencia)s,
                                %(cns_profissional)s, %(cbo)s, %(ine)s,
                                %(cns_paciente)s, %(cpf_paciente)s, %(nome_paciente)s, %(data_nascimento)s,
                                %(sexo)s, %(raca_cor)s, %(nacionalidade)s, %(municipio_ibge)s,
                                %(cep)s, %(logradouro_codigo)s, %(endereco)s, %(numero)s, %(complemento)s,
                                %(bairro)s, %(telefone)s, %(email)s,
                                %(data_atendimento)s, %(procedimento)s, %(quantidade)s, %(cid)s, %(carater_atendimento)s,
                                %(numero_autorizacao)s, %(cnpj)s, %(servico)s, %(classificacao)s, %(origem)s
                            )
                        ''', {
                            'cnes': data['cnes'],
                            'competencia': data['competencia'],
                            'folha': data.get('folha', 1),
                            'sequencia': data.get('sequencia', i + 1),
                            'cns_profissional': data['cns_profissional'],
                            'cbo': data['cbo'],
                            'ine': data.get('ine'),
                            'cns_paciente': data['cns_paciente'],
                            'cpf_paciente': data.get('cpf_paciente'),
                            'nome_paciente': data['nome_paciente'],
                            'data_nascimento': data['data_nascimento'],
                            'sexo': data['sexo'],
                            'raca_cor': data.get('raca_cor', '99'),
                            'nacionalidade': data.get('nacionalidade', '010'),
                            'municipio_ibge': data['municipio_ibge'],
                            'cep': data.get('cep'),
                            'logradouro_codigo': data.get('logradouro_codigo'),
                            'endereco': data.get('endereco'),
                            'numero': data.get('numero'),
                            'complemento': data.get('complemento'),
                            'bairro': data.get('bairro'),
                            'telefone': data.get('telefone'),
                            'email': data.get('email'),
                            'data_atendimento': data['data_atendimento'],
                            'procedimento': data['procedimento'],
                            'quantidade': data.get('quantidade', 1),
                            'cid': data.get('cid'),
                            'carater_atendimento': data.get('carater_atendimento', '01'),
                            'numero_autorizacao': data.get('numero_autorizacao'),
                            'cnpj': data.get('cnpj'),
                            'servico': data.get('servico'),
                            'classificacao': data.get('classificacao'),
                            'origem': data.get('origem', 'BPI')
                        })
                        saved += 1
                    except Exception as e:
                        errors.append(f"Registro {i+1}: {str(e)}")
                
                conn.commit()
        
        return {"saved": saved, "errors": errors}
    
    def get_bpa_individualizado(self, id: int) -> Optional[Dict]:
        """Busca BPA-I pelo ID"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM bpa_individualizado WHERE id = %s", (id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def list_bpa_individualizado(self, cnes: str, competencia: str = None, 
                                  exportado: bool = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Lista registros BPA-I com filtros"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM bpa_individualizado WHERE cnes = %s"
                params = [cnes]
                
                if competencia:
                    query += " AND competencia = %s"
                    params.append(competencia)
                
                if exportado is not None:
                    query += " AND exportado = %s"
                    params.append(exportado)
                
                query += " ORDER BY id DESC LIMIT %s OFFSET %s"
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
                    SET exportado = TRUE, data_exportacao = CURRENT_TIMESTAMP
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
                        cnes, competencia, folha,
                        cns_profissional, cbo,
                        procedimento, quantidade, idade, origem
                    ) VALUES (
                        %(cnes)s, %(competencia)s, %(folha)s,
                        %(cns_profissional)s, %(cbo)s,
                        %(procedimento)s, %(quantidade)s, %(idade)s, %(origem)s
                    )
                    RETURNING id
                ''', {
                    'cnes': data['cnes'],
                    'competencia': data['competencia'],
                    'folha': data.get('folha', 1),
                    'cns_profissional': data['cns_profissional'],
                    'cbo': data['cbo'],
                    'procedimento': data['procedimento'],
                    'quantidade': data.get('quantidade', 1),
                    'idade': data.get('idade'),
                    'origem': data.get('origem', 'BPC')
                })
                result = cursor.fetchone()
                conn.commit()
                return result['id']
    
    def list_bpa_consolidado(self, cnes: str, competencia: str = None,
                              exportado: bool = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Lista registros BPA-C com filtros"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM bpa_consolidado WHERE cnes = %s"
                params = [cnes]
                
                if competencia:
                    query += " AND competencia = %s"
                    params.append(competencia)
                
                if exportado is not None:
                    query += " AND exportado = %s"
                    params.append(exportado)
                
                query += " ORDER BY id DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def mark_exported_bpac(self, ids: List[int]) -> int:
        """Marca registros BPA-C como exportados"""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE bpa_consolidado 
                    SET exportado = TRUE, data_exportacao = CURRENT_TIMESTAMP
                    WHERE id = ANY(%s)
                ''', (ids,))
                conn.commit()
                return cursor.rowcount
    
    # ========== ESTATÍSTICAS ==========
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas gerais"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                stats = {}
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_individualizado")
                stats['bpai_total'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_individualizado WHERE exportado = FALSE")
                stats['bpai_pendente'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_individualizado WHERE exportado = TRUE")
                stats['bpai_exportado'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_consolidado")
                stats['bpac_total'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_consolidado WHERE exportado = FALSE")
                stats['bpac_pendente'] = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM bpa_consolidado WHERE exportado = TRUE")
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
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_individualizado WHERE cnes = %s', (cnes,))
                stats['bpai_total'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_individualizado WHERE cnes = %s AND exportado = FALSE', (cnes,))
                stats['bpai_pendente'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_individualizado WHERE cnes = %s AND exportado = TRUE', (cnes,))
                stats['bpai_exportado'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT DISTINCT competencia FROM bpa_individualizado WHERE cnes = %s ORDER BY competencia DESC', (cnes,))
                stats['bpai_competencias'] = [row['competencia'] for row in cursor.fetchall()]
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_consolidado WHERE cnes = %s', (cnes,))
                stats['bpac_total'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_consolidado WHERE cnes = %s AND exportado = FALSE', (cnes,))
                stats['bpac_pendente'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(*) as total FROM bpa_consolidado WHERE cnes = %s AND exportado = TRUE', (cnes,))
                stats['bpac_exportado'] = cursor.fetchone()['total']
                
                cursor.execute('SELECT DISTINCT competencia FROM bpa_consolidado WHERE cnes = %s ORDER BY competencia DESC', (cnes,))
                stats['bpac_competencias'] = [row['competencia'] for row in cursor.fetchall()]
                
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
                    SELECT DISTINCT competencia FROM (
                        SELECT competencia FROM bpa_individualizado WHERE cnes = %s
                        UNION
                        SELECT competencia FROM bpa_consolidado WHERE cnes = %s
                    ) t ORDER BY competencia DESC
                ''', (cnes, cnes))
                return [row['competencia'] for row in cursor.fetchall()]
    
    # ========== EXPORTAÇÃO ==========
    
    def get_bpai_for_export(self, cnes: str, competencia: str) -> List[Dict]:
        """Obtém BPA-I para exportação"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT * FROM bpa_individualizado 
                    WHERE cnes = %s AND competencia = %s AND exportado = FALSE
                    ORDER BY folha, sequencia
                ''', (cnes, competencia))
                return [dict(row) for row in cursor.fetchall()]
    
    def get_bpac_for_export(self, cnes: str, competencia: str) -> List[Dict]:
        """Obtém BPA-C para exportação"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT * FROM bpa_consolidado 
                    WHERE cnes = %s AND competencia = %s AND exportado = FALSE
                    ORDER BY folha
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


# Singleton - inicializado quando importado
db = BPADatabase()
