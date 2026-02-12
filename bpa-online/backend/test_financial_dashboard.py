
import sys
import os

# Adicionar backend ao path
sys.path.append(r"c:\Users\60612427358\Documents\bpa-online\bpa-online\backend")

from services.financial_service import get_financial_service

def test_dashboard():
    print("=== TESTE DASHBOARD FINANCEIRO ===")
    service = get_financial_service()
    
    # 1. Teste sem filtros (pega tudo)
    print("\n1. Teste Global (sem filtros)")
    stats = service.get_dashboard_stats()
    kpis = stats['kpis']
    print(f"Total Faturado: R$ {kpis['total_faturado']}")
    print(f"Total Procedimentos: {kpis['total_procedimentos']}")
    print(f"Total CBOs: {kpis['total_cbos_atuantes']}")
    
    if stats['graficos']['top_procedimentos_valor']:
        top1 = stats['graficos']['top_procedimentos_valor'][0]
        print(f"Top 1 Proc: {top1['nome']} (R$ {top1['valor']:.2f})")
    else:
        print("Nenhum procedimento encontrado.")

    # 2. Teste com Filtro de CBO (ex: Dentista 223505)
    print("\n2. Teste Filtro CBO '223505' (Cirurgião Dentista)")
    stats_cbo = service.get_dashboard_stats(cbo='223505')
    print(f"Total Faturado (Só Dentistas): R$ {stats_cbo['kpis']['total_faturado']}")
    
    # 3. Teste com Filtro de Procedimento (ex: Consulta 0301010072)
    print("\n3. Teste Filtro Procedimento '0301010072' (Consulta Básica)")
    stats_proc = service.get_dashboard_stats(procedimento='0301010072')
    print(f"Total Faturado (Só Consultas): R$ {stats_proc['kpis']['total_faturado']}")

if __name__ == "__main__":
    try:
        test_dashboard()
    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
