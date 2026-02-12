"""
Serviço de filtragem de procedimentos usando tabelas SIGTAP diretamente dos arquivos TXT
"""
from typing import List, Dict, Optional, Set, Union
from services.sigtap_parser import SigtapParser
from services.sigtap_manager_service import get_sigtap_manager
import logging

logger = logging.getLogger(__name__)

class SigtapFilterService:
    """Serviço para filtrar procedimentos baseado em CBO e tipo de estabelecimento"""
    
    def __init__(self, sigtap_dir: str = None):
        self.manager = get_sigtap_manager()
        self._parsers: Dict[str, SigtapParser] = {}
        
        # Retrocompatibilidade
        if sigtap_dir:
            logger.info(f"Modo SIGTAP legado ativado: {sigtap_dir}")
            self._parsers["LEGACY"] = SigtapParser(sigtap_dir)

    def _get_parser(self, competencia: str = None) -> SigtapParser:
        if not competencia:
            competencia = self.manager.get_active_competencia()
            if not competencia:
                if "LEGACY" in self._parsers:
                    return self._parsers["LEGACY"]
                
                try:
                    dir_path = self.manager.get_sigtap_dir(None)
                    competencia = "LEGACY_AUTO"
                    if competencia not in self._parsers:
                         self._parsers[competencia] = SigtapParser(dir_path)
                    return self._parsers[competencia]
                except Exception as e:
                     logger.error(f"Não foi possível obter parser SIGTAP: {e}")
                     raise ValueError("SIGTAP não configurado. Importe uma competência.")
        
        if competencia not in self._parsers:
            try:
                dir_path = self.manager.get_sigtap_dir(competencia)
                self._parsers[competencia] = SigtapParser(dir_path)
            except Exception as e:
                if "LEGACY" in self._parsers:
                    logger.warning(f"Competência {competencia} não encontrada, usando LEGACY.")
                    return self._parsers["LEGACY"]
                raise e
            
        return self._parsers[competencia]
    
    def _get_procedimento_registro_map(self, competencia: str = None) -> Dict[str, Set[str]]:
        relacoes = self._get_parser(competencia).parse_procedimento_registro()
        result = {}
        for rel in relacoes:
            proc = rel['CO_PROCEDIMENTO']
            registro = rel['CO_REGISTRO']
            if proc not in result:
                result[proc] = set()
            result[proc].add(registro)
        return result
    
    def _get_procedimento_cbo_map(self, competencia: str = None) -> Dict[str, Set[str]]:
        relacoes = self._get_parser(competencia).parse_procedimento_ocupacao()
        result = {}
        for rel in relacoes:
            proc = rel['CO_PROCEDIMENTO']
            cbo = rel['CO_OCUPACAO']
            if proc not in result:
                result[proc] = set()
            result[proc].add(cbo)
        return result
    
    def _get_procedimento_servico_map(self, competencia: str = None) -> Dict[str, Set[tuple]]:
        relacoes = self._get_parser(competencia).parse_procedimento_servico()
        result = {}
        for rel in relacoes:
            proc = rel['CO_PROCEDIMENTO']
            servico = rel['CO_SERVICO']
            classificacao = rel['CO_CLASSIFICACAO']
            if proc not in result:
                result[proc] = set()
            result[proc].add((servico, classificacao))
        return result
    
    def get_procedimentos_filtrados(
        self,
        tipo_registro: Union[str, List[str]] = None,
        cbo: str = None,
        servico: str = None,
        classificacao: str = None,
        termo_busca: str = None,
        competencia: str = None,
        sort_field: str = None,
        sort_order: str = 'asc'
    ) -> List[Dict[str, str]]:
        """
        Retorna procedimentos filtrados por múltiplos critérios
        """
        parser = self._get_parser(competencia)
        todos_procedimentos = parser.parse_procedimentos()
        registro_map = self._get_procedimento_registro_map(competencia)

        # Copia da lista para não alterar cache
        # Mas para performance, vamos filtrar primeiro
        procedimentos = todos_procedimentos
        
        # Filtrar por tipo de registro (BPA-I, BPA-C, etc) - Lógica OR para lista
        if tipo_registro:
            if isinstance(tipo_registro, str):
                tipos = {tipo_registro}
            else:
                tipos = set(tipo_registro)
                
            procedimentos = [
                p for p in procedimentos
                if tipos.intersection(registro_map.get(p['CO_PROCEDIMENTO'], set()))
            ]
        
        # Filtrar por CBO
        if cbo:
            cbo_map = self._get_procedimento_cbo_map(competencia)
            procedimentos = [
                p for p in procedimentos
                if cbo in cbo_map.get(p['CO_PROCEDIMENTO'], set())
            ]
        
        # Filtrar por serviço/classificação
        if servico or classificacao:
            servico_map = self._get_procedimento_servico_map(competencia)
            procedimentos = [
                p for p in procedimentos
                if any(
                    (not servico or s == servico) and 
                    (not classificacao or c == classificacao)
                    for s, c in servico_map.get(p['CO_PROCEDIMENTO'], set())
                )
            ]
        
        # Filtrar por termo de busca no nome
        if termo_busca:
            termo_upper = termo_busca.upper()
            filtered = []
            for p in procedimentos:
                if (termo_upper in p['NO_PROCEDIMENTO'].upper()) or (termo_upper in p['CO_PROCEDIMENTO']):
                    filtered.append(p)
            procedimentos = filtered
        
        # Enriquecer com lista de registros e Valores float
        enriched = []
        for p in procedimentos:
            # Copiar para não alterar original do cache
            item = p.copy()
            item['REGISTROS'] = list(registro_map.get(p['CO_PROCEDIMENTO'], set()))
            
            # Converter valores para sort (se ainda forem strings)
            # O parser retorna strings no dict bruto, mas tem o método get_procedimento_valor que retorna float
            # Aqui vamos adicionar floats helper
            item['_vl_sa_float'] = float(p.get('VL_SA', '0')) / 100
            item['_vl_sh_float'] = float(p.get('VL_SH', '0')) / 100
            
            enriched.append(item)
            
        procedimentos = enriched
            
        # Ordenação
        if sort_field:
            reverse = sort_order == 'desc'
            if sort_field == 'valor':
                # Usa valor ambulatorial como referência principal
                procedimentos.sort(key=lambda x: x['_vl_sa_float'], reverse=reverse)
            elif sort_field == 'nome':
                procedimentos.sort(key=lambda x: x['NO_PROCEDIMENTO'], reverse=reverse)
            elif sort_field == 'codigo':
                procedimentos.sort(key=lambda x: x['CO_PROCEDIMENTO'], reverse=reverse)

        return procedimentos
    
    def get_procedimentos_por_profissional(
        self,
        cbo: str,
        tipo_bpa: str = '02',
        termo_busca: str = None,
        competencia: str = None
    ) -> List[Dict[str, str]]:
        return self.get_procedimentos_filtrados(
            tipo_registro=tipo_bpa,
            cbo=cbo,
            termo_busca=termo_busca,
            competencia=competencia
        )
    
    def get_cbos(self, competencia: str = None) -> List[Dict[str, str]]:
        return self._get_parser(competencia).parse_ocupacoes()
    
    def get_servicos(self, competencia: str = None) -> List[Dict[str, str]]:
        return self._get_parser(competencia).parse_servicos()
    
    def get_registros(self, competencia: str = None) -> List[Dict[str, str]]:
        return self._get_parser(competencia).parse_registros()

    def get_parser(self, competencia: str = None) -> SigtapParser:
        """Retorna o parser da competência informada (ou ativa)"""
        return self._get_parser(competencia)
    
    def get_procedimento_info(self, codigo: str, competencia: str = None) -> Optional[Dict]:
        """
        Retorna informações completas de um procedimento específico
        
        Args:
            codigo: Código do procedimento (10 dígitos)
            competencia: Competência SIGTAP (opcional)
            
        Returns:
            Dict com dados do procedimento ou None se não encontrado
        """
        parser = self._get_parser(competencia)
        procedimentos = parser.parse_procedimentos()
        
        for proc in procedimentos:
            if proc['CO_PROCEDIMENTO'] == codigo:
                # Obter valores financeiros
                valores = parser.get_procedimento_valor(codigo)
                
                # Obter registros permitidos
                registro_map = self._get_procedimento_registro_map(competencia)
                registros = list(registro_map.get(codigo, set()))
                
                # Obter CBOs permitidos
                cbo_map = self._get_procedimento_cbo_map(competencia)
                cbos = list(cbo_map.get(codigo, set()))
                
                return {
                    'codigo': proc['CO_PROCEDIMENTO'],
                    'nome': proc['NO_PROCEDIMENTO'],
                    'complexidade': proc.get('TP_COMPLEXIDADE', ''),
                    'sexo': proc.get('TP_SEXO', ''),
                    'idade_minima': proc.get('VL_IDADE_MINIMA', ''),
                    'idade_maxima': proc.get('VL_IDADE_MAXIMA', ''),
                    'valor_sa': valores['valor_sa'],
                    'valor_sh': valores['valor_hospitalar'],
                    'valor_sp': valores['valor_sp'],
                    'valor_total': valores['valor_sa'] + valores['valor_hospitalar'] + valores['valor_sp'],
                    'registros': registros,
                    'cbos': cbos,
                    'raw': proc
                }
        
        return None
    
    def verificar_procedimento_valido(
        self,
        co_procedimento: str,
        cbo: str,
        tipo_bpa: str = '02',
        competencia: str = None
    ) -> bool:
        cbo_map = self._get_procedimento_cbo_map(competencia)
        registro_map = self._get_procedimento_registro_map(competencia)
        
        if co_procedimento not in cbo_map: return False
        if cbo not in cbo_map[co_procedimento]: return False
        if co_procedimento not in registro_map: return False
        if tipo_bpa not in registro_map[co_procedimento]: return False
        
        return True
    
    def get_estatisticas(self, competencia: str = None) -> Dict:
        parser = self._get_parser(competencia)
        return {
            'competencia': competencia or self.manager.get_active_competencia() or 'LEGACY',
            'total_procedimentos': len(parser.parse_procedimentos()),
            'total_cbos': len(parser.parse_ocupacoes()),
            'total_servicos': len(parser.parse_servicos()),
            'total_instrumentos': len(parser.parse_registros()),
            'total_relacoes_cbo': len(parser.parse_procedimento_ocupacao()),
            'total_relacoes_servico': len(parser.parse_procedimento_servico()),
            'total_relacoes_registro': len(parser.parse_procedimento_registro()),
        }
    
    def get_procedimentos_por_estabelecimento(
        self,
        cnes: str,
        tipo_registro: str = None,
        competencia: str = None
    ) -> Set[str]:
        from constants.estabelecimentos import (
            get_estabelecimento, get_servicos_por_tipo, 
            get_classificacoes_por_tipo, is_ambulatorio_geral
        )
        
        parser = self._get_parser(competencia)
        estabelecimento = get_estabelecimento(cnes)
        if not estabelecimento:
            logger.warning(f"CNES {cnes} não encontrado, retornando todos ambulatoriais")
            return parser.get_procedimentos_ambulatoriais()
        
        tipo = estabelecimento.get("tipo")
        servico_especifico = estabelecimento.get("servico_sigtap")
        classificacao_especifica = estabelecimento.get("classificacao_sigtap")
        
        if is_ambulatorio_geral(cnes):
            procedimentos = parser.get_procedimentos_ambulatoriais()
        else:
            if servico_especifico:
                procedimentos = set(parser.get_procedimentos_by_servico(
                    servico_especifico, 
                    classificacao_especifica
                ))
            else:
                servicos = get_servicos_por_tipo(tipo)
                classificacoes = get_classificacoes_por_tipo(tipo)
                if servicos:
                    procedimentos = parser.get_procedimentos_by_servicos(servicos, classificacoes or None)
                else:
                    procedimentos = parser.get_procedimentos_ambulatoriais()
        
        if tipo_registro:
            registro_map = self._get_procedimento_registro_map(competencia)
            procedimentos = {
                p for p in procedimentos
                if tipo_registro in registro_map.get(p, set())
            }
        
        return procedimentos
    
    def validar_procedimento_para_estabelecimento(
        self,
        co_procedimento: str,
        cnes: str,
        tipo_registro: str = None,
        competencia: str = None
    ) -> bool:
        procedimentos_validos = self.get_procedimentos_por_estabelecimento(cnes, tipo_registro, competencia)
        return co_procedimento in procedimentos_validos


_filter_service = None
def get_sigtap_filter_service() -> SigtapFilterService:
    global _filter_service
    if _filter_service is None:
        _filter_service = SigtapFilterService()
    return _filter_service
