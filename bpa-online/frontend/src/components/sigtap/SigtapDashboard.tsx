import React, { useState, useEffect, useRef } from 'react';
import {
    Search, Filter, ChevronLeft, ChevronRight,
    Stethoscope, Activity, DollarSign, Database,
    ArrowUpDown, CheckSquare, Square
} from 'lucide-react';
import {
    searchProcedimentos,
    listRegistros,
    SigtapProcedimento,
    SigtapSearchFilters,
    getSigtapStats,
    SigtapRegistro
} from '../../services/sigtapService';

const SigtapDashboard: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<SigtapProcedimento[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [stats, setStats] = useState<any>(null);
    const [allRegistros, setAllRegistros] = useState<SigtapRegistro[]>([]);

    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCBO, setSelectedCBO] = useState('');
    const [selectedServico, setSelectedServico] = useState('');
    const [selectedRegistros, setSelectedRegistros] = useState<string[]>([]);

    // Sorting
    const [sortField, setSortField] = useState<'nome' | 'valor' | 'codigo' | undefined>(undefined);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    // MultiSelect UI State
    const [showRegistroDropdown, setShowRegistroDropdown] = useState(false);
    const registroDropdownRef = useRef<HTMLDivElement>(null);

    // Initial Load
    useEffect(() => {
        const init = async () => {
            try {
                const [s, r] = await Promise.all([getSigtapStats(), listRegistros()]);
                setStats(s || null);
                const registros = Array.isArray(r) ? r : (r as any)?.data || [];
                setAllRegistros(registros);
            } catch (e) {
                console.error(e);
                setStats(null);
                setAllRegistros([]);
            }
        };
        init();
    }, []);

    // Close Dropdown on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (registroDropdownRef.current && !registroDropdownRef.current.contains(event.target as Node)) {
                setShowRegistroDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const filters: SigtapSearchFilters = {
                q: searchTerm,
                page: page,
                limit: 50,
                cbo: selectedCBO || undefined,
                servico: selectedServico || undefined,
                tipo_registro: selectedRegistros,
                sort_field: sortField,
                sort_order: sortOrder
            };

            const res = await searchProcedimentos(filters);
            setResults(res?.data || []);
            setTotal(res?.total || 0);
            setTotalPages(res?.pages || 1);
        } catch (error) {
            console.error(error);
            setResults([]);
            setTotal(0);
            setTotalPages(1);
        } finally {
            setLoading(false);
        }
    };

    // Debounce search & filters
    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1); // Reset page on filter change
            loadData();
        }, 500);
        return () => clearTimeout(timer);
    }, [searchTerm, selectedCBO, selectedServico, selectedRegistros, sortField, sortOrder]);

    // Page change trigger
    useEffect(() => {
        loadData();
    }, [page]);

    const formatCurrency = (val: string) => {
        if (!val) return 'R$ 0,00';
        const num = parseInt(val) / 100;
        return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    };

    const toggleRegistro = (code: string) => {
        setSelectedRegistros(prev =>
            prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
        );
    };

    const handleSort = (field: 'nome' | 'valor' | 'codigo') => {
        if (sortField === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortOrder('desc'); // Default to desc for ease (especially value)
        }
    };

    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-500">Total Procedimentos</h4>
                        <Database className="w-4 h-4 text-blue-500" />
                    </div>
                    <p className="text-2xl font-bold text-gray-800">
                        {stats ? stats.total_procedimentos.toLocaleString('pt-BR') : '-'}
                    </p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-500">Procedimentos Filtrados</h4>
                        <Filter className="w-4 h-4 text-purple-500" />
                    </div>
                    <p className="text-2xl font-bold text-gray-800">
                        {total.toLocaleString('pt-BR')}
                    </p>
                </div>
            </div>

            {/* Filters Section */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 space-y-4">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Buscar Procedimento</label>
                        <div className="relative">
                            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Digite nome ou código..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>

                    {/* MultiSelect Instrumento */}
                    <div className="w-full md:w-64 relative" ref={registroDropdownRef}>
                        <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Instrumentos</label>
                        <div
                            className="w-full p-2 border border-gray-300 rounded-md text-sm bg-white cursor-pointer flex justify-between items-center"
                            onClick={() => setShowRegistroDropdown(!showRegistroDropdown)}
                        >
                            <span className="truncate">
                                {selectedRegistros.length === 0
                                    ? 'Todos'
                                    : `${selectedRegistros.length} selecionado(s)`}
                            </span>
                            <ChevronRight className={`w-4 h-4 transition-transform ${showRegistroDropdown ? 'rotate-90' : ''}`} />
                        </div>

                        {showRegistroDropdown && (
                            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                                {(allRegistros || []).map(reg => (
                                    <div
                                        key={reg.CO_REGISTRO}
                                        className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm"
                                        onClick={() => toggleRegistro(reg.CO_REGISTRO)}
                                    >
                                        {selectedRegistros.includes(reg.CO_REGISTRO)
                                            ? <CheckSquare className="w-4 h-4 text-primary-600" />
                                            : <Square className="w-4 h-4 text-gray-400" />
                                        }
                                        <span className="text-gray-700">{reg.CO_REGISTRO} - {reg.NO_REGISTRO}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>


                    <div className="w-full md:w-48">
                        <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">CBO (Código)</label>
                        <input
                            type="text"
                            placeholder="Ex: 225125"
                            value={selectedCBO}
                            onChange={(e) => setSelectedCBO(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>

                    <div className="w-full md:w-48">
                        <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Serviço (Código)</label>
                        <input
                            type="text"
                            placeholder="Ex: 115"
                            value={selectedServico}
                            onChange={(e) => setSelectedServico(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>
                </div>

                {/* Active Filters Tags */}
                {selectedRegistros.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
                        <span className="text-xs text-gray-500 py-1">Filtros ativos:</span>
                        {selectedRegistros.map(r => (
                            <span key={r} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-50 text-blue-700 text-xs">
                                Instrumento: {r}
                                <button onClick={() => toggleRegistro(r)} className="hover:text-blue-900">×</button>
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Table Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-100 text-gray-700 font-medium border-b border-gray-200">
                            <tr>
                                <th
                                    className="px-4 py-3 w-32 cursor-pointer hover:bg-gray-200 transition-colors"
                                    onClick={() => handleSort('codigo')}
                                >
                                    <div className="flex items-center gap-1">
                                        Código
                                        {sortField === 'codigo' && <ArrowUpDown className="w-3 h-3" />}
                                    </div>
                                </th>
                                <th
                                    className="px-4 py-3 cursor-pointer hover:bg-gray-200 transition-colors"
                                    onClick={() => handleSort('nome')}
                                >
                                    <div className="flex items-center gap-1">
                                        Nome do Procedimento
                                        {sortField === 'nome' && <ArrowUpDown className="w-3 h-3" />}
                                    </div>
                                </th>
                                <th className="px-4 py-3 w-40">Instrumentos</th>
                                <th
                                    className="px-4 py-3 w-32 text-right cursor-pointer hover:bg-gray-200 transition-colors"
                                    onClick={() => handleSort('valor')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        R$ Ambul.
                                        {sortField === 'valor' && <ArrowUpDown className="w-3 h-3" />}
                                    </div>
                                </th>
                                <th className="px-4 py-3 w-32 text-right">R$ Hosp.</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                                        Carregando...
                                    </td>
                                </tr>
                            ) : (results || []).length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                                        Nenhum procedimento encontrado.
                                    </td>
                                </tr>
                            ) : (
                                (results || []).map((proc) => (
                                    <tr key={proc.CO_PROCEDIMENTO} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-4 py-3 font-mono font-medium text-primary-700">
                                            {proc.CO_PROCEDIMENTO}
                                        </td>
                                        <td className="px-4 py-3 font-medium text-gray-900">
                                            {proc.NO_PROCEDIMENTO}
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex flex-wrap gap-1">
                                                {proc.REGISTROS?.map(reg => (
                                                    <span
                                                        key={reg}
                                                        className={`text-[10px] px-1.5 py-0.5 rounded border ${reg === '02' ? 'bg-green-50 text-green-700 border-green-200' :
                                                                reg === '01' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                                                    'bg-gray-50 text-gray-600 border-gray-200'
                                                            }`}
                                                    >
                                                        {reg === '02' ? 'BPA-I' : reg === '01' ? 'BPA-C' : reg}
                                                    </span>
                                                ))}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-right font-mono text-green-700">
                                            {formatCurrency(proc.VL_SA)}
                                        </td>
                                        <td className="px-4 py-3 text-right font-mono text-gray-500">
                                            {formatCurrency(proc.VL_SH)}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                        Mostrando <span className="font-medium">{Math.min((page - 1) * 50 + 1, total)}</span> a <span className="font-medium">{Math.min(page * 50, total)}</span> de <span className="font-medium">{total}</span> resultados
                    </p>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            aria-label="Página anterior"
                            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>
                        <span className="text-sm font-medium text-gray-700">
                            Página {page} de {Math.max(1, totalPages)}
                        </span>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            aria-label="Próxima página"
                            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SigtapDashboard;
