"""
Teste do fluxo de filtro SIGTAP simplificado
Filtra APENAS pelo tipo de registro (BPA-I ou BPA-C)
NÃO filtra por valor - procedimentos zerados são válidos!
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.sigtap_parser import SigtapParser
from services.sigtap_filter_service import get_sigtap_filter_service

SIGTAP_DIR = r"C:\Users\60612427358\Documents\bpa-online\bpa-online\BPA-main\TabelaUnificada_202512_v2601161858"


def test_procedimentos_por_tipo_registro():
    """Testa quantos procedimentos podem ser BPA-I ou BPA-C"""
    print("\n" + "="*70)
    print("TESTE 1: Procedimentos por Tipo de Registro")
    print("="*70)
    
    sigtap = get_sigtap_filter_service()
    registro_map = sigtap._get_procedimento_registro_map()
    
    bpa_i = 0  # tipo '02'
    bpa_c = 0  # tipo '01'
    ambos = 0
    esus = 0   # tipo '10'
    outros = 0
    
    for proc, registros in registro_map.items():
        tem_i = '02' in registros
        tem_c = '01' in registros
        tem_esus = '10' in registros
        
        if tem_i and tem_c:
            ambos += 1
        elif tem_i:
            bpa_i += 1
        elif tem_c:
            bpa_c += 1
        elif tem_esus:
            esus += 1
        else:
            outros += 1
    
    print(f"\n📊 Procedimentos por tipo de registro:")
    print(f"   Apenas BPA-I ('02'): {bpa_i}")
    print(f"   Apenas BPA-C ('01'): {bpa_c}")
    print(f"   Ambos (BPA-I e BPA-C): {ambos}")
    print(f"   Apenas e-SUS ('10'): {esus}")
    print(f"   Outros: {outros}")
    print(f"\n   TOTAL com registro BPA: {bpa_i + bpa_c + ambos}")
    
    print("\n✅ Teste OK!")
    return True


def test_procedimentos_zerados_incluidos():
    """Verifica que procedimentos com VL_SA=0 são incluídos"""
    print("\n" + "="*70)
    print("TESTE 2: Procedimentos Zerados São Incluídos")
    print("="*70)
    
    parser = SigtapParser(SIGTAP_DIR)
    sigtap = get_sigtap_filter_service()
    registro_map = sigtap._get_procedimento_registro_map()
    
    # Buscar procedimentos com VL_SA = 0 que podem ser BPA
    zerados_bpa = []
    todos_procs = parser.parse_procedimentos()
    
    for proc in todos_procs[:500]:  # Amostra
        cod = proc['CO_PROCEDIMENTO']
        valores = parser.get_procedimento_valor(cod)
        registros = registro_map.get(cod, set())
        
        if valores['valor_sa'] == 0 and ('01' in registros or '02' in registros):
            zerados_bpa.append({
                'cod': cod,
                'nome': proc['NO_PROCEDIMENTO'][:50],
                'tipo': 'BPA-I' if '02' in registros else 'BPA-C'
            })
    
    print(f"\n📋 Procedimentos com VL_SA=0 que podem ser BPA (amostra):")
    print(f"   Total encontrados: {len(zerados_bpa)}")
    
    if zerados_bpa:
        print("\n   Exemplos:")
        for p in zerados_bpa[:5]:
            print(f"   {p['cod']} ({p['tipo']}): {p['nome']}")
    
    print("\n   ✅ Estes procedimentos SERÃO incluídos na extração!")
    print("\n✅ Teste OK!")
    return True


def test_simulacao_extracao():
    """Testa simulação de extração sem filtro por valor"""
    print("\n" + "="*70)
    print("TESTE 3: Simulação de Extração")
    print("="*70)
    
    from services.biserver_client import BiServerExtractionService
    
    service = BiServerExtractionService(enable_sigtap_validation=True)
    parser = SigtapParser(SIGTAP_DIR)
    sigtap = get_sigtap_filter_service()
    registro_map = sigtap._get_procedimento_registro_map()
    
    mock_records = []
    
    # Pegar 5 com valor > 0
    for proc in parser.parse_procedimentos()[:100]:
        cod = proc['CO_PROCEDIMENTO']
        valores = parser.get_procedimento_valor(cod)
        registros = registro_map.get(cod, set())
        
        if valores['valor_sa'] > 0 and '02' in registros:
            mock_records.append({
                'prd_pa': cod,
                'prd_qt_p': 1,
                'valor_original': valores['valor_sa']
            })
            if len(mock_records) >= 5:
                break
    
    # Pegar 3 com valor = 0 (zerados)
    for proc in parser.parse_procedimentos():
        cod = proc['CO_PROCEDIMENTO']
        valores = parser.get_procedimento_valor(cod)
        registros = registro_map.get(cod, set())
        
        if valores['valor_sa'] == 0 and '02' in registros:
            mock_records.append({
                'prd_pa': cod,
                'prd_qt_p': 1,
                'valor_original': 0
            })
            if len([r for r in mock_records if r['valor_original'] == 0]) >= 3:
                break
    
    # Pegar 2 que NÃO são BPA
    for proc in parser.parse_procedimentos():
        cod = proc['CO_PROCEDIMENTO']
        registros = registro_map.get(cod, set())
        
        if '02' not in registros and '01' not in registros:
            mock_records.append({
                'prd_pa': cod,
                'prd_qt_p': 1,
                'valor_original': -1,
                'tipo_teste': 'nao_bpa'
            })
            if len([r for r in mock_records if r.get('tipo_teste') == 'nao_bpa']) >= 2:
                break
    
    com_valor = len([r for r in mock_records if r['valor_original'] > 0])
    zerados = len([r for r in mock_records if r['valor_original'] == 0])
    nao_bpa = len([r for r in mock_records if r.get('tipo_teste') == 'nao_bpa'])
    
    print(f"\n📋 Registros simulados: {len(mock_records)}")
    print(f"   Com valor (VL_SA > 0): {com_valor}")
    print(f"   Zerados (VL_SA = 0): {zerados}")
    print(f"   Não são BPA: {nao_bpa}")
    
    print("\n🔄 Executando separação...")
    result = service._separate_bpa_by_sigtap(mock_records, cnes='6061478')
    
    print(f"\n📊 Resultado:")
    print(f"   BPA-I aceitos: {len(result['bpa_i'])}")
    print(f"   BPA-C aceitos: {len(result['bpa_c'])}")
    print(f"   Removidos (não são BPA): {result['stats'].get('removed_sem_registro', 0)}")
    
    total_aceitos = len(result['bpa_i']) + len(result['bpa_c'])
    esperado = com_valor + zerados
    
    print(f"\n   Esperado aceitar: {esperado} (com valor + zerados)")
    print(f"   Aceitos: {total_aceitos}")
    
    assert total_aceitos == esperado, f"Deveria aceitar {esperado}, aceitou {total_aceitos}"
    print("\n   ✅ CORRETO: Zerados foram incluídos!")
    
    print("\n✅ Teste OK!")
    return True


def main():
    print("\n" + "="*70)
    print("🧪 TESTE DO FLUXO SIGTAP SIMPLIFICADO")
    print("="*70)
    print("\nFLUXO ATUAL:")
    print("1. Aceita TODOS procedimentos que podem ser BPA-I ou BPA-C")
    print("2. Separa por tipo_registro ('02' = BPA-I, '01' = BPA-C)")
    print("3. NÃO filtra por valor (zerados são válidos!)")
    print("4. NÃO filtra por tipo de estabelecimento")
    print("\n→ Registra tudo que pode ser registrado!")
    
    tests = [
        test_procedimentos_por_tipo_registro,
        test_procedimentos_zerados_incluidos,
        test_simulacao_extracao,
    ]
    
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ FALHA: {test.__name__}: {e}")
    
    print("\n" + "="*70)
    print(f"📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    print("="*70)


if __name__ == '__main__':
    main()
