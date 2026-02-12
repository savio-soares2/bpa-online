from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from typing import List, Optional
import shutil
import os
from pathlib import Path

from services.sigtap_manager_service import get_sigtap_manager
from services.sigtap_filter_service import get_sigtap_filter_service

router = APIRouter(prefix="/api/sigtap", tags=["sigtap"])

@router.get("/competencias")
def list_competencias():
    """Lista todas as competências SIGTAP instaladas"""
    manager = get_sigtap_manager()
    return {
        "active": manager.get_active_competencia(),
        "available": manager.get_available_competencias()
    }

@router.post("/competencias")
async def upload_competencia(
    file: UploadFile = File(...),
    competencia: str = Form(...)  # Ex: 202512
):
    """Upload de nova tabela SIGTAP (arquivo ZIP)"""
    manager = get_sigtap_manager()
    
    # Validar nome da competência (YYYYMM)
    if not competencia.isdigit() or len(competencia) != 6:
        raise HTTPException(status_code=400, detail="Competência deve estar no formato YYYYMM (ex: 202512)")
    
    # Salvar ZIP temporariamente
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = manager.import_competencia(str(temp_path), competencia)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            os.remove(temp_path)

@router.put("/competencias/{competencia}/activate")
def activate_competencia(competencia: str):
    """Define uma competência como ativa"""
    manager = get_sigtap_manager()
    try:
        manager.set_active_competencia(competencia)
        return {"success": True, "active": competencia}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Competência não encontrada")

@router.get("/procedimentos")
def search_procedimentos(
    q: Optional[str] = Query(None, description="Termo de busca (nome ou código)"),
    page: int = 1,
    limit: int = 50,
    cbo: Optional[str] = None,
    servico: Optional[str] = None,
    classificacao: Optional[str] = None,
    tipo_registro: Optional[List[str]] = Query(default=None), 
    competencia: Optional[str] = None,
    sort_field: Optional[str] = Query(None, enum=['nome', 'valor', 'codigo']),
    sort_order: Optional[str] = Query('asc', enum=['asc', 'desc'])
):
    """Busca procedimentos com filtros (agora suporta multiselect em tipo_registro) e paginação"""
    service = get_sigtap_filter_service()
    
    try:
        results = service.get_procedimentos_filtrados(
            tipo_registro=tipo_registro,
            cbo=cbo,
            servico=servico,
            classificacao=classificacao,
            termo_busca=q,
            competencia=competencia,
            sort_field=sort_field,
            sort_order=sort_order
        )
        
        # Paginação manual (já que o service retorna tudo filtrado)
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated_data = results[start:end]
        
        return {
            "data": paginated_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/estatisticas")
def get_stats(competencia: Optional[str] = None):
    """Retorna estatísticas da tabela"""
    service = get_sigtap_filter_service()
    return service.get_estatisticas(competencia)

@router.get("/cbos")
def list_cbos(competencia: Optional[str] = None):
    service = get_sigtap_filter_service()
    return service.get_cbos(competencia)

@router.get("/servicos")
def list_servicos(competencia: Optional[str] = None):
    service = get_sigtap_filter_service()
    return service.get_servicos(competencia)

@router.get("/registros")
def list_registros(competencia: Optional[str] = None):
    """Lista todos os tipos de registros disponíveis (BPAI, BPAC, etc)"""
    service = get_sigtap_filter_service()
    return service.get_registros(competencia)
