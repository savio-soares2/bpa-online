from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Optional
from models.schemas import ProfissionalCreate, ProfissionalResponse
from services.admin_service import get_admin_service
from auth import decode_jwt_token, get_user_by_id, list_users
from constants.estabelecimentos import ESTABELECIMENTOS

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Obtém usuário atual pelo token JWT"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    # Remove 'Bearer ' se presente
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Decodifica token
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    # Busca usuário
    user = get_user_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Requer que o usuário seja admin"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


# ========== UNIDADES ==========

@router.get("/unidades")
def list_unidades(current_user: dict = Depends(require_admin)):
    """Lista todas as unidades com estatísticas"""
    service = get_admin_service()
    all_users = list_users()
    
    result = []
    for est in ESTABELECIMENTOS:
        # Conta profissionais
        profissionais = service.get_profissionais_by_cnes(est['cnes'])
        
        # Conta usuários vinculados
        usuarios_cnes = [u for u in all_users if u.get('cnes') == est['cnes']]
        
        result.append({
            "cnes": est['cnes'],
            "nome": est['nome'],
            "sigla": est['sigla'],
            "tipo": est['tipo'],
            "profissionais": len(profissionais),
            "usuarios": len(usuarios_cnes)
        })
    
    return result


@router.get("/unidades/{cnes}/usuarios")
def list_usuarios_unidade(
    cnes: str,
    current_user: dict = Depends(require_admin)
):
    """Lista usuários vinculados a uma unidade"""
    all_users = list_users()
    usuarios_cnes = [u for u in all_users if u.get('cnes') == cnes]
    return usuarios_cnes


@router.get("/unidades/{cnes}/stats")
def get_unidade_stats(
    cnes: str,
    current_user: dict = Depends(require_admin)
):
    """Estatísticas da unidade"""
    service = get_admin_service()
    all_users = list_users()
    
    profissionais = service.get_profissionais_by_cnes(cnes)
    usuarios_cnes = [u for u in all_users if u.get('cnes') == cnes]
    
    # Agrupa CBOs
    cbos = {}
    for p in profissionais:
        cbo = p.get('cbo', 'N/A')
        cbos[cbo] = cbos.get(cbo, 0) + 1
    
    return {
        "cnes": cnes,
        "total_profissionais": len(profissionais),
        "total_usuarios": len(usuarios_cnes),
        "cbos": cbos
    }


# ========== PROFISSIONAIS ==========

@router.post("/profissionais", response_model=dict)
def create_profissional(
    data: ProfissionalCreate,
    current_user: dict = Depends(get_current_user)
):
    """Cadastra um profissional (Requer privilégios de admin/gestor ou ser do mesmo CNES)"""
    service = get_admin_service()
    
    # Validação simples de permissão (se usuário tem cnes, só pode adicionar pro mesmo)
    if current_user.get('cnes') and current_user['cnes'] != data.cnes:
        raise HTTPException(status_code=403, detail="Você só pode adicionar profissionais na sua unidade")
        
    id = service.create_profissional(data)
    return {"id": id, "message": "Profissional criado com sucesso"}

@router.get("/profissionais", response_model=List[dict])
def list_profissionais(
    cnes: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Lista profissionais de um CNES"""
    service = get_admin_service()
    
    # Se usuário for restrito a CNES, validar
    if current_user.get('cnes') and current_user['cnes'] != cnes:
         # TODO: Permitir que vejam se tiver permissão multi-unidade. Por enqt bloqueia.
         # Se usuário não tem CNES definido (admin global), passa.
         if not current_user.get('is_admin'):
             raise HTTPException(status_code=403, detail="Acesso não autorizado a esta unidade")

    return service.get_profissionais_by_cnes(cnes)

@router.delete("/profissionais/{id}")
def delete_profissional(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove um profissional"""
    if not current_user.get('is_admin'):
         raise HTTPException(status_code=403, detail="Apenas administradores podem remover")
         
    service = get_admin_service()
    if service.delete_profissional(id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Profissional não encontrado")

@router.get("/cbos")
def list_cbos_unidade(
    cnes: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Lista CBOs disponíveis na unidade (baseado nos profissionais cadastrados)"""
    service = get_admin_service()
    return service.get_cbos_by_cnes(cnes)

