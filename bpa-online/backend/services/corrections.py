"""
Serviço de Correções BPA
Aplica todas as correções necessárias antes da exportação do BPA
Baseado nos scripts SQL de correção do BPA-main
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


def pad_left(value: str, char: str, length: int) -> str:
    """
    Equivalente Python da função SM_PADLEFT do Firebird
    Preenche uma string à esquerda com um caractere até atingir o tamanho desejado
    
    Args:
        value: Valor original
        char: Caractere de preenchimento
        length: Tamanho final desejado
    
    Returns:
        String preenchida
    
    Exemplo:
        pad_left('5', '0', 3) -> '005'
        pad_left('12', '0', 2) -> '12'
    """
    return str(value).rjust(length, char)


@dataclass
class CorrectionResult:
    """Resultado da aplicação de correções"""
    original: Dict
    corrected: Dict
    corrections_applied: List[str]
    should_delete: bool
    delete_reason: Optional[str] = None


class BPACorrections:
    """Aplica correções aos registros BPA antes da exportação"""
    
    # Procedimentos que devem ser excluídos (não pertencem ao BPA)
    PROCEDIMENTOS_EXCLUIR = {
        '0100000002','0101000006','0101010001','0101020007','0101030002','0101040008','0101050003',
        '0102000000','0102010005','0102020000','0200000004','0201000008','0201010003','0201020009',
        '0202000001','0202010007','0202020002','0202030008','0202040003','0202050009','0202060004',
        '0202070000','0202080005','0202090000','0202100006','0202110001','0202120007','0203000005',
        '0203010000','0203020006','0204000009','0204010004','0204020000','0204030005','0204040000',
        '0204050006','0204060001','0205000002','0205010008','0205020003','0206000006','0206010001',
        '0206020007','0206030002','0207000000','0207010005','0207020000','0207030006','0208000003',
        '0208010009','0208030000','0208040005','0208050000','0208060006','0208080007','0208090002',
        '0209000007','0209010002','0209020008','0209030003','0209040009','0210000007','0210010002',
        '0210020008','0211000000','0211010006','0211020001','0211030007','0211040002','0211050008',
        '0211060003','0211070009','0211080004','0211090000','0211100005','0212000004','0212010000',
        '0212020005','0213000008','0213010003','0213020009','0214000001','0214010007','0300000006',
        '0301000000','0301010005','0301020000','0301030006','0301040001','0301050007','0301060002',
        '0301070008','0301080003','0301090009','0301100004','0301110000','0301120005','0301130000',
        '0301160007','0302000003','0302010009','0302020004','0302030000','0302040005','0302050000',
        '0302060006','0302070001','0303000007','0303010002','0303020008','0303030003','0303050004',
        '0303060000','0303070005','0303080000','0303090006','0303120002','0303140003','0303190000',
        '0304000000','0304010006','0304020001','0304030007','0304040002','0304050008','0304060003',
        '0304070009','0304080004','0304090000','0305000004','0305010000','0305020005','0306000008',
        '0306010003','0306020009','0307000001','0307010007','0307020002','0307030008','0307040003',
        '0308000005','0308010000','0309000009','0309020000','0309030005','0309040000','0309050006',
        '0309070007','0310000009','0311000002','0311010008','0311020003','0400000008','0401000001',
        '0401010007','0401020002','0403000009','0403050006','0404000002','0404010008','0404020003',
        '0405000006','0405010001','0405020007','0405030002','0405040008','0405050003','0406000000',
        '0406020000','0406030006','0407000003','0407010009','0407020004','0407030000','0407040005',
        '0408000007','0408010002','0408020008','0408050004','0408060000','0409000000','0409010006',
        '0409020001','0409040002','0409050008','0409060003','0409070009','0410000000','0410010006',
        '0411000004','0411010000','0411020005','0412000008','0412010003','0412030004','0412050005',
        '0413000001','0413010007','0413030008','0413040003','0414000005','0414010000','0414020006',
        '0415000009','0415040000','0416000002','0416030009','0417000006','0417010001','0418000000',
        '0418010005','0418020000','0500000000','0501000003','0501010009','0501020004','0501030000',
        '0501040005','0501070001','0501080007','0503010006','0503030007','0503040002','0504000004',
        '0504010000','0504040006','0505000008','0505010003','0506000001','0506010007','0600000001',
        '0603000002','0603050000','0604000006','0604010001','0604020007','0604030002','0604040008',
        '0604050003','0604060009','0604070004','0604080000','0604090005','0604100000','0604110006',
        '0604120001','0604130007','0604140002','0604150008','0604160003','0604170009','0604180004',
        '0604190000','0604200005','0604210000','0604220006','0604230001','0604240007','0604250002',
        '0604260008','0604270003','0604280009','0604290004','0604310005','0604320000','0604330006',
        '0604340001','0604350007','0604360002','0604370008','0604380003','0604390009','0604400004',
        '0604410000','0604420005','0604430000','0604440006','0604470002','0604480008','0604490003',
        '0604500009','0604510004','0604520000','0604530005','0604540000','0604550006','0604560001',
        '0604570007','0604580002','0604590008','0604600003','0604610009','0604620004','0604630000',
        '0604650000','0604660006','0604670001','0604680007','0604690002','0604700008','0604710003',
        '0604720009','0604730004','0604740000','0604750005','0604770006','0604780001','0604790007',
        '0604800002','0604810008','0604820003','0604830009','0604840004','0604850000','0604860005',
        '0604870000','0700000003','0701000007','0701010002','0701020008','0701030003','0701040009',
        '0701050004','0701060000','0701070005','0701080000','0701090006','0701100001','0702000000',
        '0702020001','0702040002','0702050008','0702070009','0702100005','0702120006','0800000005',
        '0801000009','0801010004','0803000006','0803010001','0804000000','0804010005','0804020000',
        '0804030006','0900000007','0901000000','0901010006','0902000004','0902010000','0903000008',
        '0903010003','0904000001','0904010007','0905000005','0905010000',
        # Procedimentos adicionais específicos
        '0309010101','0303140135','0303130024','0302050035','0201010054','0301060070','0101040121',
        '0301100250','0101040083','0101040075','0301100268',
    }
    
    # CNES que são UPAs (caráter de atendimento = 02)
    CNES_UPAS = {'2755289', '2492555', '2829606'}
    
    # Mapa de correção de procedimentos revogados
    PROCEDIMENTOS_REVOGADOS = {
        '0214010090': '0214010295',
        '0214010104': '0214010228',
        '0301010064': '0301010072',
        '0301010030': '0301010048',
    }
    
    # Mapa de correção de CID por procedimento (PA -> CID correto)
    CORRECOES_CID = {
        '0302010017': 'N318',
        '0201010526': 'A308',
        '0302050027': 'M998',
        '0301070059': 'F848',
        '0303030097': 'F649',
        '0401010104': 'L029',
        '0301080232': 'F018',  # Atualizado
        '0301130043': 'F640',
        '0301040052': 'Z614',
        '0404010318': 'T16',
        '0302020039': 'A818',
        '0211030074': 'M797',
        '0301070121': 'G64',
        '0301070148': 'H540',
        '0302010025': 'N039',
        '0302040013': 'J989',
        '0302040021': 'J989',
        '0302040030': 'I018',
        '0302040048': 'I519',
        '0302050019': 'M241',
        '0302060014': 'M349',
        '0302060022': 'G64',
        '0302060030': 'G833',
        '0303190019': 'G979',
        '0301070113': 'F900',
        '0401010031': 'L029',
        '0404020054': 'D180',
        '0404020097': 'K061',
        '0302060057': 'A308',
        '0201010267': 'Z018',
        '0302060049': 'F018',
        '0201010151': 'N970',
        '0301120048': 'E031',
        '0404020313': 'T858',
        '0309070015': 'I832',
        '0309070023': 'I832',
        '0301070105': 'Z899',  # Atualizado
        '0302070010': 'T302',
        '0301130035': 'F640',
        '0404020089': 'K117',
        '0201010585': 'N63',
    }
    
    # Limite máximo de quantidade por procedimento
    LIMITES_QUANTIDADE = {
        '0302050027': 20,
        '0302060014': 20,
        '0701070080': 1,
        '0201010372': 1,
        '0701070137': 1,
        '0302060022': 20,
        '0302040021': 20,
        '0302050019': 20,
        '0301010315': 1,
        '0301130035': 1,
        '0205020054': 1,
        '0205020143': 1,
    }
    
    # CEP padrão para Palmas-TO
    CEP_PADRAO = '77001324'
    
    # CEPs inválidos que devem ser substituídos pelo padrão
    CEPS_INVALIDOS = {
        '77024899', '77022000', '77008738', '77063000', '77060561', '75380000',
        '77024000', '77000623', '77270000', '77134050', '77000173', '07701507',
        '77003214', '68925000', '77015341', '64800000', '74900000', '77015970',
        '77100070', '77140300', '77271000', '77400000', '77800000', '77000000',
        '65000000', '65085000', '65600000', '65900000', '68500000', '68550970',
        '68555110', '70000000', '72110800', '74000000', '74230020', '75000000',
        '75900000', '77010970', '77130130', '77140520',
    }
    
    # Código IBGE padrão (Palmas-TO)
    IBGE_PADRAO = '172100'
    
    # Código de logradouro padrão
    LOGRADOURO_PADRAO = '077'
    
    # Serviço/Classificação para procedimentos específicos
    SERVICO_CLASSIFICACAO = {
        '0211060127': ('131', None),
        '0405050089': ('131', '003'),
        '0211060011': ('131', None),
        '0211060151': ('131', None),
    }
    
    # Procedimentos AB que devem ser filtrados
    PROCEDIMENTOS_AB_EXCLUIR = {
        'ABPO015', 'ABPG040', 'ABPG039', 'ABPG038', 'ABPG034',
        'ABEX022', 'ABEX013', 'ABEX012',
    }
    
    def __init__(self, cnes: str = None):
        """
        Inicializa o serviço de correções
        
        Args:
            cnes: CNES da unidade (usado para correções específicas)
        """
        self.cnes = cnes
        self.is_upa = cnes in self.CNES_UPAS if cnes else False
    
    def apply_corrections(self, record: Dict, tipo: str = 'BPI') -> CorrectionResult:
        """
        Aplica todas as correções necessárias a um registro
        
        Args:
            record: Dicionário com os dados do registro
            tipo: Tipo do BPA ('BPI' ou 'BPA')
        
        Returns:
            CorrectionResult com os dados corrigidos e lista de correções
        """
        corrections = []
        corrected = record.copy()
        should_delete = False
        delete_reason = None
        
        # 1. Verifica se o procedimento deve ser excluído
        procedimento = record.get('procedimento') or record.get('prd_pa') or ''
        
        if procedimento in self.PROCEDIMENTOS_EXCLUIR:
            should_delete = True
            delete_reason = f"Procedimento {procedimento} não pertence ao BPA"
            return CorrectionResult(
                original=record,
                corrected=corrected,
                corrections_applied=corrections,
                should_delete=should_delete,
                delete_reason=delete_reason
            )
        
        # 2. Verifica procedimento vazio ou nulo
        if not procedimento or procedimento.strip() == '':
            should_delete = True
            delete_reason = "Procedimento vazio ou nulo"
            return CorrectionResult(
                original=record,
                corrected=corrected,
                corrections_applied=corrections,
                should_delete=should_delete,
                delete_reason=delete_reason
            )
        
        # 3. Para BPI, verifica CNS ou CPF do paciente (pelo menos um deve estar preenchido)
        if tipo == 'BPI':
            cns_paciente = record.get('cns_paciente') or record.get('prd_cnspac') or ''
            cpf_paciente = record.get('cpf_paciente') or record.get('prd_cpf_pcnte') or ''

            cns_paciente = str(cns_paciente) if cns_paciente is not None else ''
            cpf_paciente = str(cpf_paciente) if cpf_paciente is not None else ''

            cns_valido = cns_paciente and cns_paciente.strip() != ''
            cpf_valido = cpf_paciente and cpf_paciente.strip() != '' and len(cpf_paciente.strip()) >= 11
            
            # Se CNS/CPF vazios, tenta buscar no cadastro de pacientes pelo nome+nascimento
            if not cns_valido and not cpf_valido:
                nome = record.get('nome_paciente') or record.get('prd_nmpac') or ''
                data_nasc = record.get('data_nascimento') or record.get('prd_dtnasc') or ''
                
                if nome and data_nasc:
                    try:
                        from database import BPADatabase
                        db = BPADatabase()
                        paciente = db.get_paciente_by_nome_nascimento(nome, data_nasc)
                        if paciente:
                            # Encontrou paciente no cadastro!
                            if paciente.get('cns'):
                                cns_paciente = paciente['cns']
                                cns_valido = True
                                corrected['cns_paciente'] = cns_paciente
                                if 'prd_cnspac' in corrected:
                                    corrected['prd_cnspac'] = cns_paciente
                                corrections.append(f"CNS recuperado do cadastro: {cns_paciente}")
                            elif paciente.get('cpf'):
                                cpf_paciente = paciente['cpf']
                                cpf_valido = True
                                corrections.append(f"CPF recuperado do cadastro: {cpf_paciente}")
                    except Exception as e:
                        pass  # Ignora erro de busca, vai usar validação padrão
            
            if not cns_valido and not cpf_valido:
                should_delete = True
                delete_reason = "CNS/CPF do paciente vazio (obrigatório para BPI)"
                return CorrectionResult(
                    original=record,
                    corrected=corrected,
                    corrections_applied=corrections,
                    should_delete=should_delete,
                    delete_reason=delete_reason
                )
            
            # Se tem CPF mas não CNS, usa o CPF no campo CNS para exportação
            if not cns_valido and cpf_valido:
                corrected['cns_paciente'] = cpf_paciente.strip()
                if 'prd_cnspac' in corrected:
                    corrected['prd_cnspac'] = cpf_paciente.strip()
                corrections.append(f"Usando CPF como identificador: {cpf_paciente.strip()}")
        
        # 4. Corrige procedimentos revogados
        if procedimento in self.PROCEDIMENTOS_REVOGADOS:
            novo_pa = self.PROCEDIMENTOS_REVOGADOS[procedimento]
            corrected['procedimento'] = novo_pa
            if 'prd_pa' in corrected:
                corrected['prd_pa'] = novo_pa
            corrections.append(f"Procedimento revogado: {procedimento} → {novo_pa}")
        
        # 5. Corrige raça/cor (05 e 06 → 03)
        raca = str(record.get('raca_cor') or record.get('prd_raca') or '01')
        if raca in ('05', '06'):
            corrected['raca_cor'] = '03'
            if 'prd_raca' in corrected:
                corrected['prd_raca'] = '03'
            corrections.append(f"Raça/Cor corrigida: {raca} → 03")
        
        # 6. Corrige caráter de atendimento para UPAs
        if tipo == 'BPI' and self.is_upa:
            caten = record.get('carater_atendimento') or record.get('prd_caten') or '01'
            if caten == '01':
                corrected['carater_atendimento'] = '02'
                if 'prd_caten' in corrected:
                    corrected['prd_caten'] = '02'
                corrections.append("Caráter de atendimento UPA: 01 → 02")
        
        # 7. Corrige CID para procedimentos específicos
        procedimento_atual = corrected.get('procedimento') or corrected.get('prd_pa') or ''
        if procedimento_atual in self.CORRECOES_CID:
            cid_correto = self.CORRECOES_CID[procedimento_atual]
            cid_atual = record.get('cid') or record.get('prd_cid') or ''
            if cid_atual != cid_correto:
                corrected['cid'] = cid_correto
                if 'prd_cid' in corrected:
                    corrected['prd_cid'] = cid_correto
                corrections.append(f"CID corrigido para PA {procedimento_atual}: {cid_atual} → {cid_correto}")
        
        # 8. Aplica limites de quantidade
        if procedimento_atual in self.LIMITES_QUANTIDADE:
            limite = self.LIMITES_QUANTIDADE[procedimento_atual]
            qtd = int(record.get('quantidade') or record.get('prd_qt_p') or 1)
            if qtd > limite:
                corrected['quantidade'] = limite
                if 'prd_qt_p' in corrected:
                    corrected['prd_qt_p'] = limite
                corrections.append(f"Quantidade limitada: {qtd} → {limite} (PA {procedimento_atual})")
        
        # 9. Corrige CEP (para BPI)
        if tipo == 'BPI':
            cep = str(record.get('cep') or record.get('prd_cep_pcnte') or '')
            if not cep or cep.strip() == '' or cep in self.CEPS_INVALIDOS:
                corrected['cep'] = self.CEP_PADRAO
                if 'prd_cep_pcnte' in corrected:
                    corrected['prd_cep_pcnte'] = self.CEP_PADRAO
                if cep:
                    corrections.append(f"CEP inválido corrigido: {cep} → {self.CEP_PADRAO}")
                else:
                    corrections.append(f"CEP vazio preenchido: {self.CEP_PADRAO}")
        
        # 10. Corrige código IBGE
        ibge = record.get('municipio_ibge') or record.get('prd_ibge') or ''
        if not ibge or ibge.strip() == '':
            corrected['municipio_ibge'] = self.IBGE_PADRAO
            if 'prd_ibge' in corrected:
                corrected['prd_ibge'] = self.IBGE_PADRAO
            corrections.append(f"IBGE vazio preenchido: {self.IBGE_PADRAO}")
        
        # 11. Corrige logradouro (para BPI)
        if tipo == 'BPI':
            logradouro = record.get('logradouro_codigo') or record.get('prd_lograd_pcnte') or ''
            if not logradouro or logradouro.strip() == '':
                corrected['logradouro_codigo'] = self.LOGRADOURO_PADRAO
                if 'prd_lograd_pcnte' in corrected:
                    corrected['prd_lograd_pcnte'] = self.LOGRADOURO_PADRAO
                corrections.append(f"Logradouro vazio preenchido: {self.LOGRADOURO_PADRAO}")
        
        # 12. Corrige endereço vazio
        if tipo == 'BPI':
            endereco = record.get('endereco') or record.get('prd_end_pcnte') or ''
            if not endereco or endereco.strip() == '':
                corrected['endereco'] = 'NAO LOCALIZADO'
                if 'prd_end_pcnte' in corrected:
                    corrected['prd_end_pcnte'] = 'NAO LOCALIZADO'
                corrections.append("Endereço vazio preenchido: NAO LOCALIZADO")
        
        # 13. Corrige bairro vazio
        if tipo == 'BPI':
            bairro = record.get('bairro') or record.get('prd_bairro_pcnte') or ''
            if not bairro or bairro.strip() == '':
                corrected['bairro'] = 'NAO LOCALIZADO'
                if 'prd_bairro_pcnte' in corrected:
                    corrected['prd_bairro_pcnte'] = 'NAO LOCALIZADO'
                corrections.append("Bairro vazio preenchido: NAO LOCALIZADO")
        
        # 14. Corrige número vazio ou inválido
        if tipo == 'BPI':
            numero = str(record.get('numero') or record.get('prd_num_pcnte') or '')
            numeros_invalidos = {'', '00', '000', '0000', '00000', 'S/N', 'cs02', 'SN'}
            if numero.upper() in numeros_invalidos:
                corrected['numero'] = '01'
                if 'prd_num_pcnte' in corrected:
                    corrected['prd_num_pcnte'] = '01'
                corrections.append(f"Número inválido corrigido: '{numero}' → 01")
        
        # 15. Aplica serviço/classificação para procedimentos específicos
        if procedimento_atual in self.SERVICO_CLASSIFICACAO:
            servico, classificacao = self.SERVICO_CLASSIFICACAO[procedimento_atual]
            if servico:
                corrected['servico'] = servico
                if 'prd_servico' in corrected:
                    corrected['prd_servico'] = servico
                corrections.append(f"Serviço definido: {servico}")
            if classificacao:
                corrected['classificacao'] = classificacao
                if 'prd_classificacao' in corrected:
                    corrected['prd_classificacao'] = classificacao
                corrections.append(f"Classificação definida: {classificacao}")
        
        # 16. Corrige SEXO (0 -> M, 1 -> F)
        if tipo == 'BPI':
            sexo = str(record.get('sexo') or record.get('prd_sexo') or '')
            novo_sexo = sexo
            
            if sexo == '0':
                novo_sexo = 'M'
            elif sexo == '1':
                novo_sexo = 'F'
            elif sexo not in ('M', 'F'):
                novo_sexo = 'M'  # Default para valores inválidos
            
            if novo_sexo != sexo:
                corrected['sexo'] = novo_sexo
                if 'prd_sexo' in corrected:
                    corrected['prd_sexo'] = novo_sexo
                corrections.append(f"Sexo corrigido: {sexo} → {novo_sexo}")
        
        return CorrectionResult(
            original=record,
            corrected=corrected,
            corrections_applied=corrections,
            should_delete=should_delete,
            delete_reason=delete_reason
        )
    
    def process_batch(self, records: List[Dict], tipo: str = 'BPI') -> Tuple[List[Dict], Dict]:
        """
        Processa um lote de registros aplicando correções
        
        Args:
            records: Lista de registros
            tipo: Tipo do BPA ('BPI' ou 'BPA')
        
        Returns:
            Tupla com (registros_corrigidos, estatísticas)
        """
        corrected_records = []
        stats = {
            'total_input': len(records),
            'total_output': 0,
            'deleted': 0,
            'corrected': 0,
            'unchanged': 0,
            'delete_reasons': {},
            'correction_types': {},
        }
        
        for record in records:
            result = self.apply_corrections(record, tipo)
            
            if result.should_delete:
                stats['deleted'] += 1
                reason = result.delete_reason or 'Desconhecido'
                stats['delete_reasons'][reason] = stats['delete_reasons'].get(reason, 0) + 1
            else:
                corrected_records.append(result.corrected)
                
                if result.corrections_applied:
                    stats['corrected'] += 1
                    for correction in result.corrections_applied:
                        # Extrai tipo de correção
                        correction_type = correction.split(':')[0] if ':' in correction else correction
                        stats['correction_types'][correction_type] = stats['correction_types'].get(correction_type, 0) + 1
                else:
                    stats['unchanged'] += 1
        
        stats['total_output'] = len(corrected_records)
        
        return corrected_records, stats
    
    def get_correction_summary(self, stats: Dict) -> str:
        """
        Gera um resumo textual das correções aplicadas
        
        Args:
            stats: Estatísticas retornadas por process_batch
        
        Returns:
            String com resumo formatado
        """
        lines = [
            "=" * 50,
            "RESUMO DAS CORREÇÕES BPA",
            "=" * 50,
            f"Total de registros recebidos: {stats['total_input']}",
            f"Total de registros exportados: {stats['total_output']}",
            f"Registros excluídos: {stats['deleted']}",
            f"Registros corrigidos: {stats['corrected']}",
            f"Registros sem alteração: {stats['unchanged']}",
            "",
        ]
        
        if stats['delete_reasons']:
            lines.append("MOTIVOS DE EXCLUSÃO:")
            for reason, count in stats['delete_reasons'].items():
                lines.append(f"  - {reason}: {count}")
            lines.append("")
        
        if stats['correction_types']:
            lines.append("TIPOS DE CORREÇÃO APLICADAS:")
            for correction_type, count in stats['correction_types'].items():
                lines.append(f"  - {correction_type}: {count}")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def assign_sequence_bpi(self, records: List[Dict]) -> List[Dict]:
        """
        Atribui folha e sequência para registros BPI
        Equivalente à procedure CORRIGE_SEQUENCIA_BPI do Firebird
        
        Regras:
        - Agrupa por CMP (competência) e CNSMED (CNS do profissional)
        - Máximo 99 registros por folha
        - Ordena por: competência, CNS profissional, PA, data atendimento, CNES
        
        Args:
            records: Lista de registros BPI
        
        Returns:
            Lista de registros com folha e sequência atribuídas
        """
        if not records:
            return records
        
        # Ordena os registros
        sorted_records = sorted(records, key=lambda r: (
            r.get('competencia') or r.get('prd_cmp') or '',
            r.get('cns_profissional') or r.get('prd_cnsmed') or '',
            r.get('procedimento') or r.get('prd_pa') or '',
            r.get('data_atendimento') or r.get('prd_dtaten') or '',
            r.get('cnes') or r.get('prd_uid') or ''
        ))
        
        prev_cnsmed = ''
        prev_cmp = ''
        fol_novo = 0
        seq_novo = 0
        
        for record in sorted_records:
            cnsmed = record.get('cns_profissional') or record.get('prd_cnsmed') or ''
            cmp = record.get('competencia') or record.get('prd_cmp') or ''
            
            seq_novo += 1
            
            # Reinicia se mudar o profissional
            if cnsmed != prev_cnsmed:
                prev_cnsmed = cnsmed
                seq_novo = 1
                fol_novo = 1
            
            # Reinicia se mudar a competência
            if cmp != prev_cmp:
                prev_cmp = cmp
                seq_novo = 1
                fol_novo = 1
            
            # Nova folha a cada 99 registros
            if seq_novo > 99:
                seq_novo = 1
                fol_novo += 1
            
            # Atribui folha e sequência formatadas
            record['folha'] = pad_left(str(fol_novo), '0', 3)
            record['sequencia'] = pad_left(str(seq_novo), '0', 2)
            
            # Também nos campos PRD_ se existirem
            if 'prd_flh' in record:
                record['prd_flh'] = pad_left(str(fol_novo), '0', 3)
            if 'prd_seq' in record:
                record['prd_seq'] = pad_left(str(seq_novo), '0', 2)
        
        return sorted_records
    
    def assign_sequence_bpa(self, records: List[Dict]) -> List[Dict]:
        """
        Atribui folha e sequência para registros BPA consolidado
        Equivalente à procedure CORRIGE_SEQUENCIA_BPA do Firebird
        
        Regras:
        - Agrupa por CNES (UID)
        - Máximo 20 registros por folha
        - Ordena por: CNES
        
        Args:
            records: Lista de registros BPA consolidado
        
        Returns:
            Lista de registros com folha e sequência atribuídas
        """
        if not records:
            return records
        
        # Ordena os registros por CNES
        sorted_records = sorted(records, key=lambda r: (
            r.get('cnes') or r.get('prd_uid') or ''
        ))
        
        prev_cnes = ''
        fol_novo = 0
        seq_novo = 0
        
        for record in sorted_records:
            cnes = record.get('cnes') or record.get('prd_uid') or ''
            
            seq_novo += 1
            
            # Reinicia se mudar o CNES
            if cnes != prev_cnes:
                prev_cnes = cnes
                seq_novo = 1
                fol_novo = 1
            
            # Nova folha a cada 20 registros
            if seq_novo > 20:
                seq_novo = 1
                fol_novo += 1
            
            # Atribui folha e sequência formatadas
            record['folha'] = pad_left(str(fol_novo), '0', 3)
            record['sequencia'] = pad_left(str(seq_novo), '0', 2)
            
            # Também nos campos PRD_ se existirem
            if 'prd_flh' in record:
                record['prd_flh'] = pad_left(str(fol_novo), '0', 3)
            if 'prd_seq' in record:
                record['prd_seq'] = pad_left(str(seq_novo), '0', 2)
        
        return sorted_records
    
    def generate_id(self, start_id: int = 1) -> callable:
        """
        Cria um gerador de IDs sequenciais
        Equivalente ao GENERATOR GEN_S_PRD_ID do Firebird
        
        Args:
            start_id: ID inicial
        
        Returns:
            Função geradora que retorna o próximo ID
        """
        current_id = start_id - 1
        
        def next_id():
            nonlocal current_id
            current_id += 1
            return current_id
        
        return next_id
    
    def assign_ids(self, records: List[Dict], start_id: int = 1) -> List[Dict]:
        """
        Atribui IDs sequenciais aos registros
        
        Args:
            records: Lista de registros
            start_id: ID inicial
        
        Returns:
            Lista de registros com IDs atribuídos
        """
        get_next_id = self.generate_id(start_id)
        
        for record in records:
            record['prd_id'] = get_next_id()
        
        return records


# Instância padrão
corrections = BPACorrections()
