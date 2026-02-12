import pytest
from database import BPADatabase
from services.admin_service import get_admin_service
from services.consolidation_service import get_consolidation_service
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
db = BPADatabase()

@pytest.fixture
def clean_db():
    """Limpa dados de teste"""
    # Limpa profissionais do CNES de teste
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profissionais WHERE cnes = 'TESTE12'")
        cursor.execute("DELETE FROM bpa_consolidado WHERE prd_uid = 'TESTE12'")
        cursor.execute("DELETE FROM bpa_individualizado WHERE prd_uid = 'TESTE12'")
        conn.commit()
    yield

def test_admin_profissional_flow(clean_db):
    """Teste do fluxo de administração de profissionais"""
    
    # 1. Cria usuário simulado (no teste integracao seria via API)
    # Aqui testamos o service
    
    # 2. Service: Criar Profissional
    service = get_admin_service()
    prof_data = {
        "cnes": "TESTE12",
        "cns": "700000000000001",
        "nome": "MEDICO TESTE",
        "cbo": "225125",
        "ine": "0000000000",
        "conselho": "12345",
        "uf_conselho": "TO"
    }
    
    # Mock do objeto Pydantic
    class MockProf:
        def __init__(self, data):
            self.__dict__ = data
        def dict(self):
            return self.__dict__
    
    prof_obj = MockProf(prof_data)
    
    service.create_profissional(prof_obj)
    
    # 3. Listar e verificar
    profs = service.get_profissionais_by_cnes("TESTE12")
    assert len(profs) == 1
    assert profs[0]['nome'] == "MEDICO TESTE"
    assert profs[0]['conselho'] == "12345"
    
    # 4. Verificar CBOs list
    cbos = service.get_cbos_by_cnes("TESTE12")
    assert len(cbos) == 1
    assert cbos[0]['cbo'] == "225125"

def test_bpa_consolidado_api(clean_db):
    """Teste de criação de BPA Consolidado via API"""
    
    # Mock auth de usuário existente ou criar um token
    # Para simplificar, vou usar o db direto ou mockar o auth no client
    # Complicado mockar auth no TestClient sem token real.
    # Vou testar o endpoint se tiver um jeito de burlar auth ou gerar token
    
    # Gerar token para admin default e criar user teste
    login_res = client.post("/api/auth/login", json={"email": "admin@bpa.local", "senha": "admin123"})
    if login_res.status_code != 200:
        pytest.skip("Admin default não criado ou senha errada")
        
    admin_token = login_res.json()['access_token']
    
    # Criar user teste
    client.post("/api/admin/users", 
        json={
            "email": "teste_bpa@local.com", 
            "senha": "123", 
            "nome": "Tester", 
            "cnes": "TESTE12", 
            "cbo": "000000"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Login com user teste
    login_user = client.post("/api/auth/login", json={"email": "teste_bpa@local.com", "senha": "123"})
    user_token = login_user.json()['access_token']
    
    # Criar BPA-C
    bpa_data = {
        "cnes": "TESTE12", # Ignorado pelo backend que pega do token
        "competencia": "202512",
        "cns_profissional": None, # Opcional
        "cbo": "225125",
        "procedimento": "0301010072",
        "idade": "020",
        "quantidade": 10,
        "folha": 1
    }
    
    res = client.post("/api/bpa/consolidado", json=bpa_data, headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["cnes"] == "TESTE12"
    assert data["quantidade"] == 10
    
    # Listar
    list_res = client.get("/api/bpa/consolidado?competencia=202512", headers={"Authorization": f"Bearer {user_token}"})
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert items[0]['cbo'] == "225125"

