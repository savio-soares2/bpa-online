"""
Módulo de Autenticação - JWT + Usuários
"""
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps

# JWT simples sem dependências externas
import base64
import json
import hmac

SECRET_KEY = os.environ.get("SECRET_KEY", "bpa-online-secret-key-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

DB_PATH = os.path.join(os.path.dirname(__file__), "bpa_local.db")


def get_db():
    """Conexão com o banco"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_tables():
    """Cria tabelas de autenticação"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cbo TEXT,
            cnes TEXT,
            nome_unidade TEXT,
            is_admin INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migração para adicionar coluna CBO se não existir
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN cbo TEXT")
    except:
        pass  # Coluna já existe
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    
    # Cria admin padrão se não existir
    cursor.execute("SELECT id FROM usuarios WHERE email = 'admin@bpa.local'")
    if not cursor.fetchone():
        admin_hash = hash_password("admin123")
        cursor.execute("""
            INSERT INTO usuarios (email, senha_hash, nome, cnes, nome_unidade, is_admin)
            VALUES ('admin@bpa.local', ?, 'Administrador', '', 'Sistema BPA', 1)
        """, (admin_hash,))
        print("[AUTH] Usuário admin criado: admin@bpa.local / admin123")
    
    conn.commit()
    conn.close()
    print("[AUTH] Tabelas de autenticação inicializadas")


def hash_password(password: str) -> str:
    """Hash da senha com salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hash_obj.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica senha"""
    try:
        salt, hash_value = stored_hash.split(':')
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == hash_value
    except:
        return False


def create_jwt_token(data: dict, expires_delta: timedelta = None) -> str:
    """Cria token JWT simples"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        **data,
        "exp": expire.isoformat()
    }
    
    # Header
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    
    # Payload
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Signature
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt_token(token: str) -> Optional[dict]:
    """Decodifica e valida token JWT"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Verifica assinatura
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
        
        if signature_b64 != expected_sig_b64:
            return None
        
        # Decodifica payload
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Verifica expiração
        exp = datetime.fromisoformat(payload.get('exp', ''))
        if datetime.utcnow() > exp:
            return None
        
        return payload
    except Exception as e:
        print(f"[AUTH] Erro ao decodificar token: {e}")
        return None


# ========== CRUD Usuários ==========

def create_user(email: str, senha: str, nome: str, cbo: str = None, cnes: str = None, nome_unidade: str = None, is_admin: bool = False) -> dict:
    """Cria novo usuário"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verifica se email já existe
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email já cadastrado")
    
    senha_hash = hash_password(senha)
    
    cursor.execute("""
        INSERT INTO usuarios (email, senha_hash, nome, cbo, cnes, nome_unidade, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email, senha_hash, nome, cbo or '', cnes or '', nome_unidade, 1 if is_admin else 0))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": user_id,
        "email": email,
        "nome": nome,
        "cbo": cbo,
        "cnes": cnes,
        "nome_unidade": nome_unidade,
        "is_admin": is_admin
    }


def authenticate_user(email: str, senha: str) -> Optional[dict]:
    """Autentica usuário"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, senha_hash, nome, cbo, cnes, nome_unidade, is_admin, ativo
        FROM usuarios WHERE email = ?
    """, (email,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    if not row['ativo']:
        return None
    
    if not verify_password(senha, row['senha_hash']):
        return None
    
    return {
        "id": row['id'],
        "email": row['email'],
        "nome": row['nome'],
        "cbo": row['cbo'],
        "cnes": row['cnes'],
        "nome_unidade": row['nome_unidade'],
        "is_admin": bool(row['is_admin'])
    }


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Busca usuário por ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, nome, cbo, cnes, nome_unidade, is_admin, ativo, created_at
        FROM usuarios WHERE id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return dict(row)


def get_user_by_email(email: str) -> Optional[dict]:
    """Busca usuário por email"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, nome, cbo, cnes, nome_unidade, is_admin, ativo, created_at
        FROM usuarios WHERE email = ?
    """, (email,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return dict(row)


def update_user(user_id: int, nome: str = None, nome_unidade: str = None) -> bool:
    """Atualiza dados do usuário"""
    conn = get_db()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if nome:
        updates.append("nome = ?")
        params.append(nome)
    
    if nome_unidade:
        updates.append("nome_unidade = ?")
        params.append(nome_unidade)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)
    
    cursor.execute(f"""
        UPDATE usuarios SET {', '.join(updates)} WHERE id = ?
    """, params)
    
    conn.commit()
    conn.close()
    return True


def change_password(user_id: int, senha_atual: str, nova_senha: str) -> bool:
    """Altera senha do usuário"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT senha_hash FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row or not verify_password(senha_atual, row['senha_hash']):
        conn.close()
        return False
    
    nova_hash = hash_password(nova_senha)
    cursor.execute("""
        UPDATE usuarios SET senha_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (nova_hash, user_id))
    
    conn.commit()
    conn.close()
    return True


# ========== Funções de Admin ==========

def list_users() -> list:
    """Lista todos os usuários (admin)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, nome, cbo, cnes, nome_unidade, is_admin, ativo, created_at
        FROM usuarios ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def toggle_user_status(user_id: int, ativo: bool) -> bool:
    """Ativa/desativa usuário"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE usuarios SET ativo = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (1 if ativo else 0, user_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def delete_user(user_id: int) -> bool:
    """Remove usuário"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Não permite deletar admin principal
    cursor.execute("SELECT is_admin FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row['is_admin']:
        conn.close()
        return False
    
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def reset_user_password(user_id: int, nova_senha: str) -> bool:
    """Reset de senha pelo admin"""
    conn = get_db()
    cursor = conn.cursor()
    
    nova_hash = hash_password(nova_senha)
    cursor.execute("""
        UPDATE usuarios SET senha_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (nova_hash, user_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def update_user(user_id: int, updates: dict) -> Optional[dict]:
    """Atualiza dados do usuário"""
    if not updates:
        return None
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Constrói query de update dinamicamente
    fields = []
    values = []
    
    allowed_fields = ['nome', 'email', 'cbo', 'cnes', 'nome_unidade', 'ativo']
    
    for field, value in updates.items():
        if field in allowed_fields:
            fields.append(f"{field} = ?")
            if field == 'ativo' and isinstance(value, bool):
                values.append(1 if value else 0)
            else:
                values.append(value)
    
    if not fields:
        conn.close()
        return None
        
    # Adiciona timestamp de atualização
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(user_id)
    
    query = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = ?"
    
    try:
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount > 0:
            # Retorna o usuário atualizado
            cursor.execute("""
                SELECT id, email, nome, cbo, cnes, nome_unidade, is_admin, ativo, created_at
                FROM usuarios WHERE id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
        else:
            conn.close()
            return None
            
    except Exception as e:
        conn.close()
        raise ValueError(f"Erro ao atualizar usuário: {str(e)}")


# Inicializa tabelas ao importar
init_auth_tables()
