#!/usr/bin/env python
"""
Teste de Endpoints - BPA Online Django
Testa todos os módulos da API para validar a migração

Uso:
    python teste_endpoints.py [--base-url http://localhost:8000]
"""
import sys
import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
except ImportError:
    print("ERRO: Módulo 'requests' não encontrado. Instale com: pip install requests")
    sys.exit(1)


class TestStatus(Enum):
    PASSED = "✅"
    FAILED = "❌"
    SKIPPED = "⏭️"
    WARNING = "⚠️"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    response_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    details: Dict = field(default_factory=dict)


class BPAEndpointTester:
    """Testador de endpoints da API BPA Online"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.token: Optional[str] = None
        self.results: List[TestResult] = []
        self.session = requests.Session()
        
        # Credenciais de teste
        self.admin_email = "admin@bpaonline.local"
        self.admin_password = "admin123"
        
    def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[Optional[requests.Response], float]:
        """Faz uma requisição e retorna response + tempo em ms"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = kwargs.pop('headers', {})
        
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        
        start = datetime.now()
        try:
            response = self.session.request(method, url, headers=headers, timeout=30, **kwargs)
            elapsed = (datetime.now() - start).total_seconds() * 1000
            return response, elapsed
        except requests.exceptions.ConnectionError:
            return None, 0
        except requests.exceptions.Timeout:
            return None, 30000
        except Exception as e:
            return None, 0
    
    def _add_result(self, name: str, status: TestStatus, message: str, 
                    response: Optional[requests.Response] = None, 
                    response_time: float = 0, details: Dict = None):
        """Adiciona resultado de teste"""
        result = TestResult(
            name=name,
            status=status,
            message=message,
            response_code=response.status_code if response else None,
            response_time_ms=response_time,
            details=details or {}
        )
        self.results.append(result)
        
        # Print imediato
        status_icon = status.value
        code_str = f"[{response.status_code}]" if response else "[---]"
        time_str = f"{response_time:.0f}ms" if response_time > 0 else "---"
        print(f"  {status_icon} {name}: {message} {code_str} {time_str}")
    
    # ==================== MÓDULO: HEALTH ====================
    def test_health(self):
        """Testa endpoint de health check"""
        print("\n" + "="*60)
        print("MÓDULO: HEALTH CHECK")
        print("="*60)
        
        response, time_ms = self._request('GET', 'health')
        
        if response is None:
            self._add_result("Health Check", TestStatus.FAILED, 
                           "Servidor não responde - verifique se Django está rodando")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                self._add_result("Health Check", TestStatus.PASSED, 
                               f"Servidor OK", response, time_ms, data)
                return True
            except:
                self._add_result("Health Check", TestStatus.WARNING, 
                               "Resposta não é JSON válido", response, time_ms)
                return True
        else:
            self._add_result("Health Check", TestStatus.FAILED, 
                           f"Status inesperado", response, time_ms)
            return False
    
    # ==================== MÓDULO: AUTENTICAÇÃO ====================
    def test_auth(self):
        """Testa módulo de autenticação"""
        print("\n" + "="*60)
        print("MÓDULO: AUTENTICAÇÃO")
        print("="*60)
        
        # 1. Login com credenciais válidas
        response, time_ms = self._request('POST', 'auth/login', json={
            'email': self.admin_email,
            'password': self.admin_password
        })
        
        if response is None:
            self._add_result("Login", TestStatus.FAILED, "Servidor não responde")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get('access_token') or data.get('token')
                if self.token:
                    self._add_result("Login", TestStatus.PASSED, 
                                   f"Token obtido", response, time_ms)
                else:
                    self._add_result("Login", TestStatus.WARNING, 
                                   "Login OK mas token não encontrado na resposta", 
                                   response, time_ms, data)
                    return False
            except:
                self._add_result("Login", TestStatus.FAILED, 
                               "Resposta não é JSON válido", response, time_ms)
                return False
        else:
            self._add_result("Login", TestStatus.FAILED, 
                           f"Falha no login", response, time_ms, 
                           {'body': response.text[:200]})
            return False
        
        # 2. Get /me com token
        response, time_ms = self._request('GET', 'auth/me')
        if response and response.status_code == 200:
            data = response.json()
            self._add_result("Get Me", TestStatus.PASSED, 
                           f"Usuário: {data.get('email', 'N/A')}", response, time_ms)
        else:
            self._add_result("Get Me", TestStatus.FAILED, 
                           "Falha ao obter dados do usuário", response, time_ms)
        
        # 3. Login com credenciais inválidas
        response, time_ms = self._request('POST', 'auth/login', json={
            'email': 'invalid@test.com',
            'password': 'wrongpassword'
        })
        if response and response.status_code in [401, 400]:
            self._add_result("Login Inválido", TestStatus.PASSED, 
                           "Rejeita credenciais inválidas corretamente", response, time_ms)
        else:
            self._add_result("Login Inválido", TestStatus.WARNING, 
                           "Deveria retornar 401 para credenciais inválidas", response, time_ms)
        
        return True
    
    # ==================== MÓDULO: DASHBOARD ====================
    def test_dashboard(self):
        """Testa endpoints de dashboard"""
        print("\n" + "="*60)
        print("MÓDULO: DASHBOARD")
        print("="*60)
        
        # 1. Dashboard stats
        response, time_ms = self._request('GET', 'dashboard/stats')
        if response and response.status_code == 200:
            data = response.json()
            self._add_result("Dashboard Stats", TestStatus.PASSED, 
                           f"Stats obtidas", response, time_ms,
                           {'keys': list(data.keys()) if isinstance(data, dict) else []})
        else:
            self._add_result("Dashboard Stats", TestStatus.FAILED, 
                           "Falha ao obter stats", response, time_ms)
        
        # 2. BPA Stats (precisa de cnes)
        response, time_ms = self._request('GET', 'bpa/stats', params={'cnes': '2560038'})
        if response and response.status_code == 200:
            self._add_result("BPA Stats", TestStatus.PASSED, 
                           "Stats BPA obtidas", response, time_ms)
        elif response and response.status_code == 400:
            self._add_result("BPA Stats", TestStatus.WARNING, 
                           "Requer parâmetro CNES válido", response, time_ms)
        else:
            self._add_result("BPA Stats", TestStatus.FAILED, 
                           "Falha ao obter BPA stats", response, time_ms)
    
    # ==================== MÓDULO: ADMIN ====================
    def test_admin(self):
        """Testa endpoints administrativos"""
        print("\n" + "="*60)
        print("MÓDULO: ADMIN")
        print("="*60)
        
        # 1. Database Overview
        response, time_ms = self._request('GET', 'admin/database-overview')
        if response and response.status_code == 200:
            data = response.json()
            self._add_result("Database Overview", TestStatus.PASSED, 
                           "Visão geral do banco obtida", response, time_ms,
                           {'totals': data.get('totals', {})})
        else:
            self._add_result("Database Overview", TestStatus.FAILED, 
                           "Falha ao obter visão do banco", response, time_ms)
        
        # 2. Lista de Usuários
        response, time_ms = self._request('GET', 'admin/users')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('count', 'N/A')
            self._add_result("Lista Usuários", TestStatus.PASSED, 
                           f"Usuários: {count}", response, time_ms)
        else:
            self._add_result("Lista Usuários", TestStatus.FAILED, 
                           "Falha ao listar usuários", response, time_ms)
        
        # 3. Lista de CBOs
        response, time_ms = self._request('GET', 'admin/cbos')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Lista CBOs", TestStatus.PASSED, 
                           f"CBOs: {count}", response, time_ms)
        else:
            self._add_result("Lista CBOs", TestStatus.FAILED, 
                           "Falha ao listar CBOs", response, time_ms)
        
        # 4. Lista de Profissionais (admin)
        response, time_ms = self._request('GET', 'admin/profissionais')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('total', 'N/A')
            self._add_result("Lista Profissionais (Admin)", TestStatus.PASSED, 
                           f"Profissionais: {count}", response, time_ms)
        else:
            self._add_result("Lista Profissionais (Admin)", TestStatus.FAILED, 
                           "Falha ao listar profissionais", response, time_ms)
        
        # 5. Dashboard Stats Admin
        response, time_ms = self._request('GET', 'admin/dashboard/stats')
        if response and response.status_code == 200:
            self._add_result("Dashboard Stats (Admin)", TestStatus.PASSED, 
                           "Stats admin obtidas", response, time_ms)
        else:
            self._add_result("Dashboard Stats (Admin)", TestStatus.FAILED, 
                           "Falha ao obter stats admin", response, time_ms)
        
        # 6. Histórico de Extrações
        response, time_ms = self._request('GET', 'admin/historico-extracoes')
        if response and response.status_code == 200:
            self._add_result("Histórico Extrações", TestStatus.PASSED, 
                           "Histórico obtido", response, time_ms)
        else:
            self._add_result("Histórico Extrações", TestStatus.FAILED, 
                           "Falha ao obter histórico", response, time_ms)
    
    # ==================== MÓDULO: PROFISSIONAIS ====================
    def test_profissionais(self):
        """Testa endpoints de profissionais"""
        print("\n" + "="*60)
        print("MÓDULO: PROFISSIONAIS")
        print("="*60)
        
        # 1. Lista de Profissionais
        response, time_ms = self._request('GET', 'profissionais')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('total', 'N/A')
            self._add_result("Lista Profissionais", TestStatus.PASSED, 
                           f"Total: {count}", response, time_ms)
            
            # Testa detalhe do primeiro profissional
            if isinstance(data, list) and len(data) > 0:
                cns = data[0].get('cns') or data[0].get('CNS_PROF')
                if cns:
                    response2, time_ms2 = self._request('GET', f'profissionais/{cns}')
                    if response2 and response2.status_code == 200:
                        self._add_result("Detalhe Profissional", TestStatus.PASSED, 
                                       f"CNS: {cns}", response2, time_ms2)
                    else:
                        self._add_result("Detalhe Profissional", TestStatus.FAILED, 
                                       f"Falha ao obter profissional {cns}", response2, time_ms2)
        else:
            self._add_result("Lista Profissionais", TestStatus.FAILED, 
                           "Falha ao listar profissionais", response, time_ms)
    
    # ==================== MÓDULO: PACIENTES ====================
    def test_pacientes(self):
        """Testa endpoints de pacientes"""
        print("\n" + "="*60)
        print("MÓDULO: PACIENTES")
        print("="*60)
        
        # 1. Busca de Pacientes
        response, time_ms = self._request('GET', 'pacientes/search', params={'q': 'a', 'limit': 5})
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('total', 'N/A')
            self._add_result("Busca Pacientes", TestStatus.PASSED, 
                           f"Encontrados: {count}", response, time_ms)
            
            # Testa detalhe do primeiro paciente
            if isinstance(data, list) and len(data) > 0:
                cns = data[0].get('cns') or data[0].get('PA_CODUNI')
                if cns:
                    response2, time_ms2 = self._request('GET', f'pacientes/{cns}')
                    if response2 and response2.status_code == 200:
                        self._add_result("Detalhe Paciente", TestStatus.PASSED, 
                                       f"CNS: {cns}", response2, time_ms2)
                    elif response2 and response2.status_code == 404:
                        self._add_result("Detalhe Paciente", TestStatus.WARNING, 
                                       "Paciente não encontrado (pode ser normal)", response2, time_ms2)
                    else:
                        self._add_result("Detalhe Paciente", TestStatus.FAILED, 
                                       f"Falha ao obter paciente", response2, time_ms2)
        else:
            self._add_result("Busca Pacientes", TestStatus.FAILED, 
                           "Falha na busca", response, time_ms)
    
    # ==================== MÓDULO: PROCEDIMENTOS ====================
    def test_procedimentos(self):
        """Testa endpoints de procedimentos"""
        print("\n" + "="*60)
        print("MÓDULO: PROCEDIMENTOS")
        print("="*60)
        
        # 1. Busca de Procedimentos
        response, time_ms = self._request('GET', 'procedimentos/search', params={'q': 'consulta', 'limit': 5})
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Busca Procedimentos", TestStatus.PASSED, 
                           f"Encontrados: {count}", response, time_ms)
        else:
            self._add_result("Busca Procedimentos", TestStatus.FAILED, 
                           "Falha na busca", response, time_ms)
        
        # 2. Detalhe de Procedimento específico
        response, time_ms = self._request('GET', 'procedimentos/0301010072')
        if response and response.status_code == 200:
            data = response.json()
            valor = data.get('valor_sa') or data.get('valor_total') or data.get('VL_SA', 0)
            self._add_result("Detalhe Procedimento", TestStatus.PASSED, 
                           f"Consulta Médica - Valor: R$ {valor}", response, time_ms)
        else:
            self._add_result("Detalhe Procedimento", TestStatus.FAILED, 
                           "Falha ao obter procedimento", response, time_ms)
    
    # ==================== MÓDULO: SIGTAP ====================
    def test_sigtap(self):
        """Testa endpoints SIGTAP"""
        print("\n" + "="*60)
        print("MÓDULO: SIGTAP")
        print("="*60)
        
        # 1. Competências
        response, time_ms = self._request('GET', 'sigtap/competencias')
        if response and response.status_code == 200:
            data = response.json()
            self._add_result("SIGTAP Competências", TestStatus.PASSED, 
                           f"Competências listadas", response, time_ms, data)
        else:
            self._add_result("SIGTAP Competências", TestStatus.FAILED, 
                           "Falha ao listar competências", response, time_ms)
        
        # 2. Procedimentos SIGTAP
        response, time_ms = self._request('GET', 'sigtap/procedimentos', params={'limit': 10})
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('total', 'N/A')
            self._add_result("SIGTAP Procedimentos", TestStatus.PASSED, 
                           f"Procedimentos: {count}", response, time_ms)
        else:
            self._add_result("SIGTAP Procedimentos", TestStatus.FAILED, 
                           "Falha ao listar procedimentos SIGTAP", response, time_ms)
        
        # 3. Estatísticas SIGTAP
        response, time_ms = self._request('GET', 'sigtap/estatisticas')
        if response and response.status_code == 200:
            data = response.json()
            self._add_result("SIGTAP Estatísticas", TestStatus.PASSED, 
                           f"Estatísticas obtidas", response, time_ms, data)
        else:
            self._add_result("SIGTAP Estatísticas", TestStatus.FAILED, 
                           "Falha ao obter estatísticas", response, time_ms)
        
        # 4. Registros SIGTAP
        response, time_ms = self._request('GET', 'sigtap/registros')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("SIGTAP Registros", TestStatus.PASSED, 
                           f"Registros: {count}", response, time_ms)
        else:
            self._add_result("SIGTAP Registros", TestStatus.FAILED, 
                           "Falha ao listar registros", response, time_ms)
    
    # ==================== MÓDULO: BPA ====================
    def test_bpa(self):
        """Testa endpoints de BPA"""
        print("\n" + "="*60)
        print("MÓDULO: BPA (Individualizado e Consolidado)")
        print("="*60)
        
        # 1. BPA Individualizado (precisa de competencia)
        response, time_ms = self._request('GET', 'bpa/individualizado', params={
            'competencia': '202501', 'limit': 10
        })
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                count = data.get('total', len(data.get('items', [])))
            else:
                count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("BPA Individualizado", TestStatus.PASSED, 
                           f"Registros: {count}", response, time_ms)
        else:
            self._add_result("BPA Individualizado", TestStatus.FAILED, 
                           "Falha ao listar BPA-I", response, time_ms)
        
        # 2. BPA Consolidado (precisa de competencia)
        response, time_ms = self._request('GET', 'bpa/consolidado', params={
            'competencia': '202501', 'limit': 10
        })
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                count = data.get('total', len(data.get('items', [])))
            else:
                count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("BPA Consolidado", TestStatus.PASSED, 
                           f"Registros: {count}", response, time_ms)
        else:
            self._add_result("BPA Consolidado", TestStatus.FAILED, 
                           "Falha ao listar BPA-C", response, time_ms)
        
        # 3. Inconsistências (precisa de cnes e competencia)
        response, time_ms = self._request('GET', 'bpa/inconsistencies', params={
            'cnes': '2560038', 'competencia': '202501'
        })
        if response and response.status_code == 200:
            data = response.json()
            count = data.get('summary', {}).get('total', 0) if isinstance(data, dict) else 'N/A'
            self._add_result("BPA Inconsistências", TestStatus.PASSED, 
                           f"Inconsistências: {count}", response, time_ms)
        else:
            self._add_result("BPA Inconsistências", TestStatus.FAILED, 
                           "Falha ao listar inconsistências", response, time_ms)
    
    # ==================== MÓDULO: BISERVER ====================
    def test_biserver(self):
        """Testa endpoints do BiServer"""
        print("\n" + "="*60)
        print("MÓDULO: BISERVER")
        print("="*60)
        
        # 1. Test Connection
        response, time_ms = self._request('GET', 'biserver/test-connection')
        if response and response.status_code == 200:
            data = response.json()
            status = data.get('status', 'N/A')
            self._add_result("BiServer Conexão", TestStatus.PASSED, 
                           f"Status: {status}", response, time_ms)
        elif response and response.status_code in [503, 502]:
            self._add_result("BiServer Conexão", TestStatus.WARNING, 
                           "BiServer não disponível (pode ser normal)", response, time_ms)
        else:
            self._add_result("BiServer Conexão", TestStatus.FAILED, 
                           "Falha ao testar conexão", response, time_ms)
        
        # 2. Export Options
        response, time_ms = self._request('GET', 'biserver/export-options')
        if response and response.status_code == 200:
            self._add_result("BiServer Export Options", TestStatus.PASSED, 
                           "Opções obtidas", response, time_ms)
        else:
            self._add_result("BiServer Export Options", TestStatus.FAILED, 
                           "Falha ao obter opções", response, time_ms)
        
        # 3. Count (sem parâmetros, deve retornar erro ou 0)
        response, time_ms = self._request('GET', 'biserver/count', params={
            'competencia': '202501',
            'cnes': '2560038'
        })
        if response and response.status_code in [200, 400]:
            self._add_result("BiServer Count", TestStatus.PASSED, 
                           "Endpoint responde", response, time_ms)
        else:
            self._add_result("BiServer Count", TestStatus.FAILED, 
                           "Falha no count", response, time_ms)
    
    # ==================== MÓDULO: EXPORT ====================
    def test_export(self):
        """Testa endpoints de exportação"""
        print("\n" + "="*60)
        print("MÓDULO: EXPORT")
        print("="*60)
        
        # 1. Lista de Exports
        response, time_ms = self._request('GET', 'export/list')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Lista Exports", TestStatus.PASSED, 
                           f"Exports: {count}", response, time_ms)
        else:
            self._add_result("Lista Exports", TestStatus.FAILED, 
                           "Falha ao listar exports", response, time_ms)
    
    # ==================== MÓDULO: REFERÊNCIAS ====================
    def test_referencias(self):
        """Testa endpoints de referências"""
        print("\n" + "="*60)
        print("MÓDULO: REFERÊNCIAS")
        print("="*60)
        
        # 1. Raça/Cor
        response, time_ms = self._request('GET', 'referencias/raca-cor')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Referência Raça/Cor", TestStatus.PASSED, 
                           f"Itens: {count}", response, time_ms)
        else:
            self._add_result("Referência Raça/Cor", TestStatus.FAILED, 
                           "Falha ao obter raça/cor", response, time_ms)
        
        # 2. Sexo
        response, time_ms = self._request('GET', 'referencias/sexo')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Referência Sexo", TestStatus.PASSED, 
                           f"Itens: {count}", response, time_ms)
        else:
            self._add_result("Referência Sexo", TestStatus.FAILED, 
                           "Falha ao obter sexo", response, time_ms)
        
        # 3. Caráter Atendimento
        response, time_ms = self._request('GET', 'referencias/carater-atendimento')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Referência Caráter", TestStatus.PASSED, 
                           f"Itens: {count}", response, time_ms)
        else:
            self._add_result("Referência Caráter", TestStatus.FAILED, 
                           "Falha ao obter caráter", response, time_ms)
    
    # ==================== MÓDULO: CONSOLIDAÇÃO ====================
    def test_consolidacao(self):
        """Testa endpoints de consolidação"""
        print("\n" + "="*60)
        print("MÓDULO: CONSOLIDAÇÃO")
        print("="*60)
        
        # 1. Stats (precisa de cnes e competencia)
        response, time_ms = self._request('GET', 'consolidation/stats', params={
            'cnes': '2560038', 'competencia': '202501'
        })
        if response and response.status_code == 200:
            self._add_result("Consolidação Stats", TestStatus.PASSED, 
                           "Stats obtidas", response, time_ms)
        elif response and response.status_code == 400:
            self._add_result("Consolidação Stats", TestStatus.WARNING, 
                           "Requer parâmetros válidos", response, time_ms)
        else:
            self._add_result("Consolidação Stats", TestStatus.FAILED, 
                           "Falha ao obter stats", response, time_ms)
        
        # 2. Verify Procedure
        response, time_ms = self._request('GET', 'consolidation/verify-procedure/0301010072')
        if response and response.status_code == 200:
            data = response.json()
            self._add_result("Verificar Procedimento", TestStatus.PASSED, 
                           f"Procedimento verificado", response, time_ms)
        else:
            self._add_result("Verificar Procedimento", TestStatus.FAILED, 
                           "Falha ao verificar procedimento", response, time_ms)
    
    # ==================== MÓDULO: REPORTS ====================
    def test_reports(self):
        """Testa endpoints de relatórios"""
        print("\n" + "="*60)
        print("MÓDULO: RELATÓRIOS")
        print("="*60)
        
        # 1. Lista de Reports
        response, time_ms = self._request('GET', 'reports/list')
        if response and response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 'N/A'
            self._add_result("Lista Relatórios", TestStatus.PASSED, 
                           f"Relatórios: {count}", response, time_ms)
        else:
            self._add_result("Lista Relatórios", TestStatus.FAILED, 
                           "Falha ao listar relatórios", response, time_ms)
    
    # ==================== MÓDULO: JULIA ====================
    def test_julia(self):
        """Testa endpoints Julia (integração)"""
        print("\n" + "="*60)
        print("MÓDULO: JULIA (Integração)")
        print("="*60)
        
        # 1. Check Connection
        response, time_ms = self._request('GET', 'julia/check-connection')
        if response and response.status_code == 200:
            data = response.json()
            status = data.get('status', 'N/A')
            self._add_result("Julia Conexão", TestStatus.PASSED, 
                           f"Status: {status}", response, time_ms)
        elif response and response.status_code in [503, 502, 500]:
            self._add_result("Julia Conexão", TestStatus.WARNING, 
                           "Julia não disponível (pode ser normal)", response, time_ms)
        else:
            self._add_result("Julia Conexão", TestStatus.FAILED, 
                           "Falha ao testar conexão Julia", response, time_ms)
    
    def run_all_tests(self) -> Dict:
        """Executa todos os testes"""
        print("\n" + "="*70)
        print("TESTE DE ENDPOINTS - BPA ONLINE (DJANGO)")
        print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"URL Base: {self.base_url}")
        print("="*70)
        
        # 1. Health Check (obrigatório)
        if not self.test_health():
            print("\n❌ ERRO CRÍTICO: Servidor não está respondendo!")
            print("   Verifique se o Django está rodando em", self.base_url)
            return self._generate_report()
        
        # 2. Autenticação (obrigatório para os demais)
        if not self.test_auth():
            print("\n⚠️ AVISO: Autenticação falhou - alguns testes podem falhar")
        
        # 3. Demais módulos
        self.test_dashboard()
        self.test_admin()
        self.test_profissionais()
        self.test_pacientes()
        self.test_procedimentos()
        self.test_sigtap()
        self.test_bpa()
        self.test_biserver()
        self.test_export()
        self.test_referencias()
        self.test_consolidacao()
        self.test_reports()
        # Julia removido - integração externa não testada automaticamente
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict:
        """Gera relatório final"""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == TestStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        total = len(self.results)
        
        print("\n" + "="*70)
        print("RESUMO DOS TESTES")
        print("="*70)
        print(f"\n  ✅ Sucesso:  {passed}")
        print(f"  ❌ Falha:    {failed}")
        print(f"  ⚠️  Aviso:   {warnings}")
        print(f"  ⏭️  Pulado:  {skipped}")
        print(f"  ────────────────")
        print(f"  Total:      {total}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n  Taxa de Sucesso: {success_rate:.1f}%")
        
        if failed > 0:
            print("\n" + "-"*70)
            print("ENDPOINTS COM FALHA:")
            print("-"*70)
            for r in self.results:
                if r.status == TestStatus.FAILED:
                    code = f"[{r.response_code}]" if r.response_code else "[---]"
                    print(f"  ❌ {r.name}: {r.message} {code}")
        
        print("\n" + "="*70)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'skipped': skipped,
            'success_rate': success_rate,
            'results': [
                {
                    'name': r.name,
                    'status': r.status.name,
                    'message': r.message,
                    'response_code': r.response_code,
                    'response_time_ms': r.response_time_ms
                }
                for r in self.results
            ]
        }


def main():
    parser = argparse.ArgumentParser(description='Teste de Endpoints BPA Online')
    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='URL base do servidor Django (default: http://localhost:8000)')
    parser.add_argument('--json', action='store_true',
                       help='Exibe resultado em JSON')
    
    args = parser.parse_args()
    
    tester = BPAEndpointTester(args.base_url)
    report = tester.run_all_tests()
    
    if args.json:
        print(json.dumps(report, indent=2))
    
    # Exit code baseado no resultado
    if report['failed'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
