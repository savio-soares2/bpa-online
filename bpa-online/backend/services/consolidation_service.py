"""
Serviço de Consolidação BPA-I para BPA-C
Converte registros individualizados em consolidados baseado em listas de procedimentos
"""
import json
import os
from typing import Dict, List, Tuple
from database import BPADatabase
import logging

logger = logging.getLogger(__name__)

class BPAConsolidationService:
    """Serviço para consolidar BPA-I em BPA-C"""
    
    def __init__(self):
        self.db = BPADatabase()
        self._load_procedimentos_lists()
    
    def _load_procedimentos_lists(self):
        """Carrega listas de procedimentos do arquivo JSON"""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'procedimentos_bpa_c.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.proc_bpa_c_geral = set(data['bpa_c_geral']['procedimentos'])
                self.proc_bpa_c_idade = set(data['bpa_c_idade']['procedimentos'])
                logger.info(f"Carregadas {len(self.proc_bpa_c_geral)} procedimentos BPA-C geral")
                logger.info(f"Carregadas {len(self.proc_bpa_c_idade)} procedimentos BPA-C com idade")
        except Exception as e:
            logger.error(f"Erro ao carregar listas de procedimentos: {e}")
            self.proc_bpa_c_geral = set()
            self.proc_bpa_c_idade = set()
    
    def consolidar_bpai_para_bpac(self, cnes: str, competencia: str) -> Dict:
        """
        Consolida BPA-I em BPA-C para um CNES e competência específicos
        
        Fluxo:
        1. Identifica BPA-I que devem virar BPA-C (baseado na lista de procedimentos)
        2. Agrupa por: CNES + CBO + Procedimento + Competência (+ Idade se aplicável)
        3. Soma quantidades
        4. Cria registros BPA-C
        5. Remove BPA-I originais que viraram BPA-C
        
        Args:
            cnes: Código CNES
            competencia: Competência YYYYMM
            
        Returns:
            Dict com estatísticas da consolidação
        """
        try:
            logger.info(f"Iniciando consolidação BPA-I → BPA-C: CNES={cnes}, Competência={competencia}")
            
            stats = {
                'cnes': cnes,
                'competencia': competencia,
                'bpai_analisados': 0,
                'bpac_geral_criados': 0,
                'bpac_idade_criados': 0,
                'bpai_removidos': 0,
                'bpai_mantidos': 0,
                'erros': []
            }
            
            # 1. Busca todos os BPA-I do CNES/Competência
            bpai_records = self.db.list_bpa_individualizado(cnes, competencia, exportado=False)
            stats['bpai_analisados'] = len(bpai_records)
            
            if not bpai_records:
                logger.info("Nenhum BPA-I encontrado para consolidar")
                return stats
            
            # 2. Separa por tipo de consolidação
            to_consolidate_geral = []  # Vira BPA-C sem idade
            to_consolidate_idade = []  # Vira BPA-C com idade
            to_keep = []  # Mantém como BPA-I
            
            for record in bpai_records:
                procedimento = record.get('prd_pa', '')
                
                if procedimento in self.proc_bpa_c_geral:
                    to_consolidate_geral.append(record)
                elif procedimento in self.proc_bpa_c_idade:
                    to_consolidate_idade.append(record)
                else:
                    to_keep.append(record)
            
            stats['bpai_mantidos'] = len(to_keep)
            
            # 3. Consolida BPA-C Geral (sem idade)
            if to_consolidate_geral:
                created, removed = self._consolidate_geral(to_consolidate_geral, cnes, competencia)
                stats['bpac_geral_criados'] = created
                stats['bpai_removidos'] += removed
            
            # 4. Consolida BPA-C com Idade
            if to_consolidate_idade:
                created, removed = self._consolidate_idade(to_consolidate_idade, cnes, competencia)
                stats['bpac_idade_criados'] = created
                stats['bpai_removidos'] += removed
            
            logger.info(f"Consolidação concluída: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro na consolidação: {e}")
            stats['erros'].append(str(e))
            return stats
    
    def _consolidate_geral(self, records: List[Dict], cnes: str, competencia: str) -> Tuple[int, int]:
        """
        Consolida BPA-I em BPA-C GERAL (idade = 000)
        Agrupa por: CNES + CBO + Procedimento + Competência
        """
        # Agrupa registros
        grupos = {}
        
        for record in records:
            cbo = record.get('prd_cbo', '')
            procedimento = record.get('prd_pa', '')
            quantidade = record.get('prd_qt_p', 1)
            
            # Chave de agrupamento
            key = (cnes, competencia, cbo, procedimento)
            
            if key not in grupos:
                grupos[key] = {
                    'quantidade_total': 0,
                    'ids': []
                }
            
            grupos[key]['quantidade_total'] += quantidade
            grupos[key]['ids'].append(record.get('id'))
        
        # Cria registros BPA-C
        created = 0
        removed = 0
        
        for (uid, cmp, cbo, pa), data in grupos.items():
            try:
                # Cria BPA-C
                bpac_data = {
                    'prd_uid': uid,
                    'prd_cmp': cmp,
                    'prd_flh': 1,
                    'prd_cnsmed': '',  # Consolidado não tem CNS individual
                    'prd_cbo': cbo,
                    'prd_pa': pa,
                    'prd_qt_p': data['quantidade_total'],
                    'prd_idade': '000',  # Todas as idades
                    'prd_org': 'BPC'
                }
                
                self.db.save_bpa_consolidado(bpac_data)
                created += 1
                
                # Remove BPA-I originais
                for bpai_id in data['ids']:
                    if self.db.delete_bpa_individualizado(bpai_id):
                        removed += 1
                        
            except Exception as e:
                logger.error(f"Erro ao consolidar grupo {key}: {e}")
        
        return created, removed
    
    def _consolidate_idade(self, records: List[Dict], cnes: str, competencia: str) -> Tuple[int, int]:
        """
        Consolida BPA-I em BPA-C COM IDADE
        Agrupa por: CNES + CBO + Procedimento + Competência + Idade
        """
        # Agrupa registros
        grupos = {}
        
        for record in records:
            cbo = record.get('prd_cbo', '')
            procedimento = record.get('prd_pa', '')
            idade = record.get('prd_idade', '000')
            quantidade = record.get('prd_qt_p', 1)
            
            # Chave de agrupamento (inclui idade)
            key = (cnes, competencia, cbo, procedimento, idade)
            
            if key not in grupos:
                grupos[key] = {
                    'quantidade_total': 0,
                    'ids': []
                }
            
            grupos[key]['quantidade_total'] += quantidade
            grupos[key]['ids'].append(record.get('id'))
        
        # Cria registros BPA-C
        created = 0
        removed = 0
        
        for (uid, cmp, cbo, pa, idade), data in grupos.items():
            try:
                # Cria BPA-C
                bpac_data = {
                    'prd_uid': uid,
                    'prd_cmp': cmp,
                    'prd_flh': 1,
                    'prd_cnsmed': '',  # Consolidado não tem CNS individual
                    'prd_cbo': cbo,
                    'prd_pa': pa,
                    'prd_qt_p': data['quantidade_total'],
                    'prd_idade': idade,  # Mantém faixa etária
                    'prd_org': 'BPC'
                }
                
                self.db.save_bpa_consolidado(bpac_data)
                created += 1
                
                # Remove BPA-I originais
                for bpai_id in data['ids']:
                    if self.db.delete_bpa_individualizado(bpai_id):
                        removed += 1
                        
            except Exception as e:
                logger.error(f"Erro ao consolidar grupo {key}: {e}")
        
        return created, removed
    
    def verificar_procedimento(self, codigo: str) -> Dict:
        """
        Verifica se um procedimento deve ser BPA-I ou BPA-C
        
        Returns:
            Dict com tipo e detalhes
        """
        if codigo in self.proc_bpa_c_geral:
            return {
                'codigo': codigo,
                'tipo': 'BPA-C',
                'subtipo': 'geral',
                'idade': '000',
                'descricao': 'Deve ser consolidado SEM separação por idade'
            }
        elif codigo in self.proc_bpa_c_idade:
            return {
                'codigo': codigo,
                'tipo': 'BPA-C',
                'subtipo': 'idade',
                'idade': 'mantém',
                'descricao': 'Deve ser consolidado COM separação por faixa etária'
            }
        else:
            return {
                'codigo': codigo,
                'tipo': 'BPA-I',
                'subtipo': None,
                'idade': None,
                'descricao': 'Mantém como BPA Individualizado'
            }


# Singleton
_consolidation_service = None

def get_consolidation_service() -> BPAConsolidationService:
    """Retorna instância singleton do serviço de consolidação"""
    global _consolidation_service
    if _consolidation_service is None:
        _consolidation_service = BPAConsolidationService()
    return _consolidation_service
