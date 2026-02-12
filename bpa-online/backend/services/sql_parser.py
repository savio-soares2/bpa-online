import os
import re
from typing import List, Dict, Any
from datetime import datetime
from models.schemas import CNESInfo

class SQLParser:
    """Parser para arquivos SQL de teste"""
    
    def __init__(self):
        self.sql_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'BPA-main',
            'arquivos_sql'
        )
    
    def get_available_cnes(self) -> List[CNESInfo]:
        """Retorna lista de CNES disponíveis nos arquivos SQL"""
        cnes_dict = {}
        
        # Procura por arquivos SQL
        if os.path.exists(self.sql_dir):
            for filename in os.listdir(self.sql_dir):
                if filename.endswith('.sql') and filename != 'lista_procedimentos_excluir.sql' and filename != 'procedimento BPA-C.sql':
                    filepath = os.path.join(self.sql_dir, filename)
                    
                    # Extrai CNES do nome do arquivo (ex: 2025116061478.sql -> 6061478)
                    # Formato: YYYYMMCNES.sql
                    match = re.search(r'(\d{6})(\d+)\.sql', filename)
                    if match:
                        competencia = match.group(1)  # YYYYMM
                        cnes = match.group(2)  # CNES
                        
                        # Formata competência
                        comp_formatted = f"{competencia[:4]}-{competencia[4:]}"
                        
                        if cnes not in cnes_dict:
                            cnes_dict[cnes] = {
                                'cnes': cnes,
                                'competencias': [],
                                'total_registros': 0
                            }
                        
                        cnes_dict[cnes]['competencias'].append(comp_formatted)
                        
                        # Conta registros no arquivo
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                inserts = content.count('INSERT INTO')
                                cnes_dict[cnes]['total_registros'] += inserts
                        except Exception as e:
                            print(f"Erro ao ler {filename}: {e}")
        
        # Converte para lista de CNESInfo
        result = []
        for cnes_data in cnes_dict.values():
            result.append(CNESInfo(
                cnes=cnes_data['cnes'],
                nome=f"Unidade {cnes_data['cnes']}",
                total_registros=cnes_data['total_registros'],
                competencias=sorted(cnes_data['competencias']),
                ultima_atualizacao=datetime.now().isoformat()
            ))
        
        return sorted(result, key=lambda x: x.cnes)
    
    def get_cnes_stats(self, cnes: str) -> Dict[str, Any]:
        """Retorna estatísticas de um CNES específico"""
        stats = {
            'cnes': cnes,
            'total_registros': 0,
            'competencias': [],
            'procedimentos_unicos': 0,
            'pacientes_unicos': 0
        }
        
        # Procura arquivos deste CNES
        if os.path.exists(self.sql_dir):
            for filename in os.listdir(self.sql_dir):
                if cnes in filename and filename.endswith('.sql'):
                    filepath = os.path.join(self.sql_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Conta registros
                            inserts = content.count('INSERT INTO')
                            stats['total_registros'] += inserts
                            
                            # Extrai competência
                            match = re.search(r'(\d{6})', filename)
                            if match:
                                comp = match.group(1)
                                comp_formatted = f"{comp[:4]}-{comp[4:]}"
                                if comp_formatted not in stats['competencias']:
                                    stats['competencias'].append(comp_formatted)
                    except Exception as e:
                        print(f"Erro ao processar {filename}: {e}")
        
        stats['competencias'] = sorted(stats['competencias'])
        return stats
    
    def parse_sql_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Parse de arquivo SQL para extrair dados estruturados"""
        records = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Regex para capturar INSERT statements
            pattern = r"INSERT INTO S_PRD \((.*?)\)\s*VALUES \((.*?)\);"
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                columns = [col.strip() for col in match.group(1).split(',')]
                values = match.group(2)
                
                # Parse valores (simplificado)
                value_list = []
                in_string = False
                current_value = ""
                
                for char in values:
                    if char == "'" and (not current_value or current_value[-1] != '\\'):
                        in_string = not in_string
                        current_value += char
                    elif char == ',' and not in_string:
                        value_list.append(current_value.strip())
                        current_value = ""
                    else:
                        current_value += char
                
                if current_value:
                    value_list.append(current_value.strip())
                
                # Cria dicionário
                record = {}
                for i, col in enumerate(columns):
                    if i < len(value_list):
                        val = value_list[i].strip()
                        # Remove aspas
                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1]
                        if val.upper() == 'NULL':
                            val = None
                        record[col.lower()] = val
                
                records.append(record)
        
        except Exception as e:
            print(f"Erro ao fazer parse de {filepath}: {e}")
        
        return records
    
    def get_records_by_cnes_competencia(self, cnes: str, competencia: str) -> List[Dict[str, Any]]:
        """Retorna registros de um CNES e competência específicos"""
        # Formata nome do arquivo
        comp_num = competencia.replace('-', '')  # 2025-11 -> 202511
        filename = f"{comp_num}{cnes}.sql"
        filepath = os.path.join(self.sql_dir, filename)
        
        if os.path.exists(filepath):
            return self.parse_sql_file(filepath)
        
        return []
