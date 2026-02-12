"""
Testes para o serviço de correções BPA
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.corrections import BPACorrections, CorrectionResult, pad_left


def test_pad_left():
    """Testa função pad_left (equivalente ao SM_PADLEFT do Firebird)"""
    assert pad_left('5', '0', 3) == '005'
    assert pad_left('12', '0', 2) == '12'
    assert pad_left('1', '0', 3) == '001'
    assert pad_left('999', '0', 3) == '999'
    assert pad_left('1', ' ', 5) == '    1'
    print("✅ Função pad_left (SM_PADLEFT): OK")


def test_correcao_raca():
    """Testa correção de raça/cor"""
    corrections = BPACorrections()
    
    # Raça 05 deve ser corrigida para 03
    record = {
        'procedimento': '0301010010',
        'raca_cor': '05',
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['raca_cor'] == '03'
    assert any('Raça' in c for c in result.corrections_applied)
    print("✅ Correção de raça 05 → 03: OK")
    
    # Raça 06 deve ser corrigida para 03
    record['raca_cor'] = '06'
    result = corrections.apply_corrections(record, 'BPI')
    assert result.corrected['raca_cor'] == '03'
    print("✅ Correção de raça 06 → 03: OK")


def test_procedimento_excluido():
    """Testa exclusão de procedimentos inválidos"""
    corrections = BPACorrections()
    
    # Procedimento da lista de exclusão
    record = {
        'procedimento': '0100000002',  # Na lista de exclusão
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert result.should_delete
    assert 'não pertence ao BPA' in result.delete_reason
    print("✅ Exclusão de procedimento inválido: OK")


def test_procedimento_revogado():
    """Testa correção de procedimentos revogados"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0214010090',  # Revogado
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['procedimento'] == '0214010295'
    print("✅ Correção de procedimento revogado: OK")


def test_correcao_cid():
    """Testa correção de CID por procedimento"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0302010017',  # Deve ter CID N318
        'cid': 'X999',  # CID errado
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['cid'] == 'N318'
    print("✅ Correção de CID por procedimento: OK")


def test_limite_quantidade():
    """Testa limite de quantidade por procedimento"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0302050027',  # Limite 20
        'quantidade': 50,  # Acima do limite
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['quantidade'] == 20
    print("✅ Limite de quantidade: OK")


def test_carater_atendimento_upa():
    """Testa correção de caráter de atendimento para UPA"""
    # UPA (CNES 2492555)
    corrections = BPACorrections('2492555')
    
    record = {
        'procedimento': '0301010010',
        'carater_atendimento': '01',
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['carater_atendimento'] == '02'
    print("✅ Correção de caráter de atendimento UPA: OK")


def test_cep_invalido():
    """Testa correção de CEP inválido"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0301010010',
        'cep': '77024899',  # CEP inválido
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['cep'] == '77001324'  # CEP padrão
    print("✅ Correção de CEP inválido: OK")


def test_cep_vazio():
    """Testa preenchimento de CEP vazio"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0301010010',
        'cep': '',
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['cep'] == '77001324'
    print("✅ Preenchimento de CEP vazio: OK")


def test_endereco_vazio():
    """Testa preenchimento de endereço vazio"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0301010010',
        'endereco': '',
        'bairro': None,
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['endereco'] == 'NAO LOCALIZADO'
    assert result.corrected['bairro'] == 'NAO LOCALIZADO'
    print("✅ Preenchimento de endereço/bairro vazio: OK")


def test_numero_invalido():
    """Testa correção de número inválido"""
    corrections = BPACorrections()
    
    for numero_invalido in ['', '00', 'S/N', 'SN']:
        record = {
            'procedimento': '0301010010',
            'numero': numero_invalido,
            'cns_paciente': '123456789012345'
        }
        result = corrections.apply_corrections(record, 'BPI')
        
        assert not result.should_delete
        assert result.corrected['numero'] == '01'
    
    print("✅ Correção de número inválido: OK")


def test_cns_paciente_vazio():
    """Testa exclusão quando CNS do paciente está vazio (BPI)"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0301010010',
        'cns_paciente': ''
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert result.should_delete
    assert 'CNS do paciente vazio' in result.delete_reason
    print("✅ Exclusão por CNS do paciente vazio: OK")


def test_batch_processing():
    """Testa processamento em lote"""
    corrections = BPACorrections('2492555')  # UPA
    
    records = [
        # Válido, será corrigido
        {
            'procedimento': '0301010010',
            'raca_cor': '05',
            'carater_atendimento': '01',
            'cns_paciente': '123456789012345'
        },
        # Será excluído (procedimento inválido)
        {
            'procedimento': '0100000002',
            'cns_paciente': '123456789012345'
        },
        # Será excluído (CNS vazio)
        {
            'procedimento': '0301010010',
            'cns_paciente': ''
        },
        # Válido, sem correções
        {
            'procedimento': '0301010010',
            'raca_cor': '01',
            'carater_atendimento': '02',
            'cns_paciente': '123456789012345',
            'cep': '77001324'
        }
    ]
    
    corrected, stats = corrections.process_batch(records, 'BPI')
    
    assert stats['total_input'] == 4
    assert stats['total_output'] == 2
    assert stats['deleted'] == 2
    assert len(corrected) == 2
    
    print("✅ Processamento em lote: OK")
    print(f"   - Total entrada: {stats['total_input']}")
    print(f"   - Total saída: {stats['total_output']}")
    print(f"   - Excluídos: {stats['deleted']}")
    print(f"   - Corrigidos: {stats['corrected']}")


def test_servico_classificacao():
    """Testa definição de serviço/classificação"""
    corrections = BPACorrections()
    
    record = {
        'procedimento': '0405050089',  # Deve ter serviço 131 e classificação 003
        'cns_paciente': '123456789012345'
    }
    result = corrections.apply_corrections(record, 'BPI')
    
    assert not result.should_delete
    assert result.corrected['servico'] == '131'
    assert result.corrected['classificacao'] == '003'
    print("✅ Definição de serviço/classificação: OK")


def test_sequenciamento_bpi():
    """Testa sequenciamento BPI (CORRIGE_SEQUENCIA_BPI)"""
    corrections = BPACorrections()
    
    # Cria 150 registros para testar mudança de folha (máx 99 por folha)
    records = []
    for i in range(150):
        records.append({
            'procedimento': f'03010100{str(i % 10).zfill(2)}',
            'cns_profissional': '123456789012345',  # Mesmo profissional
            'competencia': '202512',
            'cns_paciente': f'987654321{str(i).zfill(5)}'
        })
    
    sequenced = corrections.assign_sequence_bpi(records)
    
    # Verifica que os primeiros 99 estão na folha 001
    assert sequenced[0]['folha'] == '001'
    assert sequenced[0]['sequencia'] == '01'
    assert sequenced[98]['folha'] == '001'
    assert sequenced[98]['sequencia'] == '99'
    
    # Verifica que o 100º está na folha 002
    assert sequenced[99]['folha'] == '002'
    assert sequenced[99]['sequencia'] == '01'
    
    print("✅ Sequenciamento BPI (folha/sequência): OK")


def test_sequenciamento_bpa():
    """Testa sequenciamento BPA-C (CORRIGE_SEQUENCIA_BPA)"""
    corrections = BPACorrections()
    
    # Cria 25 registros para testar mudança de folha (máx 20 por folha)
    records = []
    for i in range(25):
        records.append({
            'procedimento': f'03010100{str(i % 10).zfill(2)}',
            'cnes': '2492555',  # Mesmo CNES
            'competencia': '202512',
            'cbo': '225125'
        })
    
    sequenced = corrections.assign_sequence_bpa(records)
    
    # Verifica que os primeiros 20 estão na folha 001
    assert sequenced[0]['folha'] == '001'
    assert sequenced[0]['sequencia'] == '01'
    assert sequenced[19]['folha'] == '001'
    assert sequenced[19]['sequencia'] == '20'
    
    # Verifica que o 21º está na folha 002
    assert sequenced[20]['folha'] == '002'
    assert sequenced[20]['sequencia'] == '01'
    
    print("✅ Sequenciamento BPA-C (folha/sequência): OK")


def test_gerador_id():
    """Testa gerador de IDs (GEN_S_PRD_ID)"""
    corrections = BPACorrections()
    
    # Cria registros e atribui IDs
    records = [{'procedimento': '0301010010'} for _ in range(5)]
    
    records = corrections.assign_ids(records, start_id=100)
    
    assert records[0]['prd_id'] == 100
    assert records[1]['prd_id'] == 101
    assert records[4]['prd_id'] == 104
    
    print("✅ Gerador de IDs (GEN_S_PRD_ID): OK")


if __name__ == '__main__':
    print("=" * 50)
    print("TESTES DO SERVIÇO DE CORREÇÕES BPA")
    print("=" * 50)
    print()
    
    test_pad_left()
    test_correcao_raca()
    test_procedimento_excluido()
    test_procedimento_revogado()
    test_correcao_cid()
    test_limite_quantidade()
    test_carater_atendimento_upa()
    test_cep_invalido()
    test_cep_vazio()
    test_endereco_vazio()
    test_numero_invalido()
    test_cns_paciente_vazio()
    test_servico_classificacao()
    test_batch_processing()
    test_sequenciamento_bpi()
    test_sequenciamento_bpa()
    test_gerador_id()
    
    print()
    print("=" * 50)
    print("TODOS OS TESTES PASSARAM! ✅")
    print("=" * 50)
