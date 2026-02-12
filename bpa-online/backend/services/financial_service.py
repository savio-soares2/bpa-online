
from typing import List, Dict, Optional
import logging
from database import db
from services.sigtap_parser import SigtapParser
from services.sigtap_filter_service import get_sigtap_filter_service
from datetime import datetime

logger = logging.getLogger(__name__)

class FinancialService:
    def __init__(self):
        # Reutiliza o parser do serviço de filtro que já é singleton/cacheado
        self.sigtap_service = get_sigtap_filter_service()

    def get_dashboard_stats(
        self,
        competencia_inicio: str = None,
        competencia_fim: str = None,
        cnes_list: List[str] = None,
        tipo_bpa: str = None,
        cbo: str = None,
        procedimento: str = None
    ) -> Dict:
        """
        Gera estatísticas financeiras completas para o dashboard
        """
        # Usa parser da competência informada (ou ativa). Faz fallback se a competência não existir.
        parser = None
        parser_competencia = competencia_inicio or competencia_fim
        try:
            parser = self.sigtap_service.get_parser(parser_competencia)
        except Exception as e:
            logger.warning(f"Falha ao carregar SIGTAP da competência {parser_competencia}: {e}")
            try:
                parser = self.sigtap_service.get_parser()
            except Exception as e2:
                logger.error(f"Falha ao carregar SIGTAP ativo: {e2}")
                parser = None

        # 1. Buscar dados agregados do banco de dados
        raw_data = db.get_production_for_dashboard(
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            cnes_list=cnes_list,
            tipo_bpa=tipo_bpa,
            cbo=cbo,
            procedimento=procedimento
        )
        
        # 2. Processar e enriquecer com valores do SIGTAP
        stats = {
            'total_valor': 0.0,
            'total_procedimentos': 0,
            'total_profissionais': 0,  # Estimativa baseada em CBOs únicos por CNES (não exata na agregação atual)
            'evolution_data': {}, # {competencia: {valor: X, quantidade: Y}}
            'top_procedimentos': [],
            'top_cbos': []
        }
        
        proc_stats = {} # Mapa temporário para agregar totais por procedimento
        cbo_stats = {}  # Mapa temporário para agregar totais por CBO
        procedimentos_map = None
        if parser:
            try:
                procedimentos_map = {p['CO_PROCEDIMENTO']: p for p in parser.parse_procedimentos()}
            except Exception as e:
                logger.warning(f"Falha ao carregar procedimentos SIGTAP: {e}")
                procedimentos_map = None
        
        for row in raw_data:
            proc_code = row['procedimento']
            qtde_raw = row['quantidade_total'] or 0
            try:
                qtde = int(qtde_raw)
            except Exception:
                qtde = int(float(qtde_raw) if qtde_raw is not None else 0)
            competencia = row['competencia']
            cbo_code = row['cbo']
            
            # Buscar valor unitário
            valor_unit = 0.0
            if parser:
                try:
                    valores = parser.get_procedimento_valor(proc_code)
                    valor_unit = float(valores.get('valor_sa', 0.0) or 0.0)
                except Exception:
                    valor_unit = 0.0
            valor_total = float(valor_unit) * float(qtde)
            
            # Atualizar totais globais
            stats['total_valor'] += valor_total
            stats['total_procedimentos'] += qtde
            
            # Atualizar evolução temporal
            if competencia not in stats['evolution_data']:
                stats['evolution_data'][competencia] = {'valor': 0.0, 'quantidade': 0}
            stats['evolution_data'][competencia]['valor'] += valor_total
            stats['evolution_data'][competencia]['quantidade'] += qtde
            
            # Atualizar ranking procedimentos
            if proc_code not in proc_stats:
                # Buscar nome apenas uma vez
                dados_proc = procedimentos_map.get(proc_code) if procedimentos_map else None
                nome_proc = dados_proc['NO_PROCEDIMENTO'] if dados_proc else f"PROC {proc_code}"
                
                proc_stats[proc_code] = {
                    'codigo': proc_code,
                    'nome': nome_proc,
                    'quantidade': 0,
                    'valor': 0.0
                }
            proc_stats[proc_code]['quantidade'] += qtde
            proc_stats[proc_code]['valor'] += valor_total

            # Atualizar ranking CBOs
            if cbo_code:
                if cbo_code not in cbo_stats:
                    cbo_stats[cbo_code] = {
                        'cbo': cbo_code,
                        'quantidade': 0,
                        'valor': 0.0
                    }
                cbo_stats[cbo_code]['quantidade'] += qtde
                cbo_stats[cbo_code]['valor'] += valor_total
                
        # 3. Formatar resultados para o frontend
        
        # Evolução (ordenada por competência)
        evolution_list = [
            {'competencia': k, **v} 
            for k, v in sorted(stats['evolution_data'].items())
        ]
        
        # Top Procedimentos (por valor)
        top_procs = sorted(proc_stats.values(), key=lambda x: x['valor'], reverse=True)[:10]
        
        # Top CBOs (por valor)
        # Buscar nomes dos CBOs para exibição bonita
        # Mapa CBO -> Nome
        if parser:
            try:
                cbos_map = {c['CO_OCUPACAO']: c['NO_OCUPACAO'] for c in parser.parse_ocupacoes()}
                for item in cbo_stats.values():
                    item['nome'] = cbos_map.get(item['cbo'], f"CBO {item['cbo']}")
            except Exception:
                pass # Fallback se falhar parser de CBO
            
        top_cbos = sorted(cbo_stats.values(), key=lambda x: x['valor'], reverse=True)[:10]
        
        return {
            'kpis': {
                'total_faturado': round(stats['total_valor'], 2),
                'total_procedimentos': stats['total_procedimentos'],
                'total_cbos_atuantes': len(cbo_stats) 
            },
            'graficos': {
                'evolucao_faturamento': evolution_list,
                'top_procedimentos_valor': top_procs,
                'top_cbos_valor': top_cbos
            }
        }

# Singleton
_financial_service = None
def get_financial_service():
    global _financial_service
    if _financial_service is None:
        _financial_service = FinancialService()
    return _financial_service
