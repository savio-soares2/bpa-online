#!/usr/bin/env python
"""
Script de Diagnostico - Testa todos os componentes do sistema BPA Online
Verifica a integracao entre Django e servicos legados (FastAPI)
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Adiciona backend ao path para imports legados
BACKEND_PATH = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))


class DiagnosticoResult:
    def __init__(self, nome: str):
        self.nome = nome
        self.sucesso = False
        self.mensagem = ""
        self.detalhes = {}
    
    def ok(self, msg: str = "OK", **detalhes):
        self.sucesso = True
        self.mensagem = msg
        self.detalhes = detalhes
        return self
    
    def erro(self, msg: str, **detalhes):
        self.sucesso = False
        self.mensagem = msg
        self.detalhes = detalhes
        return self
    
    def __str__(self):
        status = "✅" if self.sucesso else "❌"
        result = f"{status} {self.nome}: {self.mensagem}"
        if self.detalhes:
            for k, v in self.detalhes.items():
                result += f"\n     {k}: {v}"
        return result


def test_django_database():
    """Testa conexao Django com PostgreSQL"""
    result = DiagnosticoResult("Django Database")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usuarios;")
            users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bpa_individualizado;")
            bpa_i = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bpa_consolidado;")
            bpa_c = cursor.fetchone()[0]
            
        return result.ok(
            f"PostgreSQL conectado",
            version=version[:50],
            usuarios=users,
            bpa_i=bpa_i,
            bpa_c=bpa_c
        )
    except Exception as e:
        return result.erro(str(e))


def test_legacy_database():
    """Testa conexao do database.py legado"""
    result = DiagnosticoResult("Legacy Database (backend/database.py)")
    try:
        from database import get_connection, DB_CONFIG
        
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
        
        return result.ok(
            "Conexao OK",
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database']
        )
    except Exception as e:
        return result.erro(str(e))


def test_sigtap_parser():
    """Testa o SigtapParser"""
    result = DiagnosticoResult("SIGTAP Parser")
    try:
        from services.sigtap_parser import SigtapParser
        
        # Encontra diretorio SIGTAP
        sigtap_dir = os.getenv(
            "SIGTAP_DIR",
            str(Path(__file__).resolve().parents[1] / "BPA-main" / "TabelaUnificada_202512_v2601161858")
        )
        
        if not os.path.isdir(sigtap_dir):
            return result.erro(f"Diretorio SIGTAP nao encontrado: {sigtap_dir}")
        
        parser = SigtapParser(sigtap_dir)
        
        # Testa parse de procedimentos
        procedimentos = parser.parse_procedimentos()
        if not procedimentos:
            return result.erro("Nenhum procedimento encontrado")
        
        # Pega um procedimento de exemplo
        proc_exemplo = procedimentos[0]
        
        # Verifica campos essenciais
        campos_obrigatorios = ['CO_PROCEDIMENTO', 'NO_PROCEDIMENTO']
        campos_faltando = [c for c in campos_obrigatorios if c not in proc_exemplo]
        
        if campos_faltando:
            return result.erro(f"Campos faltando: {campos_faltando}")
        
        # Verifica valores (VL_SA, VL_SH, VL_SP)
        campos_valor = ['VL_SA', 'VL_SH', 'VL_SP']
        valores_encontrados = {c: c in proc_exemplo for c in campos_valor}
        
        return result.ok(
            f"{len(procedimentos)} procedimentos carregados",
            diretorio=sigtap_dir,
            exemplo_codigo=proc_exemplo.get('CO_PROCEDIMENTO'),
            exemplo_nome=proc_exemplo.get('NO_PROCEDIMENTO', '')[:50],
            campos_valor=valores_encontrados,
            campos_exemplo=list(proc_exemplo.keys())[:10]
        )
    except Exception as e:
        import traceback
        return result.erro(f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


def test_sigtap_filter_service():
    """Testa o SigtapFilterService"""
    result = DiagnosticoResult("SIGTAP Filter Service")
    try:
        from services.sigtap_filter_service import get_sigtap_filter_service
        
        service = get_sigtap_filter_service()
        
        # Testa busca de procedimento conhecido
        proc_teste = "0301010072"  # Consulta medica em atencao basica
        info = service.get_procedimento_info(proc_teste)
        
        if not info:
            return result.erro(f"Procedimento {proc_teste} nao encontrado")
        
        # Verifica valores
        valor_total = info.get('valor_total', 0)
        valor_sh = info.get('valor_sh', 0)
        valor_sa = info.get('valor_sa', 0)
        valor_sp = info.get('valor_sp', 0)
        
        return result.ok(
            f"Procedimento {proc_teste} encontrado",
            nome=info.get('nome', '')[:50],
            valor_total=valor_total,
            valor_sh=valor_sh,
            valor_sa=valor_sa,
            valor_sp=valor_sp,
            tipo_registro=info.get('tipo_registro')
        )
    except Exception as e:
        import traceback
        return result.erro(f"{type(e).__name__}: {e}")


def test_sigtap_valores():
    """Testa especificamente os valores dos procedimentos SIGTAP"""
    result = DiagnosticoResult("SIGTAP Valores (VL_SA, VL_SH, VL_SP)")
    try:
        from services.sigtap_parser import SigtapParser
        
        sigtap_dir = os.getenv(
            "SIGTAP_DIR",
            str(Path(__file__).resolve().parents[1] / "BPA-main" / "TabelaUnificada_202512_v2601161858")
        )
        
        parser = SigtapParser(sigtap_dir)
        
        # Verifica se existe arquivo de valores
        valores_file = Path(sigtap_dir) / "tb_procedimento.txt"
        layout_file = Path(sigtap_dir) / "tb_procedimento_layout.txt"
        
        if not valores_file.exists():
            return result.erro(f"Arquivo nao encontrado: {valores_file}")
        
        if not layout_file.exists():
            return result.erro(f"Layout nao encontrado: {layout_file}")
        
        # Le layout para verificar campos de valor
        layout = parser.read_layout("tb_procedimento_layout.txt")
        campos_layout = [col.name for col in layout]
        
        campos_valor = ['VL_SH', 'VL_SA', 'VL_SP']
        campos_valor_presentes = [c for c in campos_valor if c in campos_layout]
        
        # Carrega procedimentos e verifica valores
        procedimentos = parser.parse_procedimentos()
        
        # Conta procedimentos com valor > 0
        com_valor = 0
        sem_valor = 0
        exemplos_com_valor = []
        
        for proc in procedimentos[:100]:  # Verifica primeiros 100
            vl_sh = float(proc.get('VL_SH', 0) or 0)
            vl_sa = float(proc.get('VL_SA', 0) or 0)
            vl_sp = float(proc.get('VL_SP', 0) or 0)
            total = vl_sh + vl_sa + vl_sp
            
            if total > 0:
                com_valor += 1
                if len(exemplos_com_valor) < 3:
                    exemplos_com_valor.append({
                        'codigo': proc.get('CO_PROCEDIMENTO'),
                        'vl_sh': vl_sh,
                        'vl_sa': vl_sa,
                        'vl_sp': vl_sp,
                        'total': total
                    })
            else:
                sem_valor += 1
        
        if com_valor == 0:
            return result.erro(
                "Nenhum procedimento com valor > 0 encontrado!",
                campos_layout=campos_layout,
                campos_valor_presentes=campos_valor_presentes
            )
        
        return result.ok(
            f"{com_valor} com valor, {sem_valor} zerados (de 100 testados)",
            campos_valor_presentes=campos_valor_presentes,
            exemplos=exemplos_com_valor
        )
    except Exception as e:
        import traceback
        return result.erro(f"{type(e).__name__}: {e}")


def test_biserver_client():
    """Testa o BiServerClient"""
    result = DiagnosticoResult("BiServer Client")
    try:
        from services.biserver_client import BiServerAPIClient, BiServerConfig
        
        client = BiServerAPIClient()
        
        return result.ok(
            "Cliente configurado",
            api_url=BiServerConfig.API_URL,
            mock_mode=BiServerConfig.MOCK_MODE,
            timeout=BiServerConfig.TIMEOUT
        )
    except Exception as e:
        return result.erro(str(e))


def test_biserver_extraction_service():
    """Testa o BiServerExtractionService"""
    result = DiagnosticoResult("BiServer Extraction Service")
    try:
        from services.biserver_client import get_extraction_service
        
        service = get_extraction_service()
        
        return result.ok(
            "Servico configurado",
            mock_mode=service.mock_mode,
            sigtap_validation=service.enable_sigtap_validation,
            sigtap_disponivel=service.sigtap is not None
        )
    except Exception as e:
        return result.erro(str(e))


def test_dbf_manager():
    """Testa o DBFManager"""
    result = DiagnosticoResult("DBF Manager")
    try:
        from services.dbf_manager_service import get_dbf_manager_instance
        
        dbf = get_dbf_manager_instance()
        
        # Tenta carregar procedimentos
        procs = dbf.get_procedimentos_info()
        
        if not procs:
            return result.erro("Nenhum procedimento carregado")
        
        # Verifica um procedimento
        exemplo = list(procs.items())[0] if procs else (None, None)
        
        return result.ok(
            f"{len(procs)} procedimentos carregados",
            exemplo_codigo=exemplo[0],
            exemplo_info=exemplo[1] if exemplo[1] else {}
        )
    except Exception as e:
        return result.erro(str(e))


def test_django_api_endpoints():
    """Testa os endpoints Django via request interno"""
    result = DiagnosticoResult("Django API Endpoints")
    try:
        from django.test import Client
        
        client = Client()
        
        # Testa health
        resp = client.get('/api/health')
        health_ok = resp.status_code == 200
        
        # Testa database-overview
        resp = client.get('/api/admin/database-overview')
        db_overview_ok = resp.status_code in [200, 401, 403]  # 401/403 se precisar auth
        
        # Testa sigtap/procedimentos
        resp = client.get('/api/sigtap/procedimentos')
        sigtap_ok = resp.status_code in [200, 401, 403]
        
        return result.ok(
            "Endpoints respondendo",
            health=health_ok,
            database_overview=db_overview_ok,
            sigtap_procedimentos=sigtap_ok
        )
    except Exception as e:
        return result.erro(str(e))


def test_env_variables():
    """Verifica variaveis de ambiente criticas"""
    result = DiagnosticoResult("Environment Variables")
    
    from dotenv import load_dotenv
    
    # Carrega .env files
    env_root = Path(__file__).resolve().parents[1] / ".env"
    env_backend = Path(__file__).resolve().parents[1] / "backend" / ".env"
    
    load_dotenv(env_root)
    load_dotenv(env_backend, override=True)
    
    vars_criticas = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_PORT': os.getenv('DB_PORT'),
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'SIGTAP_DIR': os.getenv('SIGTAP_DIR'),
        'BISERVER_API_URL': os.getenv('BISERVER_API_URL'),
        'DEBUG': os.getenv('DEBUG'),
    }
    
    faltando = [k for k, v in vars_criticas.items() if not v]
    
    if faltando:
        return result.erro(f"Variaveis faltando: {faltando}", **vars_criticas)
    
    return result.ok("Todas variaveis configuradas", **vars_criticas)


def test_sigtap_procedimento_registro():
    """Testa mapeamento procedimento -> tipo registro"""
    result = DiagnosticoResult("SIGTAP Procedimento-Registro Map")
    try:
        from services.sigtap_filter_service import get_sigtap_filter_service
        
        service = get_sigtap_filter_service()
        
        # Obtem mapa de registros
        registro_map = service._get_procedimento_registro_map()
        
        if not registro_map:
            return result.erro("Mapa de registros vazio")
        
        # Estatisticas
        total = len(registro_map)
        bpa_i_only = sum(1 for regs in registro_map.values() if regs == {'02'})
        bpa_c_only = sum(1 for regs in registro_map.values() if regs == {'01'})
        dual = sum(1 for regs in registro_map.values() if '01' in regs and '02' in regs)
        
        # Exemplo
        exemplo = list(registro_map.items())[0] if registro_map else (None, None)
        
        return result.ok(
            f"{total} procedimentos mapeados",
            bpa_i_only=bpa_i_only,
            bpa_c_only=bpa_c_only,
            dual=dual,
            exemplo=exemplo
        )
    except Exception as e:
        return result.erro(str(e))


def run_diagnostico():
    """Executa todos os testes de diagnostico"""
    print("=" * 70)
    print("DIAGNOSTICO DO SISTEMA BPA ONLINE - MIGRACAO DJANGO")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    testes = [
        ("1. Environment Variables", test_env_variables),
        ("2. Django Database", test_django_database),
        ("3. Legacy Database", test_legacy_database),
        ("4. SIGTAP Parser", test_sigtap_parser),
        ("5. SIGTAP Valores", test_sigtap_valores),
        ("6. SIGTAP Filter Service", test_sigtap_filter_service),
        ("7. SIGTAP Proc-Registro Map", test_sigtap_procedimento_registro),
        ("8. BiServer Client", test_biserver_client),
        ("9. BiServer Extraction", test_biserver_extraction_service),
        ("10. DBF Manager", test_dbf_manager),
        ("11. Django API Endpoints", test_django_api_endpoints),
    ]
    
    resultados = []
    
    for nome, teste in testes:
        print(f"\n{'=' * 50}")
        print(f"Executando: {nome}")
        print("-" * 50)
        
        try:
            resultado = teste()
            resultados.append(resultado)
            print(resultado)
        except Exception as e:
            import traceback
            err_result = DiagnosticoResult(nome)
            err_result.erro(f"Excecao nao tratada: {e}\n{traceback.format_exc()}")
            resultados.append(err_result)
            print(err_result)
    
    # Resumo
    print("\n")
    print("=" * 70)
    print("RESUMO DO DIAGNOSTICO")
    print("=" * 70)
    
    sucesso = sum(1 for r in resultados if r.sucesso)
    falha = sum(1 for r in resultados if not r.sucesso)
    
    print(f"\n✅ Sucesso: {sucesso}")
    print(f"❌ Falha: {falha}")
    print(f"Total: {len(resultados)}")
    
    if falha > 0:
        print("\n⚠️ COMPONENTES COM PROBLEMA:")
        for r in resultados:
            if not r.sucesso:
                print(f"   - {r.nome}: {r.mensagem}")
    
    print("\n" + "=" * 70)
    
    return resultados


if __name__ == "__main__":
    run_diagnostico()
