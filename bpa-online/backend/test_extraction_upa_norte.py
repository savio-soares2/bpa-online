"""
Teste de Extração BiServer - UPA Norte (CNES 2755289)
Investigação: Por que 30k procedimentos na tabela mas menos de 10k extraídos?

Objetivo:
1. Extrair dados SEM filtro SIGTAP e contar
2. Extrair dados COM filtro SIGTAP e contar
3. Detalhar onde os dados estão sendo filtrados
"""

import asyncio
import logging
import sys
from collections import Counter
from datetime import datetime

# Configura logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Importa serviços
from services.biserver_client import BiServerAPIClient, BiServerExtractionService
from services.sigtap_filter_service import get_sigtap_filter_service

CNES_UPA_NORTE = "2755289"
COMPETENCIA = "202601"  # Janeiro 2026


def test_api_raw_extraction():
    """
    Teste 1: Extração bruta da API sem nenhum filtro
    Verifica quantos registros a API retorna de fato
    """
    print("\n" + "="*80)
    print("TESTE 1: EXTRAÇÃO BRUTA DA API (SEM FILTROS)")
    print("="*80)
    
    client = BiServerAPIClient()
    
    # Formata competência
    comp_formatada = f"{COMPETENCIA[:4]}-{COMPETENCIA[4:6]}"
    
    all_records = []
    page = 0
    max_pages = 100  # Limite alto para pegar tudo
    
    print(f"\n📥 Extraindo da API para CNES={CNES_UPA_NORTE}, Competência={comp_formatada}")
    
    while page < max_pages:
        try:
            params = {
                "cnes": CNES_UPA_NORTE,
                "competencia": comp_formatada,
                "page": page
            }
            
            result = client.get("/api/bpa/data", params=params, timeout=180)
            
            page_records = result.get("registros", [])
            total_api = result.get("total_registros", "N/A")
            
            if not page_records:
                print(f"   Página {page}: vazia (FIM)")
                break
            
            all_records.extend(page_records)
            print(f"   Página {page}: {len(page_records)} registros (acumulado: {len(all_records)}, total API: {total_api})")
            
            # Se página tem menos que esperado, provavelmente é a última
            if len(page_records) < 500:
                print(f"   Página parcial - provavelmente última")
                break
                
            page += 1
            
            # Pequeno delay para não sobrecarregar
            import time
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Erro na página {page}: {e}")
            break
    
    print(f"\n📊 TOTAL EXTRAÍDO DA API: {len(all_records)} registros")
    
    # Analisa campos dos registros
    if all_records:
        first_record = all_records[0]
        print(f"\n📋 Campos do primeiro registro:")
        for key, value in first_record.items():
            print(f"   - {key}: {value}")
    
    return all_records


def analyze_procedures(records: list):
    """
    Teste 2: Analisa os procedimentos nos registros extraídos
    """
    print("\n" + "="*80)
    print("TESTE 2: ANÁLISE DOS PROCEDIMENTOS")
    print("="*80)
    
    # Conta procedimentos
    proc_counter = Counter()
    for rec in records:
        proc = rec.get('prd_pa', rec.get('procedimento', 'VAZIO'))
        proc_counter[proc] += 1
    
    print(f"\n📊 Total de procedimentos únicos: {len(proc_counter)}")
    print(f"📊 Top 20 procedimentos mais frequentes:")
    
    for proc, count in proc_counter.most_common(20):
        print(f"   {proc}: {count} registros")
    
    return proc_counter


def test_sigtap_filtering(records: list):
    """
    Teste 3: Aplica filtro SIGTAP e verifica quantos são removidos
    """
    print("\n" + "="*80)
    print("TESTE 3: FILTRO SIGTAP")
    print("="*80)
    
    try:
        sigtap = get_sigtap_filter_service()
        parser = sigtap.get_parser()
        
        if not parser:
            print("❌ SIGTAP não carregado - não é possível filtrar")
            return records, []
        
        # Obtém mapa de registro
        registro_map = sigtap._get_procedimento_registro_map()
        
        print(f"\n📊 Procedimentos no SIGTAP: {len(registro_map)}")
        
        # Classifica cada registro
        bpa_i_only = []  # Só BPA-I (tipo_registro = 02)
        bpa_c_only = []  # Só BPA-C (tipo_registro = 01)
        bpa_dual = []    # Ambos (01 e 02)
        sem_registro = []  # Não encontrado no SIGTAP
        
        proc_nao_encontrados = Counter()
        
        for rec in records:
            proc = rec.get('prd_pa', rec.get('procedimento', ''))
            registros = registro_map.get(proc, set())
            
            has_bpa_i = '02' in registros
            has_bpa_c = '01' in registros
            
            if has_bpa_i and has_bpa_c:
                bpa_dual.append(rec)
            elif has_bpa_i:
                bpa_i_only.append(rec)
            elif has_bpa_c:
                bpa_c_only.append(rec)
            else:
                sem_registro.append(rec)
                proc_nao_encontrados[proc] += 1
        
        print(f"\n📊 RESULTADO DA CLASSIFICAÇÃO:")
        print(f"   ✅ BPA-I only (tipo=02): {len(bpa_i_only)}")
        print(f"   ✅ BPA-C only (tipo=01): {len(bpa_c_only)}")
        print(f"   ✅ DUAL (01+02) → BPA-C: {len(bpa_dual)}")
        print(f"   ❌ SEM REGISTRO BPA: {len(sem_registro)}")
        
        print(f"\n📊 RESUMO:")
        total_validos = len(bpa_i_only) + len(bpa_c_only) + len(bpa_dual)
        print(f"   Total válidos para BPA: {total_validos}")
        print(f"   → Seriam BPA-I: {len(bpa_i_only)}")
        print(f"   → Seriam BPA-C: {len(bpa_c_only) + len(bpa_dual)}")
        print(f"   Removidos (sem registro): {len(sem_registro)}")
        
        if proc_nao_encontrados:
            print(f"\n📋 Procedimentos NÃO encontrados no SIGTAP (top 20):")
            for proc, count in proc_nao_encontrados.most_common(20):
                print(f"   {proc}: {count} registros")
        
        return (bpa_i_only, bpa_c_only + bpa_dual), sem_registro
        
    except Exception as e:
        print(f"❌ Erro ao filtrar: {e}")
        import traceback
        traceback.print_exc()
        return records, []


def test_with_extraction_service():
    """
    Teste 4: Usa o serviço de extração completo
    """
    print("\n" + "="*80)
    print("TESTE 4: SERVIÇO DE EXTRAÇÃO COMPLETO (SEM LIMITE)")
    print("="*80)
    
    service = BiServerExtractionService(enable_sigtap_validation=True)
    
    print(f"\n📥 Extraindo via serviço unificado (sem limite)...")
    result = service.extract_and_separate_bpa(
        cnes=CNES_UPA_NORTE,
        competencia=COMPETENCIA,
        limit=None  # Sem limite - extrai TUDO
    )
    
    print(f"\n📊 RESULTADO DO SERVIÇO:")
    print(f"   Success: {result.get('success')}")
    print(f"   Message: {result.get('message')}")
    
    stats = result.get('stats', {})
    print(f"\n📊 ESTATÍSTICAS:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n📊 REGISTROS RETORNADOS:")
    print(f"   BPA-I: {len(result.get('bpa_i', []))}")
    print(f"   BPA-C: {len(result.get('bpa_c', []))}")
    
    # Verifica se quantidade está sendo preservada na agregação
    bpa_c = result.get('bpa_c', [])
    if bpa_c:
        print(f"\n📊 VERIFICAÇÃO DE QUANTIDADES BPA-C:")
        total_qtd = sum(int(r.get('prd_qt_p', 0) or 0) for r in bpa_c)
        print(f"   Total de registros agregados: {len(bpa_c)}")
        print(f"   Soma total das quantidades (prd_qt_p): {total_qtd}")
        
        # Mostra alguns exemplos
        print(f"\n   Amostra de registros agregados:")
        for i, rec in enumerate(bpa_c[:10]):
            print(f"      {rec.get('prd_pa')} | CBO:{rec.get('prd_cbo')} | Idade:{rec.get('prd_idade')} | QTD:{rec.get('prd_qt_p')}")
    
    return result


def check_database_counts():
    """
    Teste 5: Verifica contagem no banco de dados
    """
    print("\n" + "="*80)
    print("TESTE 5: CONTAGEM NO BANCO DE DADOS")
    print("="*80)
    
    try:
        from database import BPADatabase
        db = BPADatabase()
        
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Conta BPA-I
                cur.execute("""
                    SELECT COUNT(*) FROM bpa_individualizado 
                    WHERE prd_uid = %s AND prd_cmp = %s
                """, (CNES_UPA_NORTE, COMPETENCIA))
                count_bpa_i = cur.fetchone()[0]
                
                # Conta BPA-C
                cur.execute("""
                    SELECT COUNT(*) FROM bpa_consolidado 
                    WHERE prd_uid = %s AND prd_cmp = %s
                """, (CNES_UPA_NORTE, COMPETENCIA))
                count_bpa_c = cur.fetchone()[0]
                
                # Conta total de todos CNES
                cur.execute("""
                    SELECT prd_uid, COUNT(*) as total 
                    FROM bpa_individualizado 
                    WHERE prd_cmp = %s
                    GROUP BY prd_uid
                    ORDER BY total DESC
                """, (COMPETENCIA,))
                
                print(f"\n📊 CONTAGEM POR CNES (BPA-I, competência {COMPETENCIA}):")
                for row in cur.fetchall():
                    print(f"   CNES {row[0]}: {row[1]} registros")
        
        print(f"\n📊 UPA NORTE ({CNES_UPA_NORTE}):")
        print(f"   BPA-I no banco: {count_bpa_i}")
        print(f"   BPA-C no banco: {count_bpa_c}")
        
    except Exception as e:
        print(f"❌ Erro ao consultar banco: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "#"*80)
    print("# INVESTIGAÇÃO DE EXTRAÇÃO BISERVER - UPA NORTE (CNES 2755289)")
    print(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# Competência: {COMPETENCIA}")
    print("#"*80)
    
    # Teste 1: Extração bruta
    records = test_api_raw_extraction()
    
    if records:
        # Teste 2: Análise de procedimentos
        analyze_procedures(records)
        
        # Teste 3: Filtro SIGTAP
        test_sigtap_filtering(records)
    
    # Teste 4: Serviço completo
    test_with_extraction_service()
    
    # Teste 5: Banco de dados
    check_database_counts()
    
    print("\n" + "#"*80)
    print("# FIM DA INVESTIGAÇÃO")
    print("#"*80)


if __name__ == "__main__":
    main()
