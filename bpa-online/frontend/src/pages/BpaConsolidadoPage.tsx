import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Save, Trash2, Search } from 'lucide-react';
import { createBPAConsolidado, listBPAConsolidado, BPAConsolidado } from '../services/bpaService';
import { searchProcedimentos, SigtapProcedimento } from '../services/sigtapService';
import { listCbosUnidade, CboSummary } from '../services/adminService';

const BpaConsolidadoPage: React.FC = () => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState<BPAConsolidado[]>([]);

    // Header Data
    const [competencia, setCompetencia] = useState('202512'); // TODO: Pegar atual
    const [folha, setFolha] = useState('1');

    // Form Data
    const [selectedProc, setSelectedProc] = useState<SigtapProcedimento | null>(null);
    const [procQuery, setProcQuery] = useState('');
    const [procResults, setProcResults] = useState<SigtapProcedimento[]>([]);
    const [showProcList, setShowProcList] = useState(false);

    const [selectedCbo, setSelectedCbo] = useState('');
    const [idade, setIdade] = useState('');
    const [quantidade, setQuantidade] = useState('1');

    // Aux Data
    const [unitCbos, setUnitCbos] = useState<CboSummary[]>([]);

    useEffect(() => {
        if (user?.cnes) {
            loadUnitData();
            loadItems();
        }
    }, [user?.cnes, competencia, folha]);

    const loadUnitData = async () => {
        if (!user?.cnes) return;
        try {
            const cbos = await listCbosUnidade(user.cnes);
            setUnitCbos(cbos);
        } catch (e) {
            console.error(e);
        }
    };

    const loadItems = async () => {
        // TODO: Backend filter by folha? Currently lists all by competencia.
        // We will filter client side or update backend later.
        if (!user?.cnes) return;
        try {
            const all = await listBPAConsolidado(competencia);
            // Filter by folha if we implemented that field... Schema has 'prd_flh' in DB but mapped?
            // createBPAConsolidado endpoint map 'prd_flh'.
            // listBPAConsolidado endpoint returns standard list.
            // Let's assume standard list for now.
            setItems(all);
        } catch (e) {
            console.error(e);
        }
    };

    // Procedure Search
    useEffect(() => {
        const search = async () => {
            if (procQuery.length >= 3) {
                const res = await searchProcedimentos({ q: procQuery, limit: 10 });
                setProcResults(res.data);
                setShowProcList(true);
            } else {
                setProcResults([]);
                setShowProcList(false);
            }
        };
        const timeout = setTimeout(search, 300);
        return () => clearTimeout(timeout);
    }, [procQuery]);

    const handleSelectProc = (proc: SigtapProcedimento) => {
        setSelectedProc(proc);
        setProcQuery(`${proc.CO_PROCEDIMENTO} - ${proc.NO_PROCEDIMENTO}`);
        setShowProcList(false);
    };

    const handleAddItem = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProc || !selectedCbo || !idade || !quantidade) return;

        setLoading(true);
        try {
            const newItem = await createBPAConsolidado({
                competencia,
                procedimento: selectedProc.CO_PROCEDIMENTO,
                cbo: selectedCbo,
                idade,
                quantidade: parseInt(quantidade),
                // folha: parseInt(folha) // Need to add folha to interface if backend accepts
            });
            setItems([...items, newItem]);
            // Reset fields but keep CBO?
            setSelectedProc(null);
            setProcQuery('');
            setQuantidade('1');
            // Keep CBO and Age potentially
        } catch (error) {
            alert('Erro ao adicionar item');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-20 px-6 pt-6">
            {/* Header / Config */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">CNES</label>
                        <input
                            disabled
                            value={user?.cnes || ''}
                            className="w-full p-2 bg-gray-100 border rounded text-gray-700"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">Unidade</label>
                        <input
                            disabled
                            value={user?.nome_unidade || ''}
                            className="w-full p-2 bg-gray-100 border rounded text-gray-700 truncate"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">Competência</label>
                        <input
                            value={competencia}
                            onChange={e => setCompetencia(e.target.value)}
                            maxLength={6}
                            className="w-full p-2 border rounded font-mono text-center"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">Folha</label>
                        <input
                            value={folha}
                            onChange={e => setFolha(e.target.value)}
                            type="number"
                            className="w-full p-2 border rounded font-mono text-center"
                        />
                    </div>
                </div>
            </div>

            {/* Input Grid (Legacy Style) */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <form onSubmit={handleAddItem} className="flex flex-col md:flex-row gap-4 items-end">

                    {/* Procedimento Search */}
                    <div className="flex-1 relative">
                        <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Procedimento</label>
                        <input
                            type="text"
                            value={procQuery}
                            onChange={e => {
                                setProcQuery(e.target.value);
                                if (!e.target.value) setSelectedProc(null);
                            }}
                            className="w-full p-2 border rounded font-mono text-sm focus:ring-2 focus:ring-primary-500"
                            placeholder="Digite código ou nome..."
                            autoFocus
                        />
                        {showProcList && (
                            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                                {procResults.map(p => (
                                    <div
                                        key={p.CO_PROCEDIMENTO}
                                        className="px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm border-b border-gray-100 last:border-0"
                                        onClick={() => handleSelectProc(p)}
                                    >
                                        <span className="font-bold text-primary-700 mr-2">{p.CO_PROCEDIMENTO}</span>
                                        <span className="text-gray-700">{p.NO_PROCEDIMENTO}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* CBO Select */}
                    <div className="w-full md:w-64">
                        <label className="block text-xs font-medium text-gray-500 uppercase mb-1">CBO</label>
                        <select
                            required
                            value={selectedCbo}
                            onChange={e => setSelectedCbo(e.target.value)}
                            className="w-full p-2 border rounded text-sm bg-white"
                        >
                            <option value="">Selecione...</option>
                            {unitCbos.map(c => (
                                <option key={c.cbo} value={c.cbo}>
                                    {c.cbo} ({c.total} profs)
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Idade */}
                    <div className="w-20">
                        <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Idade</label>
                        <input
                            required
                            value={idade}
                            onChange={e => setIdade(e.target.value)}
                            maxLength={3}
                            className="w-full p-2 border rounded text-center"
                        />
                    </div>

                    {/* Qtd */}
                    <div className="w-20">
                        <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Qtd.</label>
                        <input
                            required
                            type="number"
                            min="1"
                            value={quantidade}
                            onChange={e => setQuantidade(e.target.value)}
                            className="w-full p-2 border rounded text-center"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-primary-600 text-white p-2 rounded hover:bg-primary-700 transition flex items-center justify-center min-w-[40px]"
                    >
                        <Plus className="w-5 h-5" />
                    </button>
                </form>
            </div>

            {/* List Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-gray-100 text-gray-700 font-medium border-b border-gray-200">
                        <tr>
                            <th className="px-4 py-2 w-16 text-center">Seq</th>
                            <th className="px-4 py-2">Procedimento</th>
                            <th className="px-4 py-2 w-32">CBO</th>
                            <th className="px-4 py-2 w-20 text-center">Idade</th>
                            <th className="px-4 py-2 w-20 text-center">Qtd</th>
                            <th className="px-4 py-2 w-16"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {items.length === 0 ? (
                            <tr><td colSpan={6} className="text-center py-8 text-gray-400">Nenhum item lançado nesta folha.</td></tr>
                        ) : (
                            items.slice().reverse().map((item, idx) => (
                                <tr key={item.id || idx} className="hover:bg-gray-50">
                                    <td className="px-4 py-2 text-center text-gray-500">{items.length - idx}</td>
                                    <td className="px-4 py-2 font-mono">{item.procedimento}</td>
                                    <td className="px-4 py-2">{item.cbo}</td>
                                    <td className="px-4 py-2 text-center">{item.idade}</td>
                                    <td className="px-4 py-2 text-center font-bold">{item.quantidade}</td>
                                    <td className="px-4 py-2 text-right">
                                        <button className="text-red-400 hover:text-red-600">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer Actions */}
            <div className="fixed bottom-0 left-64 right-0 bg-white border-t border-gray-200 p-4 flex justify-end gap-4 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
                <div className="text-sm text-gray-500 self-center mr-auto">
                    Total de itens: <b>{items.length}</b>
                </div>
                <button className="px-6 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 font-medium">
                    Nova Folha
                </button>
                <button className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-medium flex items-center gap-2">
                    <Save className="w-4 h-4" />
                    Gravar Boletim
                </button>
            </div>
        </div>
    );
};

export default BpaConsolidadoPage;
