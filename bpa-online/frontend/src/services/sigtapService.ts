import api from './api';

export interface SigtapCompetencia {
    competencia: string;
    created_at: string;
    path: string;
}

export interface SigtapCompetenciaResponse {
    active: string | null;
    available: SigtapCompetencia[];
}

export interface SigtapProcedimento {
    CO_PROCEDIMENTO: string;
    NO_PROCEDIMENTO: string;
    VL_SH: string;
    VL_SA: string;
    VL_SP: string;
    TP_COMPLEXIDADE?: string;
    TP_FINANCIAMENTO?: string;
    REGISTROS?: string[]; // Lista de códigos de registro permitidos
}

export interface SigtapSearchFilters {
    q?: string;
    page?: number;
    limit?: number;
    cbo?: string;
    servico?: string;
    classificacao?: string;
    tipo_registro?: string[]; // Agora array
    competencia?: string;
    sort_field?: 'nome' | 'valor' | 'codigo';
    sort_order?: 'asc' | 'desc';
}

export interface SigtapSearchResponse {
    data: SigtapProcedimento[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export interface SigtapStats {
    competencia: string;
    total_procedimentos: number;
    total_cbos: number;
    total_servicos: number;
    total_instrumentos: number;
    total_relacoes_cbo: number;
    total_relacoes_servico: number;
    total_relacoes_registro: number;
}

export interface SigtapRegistro {
    CO_REGISTRO: string;
    NO_REGISTRO: string;
}

export const listCompetencias = async (): Promise<SigtapCompetenciaResponse> => {
    const response = await api.get('/sigtap/competencias');
    return response.data;
};

export const uploadCompetencia = async (file: File, competencia: string): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('competencia', competencia);

    const response = await api.post('/sigtap/competencias', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const activateCompetencia = async (competencia: string): Promise<any> => {
    const response = await api.put(`/sigtap/competencias/${competencia}/activate`);
    return response.data;
};

export const searchProcedimentos = async (filters: SigtapSearchFilters): Promise<SigtapSearchResponse> => {
    // Axios array serialization para tipo_registro=v1&tipo_registro=v2
    const params = new URLSearchParams();
    if (filters.q) params.append('q', filters.q);
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.cbo) params.append('cbo', filters.cbo);
    if (filters.servico) params.append('servico', filters.servico);

    if (filters.tipo_registro && filters.tipo_registro.length > 0) {
        filters.tipo_registro.forEach(r => params.append('tipo_registro', r));
    }

    if (filters.sort_field) params.append('sort_field', filters.sort_field);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);

    const response = await api.get('/sigtap/procedimentos', { params });
    return response.data;
};

export const getSigtapStats = async (competencia?: string): Promise<SigtapStats> => {
    const params = competencia ? { competencia } : {};
    const response = await api.get('/sigtap/estatisticas', { params });
    return response.data;
};

export const listRegistros = async (): Promise<SigtapRegistro[]> => {
    const response = await api.get('/sigtap/registros');
    return response.data;
}
