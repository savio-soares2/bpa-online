import pytest
from unittest.mock import MagicMock
from services.sigtap_filter_service import SigtapFilterService

class TestSigtapFilter:
    @pytest.fixture
    def service(self):
        svc = SigtapFilterService()
        mock_parser = MagicMock()
        
        # Dados simulados com valores diferentes
        mock_parser.parse_procedimentos.return_value = [
            {'CO_PROCEDIMENTO': '01', 'NO_PROCEDIMENTO': 'CONSULTA A', 'VL_SA': '1000'},
            {'CO_PROCEDIMENTO': '02', 'NO_PROCEDIMENTO': 'CONSULTA B', 'VL_SA': '2000'},
            {'CO_PROCEDIMENTO': '03', 'NO_PROCEDIMENTO': 'CIRURGIA', 'VL_SA': '5000'},
        ]
        
        # Relacionamentos
        mock_parser.parse_procedimento_registro.return_value = [
            {'CO_PROCEDIMENTO': '01', 'CO_REGISTRO': '01'}, # BPA-C
            {'CO_PROCEDIMENTO': '02', 'CO_REGISTRO': '02'}, # BPA-I
            {'CO_PROCEDIMENTO': '03', 'CO_REGISTRO': '01'}, # BPA-C
            {'CO_PROCEDIMENTO': '03', 'CO_REGISTRO': '02'}, # BPA-I
        ]
        
        # CBO Dummy
        mock_parser.parse_procedimento_ocupacao.return_value = []
        # Servico Dummy
        mock_parser.parse_procedimento_servico.return_value = []
        
        svc._parsers["TESTE"] = mock_parser
        return svc

    def test_multiselect_registro(self, service):
        # 1. Filtra só BPA-I (02) -> Deve vir 02 e 03
        res = service.get_procedimentos_filtrados(
            tipo_registro=['02'], competencia='TESTE'
        )
        ids = sorted([p['CO_PROCEDIMENTO'] for p in res])
        assert ids == ['02', '03']
        
        # 2. Filtra BPA-I e BPA-C -> Deve vir todos (01 é C, 02 é I, 03 é ambos)
        res_all = service.get_procedimentos_filtrados(
            tipo_registro=['01', '02'], competencia='TESTE'
        )
        assert len(res_all) == 3

    def test_sorting_valor(self, service):
        # Ascendente
        res_asc = service.get_procedimentos_filtrados(
            competencia='TESTE',
            sort_field='valor',
            sort_order='asc'
        )
        assert res_asc[0]['CO_PROCEDIMENTO'] == '01' # 10.00
        assert res_asc[2]['CO_PROCEDIMENTO'] == '03' # 50.00
        
        # Descendente
        res_desc = service.get_procedimentos_filtrados(
            competencia='TESTE',
            sort_field='valor',
            sort_order='desc'
        )
        assert res_desc[0]['CO_PROCEDIMENTO'] == '03' # 50.00
        assert res_desc[2]['CO_PROCEDIMENTO'] == '01' # 10.00

    def test_sorting_nome(self, service):
        res = service.get_procedimentos_filtrados(
            competencia='TESTE',
            sort_field='nome',
            sort_order='asc'
        )
        # CIRURGIA vem antes de CONSULTA A
        assert res[0]['NO_PROCEDIMENTO'] == 'CIRURGIA'
