import os
import sqlite3
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from models.user_schemas import UsuarioCreate, UsuarioResponse, LoginResponse
from services.dbf_manager_service import DBFManagerService
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Serviço de gerenciamento de usuários com integração DBF"""
    
    def __init__(self, db_path: str = None):
        """
        Inicializa o serviço de usuários
        
        Args:
            db_path: Caminho do banco SQLite. Se None, usa o padrão
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'users.db'
        )
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.token_expires_hours = 24
        
        # Inicializa DBF Manager
        self.dbf_manager = DBFManagerService()
        
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Inicializa banco
        self._init_database()
    
    def _init_database(self):
        """Inicializa as tabelas do banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    cbo TEXT NOT NULL,
                    cnes TEXT,
                    perfil TEXT DEFAULT 'user',
                    ativo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    revoked BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES usuarios (id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_username ON usuarios(username);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cbo ON usuarios(cbo);
            """)
            
            conn.commit()
            
        logger.info("Banco de dados de usuários inicializado")
    
    def _hash_password(self, password: str) -> str:
        """Gera hash da senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hash_stored: str) -> bool:
        """Verifica senha"""
        return hashlib.sha256(password.encode()).hexdigest() == hash_stored
    
    def _generate_token(self, user_id: int, username: str) -> str:
        """Gera token JWT"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expires_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decodifica token JWT"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token inválido")
            return None
    
    def create_user(self, user_data: UsuarioCreate) -> UsuarioResponse:
        """
        Cria um novo usuário
        
        Args:
            user_data: Dados do usuário
            
        Returns:
            Usuário criado
            
        Raises:
            ValueError: Se o CBO não for válido ou dados inválidos
        """
        # Valida se o CBO existe nos DBFs
        procedimentos_cbo = self.dbf_manager.get_procedimentos_for_cbo(user_data.cbo)
        if not procedimentos_cbo:
            raise ValueError(f"CBO {user_data.cbo} não encontrado nas tabelas DBF ou não possui procedimentos associados")
        
        logger.info(f"CBO {user_data.cbo} validado com {len(procedimentos_cbo)} procedimentos")
        
        # Hash da senha
        password_hash = self._hash_password(user_data.password)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO usuarios (username, email, password_hash, nome, cbo, cnes, perfil, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data.username,
                    user_data.email,
                    password_hash,
                    user_data.nome,
                    user_data.cbo,
                    user_data.cnes,
                    user_data.perfil,
                    user_data.ativo
                ))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Usuário criado: {user_data.username} (ID: {user_id})")
                
                # Retorna o usuário criado
                return self.get_user_by_id(user_id)
                
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValueError("Nome de usuário já existe")
            elif "email" in str(e):
                raise ValueError("E-mail já cadastrado")
            else:
                raise ValueError("Erro ao criar usuário")
    
    def authenticate(self, username: str, password: str) -> Optional[LoginResponse]:
        """
        Autentica usuário e retorna token
        
        Args:
            username: Nome do usuário
            password: Senha
            
        Returns:
            Dados de login ou None se inválido
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM usuarios 
                WHERE username = ? AND ativo = 1
            """, (username,))
            
            user_row = cursor.fetchone()
            
        if not user_row:
            logger.warning(f"Usuário não encontrado ou inativo: {username}")
            return None
        
        if not self._verify_password(password, user_row['password_hash']):
            logger.warning(f"Senha incorreta para usuário: {username}")
            return None
        
        # Atualiza último login
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE usuarios SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (user_row['id'],))
            conn.commit()
        
        # Gera token
        token = self._generate_token(user_row['id'], user_row['username'])
        
        # Salva sessão
        expires_at = datetime.utcnow() + timedelta(hours=self.token_expires_hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO user_sessions (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user_row['id'], token, expires_at))
            conn.commit()
        
        # Obtém procedimentos permitidos para o CBO do usuário
        procedimentos_permitidos = self.dbf_manager.get_procedimentos_for_cbo(user_row['cbo'])
        
        user_response = UsuarioResponse(
            id=user_row['id'],
            username=user_row['username'],
            email=user_row['email'],
            nome=user_row['nome'],
            cbo=user_row['cbo'],
            cnes=user_row['cnes'],
            perfil=user_row['perfil'],
            ativo=user_row['ativo'],
            created_at=user_row['created_at'],
            last_login=user_row['last_login']
        )
        
        logger.info(f"Login realizado: {username} com {len(procedimentos_permitidos)} procedimentos permitidos")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=user_response,
            procedimentos_permitidos=procedimentos_permitidos
        )
    
    def get_user_by_token(self, token: str) -> Optional[UsuarioResponse]:
        """
        Obtém usuário pelo token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Usuário ou None se inválido
        """
        payload = self._decode_token(token)
        if not payload:
            return None
        
        # Verifica se a sessão não foi revogada
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT s.*, u.* FROM user_sessions s
                JOIN usuarios u ON s.user_id = u.id
                WHERE s.token = ? AND s.revoked = 0 AND s.expires_at > datetime('now')
            """, (token,))
            
            session_row = cursor.fetchone()
        
        if not session_row:
            logger.warning("Sessão não encontrada ou expirada")
            return None
        
        return UsuarioResponse(
            id=session_row['id'],
            username=session_row['username'],
            email=session_row['email'],
            nome=session_row['nome'],
            cbo=session_row['cbo'],
            cnes=session_row['cnes'],
            perfil=session_row['perfil'],
            ativo=session_row['ativo'],
            created_at=session_row['created_at'],
            last_login=session_row['last_login']
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[UsuarioResponse]:
        """Obtém usuário pelo ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM usuarios WHERE id = ?
            """, (user_id,))
            
            user_row = cursor.fetchone()
        
        if not user_row:
            return None
        
        return UsuarioResponse(
            id=user_row['id'],
            username=user_row['username'],
            email=user_row['email'],
            nome=user_row['nome'],
            cbo=user_row['cbo'],
            cnes=user_row['cnes'],
            perfil=user_row['perfil'],
            ativo=user_row['ativo'],
            created_at=user_row['created_at'],
            last_login=user_row['last_login']
        )
    
    def validate_user_procedure(self, user_id: int, codigo_procedimento: str) -> bool:
        """
        Valida se o usuário pode executar um procedimento
        
        Args:
            user_id: ID do usuário
            codigo_procedimento: Código do procedimento
            
        Returns:
            True se o usuário pode executar o procedimento
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        return self.dbf_manager.validate_cbo_procedimento(user.cbo, codigo_procedimento)
    
    def get_user_procedures(self, user_id: int) -> List[str]:
        """
        Obtém lista de procedimentos que o usuário pode executar
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de códigos de procedimentos
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        
        return self.dbf_manager.get_procedimentos_for_cbo(user.cbo)
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoga um token (logout)
        
        Args:
            token: Token a ser revogado
            
        Returns:
            True se revogado com sucesso
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE user_sessions 
                    SET revoked = 1 
                    WHERE token = ?
                """, (token,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Erro ao revogar token: {e}")
            return False
    
    def list_users(self) -> List[UsuarioResponse]:
        """Lista todos os usuários"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM usuarios ORDER BY nome
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append(UsuarioResponse(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    nome=row['nome'],
                    cbo=row['cbo'],
                    cnes=row['cnes'],
                    perfil=row['perfil'],
                    ativo=row['ativo'],
                    created_at=row['created_at'],
                    last_login=row['last_login']
                ))
            
            return users
    
    def update_user_status(self, user_id: int, ativo: bool) -> bool:
        """Atualiza status ativo/inativo do usuário"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE usuarios SET ativo = ? WHERE id = ?
                """, (ativo, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status do usuário: {e}")
            return False