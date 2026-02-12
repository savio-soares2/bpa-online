import React, { useState, useEffect } from 'react';
import { Upload, Check, Calendar, AlertCircle, PlayCircle, Loader2 } from 'lucide-react';
import {
    listCompetencias,
    uploadCompetencia,
    activateCompetencia,
    SigtapCompetencia
} from '../../services/sigtapService';

const SigtapManager: React.FC = () => {
    const [competencias, setCompetencias] = useState<SigtapCompetencia[]>([]);
    const [activeCompetencia, setActiveCompetencia] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Upload state
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [newCompetencia, setNewCompetencia] = useState('');
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchCompetencias = async () => {
        setLoading(true);
        try {
            const res = await listCompetencias();
            setCompetencias(res.available);
            setActiveCompetencia(res.active);
        } catch (err) {
            setError('Erro ao carregar competências');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCompetencias();
    }, []);

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!uploadFile || !newCompetencia) return;

        setUploading(true);
        setError(null);
        try {
            await uploadCompetencia(uploadFile, newCompetencia);
            setUploadFile(null);
            setNewCompetencia('');
            await fetchCompetencias();
            alert('Competência importada com sucesso!');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Erro no upload');
        } finally {
            setUploading(false);
        }
    };

    const handleActivate = async (comp: string) => {
        if (!window.confirm(`Deseja definir ${comp} como a competência ativa?`)) return;

        setLoading(true);
        try {
            await activateCompetencia(comp);
            await fetchCompetencias();
        } catch (err) {
            setError('Erro ao ativar competência');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Upload Section */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <Upload className="w-5 h-5 text-primary-600" />
                    Importar Nova Tabela
                </h3>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                )}

                <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Competência (AAAAQM)</label>
                        <input
                            type="text"
                            placeholder="Ex: 202512"
                            value={newCompetencia}
                            onChange={(e) => setNewCompetencia(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Arquivo ZIP (.zip)</label>
                        <input
                            type="file"
                            accept=".zip"
                            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                            className="w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-primary-50 file:text-primary-700
                hover:file:bg-primary-100"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={uploading}
                        className="flex items-center justify-center gap-2 bg-primary-600 text-white p-2 rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
                    >
                        {uploading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Importando...
                            </>
                        ) : (
                            <>
                                <Upload className="w-5 h-5" />
                                Importar
                            </>
                        )}
                    </button>
                </form>
                <p className="mt-2 text-xs text-gray-500">
                    Compacte os arquivos .txt (tb_procedimento, etc) em um arquivo .zip.
                </p>
            </div>

            {/* List Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-gray-600" />
                        Competências Instaladas
                    </h3>
                    <span className="text-sm text-gray-500">
                        Ativa: <span className="font-bold text-green-600">{activeCompetencia || 'Nenhuma'}</span>
                    </span>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-100 text-gray-700 font-medium border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3">Competência</th>
                                <th className="px-6 py-3">Data Importação</th>
                                <th className="px-6 py-3">Status</th>
                                <th className="px-6 py-3 text-right">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {competencias.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                                        Nenhuma tabela instalada.
                                    </td>
                                </tr>
                            ) : (
                                competencias.map((comp) => (
                                    <tr key={comp.competencia} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-gray-900">{comp.competencia}</td>
                                        <td className="px-6 py-4">{new Date(comp.created_at).toLocaleDateString()}</td>
                                        <td className="px-6 py-4">
                                            {activeCompetencia === comp.competencia ? (
                                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                    <Check className="w-3 h-3" />
                                                    Ativa
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                    Disponível
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {activeCompetencia !== comp.competencia && (
                                                <button
                                                    onClick={() => handleActivate(comp.competencia)}
                                                    className="text-primary-600 hover:text-primary-900 font-medium inline-flex items-center gap-1"
                                                >
                                                    <PlayCircle className="w-4 h-4" />
                                                    Ativar
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default SigtapManager;
