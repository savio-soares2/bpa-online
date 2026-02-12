from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class ExtractionMode(str, Enum):
    TEST = "TEST"
    ESUS = "ESUS"

class ExtractionRequest(BaseModel):
    """Requisição de extração de dados"""
    cnes_list: List[str] = Field(..., description="Lista de códigos CNES")
    competencia_inicial: str = Field(..., description="Competência inicial (YYYY-MM)")
    competencia_final: str = Field(..., description="Competência final (YYYY-MM)")
    mode: ExtractionMode = Field(default=ExtractionMode.TEST, description="Modo de extração")

class ExtractionResponse(BaseModel):
    """Resposta de extração iniciada"""
    task_id: str
    status: str
    message: str

class ProcessStatus(BaseModel):
    """Status de processamento"""
    task_id: str
    status: str
    progress: int
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    errors: List[str] = []

class CNESInfo(BaseModel):
    """Informações sobre um CNES"""
    cnes: str
    nome: Optional[str] = None
    total_registros: int = 0
    competencias: List[str] = []
    ultima_atualizacao: Optional[str] = None

class DashboardStats(BaseModel):
    """Estatísticas do dashboard"""
    total_cnes: int = 0
    total_registros: int = 0
    tarefas_ativas: int = 0
    tarefas_completas: int = 0
    tarefas_com_erro: int = 0
    ultima_extracao: Optional[datetime] = None
    cnes_disponiveis: List[str] = []

class FirebirdImportRequest(BaseModel):
    """Requisição de importação para Firebird"""
    task_id: str
    firebird_config: Optional[Dict[str, Any]] = None

class FirebirdImportResponse(BaseModel):
    """Resposta da importação Firebird"""
    status: str
    message: str
    total_records: int = 0
    imported: int = 0
    errors: int = 0
    error_messages: List[str] = []

class FirebirdConfigRequest(BaseModel):
    """Configuração do Firebird"""
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    charset: Optional[str] = None


# ========== NOVOS SCHEMAS PARA FORMULÁRIO BPA ==========

class ProfissionalCreate(BaseModel):
    """Cadastro de profissional"""
    cns: str = Field(..., min_length=15, max_length=15, description="CNS do profissional")
    nome: Optional[str] = Field(None, max_length=100)
    cbo: Optional[str] = Field(None, max_length=6)
    cnes: Optional[str] = Field(None, max_length=7)
    ine: Optional[str] = Field(None, max_length=10)
    conselho: Optional[str] = Field(None, max_length=20)
    uf_conselho: Optional[str] = Field(None, max_length=2)

class ProfissionalResponse(BaseModel):
    """Resposta de profissional"""
    id: int
    cns: str
    nome: Optional[str] = None
    cbo: Optional[str] = None
    cnes: Optional[str] = None
    ine: Optional[str] = None
    conselho: Optional[str] = None
    uf_conselho: Optional[str] = None

class PacienteCreate(BaseModel):
    """Cadastro de paciente"""
    cns: str = Field(..., min_length=15, max_length=15)
    cpf: Optional[str] = Field(None, max_length=11)
    nome: str = Field(..., max_length=100)
    data_nascimento: str
    sexo: str = Field(..., max_length=1)
    raca_cor: str = Field(..., max_length=2)
    nacionalidade: str = Field(default="010", max_length=3)
    municipio_ibge: str = Field(..., max_length=6)
    cep: Optional[str] = Field(None, max_length=8)
    logradouro_codigo: Optional[str] = Field(None, max_length=10)
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)

class PacienteResponse(BaseModel):
    """Resposta de paciente"""
    id: int
    cns: str
    cpf: Optional[str] = None
    nome: str
    data_nascimento: Optional[str] = None
    sexo: Optional[str] = None
    raca_cor: Optional[str] = None
    municipio_ibge: Optional[str] = None

class BPAIndividualizadoCreate(BaseModel):
    """Cadastro de BPA Individualizado"""
    # Identificação
    cnes: str = Field(..., max_length=7)
    competencia: str = Field(..., max_length=6, description="YYYYMM")
    folha: int = Field(default=1)
    sequencia: int = Field(default=1)
    
    # Profissional
    cns_profissional: str = Field(..., max_length=15)
    cbo: str = Field(..., max_length=6)
    ine: Optional[str] = Field(None, max_length=10)
    
    # Paciente
    cns_paciente: str = Field(..., max_length=15)
    cpf_paciente: Optional[str] = Field(None, max_length=11)
    nome_paciente: str = Field(..., max_length=30)
    data_nascimento: str
    sexo: str = Field(..., max_length=1)
    raca_cor: str = Field(..., max_length=2)
    nacionalidade: str = Field(default="010", max_length=3)
    municipio_ibge: str = Field(..., max_length=6)
    
    # Endereço (opcional)
    cep: Optional[str] = Field(None, max_length=8)
    logradouro_codigo: Optional[str] = Field(None, max_length=10)
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    # Procedimento
    data_atendimento: str
    procedimento: str = Field(..., max_length=10)
    quantidade: int = Field(default=1)
    cid: Optional[str] = Field(None, max_length=4)
    carater_atendimento: str = Field(default="01", max_length=2)
    numero_autorizacao: Optional[str] = Field(None, max_length=13)
    
    # Serviço
    cnpj: Optional[str] = Field(None, max_length=14)
    servico: Optional[str] = Field(None, max_length=3)
    classificacao: Optional[str] = Field(None, max_length=3)
    
    class Config:
        json_schema_extra = {
            "example": {
                "cnes": "6061478",
                "competencia": "202511",
                "cns_profissional": "700001016250104",
                "cbo": "223505",
                "cns_paciente": "700501926845056",
                "nome_paciente": "JOAO DA SILVA",
                "data_nascimento": "1976-03-03",
                "sexo": "M",
                "raca_cor": "01",
                "municipio_ibge": "172100",
                "data_atendimento": "2025-11-21",
                "procedimento": "0301010048",
                "quantidade": 1,
                "carater_atendimento": "01"
            }
        }

class BPAIndividualizadoResponse(BaseModel):
    """Resposta de BPA-I"""
    id: int
    cnes: str
    competencia: str
    cns_profissional: str
    cbo: str
    cns_paciente: str
    nome_paciente: str
    data_nascimento: Optional[str] = None
    sexo: str
    procedimento: str
    data_atendimento: Optional[str] = None
    quantidade: int
    exportado: bool = False
    created_at: Optional[str] = None

class BPAConsolidadoCreate(BaseModel):
    """Cadastro de BPA Consolidado"""
    cnes: str = Field(..., max_length=7)
    competencia: str = Field(..., max_length=6)
    competencia: str = Field(..., max_length=6)
    cns_profissional: Optional[str] = Field(None, max_length=15)
    cbo: str = Field(..., max_length=6)
    cbo: str = Field(..., max_length=6)
    procedimento: str = Field(..., max_length=10)
    idade: str = Field(default="999", max_length=3)
    quantidade: int = Field(..., gt=0)

class BPAConsolidadoResponse(BaseModel):
    """Resposta de BPA-C"""
    id: int
    cnes: str
    competencia: str
    competencia: str
    cns_profissional: Optional[str] = None
    cbo: str
    cbo: str
    procedimento: str
    idade: str
    quantidade: int
    exportado: bool = False

class ExportRequest(BaseModel):
    """Requisição de exportação"""
    cnes: str = Field(..., max_length=7)
    competencia: str = Field(..., max_length=6)
    tipo: str = Field(default="BPA-I", description="BPA-I, BPA-C ou TODOS")
    apenas_nao_exportados: bool = Field(default=True)

class ExportResponse(BaseModel):
    """Resposta de exportação"""
    status: str
    message: str
    total: int = 0
    filename: Optional[str] = None
    download_url: Optional[str] = None
    # Campos extras para compatibilidade com frontend
    total_registros: int = 0
    arquivo: Optional[str] = None
    filepath: Optional[str] = None
    correction_stats: Optional[Dict[str, Any]] = None
    bpai_count: int = 0
    bpac_count: int = 0
    
    class Config:
        extra = "allow"  # Permite campos extras

class ProcedimentoResponse(BaseModel):
    """Procedimento do SIGTAP"""
    codigo: str
    descricao: Optional[str] = None
    valor: float = 0.0

class JuliaImportRequest(BaseModel):
    """Requisição de importação da API Julia"""
    tipo: str = Field(..., description="BPA-I ou BPA-C")
    cnes: str
    competencia: str
    registros: List[Dict[str, Any]]

class JuliaImportResponse(BaseModel):
    """Resposta da importação Julia"""
    status: str
    message: str
    total_recebidos: int = 0
    total_importados: int = 0
    erros: List[str] = []

class BPAStatsResponse(BaseModel):
    """Estatísticas do BPA"""
    total_bpai: int = 0
    total_bpac: int = 0
    total_profissionais: int = 0
    total_pacientes: int = 0
    competencias: List[str] = []
    cnes_list: List[str] = []

