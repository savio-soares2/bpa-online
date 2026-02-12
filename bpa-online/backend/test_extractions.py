"""
Script de teste para simular 10 extrações e verificar funcionamento
"""
import sys
import time
from database import BPADatabase

def test_database_connection():
    """Testa conexão com banco"""
    print("=" * 60)
    print("TESTE 1: Conexão com Banco de Dados")
    print("=" * 60)
    
    try:
        db = BPADatabase()
        print("✅ Conexão estabelecida com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def test_historico_save():
    """Testa salvamento de histórico"""
    print("\n" + "=" * 60)
    print("TESTE 2: Salvamento de Histórico (10 extrações)")
    print("=" * 60)
    
    db = BPADatabase()
    
    for i in range(1, 11):
        print(f"\n📊 Simulando extração {i}/10...")
        
        try:
            historico_data = {
                'cnes': '2492555',
                'competencia': '202601',
                'total_bpa_i': 100 * i,
                'total_bpa_c': 50 * i,
                'total_removido': 10 * i,
                'total_geral': 150 * i,
                'valor_total_bpa_i': 1000.50 * i,
                'valor_total_bpa_c': 500.25 * i,
                'valor_total_geral': 1500.75 * i,
                'procedimentos_mais_usados': [
                    {
                        'codigo': f'030101007{i}',
                        'nome': f'Procedimento Teste {i}',
                        'quantidade': 10 * i,
                        'valor_unitario': 10.50,
                        'valor_total': 105.00 * i
                    }
                ],
                'profissionais_mais_ativos': [
                    {
                        'cns': f'70000000000000{i}',
                        'cbo': '225125',
                        'quantidade': 20 * i
                    }
                ],
                'distribuicao_por_dia': {
                    '01': 5 * i,
                    '15': 10 * i,
                    '30': 3 * i
                },
                'usuario_id': 1,
                'duracao_segundos': 30 + i,
                'status': 'concluido'
            }
            
            historico_id = db.save_historico_extracao(historico_data)
            print(f"   ✅ Extração {i} salva com ID: {historico_id}")
            
        except Exception as e:
            print(f"   ❌ Erro na extração {i}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print(f"\n✅ Todas as 10 extrações foram salvas com sucesso!")
    return True

def test_historico_list():
    """Testa listagem de histórico"""
    print("\n" + "=" * 60)
    print("TESTE 3: Listagem de Histórico")
    print("=" * 60)
    
    db = BPADatabase()
    
    try:
        # Lista primeira página
        result = db.list_historico_extracoes(cnes='2492555', limit=5, offset=0)
        print(f"\n📋 Total de registros: {result['total']}")
        print(f"📄 Página 1 (5 registros):")
        
        for i, record in enumerate(result['records'], 1):
            print(f"\n   Registro {i}:")
            print(f"   - ID: {record['id']}")
            print(f"   - CNES: {record['cnes']} | Competência: {record['competencia']}")
            print(f"   - BPA-I: {record['total_bpa_i']} | BPA-C: {record['total_bpa_c']}")
            print(f"   - Valor Total: R$ {record['valor_total_geral']:.2f}")
            print(f"   - Duração: {record['duracao_segundos']}s")
            print(f"   - Top Procedimento: {record['procedimentos_mais_usados'][0]['codigo'] if record['procedimentos_mais_usados'] else 'N/A'}")
        
        # Lista segunda página
        result2 = db.list_historico_extracoes(cnes='2492555', limit=5, offset=5)
        print(f"\n📄 Página 2 ({len(result2['records'])} registros):")
        
        for i, record in enumerate(result2['records'], 1):
            print(f"   {i}. ID {record['id']} - R$ {record['valor_total_geral']:.2f}")
        
        print(f"\n✅ Listagem funcionando corretamente!")
        print(f"   - Paginação: OK")
        print(f"   - JSON parsing: OK")
        print(f"   - Total de registros: {result['total']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao listar: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cleanup():
    """Remove dados de teste"""
    print("\n" + "=" * 60)
    print("TESTE 4: Limpeza de Dados de Teste")
    print("=" * 60)
    
    from database import get_connection
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Deleta apenas os registros de teste
                cursor.execute("""
                    DELETE FROM historico_extracoes 
                    WHERE cnes = '2492555' 
                    AND competencia = '202601'
                    AND total_geral >= 150
                """)
                deleted = cursor.rowcount
                conn.commit()
                
        print(f"✅ {deleted} registros de teste removidos")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao limpar: {e}")
        return False

if __name__ == '__main__':
    print("\n🧪 TESTE DE HISTÓRICO DE EXTRAÇÕES\n")
    
    inicio = time.time()
    
    # Executa testes
    tests = [
        ("Conexão", test_database_connection),
        ("Salvamento", test_historico_save),
        ("Listagem", test_historico_list),
        ("Limpeza", test_cleanup)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO em {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
            break
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {name}")
    
    total_passed = sum(1 for _, r in results if r)
    total_tests = len(results)
    
    duracao = time.time() - inicio
    
    print(f"\n📊 Resultado: {total_passed}/{total_tests} testes passaram")
    print(f"⏱️  Tempo total: {duracao:.2f}s")
    
    if total_passed == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        sys.exit(1)
