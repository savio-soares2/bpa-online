"""
Serviço de administração para gestão de profissionais e usuários
"""
from typing import List, Optional
from database import BPADatabase
from models.schemas import ProfissionalCreate, ProfissionalResponse
from auth import get_user_by_email, create_user, update_user

db = BPADatabase()

class AdminService:
    def __init__(self):
        pass

    # Gestão de Profissionais
    def create_profissional(self, data: ProfissionalCreate) -> int:
        return db.save_profissional(data.dict())

    def get_profissionais_by_cnes(self, cnes: str) -> List[dict]:
        return db.list_profissionais(cnes)

    def delete_profissional(self, id: int) -> bool:
        return db.delete_profissional(id)
    
    # Helpers para Formulários
    def get_cbos_by_cnes(self, cnes: str) -> List[dict]:
        return db.list_cbos_by_cnes(cnes)

_admin_service = AdminService()

def get_admin_service():
    return _admin_service
