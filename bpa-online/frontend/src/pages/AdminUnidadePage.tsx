import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
    Users, Plus, Trash2, Save, X, Search
} from 'lucide-react';
import { listProfissionais, createProfissional, deleteProfissional, Profissional } from '../services/adminService';

const AdminUnidadePage: React.FC = () => {
    const { user } = useAuth();
    const [profissionais, setProfissionais] = useState<Profissional[]>([]);
    const [loading, setLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    // Form State
    const [formData, setFormData] = useState<Partial<Profissional>>({
        cns: '',
        nome: '',
        cbo: '',
        conselho: '',
        uf_conselho: '' // Default UF do user?
    });

    useEffect(() => {
        if (user?.cnes) {
            loadProfissionais();
        }
    }, [user?.cnes]);

    const loadProfissionais = async () => {
        if (!user?.cnes) return;
        setLoading(true);
        try {
            const data = await listProfissionais(user.cnes);
            setProfissionais(data);
        } catch (error) {
            console.error('Erro ao listar profissionais', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user?.cnes) return;
        try {
            await createProfissional({
                ...formData,
                cnes: user.cnes
            } as Profissional);
            setShowModal(false);
            setFormData({ cns: '', nome: '', cbo: '', conselho: '', uf_conselho: '' });
            loadProfissionais();
        } catch (error) {
            alert('Erro ao salvar profissional. Verifique o CNS.');
        }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm('Tem certeza que deseja remover este profissional?')) return;
        try {
            await deleteProfissional(id);
            loadProfissionais();
        } catch (error) {
            console.error(error);
            alert('Erro ao remover.');
        }
    };

    const filteredProfs = profissionais.filter(p =>
        p.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.cns.includes(searchTerm) ||
        p.cbo.includes(searchTerm)
    );

    return (
        <div className="space-y-6 animate-fadeIn">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">Gestão da Unidade</h1>
                        <p className="text-gray-500">CNES: {user?.cnes} - {user?.nome_unidade}</p>
                    </div>
                    <button
                        onClick={() => setShowModal(true)}
                        className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition"
                    >
                        <Plus className="w-4 h-4" />
                        Novo Profissional
                    </button>
                </div>

                {/* Search */}
                <div className="relative mb-4">
                    <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Buscar profissional por nome, CNS ou CBO..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    />
                </div>

                {/* Table */}
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
                            {loading ? (
                                <tr><td colSpan={5} className="text-center py-4">Carregando...</td></tr>
                            ) : filteredProfs.length === 0 ? (
                                <tr><td colSpan={5} className="text-center py-4 text-gray-500">Nenhum profissional encontrado. Cadastre o primeiro!</td></tr>
                            ) : (
                                filteredProfs.map(prof => (
                                    <tr key={prof.id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3">{prof.nome}</td>
                                        <td className="px-4 py-3 font-mono text-sm">{prof.cns}</td>
                                        <td className="px-4 py-3">{prof.cbo}</td>
                                        <td className="px-4 py-3">{prof.conselho} {prof.uf_conselho && `/${prof.uf_conselho}`}</td>
                                        <td className="px-4 py-3 text-right">
                                            <button
                                                onClick={() => handleDelete(prof.id!)}
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

            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold">Cadastrar Profissional</h2>
                            <button onClick={() => setShowModal(false)}><X className="w-5 h-5 text-gray-500" /></button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">CNS</label>
                                <input
                                    required
                                    maxLength={15}
                                    value={formData.cns}
                                    onChange={e => setFormData({ ...formData, cns: e.target.value })}
                                    className="w-full mt-1 p-2 border rounded"
                                    placeholder="700..."
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nome Completo</label>
                                <input
                                    required
                                    value={formData.nome}
                                    onChange={e => setFormData({ ...formData, nome: e.target.value })}
                                    className="w-full mt-1 p-2 border rounded uppercase"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">CBO</label>
                                <input
                                    required
                                    maxLength={6}
                                    value={formData.cbo}
                                    onChange={e => setFormData({ ...formData, cbo: e.target.value })}
                                    className="w-full mt-1 p-2 border rounded"
                                    placeholder="Ex: 225125"
                                />
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700">Nº Conselho</label>
                                    <input
                                        value={formData.conselho}
                                        onChange={e => setFormData({ ...formData, conselho: e.target.value })}
                                        className="w-full mt-1 p-2 border rounded"
                                        placeholder="CRM 1234"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">UF</label>
                                    <input
                                        maxLength={2}
                                        value={formData.uf_conselho}
                                        onChange={e => setFormData({ ...formData, uf_conselho: e.target.value.toUpperCase() })}
                                        className="w-full mt-1 p-2 border rounded uppercase"
                                        placeholder="TO"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                                >
                                    Salvar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminUnidadePage;
