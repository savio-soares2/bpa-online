"""
SIGTAP Parser - Extrai dados das tabelas SIGTAP (formato fixed-width)
"""
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ColumnLayout:
    """Define o layout de uma coluna em arquivo fixed-width"""
    name: str
    size: int
    start: int  # 1-based position
    end: int    # 1-based position
    type: str


class SigtapParser:
    """Parser para arquivos SIGTAP em formato fixed-width"""
    
    def __init__(self, sigtap_dir: str):
        """
        Args:
            sigtap_dir: Caminho para o diretório com os arquivos SIGTAP
        """
        self.sigtap_dir = Path(sigtap_dir)
        
        # Caches para evitar re-parsing (grande melhoria de performance)
        self._procedimentos_cache = None
        self._valores_cache = None
        self._ocupacoes_cache = None
        self._servicos_cache = None
        self._registros_cache = None
        self._rel_ocupacao_cache = None
        self._rel_servico_cache = None
        self._rel_registro_cache = None
        
    def read_layout(self, layout_file: str) -> List[ColumnLayout]:
        """
        Lê o arquivo de layout (CSV) e retorna a estrutura das colunas
        
        Args:
            layout_file: Nome do arquivo de layout (ex: 'tb_procedimento_layout.txt')
            
        Returns:
            Lista de ColumnLayout
        """
        layout_path = self.sigtap_dir / layout_file
        columns = []
        
        # Tentar UTF-8 primeiro, fallback para Latin-1 se falhar
        # (resolve problemas com caracteres acentuados em alguns arquivos)
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(layout_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        columns.append(ColumnLayout(
                            name=row['Coluna'],
                            size=int(row['Tamanho']),
                            start=int(row['Inicio']),
                            end=int(row['Fim']),
                            type=row['Tipo']
                        ))
                return columns
            except UnicodeDecodeError:
                columns = []  # Reset para próxima tentativa
                continue
        
        # Se nenhum encoding funcionar, relança o erro
        raise UnicodeDecodeError(f"Não foi possível decodificar {layout_path} com nenhum encoding suportado")
    
    def parse_fixed_width_line(self, line: str, layout: List[ColumnLayout]) -> Dict[str, str]:
        """
        Extrai os dados de uma linha usando o layout especificado
        
        Args:
            line: Linha do arquivo
            layout: Layout das colunas
            
        Returns:
            Dicionário com os valores extraídos
        """
        row = {}
        for col in layout:
            # Posições são 1-based, Python é 0-based
            value = line[col.start-1:col.end].strip()
            row[col.name] = value
        
        return row
    
    def parse_file(self, data_file: str, layout_file: str) -> List[Dict[str, str]]:
        """
        Faz o parsing completo de um arquivo SIGTAP
        
        Args:
            data_file: Nome do arquivo de dados (ex: 'tb_procedimento.txt')
            layout_file: Nome do arquivo de layout (ex: 'tb_procedimento_layout.txt')
            
        Returns:
            Lista de dicionários com os dados
        """
        layout = self.read_layout(layout_file)
        data_path = self.sigtap_dir / data_file
        
        records = []
        # SIGTAP usa encoding Latin-1 (ISO-8859-1), não UTF-8
        with open(data_path, 'r', encoding='latin-1') as f:
            for line in f:
                if line.strip():
                    record = self.parse_fixed_width_line(line, layout)
                    records.append(record)
        
        return records
    
    def parse_procedimentos(self) -> List[Dict[str, str]]:
        """Parse da tabela de procedimentos (com cache)"""
        if self._procedimentos_cache is None:
            self._procedimentos_cache = self.parse_file('tb_procedimento.txt', 'tb_procedimento_layout.txt')
        return self._procedimentos_cache
    
    def parse_ocupacoes(self) -> List[Dict[str, str]]:
        """Parse da tabela de ocupações (CBO)"""
        if self._ocupacoes_cache is None:
            self._ocupacoes_cache = self.parse_file('tb_ocupacao.txt', 'tb_ocupacao_layout.txt')
        return self._ocupacoes_cache
    
    def parse_servicos(self) -> List[Dict[str, str]]:
        """Parse da tabela de serviços/classificações"""
        if self._servicos_cache is None:
            self._servicos_cache = self.parse_file('tb_servico.txt', 'tb_servico_layout.txt')
        return self._servicos_cache
    
    def parse_registros(self) -> List[Dict[str, str]]:
        """Parse da tabela de instrumentos de registro (BPA-C, BPA-I, etc)"""
        if self._registros_cache is None:
            self._registros_cache = self.parse_file('tb_registro.txt', 'tb_registro_layout.txt')
        return self._registros_cache
    
    def parse_procedimento_ocupacao(self) -> List[Dict[str, str]]:
        """Parse da relação procedimento x ocupação (CBO)"""
        if self._rel_ocupacao_cache is None:
            self._rel_ocupacao_cache = self.parse_file('rl_procedimento_ocupacao.txt', 'rl_procedimento_ocupacao_layout.txt')
        return self._rel_ocupacao_cache
    
    def parse_procedimento_servico(self) -> List[Dict[str, str]]:
        """Parse da relação procedimento x serviço"""
        if self._rel_servico_cache is None:
            self._rel_servico_cache = self.parse_file('rl_procedimento_servico.txt', 'rl_procedimento_servico_layout.txt')
        return self._rel_servico_cache
    
    def parse_procedimento_registro(self) -> List[Dict[str, str]]:
        """Parse da relação procedimento x instrumento de registro"""
        if self._rel_registro_cache is None:
            self._rel_registro_cache = self.parse_file('rl_procedimento_registro.txt', 'rl_procedimento_registro_layout.txt')
        return self._rel_registro_cache
    
    def get_procedimentos_by_tipo_registro(self, tipo_registro: str = '02') -> List[str]:
        """
        Retorna lista de códigos de procedimentos para um tipo de registro
        
        Args:
            tipo_registro: Código do tipo de registro
                          '01' = BPA-C (Consolidado)
                          '02' = BPA-I (Individualizado)
                          '10' = e-SUS APS
                          
        Returns:
            Lista de códigos de procedimentos
        """
        registros = self.parse_procedimento_registro()
        return [
            r['CO_PROCEDIMENTO'] 
            for r in registros 
            if r['CO_REGISTRO'] == tipo_registro
        ]
    
    def get_procedimentos_by_cbo(self, cbo: str) -> List[str]:
        """
        Retorna lista de códigos de procedimentos permitidos para um CBO
        
        Args:
            cbo: Código CBO (6 dígitos)
            
        Returns:
            Lista de códigos de procedimentos
        """
        relacoes = self.parse_procedimento_ocupacao()
        return [
            r['CO_PROCEDIMENTO']
            for r in relacoes
            if r['CO_OCUPACAO'] == cbo
        ]
    
    def get_procedimentos_by_servico(self, servico: str, classificacao: str = None) -> List[str]:
        """
        Retorna lista de códigos de procedimentos permitidos para um tipo de serviço
        
        Args:
            servico: Código do serviço (3 dígitos) - ex: '115' para CAPS
            classificacao: Código da classificação (3 dígitos) - opcional
            
        Returns:
            Lista de códigos de procedimentos
        """
        relacoes = self.parse_procedimento_servico()
        
        if classificacao:
            return [
                r['CO_PROCEDIMENTO']
                for r in relacoes
                if r['CO_SERVICO'] == servico and r['CO_CLASSIFICACAO'] == classificacao
            ]
        else:
            return [
                r['CO_PROCEDIMENTO']
                for r in relacoes
                if r['CO_SERVICO'] == servico
            ]
    
    def get_procedimentos_by_servicos(self, servicos: List[str], classificacoes: List[str] = None) -> set:
        """
        Retorna conjunto de procedimentos para múltiplos serviços/classificações
        
        Args:
            servicos: Lista de códigos de serviço (ex: ['115', '114'])
            classificacoes: Lista de classificações (opcional)
            
        Returns:
            Set de códigos de procedimentos
        """
        if not servicos:
            return set()
        
        codigos = set()
        relacoes = self.parse_procedimento_servico()
        
        for rel in relacoes:
            if rel['CO_SERVICO'] in servicos:
                if classificacoes is None or rel['CO_CLASSIFICACAO'] in classificacoes:
                    codigos.add(rel['CO_PROCEDIMENTO'])
        
        return codigos
    
    def get_procedimentos_ambulatoriais(self) -> set:
        """
        Retorna conjunto de procedimentos que têm valor ambulatorial (VL_SA > 0)
        
        Estes são os únicos procedimentos válidos para BPA, já que é um sistema
        exclusivamente ambulatorial. Procedimentos com apenas valor hospitalar
        serão rejeitados (glozados) pelo SIA.
        
        Returns:
            Set de códigos de procedimentos com VL_SA > 0
        """
        # Garante que o cache de valores está preenchido
        if self._valores_cache is None:
            self.get_procedimento_valor("0000000000")  # Força inicialização do cache
        
        return {
            codigo for codigo, valores in self._valores_cache.items()
            if valores.get('valor_sa', 0) > 0
        }
    
    def get_procedimentos_filtered(
        self, 
        tipo_registro: str = None,
        cbo: str = None, 
        servico: str = None
    ) -> List[Dict[str, str]]:
        """
        Retorna procedimentos filtrados por múltiplos critérios (AND)
        
        Args:
            tipo_registro: Código do tipo de registro ('01'=BPA-C, '02'=BPA-I)
            cbo: Código CBO (6 dígitos)
            servico: Código do serviço (3 dígitos)
            
        Returns:
            Lista de dicionários com dados dos procedimentos filtrados
        """
        # Buscar códigos permitidos para cada filtro
        codigos_permitidos = None
        
        if tipo_registro:
            codigos = set(self.get_procedimentos_by_tipo_registro(tipo_registro))
            codigos_permitidos = codigos if codigos_permitidos is None else codigos_permitidos & codigos
        
        if cbo:
            codigos = set(self.get_procedimentos_by_cbo(cbo))
            codigos_permitidos = codigos if codigos_permitidos is None else codigos_permitidos & codigos
        
        if servico:
            codigos = set(self.get_procedimentos_by_servico(servico))
            codigos_permitidos = codigos if codigos_permitidos is None else codigos_permitidos & codigos
        
        # Se nenhum filtro foi aplicado, retorna tudo
        if codigos_permitidos is None:
            return self.parse_procedimentos()
        
        # Buscar dados completos dos procedimentos permitidos
        todos_procedimentos = self.parse_procedimentos()
        return [
            p for p in todos_procedimentos
            if p['CO_PROCEDIMENTO'] in codigos_permitidos
        ]
    
    def get_procedimento_valor(self, codigo_procedimento: str) -> Dict[str, float]:
        """
        Retorna os valores financeiros de um procedimento (com cache)
        
        Os valores no SIGTAP estão em CENTAVOS (inteiro), então dividimos por 100.
        
        Args:
            codigo_procedimento: Código do procedimento (10 dígitos)
            
        Returns:
            Dict com valores em REAIS: {
                'valor_ambulatorio': float,  # VL_SA (Serviço Ambulatorial) / 100
                'valor_hospitalar': float,   # VL_SH (Serviço Hospitalar) / 100
                'valor_sa': float,           # VL_SA / 100 (alias)
                'valor_sp': float            # VL_SP (Serviço Profissional) / 100
            }
        """
        # Inicializa cache de valores na primeira chamada
        if self._valores_cache is None:
            self._valores_cache = {}
            procedimentos = self.parse_procedimentos()
            
            def parse_valor_centavos(val_str: str) -> float:
                """Converte valor em centavos (string) para reais (float)"""
                if not val_str or val_str.strip() == '':
                    return 0.0
                val_clean = val_str.strip()
                try:
                    # Valores estão em centavos como inteiro (ex: 000000001247 = R$ 12,47)
                    centavos = int(val_clean)
                    return centavos / 100.0
                except ValueError:
                    return 0.0
            
            for proc in procedimentos:
                cod = proc['CO_PROCEDIMENTO']
                vl_sh = parse_valor_centavos(proc.get('VL_SH', '0'))
                vl_sa = parse_valor_centavos(proc.get('VL_SA', '0'))
                vl_sp = parse_valor_centavos(proc.get('VL_SP', '0'))
                
                self._valores_cache[cod] = {
                    'valor_ambulatorio': vl_sa,  # VL_SA é o valor ambulatorial
                    'valor_hospitalar': vl_sh,   # VL_SH é o valor hospitalar
                    'valor_sa': vl_sa,
                    'valor_sp': vl_sp
                }
        
        # Retorna do cache ou zeros se não encontrar
        return self._valores_cache.get(codigo_procedimento, {
            'valor_ambulatorio': 0.0,
            'valor_hospitalar': 0.0,
            'valor_sa': 0.0,
            'valor_sp': 0.0
        })


# Exemplo de uso
if __name__ == '__main__':
    parser = SigtapParser(r'C:\Users\60612427358\Documents\bpa-online\bpa-online\BPA-main\TabelaUnificada_202512_v2601161858')
    
    # Teste 1: Procedimentos BPA-I
    print("=== PROCEDIMENTOS BPA-I (amostra) ===")
    proc_bpai = parser.get_procedimentos_by_tipo_registro('02')
    print(f"Total: {len(proc_bpai)}")
    print("Primeiros 5:", proc_bpai[:5])
    
    # Teste 2: Procedimentos BPA-C
    print("\n=== PROCEDIMENTOS BPA-C (amostra) ===")
    proc_bpac = parser.get_procedimentos_by_tipo_registro('01')
    print(f"Total: {len(proc_bpac)}")
    print("Primeiros 5:", proc_bpac[:5])
    
    # Teste 3: Procedimentos filtrados (BPA-I + CBO específico)
    print("\n=== PROCEDIMENTOS COM FILTROS MÚLTIPLOS ===")
    # Exemplo: BPA-I para médico clínico (CBO 225125)
    proc_filtrados = parser.get_procedimentos_filtered(
        tipo_registro='02',
        cbo='225125'
    )
    print(f"Total com filtros: {len(proc_filtrados)}")
    if proc_filtrados:
        print(f"Exemplo: {proc_filtrados[0]['CO_PROCEDIMENTO']} - {proc_filtrados[0]['NO_PROCEDIMENTO']}")
