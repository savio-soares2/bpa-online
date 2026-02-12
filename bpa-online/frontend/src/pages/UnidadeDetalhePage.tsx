import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Building2,
    Users,
    UserCheck,
    Plus,
    Trash2,
    ArrowLeft,
    Search,
    X,
    Save,
    BarChart3,
    Mail,
    Shield
} from 'lucide-react';
import { getEstabelecimentoByCnes, Estabelecimento } from '../constants/estabelecimentos';
import { listProfissionais, createProfissional, deleteProfissional, Profissional } from '../services/adminService';
import api from '../services/api';

type TabType = 'profissionais' | 'usuarios' | 'estatisticas';

interface Usuario {
    id: number;
    email: string;
    nome: string;
    cbo?: string;
    is_admin: boolean;
    ativo: boolean;
}

const UnidadeDetalhePage: React.FC = () => {
    const { cnes } = useParams<{ cnes: string }>();
    const navigate = useNavigate();

    const [activeTab, setActiveTab] = useState<TabType>('profissionais');
    const [unidade, setUnidade] = useState<Estabelecimento | null>(null);

    // Profissionais
    const [profissionais, setProfissionais] = useState<Profissional[]>([]);
    const [loadingProfs, setLoadingProfs] = useState(true);
    const [showProfModal, setShowProfModal] = useState(false);
    const [searchProf, setSearchProf] = useState('');
    const [profForm, setProfForm] = useState<Partial<Profissional>>({
        cns: '', nome: '', cbo: '', conselho: '', uf_conselho: ''
    });

    // Usuários
    const [usuarios, setUsuarios] = useState<Usuario[]>([]);
    const [loadingUsers, setLoadingUsers] = useState(true);

    useEffect(() => {
        if (cnes) {
            const est = getEstabelecimentoByCnes(cnes);
            setUnidade(est || null);
            loadProfissionais();
            loadUsuarios();
        }
    }, [cnes]);

    const loadProfissionais = async () => {
        if (!cnes) return;
        setLoadingProfs(true);
        try {
            const data = await listProfissionais(cnes);
            setProfissionais(data);
        } catch (error) {
            console.error('Erro ao carregar profissionais:', error);
        } finally {
            setLoadingProfs(false);
        }
    };

    const loadUsuarios = async () => {
        if (!cnes) return;
        setLoadingUsers(true);
        try {
            const response = await api.get(`/admin/unidades/${cnes}/usuarios`);
            setUsuarios(response.data);
        } catch (error) {
            console.error('Erro ao carregar usuários:', error);
        } finally {
            setLoadingUsers(false);
        }
    };

    const handleCreateProfissional = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!cnes) return;

        try {
            await createProfissional({
                ...profForm,
                cnes
            } as Profissional);
            setShowProfModal(false);
            setProfForm({ cns: '', nome: '', cbo: '', conselho: '', uf_conselho: '' });
            loadProfissionais();
        } catch (error) {
            alert('Erro ao salvar profissional. Verifique o CNS.');
        }
    };

    const handleDeleteProfissional = async (id: number) => {
        if (!window.confirm('Tem certeza que deseja remover este profissional?')) return;
        try {
            await deleteProfissional(id);
            loadProfissionais();
        } catch (error) {
            alert('Erro ao remover profissional.');
        }
    };

    const filteredProfs = profissionais.filter(p =>
        p.nome.toLowerCase().includes(searchProf.toLowerCase()) ||
        p.cns.includes(searchProf) ||
        p.cbo.includes(searchProf)
    );

    if (!unidade) {
        return (
            <div className="p-6 max-w-7xl mx-auto">
                <div className="text-center py-12">
                    <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">Unidade não encontrada (CNES: {cnes})</p>
                    <button
                        onClick={() => navigate('/admin/unidades')}
                        className="mt-4 text-primary-600 hover:underline"
                    >
                        Voltar para lista
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-7xl mx-auto animate-fadeIn">
            {/* Header com navegação */}
            <div className="mb-6">
                <button
                    onClick={() => navigate('/admin/unidades')}
                    className="flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-4 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Voltar para Unidades
                </button>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-4 bg-primary-100 rounded-xl">
                                <Building2 className="w-8 h-8 text-primary-600" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-800">{unidade.sigla}</h1>
                                <p className="text-gray-500">{unidade.nome}</p>
                                <div className="flex items-center gap-2 mt-2">
                                    <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                        CNES: {unidade.cnes}
                                    </span>
                                    <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded capitalize">
                                        {unidade.tipo.replace('_', ' ').toLowerCase()}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Stats rápidas */}
                        <div className="flex gap-4">
                            <div className="text-center">
                                <p className="text-2xl font-bold text-green-600">{profissionais.length}</p>
                                <p className="text-xs text-gray-500">Profissionais</p>
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold text-blue-600">{usuarios.length}</p>
                                <p className="text-xs text-gray-500">Usuários</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
                <button
                    onClick={() => setActiveTab('profissionais')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'profissionais'
                        ? 'bg-white text-primary-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-800'
                        }`}
                >
                    <UserCheck className="w-4 h-4" />
                    Profissionais
                </button>
                <button
                    onClick={() => setActiveTab('usuarios')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'usuarios'
                        ? 'bg-white text-primary-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-800'
                        }`}
                >
                    <Users className="w-4 h-4" />
                    Usuários do Sistema
                </button>
                <button
                    onClick={() => setActiveTab('estatisticas')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'estatisticas'
                        ? 'bg-white text-primary-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-800'
                        }`}
                >
                    <BarChart3 className="w-4 h-4" />
                    Estatísticas
                </button>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                {/* PROFISSIONAIS TAB */}
                {activeTab === 'profissionais' && (
                    <div>
                        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Buscar por nome, CNS ou CBO..."
                                    value={searchProf}
                                    onChange={e => setSearchProf(e.target.value)}
                                    className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                                />
                            </div>
                            <button
                                onClick={() => setShowProfModal(true)}
                                className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition ml-4"
                            >
                                <Plus className="w-4 h-4" />
                                Novo Profissional
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-gray-50 text-gray-700 font-medium">
                                    <tr>
                                        <th className="px-4 py-3">Nome</th>
                                        <th className="px-4 py-3">CNS</th>
                                        <th className="px-4 py-3">CBO</th>
                                        <th className="px-4 py-3">Conselho</th>
                                        <th className="px-4 py-3 text-right">Ações</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {loadingProfs ? (
                                        <tr><td colSpan={5} className="text-center py-8 text-gray-500">Carregando...</td></tr>
                                    ) : filteredProfs.length === 0 ? (
                                        <tr><td colSpan={5} className="text-center py-8 text-gray-500">
                                            Nenhum profissional encontrado. Cadastre o primeiro!
                                        </td></tr>
                                    ) : (
                                        filteredProfs.map(prof => (
                                            <tr key={prof.id} className="hover:bg-gray-50">
                                                <td className="px-4 py-3 font-medium">{prof.nome}</td>
                                                <td className="px-4 py-3 font-mono text-sm">{prof.cns}</td>
                                                <td className="px-4 py-3">{prof.cbo}</td>
                                                <td className="px-4 py-3">{prof.conselho} {prof.uf_conselho && `/${prof.uf_conselho}`}</td>
                                                <td className="px-4 py-3 text-right">
                                                    <button
                                                        onClick={() => handleDeleteProfissional(prof.id!)}
                                                        className="text-red-500 hover:text-red-700 p-1"
                                                        title="Remover"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* USUÁRIOS TAB */}
                {activeTab === 'usuarios' && (
                    <div className="p-6">
                        {loadingUsers ? (
                            <div className="text-center py-8 text-gray-500">Carregando...</div>
                        ) : usuarios.length === 0 ? (
                            <div className="text-center py-12">
                                <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                <p className="text-gray-500 mb-4">Nenhum usuário vinculado a esta unidade</p>
                                <button
                                    onClick={() => navigate('/admin/usuarios')}
                                    className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                                >
                                    <Plus className="w-4 h-4" />
                                    Criar Usuário para esta Unidade
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {usuarios.map(user => (
                                    <div key={user.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${user.is_admin ? 'bg-purple-100' : 'bg-blue-100'}`}>
                                                {user.is_admin ? <Shield className="w-5 h-5 text-purple-600" /> : <Users className="w-5 h-5 text-blue-600" />}
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-800">{user.nome}</p>
                                                <p className="text-sm text-gray-500 flex items-center gap-1">
                                                    <Mail className="w-3 h-3" />
                                                    {user.email}
                                                </p>
                                            </div>
                                        </div>
                                        <span className={`px-2 py-1 text-xs rounded-full ${user.ativo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {user.ativo ? 'Ativo' : 'Inativo'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* ESTATÍSTICAS TAB */}
                {activeTab === 'estatisticas' && (
                    <div className="p-6 text-center py-12">
                        <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">Estatísticas da unidade em desenvolvimento</p>
                        <p className="text-sm text-gray-400 mt-2">Em breve: gráficos de produção, atendimentos e tendências</p>
                    </div>
                )}
            </div>

            {/* Modal Novo Profissional */}
            {showProfModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold">Cadastrar Profissional</h2>
                            <button onClick={() => setShowProfModal(false)}>
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>

                        <form onSubmit={handleCreateProfissional} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">CNS</label>
                                <input
                                    required
                                    maxLength={15}
                                    value={profForm.cns}
                                    onChange={e => setProfForm({ ...profForm, cns: e.target.value })}
                                    className="w-full mt-1 p-2 border rounded-lg"
                                    placeholder="700..."
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nome Completo</label>
                                <input
                                    required
                                    value={profForm.nome}
                                    onChange={e => setProfForm({ ...profForm, nome: e.target.value })}
                                    className="w-full mt-1 p-2 border rounded-lg uppercase"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">CBO</label>
                                <input
                                    required
                                    maxLength={6}
                                    value={profForm.cbo}
                                    onChange={e => setProfForm({ ...profForm, cbo: e.target.value })}
                                    className="w-full mt-1 p-2 border rounded-lg"
                                    placeholder="Ex: 225125"
                                />
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700">Nº Conselho</label>
                                    <input
                                        value={profForm.conselho}
                                        onChange={e => setProfForm({ ...profForm, conselho: e.target.value })}
                                        className="w-full mt-1 p-2 border rounded-lg"
                                        placeholder="CRM 1234"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">UF</label>
                                    <input
                                        maxLength={2}
                                        value={profForm.uf_conselho}
                                        onChange={e => setProfForm({ ...profForm, uf_conselho: e.target.value.toUpperCase() })}
                                        className="w-full mt-1 p-2 border rounded-lg uppercase"
                                        placeholder="TO"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowProfModal(false)}
                                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                                >
                                    <Save className="w-4 h-4" />
                                    Salvar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UnidadeDetalhePage;
