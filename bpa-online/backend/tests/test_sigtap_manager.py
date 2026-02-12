import pytest
import os
import shutil
import tempfile
import zipfile
import json
from pathlib import Path
from services.sigtap_manager_service import SigtapManagerService

class TestSigtapManager:
    @pytest.fixture
    def manager(self):
        # Setup: Criar diretório temporário
        self.temp_dir = tempfile.mkdtemp()
        service = SigtapManagerService(root_dir=self.temp_dir)
        yield service
        # Teardown: Remover diretório
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_dummy_zip(self, filename="sigtap.zip"):
        path = os.path.join(self.temp_dir, filename)
        with zipfile.ZipFile(path, 'w') as zf:
            zf.writestr('tb_procedimento.txt', 'DUMMY DATA')
            zf.writestr('tb_ocupacao.txt', 'DUMMY DATA')
        return path

    def test_initial_state(self, manager):
        assert manager.get_available_competencias() == []
        assert manager.get_active_competencia() is None

    def test_import_competencia(self, manager):
        zip_path = self.create_dummy_zip()
        
        result = manager.import_competencia(zip_path, "202512")
        
        assert result["success"] == True
        assert result["competencia"] == "202512"
        
        available = manager.get_available_competencias()
        assert len(available) == 1
        assert available[0]["competencia"] == "202512"
        
        # Verifica se definiu como ativa automaticamente (pois é a primeira)
        assert manager.get_active_competencia() == "202512"

    def test_switch_active_competencia(self, manager):
        # Importar duas competências
        zip_path = self.create_dummy_zip()
        manager.import_competencia(zip_path, "202511")
        manager.import_competencia(zip_path, "202512")
        
        # Padrão deve ser a primeira (202511) setada auto, ou talvez lógica mudou?
        # Minha lógica diz: "Define como ativa automaticamente se for a única"
        # Então a primeira (202511) setou active. A segunda não deve mudar auto.
        assert manager.get_active_competencia() == "202511"
        
        # Mudar para 202512
        manager.set_active_competencia("202512")
        assert manager.get_active_competencia() == "202512"
        
        # Verificar persistência
        new_manager = SigtapManagerService(root_dir=manager.base_dir) # Reabre mesmo dir
        assert new_manager.get_active_competencia() == "202512"

    def test_get_sigtap_dir(self, manager):
        zip_path = self.create_dummy_zip()
        manager.import_competencia(zip_path, "202512")
        
        path = manager.get_sigtap_dir("202512")
        assert "202512" in path
        assert os.path.exists(path)
        
        # Testar active
        path_active = manager.get_sigtap_dir()
        assert path_active == path
