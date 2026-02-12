"""
Teste direto da API BiServer - igual ao código Django original
"""
import requests
import jwt
from time import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurações
BISERVER_API_URL = 'https://biserver.rb.adm.br/'
API_SECRET_KEY = '#g(w&t_ju9yz(g5c25l=0m(1mkmou)vucwsu7vmd#-k@zjnd0_'


class BiServerAPIClient:
    """
    Cópia exata do código Django para teste
    """

    def __init__(self, timeout=10):
        self.base_url = BISERVER_API_URL
        self.secret = API_SECRET_KEY
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self):
        """Create session with connection pooling and retry logic"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _get_headers(self):
        """Generate authorization headers with fresh JWT"""
        payload = {
            'app': 'bi_django',
            'action': 'call_bi_server_api',
            'iat': int(time()),
            'exp': int(time()) + 300,
        }
        token = jwt.encode(payload, self.secret, algorithm='HS256')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _request(self, method: str, endpoint: str, retry: bool = True, timeout: float = None, **kwargs):
        """Generic request method"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))
        
        # Use session (with retries) or plain requests (no retries)
        requester = self.session if retry else requests
        
        print(f"Chamando: {method} {url}")
        print(f"Params: {kwargs.get('params', {})}")
        
        try:
            resp = requester.request(
                method,
                url,
                headers=headers,
                timeout=(timeout if timeout is not None else self.timeout),
                **kwargs
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500] if resp.text else 'empty'}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro: {e}")
            raise

    def get(self, endpoint: str, params: dict = None, retry: bool = True, timeout: float = None):
        return self._request("GET", endpoint, retry=retry, timeout=timeout, params=params)

    def get_bpa_data(self, cnes: str, competencia: str, page: int = 0, timeout: float = 120):
        """Busca dados de BPA - endpoint correto"""
        return self.get(
            "/api/bpa/data",
            params={"cnes": cnes, "competencia": competencia, "page": page},
            retry=False,
            timeout=timeout
        )

    def call_genie_protected_endpoint(self):
        """Test calling Genie's /api/protected endpoint"""
        return self.get('/api/protected')

    def close(self):
        self.session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Testando conexão com BiServer API")
    print("=" * 60)
    
    client = BiServerAPIClient()
    
    # Teste 1: Endpoint protegido
    print("\n[1] Testando /api/protected...")
    try:
        result = client.call_genie_protected_endpoint()
        print("✅ SUCESSO!")
        print(f"Resultado: {result}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    # Teste 2: Buscar dados BPA
    print("\n" + "=" * 60)
    print("[2] Testando /api/bpa/data...")
    try:
        result = client.get_bpa_data(
            cnes="2492555",  # Substitua pelo CNES real
            competencia="2025-12",
            page=0
        )
        print("✅ SUCESSO!")
        print(f"Total registros: {len(result.get('data', result.get('records', [])))}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    client.close()
