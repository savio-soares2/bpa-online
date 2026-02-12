"""
Gerador de Relatórios BPA - Clona funcionalidade do BPA usando DBFs + dados da produção

Este módulo gera os relatórios TXT no mesmo formato do software BPA oficial,
usando:
- Dados de produção do Firebird (S_PRD) ou direto do e-SUS
- Parâmetros dos arquivos DBF (S_PA, S_PROCED, S_CID, etc.)
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dbfread import DBF
import firebirdsql
from dataclasses import dataclass


@dataclass
class DBFConfig:
    """Configuração dos caminhos dos DBFs"""
    dbf_path: str = r"C:\Users\60612427358\Documents\bpa-online\bpa-online\BPA-main\RELATORIOS"


class DBFReader:
    """Leitor de arquivos DBF para parâmetros do BPA"""
    
    def __init__(self, dbf_path: str):
        self.dbf_path = dbf_path
        self._cache = {}
    
    def _load_dbf(self, filename: str) -> List[Dict]:
        """Carrega DBF e cacheia"""
        if filename not in self._cache:
            path = os.path.join(self.dbf_path, filename)
            if os.path.exists(path):
                table = DBF(path, encoding='latin-1')
                self._cache[filename] = [dict(rec) for rec in table]
            else:
                self._cache[filename] = []
        return self._cache[filename]
    
    def get_procedimento(self, pa_cod: str) -> Optional[Dict]:
        """Busca dados de um procedimento pelo código (sem DV)"""
        if not pa_cod:
            return None
        # Remove hífen e DV se existir (ex: 03.01.01.004-8 -> 030101004)
        pa_id = pa_cod.replace('.', '').replace('-', '')[:9]
        
        records = self._load_dbf('S_PA.DBF')
        for rec in records:
            if rec.get('PA_ID') == pa_id:
                return rec
        return None
    
    def get_procedimento_valor(self, pa_cod: str) -> float:
        """Retorna valor (PA_TOTAL) de um procedimento"""
        if not pa_cod:
            return 0.0
        proc = self.get_procedimento(pa_cod)
        if proc:
            return proc.get('PA_TOTAL', 0.0)
        return 0.0
    
    def get_municipio(self, ibge: str) -> Optional[Dict]:
        """Busca município pelo código IBGE"""
        records = self._load_dbf('CADMUN.DBF')
        for rec in records:
            # IBGE no DBF é UF+MUNIC (ex: 172100 -> UF=17, MUNIC=2100)
            cod = rec.get('CODUF', '') + rec.get('CODMUNIC', '').lstrip('0').zfill(4)
            if cod == ibge:
                return rec
        return None
    
    def get_cid(self, cid_cod: str) -> Optional[Dict]:
        """Busca CID pelo código"""
        records = self._load_dbf('S_CID.DBF')
        for rec in records:
            if rec.get('CD_COD') == cid_cod:
                return rec
        return None


class BPAReportGenerator:
    """Gerador de relatórios BPA no formato TXT"""
    
    VERSION = "04.10"
    LINES_PER_PAGE = 19  # Registros por página (cada registro = 2 linhas)
    
    MESES = {
        '01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR',
        '05': 'MAI', '06': 'JUN', '07': 'JUL', '08': 'AGO',
        '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'
    }
    
    def __init__(self, dbf_path: str):
        self.dbf_reader = DBFReader(dbf_path)
    
    def format_date(self, date_str: str) -> str:
        """Formata data de YYYYMMDD para DD/MM/YYYY"""
        if not date_str or len(date_str) != 8:
            return '          '
        return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
    
    def format_competencia(self, comp: str) -> str:
        """Formata competência de YYYYMM para MM/YYYY"""
        if not comp or len(comp) != 6:
            return '       '
        return f"{comp[4:6]}/{comp[0:4]}"
    
    def format_competencia_header(self, comp: str) -> str:
        """Formata competência de YYYYMM para MES/YYYY (ex: NOV/2025)"""
        if not comp or len(comp) != 6:
            return '        '
        mes = self.MESES.get(comp[4:6], comp[4:6])
        return f"{mes}/{comp[0:4]}"
    
    def format_procedimento(self, pa_cod: str) -> str:
        """Formata código do procedimento (ex: 0301010048 -> 03.01.01.004-8)"""
        if not pa_cod or len(pa_cod) < 10:
            return (pa_cod or '').ljust(14)
        
        # Formato: GG.SS.TT.PPP-D
        return f"{pa_cod[0:2]}.{pa_cod[2:4]}.{pa_cod[4:6]}.{pa_cod[6:9]}-{pa_cod[9]}"
    
    def format_valor(self, valor: float) -> str:
        """Formata valor com vírgula decimal (padrão brasileiro)"""
        return f"{valor:5.2f}".replace('.', ',')
    
    def get_situacao(self, record: Dict) -> str:
        """Determina situação do registro baseado nos flags"""
        flags = ['PRD_FLPA', 'PRD_FLCBO', 'PRD_FLCA', 'PRD_FLIDA', 
                 'PRD_FLQT', 'PRD_FLER', 'PRD_FLMUN', 'PRD_FLCID']
        
        for flag in flags:
            if record.get(flag, '0') != '0':
                return 'Com Erros'
        return 'Sem Erros'
    
    def generate_header(self, page_num: int, comp_display: str) -> str:
        """Gera cabeçalho da página"""
        today = datetime.now().strftime('%d/%m/%Y')
        
        header = f"""
    Folha:{page_num:4d}******************************************************Versao: {self.VERSION}
    MS/SAS/DATASUS/BPA  SISTEMA DE INFORMACOES AMBULATORIAIS             Data Comp
    {today}           RELATORIO DE BPA INDIVIDUALIZADO                {comp_display}
    *******************************************************************************
"""
        return header
    
    def generate_profissional_header(self, cnes: str, cns_prof: str, cbo: str, comp: str, folha: int) -> str:
        """Gera cabeçalho do profissional"""
        cns_prof = cns_prof or ''
        cbo = cbo or ''
        return f"""
    CNES  : {cnes}
    
    CNS PROFISSIONAL {cns_prof}  CBO : {cbo}
    
    COMPETENCIA : {self.format_competencia(comp)} FOLHA : {folha:03d}
    
    SQ CNS PACIENTE/NOME  DT.NASC SEXO RACA MUNIC. DT.ATEND.  PROCEDIMENTO   QTD. CID. CA.       PREVIA SITUACAO
"""
    
    def generate_record_line(self, seq: int, record: Dict) -> str:
        """Gera linha do registro no formato idêntico ao original do BPA"""
        # Busca valor do procedimento
        pa_cod = record.get('PRD_PA') or ''
        valor = self.dbf_reader.get_procedimento_valor(pa_cod)
        
        # Formata campos - trata None em todos
        # Formato exato baseado na análise do BPAI_REL.TXT original:
        # "    01 700501926845056 03/03/1976 M    01  172100 21/11/2025 02.14.01.005-8     1  065 02          1,00 Sem Erros"
        #                                                                                     QTD CID CA
        
        cns = (record.get('PRD_CNSPAC') or '').ljust(15)[:15]
        dtnasc = self.format_date(record.get('PRD_DTNASC') or '')
        sexo = (record.get('PRD_SEXO') or ' ')[0:1]
        raca = (record.get('PRD_RACA') or '').zfill(2)[:2]
        ibge = (record.get('PRD_IBGE') or '').ljust(6)[:6]
        dtaten = self.format_date(record.get('PRD_DTATEN') or '')
        proc = self.format_procedimento(pa_cod).ljust(14)[:14]
        qtd = int(record.get('PRD_QT_P') or 0)
        cid = (record.get('PRD_CID') or '').ljust(3)[:3]  # CID - 3 caracteres
        caten = (record.get('PRD_CATEN') or '').zfill(2)[:2]
        situacao = self.get_situacao(record)
        nome = (record.get('PRD_NMPAC') or '').ljust(30)[:30]
        valor_fmt = self.format_valor(valor)
        
        # Linha 1: dados do registro
        # indent(4) + SQ(2) + sp(1) + CNS(15) + sp(1) + DTNASC(10) + sp(1) + SEXO(1) + sp(4) + RACA(2) + sp(2) + IBGE(6) + sp(1) + DTATEN(10) + sp(1) + PROC(14) + sp(5) + QTD(1) + sp(2) + CID(3) + sp(1) + CATEN(2) + sp(10) + VALOR(4) + sp(1) + SIT
        line1 = f"    {seq:02d} {cns} {dtnasc} {sexo}    {raca}  {ibge} {dtaten} {proc}     {qtd}  {cid} {caten}         {valor_fmt} {situacao}"
        
        # Linha 2: nome (7 espaços + nome)
        line2 = f"       {nome}"
        
        return f"{line1}\n{line2}\n"
    
    def generate_footer(self) -> str:
        """Gera rodapé de formalização"""
        return """
    FORMALIZACAO ----------- Valores sujeitos a criticas/alteração pelo gestor -
    RESP.UNIDADE :           RESP.GESTOR MUNICIPAL :      RESP.GESTOR ESTADUAL :
    Carimbo     Rubrica      Carimbo     Rubrica          Carimbo     Rubrica   
    Data:___/___/___         Data:___/___/___             Data:___/___/___      
"""
    
    def generate_bpai_report(self, records: List[Dict], cnes: str, competencia: str) -> str:
        """Gera relatório BPA-I completo no formato idêntico ao original"""
        output = []
        page_num = 1
        records_on_page = 0
        
        # Agrupa por profissional
        by_professional = {}
        for rec in records:
            if rec.get('PRD_ORG') == 'BPI':  # Apenas BPA Individualizado
                key = (rec.get('PRD_CNSMED') or '', rec.get('PRD_CBO') or '')
                if key not in by_professional:
                    by_professional[key] = []
                by_professional[key].append(rec)
        
        # Formato da competência: NOV/2025
        comp_display = self.format_competencia_header(competencia)
        
        for (cns_prof, cbo), prof_records in by_professional.items():
            # Primeiro cabeçalho do profissional
            output.append(self.generate_header(page_num, comp_display))
            output.append(self.generate_profissional_header(cnes, cns_prof, cbo, competencia, 1))
            records_on_page = 0
            
            # Registros - sequencial sempre "1" como no original
            for rec in prof_records:
                # Verifica se precisa quebrar página
                if records_on_page >= self.LINES_PER_PAGE:
                    output.append(self.generate_footer())
                    page_num += 1
                    output.append(self.generate_header(page_num, comp_display))
                    records_on_page = 0
                
                # Sequencial sempre 1 como no original
                output.append(self.generate_record_line(1, rec))
                records_on_page += 1
        
        output.append(self.generate_footer())
        
        return ''.join(output)


class FirebirdDataSource:
    """Fonte de dados do Firebird"""
    
    def __init__(self, host='localhost', port=3050, database=r'C:\BPA\BPAMAG.GDB',
                 user='SYSDBA', password='masterkey'):
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'charset': 'UTF8'
        }
    
    def get_records(self, cnes: str, competencia: str) -> List[Dict]:
        """Busca registros de produção do Firebird"""
        conn = firebirdsql.connect(**self.config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM S_PRD 
            WHERE PRD_UID = ? AND PRD_CMP = ?
            ORDER BY PRD_CNSMED, PRD_PA, PRD_DTATEN
        """, (cnes, competencia))
        
        cols = [d[0] for d in cursor.description]
        records = [dict(zip(cols, row)) for row in cursor.fetchall()]
        
        conn.close()
        return records


def generate_report(cnes: str, competencia: str, output_path: str = None) -> str:
    """
    Função principal para gerar relatório BPA-I
    
    Args:
        cnes: Código CNES do estabelecimento
        competencia: Competência no formato YYYYMM
        output_path: Caminho para salvar o arquivo (opcional)
    
    Returns:
        Conteúdo do relatório
    """
    # Configura fontes
    dbf_path = r"C:\Users\60612427358\Documents\bpa-online\bpa-online\BPA-main\RELATORIOS"
    
    # Busca dados
    data_source = FirebirdDataSource()
    records = data_source.get_records(cnes, competencia)
    
    # Gera relatório
    generator = BPAReportGenerator(dbf_path)
    report = generator.generate_bpai_report(records, cnes, competencia)
    
    # Salva se especificado
    if output_path:
        with open(output_path, 'w', encoding='latin-1') as f:
            f.write(report)
        print(f"Relatório salvo em: {output_path}")
    
    return report


if __name__ == '__main__':
    # Teste
    report = generate_report('6061478', '202511', 'BPAI_TESTE.TXT')
    print("Relatório gerado!")
    print(report[:2000])  # Primeiras linhas
