"""
Gerador de Relatórios BPA - Gera os 4 arquivos do BPA Magnético

Este módulo gera os arquivos de exportação no mesmo formato do software BPA oficial:
1. PACAPSAD.SET - Arquivo de remessa (dados de produção)
2. RELEXP.PRN - Relatório de controle de remessa
3. BPAI_REL.TXT - Relatório de BPA Individualizado
4. BPAC_REL.TXT - Relatório de BPA Consolidado

Layout baseado na análise do BPA v04.10
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Mapeamento de meses
MESES = {
    '01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR',
    '05': 'MAI', '06': 'JUN', '07': 'JUL', '08': 'AGO',
    '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'
}

MESES_EXT = {
    '01': 'JANEIRO', '02': 'FEVEREIRO', '03': 'MARÇO', '04': 'ABRIL',
    '05': 'MAIO', '06': 'JUNHO', '07': 'JULHO', '08': 'AGOSTO',
    '09': 'SETEMBRO', '10': 'OUTUBRO', '11': 'NOVEMBRO', '12': 'DEZEMBRO'
}


@dataclass
class BPAExportConfig:
    """Configuração para exportação BPA"""
    cnes: str
    competencia: str  # YYYYMM
    sigla: str = "CAPSAD"  # Sigla do estabelecimento
    ibge_municipio: str = ""  # Código IBGE do município (usado como fallback)
    versao_sistema: str = "04.10"
    versao_banco: str = ""  # Será preenchido com competencia


class BPAFileGenerator:
    """Gerador de arquivos BPA Magnético"""
    
    VERSION = "04.10"
    
    def __init__(self, config: BPAExportConfig, db_connection=None, sigtap_parser=None):
        self.config = config
        self.db = db_connection
        self.sigtap_parser = sigtap_parser
        self.config.versao_banco = f"{config.competencia}a"
        self._valores_cache = {}  # Cache de valores de procedimentos
    
    def format_date_yyyymmdd(self, date_str: str) -> str:
        """Converte data de vários formatos para YYYYMMDD"""
        if not date_str:
            return "        "
        
        date_str = str(date_str)[:10]
        
        # Se já está no formato YYYYMMDD
        if len(date_str) == 8 and date_str.isdigit():
            return date_str
        
        # Tenta YYYY-MM-DD
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y%m%d')
        except:
            pass
        
        # Tenta DD/MM/YYYY
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%Y%m%d')
        except:
            pass
        
        return "        "
    
    def format_date_display(self, date_str: str) -> str:
        """Formata data para exibição DD/MM/YYYY"""
        yyyymmdd = self.format_date_yyyymmdd(date_str)
        if len(yyyymmdd) == 8:
            return f"{yyyymmdd[6:8]}/{yyyymmdd[4:6]}/{yyyymmdd[0:4]}"
        return "  /  /    "
    
    def format_competencia_display(self, comp: str) -> str:
        """Formata competência de YYYYMM para MES/YYYY (ex: SET/2025)"""
        if not comp or len(comp) != 6:
            return "        "
        mes = MESES.get(comp[4:6], comp[4:6])
        return f"{mes}/{comp[0:4]}"
    
    def pad_left(self, value: str, size: int, char: str = '0') -> str:
        """Preenche à esquerda"""
        return str(value or '').zfill(size)[:size]
    
    def pad_right(self, value: str, size: int, char: str = ' ') -> str:
        """Preenche à direita"""
        return str(value or '').ljust(size, char)[:size]
    
    def _get_valor_procedimento(self, codigo_procedimento: str, quantidade: int = 1) -> str:
        """
        Obtém o valor do procedimento via SIGTAP e formata para exibição.
        Retorna o valor unitário * quantidade, formatado como "X.XXX,XX"
        """
        if not codigo_procedimento:
            return "0,00"
        
        # Normaliza código (remove formatação se houver)
        codigo = codigo_procedimento.replace('.', '').replace('-', '').strip()[:10]
        
        # Verifica cache
        if codigo in self._valores_cache:
            valor_unit = self._valores_cache[codigo]
        elif self.sigtap_parser:
            try:
                valores = self.sigtap_parser.get_procedimento_valor(codigo)
                # Usa valor ambulatorial (VL_SA)
                valor_unit = valores.get('valor_ambulatorio', 0.0) or valores.get('valor_sa', 0.0) or 0.0
                self._valores_cache[codigo] = valor_unit
            except Exception as e:
                logger.warning(f"Erro ao obter valor do procedimento {codigo}: {e}")
                valor_unit = 0.0
                self._valores_cache[codigo] = valor_unit
        else:
            # Sem parser SIGTAP, retorna 0
            valor_unit = 0.0
        
        # Calcula valor total (unitário * quantidade)
        valor_total = valor_unit * quantidade
        
        # Formata como "X,XX" (padrão brasileiro) - alinhado à direita em 13 chars
        # Ex: 1234.56 -> "1.234,56"
        if valor_total >= 1000:
            valor_str = f"{valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            valor_str = f"{valor_total:.2f}".replace(".", ",")
        
        # Alinha à direita em 13 caracteres (padrão do BPA oficial)
        return valor_str.rjust(13)
    
    def calculate_age(self, birth_date: str, ref_date: str = None) -> int:
        """Calcula idade"""
        try:
            birth = self.format_date_yyyymmdd(birth_date)
            if len(birth) != 8:
                return 0
            
            ref = ref_date or datetime.now().strftime('%Y%m%d')
            if isinstance(ref, str) and len(ref) == 8:
                ref_year = int(ref[:4])
                ref_month = int(ref[4:6])
                ref_day = int(ref[6:8])
            else:
                ref_year = datetime.now().year
                ref_month = datetime.now().month
                ref_day = datetime.now().day
            
            birth_year = int(birth[:4])
            birth_month = int(birth[4:6])
            birth_day = int(birth[6:8])
            
            age = ref_year - birth_year
            if (ref_month, ref_day) < (birth_month, birth_day):
                age -= 1
            
            return max(0, min(999, age))
        except:
            return 0
    
    # ==========================================================================
    # GERADOR: PACAPSAD.SET - Arquivo de Remessa
    # ==========================================================================
    
    def generate_set_header(self, total_registros: int, total_bpas: int, campo_controle: str) -> str:
        """
        Gera linha de cabeçalho (tipo 01) do arquivo .SET
        
        Layout:
        01#BPA#2025090004520000181112                                    00000000000000                                         D04.10
        """
        linha = ""
        linha += "01"  # Tipo registro (pos 1-2)
        linha += "#BPA#"  # Indicador (pos 3-7)
        linha += self.config.competencia  # Competência YYYYMM (pos 8-13)
        linha += self.pad_left(str(total_registros), 6)  # Total registros (pos 14-19)
        linha += self.pad_left(str(total_bpas), 6)  # Total BPAs (pos 20-25)
        linha += self.pad_left(campo_controle, 4)  # Campo controle (pos 26-29)
        linha += " " * 52  # Espaços reservados (pos 30-81)
        linha += "0" * 14  # Zeros (pos 82-95)
        linha += " " * 41  # Espaços (pos 96-136)
        linha += "D" + self.VERSION  # Versão (pos 137-142)
        
        return linha
    
    def generate_set_bpac_line(self, record: Dict, folha: int, seq: int) -> str:
        """
        Gera linha BPA-C (tipo 02) do arquivo .SET
        
        Layout (46 caracteres):
        02 CNES(7) COMP(6) CBO(6) FOLHA(3) SEQ(2) PROC(10) IDADE(3) QTD(6) SEQPAC(3) BPA
        """
        linha = ""
        linha += "02"  # Tipo registro
        linha += self.pad_left(self.config.cnes, 7)  # CNES
        linha += self.config.competencia  # Competência
        linha += self.pad_left(record.get('prd_cbo', ''), 6)  # CBO
        linha += self.pad_left(str(folha), 3)  # Folha
        linha += self.pad_left(str(seq), 2)  # Sequência
        linha += self.pad_left(record.get('prd_pa', ''), 10)  # Procedimento
        linha += self.pad_left(str(record.get('prd_idade', 0)), 3)  # Idade
        linha += self.pad_left(str(record.get('prd_qt_p', 1)), 6)  # Quantidade
        linha += self.pad_left(str(record.get('seq_paciente', 1)), 3)  # Seq paciente
        linha += "BPA"  # Indicador
        
        return linha
    
    def generate_set_bpai_line(self, record: Dict, folha: int, seq: int) -> str:
        """
        Gera linha BPA-I (tipo 03) do arquivo .SET
        
        Layout completo (379 caracteres):
        Contém todos os dados do paciente
        """
        linha = ""
        
        # Cabeçalho (pos 1-49)
        linha += "03"  # Tipo registro (1-2)
        linha += self.pad_left(self.config.cnes, 7)  # CNES (3-9)
        linha += self.config.competencia  # Competência (10-15)
        linha += self.pad_left(record.get('prd_cbo', ''), 6)  # CBO (16-21)
        linha += self.pad_right(record.get('prd_cnspac', ''), 15)  # CNS Paciente (22-36)
        linha += self.format_date_yyyymmdd(record.get('prd_dtaten', ''))  # Data atendimento (37-44)
        linha += self.pad_left(str(folha), 3)  # Folha (45-47)
        linha += self.pad_left(str(seq), 2)  # Sequência (48-49)
        
        # Procedimento e profissional (pos 50-74)
        linha += self.pad_left(record.get('prd_pa', ''), 10)  # Procedimento (50-59)
        linha += self.pad_right(record.get('prd_cnsmed', ''), 15)  # CNS Profissional (60-74)
        
        # Dados demográficos (pos 75-96)
        linha += self.pad_right(record.get('prd_sexo', ''), 1)  # Sexo (75)
        linha += self.pad_left(record.get('prd_ibge', ''), 6)  # IBGE (76-81)
        linha += self.pad_right(record.get('prd_cid', ''), 4)  # CID (82-85)
        
        # Calcula idade
        idade = self.calculate_age(
            record.get('prd_dtnasc', ''),
            record.get('prd_dtaten', '')
        )
        linha += self.pad_left(str(idade), 3)  # Idade (86-88)
        linha += self.pad_left(str(record.get('prd_qt_p', 1)), 6)  # Quantidade (89-94)
        linha += self.pad_left(record.get('prd_caten', '01'), 2)  # Caráter atendimento (95-96)
        
        # Autorização (pos 97-109)
        linha += self.pad_right(record.get('prd_naut', ''), 13)  # Num autorização (97-109)
        
        # Indicador (pos 110-112)
        linha += "BPA"
        
        # Nome do paciente (pos 113-142)
        linha += self.pad_right(record.get('prd_nmpac', ''), 30)
        
        # Data nascimento (pos 143-150)
        linha += self.format_date_yyyymmdd(record.get('prd_dtnasc', ''))
        
        # Raça/cor e etnia (pos 151-156)
        linha += self.pad_left(record.get('prd_raca', '99'), 2)  # Raça (151-152)
        linha += self.pad_right(record.get('prd_etnia', ''), 4)  # Etnia (153-156)
        
        # Nacionalidade (pos 157-159)
        linha += self.pad_left(record.get('prd_nac', '010'), 3)
        
        # Reservado (pos 160-193)
        linha += " " * 34
        
        # Endereço (pos 194+)
        linha += self.pad_left(record.get('prd_cep_pcnte', ''), 8)  # CEP (194-201)
        linha += self.pad_left(record.get('prd_lograd_pcnte', ''), 3)  # Tipo logradouro (202-204)
        linha += self.pad_right(record.get('prd_end_pcnte', ''), 30)  # Logradouro (205-234)
        linha += self.pad_right(record.get('prd_compl_pcnte', ''), 10)  # Complemento (235-244)
        linha += self.pad_right(record.get('prd_num_pcnte', ''), 5)  # Número (245-249)
        linha += self.pad_right(record.get('prd_bairro_pcnte', ''), 30)  # Bairro (250-279)
        
        # Telefone (pos 280-290)
        telefone = str(record.get('prd_ddtel_pcnte', '') or '') + str(record.get('prd_tel_pcnte', '') or '')
        linha += self.pad_right(telefone, 11)
        
        # Reservado final (pos 291-379)
        linha += " " * 89
        
        return linha
    
    def generate_set_file(self, bpai_records: List[Dict], bpac_records: List[Dict]) -> Tuple[str, int, int]:
        """
        Gera o arquivo .SET completo
        
        Returns:
            Tuple[str, int, int]: (conteúdo do arquivo, total registros, total BPAs)
        """
        lines = []
        total_registros = len(bpai_records) + len(bpac_records)
        
        # Conta folhas únicas para determinar total de BPAs
        folhas_bpai = set()
        folhas_bpac = set()
        
        # Processa BPA-C
        folha = 1
        seq = 1
        for i, rec in enumerate(bpac_records):
            if seq > 20:  # 20 registros por folha no BPA-C
                folha += 1
                seq = 1
            folhas_bpac.add(folha)
            lines.append(self.generate_set_bpac_line(rec, folha, seq))
            seq += 1
        
        # Processa BPA-I
        folha = 1
        seq = 1
        for i, rec in enumerate(bpai_records):
            if seq > 20:  # 20 registros por folha no BPA-I
                folha += 1
                seq = 1
            folhas_bpai.add(folha)
            lines.append(self.generate_set_bpai_line(rec, folha, seq))
            seq += 1
        
        total_bpas = len(folhas_bpai) + len(folhas_bpac)
        
        # Calcula campo de controle (soma de verificação simples)
        campo_controle = str((total_registros * 7 + total_bpas * 3) % 10000).zfill(4)
        
        # Adiciona cabeçalho no início
        header = self.generate_set_header(total_registros, total_bpas, campo_controle)
        lines.insert(0, header)
        
        return "\n".join(lines), total_registros, total_bpas
    
    # ==========================================================================
    # GERADOR: RELEXP.PRN - Relatório de Controle de Remessa
    # ==========================================================================
    
    def generate_relexp(self, total_registros: int, total_bpas: int, campo_controle: str, extensao: str = None) -> str:
        """
        Gera o arquivo RELEXP.PRN - Relatório de Controle de Remessa
        
        Parâmetros:
        - total_registros: total de linhas no arquivo
        - total_bpas: número de BPAs
        - campo_controle: campo de verificação (cálculo: (registros*7 + bpas*3) % 10000)
        - extensao: extensão do arquivo de remessa (JAN, FEV, etc.) - baseado no mês
        """
        today = datetime.now().strftime('%d/%m/%Y')
        comp_display = self.format_competencia_display(self.config.competencia)
        
        # Se não passou extensão, calcula baseado no mês da competência
        if not extensao:
            mes = self.config.competencia[4:6] if len(self.config.competencia) == 6 else '01'
            extensao = MESES.get(mes, 'TXT')
        
        filename = f"PA{self.config.sigla}.{extensao}"
        
        content = f"""
*******************************************************************Versao: {self.VERSION}
MS/SAS/DATASUS/     SISTEMA DE INFORMACOES AMBULATORIAIS            DATA COMP.
{today}            RELATORIO DE CONTROLE DE REMESSA                {comp_display}
************************************************************Versao banco :{self.config.versao_banco}


 ORGAO RESPONSAVEL PELA INFORMACAO

 NOME   : 

 SIGLA  : 

 CGC/CPF: 


 Carimbo e
 Assinatura : ___________________



 SECRETARIA DE SAUDE DESTINO DOS B.P.A.(s)

 NOME  : 

 ORGAO (M)UNICIPAL OU (E)STADUAL : 


 Setor de                                       Carimbo e
 Recebimento : ____________ Data : ___/___/___  Assinatura : ________________



 ARQUIVO DE BPA(s) GERADO

               NOME : {filename}

 REGISTROS GRAVADOS : {str(total_registros).zfill(6)}

             BPA(s) : {str(total_bpas).zfill(6)}

  CAMPO DE CONTROLE : {campo_controle}





    (ENCAMINHAR ESTE RELATORIO JUNTAMENTE COM O ARQUIVO DE BPA(s) GERADO.)

"""
        return content
    
    # ==========================================================================
    # GERADOR: BPAI_REL.TXT - Relatório BPA Individualizado
    # ==========================================================================
    
    def generate_bpai_header(self, page_num: int, comp_display: str) -> str:
        """Gera cabeçalho da página do relatório BPA-I"""
        today = datetime.now().strftime('%d/%m/%Y')
        
        return f"""
    Folha:{page_num:4d}******************************************************Versao: {self.VERSION}
    MS/SAS/DATASUS/BPA  SISTEMA DE INFORMACOES AMBULATORIAIS             Data Comp
    {today}           RELATORIO DE BPA INDIVIDUALIZADO                {comp_display}
    *******************************************************************************
"""
    
    def generate_bpai_profissional_header(self, cnes: str, cns_prof: str, cbo: str, comp: str, folha: int) -> str:
        """Gera cabeçalho do profissional"""
        comp_fmt = f"{comp[4:6]}/{comp[0:4]}" if len(comp) == 6 else comp
        return f"""
    CNES  : {cnes}
    
    CNS PROFISSIONAL {cns_prof or ''}  CBO : {cbo or ''}
    
    COMPETENCIA : {comp_fmt} FOLHA : {folha:03d}
    
    SQ CNS PACIENTE/NOME  DT.NASC SEXO RACA MUNIC. DT.ATEND.  PROCEDIMENTO   QTD. CID. CA.       PREVIA SITUACAO
"""
    
    def generate_bpai_record_line(self, seq: int, record: Dict) -> str:
        """Gera linha do registro no relatório BPA-I
        
        Layout baseado no arquivo oficial do BPA v04.10 (113 chars):
        Pos 0-3:   4 espaços de indentação
        Pos 4-5:   SQ (2 chars)
        Pos 6:     espaço
        Pos 7-21:  CNS (15 chars)
        Pos 22:    espaço
        Pos 23-32: DT.NASC (10 chars DD/MM/YYYY)
        Pos 33:    espaço
        Pos 34:    SEXO (1 char ou espaço)
        Pos 35-38: 4 espaços
        Pos 39-40: RACA (2 chars)
        Pos 41-42: 2 espaços
        Pos 43-48: MUNIC (6 chars)
        Pos 49:    espaço
        Pos 50-59: DT.ATEND (10 chars DD/MM/YYYY)
        Pos 60:    espaço
        Pos 61-74: PROCEDIMENTO (14 chars GG.SS.TT.PPP-D)
        Pos 75-79: 5 espaços
        Pos 80:    QTD
        Pos 81-82: 2 espaços
        Pos 83-86: CID (4 chars)
        Pos 87:    espaço
        Pos 88-89: CA (2 chars)
        Pos 90-98: 9 espaços
        Pos 99-102: PREVIA (X,XX - 4 chars mínimo)
        Pos 103:   espaço
        Pos 104+:  SITUACAO
        """
        # Formata campos
        cns = self.pad_right(record.get('prd_cnspac', ''), 15)
        dtnasc = self.format_date_display(record.get('prd_dtnasc', ''))
        sexo = record.get('prd_sexo', '') or ' '
        raca = self.pad_left(record.get('prd_raca', ''), 2)
        # Usa código IBGE do registro, ou fallback para o município do estabelecimento
        ibge_raw = record.get('prd_ibge', '') or ''
        if not ibge_raw.strip():
            ibge_raw = self.config.ibge_municipio or ''
        ibge = self.pad_right(ibge_raw, 6)
        dtaten = self.format_date_display(record.get('prd_dtaten', ''))
        
        # Formata procedimento (GG.SS.TT.PPP-D)
        pa = record.get('prd_pa', '') or ''
        if len(pa) >= 10:
            proc = f"{pa[0:2]}.{pa[2:4]}.{pa[4:6]}.{pa[6:9]}-{pa[9]}"
        else:
            proc = self.pad_right(pa, 14)
        
        qtd = int(record.get('prd_qt_p', 0) or 0)
        cid = self.pad_right(record.get('prd_cid', ''), 4)
        caten = self.pad_left(record.get('prd_caten', '01'), 2)
        nome = self.pad_right(record.get('prd_nmpac', ''), 30)
        situacao = "Sem Erros"
        
        # Obtém valor real do procedimento via SIGTAP
        valor_num = self._get_valor_procedimento_num(pa, qtd)
        # Formata valor com 10 espaços antes (alinha à direita em 14 chars)
        # No arquivo oficial: CA(2) + 10 espaços + valor(4) = 16 chars total após CID
        valor_str = f"{valor_num:.2f}".replace('.', ',')
        valor = valor_str.rjust(14)  # 10 espaços + 4 chars (X,XX)
        
        # Formato CID/CA baseado no arquivo oficial:
        # - Com CID: "{qtd} {cid:4} {ca}" = QTD + 1 espaço + CID(4) + 1 espaço + CA
        # - Sem CID: "{qtd}      {ca}" = QTD + 6 espaços + CA
        # Total entre QTD e CA: 6 chars quando vazio, 6 chars quando preenchido (1+4+1)
        if cid.strip():
            cid_section = f" {cid:4} "  # espaço + CID(4) + espaço = 6 chars
        else:
            cid_section = "      "  # 6 espaços
        
        line1 = f"    {seq:02d} {cns} {dtnasc} {sexo}    {raca}  {ibge} {dtaten} {proc}     {qtd}{cid_section}{caten}{valor} {situacao}"
        line2 = f"       {nome}"
        
        return f"{line1}\n{line2}\n"
    
    def _get_valor_procedimento_num(self, codigo_procedimento: str, quantidade: int = 1) -> float:
        """Obtém o valor numérico do procedimento (sem formatação)"""
        if not codigo_procedimento:
            return 0.0
        
        codigo = codigo_procedimento.replace('.', '').replace('-', '').strip()[:10]
        
        if codigo in self._valores_cache:
            valor_unit = self._valores_cache[codigo]
        elif self.sigtap_parser:
            try:
                valores = self.sigtap_parser.get_procedimento_valor(codigo)
                valor_unit = valores.get('valor_ambulatorio', 0.0) or valores.get('valor_sa', 0.0) or 0.0
                self._valores_cache[codigo] = valor_unit
            except Exception as e:
                logger.warning(f"Erro ao obter valor do procedimento {codigo}: {e}")
                valor_unit = 0.0
                self._valores_cache[codigo] = valor_unit
        else:
            valor_unit = 0.0
        
        return valor_unit * quantidade
    
    def generate_bpai_footer(self) -> str:
        """Gera rodapé de formalização"""
        return """
    FORMALIZACAO ----------- Valores sujeitos a criticas/alteração pelo gestor -
    RESP.UNIDADE :           RESP.GESTOR MUNICIPAL :      RESP.GESTOR ESTADUAL :
    Carimbo     Rubrica      Carimbo     Rubrica          Carimbo     Rubrica   
    Data:___/___/___         Data:___/___/___             Data:___/___/___      
"""
    
    def generate_bpai_report(self, records: List[Dict]) -> str:
        """Gera relatório BPA-I completo"""
        output = []
        comp_display = self.format_competencia_display(self.config.competencia)
        
        # Agrupa por profissional
        by_professional = {}
        for rec in records:
            key = (rec.get('prd_cnsmed', ''), rec.get('prd_cbo', ''))
            if key not in by_professional:
                by_professional[key] = []
            by_professional[key].append(rec)
        
        # Ordena profissionais por CNS (ordem crescente)
        sorted_professionals = sorted(by_professional.keys(), key=lambda x: x[0] or '')
        
        page_num = 1
        for (cns_prof, cbo) in sorted_professionals:
            prof_records = by_professional[(cns_prof, cbo)]
            
            # Ordena registros por data de atendimento
            prof_records.sort(key=lambda r: self.format_date_yyyymmdd(r.get('prd_dtaten', '')) or '00000000')
            
            folha = 1
            records_on_page = 0
            
            output.append(self.generate_bpai_header(page_num, comp_display))
            output.append(self.generate_bpai_profissional_header(
                self.config.cnes, cns_prof, cbo, self.config.competencia, folha
            ))
            
            for i, rec in enumerate(prof_records):
                if records_on_page >= 19:
                    output.append(self.generate_bpai_footer())
                    page_num += 1
                    folha += 1
                    output.append(self.generate_bpai_header(page_num, comp_display))
                    output.append(self.generate_bpai_profissional_header(
                        self.config.cnes, cns_prof, cbo, self.config.competencia, folha
                    ))
                    records_on_page = 0
                
                output.append(self.generate_bpai_record_line(i + 1, rec))
                records_on_page += 1
            
            output.append(self.generate_bpai_footer())
            page_num += 1
        
        return ''.join(output)
    
    # ==========================================================================
    # GERADOR: BPAC_REL.TXT - Relatório BPA Consolidado
    # ==========================================================================
    
    def generate_bpac_header(self, page_num: int, comp_display: str) -> str:
        """Gera cabeçalho da página do relatório BPA-C"""
        today = datetime.now().strftime('%d/%m/%Y')
        
        return f"""
    Folha:{page_num:4d}******************************************************Versao: {self.VERSION}
    MS/SAS/DATASUS/BPA  SISTEMA DE INFORMACOES AMBULATORIAIS             Data Comp
    {today}           RELATORIO DE BPA CONSOLIDADO                    {comp_display}
    *******************************************************************************
"""
    
    def generate_bpac_table_header(self, cnes: str, cbo: str, comp: str, folha: int) -> str:
        """Gera cabeçalho da tabela BPA-C"""
        comp_fmt = f"{comp[4:6]}/{comp[0:4]}" if len(comp) == 6 else comp
        return f"""
    CNES  : {cnes}
    
    CBO : {cbo or ''}
    
    COMPETENCIA : {comp_fmt} FOLHA : {folha:03d}
    
    SQ  PROCEDIMENTO   IDADE QTD   SQ  PROCEDIMENTO   IDADE QTD   SQ  PROCEDIMENTO   IDADE QTD
"""
    
    def generate_bpac_record_line(self, records: List[Dict], start_seq: int) -> str:
        """Gera linha com até 3 registros lado a lado"""
        parts = []
        for i, rec in enumerate(records[:3]):
            seq = start_seq + i
            
            # Formata procedimento
            pa = rec.get('prd_pa', '') or ''
            if len(pa) >= 10:
                proc = f"{pa[0:2]}.{pa[2:4]}.{pa[4:6]}.{pa[6:9]}-{pa[9]}"
            else:
                proc = self.pad_right(pa, 14)
            
            idade = self.pad_left(str(rec.get('prd_idade', 0) or 0), 3)
            qtd = self.pad_left(str(rec.get('prd_qt_p', 1) or 1), 4)
            
            parts.append(f"{seq:02d}  {proc} {idade}  {qtd}")
        
        # Preenche com espaços se menos de 3 registros
        while len(parts) < 3:
            parts.append(" " * 25)
        
        return "    " + "   ".join(parts) + "\n"
    
    def generate_bpac_footer(self) -> str:
        """Gera rodapé BPA-C"""
        return """
    FORMALIZACAO ----------- Valores sujeitos a criticas/alteração pelo gestor -
    RESP.UNIDADE :           RESP.GESTOR MUNICIPAL :      RESP.GESTOR ESTADUAL :
    Carimbo     Rubrica      Carimbo     Rubrica          Carimbo     Rubrica   
    Data:___/___/___         Data:___/___/___             Data:___/___/___      
"""
    
    def generate_bpac_report(self, records: List[Dict]) -> str:
        """Gera relatório BPA-C completo"""
        output = []
        comp_display = self.format_competencia_display(self.config.competencia)
        
        # Agrupa por CBO
        by_cbo = {}
        for rec in records:
            cbo = rec.get('prd_cbo', '')
            if cbo not in by_cbo:
                by_cbo[cbo] = []
            by_cbo[cbo].append(rec)
        
        page_num = 1
        for cbo, cbo_records in by_cbo.items():
            folha = 1
            records_on_page = 0
            
            output.append(self.generate_bpac_header(page_num, comp_display))
            output.append(self.generate_bpac_table_header(
                self.config.cnes, cbo, self.config.competencia, folha
            ))
            
            # Processa em grupos de 3 (3 colunas por linha)
            for i in range(0, len(cbo_records), 3):
                if records_on_page >= 20:
                    output.append(self.generate_bpac_footer())
                    page_num += 1
                    folha += 1
                    output.append(self.generate_bpac_header(page_num, comp_display))
                    output.append(self.generate_bpac_table_header(
                        self.config.cnes, cbo, self.config.competencia, folha
                    ))
                    records_on_page = 0
                
                batch = cbo_records[i:i+3]
                output.append(self.generate_bpac_record_line(batch, i + 1))
                records_on_page += 1
            
            output.append(self.generate_bpac_footer())
            page_num += 1
        
        return ''.join(output)


class BPAReportService:
    """Serviço para geração de relatórios BPA a partir do PostgreSQL"""
    
    def __init__(self, db_module):
        """
        Args:
            db_module: Módulo de banco de dados (database.py)
        """
        self.db = db_module
    
    def get_bpai_records(self, cnes: str, competencia: str) -> List[Dict]:
        """Busca registros BPA-I do PostgreSQL"""
        return self.db.list_bpa_individualizado(cnes, competencia)
    
    def get_bpac_records(self, cnes: str, competencia: str) -> List[Dict]:
        """Busca registros BPA-C do PostgreSQL"""
        return self.db.list_bpa_consolidado(cnes, competencia)
    
    def generate_all_reports(
        self, 
        cnes: str, 
        competencia: str, 
        sigla: str = "CAPSAD"
    ) -> Dict[str, Any]:
        """
        Gera todos os 4 relatórios BPA
        
        Returns:
            Dict com:
                - set_file: conteúdo do arquivo .SET
                - set_filename: nome do arquivo .SET
                - relexp: conteúdo do RELEXP.PRN
                - bpai_rel: conteúdo do BPAI_REL.TXT
                - bpac_rel: conteúdo do BPAC_REL.TXT
                - stats: estatísticas
        """
        # Busca dados
        bpai_records = self.get_bpai_records(cnes, competencia)
        bpac_records = self.get_bpac_records(cnes, competencia)
        
        # Configura gerador
        config = BPAExportConfig(
            cnes=cnes,
            competencia=competencia,
            sigla=sigla
        )
        generator = BPAFileGenerator(config)
        
        # Gera arquivo .SET
        set_content, total_registros, total_bpas = generator.generate_set_file(
            bpai_records, bpac_records
        )
        campo_controle = str((total_registros * 7 + total_bpas * 3) % 10000).zfill(4)
        
        # Gera outros relatórios
        relexp_content = generator.generate_relexp(total_registros, total_bpas, campo_controle)
        bpai_rel_content = generator.generate_bpai_report(bpai_records)
        bpac_rel_content = generator.generate_bpac_report(bpac_records)
        
        return {
            'set_file': set_content,
            'set_filename': f"PA{sigla}.SET",
            'relexp': relexp_content,
            'relexp_filename': 'RELEXP.PRN',
            'bpai_rel': bpai_rel_content,
            'bpai_rel_filename': 'BPAI_REL.TXT',
            'bpac_rel': bpac_rel_content,
            'bpac_rel_filename': 'BPAC_REL.TXT',
            'stats': {
                'total_registros': total_registros,
                'total_bpas': total_bpas,
                'bpai_count': len(bpai_records),
                'bpac_count': len(bpac_records),
                'campo_controle': campo_controle,
                'competencia': competencia,
                'cnes': cnes
            }
        }
