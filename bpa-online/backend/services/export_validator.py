"""
Validador de Exportação BPA
Valida registros antes da exportação para Firebird
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationIssue:
    """Representa um problema encontrado em um registro"""
    record_id: Optional[int]
    severity: str  # 'critical', 'warning', 'info'
    field: str
    issue: str
    current_value: str
    suggested_fix: Optional[str] = None
    record_identifier: Optional[str] = None  # Nome ou identificador do registro


@dataclass
class ValidationReport:
    """Relatório completo de validação"""
    total_records: int
    valid_records: int
    records_with_warnings: int
    records_with_errors: int
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    def has_critical_errors(self) -> bool:
        """Verifica se há erros críticos que impedem exportação"""
        return self.records_with_errors > 0
    
    def add_issue(self, issue: ValidationIssue):
        """Adiciona um problema ao relatório"""
        self.issues.append(issue)
        # Atualiza contador por tipo
        issue_type = f"{issue.severity}_{issue.field}"
        self.summary[issue_type] = self.summary.get(issue_type, 0) + 1


class ExportValidator:
    """Validador de registros BPA antes da exportação"""
    
    def __init__(self):
        # Campos obrigatórios
        self.required_fields = {
            'cnes': 'CNES',
            'competencia': 'Competência',
            'procedimento': 'Procedimento',
            'data_atendimento': 'Data de Atendimento',
            'cns_profissional': 'CNS do Profissional',
            'cbo': 'CBO',
            'nome_paciente': 'Nome do Paciente',
            'data_nascimento': 'Data de Nascimento',
            'sexo': 'Sexo',
        }
        
        # Campos recomendados (geram warning se vazios)
        self.recommended_fields = {
            'cid': 'CID',
            'municipio_ibge': 'Município (IBGE)',
            'bairro': 'Bairro',
        }
    
    def validate_record(self, record: Dict, record_index: int = 0) -> List[ValidationIssue]:
        """
        Valida um único registro
        
        Args:
            record: Dicionário com dados do registro
            record_index: Índice do registro (para identificação)
        
        Returns:
            Lista de problemas encontrados
        """
        issues = []
        record_id = record.get('id')
        identifier = record.get('nome_paciente', f'Registro #{record_index + 1}')
        
        # 1. Valida campos obrigatórios
        for field, name in self.required_fields.items():
            value = record.get(field)
            if not value or str(value).strip() == '':
                issues.append(ValidationIssue(
                    record_id=record_id,
                    severity='critical',
                    field=field,
                    issue=f'{name} é obrigatório',
                    current_value='',
                    suggested_fix='Preencher com valor válido',
                    record_identifier=identifier
                ))
        
        # 2. Valida CNS ou CPF do paciente (ao menos um)
        cns_paciente = record.get('cns_paciente', '')
        cpf_paciente = record.get('cpf_paciente', '')
        
        if not (cns_paciente and str(cns_paciente).strip()) and \
           not (cpf_paciente and str(cpf_paciente).strip()):
            issues.append(ValidationIssue(
                record_id=record_id,
                severity='critical',
                field='cns_paciente',
                issue='Paciente deve ter CNS ou CPF',
                current_value='Vazio',
                suggested_fix='Obter CNS ou CPF do paciente',
                record_identifier=identifier
            ))
        
        # 3. Valida formato de datas
        for date_field in ['data_atendimento', 'data_nascimento']:
            date_value = record.get(date_field)
            if date_value:
                if not self._is_valid_date(str(date_value)):
                    issues.append(ValidationIssue(
                        record_id=record_id,
                        severity='critical',
                        field=date_field,
                        issue=f'Data inválida',
                        current_value=str(date_value),
                        suggested_fix='Formato esperado: YYYYMMDD ou YYYY-MM-DD',
                        record_identifier=identifier
                    ))
        
        # 4. Valida campos recomendados
        for field, name in self.recommended_fields.items():
            value = record.get(field)
            if not value or str(value).strip() == '':
                issues.append(ValidationIssue(
                    record_id=record_id,
                    severity='warning',
                    field=field,
                    issue=f'{name} não preenchido',
                    current_value='',
                    suggested_fix=f'Recomendado preencher {name}',
                    record_identifier=identifier
                ))
        
        # 5. Valida procedimento válido
        procedimento = record.get('procedimento', '')
        if procedimento:
            if len(str(procedimento).strip()) != 10:
                issues.append(ValidationIssue(
                    record_id=record_id,
                    severity='warning',
                    field='procedimento',
                    issue='Procedimento deve ter 10 dígitos',
                    current_value=str(procedimento),
                    suggested_fix='Verificar código do procedimento',
                    record_identifier=identifier
                ))
        
        # 6. Valida sexo
        sexo = record.get('sexo', '')
        if sexo and str(sexo).upper() not in ('M', 'F'):
            issues.append(ValidationIssue(
                record_id=record_id,
                severity='warning',
                field='sexo',
                issue='Sexo deve ser M ou F',
                current_value=str(sexo),
                suggested_fix='Converter para M ou F',
                record_identifier=identifier
            ))
        
        return issues
    
    def validate_batch(self, records: List[Dict]) -> ValidationReport:
        """
        Valida um lote de registros
        
        Args:
            records: Lista de registros a validar
        
        Returns:
            Relatório completo de validação
        """
        report = ValidationReport(
            total_records=len(records),
            valid_records=0,
            records_with_warnings=0,
            records_with_errors=0
        )
        
        for idx, record in enumerate(records):
            issues = self.validate_record(record, idx)
            
            has_errors = any(i.severity == 'critical' for i in issues)
            has_warnings = any(i.severity == 'warning' for i in issues)
            
            if has_errors:
                report.records_with_errors += 1
            elif has_warnings:
                report.records_with_warnings += 1
            else:
                report.valid_records += 1
            
            # Adiciona problemas ao relatório
            for issue in issues:
                report.add_issue(issue)
        
        return report
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Valida se uma string é uma data válida"""
        if not date_str:
            return False
        
        # Remove hifens e espaços
        cleaned = date_str.replace('-', '').replace('/', '').strip()
        
        # Deve ter 8 dígitos
        if len(cleaned) != 8 or not cleaned.isdigit():
            return False
        
        try:
            # Tenta parsear a data
            year = int(cleaned[0:4])
            month = int(cleaned[4:6])
            day = int(cleaned[6:8])
            
            # Validações básicas
            if year < 1900 or year > 2100:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            
            # Tenta criar objeto datetime para validação completa
            datetime(year, month, day)
            return True
        except (ValueError, TypeError):
            return False
    
    def generate_summary_text(self, report: ValidationReport) -> str:
        """Gera texto resumido do relatório"""
        lines = []
        lines.append(f"Total de registros: {report.total_records}")
        lines.append(f"  ✅ Válidos: {report.valid_records}")
        lines.append(f"  ⚠️  Com avisos: {report.records_with_warnings}")
        lines.append(f"  ❌ Com erros: {report.records_with_errors}")
        
        if report.summary:
            lines.append("\nProblemas por tipo:")
            # Agrupa por campo
            by_field = {}
            for key, count in report.summary.items():
                severity, field = key.split('_', 1)
                if field not in by_field:
                    by_field[field] = {'critical': 0, 'warning': 0}
                by_field[field][severity] = count
            
            for field, counts in sorted(by_field.items()):
                if counts['critical'] > 0:
                    lines.append(f"  ❌ {field}: {counts['critical']} erros")
                if counts['warning'] > 0:
                    lines.append(f"  ⚠️  {field}: {counts['warning']} avisos")
        
        return '\n'.join(lines)


# Instância global
validator = ExportValidator()
