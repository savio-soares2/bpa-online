"""
Gerador de arquivo SQL para exportação para Firebird
Gera arquivo .sql com INSERTs para importar no Firebird local
Inclui correções automáticas baseadas nos scripts SQL do BPA-main
"""
import os
import unicodedata
import re
from datetime import datetime
from typing import List, Dict, Optional
from database import BPADatabase
from services.corrections import BPACorrections
from constants.estabelecimentos import get_nome_estabelecimento


def remove_accents(text: str) -> str:
    """Remove acentos de uma string para compatibilidade com latin-1"""
    if not text:
        return text
    # Normaliza para NFD (separa caracteres de acentos)
    # Remove caracteres de combinação (acentos)
    normalized = unicodedata.normalize('NFD', str(text))
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


class FirebirdExporter:
    """Exporta dados para arquivo SQL compatível com Firebird"""
    
    # Mapeamento de campos do banco (prd_*) para formato snake_case
    FIELD_MAP_BPAI = {
        'prd_uid': 'cnes',
        'prd_cmp': 'competencia',
        'prd_cnsmed': 'cns_profissional',
        'prd_cbo': 'cbo',
        'prd_flh': 'folha',
        'prd_seq': 'sequencia',
        'prd_pa': 'procedimento',
        'prd_cnspac': 'cns_paciente',
        'prd_nmpac': 'nome_paciente',
        'prd_dtnasc': 'data_nascimento',
        'prd_sexo': 'sexo',
        'prd_raca': 'raca_cor',
        'prd_nac': 'nacionalidade',
        'prd_ibge': 'municipio_ibge',
        'prd_dtaten': 'data_atendimento',
        'prd_qt_p': 'quantidade',
        'prd_cid': 'cid',
        'prd_caten': 'carater_atendimento',
        'prd_naut': 'numero_autorizacao',
        'prd_ine': 'ine',
        'prd_servico': 'servico',
        'prd_classificacao': 'classificacao',
        'prd_cep_pcnte': 'cep',
        'prd_lograd_pcnte': 'logradouro_codigo',
        'prd_end_pcnte': 'endereco',
        'prd_num_pcnte': 'numero',
        'prd_compl_pcnte': 'complemento',
        'prd_bairro_pcnte': 'bairro',
        'prd_ddtel_pcnte': 'ddd_telefone',
        'prd_tel_pcnte': 'telefone',
        'prd_email_pcnte': 'email',
    }
    
    FIELD_MAP_BPAC = {
        'prd_uid': 'cnes',
        'prd_cmp': 'competencia',
        'prd_cnsmed': 'cns_profissional',
        'prd_cbo': 'cbo',
        'prd_flh': 'folha',
        'prd_seq': 'sequencia',
        'prd_pa': 'procedimento',
        'prd_idade': 'idade',
        'prd_qt_p': 'quantidade',
    }
    
    def __init__(self, output_dir: str = None, cnes: str = None):
        self.db = BPADatabase()
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), 'exports')
        self.cnes = cnes
        self.corrections = BPACorrections(cnes)
        
        # Cria diretório de exportação se não existir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_unit_name(self, cnes: str) -> str:
        """Busca sigla da unidade nos constantes"""
        try:
            # Se não tiver CNES, retorna UNIDADE
            if not cnes:
                return "UNIDADE"

            # Busca nome/sigla do estabelecimento
            name = get_nome_estabelecimento(cnes)
            
            if name:
                # Sanitiza nome (apenas letras, números e guarda underscores)
                # Remove acentos
                name = remove_accents(name)
                # Substitui espaços e chars especiais
                clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
                # Remove underscores duplicados
                clean_name = re.sub(r'_+', '_', clean_name)
                # Remove underscores do início/fim
                clean_name = clean_name.strip('_')
                return clean_name[:30].upper() # Limita tamanho e uppercase
                
            return "UNIDADE"
        except Exception as e:
            print(f"Erro ao buscar nome unidade: {e}")
            return "UNIDADE"
    
    def map_record(self, record: Dict, field_map: Dict) -> Dict:
        """Converte campos do banco (prd_*) para formato snake_case"""
        mapped = {'id': record.get('id')}  # Preserva o ID
        for db_field, snake_field in field_map.items():
            if db_field in record:
                mapped[snake_field] = record[db_field]
        return mapped
    
    def format_date(self, date_str: str) -> str:
        """Formata data para Firebird (DD.MM.YYYY)"""
        if not date_str:
            return 'NULL'
        
        try:
            # Tenta diferentes formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y']:
                try:
                    dt = datetime.strptime(str(date_str)[:10], fmt)
                    return f"'{dt.strftime('%d.%m.%Y')}'"
                except:
                    continue
            return 'NULL'
        except:
            return 'NULL'
    
    def format_string(self, value: str, max_length: int = None) -> str:
        """Formata string para SQL"""
        if value is None:
            return 'NULL'
        
        # Remove aspas simples (escape)
        value = str(value).replace("'", "''").strip()
        
        # Trunca se necessário
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return f"'{value}'"
    
    def format_number(self, value) -> str:
        """Formata número para SQL"""
        if value is None:
            return 'NULL'
        return str(value)
    
    def generate_sql_header(self, f, cnes: str, competencia: str, 
                           tipo: str, total: int, correction_stats: dict = None,
                           bpai_count: int = 0, bpac_count: int = 0):
        """
        Gera o cabeçalho SQL completo com todos objetos necessários
        Inclui: Generator, Trigger e instruções
        """
        # Cabeçalho informativo (sem acentos para compatibilidade latin-1)
        f.write(f"-- ============================================================\n")
        f.write(f"-- BPA Online - Exportacao {tipo}\n")
        f.write(f"-- ============================================================\n")
        f.write(f"-- CNES: {cnes}\n")
        f.write(f"-- Competencia: {competencia}\n")
        f.write(f"-- Data de exportacao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        if tipo == 'COMPLETO':
            f.write(f"-- BPA-I: {bpai_count} registros\n")
            f.write(f"-- BPA-C: {bpac_count} registros\n")
        
        f.write(f"-- Total de registros: {total}\n")
        
        # Estatísticas de correção (usa remove_accents para compatibilidade)
        if correction_stats:
            f.write(f"-- \n")
            f.write(f"-- === CORRECOES APLICADAS AUTOMATICAMENTE ===\n")
            f.write(f"-- Registros originais: {correction_stats.get('total_input', 0)}\n")
            f.write(f"-- Registros excluidos: {correction_stats.get('deleted', 0)}\n")
            f.write(f"-- Registros corrigidos: {correction_stats.get('corrected', 0)}\n")
            
            if correction_stats.get('delete_reasons'):
                f.write(f"-- \n")
                f.write(f"-- Motivos de exclusao:\n")
                for reason, count in correction_stats['delete_reasons'].items():
                    f.write(f"--   - {remove_accents(reason)}: {count}\n")
            
            if correction_stats.get('correction_types'):
                f.write(f"-- \n")
                f.write(f"-- Correcoes aplicadas:\n")
                for ctype, count in correction_stats['correction_types'].items():
                    f.write(f"--   - {remove_accents(ctype)}: {count}\n")
        
        f.write(f"-- \n")
        f.write(f"-- ============================================================\n")
        f.write(f"-- ESTE SCRIPT ESTA PRONTO PARA EXECUCAO\n")
        f.write(f"-- Basta importar no Firebird - todos os objetos serao criados\n")
        f.write(f"-- ============================================================\n\n")
        
        # Delimitador para Firebird
        f.write("SET TERM ^ ;\n\n")
        
        # ========== GENERATOR ==========
        f.write("-- ============================================================\n")
        f.write("-- CRIACAO DO GENERATOR (Sequencia para IDs)\n")
        f.write("-- ============================================================\n")
        f.write("EXECUTE BLOCK AS\n")
        f.write("BEGIN\n")
        f.write("  IF (NOT EXISTS(SELECT 1 FROM RDB$GENERATORS WHERE RDB$GENERATOR_NAME = 'GEN_S_PRD_ID')) THEN\n")
        f.write("  BEGIN\n")
        f.write("    EXECUTE STATEMENT 'CREATE GENERATOR GEN_S_PRD_ID';\n")
        f.write("    EXECUTE STATEMENT 'SET GENERATOR GEN_S_PRD_ID TO 0';\n")
        f.write("  END\n")
        f.write("END^\n\n")
        
        # ========== TRIGGER ==========
        f.write("-- ============================================================\n")
        f.write("-- CRIACAO DA TRIGGER (Atribui ID automaticamente)\n")
        f.write("-- ============================================================\n")
        f.write("CREATE OR ALTER TRIGGER BI_S_PRD_ID FOR S_PRD\n")
        f.write("ACTIVE BEFORE INSERT POSITION 0\n")
        f.write("AS\n")
        f.write("BEGIN\n")
        f.write("  IF (NEW.PRD_ID IS NULL) THEN\n")
        f.write("    NEW.PRD_ID = GEN_ID(GEN_S_PRD_ID, 1);\n")
        f.write("END^\n\n")
        
        f.write("-- ============================================================\n")
        f.write("-- INICIO DOS REGISTROS\n")
        f.write("-- ============================================================\n\n")
    
    def generate_bpai_insert(self, record: Dict) -> str:
        """Gera INSERT para um registro BPA-I"""
        
        # Campos do S_PRD para BPA-I
        # PRD_ID será atribuído automaticamente pela TRIGGER BI_S_PRD_ID
        sql = f"""INSERT INTO S_PRD (
    PRD_UID, PRD_CMP, PRD_CNSMED, PRD_CBO, PRD_FLH, PRD_SEQ, PRD_PA,
    PRD_CNSPAC, PRD_NMPAC, PRD_DTNASC, PRD_SEXO, PRD_RACA,
    PRD_NAC, PRD_IBGE, PRD_DTATEN, PRD_QT_P, PRD_CID,
    PRD_CATEN, PRD_NAUT, PRD_INE, PRD_ORG, PRD_MVM,
    PRD_CEP_PCNTE, PRD_LOGRAD_PCNTE, PRD_END_PCNTE, PRD_NUM_PCNTE, PRD_COMPL_PCNTE,
    PRD_BAIRRO_PCNTE, PRD_DDTEL_PCNTE, PRD_TEL_PCNTE, PRD_EMAIL_PCNTE,
    PRD_SERVICO, PRD_CLASSIFICACAO,
    PRD_FLPA, PRD_FLCBO, PRD_FLCA, PRD_FLIDA, PRD_FLQT, PRD_FLER, PRD_FLMUN, PRD_FLCID
) VALUES (
    {self.format_string(record.get('cnes'), 7)},
    {self.format_string(record.get('competencia'), 6)},
    {self.format_string(record.get('cns_profissional'), 15)},
    {self.format_string(record.get('cbo'), 6)},
    {self.format_string(record.get('folha', '001'), 3)},
    {self.format_string(record.get('sequencia', '01'), 2)},
    {self.format_string(record.get('procedimento'), 10)},
    {self.format_string(record.get('cns_paciente'), 15)},
    {self.format_string(record.get('nome_paciente'), 30)},
    {self.format_string(record.get('data_nascimento'), 8)},
    {self.format_string(record.get('sexo'), 1)},
    {self.format_string(record.get('raca_cor'), 2)},
    {self.format_string(record.get('nacionalidade', '010'), 3)},
    {self.format_string(record.get('municipio_ibge'), 6)},
    {self.format_string(record.get('data_atendimento'), 8)},
    {self.format_number(record.get('quantidade', 1))},
    {self.format_string(record.get('cid'), 4) if record.get('cid') else 'NULL'},
    {self.format_string(record.get('carater_atendimento', '01'), 2)},
    {self.format_string(record.get('numero_autorizacao'), 13) if record.get('numero_autorizacao') else 'NULL'},
    {self.format_string(record.get('ine'), 10) if record.get('ine') else 'NULL'},
    'BPI',
    {self.format_string(record.get('competencia'), 6)},
    {self.format_string(record.get('cep'), 8) if record.get('cep') else 'NULL'},
    {self.format_string(record.get('logradouro_codigo'), 3) if record.get('logradouro_codigo') else 'NULL'},
    {self.format_string(record.get('endereco'), 30) if record.get('endereco') else 'NULL'},
    {self.format_string(record.get('numero'), 5) if record.get('numero') else 'NULL'},
    {self.format_string(record.get('complemento'), 10) if record.get('complemento') else 'NULL'},
    {self.format_string(record.get('bairro'), 30) if record.get('bairro') else 'NULL'},
    {self.format_string(record.get('ddd_telefone'), 2) if record.get('ddd_telefone') else 'NULL'},
    {self.format_string(record.get('telefone'), 9) if record.get('telefone') else 'NULL'},
    {self.format_string(record.get('email'), 40) if record.get('email') else 'NULL'},
    {self.format_string(record.get('servico'), 3) if record.get('servico') else 'NULL'},
    {self.format_string(record.get('classificacao'), 3) if record.get('classificacao') else 'NULL'},
    '0', '0', '0', '0', '0', '0', '0', '0'
);"""
        return sql
    
    def generate_bpac_insert(self, record: Dict) -> str:
        """Gera INSERT para um registro BPA-C (Consolidado)"""
        
        # PRD_ID será atribuído automaticamente pela TRIGGER BI_S_PRD_ID
        sql = f"""INSERT INTO S_PRD (
    PRD_UID, PRD_CMP, PRD_CNSMED, PRD_CBO, PRD_FLH, PRD_SEQ, PRD_PA,
    PRD_IDADE, PRD_QT_P, PRD_ORG, PRD_MVM,
    PRD_FLPA, PRD_FLCBO, PRD_FLCA, PRD_FLIDA, PRD_FLQT, PRD_FLER, PRD_FLMUN, PRD_FLCID
) VALUES (
    {self.format_string(record.get('cnes'), 7)},
    {self.format_string(record.get('competencia'), 6)},
    {self.format_string(record.get('cns_profissional'), 15) if record.get('cns_profissional') else "''"},
    {self.format_string(record.get('cbo'), 6)},
    {self.format_string(record.get('folha', '001'), 3)},
    {self.format_string(record.get('sequencia', '01'), 2)},
    {self.format_string(record.get('procedimento'), 10)},
    {self.format_string(record.get('idade', '999'), 3)},
    {self.format_number(record.get('quantidade', 1))},
    'BPA',
    {self.format_string(record.get('competencia'), 6)},
    '0', '0', '0', '0', '0', '0', '0', '0'
);"""
        return sql
    
    def export_bpai(self, cnes: str, competencia: str, 
                    apenas_nao_exportados: bool = True,
                    aplicar_correcoes: bool = True) -> Dict:
        """
        Exporta BPA-I para arquivo SQL
        
        Args:
            cnes: Código CNES
            competencia: Competência (YYYYMM)
            apenas_nao_exportados: Se True, exporta apenas registros não exportados
            aplicar_correcoes: Se True, aplica correções automáticas
        
        Returns:
            Dict com status, caminho do arquivo e estatísticas
        """
        
        # Atualiza correções com o CNES atual
        self.corrections = BPACorrections(cnes)
        
        # Busca registros
        exportado_filter = False if apenas_nao_exportados else None
        print(f"[EXPORT] Buscando BPA-I: cnes={cnes}, comp={competencia}, apenas_nao_exportados={apenas_nao_exportados}, exportado_filter={exportado_filter}")
        raw_records = self.db.list_bpa_individualizado(cnes, competencia, exportado_filter)
        print(f"[EXPORT] Encontrados {len(raw_records) if raw_records else 0} registros brutos")
        
        if not raw_records:
            return {
                'status': 'warning',
                'message': 'Nenhum registro encontrado para exportação',
                'total': 0,
                'filename': None
            }
        
        # Mapeia campos do banco para formato snake_case
        records = [self.map_record(r, self.FIELD_MAP_BPAI) for r in raw_records]
        
        # Aplica correções se habilitado
        correction_stats = None
        if aplicar_correcoes:
            print(f"[EXPORT] Aplicando correções em {len(records)} registros...")
            records, correction_stats = self.corrections.process_batch(records, 'BPI')
            print(f"[EXPORT] Após correções: {len(records)} registros restantes")
            if correction_stats:
                print(f"[EXPORT] Stats: corrigidos={correction_stats.get('corrected', 0)}, excluídos={correction_stats.get('deleted', 0)}")
                if correction_stats.get('delete_reasons'):
                    for reason, count in correction_stats['delete_reasons'].items():
                        print(f"[EXPORT]   - {reason}: {count}")
            
            if not records:
                return {
                    'status': 'warning',
                    'message': 'Todos os registros foram excluídos após correções',
                    'total': 0,
                    'filename': None,
                    'correction_stats': correction_stats
                }
        
        # Aplica sequenciamento (folha/sequência)
        records = self.corrections.assign_sequence_bpi(records)
        
        # Gera arquivo SQL
        unit_name = self.get_unit_name(cnes)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'BPA_I_{cnes}_{unit_name}_{competencia}_{timestamp}.sql'
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='latin-1') as f:
            # Cabeçalho completo com Generator e Trigger
            self.generate_sql_header(f, cnes, competencia, 'BPA-I', len(records), correction_stats)
            
            # INSERTs
            for i, record in enumerate(records, 1):
                f.write(f"-- Registro {i}/{len(records)}\n")
                f.write(self.generate_bpai_insert(record))
                f.write("\n\n")
            
            # Finaliza
            f.write("SET TERM ; ^\n")
            f.write("\nCOMMIT;\n")
            f.write(f"\n-- ============================================================\n")
            f.write(f"-- FIM DA EXPORTACAO: {len(records)} registros importados\n")
            f.write(f"-- ============================================================\n")
        
        # Marca registros como exportados
        ids = [r['id'] for r in records if 'id' in r]
        if ids:
            self.db.mark_exported_bpai(ids)
        
        result = {
            'status': 'success',
            'message': f'Exportados {len(records)} registros',
            'total': len(records),
            'filename': filename,
            'filepath': filepath
        }
        
        if correction_stats:
            result['correction_stats'] = correction_stats
            result['message'] = f"Exportados {len(records)} registros ({correction_stats['corrected']} corrigidos, {correction_stats['deleted']} excluídos)"
        
        return result
    
    def export_bpac(self, cnes: str, competencia: str,
                    aplicar_correcoes: bool = True) -> Dict:
        """Exporta BPA-C para arquivo SQL"""
        
        # Atualiza correções com o CNES atual
        self.corrections = BPACorrections(cnes)
        
        raw_records = self.db.list_bpa_consolidado(cnes, competencia)
        
        if not raw_records:
            return {
                'status': 'warning',
                'message': 'Nenhum registro BPA-C encontrado',
                'total': 0,
                'filename': None
            }
        
        # Mapeia campos do banco para formato snake_case
        records = [self.map_record(r, self.FIELD_MAP_BPAC) for r in raw_records]
        
        unit_name = self.get_unit_name(cnes)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'BPA_C_{cnes}_{unit_name}_{competencia}_{timestamp}.sql'
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='latin-1') as f:
            f.write(f"-- BPA Consolidado - Exportacao\n")
            f.write(f"-- CNES: {cnes}\n")
            f.write(f"-- Competencia: {competencia}\n")
            f.write(f"-- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"-- Total: {len(records)}\n\n")
            
            f.write("SET TERM ^ ;\n\n")
            
            for i, record in enumerate(records, 1):
                f.write(f"-- Registro {i}\n")
                f.write(self.generate_bpac_insert(record))
                f.write("\n\n")
            
            f.write("SET TERM ; ^\n")
            f.write("\nCOMMIT;\n")
        
        return {
            'status': 'success',
            'message': f'Exportados {len(records)} registros BPA-C',
            'total': len(records),
            'filename': filename,
            'filepath': filepath
        }
    
    def export_all(self, cnes: str, competencia: str,
                   aplicar_correcoes: bool = True) -> Dict:
        """Exporta BPA-I e BPA-C em um único arquivo com correções"""
        
        # Atualiza correções com o CNES atual
        self.corrections = BPACorrections(cnes)
        
        raw_bpai = self.db.list_bpa_individualizado(cnes, competencia, False)
        raw_bpac = self.db.list_bpa_consolidado(cnes, competencia)
        
        # Mapeia campos do banco para formato snake_case
        bpai_records = [self.map_record(r, self.FIELD_MAP_BPAI) for r in raw_bpai] if raw_bpai else []
        bpac_records = [self.map_record(r, self.FIELD_MAP_BPAC) for r in raw_bpac] if raw_bpac else []
        
        # Aplica correções aos registros
        bpai_stats = None
        bpac_stats = None
        
        if aplicar_correcoes:
            if bpai_records:
                bpai_records, bpai_stats = self.corrections.process_batch(bpai_records, 'BPI')
            if bpac_records:
                bpac_records, bpac_stats = self.corrections.process_batch(bpac_records, 'BPA')
        
        # Aplica sequenciamento (folha/sequência)
        if bpai_records:
            bpai_records = self.corrections.assign_sequence_bpi(bpai_records)
        if bpac_records:
            bpac_records = self.corrections.assign_sequence_bpa(bpac_records)
        
        total = len(bpai_records) + len(bpac_records)
        
        if total == 0:
            return {
                'status': 'warning',
                'message': 'Nenhum registro encontrado',
                'total': 0,
                'filename': None
            }
        
        unit_name = self.get_unit_name(cnes)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'BPA_COMPLETO_{cnes}_{unit_name}_{competencia}_{timestamp}.sql'
        filepath = os.path.join(self.output_dir, filename)
        
        # Combina estatísticas para o header
        combined_stats = None
        if bpai_stats or bpac_stats:
            combined_stats = {
                'total_input': (bpai_stats.get('total_input', 0) if bpai_stats else 0) + 
                               (bpac_stats.get('total_input', 0) if bpac_stats else 0),
                'deleted': (bpai_stats.get('deleted', 0) if bpai_stats else 0) + 
                           (bpac_stats.get('deleted', 0) if bpac_stats else 0),
                'corrected': (bpai_stats.get('corrected', 0) if bpai_stats else 0) + 
                             (bpac_stats.get('corrected', 0) if bpac_stats else 0),
                'delete_reasons': {},
                'correction_types': {}
            }
            # Combina motivos de exclusão
            for stats in [bpai_stats, bpac_stats]:
                if stats and stats.get('delete_reasons'):
                    for reason, count in stats['delete_reasons'].items():
                        combined_stats['delete_reasons'][reason] = combined_stats['delete_reasons'].get(reason, 0) + count
                if stats and stats.get('correction_types'):
                    for ctype, count in stats['correction_types'].items():
                        combined_stats['correction_types'][ctype] = combined_stats['correction_types'].get(ctype, 0) + count
        
        with open(filepath, 'w', encoding='latin-1') as f:
            # Cabeçalho completo com Generator e Trigger
            self.generate_sql_header(f, cnes, competencia, 'COMPLETO', total, combined_stats,
                                    bpai_count=len(bpai_records), bpac_count=len(bpac_records))
            
            # BPA-I
            if bpai_records:
                f.write("-- ========== BPA INDIVIDUALIZADO ==========\n\n")
                for i, record in enumerate(bpai_records, 1):
                    f.write(f"-- BPA-I #{i}\n")
                    f.write(self.generate_bpai_insert(record))
                    f.write("\n\n")
            
            # BPA-C
            if bpac_records:
                f.write("-- ========== BPA CONSOLIDADO ==========\n\n")
                for i, record in enumerate(bpac_records, 1):
                    f.write(f"-- BPA-C #{i}\n")
                    f.write(self.generate_bpac_insert(record))
                    f.write("\n\n")
            
            # Footer
            f.write("SET TERM ; ^\n\n")
            f.write("-- ============================================================\n")
            f.write(f"-- RESUMO DA IMPORTACAO\n")
            f.write("-- ============================================================\n")
            f.write(f"-- Total de registros: {total}\n")
            f.write(f"--   - BPA-I: {len(bpai_records)}\n")
            f.write(f"--   - BPA-C: {len(bpac_records)}\n")
            f.write("-- \n")
            f.write("-- IMPORTANTE: Execute este script no Firebird com:\n")
            f.write("-- isql -u SYSDBA -p masterkey BPAMAG.GDB < arquivo.sql\n")
            f.write("-- ============================================================\n\n")
            f.write("COMMIT;\n")
        
        # Marca BPA-I como exportados
        if bpai_records:
            ids = [r['id'] for r in bpai_records if 'id' in r]
            if ids:
                self.db.mark_exported_bpai(ids)
        
        result = {
            'status': 'success',
            'message': f'Exportados {len(bpai_records)} BPA-I + {len(bpac_records)} BPA-C',
            'total': total,
            'bpai_count': len(bpai_records),
            'bpac_count': len(bpac_records),
            'filename': filename,
            'filepath': filepath
        }
        
        if bpai_stats:
            result['bpai_stats'] = bpai_stats
        if bpac_stats:
            result['bpac_stats'] = bpac_stats
        
        return result
    
    def list_exports(self) -> List[Dict]:
        """Lista arquivos de exportação disponíveis"""
        exports = []
        
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.sql'):
                    filepath = os.path.join(self.output_dir, filename)
                    stat = os.stat(filepath)
                    
                    # Extrai informações do nome do arquivo
                    # Formato: BPA_I_CNES_COMPETENCIA_TIMESTAMP.sql ou BPA_C_... ou BPA_COMPLETO_...
                    parts = filename.replace('.sql', '').split('_')
                    
                    cnes = ''
                    competencia = ''
                    tipo = 'BPA'
                    
                    if len(parts) >= 6:
                        # Lógica robusta: pega competência do fim (antepenúltimo, antes de data e hora)
                        # Funciona para ambos os formatos:
                        # Antigo: BPA, I, CNES, COMP, DATE, TIME
                        # Novo:   BPA, I, CNES, UNIT..., COMP, DATE, TIME
                        
                        try:
                            competencia = parts[-3]
                            # Valida formato básica (YYYYMM)
                            if not (len(competencia) == 6 and competencia.isdigit()):
                                # Fallback para lógica antiga se algo estiver estranho
                                if len(parts) == 6:
                                    competencia = parts[3]
                            
                            type_code = parts[1]
                            cnes = parts[2]
                            
                            if type_code == 'I':
                                tipo = 'BPA-I'
                            elif type_code == 'C':
                                tipo = 'BPA-C'
                            elif type_code == 'COMPLETO':
                                tipo = 'COMPLETO'
                        except:
                            pass
                    
                    # Conta registros (INSERTs) no arquivo
                    total_registros = 0
                    try:
                        with open(filepath, 'r', encoding='latin-1') as f:
                            content = f.read()
                            total_registros = content.count('INSERT INTO')
                    except:
                        pass
                    
                    exports.append({
                        'arquivo': filename,
                        'cnes': cnes,
                        'competencia': competencia,
                        'tipo': tipo,
                        'total_registros': total_registros,
                        'data_exportacao': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        # Campos extras para compatibilidade
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'filepath': filepath
                    })
        
        # Ordena por data (mais recente primeiro)
        exports.sort(key=lambda x: x['data_exportacao'], reverse=True)
        return exports


# Instância global
exporter = FirebirdExporter()
