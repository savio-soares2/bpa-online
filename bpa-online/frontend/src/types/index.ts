// ========== REFERÊNCIAS ==========

export interface Raca {
  codigo: string;
  descricao: string;
}

export interface Sexo {
  codigo: string;
  descricao: string;
}

export interface CaraterAtendimento {
  codigo: string;
  descricao: string;
}

export const RACAS: Raca[] = [
  { codigo: '01', descricao: 'Branca' },
  { codigo: '02', descricao: 'Preta' },
  { codigo: '03', descricao: 'Parda' },
  { codigo: '04', descricao: 'Amarela' },
  { codigo: '05', descricao: 'Indígena' },
  { codigo: '99', descricao: 'Sem informação' }
];

export const SEXOS: Sexo[] = [
  { codigo: 'M', descricao: 'Masculino' },
  { codigo: 'F', descricao: 'Feminino' }
];

export const CARATER_ATENDIMENTO: CaraterAtendimento[] = [
  { codigo: '01', descricao: 'Eletivo' },
  { codigo: '02', descricao: 'Urgência' },
  { codigo: '03', descricao: 'Acidente no local de trabalho' },
  { codigo: '04', descricao: 'Acidente no trajeto' },
  { codigo: '05', descricao: 'Outros acidentes' },
  { codigo: '06', descricao: 'Outros' }
];

// ========== PROFISSIONAL ==========

export interface Profissional {
  id?: number;
  cns: string;
  nome?: string;
  cbo?: string;
  cnes?: string;
  ine?: string;
}

// ========== PACIENTE ==========

export interface Paciente {
  id?: number;
  cns: string;
  cpf?: string;
  nome: string;
  data_nascimento?: string;
  sexo?: string;
  raca_cor?: string;
  nacionalidade?: string;
  municipio_ibge?: string;
  cep?: string;
  logradouro_codigo?: string;
  endereco?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  telefone?: string;
  email?: string;
}

// ========== PROCEDIMENTO ==========

export interface Procedimento {
  codigo: string;
  descricao?: string;
  valor?: number;
}

// ========== BPA INDIVIDUALIZADO ==========

export interface BPACabecalho {
  cnes: string;
  cns_profissional: string;
  nome_profissional: string;
  cbo: string;
  ine: string;
  competencia: string;
  folha: number;
}

export interface BPARegistro {
  // Paciente
  cns_paciente: string;
  cpf_paciente: string;
  nome_paciente: string;
  data_nascimento: string;
  sexo: string;
  raca_cor: string;
  nacionalidade: string;
  municipio_ibge: string;
  cep: string;
  logradouro_codigo: string;
  endereco: string;
  numero: string;
  complemento: string;
  bairro: string;
  telefone: string;
  email: string;
  // Procedimento
  data_atendimento: string;
  procedimento: string;
  procedimento_descricao: string;
  quantidade: number;
  cid: string;
  carater_atendimento: string;
  numero_autorizacao: string;
  cnpj: string;
  servico: string;
  classificacao: string;
}

export interface BPAIndividualizado extends BPACabecalho, BPARegistro {
  id?: number;
  exportado?: boolean;
  created_at?: string;
}

export interface BPAIndividualizadoCreate {
  cnes: string;
  competencia: string;
  folha?: number;
  sequencia?: number;
  cns_profissional: string;
  cbo: string;
  ine?: string;
  cns_paciente: string;
  cpf_paciente?: string;
  nome_paciente: string;
  data_nascimento: string;
  sexo: string;
  raca_cor: string;
  nacionalidade?: string;
  municipio_ibge: string;
  cep?: string;
  logradouro_codigo?: string;
  endereco?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  telefone?: string;
  email?: string;
  data_atendimento: string;
  procedimento: string;
  quantidade?: number;
  cid?: string;
  carater_atendimento?: string;
  numero_autorizacao?: string;
  cnpj?: string;
  servico?: string;
  classificacao?: string;
}

// ========== BPA CONSOLIDADO ==========

export interface BPAConsolidado {
  id?: number;
  cnes: string;
  competencia: string;
  cns_profissional: string;
  cbo: string;
  procedimento: string;
  idade: string;
  quantidade: number;
  exportado?: boolean;
}

// ========== EXPORTAÇÃO ==========

export interface ExportRequest {
  cnes: string;
  competencia: string;
  tipo: 'individualizado' | 'consolidado' | 'all';
}

export interface ExportResponse {
  status: string;
  message: string;
  total_registros: number;
  arquivo: string;
  download_url?: string;
}

export interface ExportFile {
  arquivo: string;
  cnes: string;
  competencia: string;
  tipo: string;
  total_registros: number;
  data_exportacao: string;
}

// ========== ESTATÍSTICAS ==========

export interface BPAStats {
  bpai_total: number;
  bpai_pendente: number;
  bpai_exportado: number;
  bpac_total: number;
  bpac_pendente: number;
  bpac_exportado: number;
}

export interface DashboardStats {
  total_bpai: number;
  total_bpac: number;
  total_profissionais: number;
  total_pacientes: number;
  competencias: string[];
  cnes_list: string[];
}

// ========== API RESPONSES ==========

export interface ApiResponse<T> {
  status: string;
  message: string;
  data?: T;
}

export interface Message {
  type: 'success' | 'error' | 'warning' | 'info';
  text: string;
}
