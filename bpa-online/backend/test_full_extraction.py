"""
Teste completo do fluxo de extração - 1000 registros UPA Norte
Simula o processo completo: extração -> separação -> cálculo valores -> salvar banco -> histórico
"""
import sys
import time
from datetime import datetime
from collections import Counter
from database import BPADatabase

def generate_mock_records(count=1000):
    """Gera registros simulados da API BiServer"""
    print(f"📊 Gerando {count} registros simulados...")
    records = []
    
    for i in range(count):
        # Simula dados da API BiServer
        record = {
            "prd_pa": f"030101007{i % 10}",  # Procedimento
            "prd_cbo": "225125",  # CBO médico
            "prd_cnsmed": f"7000{i:011d}",  # CNS profissional
            "prd_cnspac": f"8000{i:011d}",  # CNS paciente
            "prd_nmpac": f"Paciente Teste {i}",
            "prd_dtnasc": "19900101",  # YYYYMMDD - 8 caracteres
            "prd_dtaten": "20251201",  # YYYYMMDD - 8 caracteres
            "prd_sexo": "M" if i % 2 == 0 else "F",
            "prd_raca": "01",
            "prd_idade": str((i % 80) + 1),
            "prd_cep_pcnte": "50050000",  # 8 caracteres
            "prd_lograd_pcnte": "12345",
            "prd_end_pcnte": f"Rua Teste {i}",
            "prd_num_pcnte": str(i),
            "prd_compl_pcnte": "",
            "prd_tel_pcnte": "987654321",
            "prd_ddtel_pcnte": "81",
            "prd_email_pcnte": "",
            "prd_cid": "A00",
            "prd_qt_p": 1
        }
        records.append(record)
    
    print(f"✅ {count} registros gerados")
    return records

def test_field_sizes(records):
    """Testa tamanhos dos campos VARCHAR(8)"""
    print("\n" + "=" * 60)
    print("TESTE 1: Verificação de Tamanho de Campos VARCHAR(8)")
    print("=" * 60)
    
    problemas = []
    campos_varchar8 = ['prd_dtnasc', 'prd_dtaten', 'prd_cep_pcnte']
    
    for i, record in enumerate(records):
        for campo in campos_varchar8:
            valor = str(record.get(campo, ''))
            if len(valor) > 8:
                problemas.append({
                    'registro': i,
                    'campo': campo,
                    'valor': valor,
                    'tamanho': len(valor)
                })
    
    if problemas:
        print(f"❌ Encontrados {len(problemas)} problemas:")
        for p in problemas[:10]:  # Mostra primeiros 10
            print(f"   Registro {p['registro']}: {p['campo']} = '{p['valor']}' ({p['tamanho']} chars)")
        return False
    else:
        print(f"✅ Todos os campos VARCHAR(8) estão dentro do limite")
        print(f"   - prd_dtnasc: max {max(len(str(r.get('prd_dtnasc', ''))) for r in records)} chars")
        print(f"   - prd_dtaten: max {max(len(str(r.get('prd_dtaten', ''))) for r in records)} chars")
        print(f"   - prd_cep_pcnte: max {max(len(str(r.get('prd_cep_pcnte', ''))) for r in records)} chars")
        return True

def test_save_bpa_individualizado(records, cnes="2755289", competencia="202512"):
    """Testa salvamento de BPA-I no banco"""
    print("\n" + "=" * 60)
    print(f"TESTE 2: Salvamento BPA-I ({len(records)} registros)")
    print("=" * 60)
    
    db = BPADatabase()
    saved = 0
    errors = []
    
    # CNES de urgência
    carater = '02'  # UPA Norte é urgência
    
    print(f"💾 Salvando registros no banco...")
    inicio = time.time()
    
    for seq, record in enumerate(records, start=1):
        try:
            # Garante que campos VARCHAR(8) estão corretos
            data_nasc = str(record.get("prd_dtnasc", ""))[:8]
            data_aten = str(record.get("prd_dtaten", ""))[:8]
            cep = str(record.get("prd_cep_pcnte", ""))[:8]
            
            bpa_data = {
                "prd_uid": cnes,
                "prd_cmp": competencia,
                "prd_flh": 1,
                "prd_seq": seq,
                "prd_cnsmed": str(record.get("prd_cnsmed", "")),
                "prd_cbo": str(record.get("prd_cbo", "")),
                "prd_ine": "",
                "prd_cnspac": str(record.get("prd_cnspac", "")),
                "prd_cpf_pcnte": "",
                "prd_nmpac": record.get("prd_nmpac", ""),
                "prd_dtnasc": data_nasc,
                "prd_sexo": str(record.get("prd_sexo", "M")),
                "prd_raca": str(record.get("prd_raca", "99")).zfill(2),
                "prd_idade": str(record.get("prd_idade", "")),
                "prd_ibge": "",
                "prd_cep_pcnte": cep,
                "prd_lograd_pcnte": str(record.get("prd_lograd_pcnte", "")),
                "prd_end_pcnte": str(record.get("prd_end_pcnte", "")),
                "prd_num_pcnte": str(record.get("prd_num_pcnte", "")),
                "prd_compl_pcnte": str(record.get("prd_compl_pcnte", "")),
                "prd_bairro_pcnte": "",
                "prd_tel_pcnte": str(record.get("prd_tel_pcnte", "")),
                "prd_ddtel_pcnte": str(record.get("prd_ddtel_pcnte", "")),
                "prd_email_pcnte": str(record.get("prd_email_pcnte", "") or ""),
                "prd_dtaten": data_aten,
                "prd_pa": record.get("prd_pa", ""),
                "prd_qt_p": record.get("prd_qt_p", 1),
                "prd_cid": record.get("prd_cid", ""),
                "prd_caten": carater,
                "prd_naut": "",
                "prd_servico": "",
                "prd_classificacao": "",
                "prd_cnpj": "",
                "prd_nac": "010",
                "prd_etnia": "",
                "prd_eqp_area": "",
                "prd_eqp_seq": "",
                "prd_mvm": competencia,
                "prd_org": "BPI",
            }
            
            db.save_bpa_individualizado(bpa_data)
            saved += 1
            
            if saved % 100 == 0:
                print(f"   ✅ {saved} registros salvos...")
                
        except Exception as e:
            error_msg = str(e)
            errors.append({
                'seq': seq,
                'error': error_msg
            })
            
            # Se houver erro, mostra e para
            if len(errors) == 1:
                print(f"\n❌ ERRO no registro {seq}:")
                print(f"   {error_msg}")
                print(f"\n   Dados do registro:")
                for campo, valor in bpa_data.items():
                    if isinstance(valor, str) and len(valor) > 0:
                        print(f"   - {campo}: '{valor}' ({len(valor)} chars)")
                return False
    
    duracao = time.time() - inicio
    
    print(f"\n✅ Salvamento concluído!")
    print(f"   - Salvos: {saved}")
    print(f"   - Erros: {len(errors)}")
    print(f"   - Tempo: {duracao:.2f}s")
    print(f"   - Taxa: {saved/duracao:.0f} registros/s")
    
    return len(errors) == 0

def test_save_historico(cnes="2755289", competencia="202512", total_salvos=1000):
    """Testa salvamento do histórico"""
    print("\n" + "=" * 60)
    print("TESTE 3: Salvamento de Histórico")
    print("=" * 60)
    
    db = BPADatabase()
    
    try:
        historico_data = {
            'cnes': cnes,
            'competencia': competencia,
            'total_bpa_i': total_salvos,
            'total_bpa_c': 0,
            'total_removido': 0,
            'total_geral': total_salvos,
            'valor_total_bpa_i': 10500.00,
            'valor_total_bpa_c': 0.00,
            'valor_total_geral': 10500.00,
            'procedimentos_mais_usados': [
                {
                    'codigo': '0301010070',
                    'nome': 'Consulta médica',
                    'quantidade': 100,
                    'valor_unitario': 10.50,
                    'valor_total': 1050.00
                }
            ],
            'profissionais_mais_ativos': [
                {
                    'cns': '700000000000001',
                    'cbo': '225125',
                    'quantidade': total_salvos
                }
            ],
            'distribuicao_por_dia': {
                '01': 50,
                '15': 100,
                '30': 20
            },
            'usuario_id': 1,
            'duracao_segundos': 45,
            'status': 'concluido'
        }
        
        historico_id = db.save_historico_extracao(historico_data)
        print(f"✅ Histórico salvo com ID: {historico_id}")
        print(f"   - Total BPA-I: {total_salvos}")
        print(f"   - Valor Total: R$ 10500.00")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar histórico: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cleanup(cnes="2755289", competencia="202512"):
    """Limpa dados de teste"""
    print("\n" + "=" * 60)
    print("TESTE 4: Limpeza de Dados de Teste")
    print("=" * 60)
    
    from database import get_connection
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Remove BPA-I de teste
                cursor.execute("""
                    DELETE FROM bpa_individualizado 
                    WHERE prd_uid = %s AND prd_cmp = %s
                """, (cnes, competencia))
                deleted_bpa = cursor.rowcount
                
                # Remove histórico de teste
                cursor.execute("""
                    DELETE FROM historico_extracoes 
                    WHERE cnes = %s AND competencia = %s
                """, (cnes, competencia))
                deleted_hist = cursor.rowcount
                
                conn.commit()
                
        print(f"✅ Limpeza concluída")
        print(f"   - BPA-I removidos: {deleted_bpa}")
        print(f"   - Históricos removidos: {deleted_hist}")
        return True
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🧪 TESTE COMPLETO - 1000 EXTRAÇÕES UPA NORTE")
    print("   CNES: 2755289 | Competência: 202512")
    print("=" * 60)
    
    inicio_total = time.time()
    
    # Gera dados
    records = generate_mock_records(1000)
    
    # Executa testes
    tests = [
        ("Validação de Campos", lambda: test_field_sizes(records)),
        ("Salvamento BPA-I", lambda: test_save_bpa_individualizado(records)),
        ("Salvamento Histórico", lambda: test_save_historico(total_salvos=len(records))),
        ("Limpeza", lambda: test_cleanup())
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            
            if not result:
                print(f"\n⚠️  Teste '{name}' falhou. Parando execução.")
                break
                
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
    duracao_total = time.time() - inicio_total
    
    print(f"\n📊 Resultado: {total_passed}/{total_tests} testes passaram")
    print(f"⏱️  Tempo total: {duracao_total:.2f}s")
    
    if total_passed == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        sys.exit(1)
