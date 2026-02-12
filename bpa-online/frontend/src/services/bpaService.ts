import api from './api';

export interface BPAConsolidado {
    id?: number;
    cnes: string;
    competencia: string;
    cns_profissional?: string; // Opcional
    cbo: string;
    procedimento: string;
    idade: string;
    quantidade: number;
    exportado?: boolean;
}

export interface BPAIndividualizado {
    id?: number;
    cnes: string;
    competencia: string;
    cns_profissional: string;
    cbo: string;
    cns_paciente: string;
    nome_paciente: string;
    data_nascimento: string;
    sexo: string;
    procedimento: string;
    data_atendimento: string;
    quantidade: number;
    exportado?: boolean;
    // ... outros campos ...
}

export const listBPAConsolidado = async (competencia: string): Promise<BPAConsolidado[]> => {
    const response = await api.get('/bpa/consolidado', { params: { competencia } });
    return response.data;
};

export const createBPAConsolidado = async (data: Omit<BPAConsolidado, 'id' | 'cnes' | 'exportado'>): Promise<BPAConsolidado> => {
    const response = await api.post('/bpa/consolidado', data);
    return response.data;
};

export const deleteBPAConsolidado = async (id: number): Promise<void> => {
    // TODO: Implementar delete no backend se não existir
    // await api.delete(`/bpa/consolidado/${id}`);
};
