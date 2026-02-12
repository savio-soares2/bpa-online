"""Debug de exportação - verifica registros pendentes e aplica correções"""
import sys
sys.path.insert(0, '.')

from database import BPADatabase
from services.corrections import BPACorrections
from exporter import FirebirdExporter

db = BPADatabase()
cnes = "2755289"
competencia = "202512"

print("="*70)
print("DEBUG DE EXPORTAÇÃO BPA-I")
print("="*70)

# 1. Verifica registros no banco
print("\n[1] CONTAGEM DE REGISTROS NO BANCO")
print("-"*50)

# Todos
all_records = db.list_bpa_individualizado(cnes, competencia, exportado=None)
print(f"Total de registros: {len(all_records)}")

# Exportados
exported = db.list_bpa_individualizado(cnes, competencia, exportado=True)
print(f"Exportados (prd_exportado=TRUE): {len(exported)}")

# Pendentes
pending = db.list_bpa_individualizado(cnes, competencia, exportado=False)
print(f"Pendentes (prd_exportado=FALSE): {len(pending)}")

if not pending:
    print("\n[!] Nenhum registro pendente encontrado!")
    sys.exit(0)

# 2. Amostra de registros pendentes
print("\n[2] AMOSTRA DE 5 REGISTROS PENDENTES")
print("-"*50)
for i, r in enumerate(pending[:5]):
    print(f"  #{i+1}: ID={r['id']}, PA={r.get('prd_pa')}, CNS={r.get('prd_cnsmed')}, CBO={r.get('prd_cbo')}")

# 3. Aplica correções para ver o que acontece
print("\n[3] SIMULAÇÃO DE CORREÇÕES")
print("-"*50)

# Mapeia campos
FIELD_MAP_BPAI = {
    'prd_uid': 'cnes', 'prd_cmp': 'competencia', 'prd_cnsmed': 'cns_profissional',
    'prd_cbo': 'cbo', 'prd_flh': 'folha', 'prd_seq': 'sequencia', 'prd_pa': 'procedimento',
    'prd_cnspac': 'cns_paciente', 'prd_nmpac': 'nome_paciente', 'prd_dtnasc': 'data_nascimento',
    'prd_sexo': 'sexo', 'prd_raca': 'raca_cor', 'prd_nac': 'nacionalidade',
    'prd_ibge': 'municipio_ibge', 'prd_dtaten': 'data_atendimento', 'prd_qt_p': 'quantidade',
    'prd_cid': 'cid', 'prd_caten': 'carater_atendimento', 'prd_naut': 'numero_autorizacao',
    'prd_ine': 'ine', 'prd_servico': 'servico', 'prd_classificacao': 'classificacao',
}

def map_record(record):
    mapped = {'id': record.get('id')}
    for db_field, snake_field in FIELD_MAP_BPAI.items():
        if db_field in record:
            mapped[snake_field] = record[db_field]
    return mapped

mapped_records = [map_record(r) for r in pending]
print(f"Registros mapeados: {len(mapped_records)}")

# Aplica correções
corrections = BPACorrections(cnes)
corrected_records, stats = corrections.process_batch(mapped_records, 'BPI')

print(f"\nResultado das correções:")
print(f"  - Entrada: {stats.get('total_input', 0)}")
print(f"  - Corrigidos: {stats.get('corrected', 0)}")
print(f"  - Excluídos: {stats.get('deleted', 0)}")
print(f"  - Restantes: {len(corrected_records)}")

if stats.get('delete_reasons'):
    print(f"\nMotivos de exclusão:")
    for reason, count in stats['delete_reasons'].items():
        print(f"  - {reason}: {count}")

if stats.get('correction_types'):
    print(f"\nTipos de correção aplicados:")
    for ctype, count in stats['correction_types'].items():
        print(f"  - {ctype}: {count}")

# 4. Se todos foram excluídos, mostra exemplos
if len(corrected_records) == 0 and stats.get('deleted', 0) > 0:
    print("\n[4] EXEMPLOS DE REGISTROS EXCLUÍDOS")
    print("-"*50)
    
    # Processa um por um para ver motivo
    for i, record in enumerate(mapped_records[:10]):
        result = corrections.process_record(record, 'BPI')
        if result.should_delete:
            print(f"  PA={record.get('procedimento')}: {result.delete_reason}")

print("\n" + "="*70)
print("FIM DO DEBUG")
print("="*70)
