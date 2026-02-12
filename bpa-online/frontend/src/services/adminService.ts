import api from './api';

export interface Profissional {
    id?: number;
    cnes: string;
    cns: string;
    nome: string;
    cbo: string;
    ine?: string;
    conselho?: string;
    uf_conselho?: string;
}

export interface CboSummary {
    cbo: string;
    total: number;
}

export const listProfissionais = async (cnes: string): Promise<Profissional[]> => {
    const response = await api.get('/admin/profissionais', { params: { cnes } });
    return response.data;
};

export const createProfissional = async (data: Profissional): Promise<Profissional> => {
    const response = await api.post('/admin/profissionais', data);
    return response.data;
};

export const deleteProfissional = async (id: number): Promise<void> => {
    await api.delete(`/admin/profissionais/${id}`);
};

export const listCbosUnidade = async (cnes: string): Promise<CboSummary[]> => {
    const response = await api.get('/admin/cbos', { params: { cnes } });
    return response.data;
}
