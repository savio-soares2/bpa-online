from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Schemas relacionados ao sistema de usuários e CBOs

class UsuarioCreate(BaseModel):
    """Cadastro de usuário"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    nome: str = Field(..., max_length=100)
    cbo: str = Field(..., max_length=6, description="Código CBO do usuário")
    cnes: Optional[str] = Field(None, max_length=7, description="CNES de vinculação")
    perfil: str = Field(default="user", max_length=20)
    ativo: bool = Field(default=True)

class UsuarioResponse(BaseModel):
    """Resposta de usuário"""
    id: int
    username: str
    email: str
    nome: str
    cbo: str
    cnes: Optional[str] = None
    perfil: str
    ativo: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class LoginRequest(BaseModel):
    """Requisição de login"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Resposta de login"""
    access_token: str
    token_type: str = "bearer"
    user: UsuarioResponse
    procedimentos_permitidos: List[str] = []

class CBOInfo(BaseModel):
    """Informações sobre um CBO"""
    codigo: str
    descricao: Optional[str] = None
    total_procedimentos: int = 0
    procedimentos: List[str] = []

class ProcedimentoInfo(BaseModel):
    """Informações detalhadas de um procedimento"""
    codigo: str
    descricao: str
    complexidade: str
    classificacao: str
    exige_cbo: bool
    valor_sh: float = 0.0
    valor_sp: float = 0.0
    valor_sa: float = 0.0
    cbos_permitidos: List[str] = []

class ValidacaoCBORequest(BaseModel):
    """Requisição de validação CBO x Procedimento"""
    cbo: str
    procedimento: str

class ValidacaoCBOResponse(BaseModel):
    """Resposta de validação CBO x Procedimento"""
    valido: bool
    cbo: str
    procedimento: str
    procedimento_info: Optional[ProcedimentoInfo] = None
    motivo: Optional[str] = None

class DBFStatsResponse(BaseModel):
    """Estatísticas dos dados DBF"""
    total_cbos: int = 0
    total_procedimentos: int = 0
    total_relacoes: int = 0
    media_procedimentos_por_cbo: float = 0.0
    data_atualizacao: Optional[datetime] = None
    cache_ativo: bool = False

class ProcedimentoFilter(BaseModel):
    """Filtros para busca de procedimentos"""
    cbo: Optional[str] = None
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    complexidade: Optional[str] = None
    classificacao: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)

class CBOFilter(BaseModel):
    """Filtros para busca de CBOs"""
    codigo: Optional[str] = None
    procedimento: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)

class PermissaoValidationError(BaseModel):
    """Erro de validação de permissão"""
    error: str
    cbo: str
    procedimento: str
    message: str