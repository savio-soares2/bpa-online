
import sys
import os

# Adiciona diretório backend ao path para imports funcionarem
sys.path.append(r"c:\Users\60612427358\Documents\bpa-online\bpa-online\backend")

from services.sigtap_filter_service import SigtapFilterService

def debug_ceo():
    service = SigtapFilterService()
    parser = service.parser
    
    print("=== DEBUG CEO (Serviço 114) ===")
    
    # 1. Verificar prosedimentos do Serviço 114
    procs_114 = parser.get_procedimentos_by_servico("114")
    print(f"Total Procedimentos no Serviço 114 (Saúde Bucal): {len(procs_114)}")
    
    if len(procs_114) == 0:
        print("ALERTA: Nenhum procedimento encontrado para serviço 114!")
    
    # 2. Buscar exemplos e verificar tipo de registro
    # Carregar todos para lookup rápido
    all_procs = {p['CO_PROCEDIMENTO']: p for p in parser.parse_procedimentos()}
    registro_map = service._get_procedimento_registro_map()
    
    # Keywords comuns de CEO
    keywords = ["ENDODONTIA", "PERIODONTIA", "CIRURGIA", "RESTAURACAO", "EXODONTIA"]
    
    found_count = 0
    for code in procs_114:
        if code in all_procs:
            proc = all_procs[code]
            nome = proc['NO_PROCEDIMENTO']
            
            # Checa se é relevante
            if any(k in nome.upper() for k in keywords):
                registros = registro_map.get(code, set())
                reg_str = ", ".join(registros)
                print(f"[{code}] {nome[:50]}... | Instrumentos: {reg_str}")
                found_count += 1
                if found_count >= 15: # Amostra
                    break
                    
    # 3. Verificar especificamente para o CNES do CEO se configurado
    print("\n=== DEBUG CNES CEO (2492547) ===")
    try:
        procs_ceo = service.get_procedimentos_por_estabelecimento("2492547")
        print(f"Total Procedimentos Válidos para CNES 2492547: {len(procs_ceo)}")
        
        # Verificar se procedimentos BPA-I estão lá
        bpa_i_count = 0
        bpa_c_count = 0
        for p in procs_ceo:
            regs = registro_map.get(p, set())
            if '02' in regs: bpa_i_count += 1
            if '01' in regs: bpa_c_count += 1
            
        print(f"  - BPA-I: {bpa_i_count}")
        print(f"  - BPA-C: {bpa_c_count}")
        
    except Exception as e:
        print(f"Erro ao testar estabelecimento: {e}")

if __name__ == "__main__":
    debug_ceo()
