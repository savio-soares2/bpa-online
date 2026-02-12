import axios from 'axios';
import type { 
  Profissional, 
  Paciente, 
  Procedimento, 
  BPAIndividualizadoCreate,
  BPAIndividualizado,
  BPAStats,
  ExportRequest,
  ExportResponse,
  ExportFile
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para adicionar token em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para redirecionar ao login se 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/cadastro') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ========== AUTENTICAÇÃO ==========

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    nome: string;
    cbo?: string;
    cnes: string;
    nome_unidade?: string;
  };
}

interface RegisterData {
  email: string;
  senha: string;
  nome: string;
  cnes: string;
  nome_unidade?: string;
}

export const login = async (email: string, senha: string): Promise<LoginResponse> => {
  const response = await api.post('/auth/login', { email, senha });
  return response.data;
};

export const register = async (data: RegisterData): Promise<LoginResponse> => {
  const response = await api.post('/auth/register', data);
  return response.data;
};

export const getMe = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// ========== ADMIN ==========

export const adminListUsers = async () => {
  const response = await api.get('/admin/users');
  return response.data;
};

export const adminCreateUser = async (data: {
  email: string;
  senha: string;
  nome: string;
  cnes?: string;
  nome_unidade?: string;
  cbo: string;
}) => {
  const response = await api.post('/admin/users', data);
  return response.data;
};

export const adminToggleUser = async (userId: number, ativo: boolean) => {
  const response = await api.put(`/admin/users/${userId}/toggle?ativo=${ativo}`);
  return response.data;
};

export const adminDeleteUser = async (userId: number) => {
  const response = await api.delete(`/admin/users/${userId}`);
  return response.data;
};

export const adminResetPassword = async (userId: number, novaSenha: string) => {
  const response = await api.post(`/admin/users/${userId}/reset-password`, { nova_senha: novaSenha });
  return response.data;
};

export const adminUpdateUser = async (userId: number, data: {
  nome?: string;
  email?: string;
  cbo?: string;
  cnes?: string;
  nome_unidade?: string;
  ativo?: boolean;
}) => {
  const response = await api.put(`/admin/users/${userId}`, data);
  return response.data;
};

export const adminGetCBOs = async (query?: string, limit: number = 50) => {
  const params: any = { limit };
  if (query) {
    params.q = query;
  }
  const response = await api.get('/admin/cbos', { params });
  return response.data;
};

// ========== DASHBOARD ==========

export const getDashboardStats = async (cnes?: string) => {
  const params = cnes ? { cnes_filter: cnes } : {};
  const response = await api.get('/dashboard/stats', { params });
  return response.data;
};

// ========== EXPORTAÇÃO ==========

export const resetExportStatus = async (cnes: string, competencia: string, tipo: string = 'all') => {
  const response = await api.post('/export/reset', { cnes, competencia, tipo });
  return response.data;
};

// ========== PROFISSIONAIS ==========

export const getProfissional = async (cns: string): Promise<Profissional | null> => {
  try {
    const response = await api.get(`/profissionais/${cns}`);
    return response.data;
  } catch {
    return null;
  }
};

export const saveProfissional = async (data: Profissional): Promise<Profissional> => {
  const response = await api.post('/profissionais', data);
  return response.data;
};

export const listProfissionais = async (cnes?: string): Promise<Profissional[]> => {
  const params = cnes ? { cnes } : {};
  const response = await api.get('/profissionais', { params });
  return response.data;
};

// ========== PACIENTES ==========

export const getPaciente = async (cns: string): Promise<Paciente | null> => {
  try {
    const response = await api.get(`/pacientes/${cns}`);
    return response.data;
  } catch {
    return null;
  }
};

export const searchPacientes = async (termo: string): Promise<Paciente[]> => {
  const response = await api.get('/pacientes/search', { params: { q: termo } });
  return response.data;
};

export const savePaciente = async (data: Paciente): Promise<Paciente> => {
  const response = await api.post('/pacientes', data);
  return response.data;
};

// ========== PROCEDIMENTOS ==========

export const getProcedimento = async (codigo: string): Promise<Procedimento | null> => {
  try {
    const response = await api.get(`/procedimentos/${codigo}`);
    return response.data;
  } catch {
    return null;
  }
};

export const searchProcedimentos = async (termo: string): Promise<Procedimento[]> => {
  try {
    const response = await api.get('/procedures/search', { 
      params: { 
        q: termo, 
        my_only: true,
        limit: 50 
      } 
    });
    return response.data;
  } catch {
    return [];
  }
};

export const getUserProcedimentos = async (): Promise<Procedimento[]> => {
  try {
    const response = await api.get('/procedures/my-procedures');
    return response.data;
  } catch {
    return [];
  }
};

// ========== BPA INDIVIDUALIZADO ==========

export const listBPAIndividualizado = async (
  cnes: string, 
  competencia: string,
  exportado?: boolean
): Promise<BPAIndividualizado[]> => {
  const params: Record<string, string | boolean> = { cnes, competencia };
  if (exportado !== undefined) params.exportado = exportado;
  
  const response = await api.get('/bpa/individualizado', { params });
  return response.data;
};

export const getBPAIndividualizadoCount = async (
  cnes: string, 
  competencia: string
): Promise<BPAStats> => {
  const response = await api.get('/bpa/individualizado/count', { 
    params: { cnes, competencia } 
  });
  return response.data;
};

export const saveBPAIndividualizado = async (
  data: BPAIndividualizadoCreate
): Promise<BPAIndividualizado> => {
  const response = await api.post('/bpa/individualizado', data);
  return response.data;
};

export const deleteBPAIndividualizado = async (id: number): Promise<void> => {
  await api.delete(`/bpa/individualizado/${id}`);
};

// ========== EXPORTAÇÃO ==========

export const exportBPA = async (request: ExportRequest): Promise<ExportResponse> => {
  const response = await api.post('/export', request);
  return response.data;
};

export const listExports = async (): Promise<ExportFile[]> => {
  const response = await api.get('/export/list');
  return response.data;
};

export const getExportDownloadUrl = (filename: string): string => {
  return `${API_URL}/export/download/${filename}`;
};

// ========== ESTATÍSTICAS ==========

export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

// ========== REFERÊNCIAS ==========

export const getRacas = async () => {
  const response = await api.get('/referencias/raca-cor');
  return response.data;
};

export const getSexos = async () => {
  const response = await api.get('/referencias/sexo');
  return response.data;
};

export const getCaraterAtendimento = async () => {
  const response = await api.get('/referencias/carater-atendimento');
  return response.data;
};

// ========== JULIA API ==========

interface JuliaConfig {
  url_base: string;
  usuario: string;
  senha: string;
  unidade_saude_id: string;
}

interface JuliaConnectionResult {
  success: boolean;
  error?: string;
}

interface JuliaImportRequest extends JuliaConfig {
  competencia: string;
}

interface JuliaImportResult {
  success: boolean;
  total_importado: number;
  bpai_importado: number;
  bpac_importado: number;
  erros: string[];
}

export const checkJuliaConnection = async (config: JuliaConfig): Promise<JuliaConnectionResult> => {
  try {
    const response = await api.post('/julia/check-connection', config);
    return response.data;
  } catch (error) {
    return { success: false, error: 'Erro ao conectar' };
  }
};

export const importFromJulia = async (request: JuliaImportRequest): Promise<JuliaImportResult> => {
  const response = await api.post('/julia/import', request);
  return response.data;
};

// ========== BPA STATS ==========

export const getBPAStats = async (cnes: string, competencia: string): Promise<BPAStats> => {
  const response = await api.get('/bpa/stats', { params: { cnes, competencia } });
  return response.data;
};

export default api;
