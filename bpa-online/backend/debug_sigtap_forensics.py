
import sys
import os
from pathlib import Path

# Adiciona diretório backend
sys.path.append(r"c:\Users\60612427358\Documents\bpa-online\bpa-online\backend")
from services.sigtap_filter_service import SigtapFilterService

def run():
    service = SigtapFilterService()
    parser = service.parser
    sigtap_dir = parser.sigtap_dir
    
    print(f"Diretório SIGTAP: {sigtap_dir}")
    print(f"Arquivo de Relacionamento: {sigtap_dir / 'rl_procedimento_servico.txt'}")
    
    # 1. Encontrar códigos de odontologia em tb_procedimento
    # Grupo 03, Subgrupo 07 (Odontologia) -> Começa com 0307
    print("\nProcurando procedimentos de Odontologia (0307...)...")
    
    dental_procs = []
    all_procs = parser.parse_procedimentos()
    
    for p in all_procs:
        cod = p['CO_PROCEDIMENTO']
        if cod.startswith('0307'):
            dental_procs.append(p)
            
    print(f"Encontrados {len(dental_procs)} procedimentos de Odontologia (Grupo 03.07).")
    
    if not dental_procs:
        print("Sério? Nenhum procedimento 03.07 encontrado? Algo errado com tb_procedimento.")
        return

    # Amostra de 5 procedimentos
    sample = dental_procs[:5]
    print("Amostra:")
    for p in sample:
        print(f" - {p['CO_PROCEDIMENTO']} {p['NO_PROCEDIMENTO']}")
        
    # 2. Verificar vínculo em rl_procedimento_servico
    print("\nVerificando vínculos em RL_PROCEDIMENTO_SERVICO...")
    relacoes = parser.parse_procedimento_servico()
    
    # Indexar para busca rápida
    # map: proc -> list of services
    proc_srv_map = {}
    for r in relacoes:
        p = r['CO_PROCEDIMENTO']
        s = r['CO_SERVICO']
        if p not in proc_srv_map: proc_srv_map[p] = []
        proc_srv_map[p].append(s)
        
    # Verificar a amostra
    for p in sample:
        cod = p['CO_PROCEDIMENTO']
        servicos = proc_srv_map.get(cod, [])
        print(f"Proc {cod} está vinculado aos serviços: {servicos}")
        
    # Verificar se algum dental está no 114
    count_114 = 0
    for p in dental_procs:
        cod = p['CO_PROCEDIMENTO']
        servicos = proc_srv_map.get(cod, [])
        if '114' in servicos:
            count_114 += 1
            
    print(f"\nTotal dental (0307) vinculados ao serviço 114: {count_114} / {len(dental_procs)}")
    
    # 3. Listar quais serviços são os mais comuns para dental
    from collections import Counter
    srv_counter = Counter()
    for p in dental_procs:
        cod = p['CO_PROCEDIMENTO']
        servicos = proc_srv_map.get(cod, [])
        for s in servicos:
            srv_counter[s] += 1
            
    print("\nServiços mais comuns para Odontologia:")
    for srv, count in srv_counter.most_common(10):
        print(f"Serviço {srv}: {count} procedimentos")

if __name__ == "__main__":
    run()
