"""
BiServer API Client - Cliente para API do bi.eSUS (Genie)
Adaptado de Django para FastAPI
"""
import requests
import jwt
import logging
from time import time
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from datetime import datetime
import random

load_dotenv()

logger = logging.getLogger(__name__)

# Import do serviço SIGTAP para validação de procedimentos
try:
    from services.sigtap_filter_service import get_sigtap_filter_service
    SIGTAP_AVAILABLE = True
except ImportError:
    logger.warning("SIGTAP Filter Service não disponível - validação de procedimentos desabilitada")
    SIGTAP_AVAILABLE = False


# ========== CONFIGURAÇÃO ==========

# CNES das UPAs que precisam extrair dados de odonto
UPAS_COM_ODONTO = {
    '2755289',  # UPA Norte
    '2492555',  # UPA Sul
}

class BiServerConfig:
    """Configuração do BiServer API"""
    API_URL: str = os.getenv('BISERVER_API_URL', 'https://biserver.rb.adm.br/')
    SECRET_KEY: str = os.getenv('API_SECRET_KEY', 'qvrSub&0i?#/NJ^h[UO$!7,[TnXyqIGCjI=XqFICZs&gW2V6a')
    KID: str = os.getenv('API_KID', 'bpaclient')
    TIMEOUT: int = int(os.getenv('BISERVER_TIMEOUT', '30'))
    # Modo mock para desenvolvimento quando API não está disponível
    MOCK_MODE: bool = os.getenv('BISERVER_MOCK_MODE', 'false').lower() == 'true'  # Desativado - API funcionando!


# ========== SCHEMAS ==========

class ExtractionResult(BaseModel):
    """Resultado de uma extração"""
    success: bool
    total_records: int
    records: List[Dict[str, Any]]
    errors: List[str] = []
    message: str


class ExtractionStatus(BaseModel):
    """Status de uma extração"""
    cnes: str
    competencia: str
    tipo: str  # 'bpa_i' ou 'bpa_c'
    status: str  # 'pending', 'extracting', 'extracted', 'inserting', 'completed', 'error'
    total_records: int = 0
    inserted_records: int = 0
    errors: List[str] = []


# ========== CLIENTE API ==========

class BiServerAPIClient:
    """
    Cliente FastAPI para chamar endpoints do Genie (bi.eSUS) com autenticação JWT
    """

    def __init__(self, kid: str = None, secret: str = None, timeout: int = None):
        self.base_url = BiServerConfig.API_URL.rstrip('/')
        self.secret = secret or BiServerConfig.SECRET_KEY
        self.kid = kid or BiServerConfig.KID
        self.timeout = timeout or BiServerConfig.TIMEOUT
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Cria sessão com connection pooling e retry logic"""
        session = requests.Session()
        
        # Estratégia de retry: retry em erros de conexão, timeouts, erros 500-503
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # delays de 1s, 2s, 4s
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        # Monta adapters para HTTP e HTTPS
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _get_headers(self) -> Dict[str, str]:
        """Gera headers de autorização com JWT"""
        payload = {
            'app': 'bpa_python',
            'action': 'python_call_server_api',
            'iat': int(time()),  # Issued at timestamp
        }
        # Inclui kid no header para informar ao servidor qual secret usar
        token = jwt.encode(payload, self.secret, algorithm='HS256', headers={'kid': self.kid})
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _request(self, method: str, endpoint: str, retry: bool = True, timeout: float = None, **kwargs) -> Dict[str, Any]:
        """Método genérico de requisição com tratamento de erros
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Caminho do endpoint da API
            retry: Se False, desabilita retries automáticos para esta requisição
            timeout: Timeout em segundos para esta requisição. Se None, usa o padrão do cliente.
            **kwargs: Argumentos adicionais passados para requests
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))
        
        # Usa session (com retries) ou requests direto (sem retries)
        requester = self.session if retry else requests
        
        try:
            resp = requester.request(
                method,
                url,
                headers=headers,
                timeout=(timeout if timeout is not None else self.timeout),
                **kwargs
            )
            resp.raise_for_status()
            # Força encoding UTF-8 se não especificado no Content-Type
            # Isso resolve problemas com caracteres acentuados (ex: ç, ã)
            if resp.encoding is None or resp.encoding.lower() == 'iso-8859-1':
                resp.encoding = 'utf-8'
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout chamando {method} {url}")
            raise Exception(f"Timeout ao conectar com BiServer: {url}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão chamando {method} {url}: {e}")
            raise Exception(f"Erro de conexão com BiServer: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP {resp.status_code} chamando {method} {url}: {resp.text}")
            raise Exception(f"Erro HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Erro chamando {method} {url}: {e}")
            raise

    def get(self, endpoint: str, params: dict = None, retry: bool = True, timeout: float = None) -> Dict[str, Any]:
        """Requisição GET"""
        return self._request("GET", endpoint, retry=retry, timeout=timeout, params=params)

    def post(self, endpoint: str, json: dict = None, retry: bool = True, timeout: float = None, **kwargs) -> Dict[str, Any]:
        """Requisição POST"""
        return self._request("POST", endpoint, retry=retry, timeout=timeout, json=json, **kwargs)

    def put(self, endpoint: str, json: dict = None, retry: bool = True, timeout: float = None, **kwargs) -> Dict[str, Any]:
        """Requisição PUT"""
        return self._request("PUT", endpoint, retry=retry, timeout=timeout, json=json, **kwargs)

    def delete(self, endpoint: str, retry: bool = True, timeout: float = None, **kwargs) -> Dict[str, Any]:
        """Requisição DELETE"""
        return self._request("DELETE", endpoint, retry=retry, timeout=timeout, **kwargs)

    def test_connection(self) -> Dict[str, Any]:
        """Testa conexão chamando endpoint protegido do Genie"""
        try:
            result = self.get('/api/protected')
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_bpa_data(self, cnes: str, competencia: str, page: int = 0, timeout: float = 120) -> Dict[str, Any]:
        """
        Busca dados de BPA do Genie
        
        Args:
            cnes: Código CNES da unidade
            competencia: Competência no formato YYYY-MM
            page: Página de resultados (começa em 0)
            timeout: Timeout em segundos (padrão 120s para consultas grandes)
        """
        return self.get(
            "/api/bpa/data",
            params={"cnes": cnes, "competencia": competencia, "page": page},
            retry=False,  # Sem retry para evitar duplicação
            timeout=timeout
        )

    def close(self):
        """Fecha sessão para liberar recursos"""
        self.session.close()


# ========== GERADOR DE DADOS MOCK ==========

class MockDataGenerator:
    """Gera dados fictícios para teste quando a API não está disponível"""
    
    NOMES = [
        "MARIA SILVA", "JOAO SANTOS", "ANA OLIVEIRA", "PEDRO SOUZA",
        "LUCIA FERREIRA", "CARLOS LIMA", "PATRICIA COSTA", "MARCOS PEREIRA",
        "FERNANDA ALVES", "RICARDO MARTINS", "JULIANA ROCHA", "BRUNO CARVALHO"
    ]
    
    PROCEDIMENTOS = [
        ("0301010072", "CONSULTA MEDICA EM ATENCAO BASICA"),
        ("0301010064", "CONSULTA DE PROFISSIONAIS DE NIVEL SUPERIOR NA ATENCAO BASICA"),
        ("0301010080", "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA"),
        ("0214010015", "ACOLHIMENTO COM CLASSIFICACAO DE RISCO"),
        ("0301010196", "CONSULTA / ATENDIMENTO DOMICILIAR NA ATENÇÃO BÁSICA"),
        ("0301060029", "ADMINISTRACAO DE MEDICAMENTOS VIA ORAL"),
        ("0301060010", "ADMINISTRACAO DE MEDICAMENTOS NA ATENCAO BASICA"),
    ]
    
    @classmethod
    def generate_cns(cls) -> str:
        """Gera CNS fictício válido"""
        return f"7{random.randint(10000000000000, 99999999999999)}"
    
    @classmethod
    def generate_bpa_i_records(cls, cnes: str, competencia: str, count: int) -> List[Dict]:
        """Gera registros fictícios de BPA-I"""
        records = []
        ano = int(competencia[:4])
        mes = int(competencia[4:6])
        
        for i in range(count):
            proc_codigo, proc_desc = random.choice(cls.PROCEDIMENTOS)
            dia = random.randint(1, 28)
            
            records.append({
                "id": i + 1,
                "cnes": cnes,
                "competencia": competencia,
                "folha": (i // 20) + 1,  # 20 registros por folha
                "sequencia": (i % 20) + 1,
                "cns_profissional": cls.generate_cns(),
                "nome_profissional": f"DR. {random.choice(cls.NOMES)}",
                "cbo": random.choice(["225125", "223505", "225142", "251510"]),
                "ine": f"000{random.randint(1000000, 9999999)}",
                "cns_paciente": cls.generate_cns(),
                "nome_paciente": random.choice(cls.NOMES),
                "data_nascimento": f"{random.randint(1950, 2010)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "sexo": random.choice(["M", "F"]),
                "raca_cor": random.choice(["01", "02", "03", "04", "99"]),
                "municipio_ibge": "172100",
                "data_atendimento": f"{ano}-{mes:02d}-{dia:02d}",
                "procedimento": proc_codigo,
                "procedimento_descricao": proc_desc,
                "quantidade": 1,
                "cid": random.choice(["Z000", "Z001", "J00", "I10", "E119", ""]),
                "carater_atendimento": "01",
                "exportado": False
            })
        
        return records
    
    @classmethod
    def generate_bpa_c_records(cls, cnes: str, competencia: str, count: int) -> List[Dict]:
        """Gera registros fictícios de BPA-C"""
        records = []
        
        for i in range(count):
            proc_codigo, proc_desc = random.choice(cls.PROCEDIMENTOS)
            
            records.append({
                "id": i + 1,
                "cnes": cnes,
                "competencia": competencia,
                "folha": (i // 10) + 1,
                "cns_profissional": cls.generate_cns(),
                "cbo": random.choice(["225125", "223505", "225142"]),
                "procedimento": proc_codigo,
                "procedimento_descricao": proc_desc,
                "quantidade": random.randint(1, 50),
                "idade": random.choice(["00", "01", "05", "15", "30", "45", "60"]),
                "exportado": False
            })
        
        return records


# ========== SERVIÇO DE EXTRAÇÃO ==========

class BiServerExtractionService:
    """
    Serviço de extração de dados do BiServer
    Separa lógica de extração da API e inserção no Firebird
    """
    
    def __init__(self, enable_sigtap_validation: bool = True):
        self.client = BiServerAPIClient()
        self.mock_mode = BiServerConfig.MOCK_MODE
        self.enable_sigtap_validation = enable_sigtap_validation and SIGTAP_AVAILABLE
        
        if self.enable_sigtap_validation:
            self.sigtap = get_sigtap_filter_service()
            logger.info("✓ Validação SIGTAP ativada - procedimentos serão filtrados")
        else:
            self.sigtap = None
            logger.warning("⚠ Validação SIGTAP desativada")
        
        if self.mock_mode:
            logger.warning("BiServer em MODO MOCK - usando dados fictícios para teste")
    
    def _validate_procedimento_sigtap(self, procedimento: str, tipo_bpa: str) -> bool:
        """
        Valida se um procedimento está nas tabelas SIGTAP para o tipo de BPA
        
        Args:
            procedimento: Código do procedimento
            tipo_bpa: '02' para BPA-I, '01' para BPA-C
            
        Returns:
            True se o procedimento é válido, False caso contrário
        """
        if not self.enable_sigtap_validation or not self.sigtap:
            return True  # Se validação desabilitada, aceita tudo
        
        try:
            # Busca procedimentos do tipo especificado
            procedimentos_validos = self.sigtap.get_procedimentos_filtrados(tipo_registro=tipo_bpa)
            codigos_validos = {p['CO_PROCEDIMENTO'] for p in procedimentos_validos}
            
            is_valid = procedimento in codigos_validos
            
            if not is_valid:
                logger.warning(f"⚠ Procedimento {procedimento} NÃO encontrado no SIGTAP para tipo {tipo_bpa}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Erro ao validar procedimento {procedimento}: {e}")
            return True  # Em caso de erro, não bloqueia
    
    def _separate_bpa_by_sigtap(self, records: List[Dict], cnes: str = None) -> Dict[str, List[Dict]]:
        """
        Separa registros entre BPA-I e BPA-C
        
        FLUXO SIMPLIFICADO:
        1. Separa por tipo_registro SIGTAP: '02' = BPA-I, '01' = BPA-C
        2. NÃO filtra por valor (procedimentos zerados são válidos!)
        3. NÃO filtra por tipo de estabelecimento
        
        Args:
            records: Lista de registros extraídos da API
            cnes: Código CNES (usado apenas para logging)
            
        Returns:
            Dict com 'bpa_i', 'bpa_c' e estatísticas
        """
        if not self.enable_sigtap_validation or not records:
            logger.info(
                "[TRATAMENTO] SIGTAP desabilitado ou sem registros. "
                "Critérios: sem filtro/sem separação, mantém todos em BPA-I."
            )
            return {
                'bpa_i': records,
                'bpa_c': [],
                'stats': {
                    'total': len(records),
                    'bpa_i': len(records),
                    'bpa_c': 0,
                    'removed_sem_registro': 0
                }
            }
        
        # Mapa de procedimento -> tipos de registro permitidos
        registro_map = self.sigtap._get_procedimento_registro_map()
        
        bpa_i_records = []
        bpa_c_records = []
        removed_sem_registro = 0
        
        for rec in records:
            proc = rec.get('prd_pa', rec.get('procedimento', ''))
            
            # Separa por tipo de registro
            registros = registro_map.get(proc, set())
            
            if '02' in registros:  # BPA-I
                bpa_i_records.append(rec)
            elif '01' in registros:  # BPA-C
                bpa_c_records.append(rec)
            else:
                # Não tem registro BPA-I nem BPA-C (pode ser e-SUS, RAAS, etc)
                removed_sem_registro += 1
        
        logger.info(f"📊 Separação: {len(bpa_i_records)} BPA-I, {len(bpa_c_records)} BPA-C")
        if removed_sem_registro > 0:
            logger.info(f"   ⚠ {removed_sem_registro} sem registro BPA (e-SUS, RAAS, etc)")
        logger.info(
            "[TRATAMENTO] Critérios: tipo_registro SIGTAP (02=BPA-I, 01=BPA-C), "
            "sem filtro por valor, sem filtro por tipo de estabelecimento."
        )
        
        return {
            'bpa_i': bpa_i_records,
            'bpa_c': bpa_c_records,
            'stats': {
                'total': len(records),
                'bpa_i': len(bpa_i_records),
                'bpa_c': len(bpa_c_records),
                'removed_sem_registro': removed_sem_registro,
                'removed': removed_sem_registro
            }
        }

    def _normalize_competencia(self, competencia: str) -> str:
        """Normaliza competência para YYYYMM"""
        if not competencia:
            return ''
        comp = str(competencia).replace('-', '').strip()
        return comp[:6]

    def _calculate_idade(self, data_nascimento: str, data_referencia: str) -> str:
        """Calcula idade em anos e retorna string com 3 dígitos"""
        try:
            dn = str(data_nascimento or '').replace('-', '')
            dr = str(data_referencia or '').replace('-', '')

            if len(dn) < 8 or len(dr) < 6:
                return '000'

            ano_nasc = int(dn[:4])
            mes_nasc = int(dn[4:6])

            ano_ref = int(dr[:4])
            mes_ref = int(dr[4:6])

            idade = ano_ref - ano_nasc
            if mes_ref < mes_nasc:
                idade -= 1

            if idade < 0:
                idade = 0
            if idade > 999:
                idade = 999

            return f"{idade:03d}"
        except Exception:
            return '000'

    def _convert_record_to_bpac(self, record: Dict, fallback_competencia: str = '') -> Dict:
        """Converte um registro para formato BPA-C"""
        prd_cmp = (
            record.get('prd_cmp')
            or record.get('competencia')
            or record.get('competencia_mes')
            or ''
        )
        if not prd_cmp and fallback_competencia:
            prd_cmp = fallback_competencia
        prd_cmp = self._normalize_competencia(prd_cmp)

        data_ref = (
            record.get('prd_dtaten')
            or record.get('data_atendimento')
            or prd_cmp
        )

        idade = (
            record.get('prd_idade')
            or record.get('idade')
            or ''
        )
        if not idade:
            idade = self._calculate_idade(
                record.get('prd_dtnasc')
                or record.get('data_nascimento')
                or record.get('data_nasc')
                or '',
                data_ref
            )

        return {
            'prd_uid': record.get('prd_uid') or record.get('cnes') or '',
            'prd_cmp': prd_cmp,
            'prd_cnsmed': record.get('prd_cnsmed') or record.get('cns_profissional') or '',
            'prd_cbo': record.get('prd_cbo') or record.get('cbo') or '',
            'prd_pa': record.get('prd_pa') or record.get('procedimento') or '',
            'prd_idade': str(idade or '000').zfill(3)[:3],
            'prd_qt_p': record.get('prd_qt_p') or record.get('quantidade') or 1,
            'prd_org': record.get('prd_org') or 'BPC_CONV'
        }

    def _aggregate_bpac_records(self, records: List[Dict]) -> List[Dict]:
        """Agrega registros BPA-C por chave única e soma quantidades"""
        if not records:
            return []

        grupos: Dict[tuple, Dict] = {}

        for rec in records:
            key = (
                rec.get('prd_uid', ''),
                rec.get('prd_cmp', ''),
                rec.get('prd_cbo', ''),
                rec.get('prd_pa', ''),
                rec.get('prd_idade', '000')
            )

            if key not in grupos:
                grupos[key] = rec.copy()
                grupos[key]['prd_qt_p'] = 0
                grupos[key]['_aggregation_count'] = 0

            grupos[key]['prd_qt_p'] += int(rec.get('prd_qt_p', 1) or 1)
            grupos[key]['_aggregation_count'] += 1

        return list(grupos.values())

    def _classify_and_convert_bpa(self, records: List[Dict], cnes: str = None, competencia: str = None) -> Dict[str, List[Dict]]:
        """
        Classifica registros e converte para BPA-C quando procedimento é dual (01+02).
        """
        competencia = self._normalize_competencia(competencia or '')
        if not self.enable_sigtap_validation or not records:
            logger.info(
                "[TRATAMENTO] SIGTAP desabilitado ou sem registros. "
                "Critérios: sem conversão/sem agregação, mantém todos em BPA-I."
            )
            return {
                'bpa_i': records,
                'bpa_c': [],
                'stats': {
                    'total': len(records),
                    'bpa_i': len(records),
                    'bpa_c': 0,
                    'converted': 0,
                    'removed_sem_registro': 0,
                    'removed': 0
                }
            }

        registro_map = self.sigtap._get_procedimento_registro_map()

        bpa_i_records = []
        bpa_c_raw = []
        removed_sem_registro = 0
        converted_count = 0

        for rec in records:
            proc = rec.get('prd_pa', rec.get('procedimento', ''))
            registros = registro_map.get(proc, set())

            has_bpa_c = '01' in registros
            has_bpa_i = '02' in registros

            if has_bpa_c and has_bpa_i:
                bpa_c_raw.append(self._convert_record_to_bpac(rec, fallback_competencia=competencia))
                converted_count += 1
            elif has_bpa_i:
                bpa_i_records.append(rec)
            elif has_bpa_c:
                bpa_c_raw.append(self._convert_record_to_bpac(rec, fallback_competencia=competencia))
            else:
                removed_sem_registro += 1

        bpa_c_aggregated = self._aggregate_bpac_records(bpa_c_raw)

        logger.info(f"📊 Classificação: {len(bpa_i_records)} BPA-I, {len(bpa_c_aggregated)} BPA-C")
        logger.info(f"   🔄 Convertidos (dual): {converted_count}")
        if removed_sem_registro > 0:
            logger.info(f"   ⚠ {removed_sem_registro} sem registro BPA (e-SUS, RAAS, etc)")
        logger.info(
            "[TRATAMENTO] Critérios: tipo_registro SIGTAP (01+02=dual->BPA-C), "
            "agregação BPA-C por chave (CNES, COMP, CBO, PA, IDADE)."
        )
        logger.info(
            f"[TRATAMENTO] Estatísticas: total={len(records)}, bpa_i={len(bpa_i_records)}, "
            f"bpa_c_raw={len(bpa_c_raw)}, bpa_c_agregado={len(bpa_c_aggregated)}, "
            f"convertidos={converted_count}, removidos={removed_sem_registro}"
        )

        return {
            'bpa_i': bpa_i_records,
            'bpa_c': bpa_c_aggregated,
            'stats': {
                'total': len(records),
                'bpa_i': len(bpa_i_records),
                'bpa_c': len(bpa_c_aggregated),
                'bpa_c_before_aggregation': len(bpa_c_raw),
                'converted': converted_count,
                'removed_sem_registro': removed_sem_registro,
                'removed': removed_sem_registro
            }
        }
    
    def _filter_records_by_sigtap(self, records: List[Dict], tipo_bpa: str, cnes: str = None) -> tuple[List[Dict], int]:
        """
        Filtra registros mantendo apenas procedimentos válidos para o tipo de BPA
        
        FLUXO SIMPLIFICADO:
        1. Aceita TODOS os procedimentos que podem ser registrados no tipo de BPA
        2. NÃO filtra por valor (VL_SA) - procedimentos zerados também são válidos!
        3. NÃO filtra por tipo de estabelecimento
        
        Args:
            records: Lista de registros extraídos
            tipo_bpa: '02' para BPA-I, '01' para BPA-C
            cnes: Código CNES (usado apenas para logging)
            
        Returns:
            Tupla (registros_validos, quantidade_removida)
        """
        if not self.enable_sigtap_validation or not records:
            return records, 0
        
        original_count = len(records)
        
        # Mapa de procedimento -> tipos de registro permitidos
        registro_map = self.sigtap._get_procedimento_registro_map()
        
        valid_records = []
        removed_tipo_errado = 0
        
        for rec in records:
            proc = rec.get('prd_pa', rec.get('procedimento', ''))
            
            # Verifica se pode ser registrado neste tipo de BPA
            registros_permitidos = registro_map.get(proc, set())
            if tipo_bpa in registros_permitidos:
                valid_records.append(rec)
            else:
                removed_tipo_errado += 1
        
        removed_count = original_count - len(valid_records)
        
        if removed_count > 0:
            tipo_nome = "BPA-I" if tipo_bpa == '02' else "BPA-C"
            logger.info(f"📋 Filtro: {len(valid_records)} válidos para {tipo_nome}, {removed_tipo_errado} não permitidos")
        
        return valid_records, removed_count
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Testa conexão com a API do BiServer"""
        if self.mock_mode:
            return {
                "success": True, 
                "mock": True,
                "message": "Modo mock ativo - API simulada para desenvolvimento"
            }
        return self.client.test_connection()
    
    def _fetch_page_with_retry(
        self, 
        endpoint: str, 
        params: dict, 
        max_retries: int = 5,
        base_delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Busca uma página da API com retry manual e backoff exponencial.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            max_retries: Número máximo de tentativas
            base_delay: Delay base entre tentativas (será multiplicado exponencialmente)
            
        Returns:
            Resposta da API
        """
        import time
        
        last_error = None
        for attempt in range(max_retries):
            try:
                # Usa retry=False pois faremos retry manual com mais controle
                result = self.client.get(endpoint, params=params, retry=False, timeout=120)
                return result
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Se for erro 502/503/504, faz retry com backoff
                if '502' in error_str or '503' in error_str or '504' in error_str or 'timeout' in error_str:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ Tentativa {attempt + 1}/{max_retries} falhou (502/timeout). Aguardando {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    # Outros erros, não faz retry
                    raise
        
        # Esgotou tentativas
        raise Exception(f"Máximo de tentativas ({max_retries}) excedido. Último erro: {last_error}")
    
    def extract_and_separate_bpa(
        self,
        cnes: str,
        competencia: str,
        limit: int = None,  # None = sem limite
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        NOVO MÉTODO UNIFICADO - Extrai todos os dados e separa BPA-I de BPA-C
        
        A API do BiServer retorna TODOS os registros juntos (BPA-I + BPA-C misturados).
        Este método:
        1. Extrai dados da API com paginação incremental e delays
        2. Se for UPA, também extrai dados de odonto (tables='odonto')
        3. Usa SIGTAP para separar por tipo_registro
        4. Retorna BPA-I e BPA-C separados
        
        Args:
            cnes: Código CNES da unidade
            competencia: Competência no formato YYYYMM (ex: 202512)
            limit: Limite de registros (None = sem limite, extrai tudo)
            offset: Offset para paginação
            
        Returns:
            Dict com bpa_i, bpa_c e estatísticas
        """
        import time
        
        try:
            logger.info(f"🔄 Extraindo e separando BPA: CNES={cnes}, Competência={competencia}")
            
            # Verifica se é UPA para também extrair odonto
            is_upa = cnes in UPAS_COM_ODONTO
            if is_upa:
                logger.info(f"🦷 UPA detectada (CNES {cnes}) - também extrairá dados de ODONTO")
            
            # Formata competência
            comp_formatada = f"{competencia[:4]}-{competencia[4:6]}" if len(competencia) == 6 else competencia
            
            endpoint = "/api/bpa/data"
            all_records = []
            page = 0
            max_pages = 500  # Limite alto para extrair tudo (500 páginas * 10k = 5M registros)
            page_delay = 1.0  # Delay entre páginas para não sobrecarregar
            
            # ========== EXTRAÇÃO PRINCIPAL (BPA) ==========
            logger.info(f"📥 Iniciando extração de BPA...")
            while page < max_pages:
                params = {
                    "cnes": cnes,
                    "competencia": comp_formatada,
                    "page": page
                }
                
                logger.info(f"📥 Buscando página {page} (BPA)...")
                
                try:
                    result = self._fetch_page_with_retry(endpoint, params)
                    page_records = result.get("registros", [])
                    
                    if not page_records:
                        logger.info(f"📭 Página {page} vazia. Fim da extração BPA.")
                        break
                    
                    all_records.extend(page_records)
                    logger.info(f"✅ Página {page}: {len(page_records)} registros (total: {len(all_records)})")
                    
                    # Se a página veio com menos registros que o esperado, provavelmente é a última
                    if len(page_records) < 500:
                        logger.info(f"📭 Página {page} parcial ({len(page_records)} < 500). Provavelmente última página.")
                        break
                    
                    page += 1
                    
                    # Delay entre páginas para não sobrecarregar o servidor
                    if page < max_pages:
                        time.sleep(page_delay)
                        
                except Exception as e:
                    logger.error(f"❌ Erro na página {page}: {e}")
                    if all_records:
                        logger.warning(f"⚠️ Continuando com {len(all_records)} registros extraídos antes do erro")
                        break
                    else:
                        raise
            
            bpa_count = len(all_records)
            logger.info(f"📊 Total BPA extraído: {bpa_count} registros")
            
            # ========== EXTRAÇÃO ODONTO (apenas para UPAs) ==========
            odonto_count = 0
            if is_upa:
                logger.info(f"🦷 Iniciando extração de ODONTO para UPA...")
                page = 0
                
                while page < max_pages:
                    params = {
                        "cnes": cnes,
                        "competencia": comp_formatada,
                        "page": page,
                        "tables": "odonto"  # Parâmetro para extrair da tabela odonto
                    }
                    
                    logger.info(f"🦷 Buscando página {page} (ODONTO)...")
                    
                    try:
                        result = self._fetch_page_with_retry(endpoint, params)
                        page_records = result.get("registros", [])
                        
                        if not page_records:
                            logger.info(f"📭 Página {page} vazia. Fim da extração ODONTO.")
                            break
                        
                        # Marca registros como vindos de odonto (para debug)
                        for rec in page_records:
                            rec['_source'] = 'odonto'
                        
                        all_records.extend(page_records)
                        odonto_count += len(page_records)
                        logger.info(f"🦷 Página {page}: {len(page_records)} registros odonto (total odonto: {odonto_count})")
                        
                        if len(page_records) < 500:
                            logger.info(f"📭 Página {page} parcial. Provavelmente última página odonto.")
                            break
                        
                        page += 1
                        time.sleep(page_delay)
                            
                    except Exception as e:
                        logger.error(f"❌ Erro na página {page} (odonto): {e}")
                        # Continua mesmo se falhar odonto, já temos os dados de BPA
                        logger.warning(f"⚠️ Continuando sem mais dados de odonto")
                        break
                
                logger.info(f"🦷 Total ODONTO extraído: {odonto_count} registros")
            
            # ========== PROCESSAMENTO ==========
            logger.info(f"📊 Total geral extraído: {len(all_records)} registros (BPA: {bpa_count}, Odonto: {odonto_count})")
            
            # Aplica offset e limit apenas se especificado
            if limit is not None:
                records = all_records[offset:offset + limit]
            else:
                records = all_records[offset:] if offset > 0 else all_records
            
            logger.info(f"📊 Processando: {len(records)} registros")
            
            # Separa BPA-I de BPA-C usando SIGTAP (dual → BPA-C) e agrega para evitar repetições
            separated = self._classify_and_convert_bpa(records, cnes=cnes, competencia=competencia)
            
            # Adiciona estatísticas de odonto
            separated['stats']['odonto'] = odonto_count
            
            return {
                'success': True,
                'bpa_i': separated['bpa_i'],
                'bpa_c': separated['bpa_c'],
                'stats': separated['stats'],
                'message': f"Extraídos e separados: {separated['stats']['bpa_i']} BPA-I, {separated['stats']['bpa_c']} BPA-C" + (f" (incluindo {odonto_count} de odonto)" if odonto_count > 0 else "")
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair e separar BPA: {e}")
            return {
                'success': False,
                'bpa_i': [],
                'bpa_c': [],
                'stats': {'total': 0, 'bpa_i': 0, 'bpa_c': 0, 'removed': 0, 'odonto': 0},
                'error': str(e)
            }
    
    def extract_bpa_individualizado(
        self, 
        cnes: str, 
        competencia: str,
        limit: int = 100,
        offset: int = 0  # Nova opção para paginação
    ) -> ExtractionResult:
        """
        Extrai registros de BPA Individualizado da API BiServer
        
        Args:
            cnes: Código CNES da unidade
            competencia: Competência no formato YYYYMM (ex: 202512)
            limit: Limite de registros por página (ex: 5000)
            offset: Quantidade de registros para pular (paginação)
        """
        try:
            logger.info(f"Extraindo BPA-I: CNES={cnes}, Competência={competencia}, Limit={limit}, Offset={offset}, Mock={self.mock_mode}")
            
            if self.mock_mode:
                # Gera dados mock para teste (respeita offset)
                all_mock_records = MockDataGenerator.generate_bpa_i_records(cnes, competencia, 10000)
                records = all_mock_records[offset:offset + limit]
                
                # Aplica filtro SIGTAP por tipo de estabelecimento
                records, removed = self._filter_records_by_sigtap(records, tipo_bpa='02', cnes=cnes)
                
                cache_key = f"bpa_i_{cnes}_{competencia}_{offset}"
                self._extracted_data[cache_key] = records
                
                msg = f"[MOCK] Extraídos {len(records)} registros de BPA-I (offset={offset})"
                if removed > 0:
                    msg += f" - {removed} removidos (SIGTAP)"
                
                return ExtractionResult(
                    success=True,
                    total_records=len(records),
                    records=records,
                    message=msg
                )
            
            # Modo real - chama API com page e limit
            # API usa formato YYYY-MM, não YYYYMM
            comp_formatada = f"{competencia[:4]}-{competencia[4:6]}" if len(competencia) == 6 else competencia
            
            # Calcula page a partir do offset
            page = offset // limit if limit > 0 else 0
            
            endpoint = f"/api/bpa/data"
            params = {
                "cnes": cnes,
                "competencia": comp_formatada,
                "page": page
            }
            
            result = self.client.get(endpoint, params=params)
            
            # Debug logging
            logger.info(f"📊 BPA-I Response type: {type(result)}")
            logger.info(f"📊 BPA-I Response keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            if isinstance(result, dict):
                logger.info(f"📊 BPA-I Total registros: {result.get('total_registros', 'N/A')}")
                if 'registros' in result:
                    logger.info(f"📊 BPA-I Len registros array: {len(result['registros'])}")
                    if result['registros']:
                        logger.info(f"📊 BPA-I First record keys: {list(result['registros'][0].keys())[:15]}")
            
            # A API retorna em 'registros'
            all_records = result.get("registros", result.get("data", result.get("records", [])))
            
            # Aplica offset e limit manualmente já que a API retorna tudo
            records = all_records[offset:offset + limit] if all_records else []
            
            # Aplica filtro SIGTAP por tipo de estabelecimento
            records, removed = self._filter_records_by_sigtap(records, tipo_bpa='02', cnes=cnes)
            
            # Armazena no cache com offset
            cache_key = f"bpa_i_{cnes}_{competencia}_{offset}"
            self._extracted_data[cache_key] = records
            
            msg = f"Extraídos {len(records)} registros de BPA-I (offset={offset})"
            if removed > 0:
                msg += f" - {removed} removidos (SIGTAP)"
            
            return ExtractionResult(
                success=True,
                total_records=len(records),
                records=records,
                message=msg
            )
            
        except Exception as e:
            logger.error(f"Erro ao extrair BPA-I: {e}")
            return ExtractionResult(
                success=False,
                total_records=0,
                records=[],
                errors=[str(e)],
                message=f"Erro na extração: {e}"
            )
    
    def extract_bpa_consolidado(
        self, 
        cnes: str, 
        competencia: str,
        limit: int = 100,
        offset: int = 0  # Nova opção para paginação
    ) -> ExtractionResult:
        """
        Extrai registros de BPA Consolidado da API BiServer
        
        Args:
            cnes: Código CNES da unidade
            competencia: Competência no formato YYYYMM
            limit: Limite de registros por página
            offset: Quantidade de registros para pular
        """
        try:
            logger.info(f"Extraindo BPA-C: CNES={cnes}, Competência={competencia}, Limit={limit}, Offset={offset}, Mock={self.mock_mode}")
            
            if self.mock_mode:
                # Gera dados mock para teste (respeita offset)
                all_mock_records = MockDataGenerator.generate_bpa_c_records(cnes, competencia, 5000)
                records = all_mock_records[offset:offset + limit]
                
                # Aplica filtro SIGTAP por tipo de estabelecimento
                records, removed = self._filter_records_by_sigtap(records, tipo_bpa='01', cnes=cnes)
                
                cache_key = f"bpa_c_{cnes}_{competencia}_{offset}"
                self._extracted_data[cache_key] = records
                
                msg = f"[MOCK] Extraídos {len(records)} registros de BPA-C (offset={offset})"
                if removed > 0:
                    msg += f" - {removed} removidos (SIGTAP)"
                
                return ExtractionResult(
                    success=True,
                    total_records=len(records),
                    records=records,
                    message=msg
                )
            
            # Modo real
            # API usa formato YYYY-MM, não YYYYMM
            comp_formatada = f"{competencia[:4]}-{competencia[4:6]}" if len(competencia) == 6 else competencia
            
            # Calcula page a partir do offset
            page = offset // limit if limit > 0 else 0
            
            endpoint = f"/api/bpa/data"
            params = {
                "cnes": cnes,
                "competencia": comp_formatada,
                "page": page
            }
            
            result = self.client.get(endpoint, params=params)
            
            # Debug logging
            logger.info(f"📊 BPA-C Response type: {type(result)}")
            logger.info(f"📊 BPA-C Response keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            if isinstance(result, dict):
                logger.info(f"📊 BPA-C Total registros: {result.get('total_registros', 'N/A')}")
                if 'registros' in result:
                    logger.info(f"📊 BPA-C Len registros array: {len(result['registros'])}")
                    if result['registros']:
                        logger.info(f"📊 BPA-C First record keys: {list(result['registros'][0].keys())[:15]}")
            
            # A API retorna em 'registros'
            all_records = result.get("registros", result.get("data", result.get("records", [])))
            
            # Aplica offset e limit manualmente
            records = all_records[offset:offset + limit] if all_records else []
            
            # Aplica filtro SIGTAP por tipo de estabelecimento (BPA-C)
            records, removed = self._filter_records_by_sigtap(records, tipo_bpa='01', cnes=cnes)
            
            cache_key = f"bpa_c_{cnes}_{competencia}_{offset}"
            self._extracted_data[cache_key] = records
            
            msg = f"Extraídos {len(records)} registros de BPA-C (offset={offset})"
            if removed > 0:
                msg += f" - {removed} removidos (SIGTAP)"
            
            return ExtractionResult(
                success=True,
                total_records=len(records),
                records=records,
                message=msg
            )
            
        except Exception as e:
            logger.error(f"Erro ao extrair BPA-C: {e}")
            return ExtractionResult(
                success=False,
                total_records=0,
                records=[],
                errors=[str(e)],
                message=f"Erro na extração: {e}"
            )
    
    def extract_profissionais(self, cnes: str, limit: int = 50) -> ExtractionResult:
        """Extrai profissionais de uma unidade"""
        try:
            endpoint = f"/api/profissionais"
            params = {"cnes": cnes, "limit": limit}
            
            result = self.client.get(endpoint, params=params)
            records = result.get("data", result.get("records", []))
            
            return ExtractionResult(
                success=True,
                total_records=len(records),
                records=records,
                message=f"Extraídos {len(records)} profissionais"
            )
        except Exception as e:
            return ExtractionResult(
                success=False,
                total_records=0,
                records=[],
                errors=[str(e)],
                message=f"Erro na extração: {e}"
            )
    
    def count_records(self, cnes: str, competencia: str, tipo: str = "bpa_i") -> Dict[str, Any]:
        """
        Conta o total de registros disponíveis para uma competência
        
        Args:
            cnes: Código CNES
            competencia: Competência YYYYMM
            tipo: 'bpa_i' ou 'bpa_c'
        
        Returns:
            Dict com total de registros
        """
        try:
            logger.info(f"Contando registros {tipo}: CNES={cnes}, Competência={competencia}, Mock={self.mock_mode}")
            
            if self.mock_mode:
                # Em modo mock, simulamos contagens realistas
                total = 10000 if tipo == "bpa_i" else 500
                return {
                    "success": True,
                    "total": total,
                    "cnes": cnes,
                    "competencia": competencia,
                    "tipo": tipo,
                    "mock": True
                }
            
            # Modo real - API não tem endpoint de count separado
            # Fazemos uma extração com limit=1 apenas para verificar se há dados
            comp_formatada = f"{competencia[:4]}-{competencia[4:6]}" if len(competencia) == 6 else competencia
            tipo_api = "individualizado" if tipo == "bpa_i" else "consolidado"
            
            endpoint = f"/api/bpa/data"
            params = {
                "cnes": cnes,
                "competencia": comp_formatada,
                "tipo": tipo_api,
                "limit": 1,
                "offset": 0
            }
            
            result = self.client.get(endpoint, params=params)
            
            # Tenta pegar o total de várias formas possíveis
            total = result.get("total", result.get("total_registros", result.get("count", 0)))
            
            return {
                "success": True,
                "total": total,
                "cnes": cnes,
                "competencia": competencia,
                "tipo": tipo,
                "mock": False
            }
            
        except Exception as e:
            logger.error(f"Erro ao contar registros: {e}")
            return {
                "success": False,
                "total": 0,
                "error": str(e)
            }
    
    def extract_all_bpa_individualizado(
        self, 
        cnes: str, 
        competencia: str,
        batch_size: int = 5000,
        on_batch_complete: callable = None
    ) -> Dict[str, Any]:
        """
        Extrai TODOS os registros de BPA-I automaticamente em lotes
        
        Args:
            cnes: Código CNES
            competencia: Competência YYYYMM
            batch_size: Tamanho de cada lote (padrão 5000)
            on_batch_complete: Callback opcional chamado após cada lote
        
        Returns:
            Dict com estatísticas completas da extração
        """
        try:
            logger.info(f"Iniciando extração COMPLETA de BPA-I: CNES={cnes}, Comp={competencia}, BatchSize={batch_size}")
            
            # Tenta contar registros (apenas em modo mock)
            expected_total = None
            total_batches_estimate = None
            
            if self.mock_mode:
                count_result = self.count_records(cnes, competencia, "bpa_i")
                if count_result["success"]:
                    expected_total = count_result["total"]
                    total_batches_estimate = (expected_total + batch_size - 1) // batch_size
                    logger.info(f"Total estimado de registros: {expected_total}")
            else:
                logger.info("Modo real: extraindo até não retornar mais dados")
            
            # Extrai em lotes até acabar
            all_records = []
            offset = 0
            batch_number = 1
            errors = []
            
            while True:
                if total_batches_estimate:
                    logger.info(f"Extraindo lote {batch_number}/{total_batches_estimate} (offset={offset})")
                else:
                    logger.info(f"Extraindo lote {batch_number} (offset={offset})")
                
                result = self.extract_bpa_individualizado(
                    cnes=cnes,
                    competencia=competencia,
                    limit=batch_size,
                    offset=offset
                )
                
                if not result.success:
                    errors.append(f"Lote {batch_number}: {result.message}")
                    break
                
                # Se não retornou registros, acabou
                if result.total_records == 0:
                    logger.info("Nenhum registro retornado, finalizando extração")
                    break
                
                all_records.extend(result.records)
                
                # Callback opcional para processar cada lote
                if on_batch_complete:
                    if total_batches_estimate:
                        on_batch_complete(batch_number, total_batches_estimate, result.records)
                    else:
                        on_batch_complete(batch_number, None, result.records)
                
                offset += batch_size
                batch_number += 1
                
                # Se retornou menos que o batch_size, acabaram os registros
                if result.total_records < batch_size:
                    logger.info(f"Último lote retornou {result.total_records} registros, finalizando")
                    break
            
            # Cacheia todos os dados
            cache_key = f"bpa_i_{cnes}_{competencia}_all"
            self._extracted_data[cache_key] = all_records
            
            return {
                "success": True,
                "total_records": len(all_records),
                "expected_records": expected_total if expected_total else len(all_records),
                "batches_processed": batch_number - 1,
                "batch_size": batch_size,
                "records": all_records,
                "errors": errors,
                "message": f"Extraídos {len(all_records)} registros em {batch_number - 1} lotes"
            }
            
        except Exception as e:
            logger.error(f"Erro na extração completa: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_records": 0,
                "records": []
            }
    
    def extract_all_bpa_consolidado(
        self, 
        cnes: str, 
        competencia: str,
        batch_size: int = 5000,
        on_batch_complete: callable = None
    ) -> Dict[str, Any]:
        """
        Extrai TODOS os registros de BPA-C automaticamente em lotes
        
        Args:
            cnes: Código CNES
            competencia: Competência YYYYMM
            batch_size: Tamanho de cada lote (padrão 5000)
            on_batch_complete: Callback opcional chamado após cada lote
        
        Returns:
            Dict com estatísticas completas da extração
        """
        try:
            logger.info(f"Iniciando extração COMPLETA de BPA-C: CNES={cnes}, Comp={competencia}, BatchSize={batch_size}")
            
            # Tenta contar registros (apenas em modo mock)
            expected_total = None
            total_batches_estimate = None
            
            if self.mock_mode:
                count_result = self.count_records(cnes, competencia, "bpa_c")
                if count_result["success"]:
                    expected_total = count_result["total"]
                    total_batches_estimate = (expected_total + batch_size - 1) // batch_size
                    logger.info(f"Total estimado de registros: {expected_total}")
            else:
                logger.info("Modo real: extraindo até não retornar mais dados")
            
            # Extrai em lotes até acabar
            all_records = []
            offset = 0
            batch_number = 1
            errors = []
            
            while True:
                if total_batches_estimate:
                    logger.info(f"Extraindo lote {batch_number}/{total_batches_estimate} (offset={offset})")
                else:
                    logger.info(f"Extraindo lote {batch_number} (offset={offset})")
                
                result = self.extract_bpa_consolidado(
                    cnes=cnes,
                    competencia=competencia,
                    limit=batch_size,
                    offset=offset
                )
                
                if not result.success:
                    errors.append(f"Lote {batch_number}: {result.message}")
                    break
                
                # Se não retornou registros, acabou
                if result.total_records == 0:
                    logger.info("Nenhum registro retornado, finalizando extração")
                    break
                
                all_records.extend(result.records)
                
                # Callback opcional para processar cada lote
                if on_batch_complete:
                    if total_batches_estimate:
                        on_batch_complete(batch_number, total_batches_estimate, result.records)
                    else:
                        on_batch_complete(batch_number, None, result.records)
                
                offset += batch_size
                batch_number += 1
                
                # Se retornou menos que o batch_size, acabaram os registros
                if result.total_records < batch_size:
                    logger.info(f"Último lote retornou {result.total_records} registros, finalizando")
                    break
            
            # Cacheia todos os dados
            cache_key = f"bpa_c_{cnes}_{competencia}_all"
            self._extracted_data[cache_key] = all_records
            
            return {
                "success": True,
                "total_records": len(all_records),
                "expected_records": expected_total if expected_total else len(all_records),
                "batches_processed": batch_number - 1,
                "batch_size": batch_size,
                "records": all_records,
                "errors": errors,
                "message": f"Extraídos {len(all_records)} registros em {batch_number - 1} lotes"
            }
            
        except Exception as e:
            logger.error(f"Erro na extração completa: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_records": 0,
                "records": []
            }
            
            return ExtractionResult(
                success=True,
                total_records=len(records),
                records=records,
                message=f"Extraídos {len(records)} profissionais"
            )
        except Exception as e:
            return ExtractionResult(
                success=False,
                total_records=0,
                records=[],
                errors=[str(e)],
                message=f"Erro: {e}"
            )
    
    def extract_pacientes(self, cnes: str, limit: int = 100) -> ExtractionResult:
        """Extrai pacientes atendidos em uma unidade"""
        try:
            endpoint = f"/api/pacientes"
            params = {"cnes": cnes, "limit": limit}
            
            result = self.client.get(endpoint, params=params)
            records = result.get("data", result.get("records", []))
            
            return ExtractionResult(
                success=True,
                total_records=len(records),
                records=records,
                message=f"Extraídos {len(records)} pacientes"
            )
        except Exception as e:
            return ExtractionResult(
                success=False,
                total_records=0,
                records=[],
                errors=[str(e)],
                message=f"Erro: {e}"
            )
    

    
    def close(self):
        """Fecha conexões"""
        self.client.close()


# ========== SINGLETON ==========

_extraction_service: Optional[BiServerExtractionService] = None

def get_extraction_service() -> BiServerExtractionService:
    """Retorna instância singleton do serviço de extração"""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = BiServerExtractionService()
    return _extraction_service
