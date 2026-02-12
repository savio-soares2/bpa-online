import pytest
import os
import tempfile
import shutil
from services.sigtap_parser import SigtapParser

class TestSigtapParser:
    @pytest.fixture
    def parser(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Criar Layout Dummy
        layout_content = "Coluna,Tamanho,Inicio,Fim,Tipo\n" \
                         "CO_PROCEDIMENTO,10,1,10,C\n" \
                         "NO_PROCEDIMENTO,20,11,30,C\n" \
                         "VL_SA,10,31,40,N\n"
        
        with open(os.path.join(self.temp_dir, 'tb_procedimento_layout.txt'), 'w', encoding='utf-8') as f:
            f.write(layout_content)
            
        # Criar Dados Dummy (Fixed Width)
        # 1-10: 0301010072
        # 11-30: CONSULTA MEDICA     (20 chars)
        # 31-40: 0000001000          (10 chars = 10,00)
        data_content = "0301010072CONSULTA MEDICA     0000001000\n" \
                       "0301010048CONSULTA ORTOPEDIA  0000002000"
                       
        with open(os.path.join(self.temp_dir, 'tb_procedimento.txt'), 'w', encoding='latin-1') as f:
            f.write(data_content)
            
        parser = SigtapParser(self.temp_dir)
        yield parser
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_procedimentos(self, parser):
        procs = parser.parse_procedimentos()
        assert len(procs) == 2
        
        p1 = procs[0]
        assert p1['CO_PROCEDIMENTO'] == '0301010072'
        assert p1['NO_PROCEDIMENTO'] == 'CONSULTA MEDICA'
        
    def test_get_procedimento_valor(self, parser):
        # O parser divide por 100
        valores = parser.get_procedimento_valor('0301010072')
        assert valores['valor_ambulatorio'] == 10.00
        
        valores2 = parser.get_procedimento_valor('0301010048')
        assert valores2['valor_ambulatorio'] == 20.00
