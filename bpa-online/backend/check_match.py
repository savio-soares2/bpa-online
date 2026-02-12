"""Verifica se pacientes pendentes existem no cadastro"""
import sys
sys.path.insert(0, '.')

from database import BPADatabase, get_connection

db = BPADatabase()

# Busca registros pendentes
pending = db.list_bpa_individualizado('2755289', '202512', exportado=False)
print(f"Total pendentes: {len(pending)}")

# Verifica quais existem no cadastro
encontrados = 0
nao_encontrados = 0
exemplos_nao_encontrados = []

for r in pending:
    nome = r.get('prd_nmpac', '')
    data_nasc = r.get('prd_dtnasc', '')
    
    if nome and data_nasc:
        paciente = db.get_paciente_by_nome_nascimento(nome, data_nasc)
        if paciente:
            encontrados += 1
        else:
            nao_encontrados += 1
            if len(exemplos_nao_encontrados) < 5:
                exemplos_nao_encontrados.append((nome, data_nasc))
    else:
        nao_encontrados += 1

print(f"\nResultado:")
print(f"  Encontrados no cadastro: {encontrados}")
print(f"  NÃO encontrados: {nao_encontrados}")

if encontrados > 0:
    print(f"\n✅ {encontrados} registros podem ser recuperados do cadastro!")
    
if exemplos_nao_encontrados:
    print(f"\nExemplos de pacientes não encontrados no cadastro:")
    for nome, nasc in exemplos_nao_encontrados:
        print(f"  - {nome} ({nasc})")
