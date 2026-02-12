#!/usr/bin/env python3
"""
Script de teste para verificar se o BPA Online está funcionando corretamente
"""

import sys
import os

def test_imports():
    """Testa se todas as bibliotecas necessárias estão instaladas"""
    print("🔍 Testando importações...\n")
    
    libraries = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'pandas': 'Pandas',
        'python-dateutil': 'dateutil'
    }
    
    missing = []
    
    for lib, name in libraries.items():
        try:
            if lib == 'python-dateutil':
                __import__('dateutil')
            else:
                __import__(lib)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name}")
            missing.append(lib)
    
    if missing:
        print(f"\n⚠️ Bibliotecas faltando: {', '.join(missing)}")
        print(f"Execute: pip install {' '.join(missing)}")
        return False
    
    print("\n✅ Todas as bibliotecas necessárias estão instaladas!\n")
    return True

def test_file_structure():
    """Verifica se a estrutura de arquivos está correta"""
    print("📁 Verificando estrutura de arquivos...\n")
    
    required_files = [
        'backend/main.py',
        'backend/models/schemas.py',
        'backend/services/bpa_service.py',
        'backend/services/sql_parser.py',
        'backend/services/firebird_importer.py',
        'backend/requirements.txt',
        'frontend/package.json',
        'frontend/src/App.js',
        'docker-compose.yml',
        'README.md'
    ]
    
    missing = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing.append(file_path)
    
    if missing:
        print(f"\n⚠️ Arquivos faltando: {len(missing)}")
        return False
    
    print("\n✅ Estrutura de arquivos está correta!\n")
    return True

def test_sql_parser():
    """Testa o parser de SQL"""
    print("🔧 Testando parser de SQL...\n")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from services.sql_parser import SQLParser
        
        parser = SQLParser()
        cnes_list = parser.get_available_cnes()
        
        if cnes_list:
            print(f"✅ Parser funcionando - {len(cnes_list)} CNES encontrados")
            for cnes in cnes_list:
                print(f"   - CNES {cnes.cnes}: {cnes.total_registros} registros")
        else:
            print("⚠️ Nenhum CNES encontrado nos dados de teste")
            print("   Verifique se existe o arquivo: BPA-main/arquivos_sql/2025116061478.sql")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Erro ao testar parser: {e}\n")
        return False

def test_api_schema():
    """Testa os schemas da API"""
    print("📋 Testando schemas da API...\n")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from models.schemas import ExtractionRequest, CNESInfo, DashboardStats
        
        # Testa criação de objetos
        request = ExtractionRequest(
            cnes_list=['6061478'],
            competencia_inicial='2025-11',
            competencia_final='2025-11',
            mode='TEST'
        )
        
        cnes = CNESInfo(
            cnes='6061478',
            nome='Teste',
            total_registros=100,
            competencias=['2025-11']
        )
        
        stats = DashboardStats(
            total_cnes=1,
            total_registros=100
        )
        
        print("✅ ExtractionRequest")
        print("✅ CNESInfo")
        print("✅ DashboardStats")
        print("\n✅ Schemas da API estão funcionando!\n")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar schemas: {e}\n")
        return False

def main():
    """Função principal"""
    print("="*60)
    print("🏥 BPA Online - Teste de Configuração")
    print("="*60)
    print()
    
    tests = [
        ("Importações", test_imports),
        ("Estrutura de Arquivos", test_file_structure),
        ("Parser SQL", test_sql_parser),
        ("Schemas API", test_api_schema)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {name}: {e}\n")
            results.append((name, False))
    
    # Resumo
    print("="*60)
    print("📊 Resumo dos Testes")
    print("="*60)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {name}")
    
    print()
    print(f"Total: {passed}/{total} testes passaram")
    print()
    
    if passed == total:
        print("🎉 Todos os testes passaram! O sistema está pronto para uso.")
        print()
        print("Para iniciar o sistema:")
        print("  - Linux/Mac: ./start.sh")
        print("  - Windows:   start.bat")
        print("  - Docker:    docker-compose up")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Corrija os problemas antes de iniciar.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
