import os
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from dbfread import DBF
import json

logger = logging.getLogger(__name__)

class DBFManagerService:
    """Serviço para gerenciar os arquivos DBF e extrair relações CBO/Procedimentos"""
    
    def __init__(self, dbf_path: str = None):
        """
        Inicializa o serviço DBF
        
        Args:
            dbf_path: Caminho para o diretório dos DBFs. Se None, usa o padrão do BPA
        """
        self.dbf_path = dbf_path or r"c:\BPA\Tabelas Nacionais do Kit BPA\202511"
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'dbf_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache em memória para performance
        self._cbo_procedimentos_cache = None
        self._procedimentos_cache = None
        self._cache_timestamp = None
        
    def _get_cache_file(self, table_name: str) -> str:
        """Retorna caminho do arquivo de cache para uma tabela"""
        return os.path.join(self.cache_dir, f"{table_name}_cache.json")
    
    def _load_dbf_table(self, table_name: str, encoding: str = 'latin1') -> List[Dict]:
        """
        Carrega uma tabela DBF e converte para lista de dicionários
        
        Args:
            table_name: Nome da tabela (ex: 'S_PACBO.DBF')
            encoding: Encoding do arquivo
            
        Returns:
            Lista de registros da tabela
        """
        table_path = os.path.join(self.dbf_path, table_name)
        
        if not os.path.exists(table_path):
            logger.warning(f"Tabela {table_name} não encontrada em {table_path}")
            return []
        
        try:
            logger.info(f"Carregando tabela {table_name}...")
            table = DBF(table_path, encoding=encoding)
            records = list(iter(table))
            logger.info(f"Tabela {table_name} carregada: {len(records)} registros")
            return records
            
        except Exception as e:
            logger.error(f"Erro ao carregar tabela {table_name}: {e}")
            return []
    
    def _save_cache(self, cache_key: str, data: Dict):
        """Salva dados no cache"""
        cache_file = self._get_cache_file(cache_key)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Cache salvo: {cache_key}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache {cache_key}: {e}")
    
    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """Carrega dados do cache"""
        cache_file = self._get_cache_file(cache_key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verifica se o cache não está muito antigo (1 hora)
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if (datetime.now() - cache_time).total_seconds() > 3600:
                logger.info(f"Cache {cache_key} expirado")
                return None
            
            logger.info(f"Cache carregado: {cache_key}")
            return cache_data['data']
            
        except Exception as e:
            logger.error(f"Erro ao carregar cache {cache_key}: {e}")
            return None
    
    def get_cbo_procedimentos_relations(self) -> Dict[str, List[str]]:
        """
        Obtém a relação completa CBO -> Lista de Procedimentos
        
        Returns:
            Dict onde key=CBO e value=lista de códigos de procedimentos
        """
        # Verifica cache em memória
        if self._cbo_procedimentos_cache and self._cache_timestamp:
            cache_age = (datetime.now() - self._cache_timestamp).total_seconds()
            if cache_age < 3600:  # 1 hora
                logger.info("Usando cache em memória para CBO/Procedimentos")
                return self._cbo_procedimentos_cache
        
        # Verifica cache em disco
        cached_data = self._load_cache('cbo_procedimentos')
        if cached_data:
            self._cbo_procedimentos_cache = cached_data
            self._cache_timestamp = datetime.now()
            return cached_data
        
        logger.info("Carregando relação CBO/Procedimentos dos DBFs...")
        
        # Carrega tabela S_PACBO.DBF
        pacbo_records = self._load_dbf_table('S_PACBO.DBF')
        
        if not pacbo_records:
            logger.error("Não foi possível carregar S_PACBO.DBF")
            return {}
        
        # Constrói o dicionário CBO -> Procedimentos
        cbo_procedimentos = {}
        
        for record in pacbo_records:
            cbo = record.get('PACBO_CBO', '').strip()
            procedimento = record.get('PACBO_PA', '').strip()
            
            if cbo and procedimento:
                if cbo not in cbo_procedimentos:
                    cbo_procedimentos[cbo] = []
                
                if procedimento not in cbo_procedimentos[cbo]:
                    cbo_procedimentos[cbo].append(procedimento)
        
        # Ordena as listas de procedimentos
        for cbo in cbo_procedimentos:
            cbo_procedimentos[cbo].sort()
        
        logger.info(f"Relação CBO/Procedimentos carregada: {len(cbo_procedimentos)} CBOs")
        
        # Salva no cache
        self._save_cache('cbo_procedimentos', cbo_procedimentos)
        self._cbo_procedimentos_cache = cbo_procedimentos
        self._cache_timestamp = datetime.now()
        
        return cbo_procedimentos
    
    def get_procedimentos_info(self) -> Dict[str, Dict[str, str]]:
        """
        Obtém informações detalhadas dos procedimentos
        
        Returns:
            Dict onde key=código procedimento e value=dict com informações
        """
        # Verifica cache
        if self._procedimentos_cache:
            return self._procedimentos_cache
        
        cached_data = self._load_cache('procedimentos_info')
        if cached_data:
            self._procedimentos_cache = cached_data
            return cached_data
        
        logger.info("Carregando informações dos procedimentos...")
        
        # Carrega tabelas
        pa_records = self._load_dbf_table('S_PA.DBF')
        proced_records = self._load_dbf_table('S_PROCED.DBF')
        
        procedimentos_info = {}
        
        # Processa S_PA.DBF (mais detalhado)
        for record in pa_records:
            codigo = record.get('PA_ID', '').strip()
            if codigo:
                procedimentos_info[codigo] = {
                    'codigo': codigo,
                    'descricao': record.get('PA_DC', '').strip(),
                    'complexidade': record.get('PA_CPX', '').strip(),
                    'classificacao': record.get('PA_CTF', '').strip(),
                    'exige_cbo': record.get('PA_EXIGCBO', 'N').strip(),
                    'valor_sh': float(record.get('PA_SH', 0) or 0),
                    'valor_sp': float(record.get('PA_SP', 0) or 0),
                    'valor_sa': float(record.get('PA_SA', 0) or 0),
                    'fonte': 'S_PA'
                }
        
        # Complementa com S_PROCED.DBF
        for record in proced_records:
            codigo = record.get('PA_ID', '').strip()
            if codigo and codigo not in procedimentos_info:
                procedimentos_info[codigo] = {
                    'codigo': codigo,
                    'descricao': record.get('PA_DC', '').strip(),
                    'complexidade': record.get('PA_CPX', '').strip(),
                    'classificacao': record.get('PA_CTF', '').strip(),
                    'exige_cbo': 'S',  # Assume que exige CBO se está em PROCED
                    'valor_sh': float(record.get('PA_SH', 0) or 0),
                    'valor_sp': float(record.get('PA_SP', 0) or 0),
                    'valor_sa': float(record.get('PA_SA', 0) or 0),
                    'fonte': 'S_PROCED'
                }
        
        logger.info(f"Informações dos procedimentos carregadas: {len(procedimentos_info)} procedimentos")
        
        # Salva no cache
        self._save_cache('procedimentos_info', procedimentos_info)
        self._procedimentos_cache = procedimentos_info
        
        return procedimentos_info
    
    def get_cbos_for_procedimento(self, codigo_procedimento: str) -> List[str]:
        """
        Obtém lista de CBOs que podem executar um procedimento específico
        
        Args:
            codigo_procedimento: Código do procedimento
            
        Returns:
            Lista de códigos CBO
        """
        cbo_procedimentos = self.get_cbo_procedimentos_relations()
        
        cbos_permitidos = []
        for cbo, procedimentos in cbo_procedimentos.items():
            if codigo_procedimento in procedimentos:
                cbos_permitidos.append(cbo)
        
        return sorted(cbos_permitidos)
    
    def get_procedimentos_for_cbo(self, codigo_cbo: str) -> List[str]:
        """
        Obtém lista de procedimentos que um CBO pode executar
        
        Args:
            codigo_cbo: Código do CBO
            
        Returns:
            Lista de códigos de procedimentos
        """
        cbo_procedimentos = self.get_cbo_procedimentos_relations()
        return cbo_procedimentos.get(codigo_cbo, [])
    
    def validate_cbo_procedimento(self, codigo_cbo: str, codigo_procedimento: str) -> bool:
        """
        Valida se um CBO pode executar um procedimento
        
        Args:
            codigo_cbo: Código do CBO
            codigo_procedimento: Código do procedimento
            
        Returns:
            True se o CBO pode executar o procedimento
        """
        procedimentos_permitidos = self.get_procedimentos_for_cbo(codigo_cbo)
        return codigo_procedimento in procedimentos_permitidos
    
    def clear_cache(self):
        """Limpa todos os caches"""
        self._cbo_procedimentos_cache = None
        self._procedimentos_cache = None
        self._cache_timestamp = None
        
        # Remove arquivos de cache
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('_cache.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("Cache limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
    
    def refresh_data(self):
        """Força atualização dos dados dos DBFs"""
        logger.info("Atualizando dados dos DBFs...")
        self.clear_cache()
        
        # Recarrega os dados
        self.get_cbo_procedimentos_relations()
        self.get_procedimentos_info()
        
        logger.info("Dados dos DBFs atualizados com sucesso")
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Obtém estatísticas dos dados carregados
        
        Returns:
            Dict com estatísticas
        """
        cbo_proc = self.get_cbo_procedimentos_relations()
        proc_info = self.get_procedimentos_info()
        
        total_relacoes = sum(len(procs) for procs in cbo_proc.values())
        
        return {
            'total_cbos': len(cbo_proc),
            'total_procedimentos': len(proc_info),
            'total_relacoes': total_relacoes,
            'media_procedimentos_por_cbo': round(total_relacoes / len(cbo_proc) if cbo_proc else 0, 2)
        }
    
    def get_all_cbos(self) -> List[Dict[str, str]]:
        """
        Obtém todos os CBOs únicos dos DBFs
        
        Returns:
            Lista com código e descrição de todos os CBOs
        """
        # Primeiro, obtém todos os CBOs das relações CBO-Procedimento
        cbo_relations = self.get_cbo_procedimentos_relations()
        cbos_set = set(cbo_relations.keys())
        
        # Carrega descrições do CBO da tabela oficial (S_CD.DBT ou similar)
        cbo_descricoes = self._get_cbo_descriptions()
        
        cbos_list = []
        for cbo_codigo in sorted(cbos_set):
            cbos_list.append({
                'codigo': cbo_codigo,
                'descricao': cbo_descricoes.get(cbo_codigo, f'CBO {cbo_codigo}'),
                'total_procedimentos': len(cbo_relations.get(cbo_codigo, []))
            })
        
        return cbos_list
    
    def _get_cbo_descriptions(self) -> Dict[str, str]:
        """
        Carrega descrições dos CBOs da tabela CBO do Ministério do Trabalho
        """
        # Tenta carregar do cache
        cached = self._load_cache('cbo_descriptions')
        if cached:
            return cached
        
        cbo_descricoes = {}
        
        # Tenta tabela específica de CBO (pode variar)
        try:
            # Verifica se há arquivo de CBO nos DBFs
            cbo_tables = ['S_CDN.DBF', 'S_CD.DBF', 'CBO.DBF']
            for table in cbo_tables:
                table_path = os.path.join(self.dbf_path, table)
                if os.path.exists(table_path):
                    try:
                        t = DBF(table_path, encoding='latin1')
                        for r in t:
                            # Formato varia conforme tabela
                            codigo = r.get('CDN_IT', r.get('CBO', r.get('CODIGO', ''))).strip()
                            descr = r.get('CDN_DSCR', r.get('DESCRICAO', r.get('NOME', ''))).strip()
                            if codigo and len(codigo) == 6 and codigo.isdigit():
                                cbo_descricoes[codigo] = descr
                    except Exception as e:
                        logger.debug(f"Erro ao carregar {table}: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Não foi possível carregar descrições do CBO: {e}")
        
        # Se não encontrou descrições, usa tabela interna básica
        if not cbo_descricoes:
            cbo_descricoes = self._get_cbo_hardcoded_descriptions()
        
        # Salva no cache
        self._save_cache('cbo_descriptions', cbo_descricoes)
        
        return cbo_descricoes
    
    def _get_cbo_hardcoded_descriptions(self) -> Dict[str, str]:
        """
        Descrições básicas de CBOs comuns na saúde
        """
        return {
            '225142': 'CIRURGIAO DENTISTA - CLINICO GERAL',
            '225125': 'MEDICO CLINICO',
            '225170': 'MEDICO PSIQUIATRA',
            '223505': 'ENFERMEIRO',
            '223565': 'ENFERMEIRO PSIQUIATRA',
            '223810': 'FISIOTERAPEUTA GERAL',
            '223905': 'FONOAUDIOLOGO',
            '225275': 'MEDICO EM MEDICINA DE FAMILIA E COMUNIDADE',
            '239415': 'PSICOLOGO CLINICO',
            '239425': 'PSICOLOGO SOCIAL',
            '251510': 'ASSISTENTE SOCIAL',
            '223605': 'NUTRICIONISTA',
            '322205': 'TECNICO DE ENFERMAGEM',
            '322245': 'AUXILIAR DE ENFERMAGEM',
            '515105': 'AGENTE COMUNITARIO DE SAUDE',
            '225133': 'MEDICO NEUROLOGISTA',
            '225175': 'MEDICO CARDIOLOGISTA',
            '225130': 'MEDICO PEDIATRA',
            '225135': 'MEDICO GINECOLOGISTA E OBSTETRA',
            '225140': 'MEDICO CIRURGIAO GERAL',
            '225105': 'MEDICO ACUPUNTURISTA',
            '225305': 'MEDICO LEGISTA',
            '351505': 'TECNICO EM FARMACIA',
            '226305': 'TERAPEUTA OCUPACIONAL',
            '515120': 'AGENTE DE COMBATE AS ENDEMIAS',
            '223710': 'FARMACEUTICO',
        }
    
    def search_cbos(self, query: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        Busca CBOs por código ou descrição
        
        Args:
            query: Texto para buscar (código ou descrição)
            limit: Número máximo de resultados
            
        Returns:
            Lista de CBOs correspondentes à busca
        """
        all_cbos = self.get_all_cbos()
        query_lower = query.lower().strip()
        
        if not query_lower:
            return all_cbos[:limit]
        
        # Filtra por código ou descrição
        matches = []
        for cbo in all_cbos:
            if (query_lower in cbo['codigo'].lower() or 
                query_lower in cbo['descricao'].lower()):
                matches.append(cbo)
                if len(matches) >= limit:
                    break
        
        return matches


# Singleton instance
_dbf_manager_instance = None

def get_dbf_manager_instance() -> DBFManagerService:
    """Obtém instância singleton do DBFManagerService"""
    global _dbf_manager_instance
    if _dbf_manager_instance is None:
        _dbf_manager_instance = DBFManagerService()
    return _dbf_manager_instance