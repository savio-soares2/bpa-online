"""
BPA Online API - Sistema de Cadastro e Exportação BPA
Versão 3.0 - Com Autenticação por CNES
"""
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Optional
import uvicorn
from datetime import datetime
import os

from database import BPADatabase, db, get_connection
from exporter import FirebirdExporter, exporter
from auth import (
    create_user, authenticate_user, get_user_by_id,
    create_jwt_token, decode_jwt_token, change_password,
    list_users, toggle_user_status, delete_user, reset_user_password,
    update_user
)
import logging

# Configurar logger
logger = logging.getLogger(__name__)

from services.bpa_report_generator import BPAReportService, BPAExportConfig, BPAFileGenerator
from services.corrections import BPACorrections
from services.consolidation_service import get_consolidation_service
from services.sigtap_filter_service import get_sigtap_filter_service
from services.financial_service import get_financial_service
from services.inconsistency_service import get_inconsistency_service
from constants.estabelecimentos import get_ibge_municipio
from models.schemas import (
    ProfissionalCreate, ProfissionalResponse,
    PacienteCreate, PacienteResponse,
    BPAIndividualizadoCreate, BPAIndividualizadoResponse,
    BPAConsolidadoCreate, BPAConsolidadoResponse,
    ExportRequest, ExportResponse,
    ProcedimentoResponse,
    JuliaImportRequest, JuliaImportResponse,
    BPAStatsResponse, DashboardStats
)
from pydantic import BaseModel
from routers.sigtap import router as sigtap_router

app = FastAPI(
    title="BPA Online API",
    description="Sistema de cadastro BPA e exportação para Firebird",
    version="3.0.0"
)

# Rotas SIGTAP
app.include_router(sigtap_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DBF_PATH = os.path.join(os.path.dirname(__file__), '..', 'BPA-main', 'RELATORIOS')


# ========== SCHEMAS DE AUTENTICAÇÃO ==========

class UserRegister(BaseModel):
    email: str
    senha: str
    nome: str
    cnes: str
    nome_unidade: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    senha: str

class UserResponse(BaseModel):
    id: int
    email: str
    nome: str
    cbo: Optional[str] = None
    cnes: Optional[str] = None
    nome_unidade: Optional[str] = None
    is_admin: Optional[bool] = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ChangePasswordRequest(BaseModel):
    senha_atual: str
    nova_senha: str


class ResetExportRequest(BaseModel):
    cnes: Optional[str] = None
    competencia: str
    tipo: Optional[str] = "all"


# ========== AUTENTICAÇÃO ==========

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Obtém usuário atual pelo token JWT"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.replace("Bearer ", "")
    
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    user = get_user_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return user


def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Obtém usuário se token fornecido"""
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_jwt_token(token)
        if payload:
            return get_user_by_id(payload.get("user_id"))
    except:
        pass
    return None


# ========== AUTH ENDPOINTS ==========

def get_admin_user(authorization: Optional[str] = Header(None)) -> dict:
    """Obtém usuário admin pelo token JWT"""
    user = get_current_user(authorization)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """Autentica usuário"""
    user = authenticate_user(data.email, data.senha)
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    token = create_jwt_token({
        "user_id": user["id"],
        "email": user["email"],
        "cnes": user.get("cnes", ""),
        "is_admin": user.get("is_admin", False)
    })
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(**user)
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Retorna dados do usuário logado"""
    return UserResponse(**user)


@app.get("/api/auth/debug")
async def debug_auth(authorization: Optional[str] = Header(None)):
    """Debug de autenticação - mostra o que está no token"""
    if not authorization:
        return {"error": "Sem token", "authorization": authorization}
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = decode_jwt_token(token)
        if payload:
            user = get_user_by_id(payload.get("user_id"))
            return {
                "token_payload": payload,
                "user_from_db": user,
                "is_admin_in_token": payload.get("is_admin"),
                "is_admin_in_db": user.get("is_admin") if user else None
            }
        else:
            return {"error": "Token inválido", "token": token[:50] + "..."}
    except Exception as e:
        return {"error": str(e), "token": token[:50] + "..."}


@app.post("/api/auth/change-password")
async def change_user_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """Altera senha do usuário"""
    if change_password(user["id"], data.senha_atual, data.nova_senha):
        return {"message": "Senha alterada com sucesso"}
    raise HTTPException(status_code=400, detail="Senha atual incorreta")


# ========== ADMIN ENDPOINTS ==========

class AdminUserCreate(BaseModel):
    email: str
    senha: str
    nome: str
    cbo: str
    cnes: Optional[str] = None
    nome_unidade: Optional[str] = None

class AdminUserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    cbo: Optional[str] = None
    cnes: Optional[str] = None
    nome_unidade: Optional[str] = None
    ativo: Optional[bool] = None

class AdminResetPassword(BaseModel):
    nova_senha: str


@app.get("/api/admin/users")
async def admin_list_users(admin: dict = Depends(get_admin_user)):
    """Lista todos os usuários (admin)"""
    return list_users()


@app.post("/api/admin/users")
async def admin_create_user(data: AdminUserCreate, admin: dict = Depends(get_admin_user)):
    """Cria novo usuário (admin)"""
    try:
        user = create_user(
            email=data.email,
            senha=data.senha,
            nome=data.nome,
            cbo=data.cbo,
            cnes=data.cnes,
            nome_unidade=data.nome_unidade
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/admin/users/{user_id}/toggle")
async def admin_toggle_user(user_id: int, ativo: bool, admin: dict = Depends(get_admin_user)):
    """Ativa/desativa usuário (admin)"""
    if toggle_user_status(user_id, ativo):
        return {"message": f"Usuário {'ativado' if ativo else 'desativado'}"}
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


@app.get("/api/admin/dashboard/stats")
async def admin_dashboard_stats(
    competencia_inicio: Optional[str] = Query(None),
    competencia_fim: Optional[str] = Query(None),
    cnes: Optional[List[str]] = Query(None, alias="cnes[]"),
    tipo_bpa: Optional[str] = Query(None),
    cbo: Optional[str] = Query(None),
    procedimento: Optional[str] = Query(None),
    admin: dict = Depends(get_admin_user)
):
    """Estatísticas financeiras do dashboard (admin) com filtros"""
    try:
        service = get_financial_service()

        # Normaliza lista de CNES
        cnes_list = cnes or []
        if isinstance(cnes_list, str):
            cnes_list = [cnes_list]

        stats = service.get_dashboard_stats(
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            cnes_list=cnes_list if cnes_list else None,
            tipo_bpa=tipo_bpa,
            cbo=cbo,
            procedimento=procedimento
        )

        return {
            "success": True,
            **stats
        }
    except Exception as e:
        logger.error(f"Erro dashboard financeiro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    """Remove usuário (admin)"""
    if delete_user(user_id):
        return {"message": "Usuário removido"}
    raise HTTPException(status_code=400, detail="Não é possível remover este usuário")


@app.post("/api/admin/users/{user_id}/reset-password")
async def admin_reset_password(user_id: int, data: AdminResetPassword, admin: dict = Depends(get_admin_user)):
    """Reset de senha (admin)"""
    if reset_user_password(user_id, data.nova_senha):
        return {"message": "Senha resetada com sucesso"}
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


# ========== ENDPOINTS BÁSICOS ==========

@app.get("/")
async def root():
    return {
        "message": "BPA Online API",
        "version": "3.0.0",
        "status": "online",
        "modules": ["auth", "bpa-i", "bpa-c", "export", "julia"]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ========== DASHBOARD ==========

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    cnes_filter: str = Query(None, description="CNES para filtrar"),
    user: dict = Depends(get_current_user)
):
    """Estatísticas do CNES filtrado ou do usuário"""
    try:
        # Usa o CNES do filtro ou o do usuário
        cnes = cnes_filter if cnes_filter else user.get("cnes")
        nome_unidade = user.get("nome_unidade", "") if not cnes_filter else ""
        
        # Se não tiver CNES definido, retorna stats vazias
        if not cnes:
            return {
                "cnes": "",
                "nome_unidade": nome_unidade,
                "usuario": user.get("nome", ""),
                "bpai": {"total": 0, "pendentes": 0, "exportados": 0, "competencias": []},
                "bpac": {"total": 0, "pendentes": 0, "exportados": 0, "competencias": []},
                "profissionais": 0,
                "pacientes": 0,
                "ultimas_exportacoes": []
            }
        
        stats = db.get_stats_by_cnes(cnes)
        
        return {
            "cnes": cnes,
            "nome_unidade": nome_unidade or stats.get("nome_unidade", ""),
            "usuario": user["nome"],
            "bpai": {
                "total": stats.get("bpai_total", 0),
                "pendentes": stats.get("bpai_pendente", 0),
                "exportados": stats.get("bpai_exportado", 0),
                "competencias": stats.get("bpai_competencias", [])
            },
            "bpac": {
                "total": stats.get("bpac_total", 0),
                "pendentes": stats.get("bpac_pendente", 0),
                "exportados": stats.get("bpac_exportado", 0),
                "competencias": stats.get("bpac_competencias", [])
            },
            "profissionais": stats.get("profissionais", 0),
            "pacientes": stats.get("pacientes", 0),
            "ultimas_exportacoes": stats.get("ultimas_exportacoes", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bpa/stats")
async def get_bpa_stats(
    cnes: str = Query(None, description="CNES (opcional, usa do usuário se não informado)"),
    competencia: str = Query(None),
    user: dict = Depends(get_current_user)
):
    """Estatísticas BPA por competência"""
    try:
        # Usa CNES do query ou do usuário
        target_cnes = cnes if cnes else user["cnes"]
        stats = db.get_bpa_stats(target_cnes, competencia)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== GERENCIAMENTO DE DADOS ==========

@app.get("/api/bpa/inconsistencies")
async def get_bpa_inconsistencies(
    cnes: str = Query(..., description="CNES para analisar"),
    competencia: str = Query(..., description="Competência para analisar"),
    user: dict = Depends(get_current_user)
):
    """
    Analisa inconsistências nos dados do banco sem alterá-los
    """
    try:
        service = get_inconsistency_service()
        report = service.get_inconsistency_report(cnes, competencia)
        return report
    except Exception as e:
        logger.error(f"Erro ao buscar inconsistências: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/database-overview")
async def get_database_overview(
    user: dict = Depends(get_current_user)
):
    """
    Visão geral do banco de dados
    Lista todos os CNES com dados e estatísticas por competência
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Estatísticas gerais por CNES
            cursor.execute("""
                SELECT 
                    prd_uid as cnes,
                    prd_cmp as competencia,
                    COUNT(*) as total_bpa_i,
                    SUM(CASE WHEN prd_exportado = FALSE THEN 1 ELSE 0 END) as pendentes,
                    SUM(CASE WHEN prd_exportado = TRUE THEN 1 ELSE 0 END) as exportados,
                    MIN(created_at) as primeira_insercao,
                    MAX(created_at) as ultima_insercao
                FROM bpa_individualizado
                GROUP BY prd_uid, prd_cmp
                ORDER BY prd_uid, prd_cmp DESC;
            """)
            
            bpa_i_data = []
            for row in cursor.fetchall():
                bpa_i_data.append({
                    "cnes": row[0],
                    "competencia": row[1],
                    "total": row[2],
                    "pendentes": row[3],
                    "exportados": row[4],
                    "primeira_insercao": row[5].isoformat() if row[5] else None,
                    "ultima_insercao": row[6].isoformat() if row[6] else None,
                    "tipo": "bpa_i"
                })
            
            # BPA-C
            cursor.execute("""
                SELECT 
                    prd_uid as cnes,
                    prd_cmp as competencia,
                    COUNT(*) as total_bpa_c,
                    SUM(CASE WHEN prd_exportado = FALSE THEN 1 ELSE 0 END) as pendentes,
                    SUM(CASE WHEN prd_exportado = TRUE THEN 1 ELSE 0 END) as exportados,
                    MIN(created_at) as primeira_insercao,
                    MAX(created_at) as ultima_insercao
                FROM bpa_consolidado
                GROUP BY prd_uid, prd_cmp
                ORDER BY prd_uid, prd_cmp DESC;
            """)
            
            bpa_c_data = []
            for row in cursor.fetchall():
                bpa_c_data.append({
                    "cnes": row[0],
                    "competencia": row[1],
                    "total": row[2],
                    "pendentes": row[3],
                    "exportados": row[4],
                    "primeira_insercao": row[5].isoformat() if row[5] else None,
                    "ultima_insercao": row[6].isoformat() if row[6] else None,
                    "tipo": "bpa_c"
                })
            
            # Lista de CNES únicos
            cursor.execute("""
                SELECT DISTINCT prd_uid 
                FROM bpa_individualizado
                UNION
                SELECT DISTINCT prd_uid 
                FROM bpa_consolidado
                ORDER BY prd_uid;
            """)
            
            cnes_list = [row[0] for row in cursor.fetchall()]
            
            # Totais gerais
            cursor.execute("SELECT COUNT(*) FROM bpa_individualizado;")
            total_bpa_i = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bpa_consolidado;")
            total_bpa_c = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM profissionais;")
            total_prof = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pacientes;")
            total_pac = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                "success": True,
                "cnes_list": cnes_list,
                "total_cnes": len(cnes_list),
                "bpa_i": bpa_i_data,
                "bpa_c": bpa_c_data,
                "totals": {
                    "bpa_i": total_bpa_i,
                    "bpa_c": total_bpa_c,
                    "profissionais": total_prof,
                    "pacientes": total_pac
                }
            }
    except Exception as e:
        logger.error(f"Erro ao buscar overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/historico-extracoes")
async def get_historico_extracoes(
    cnes: Optional[str] = Query(None, description="Filtrar por CNES"),
    limit: int = Query(20, description="Registros por página"),
    offset: int = Query(0, description="Offset para paginação"),
    user: dict = Depends(get_current_user)
):
    """
    Lista histórico de extrações com paginação
    
    Retorna:
    - Lista de extrações realizadas
    - Estatísticas de cada extração
    - Valores financeiros
    - Procedimentos mais usados
    - Total de registros para paginação
    """
    try:
        db = BPADatabase()
        result = db.list_historico_extracoes(cnes=cnes, limit=limit, offset=offset)
        
        # Formata datas
        for record in result['records']:
            if record.get('created_at'):
                record['created_at'] = record['created_at'].isoformat()
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/fix-encoding")
async def fix_encoding_historico(user: dict = Depends(get_current_user)):
    """
    Corrige encoding dos nomes de procedimentos no histórico.
    Busca os nomes corretos do SIGTAP (Latin-1).
    """
    try:
        # Carrega parser SIGTAP para ter os nomes corretos
        sigtap_parser = None
        sigtap_dir = os.getenv("SIGTAP_DIR", "/app/sigtap")
        if os.path.exists(sigtap_dir):
            try:
                from services.sigtap_parser import SigtapParser
                sigtap_parser = SigtapParser(sigtap_dir)
            except Exception as e:
                logger.warning(f"Não foi possível carregar SIGTAP: {e}")
        
        db = BPADatabase()
        result = db.fix_encoding_historico(sigtap_parser=sigtap_parser)
        
        msg = f"Encoding corrigido em {result['updated']} registros"
        if result.get('had_sigtap'):
            msg += " (nomes atualizados do SIGTAP)"
        else:
            msg += " (SIGTAP não disponível, nomes genéricos usados)"
        
        return {
            "success": True,
            "message": msg,
            **result
        }
    except Exception as e:
        logger.error(f"Erro ao corrigir encoding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/delete-data")
async def delete_data(
    cnes: str = Query(..., description="CNES para deletar"),
    competencia: str = Query(None, description="Competência específica (opcional)"),
    tipo: str = Query(..., description="bpa_i, bpa_c, profissionais, pacientes ou all"),
    user: dict = Depends(get_current_user)
):
    """
    Deleta dados do banco
    Requer confirmação e pode filtrar por CNES e competência
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            deleted_count = 0
            
            if tipo == "bpa_i" or tipo == "all":
                if competencia:
                    cursor.execute(
                        "DELETE FROM bpa_individualizado WHERE prd_uid = %s AND prd_cmp = %s",
                        (cnes, competencia)
                    )
                else:
                    cursor.execute(
                        "DELETE FROM bpa_individualizado WHERE prd_uid = %s",
                        (cnes,)
                    )
                deleted_count += cursor.rowcount
                logger.info(f"Deletados {cursor.rowcount} registros de BPA-I")
            
            if tipo == "bpa_c" or tipo == "all":
                if competencia:
                    cursor.execute(
                        "DELETE FROM bpa_consolidado WHERE prd_uid = %s AND prd_cmp = %s",
                        (cnes, competencia)
                    )
                else:
                    cursor.execute(
                        "DELETE FROM bpa_consolidado WHERE prd_uid = %s",
                        (cnes,)
                    )
                deleted_count += cursor.rowcount
                logger.info(f"Deletados {cursor.rowcount} registros de BPA-C")
            
            if tipo == "profissionais" or tipo == "all":
                cursor.execute(
                    "DELETE FROM profissionais WHERE cnes = %s",
                    (cnes,)
                )
                deleted_count += cursor.rowcount
                logger.info(f"Deletados {cursor.rowcount} profissionais")
            
            if tipo == "pacientes" or tipo == "all":
                # Apenas deleta pacientes se não houver BPA-I vinculado
                cursor.execute("""
                    DELETE FROM pacientes 
                    WHERE cns NOT IN (SELECT DISTINCT prd_cnspac FROM bpa_individualizado WHERE prd_cnspac IS NOT NULL)
                """)
                deleted_count += cursor.rowcount
                logger.info(f"Deletados {cursor.rowcount} pacientes sem vínculos")
            
            conn.commit()
            cursor.close()
            
            return {
                "success": True,
                "deleted": deleted_count,
                "cnes": cnes,
                "competencia": competencia,
                "tipo": tipo,
                "message": f"Deletados {deleted_count} registros"
            }
            
    except Exception as e:
        logger.error(f"Erro ao deletar dados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== PROFISSIONAIS ==========

@app.get("/api/profissionais", response_model=List[ProfissionalResponse])
async def list_profissionais(user: dict = Depends(get_current_user)):
    """Lista profissionais do CNES"""
    try:
        return db.list_profissionais(user["cnes"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profissionais/{cns}", response_model=ProfissionalResponse)
async def get_profissional(cns: str, user: dict = Depends(get_current_user)):
    """Busca profissional pelo CNS"""
    try:
        prof = db.get_profissional(cns)
        if not prof:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")
        return prof
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profissionais", response_model=ProfissionalResponse)
async def create_profissional(data: ProfissionalCreate, user: dict = Depends(get_current_user)):
    """Cadastra profissional no CNES do digitador"""
    try:
        prof_data = data.dict()
        prof_data['cnes'] = user['cnes']
        db.save_profissional(prof_data)
        return db.get_profissional(data.cns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PACIENTES ==========

@app.get("/api/pacientes/search")
async def search_pacientes(q: str = Query(..., min_length=2), user: dict = Depends(get_current_user)):
    """Busca pacientes"""
    try:
        return db.search_pacientes(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pacientes/{cns}", response_model=PacienteResponse)
async def get_paciente(cns: str, user: dict = Depends(get_current_user)):
    """Busca paciente pelo CNS"""
    try:
        pac = db.get_paciente(cns)
        if not pac:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        return pac
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pacientes", response_model=PacienteResponse)
async def create_paciente(data: PacienteCreate, user: dict = Depends(get_current_user)):
    """Cadastra paciente"""
    try:
        db.save_paciente(data.dict())
        return db.get_paciente(data.cns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== BPA INDIVIDUALIZADO ==========

@app.get("/api/bpa/individualizado")
async def list_bpa_individualizado(
    competencia: str = Query(...),
    exportado: Optional[bool] = None,
    user: dict = Depends(get_current_user)
):
    """Lista registros BPA-I do CNES"""
    try:
        return db.list_bpa_individualizado(user["cnes"], competencia, exportado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bpa/individualizado/{id}", response_model=BPAIndividualizadoResponse)
async def get_bpa_individualizado(id: int, user: dict = Depends(get_current_user)):
    """Busca BPA-I pelo ID"""
    try:
        record = db.get_bpa_individualizado(id)
        if not record:
            raise HTTPException(status_code=404, detail="Registro não encontrado")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bpa/individualizado", response_model=BPAIndividualizadoResponse)
async def create_bpa_individualizado(data: BPAIndividualizadoCreate, user: dict = Depends(get_current_user)):
    """Cadastra registro BPA-I"""
    try:
        # Converte para nomes PRD_*
        bpa_data = {
            'prd_uid': user['cnes'],
            'prd_cmp': data.competencia,
            'prd_cnsmed': data.cns_profissional,
            'prd_cbo': data.cbo,
            'prd_ine': data.ine,
            'prd_cnspac': data.cns_paciente,
            'prd_nmpac': data.nome_paciente,
            'prd_dtnasc': data.data_nascimento,
            'prd_sexo': data.sexo,
            'prd_raca': data.raca_cor,
            'prd_ibge': data.municipio_ibge,
            'prd_dtaten': data.data_atendimento,
            'prd_pa': data.procedimento,
            'prd_qt_p': data.quantidade,
            'prd_cid': data.cid,
        }
        
        # Cache profissional
        db.save_profissional({
            'cns': data.cns_profissional,
            'cbo': data.cbo,
            'cnes': user['cnes'],
            'ine': data.ine
        })
        
        id = db.save_bpa_individualizado(bpa_data)
        return db.get_bpa_individualizado(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/bpa/individualizado/{id}")
async def delete_bpa_individualizado(id: int, user: dict = Depends(get_current_user)):
    """Remove registro BPA-I"""
    try:
        if db.delete_bpa_individualizado(id):
            return {"message": "Registro removido"}
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== BPA CONSOLIDADO ==========

@app.get("/api/bpa/consolidado")
async def list_bpa_consolidado(competencia: str = Query(...), user: dict = Depends(get_current_user)):
    """Lista registros BPA-C do CNES"""
    try:
        return db.list_bpa_consolidado(user["cnes"], competencia)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bpa/consolidado", response_model=BPAConsolidadoResponse)
async def create_bpa_consolidado(data: BPAConsolidadoCreate, user: dict = Depends(get_current_user)):
    """Cadastra registro BPA-C"""
    try:
        bpa_data = data.dict()
        bpa_data['cnes'] = user['cnes']
        id = db.save_bpa_consolidado(bpa_data)
        records = db.list_bpa_consolidado(user['cnes'], data.competencia)
        return next((r for r in records if r['id'] == id), None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PROCEDIMENTOS (PÚBLICO) ==========

@app.get("/api/procedimentos/search")
async def search_procedimentos(q: str = Query(..., min_length=2)):
    """Busca procedimentos"""
    try:
        results = db.search_procedimentos(q)
        if not results:
            try:
                from dbfread import DBF
                dbf_file = os.path.join(DBF_PATH, 'S_PA.DBF')
                if os.path.exists(dbf_file):
                    table = DBF(dbf_file, encoding='latin-1')
                    for record in table:
                        codigo = record.get('PA_CODUNI', '').strip()
                        descricao = record.get('PA_DESUNI', '').strip()
                        if q.lower() in codigo.lower() or q.lower() in descricao.lower():
                            results.append({'codigo': codigo, 'descricao': descricao})
                            if len(results) >= 30:
                                break
            except Exception as e:
                print(f"[WARN] DBF: {e}")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/procedimentos/{codigo}")
async def get_procedimento(codigo: str):
    """Busca procedimento pelo código"""
    try:
        proc = db.get_procedimento(codigo)
        if proc:
            return proc
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== EXPORTAÇÃO ==========

@app.post("/api/export", response_model=ExportResponse)
async def export_bpa(request: ExportRequest, user: dict = Depends(get_current_user)):
    """Exporta BPA para arquivo SQL"""
    try:
        # Usa CNES do request ou do usuário
        cnes = request.cnes if request.cnes else user["cnes"]
        
        # Normaliza o tipo para aceitar ambos os formatos
        tipo = request.tipo.upper().replace('-', '').replace('_', '')
        # 'individualizado' -> 'INDIVIDUALIZADO', 'BPA-I' -> 'BPAI', 'bpai' -> 'BPAI'
        
        if tipo in ('BPAI', 'INDIVIDUALIZADO', 'I'):
            result = exporter.export_bpai(cnes, request.competencia, request.apenas_nao_exportados)
        elif tipo in ('BPAC', 'CONSOLIDADO', 'C'):
            result = exporter.export_bpac(cnes, request.competencia)
        else:  # 'ALL', 'TODOS', etc
            result = exporter.export_all(cnes, request.competencia)
        
        if result.get('filename'):
            result['download_url'] = f"/api/export/download/{result['filename']}"
        
        # Adiciona campos de compatibilidade com frontend
        result['total_registros'] = result.get('total', 0)
        result['arquivo'] = result.get('filename', '')
        
        return ExportResponse(**result)
    except Exception as e:
        logger.error(f"Erro ao exportar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/download/{filename}")
async def download_export(filename: str, user: dict = Depends(get_current_user)):
    """Download do arquivo SQL"""
    try:
        filepath = os.path.join(exporter.output_dir, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(filepath, media_type='application/sql', filename=filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/list")
async def list_exports(user: dict = Depends(get_current_user)):
    """Lista arquivos exportados"""
    try:
        return exporter.list_exports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export/reset")
async def reset_export_status(request: ResetExportRequest, user: dict = Depends(get_current_user)):
    """Reseta status de exportação para permitir nova exportação na mesma competência"""
    try:
        target_cnes = request.cnes if request.cnes else user.get("cnes")
        if not target_cnes:
            raise HTTPException(status_code=400, detail="CNES obrigatório")

        result = db.reset_export_status(target_cnes, request.competencia, request.tipo or "all")
        return {
            "success": True,
            "cnes": target_cnes,
            "competencia": request.competencia,
            "tipo": request.tipo or "all",
            "bpai_reset": result.get("bpai_reset", 0),
            "bpac_reset": result.get("bpac_reset", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== JULIA IMPORT ==========

@app.post("/api/julia/import", response_model=JuliaImportResponse)
async def import_from_julia(request: JuliaImportRequest, user: dict = Depends(get_current_user)):
    """Importa dados da API Julia"""
    try:
        imported = 0
        errors = []
        
        for i, reg in enumerate(request.registros):
            try:
                if request.tipo == "BPA-I":
                    data = {
                        'prd_uid': user["cnes"],
                        'prd_cmp': request.competencia,
                        'prd_cnsmed': reg.get('cns_profissional'),
                        'prd_cbo': reg.get('cbo'),
                        'prd_ine': reg.get('equipe_ine'),
                        'prd_cnspac': reg.get('cns_paciente'),
                        'prd_nmpac': reg.get('nome_paciente', '')[:30].upper(),
                        'prd_dtnasc': reg.get('data_nascimento'),
                        'prd_sexo': reg.get('sexo'),
                        'prd_raca': reg.get('raca_cor', '99'),
                        'prd_ibge': reg.get('municipio_ibge'),
                        'prd_dtaten': reg.get('data_atendimento'),
                        'prd_pa': reg.get('procedimento'),
                        'prd_qt_p': reg.get('quantidade', 1),
                        'prd_cid': reg.get('cid'),
                        'prd_org': 'JULIA'
                    }
                    db.save_bpa_individualizado(data)
                else:
                    data = {
                        'prd_uid': user["cnes"],
                        'prd_cmp': request.competencia,
                        'prd_cnsmed': reg.get('cns_profissional'),
                        'prd_cbo': reg.get('cbo'),
                        'prd_pa': reg.get('procedimento'),
                        'prd_idade': reg.get('idade', '999'),
                        'prd_qt_p': reg.get('quantidade', 1),
                        'prd_org': 'JULIA'
                    }
                    db.save_bpa_consolidado(data)
                imported += 1
            except Exception as e:
                errors.append(f"Reg {i+1}: {e}")
        
        return JuliaImportResponse(
            status="success" if not errors else "partial",
            message=f"Importados {imported}/{len(request.registros)}",
            total_recebidos=len(request.registros),
            total_importados=imported,
            erros=errors[:10]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/julia/check-connection")
async def check_julia_connection():
    """Verifica conexão Julia (mock)"""
    return {"success": True, "message": "OK"}


# ========== REFERÊNCIAS ==========

@app.get("/api/referencias/raca-cor")
async def get_racas():
    return [
        {"codigo": "01", "descricao": "Branca"},
        {"codigo": "02", "descricao": "Preta"},
        {"codigo": "03", "descricao": "Parda"},
        {"codigo": "04", "descricao": "Amarela"},
        {"codigo": "05", "descricao": "Indígena"},
        {"codigo": "99", "descricao": "Sem informação"}
    ]

@app.get("/api/referencias/sexo")
async def get_sexos():
    return [{"codigo": "M", "descricao": "Masculino"}, {"codigo": "F", "descricao": "Feminino"}]

@app.get("/api/referencias/carater-atendimento")
async def get_carater():
    return [
        {"codigo": "01", "descricao": "Eletivo"},
        {"codigo": "02", "descricao": "Urgência"}
    ]


# ========== EXTRAÇÃO BISERVER API ==========

from services.biserver_client import (
    BiServerAPIClient, 
    BiServerExtractionService,
    get_extraction_service,
    ExtractionResult
)

class ExtractRequest(BaseModel):
    cnes: str
    competencia: str
    tipo: str = "bpa_i"  # bpa_i ou bpa_c
    limit: int = 100
    offset: int = 0  # Para paginação

class ExtractResponse(BaseModel):
    success: bool
    message: str
    total_records: int
    records: list = []
    errors: list = []


@app.get("/api/biserver/test-connection")
async def test_biserver_connection(user: dict = Depends(get_current_user)):
    """Testa conexão com a API do BiServer"""
    try:
        service = get_extraction_service()
        result = service.test_api_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/biserver/extract", response_model=ExtractResponse)
async def extract_from_biserver(
    request: ExtractRequest,
    user: dict = Depends(get_current_user)
):
    """
    Extrai dados da API BiServer (bi.eSUS)
    NÃO insere automaticamente - apenas extrai e retorna os dados
    Suporta paginação via offset
    """
    try:
        service = get_extraction_service()
        
        if request.tipo == "bpa_i":
            result = service.extract_bpa_individualizado(
                cnes=request.cnes,
                competencia=request.competencia,
                limit=request.limit,
                offset=request.offset
            )
        elif request.tipo == "bpa_c":
            result = service.extract_bpa_consolidado(
                cnes=request.cnes,
                competencia=request.competencia,
                limit=request.limit,
                offset=request.offset
            )
        else:
            raise HTTPException(status_code=400, detail="Tipo deve ser 'bpa_i' ou 'bpa_c'")
        
        return ExtractResponse(
            success=result.success,
            message=result.message,
            total_records=result.total_records,
            records=result.records,
            errors=result.errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/biserver/extract-profissionais")
async def extract_profissionais(
    cnes: str = Query(...),
    limit: int = Query(50),
    user: dict = Depends(get_current_user)
):
    """Extrai lista de profissionais do BiServer"""
    try:
        service = get_extraction_service()
        result = service.extract_profissionais(cnes=cnes, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/biserver/count")
async def count_biserver_records(
    cnes: str = Query(..., description="Código CNES"),
    competencia: str = Query(..., description="Competência YYYYMM"),
    tipo: str = Query("bpa_i", description="Tipo: bpa_i ou bpa_c"),
    user: dict = Depends(get_current_user)
):
    """
    Conta total de registros disponíveis no BiServer para uma competência
    Use antes de extrair para saber quantos registros existem
    """
    try:
        service = get_extraction_service()
        result = service.count_records(cnes=cnes, competencia=competencia, tipo=tipo)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/biserver/extract-and-separate")
async def extract_and_separate_biserver(
    cnes: str = Query(..., description="Código CNES"),
    competencia: str = Query(..., description="Competência YYYYMM"),
    limit: Optional[int] = Query(None, description="Limite de registros (None = sem limite, extrai tudo)"),
    offset: int = Query(0, description="Offset para paginação"),
    user: dict = Depends(get_current_user)
):
    """
    🆕 MÉTODO UNIFICADO - Extrai, separa e salva automaticamente
    
    Fluxo:
    1. Extrai dados da API BiServer (paginado, sem limite total)
    2. Separa BPA-I e BPA-C usando SIGTAP
    3. Calcula valores financeiros via SIGTAP
    4. Salva direto no banco PostgreSQL
    5. Salva histórico com estatísticas
    6. Retorna resumo completo
    """
    import time
    from collections import Counter
    from services.sigtap_parser import SigtapParser
    import os
    
    inicio = time.time()
    max_errors = 25  # stop point para evitar loop infinito
    stopped_early = False
    truncation_counts = {}
    
    try:
        from database import BPADatabase
        
        sigtap_dir = os.getenv(
            "SIGTAP_DIR",
            r"C:\\Users\\60612427358\\Documents\\bpa-online\\bpa-online\\BPA-main\\TabelaUnificada_202512_v2601161858"
        )
        if not os.path.isdir(sigtap_dir):
            msg = f"Diretório SIGTAP não encontrado: {sigtap_dir}"
            logger.error(f"[EXTRACT] {msg}")
            raise HTTPException(status_code=500, detail=msg)
        sigtap_parser = SigtapParser(sigtap_dir)
        logger.info(f"[EXTRACT] SIGTAP carregado de {sigtap_dir}")
        
        # Cache de nomes de procedimentos para evitar reprocessamento
        try:
            procs_map = {
                p['CO_PROCEDIMENTO']: p['NO_PROCEDIMENTO']
                for p in sigtap_parser.parse_procedimentos()
            }
            logger.info(f"[EXTRACT] Cache SIGTAP carregado ({len(procs_map)} procedimentos)")
        except Exception as e:
            procs_map = {}
            logger.warning(f"[EXTRACT] Falha ao montar cache de procedimentos: {e}")
        
        # USA O SINGLETON para manter o cache
        service = get_extraction_service()
        
        # Extrai e separa
        logger.info(f"[EXTRACT] Chamando extract_and_separate_bpa para CNES={cnes}, COMP={competencia}, limit={limit}, offset={offset}")
        result = service.extract_and_separate_bpa(
            cnes=cnes,
            competencia=competencia,
            limit=limit,
            offset=offset
        )
        
        if not result['success']:
            logger.error(f"[EXTRACT] Falha na extração: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Erro na extração'))
        
        logger.info(f"[EXTRACT] Extração bem-sucedida: total={result['stats'].get('total', 0)}, removidos={result['stats'].get('removed', 0)}")
        
        # Aplica correções antes de salvar (CEP, sexo, logradouro, etc.)
        corrector = BPACorrections(cnes)
        stats_corr_bpi = None
        stats_corr_bpc = None

        if result.get('bpa_i'):
            logger.info(f"[EXTRACT] Aplicando correções BPA-I em {len(result['bpa_i'])} registros...")
            result['bpa_i'], stats_corr_bpi = corrector.process_batch(result['bpa_i'], 'BPI')
            if stats_corr_bpi:
                logger.info(
                    f"[EXTRACT] Correções BPA-I: corrigidos={stats_corr_bpi.get('corrected', 0)}, "
                    f"removidos={stats_corr_bpi.get('deleted', 0)}"
                )
                if stats_corr_bpi.get('correction_types'):
                    top = sorted(stats_corr_bpi['correction_types'].items(), key=lambda x: x[1], reverse=True)[:5]
                    resumo = ", ".join([f"{k}={v}" for k, v in top])
                    logger.info(f"[EXTRACT] Tipos correção BPA-I (top 5): {resumo}")
                if stats_corr_bpi.get('delete_reasons'):
                    top_del = sorted(stats_corr_bpi['delete_reasons'].items(), key=lambda x: x[1], reverse=True)[:3]
                    resumo_del = ", ".join([f"{k}={v}" for k, v in top_del])
                    logger.info(f"[EXTRACT] Motivos exclusão BPA-I (top 3): {resumo_del}")
        else:
            stats_corr_bpi = {
                "total_input": 0,
                "total_output": 0,
                "deleted": 0,
                "corrected": 0,
                "unchanged": 0,
                "delete_reasons": {},
                "correction_types": {}
            }

        if result.get('bpa_c'):
            logger.info(f"[EXTRACT] Aplicando correções BPA-C em {len(result['bpa_c'])} registros...")
            result['bpa_c'], stats_corr_bpc = corrector.process_batch(result['bpa_c'], 'BPA')
            if stats_corr_bpc:
                logger.info(
                    f"[EXTRACT] Correções BPA-C: corrigidos={stats_corr_bpc.get('corrected', 0)}, "
                    f"removidos={stats_corr_bpc.get('deleted', 0)}"
                )
        else:
            stats_corr_bpc = {
                "total_input": 0,
                "total_output": 0,
                "deleted": 0,
                "corrected": 0,
                "unchanged": 0,
                "delete_reasons": {},
                "correction_types": {}
            }

        # Salva direto no banco
        logger.info("[EXTRACT] Inicializando banco de dados...")
        db = BPADatabase()
        saved_bpa_i = 0
        saved_bpa_c = 0
        errors = []
        
        # Estatísticas
        procedimentos_counter_i = Counter()
        procedimentos_counter_c = Counter()
        profissionais_counter = Counter()
        distribuicao_dias = Counter()
        valor_total_bpa_i = 0.0
        valor_total_bpa_c = 0.0
        
        # Helpers para sanitização e logging
        def _register_truncation(field_name: str, length: int):
            truncation_counts[field_name] = truncation_counts.get(field_name, 0) + 1
            if truncation_counts[field_name] <= 3:
                logger.warning(f"[EXTRACT] {field_name} acima de limite (len={length}). Será truncado.")
        
        def sanitize_digits(value, max_len: int, field_name: str) -> str:
            raw = str(value or "")
            digits = ''.join(ch for ch in raw if ch.isdigit())
            if len(digits) > max_len:
                _register_truncation(field_name, len(digits))
            return digits[:max_len]
        
        def sanitize_text(value, max_len: int, field_name: str) -> str:
            raw = str(value or "")
            if len(raw) > max_len:
                _register_truncation(field_name, len(raw))
            return raw[:max_len]
        
        # CNES de urgência/emergência
        CNES_URGENCIA = ['2755289', '2492555', '2829606']
        carater = '02' if cnes in CNES_URGENCIA else '01'
        
        logger.info(f"[EXTRACT] Salvando {len(result['bpa_i'])} registros BPA-I...")
        
        for seq, record in enumerate(result['bpa_i'], start=1):
            if len(errors) >= max_errors:
                stopped_early = True
                logger.error(f"[EXTRACT] Stop point atingido após {len(errors)} erros em BPA-I. Abortando loop.")
                break
            try:
                procedimento = str(record.get("prd_pa", ""))
                quantidade = int(record.get("prd_qt_p", 1) or 1)
                procedimentos_counter_i[procedimento] += quantidade
                profissional_key = f"{record.get('prd_cnsmed', '')}_{record.get('prd_cbo', '')}"
                profissionais_counter[profissional_key] += 1
                
                data_aten = sanitize_digits(record.get("prd_dtaten", ""), 8, "prd_dtaten")
                data_nasc = sanitize_digits(record.get("prd_dtnasc", ""), 8, "prd_dtnasc")
                cep = sanitize_digits(record.get("prd_cep_pcnte", ""), 8, "prd_cep_pcnte")
                if len(data_aten) == 8:
                    distribuicao_dias[data_aten[6:8]] += 1
                
                try:
                    valores = sigtap_parser.get_procedimento_valor(procedimento)
                except Exception as e:
                    logger.warning(f"[EXTRACT] Falha ao obter valor SIGTAP {procedimento}: {e}")
                    valores = {}
                valor_unit = float(valores.get('valor_ambulatorio', 0.0))
                valor_total_bpa_i += valor_unit * quantidade
                
                bpa_data = {
                    "prd_uid": cnes,
                    "prd_cmp": competencia,
                    "prd_flh": 1,
                    "prd_seq": seq,
                    "prd_cnsmed": sanitize_text(record.get("prd_cnsmed", ""), 15, "prd_cnsmed"),
                    "prd_cbo": sanitize_text(record.get("prd_cbo", ""), 6, "prd_cbo"),
                    "prd_ine": "",
                    "prd_cnspac": sanitize_text(record.get("prd_cnspac", ""), 15, "prd_cnspac"),
                    # prd_cnspc da API BiServer contém o CPF do paciente (quando não tem CNS)
                    "prd_cpf_pcnte": sanitize_digits(record.get("prd_cnspc", "") or record.get("prd_cpf_pcnte", "") or record.get("cpf_paciente", "") or "", 11, "prd_cpf_pcnte"),
                    "prd_nmpac": sanitize_text(record.get("prd_nmpac", ""), 255, "prd_nmpac"),
                    "prd_dtnasc": data_nasc,
                    "prd_sexo": sanitize_text(record.get("prd_sexo", "M"), 1, "prd_sexo"),
                    "prd_raca": sanitize_text(str(record.get("prd_raca", "99")).zfill(2), 2, "prd_raca"),
                    "prd_idade": sanitize_text(record.get("prd_idade", ""), 3, "prd_idade"),
                    "prd_ibge": "",
                    "prd_cep_pcnte": cep,
                    "prd_lograd_pcnte": sanitize_text(record.get("prd_lograd_pcnte", ""), 10, "prd_lograd_pcnte"),
                    "prd_end_pcnte": sanitize_text(record.get("prd_end_pcnte", ""), 255, "prd_end_pcnte"),
                    "prd_num_pcnte": sanitize_text(record.get("prd_num_pcnte", ""), 10, "prd_num_pcnte"),
                    "prd_compl_pcnte": sanitize_text(record.get("prd_compl_pcnte", ""), 100, "prd_compl_pcnte"),
                    "prd_bairro_pcnte": sanitize_text(record.get("prd_bairro_pcnte", ""), 30, "prd_bairro_pcnte"),
                    "prd_tel_pcnte": sanitize_text(record.get("prd_tel_pcnte", ""), 20, "prd_tel_pcnte"),
                    "prd_ddtel_pcnte": sanitize_text(record.get("prd_ddtel_pcnte", ""), 2, "prd_ddtel_pcnte"),
                    "prd_email_pcnte": sanitize_text(record.get("prd_email_pcnte", "") or "", 255, "prd_email_pcnte"),
                    "prd_dtaten": data_aten,
                    "prd_pa": procedimento,
                    "prd_qt_p": quantidade,
                    "prd_cid": sanitize_text(record.get("prd_cid", ""), 10, "prd_cid"),
                    "prd_caten": carater,
                    "prd_naut": "",
                    "prd_servico": "",
                    "prd_classificacao": "",
                    "prd_cnpj": "",
                    "prd_nac": "010",
                    "prd_etnia": "",
                    "prd_eqp_area": "",
                    "prd_eqp_seq": "",
                    "prd_mvm": competencia,
                    "prd_org": "BPI",
                }
                db.save_bpa_individualizado(bpa_data)
                saved_bpa_i += 1
            except Exception as e:
                error_msg = str(e)
                errors.append(f"BPA-I #{seq}: {error_msg}")
                if len(errors) <= 3:
                    logger.error(f"[EXTRACT] Erro ao salvar BPA-I #{seq}: {error_msg}")
        
        logger.info(f"[EXTRACT] Preparando {len(result['bpa_c'])} registros BPA-C...")
        
        bpac_records_to_save = []
        for seq, record in enumerate(result['bpa_c'], start=1):
            if len(errors) >= max_errors:
                stopped_early = True
                logger.error(f"[EXTRACT] Stop point atingido após {len(errors)} erros em BPA-C. Abortando loop.")
                break
            try:
                procedimento = str(record.get("prd_pa", ""))
                quantidade = int(record.get("prd_qt_p", 1) or 1)
                procedimentos_counter_c[procedimento] += quantidade
                
                try:
                    valores = sigtap_parser.get_procedimento_valor(procedimento)
                except Exception as e:
                    logger.warning(f"[EXTRACT] Falha ao obter valor SIGTAP {procedimento}: {e}")
                    valores = {}
                valor_unit = float(valores.get('valor_ambulatorio', 0.0))
                valor_total_bpa_c += valor_unit * quantidade
                
                bpac_data = {
                    "prd_uid": cnes,
                    "prd_cmp": competencia,
                    "prd_flh": 1,
                    "prd_cnsmed": sanitize_text(record.get("prd_cnsmed", ""), 15, "prd_cnsmed"),
                    "prd_cbo": sanitize_text(record.get("prd_cbo", ""), 6, "prd_cbo"),
                    "prd_pa": procedimento,
                    "prd_qt_p": quantidade,
                    "prd_idade": sanitize_text(record.get("prd_idade", ""), 3, "prd_idade"),
                    "prd_org": "BPC",
                }
                bpac_records_to_save.append(bpac_data)
            except Exception as e:
                errors.append(f"BPA-C #{seq}: {str(e)}")
                if len(errors) <= 3:
                    logger.error(f"[EXTRACT] Erro ao preparar BPA-C #{seq}: {str(e)}")

        if not stopped_early and bpac_records_to_save:
            save_result = db.save_bpa_consolidado_batch(bpac_records_to_save)
            saved_bpa_c = save_result.get('saved', 0)
            if save_result.get('errors'):
                for err in save_result['errors'][:5]:
                    errors.append(f"BPA-C batch: {err}")
            logger.info(
                f"[EXTRACT] BPA-C batch: inserted={save_result.get('inserted', 0)}, "
                f"updated={save_result.get('updated', 0)}, saved={saved_bpa_c}"
            )
        
        duracao = int(time.time() - inicio)
        status_hist = 'concluido' if not stopped_early else 'erro'
        
        logger.info(f"[EXTRACT] Salvamento concluído: BPA-I={saved_bpa_i}, BPA-C={saved_bpa_c}, Erros={len(errors)}, Tempo={duracao}s, Stop={stopped_early}")
        if truncation_counts:
            resumo_trunc = ", ".join([f"{k}={v}" for k, v in truncation_counts.items()])
            logger.info(f"[EXTRACT] Campos truncados (contagem): {resumo_trunc}")
        
        # Monta lista de procedimentos mais usados (top 10)
        procedimentos_mais_usados = []
        todos_procedimentos = procedimentos_counter_i.copy()
        todos_procedimentos.update(procedimentos_counter_c)
        for proc_codigo, qtd in todos_procedimentos.most_common(10):
            try:
                valores = sigtap_parser.get_procedimento_valor(proc_codigo)
                valor_unit = valores.get('valor_ambulatorio', 0.0) or 0.0
            except Exception as e:
                logger.warning(f"[EXTRACT] Falha valor SIGTAP em resumo {proc_codigo}: {e}")
                valor_unit = 0.0
            nome = procs_map.get(proc_codigo, "Desconhecido")
            procedimentos_mais_usados.append({
                "codigo": proc_codigo,
                "nome": nome,
                "quantidade": qtd,
                "valor_unitario": float(valor_unit),
                "valor_total": float(valor_unit * qtd)
            })
        
        # Monta lista de profissionais mais ativos (top 10)
        profissionais_mais_ativos = []
        for prof_key, qtd in profissionais_counter.most_common(10):
            cns, cbo = prof_key.split('_')
            profissionais_mais_ativos.append({
                "cns": cns,
                "cbo": cbo,
                "quantidade": qtd
            })
        
        # Salva histórico completo
        try:
            historico_id = db.save_historico_extracao({
                'cnes': cnes,
                'competencia': competencia,
                'total_bpa_i': saved_bpa_i,
                'total_bpa_c': saved_bpa_c,
                'total_removido': result['stats'].get('removed', 0),
                'total_geral': saved_bpa_i + saved_bpa_c,
                'valor_total_bpa_i': valor_total_bpa_i,
                'valor_total_bpa_c': valor_total_bpa_c,
                'valor_total_geral': valor_total_bpa_i + valor_total_bpa_c,
                'procedimentos_mais_usados': procedimentos_mais_usados,
                'profissionais_mais_ativos': profissionais_mais_ativos,
                'distribuicao_por_dia': dict(distribuicao_dias),
                'usuario_id': user.get('id'),
                'duracao_segundos': duracao,
                'status': status_hist,
                'erro': '; '.join(errors[:3]) if errors else None
            })
            logger.info(f"[EXTRACT] Histórico salvo: ID={historico_id}")
        except Exception as e:
            logger.error(f"[EXTRACT] Erro ao salvar histórico: {e}")
            historico_id = None
        
        if stopped_early:
            return {
                "success": False,
                "historico_id": historico_id,
                "message": f"Interrompido após {len(errors)} erros. Veja logs.",
                "errors": errors[:10],
                "stats": {
                    "extracted": result['stats'],
                    "saved": {
                        "bpa_i": saved_bpa_i,
                        "bpa_c": saved_bpa_c
                    },
                    "corrections": {
                        "bpai": stats_corr_bpi,
                        "bpac": stats_corr_bpc
                    },
                    "valores": {
                        "bpa_i": float(valor_total_bpa_i),
                        "bpa_c": float(valor_total_bpa_c),
                        "total": float(valor_total_bpa_i + valor_total_bpa_c)
                    },
                    "procedimentos_mais_usados": procedimentos_mais_usados[:5],
                    "duracao_segundos": duracao
                }
            }
        
        return {
            "success": True,
            "historico_id": historico_id,
            "stats": {
                "extracted": result['stats'],
                "saved": {
                    "bpa_i": saved_bpa_i,
                    "bpa_c": saved_bpa_c
                },
                "corrections": {
                    "bpai": stats_corr_bpi,
                    "bpac": stats_corr_bpc
                },
                "valores": {
                    "bpa_i": float(valor_total_bpa_i),
                    "bpa_c": float(valor_total_bpa_c),
                    "total": float(valor_total_bpa_i + valor_total_bpa_c)
                },
                "procedimentos_mais_usados": procedimentos_mais_usados[:5],
                "duracao_segundos": duracao
            },
            "errors": errors[:10] if errors else [],
            "message": f"✅ Salvos: {saved_bpa_i} BPA-I (R$ {valor_total_bpa_i:.2f}), {saved_bpa_c} BPA-C (R$ {valor_total_bpa_c:.2f}). Total: R$ {(valor_total_bpa_i + valor_total_bpa_c):.2f}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXTRACT] ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Erro: {str(e)}",
            "stats": {},
            "errors": [str(e)]
        }


@app.post("/api/biserver/extract-all")
async def extract_all_biserver(
    cnes: str = Query(..., description="Código CNES"),
    competencia: str = Query(..., description="Competência YYYYMM"),
    tipo: str = Query("bpa_i", description="Tipo: bpa_i ou bpa_c"),
    batch_size: int = Query(5000, description="Tamanho de cada lote"),
    auto_save: bool = Query(True, description="Salvar automaticamente cada lote"),
    sigtap_filter: bool = Query(True, description="Filtrar apenas procedimentos válidos no SIGTAP"),
    user: dict = Depends(get_current_user)
):
    """
    Extrai TODOS os registros automaticamente em lotes até finalizar
    
    - Conta o total de registros primeiro
    - Extrai em lotes (padrão 5000)
    - Para automaticamente quando acabar
    - Opcionalmente salva cada lote no banco
    - Filtra procedimentos pelo SIGTAP (padrão: ativo)
    
    Retorna estatísticas completas da extração
    """
    try:
        # Cria serviço com ou sem validação SIGTAP
        from services.biserver_client import BiServerExtractionService
        service = BiServerExtractionService(enable_sigtap_validation=sigtap_filter)
        
        # Função para salvar cada lote automaticamente
        def save_batch(batch_num, total_batches, records):
            if auto_save and records:
                try:
                    # Aplica correções antes de salvar
                    corrector = BPACorrections(cnes)
                    tipo_correcao = 'BPI' if tipo == 'bpa_i' else 'BPA'
                    
                    # logger.info(f"Aplicando correções em {len(records)} registros ({tipo_correcao})...")
                    records, stats = corrector.process_batch(records, tipo_correcao)
                    
                    if stats['corrected'] > 0 or stats['deleted'] > 0:
                        logger.info(f"Lote {batch_num}: {stats['corrected']} corrigidos, {stats['deleted']} removidos")
                    else:
                        logger.info(f"Lote {batch_num}: sem correções aplicadas")

                    if stats.get('correction_types'):
                        top = sorted(stats['correction_types'].items(), key=lambda x: x[1], reverse=True)[:5]
                        resumo = ", ".join([f"{k}={v}" for k, v in top])
                        logger.info(f"Lote {batch_num}: tipos de correção (top 5): {resumo}")

                    if stats.get('delete_reasons'):
                        top_del = sorted(stats['delete_reasons'].items(), key=lambda x: x[1], reverse=True)[:3]
                        resumo_del = ", ".join([f"{k}={v}" for k, v in top_del])
                        logger.info(f"Lote {batch_num}: motivos de exclusão (top 3): {resumo_del}")

                    logger.info(f"Auto-salvando lote {batch_num}/{total_batches} ({len(records)} registros a salvar)")
                    # Salva direto no banco via BPADatabase
                    db = BPADatabase()
                    if tipo == "bpa_i":
                        db.save_bpa_individualizado(records)
                    else:
                        db.save_bpa_consolidado(records)
                except Exception as e:
                    logger.error(f"Erro ao auto-salvar lote {batch_num}: {e}")
        
        # Extrai tudo
        if tipo == "bpa_i":
            result = service.extract_all_bpa_individualizado(
                cnes=cnes,
                competencia=competencia,
                batch_size=batch_size,
                on_batch_complete=save_batch if auto_save else None
            )
        else:
            result = service.extract_all_bpa_consolidado(
                cnes=cnes,
                competencia=competencia,
                batch_size=batch_size,
                on_batch_complete=save_batch if auto_save else None
            )
        
        return {
            **result,
            "auto_saved": auto_save,
            "tipo": tipo
        }
        
    except Exception as e:
        logger.error(f"Erro na extração completa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/biserver/extract-pacientes")
async def extract_pacientes(
    cnes: str = Query(...),
    limit: int = Query(100),
    user: dict = Depends(get_current_user)
):
    """Extrai lista de pacientes do BiServer"""
    try:
        service = get_extraction_service()
        result = service.extract_pacientes(cnes=cnes, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== CONSOLIDAÇÃO BPA-I → BPA-C ==========

@app.post("/api/consolidation/execute")
async def consolidar_bpai_to_bpac(
    cnes: str = Query(..., description="CNES para consolidar"),
    competencia: str = Query(..., pattern=r"^\d{6}$", description="Competência YYYYMM"),
    user: dict = Depends(get_current_user)
):
    """
    Consolida BPA-I em BPA-C baseado nas listas de procedimentos
    
    Fluxo:
    1. Identifica BPA-I que devem virar BPA-C
    2. Agrupa e soma quantidades
    3. Cria registros BPA-C
    4. Remove BPA-I originais
    5. Mantém BPA-I que não estão nas listas
    """
    try:
        consolidation_service = get_consolidation_service()
        stats = consolidation_service.consolidar_bpai_para_bpac(cnes, competencia)
        
        return {
            "success": True,
            "message": f"Consolidação concluída para {cnes}/{competencia}",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/consolidation/verify-procedure/{codigo}")
async def verificar_procedimento(
    codigo: str,
    user: dict = Depends(get_current_user)
):
    """
    Verifica se um procedimento deve ser BPA-I ou BPA-C
    """
    try:
        consolidation_service = get_consolidation_service()
        info = consolidation_service.verificar_procedimento(codigo)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/consolidation/stats")
async def get_consolidation_stats(
    cnes: str = Query(...),
    competencia: str = Query(..., pattern=r"^\d{6}$"),
    user: dict = Depends(get_current_user)
):
    """
    Retorna estatísticas antes de consolidar
    Mostra quantos BPA-I podem virar BPA-C
    """
    try:
        consolidation_service = get_consolidation_service()
        
        # Busca BPA-I
        bpai_records = db.list_bpa_individualizado(cnes, competencia, exportado=False)
        
        # Classifica por tipo
        stats = {
            'total_bpai': len(bpai_records),
            'pode_consolidar_geral': 0,
            'pode_consolidar_idade': 0,
            'manter_bpai': 0,
            'procedimentos_geral': [],
            'procedimentos_idade': [],
            'procedimentos_manter': []
        }
        
        proc_geral = set()
        proc_idade = set()
        proc_manter = set()
        
        for record in bpai_records:
            procedimento = record.get('prd_pa', '')
            info = consolidation_service.verificar_procedimento(procedimento)
            
            if info['tipo'] == 'BPA-C':
                if info['subtipo'] == 'geral':
                    stats['pode_consolidar_geral'] += 1
                    proc_geral.add(procedimento)
                else:
                    stats['pode_consolidar_idade'] += 1
                    proc_idade.add(procedimento)
            else:
                stats['manter_bpai'] += 1
                proc_manter.add(procedimento)
        
        stats['procedimentos_geral'] = sorted(list(proc_geral))
        stats['procedimentos_idade'] = sorted(list(proc_idade))
        stats['procedimentos_manter'] = sorted(list(proc_manter))
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/biserver/export-options")
async def get_export_options():
    """
    Retorna opções de exportação disponíveis
    """
    return {
        "options": [
            {
                "id": "sql",
                "name": "Script SQL",
                "description": "Gera arquivo .sql com INSERTs para importar no Firebird via firebird-sync",
                "recommended": True
            },
            {
                "id": "csv",
                "name": "CSV",
                "description": "Exporta em CSV para conversão posterior",
                "recommended": False
            },
            {
                "id": "json",
                "name": "JSON",
                "description": "Exporta em JSON para integração com outras ferramentas",
                "recommended": False
            }
        ],
        "analysis": {
            "sql": {
                "pros": [
                    "Pronto para executar no Firebird",
                    "Suporta transações e rollback",
                    "Fácil validação antes de executar"
                ],
                "cons": [
                    "Arquivo maior que CSV",
                    "Precisa de ferramenta para executar"
                ],
                "performance": "Boa - execução direta no banco"
            },
            "csv": {
                "pros": [
                    "Arquivo compacto",
                    "Fácil visualização em Excel",
                    "Compatível com diversas ferramentas"
                ],
                "cons": [
                    "Precisa converter para SQL",
                    "Passo adicional no processo"
                ],
                "performance": "Requer conversão - processamento extra"
            }
        },
        "recommendation": "Use SQL para importação direta. CSV apenas se precisar visualizar/editar os dados antes."
    }


# ========== RELATÓRIOS BPA (CLONAGEM BPA MAGNÉTICO) ==========

class ReportRequest(BaseModel):
    competencia: str  # YYYYMM
    sigla: Optional[str] = "CAPSAD"
    cnes: Optional[str] = None  # Se não informado, usa o do usuário
    tipo: Optional[str] = "all"  # 'remessa', 'relexp', 'bpai', 'bpac', 'all'

class ReportResponse(BaseModel):
    success: bool
    message: str
    stats: dict
    files: dict  # nome -> download_url

# Mapeamento de extensões por mês
EXTENSOES_MES = {
    '01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR',
    '05': 'MAI', '06': 'JUN', '07': 'JUL', '08': 'AGO',
    '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'
}

@app.post("/api/reports/generate")
async def generate_bpa_reports(request: ReportRequest, user: dict = Depends(get_current_user)):
    """
    Gera os arquivos de relatório BPA (individual ou todos):
    - PA[SIGLA].[MES] (arquivo de remessa - extensão varia por mês)
    - RELEXP.PRN (relatório de controle)
    - BPAI_REL.TXT (relatório BPA-I)
    - BPAC_REL.TXT (relatório BPA-C)
    
    Parâmetros:
    - tipo: 'remessa', 'relexp', 'bpai', 'bpac', 'all' (default: 'all')
    - cnes: CNES do estabelecimento (opcional, usa do usuário se não informado)
    """
    try:
        # Usa CNES do request ou do usuário
        cnes = request.cnes if request.cnes else user["cnes"]
        competencia = request.competencia
        sigla = request.sigla or "CAPSAD"
        tipo = request.tipo or "all"
        
        # Extrai mês da competência para definir extensão
        mes = competencia[4:6] if len(competencia) == 6 else "01"
        extensao = EXTENSOES_MES.get(mes, "TXT")
        
        # Busca dados do banco (sem limite para relatórios)
        bpai_records = db.list_bpa_individualizado(cnes, competencia, limit=10000)
        bpac_records = db.list_bpa_consolidado(cnes, competencia, limit=10000)
        
        if not bpai_records and not bpac_records:
            return {
                "success": False,
                "message": f"Nenhum registro encontrado para competência {competencia}",
                "stats": {"bpai_count": 0, "bpac_count": 0},
                "files": {}
            }
        
        # Carrega parser SIGTAP para obter valores dos procedimentos
        sigtap_parser = None
        try:
            from services.sigtap_parser import SigtapParser
            sigtap_dir = os.path.join(os.path.dirname(__file__), '..', 'BPA-main', 'TabelaUnificada_202512_v2601161858')
            if os.path.exists(sigtap_dir):
                sigtap_parser = SigtapParser(sigtap_dir)
                logger.info(f"[REPORT] SIGTAP parser carregado de {sigtap_dir}")
        except Exception as e:
            logger.warning(f"[REPORT] Não foi possível carregar SIGTAP: {e}")
        
        # Configura gerador
        ibge_municipio = get_ibge_municipio(cnes)
        config = BPAExportConfig(
            cnes=cnes,
            competencia=competencia,
            sigla=sigla,
            ibge_municipio=ibge_municipio
        )
        generator = BPAFileGenerator(config, sigtap_parser=sigtap_parser)
        
        # Gera arquivo de remessa
        set_content, total_registros, total_bpas = generator.generate_set_file(
            bpai_records, bpac_records
        )
        
        # Campo de controle: fórmula do BPA Magnético
        # (total_registros * 7 + total_bpas * 3) mod 10000
        # Esta é a fórmula oficial usada pelo DATASUS para validação
        campo_controle = str((total_registros * 7 + total_bpas * 3) % 10000).zfill(4)
        
        # Gera relatórios (passa extensão correta para o RELEXP)
        relexp_content = generator.generate_relexp(total_registros, total_bpas, campo_controle, extensao)
        bpai_rel_content = generator.generate_bpai_report(bpai_records)
        bpac_rel_content = generator.generate_bpac_report(bpac_records)
        
        # Salva arquivos
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Subdiretório por competência e CNES
        export_dir = os.path.join(reports_dir, f"{cnes}_{competencia}")
        os.makedirs(export_dir, exist_ok=True)
        
        files = {}
        
        # Define quais arquivos gerar baseado no tipo
        # IMPORTANTE: remessa sempre gera junto com relexp (controle), pois são inseparáveis
        gerar_remessa = tipo in ('remessa', 'all')
        gerar_relexp = tipo in ('remessa', 'relexp', 'all')  # Sempre gera com remessa
        gerar_bpai = tipo in ('bpai', 'all')
        gerar_bpac = tipo in ('bpac', 'all')
        
        # Salva arquivo de remessa (extensão baseada no mês)
        if gerar_remessa:
            set_filename = f"PA{sigla}.{extensao}"
            set_path = os.path.join(export_dir, set_filename)
            with open(set_path, 'w', encoding='latin-1') as f:
                f.write(set_content)
            files[set_filename] = f"/api/reports/download/{cnes}_{competencia}/{set_filename}"
        
        # Salva RELEXP.PRN
        if gerar_relexp:
            relexp_path = os.path.join(export_dir, "RELEXP.PRN")
            with open(relexp_path, 'w', encoding='latin-1') as f:
                f.write(relexp_content)
            files["RELEXP.PRN"] = f"/api/reports/download/{cnes}_{competencia}/RELEXP.PRN"
        
        # Salva BPAI_REL.TXT
        if gerar_bpai:
            bpai_path = os.path.join(export_dir, "BPAI_REL.TXT")
            with open(bpai_path, 'w', encoding='latin-1') as f:
                f.write(bpai_rel_content)
            files["BPAI_REL.TXT"] = f"/api/reports/download/{cnes}_{competencia}/BPAI_REL.TXT"
        
        # Salva BPAC_REL.TXT
        if gerar_bpac:
            bpac_path = os.path.join(export_dir, "BPAC_REL.TXT")
            with open(bpac_path, 'w', encoding='latin-1') as f:
                f.write(bpac_rel_content)
            files["BPAC_REL.TXT"] = f"/api/reports/download/{cnes}_{competencia}/BPAC_REL.TXT"
        
        tipo_msg = {
            'remessa': 'Arquivo de remessa',
            'relexp': 'Relatório de controle',
            'bpai': 'Relatório BPA-I',
            'bpac': 'Relatório BPA-C',
            'all': 'Relatórios'
        }
        
        return {
            "success": True,
            "message": f"{tipo_msg.get(tipo, 'Relatórios')} gerado(s) com sucesso para competência {competencia}",
            "stats": {
                "total_registros": total_registros,
                "total_bpas": total_bpas,
                "bpai_count": len(bpai_records),
                "bpac_count": len(bpac_records),
                "campo_controle": campo_controle
            },
            "files": files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/download/{folder}/{filename}")
async def download_report(folder: str, filename: str, user: dict = Depends(get_current_user)):
    """Download de um arquivo de relatório"""
    try:
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        filepath = os.path.join(reports_dir, folder, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Extensões válidas de mês
        extensoes_mes = list(EXTENSOES_MES.values())
        
        # Define media type baseado na extensão
        ext = filename.split('.')[-1].upper() if '.' in filename else ''
        if ext in extensoes_mes:  # JAN, FEV, MAR, etc
            media_type = 'text/plain'
        elif filename.endswith('.PRN'):
            media_type = 'text/plain'
        elif filename.endswith('.TXT'):
            media_type = 'text/plain'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            filepath, 
            media_type=media_type, 
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/list")
async def list_reports(user: dict = Depends(get_current_user)):
    """Lista relatórios gerados"""
    try:
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        
        if not os.path.exists(reports_dir):
            return {"reports": []}
        
        reports = []
        for folder in os.listdir(reports_dir):
            folder_path = os.path.join(reports_dir, folder)
            if os.path.isdir(folder_path):
                # Extrai CNES e competência do nome da pasta
                parts = folder.split('_')
                if len(parts) >= 2:
                    cnes = parts[0]
                    competencia = parts[1]
                    
                    # Lista arquivos na pasta
                    files = []
                    for f in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, f)
                        files.append({
                            "name": f,
                            "size": os.path.getsize(file_path),
                            "download_url": f"/api/reports/download/{folder}/{f}"
                        })
                    
                    reports.append({
                        "folder": folder,
                        "cnes": cnes,
                        "competencia": competencia,
                        "files": files,
                        "created_at": datetime.fromtimestamp(
                            os.path.getctime(folder_path)
                        ).isoformat()
                    })
        
        # Ordena por data de criação (mais recente primeiro)
        reports.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {"reports": reports}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ROTAS DO SISTEMA CBO/USUÁRIOS ==========

from services.user_service import UserService
from services.bpa_service import BPAService as BPAServiceNew
from models.user_schemas import (
    UsuarioCreate, UsuarioResponse, LoginRequest, LoginResponse,
    CBOInfo, ProcedimentoInfo, ValidacaoCBORequest, ValidacaoCBOResponse,
    DBFStatsResponse, ProcedimentoFilter, CBOFilter
)

# Inicializa serviços CBO
user_service = UserService()
bpa_service_new = BPAServiceNew()

@app.post("/api/auth/register", response_model=dict, tags=["Autenticação CBO"])
async def register_cbo_user(user_data: UsuarioCreate):
    """Registra um novo usuário com validação de CBO"""
    try:
        user = user_service.create_user(user_data)
        return {
            "success": True,
            "message": "Usuário cadastrado com sucesso",
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Autenticação CBO"])
async def login_cbo_user(login_data: LoginRequest):
    """Autentica usuário e retorna procedimentos permitidos"""
    try:
        auth_result = user_service.authenticate(login_data.username, login_data.password)
        
        if not auth_result:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        return auth_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/auth/logout", tags=["Autenticação CBO"])
async def logout_cbo_user(authorization: Optional[str] = Header(None)):
    """Faz logout revogando o token"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Token não fornecido")
        
        token = authorization.replace("Bearer ", "")
        success = user_service.revoke_token(token)
        
        if not success:
            raise HTTPException(status_code=400, detail="Erro ao revogar token")
        
        return {"message": "Logout realizado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

def get_current_cbo_user(authorization: Optional[str] = Header(None)) -> UsuarioResponse:
    """Obtém usuário atual pelo token JWT (sistema CBO)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.replace("Bearer ", "")
    user = user_service.get_user_by_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    return user

@app.get("/api/auth/me", response_model=UsuarioResponse, tags=["Autenticação CBO"])
async def get_current_user_info(current_user: UsuarioResponse = Depends(get_current_cbo_user)):
    """Obtém informações do usuário logado"""
    return current_user

@app.get("/api/cbo/my-procedures", tags=["CBO/Procedimentos"])
async def get_my_procedures(current_user: UsuarioResponse = Depends(get_current_cbo_user)):
    """Obtém procedimentos permitidos para o usuário logado"""
    try:
        result = bpa_service_new.get_user_procedures(current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/cbo/validate-procedure", response_model=dict, tags=["CBO/Procedimentos"])
async def validate_procedure(
    request: ValidacaoCBORequest,
    current_user: UsuarioResponse = Depends(get_current_cbo_user)
):
    """Valida se o usuário pode executar um procedimento"""
    try:
        result = bpa_service_new.validate_procedure_for_user(current_user.id, request.procedimento)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/procedures/search", tags=["Procedimentos"])
async def search_procedures(
    q: str = Query(..., description="Termo de busca"),
    limit: int = Query(50, le=200, description="Limite de resultados"),
    my_only: bool = Query(False, description="Apenas meus procedimentos"),
    current_user: dict = Depends(get_current_user)
):
    """Busca procedimentos por código ou descrição"""
    try:
        if my_only and current_user.get('cbo'):
            # Usa o DBFManagerService para obter procedimentos do CBO do usuário
            from services.dbf_manager_service import get_dbf_manager_instance
            dbf_manager = get_dbf_manager_instance()
            
            # Obtém procedimentos permitidos ao CBO do usuário
            procedimentos_permitidos = set(dbf_manager.get_procedimentos_by_cbo(current_user['cbo']))
            
            if not procedimentos_permitidos:
                return []
            
            # Busca procedimentos por termo apenas entre os permitidos
            results = []
            procedimentos_info = dbf_manager.get_procedimentos_info()
            
            for proc_codigo in procedimentos_permitidos:
                proc_info = procedimentos_info.get(proc_codigo, {})
                descricao = proc_info.get('descricao', f'Procedimento {proc_codigo}')
                
                if q.lower() in proc_codigo.lower() or q.lower() in descricao.lower():
                    results.append({
                        'codigo': proc_codigo,
                        'descricao': descricao
                    })
                    if len(results) >= limit:
                        break
            
            return results
        else:
            # Busca normal em todos os procedimentos
            results = []
            procedimentos_info = dbf_manager.get_procedimentos_info()
            
            for proc_codigo, proc_data in procedimentos_info.items():
                descricao = proc_data.get('descricao', f'Procedimento {proc_codigo}')
                
                if q.lower() in proc_codigo.lower() or q.lower() in descricao.lower():
                    results.append({
                        'codigo': proc_codigo,
                        'descricao': descricao
                    })
                    if len(results) >= limit:
                        break
            
            return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/procedures/my-procedures", tags=["Procedimentos"])
async def get_user_allowed_procedures(current_user: dict = Depends(get_current_user)):
    """Retorna todos os procedimentos permitidos ao CBO do usuário"""
    try:
        if not current_user.get('cbo'):
            raise HTTPException(status_code=400, detail="Usuário não possui CBO definido")
        
        # Usa o DBFManagerService para obter procedimentos do CBO
        from services.dbf_manager_service import get_dbf_manager_instance
        dbf_manager = get_dbf_manager_instance()
        
        # Obtém procedimentos permitidos ao CBO do usuário
        procedimentos_permitidos = dbf_manager.get_procedimentos_for_cbo(current_user['cbo'])
        
        if not procedimentos_permitidos:
            return []
        
        # Busca informações detalhadas dos procedimentos
        procedimentos_info = dbf_manager.get_procedimentos_info()
        procedimentos_detalhados = []
        
        for proc_codigo in procedimentos_permitidos:
            proc_data = procedimentos_info.get(proc_codigo, {})
            procedimentos_detalhados.append({
                'codigo': proc_codigo,
                'descricao': proc_data.get('descricao', f'Procedimento {proc_codigo}')
            })
        
        # Ordena por código
        procedimentos_detalhados.sort(key=lambda x: x['codigo'])
        return procedimentos_detalhados
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/admin/cbos", tags=["Admin"])
async def get_all_cbos(
    q: Optional[str] = Query(None, description="Busca por código ou descrição"),
    limit: int = Query(50, ge=1, le=500),
    admin: dict = Depends(get_admin_user)
):
    """Lista CBOs disponíveis no DBF com busca opcional"""
    try:
        from services.dbf_manager_service import get_dbf_manager_instance
        dbf_manager = get_dbf_manager_instance()
        
        if q:
            cbos = dbf_manager.search_cbos(q, limit)
        else:
            cbos = dbf_manager.get_all_cbos()[:limit]
        
        return cbos
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao carregar CBOs: {str(e)}")

@app.put("/api/admin/users/{user_id}", tags=["Admin"])
async def admin_update_user(user_id: int, data: AdminUserUpdate, admin: dict = Depends(get_admin_user)):
    """Atualiza usuário (admin)"""
    try:
        updated_user = update_user(user_id, data.dict(exclude_unset=True))
        if updated_user:
            return {"message": "Usuário atualizado com sucesso", "user": updated_user}
        else:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/procedures/{codigo}/cbos", tags=["Procedimentos"])
async def get_procedure_cbos(
    codigo: str,
    current_user: UsuarioResponse = Depends(get_current_cbo_user)
):
    """Obtém CBOs que podem executar um procedimento"""
    try:
        result = bpa_service_new.get_cbos_for_procedure(codigo)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/dbf/statistics", response_model=dict, tags=["Sistema DBF"])
async def get_dbf_statistics(current_user: UsuarioResponse = Depends(get_current_cbo_user)):
    """Obtém estatísticas dos dados DBF"""
    try:
        result = bpa_service_new.get_dbf_statistics()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/dbf/refresh", tags=["Sistema DBF"])
async def refresh_dbf_data(current_user: UsuarioResponse = Depends(get_current_cbo_user)):
    """Força atualização dos dados DBF (apenas admin)"""
    try:
        if current_user.perfil != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado: apenas administradores")
        
        result = bpa_service_new.refresh_dbf_data()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/admin/users", response_model=List[UsuarioResponse], tags=["Administração"])
async def list_all_users(current_user: UsuarioResponse = Depends(get_current_cbo_user)):
    """Lista todos os usuários (apenas admin)"""
    try:
        if current_user.perfil != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado: apenas administradores")
        
        users = user_service.list_users()
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.put("/api/admin/users/{user_id}/status", tags=["Administração"])
async def toggle_user_status_cbo(
    user_id: int,
    ativo: bool,
    current_user: UsuarioResponse = Depends(get_current_cbo_user)
):
    """Ativa/desativa usuário (apenas admin)"""
    try:
        if current_user.perfil != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado: apenas administradores")
        
        success = user_service.update_user_status(user_id, ativo)
        
        if not success:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        status_text = "ativado" if ativo else "desativado"
        return {"message": f"Usuário {status_text} com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ========== MIDDLEWARE DE VALIDAÇÃO CBO PARA BPA ==========

def validate_bpa_cbo_procedure(user: UsuarioResponse, codigo_procedimento: str):
    """
    Middleware para validar se o usuário pode executar um procedimento antes de criar BPA
    """
    try:
        validation = bpa_service_new.validate_procedure_for_user(user.id, codigo_procedimento)
        if not validation.get('valido', False):
            raise HTTPException(
                status_code=403,
                detail=f"CBO {user.cbo} não autorizado para procedimento {codigo_procedimento}. {validation.get('motivo', '')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na validação CBO: {str(e)}")

# ========== ROTAS BPA COM VALIDAÇÃO CBO ==========

@app.post("/api/bpa-i/create-with-cbo", response_model=BPAIndividualizadoResponse, tags=["BPA Individualizado"])
async def create_bpai_with_cbo_validation(
    bpa: BPAIndividualizadoCreate,
    current_user: UsuarioResponse = Depends(get_current_cbo_user)
):
    """Cria BPA-I com validação de CBO"""
    try:
        # Valida se o usuário pode executar o procedimento
        validate_bpa_cbo_procedure(current_user, bpa.procedimento)
        
        # Força o CBO do usuário logado
        bpa.cbo = current_user.cbo
        bpa.cns_profissional = current_user.cnes or bpa.cns_profissional
        
        # Cria o BPA-I usando a rota existente
        result = db.create_bpa_individualizado(bpa)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/bpa-c/create-with-cbo", response_model=BPAConsolidadoResponse, tags=["BPA Consolidado"])
async def create_bpac_with_cbo_validation(
    bpa: BPAConsolidadoCreate,
    current_user: UsuarioResponse = Depends(get_current_cbo_user)
):
    """Cria BPA-C com validação de CBO"""
    try:
        # Valida se o usuário pode executar o procedimento
        validate_bpa_cbo_procedure(current_user, bpa.procedimento)
        
        # Força o CBO do usuário logado
        bpa.cbo = current_user.cbo
        bpa.cns_profissional = current_user.cnes or bpa.cns_profissional
        
        # Cria o BPA-C usando a rota existente
        result = db.create_bpa_consolidado(bpa)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# =============================================================================
# ENDPOINTS SIGTAP - Filtragem de Procedimentos
# =============================================================================

@app.get("/api/sigtap/procedimentos", tags=["SIGTAP"])
async def get_procedimentos_sigtap(
    tipo_registro: Optional[str] = Query(None, description="Tipo de registro: 01=BPA-C, 02=BPA-I"),
    cbo: Optional[str] = Query(None, description="Código CBO (6 dígitos)"),
    servico: Optional[str] = Query(None, description="Código do serviço (3 dígitos)"),
    classificacao: Optional[str] = Query(None, description="Código da classificação (3 dígitos)"),
    termo_busca: Optional[str] = Query(None, description="Termo para buscar no nome"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    Retorna procedimentos filtrados do SIGTAP
    
    Exemplos:
    - BPA-I para médico clínico: ?tipo_registro=02&cbo=225125
    - BPA-C geral: ?tipo_registro=01
    - Busca por nome: ?termo_busca=CONSULTA
    """
    try:
        sigtap = get_sigtap_filter_service()
        procedimentos = sigtap.get_procedimentos_filtrados(
            tipo_registro=tipo_registro,
            cbo=cbo,
            servico=servico,
            classificacao=classificacao,
            termo_busca=termo_busca
        )
        
        # Limitar resultados
        procedimentos = procedimentos[:limit]
        
        return {
            "total": len(procedimentos),
            "limit": limit,
            "filtros": {
                "tipo_registro": tipo_registro,
                "cbo": cbo,
                "servico": servico,
                "classificacao": classificacao,
                "termo_busca": termo_busca
            },
            "procedimentos": procedimentos
        }
    except Exception as e:
        logger.error(f"Erro ao buscar procedimentos SIGTAP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar procedimentos: {str(e)}")


@app.get("/api/sigtap/procedimentos/por-usuario", tags=["SIGTAP"])
async def get_procedimentos_por_usuario(
    tipo_bpa: str = Query("02", description="01=BPA-C, 02=BPA-I"),
    termo_busca: Optional[str] = Query(None, description="Filtro por nome"),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_cbo_user)
):
    """
    Retorna procedimentos que o usuário logado pode registrar
    Baseado no CBO do usuário
    """
    try:
        sigtap = get_sigtap_filter_service()
        procedimentos = sigtap.get_procedimentos_por_profissional(
            cbo=current_user.cbo,
            tipo_bpa=tipo_bpa,
            termo_busca=termo_busca
        )
        
        procedimentos = procedimentos[:limit]
        
        return {
            "usuario_cbo": current_user.cbo,
            "tipo_bpa": tipo_bpa,
            "total": len(procedimentos),
            "procedimentos": procedimentos
        }
    except Exception as e:
        logger.error(f"Erro ao buscar procedimentos do usuário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/api/sigtap/cbos", tags=["SIGTAP"])
async def get_cbos_sigtap():
    """Retorna lista de todas as ocupações (CBOs)"""
    try:
        sigtap = get_sigtap_filter_service()
        cbos = sigtap.get_cbos()
        return {"total": len(cbos), "cbos": cbos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sigtap/servicos", tags=["SIGTAP"])
async def get_servicos_sigtap():
    """Retorna lista de serviços/classificações"""
    try:
        sigtap = get_sigtap_filter_service()
        servicos = sigtap.get_servicos()
        return {"total": len(servicos), "servicos": servicos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sigtap/registros", tags=["SIGTAP"])
async def get_registros_sigtap():
    """Retorna instrumentos de registro (BPA-C, BPA-I, AIH, etc)"""
    try:
        sigtap = get_sigtap_filter_service()
        registros = sigtap.get_registros()
        return {"total": len(registros), "registros": registros}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sigtap/validar-procedimento", tags=["SIGTAP"])
async def validar_procedimento_sigtap(
    co_procedimento: str = Query(..., description="Código do procedimento"),
    cbo: str = Query(..., description="Código CBO"),
    tipo_bpa: str = Query("02", description="01=BPA-C, 02=BPA-I")
):
    """Verifica se um procedimento é válido para um CBO"""
    try:
        sigtap = get_sigtap_filter_service()
        valido = sigtap.verificar_procedimento_valido(
            co_procedimento=co_procedimento,
            cbo=cbo,
            tipo_bpa=tipo_bpa
        )
        return {
            "valido": valido,
            "procedimento": co_procedimento,
            "cbo": cbo,
            "tipo_bpa": tipo_bpa
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sigtap/estatisticas", tags=["SIGTAP"])
async def get_estatisticas_sigtap():
    """Retorna estatísticas sobre as tabelas SIGTAP carregadas"""
    try:
        sigtap = get_sigtap_filter_service()
        stats = sigtap.get_estatisticas()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Reload desabilitado por problema de encoding no Windows com Python 3.13
    uvicorn.run(app, host="0.0.0.0", port=8000)
