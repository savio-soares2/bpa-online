import React, { useState, useEffect } from 'react';
import { Search, Building2, Calendar, Loader2, AlertTriangle } from 'lucide-react';
import { ESTABELECIMENTOS } from '../../constants/estabelecimentos';
import InconsistencySummary from './InconsistencySummary';
import InconsistencyList from './InconsistencyList';

interface InconsistencyReport {
    summary: {
        total: number;
        critical: number;
        warnings: number;
    };
    details: any[];
}

const InconsistenciesTab: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState<InconsistencyReport | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [selectedCnes, setSelectedCnes] = useState('');
    const [selectedComp, setSelectedComp] = useState(() => {
        const now = new Date();
        return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
    });

    const loadReport = async () => {
        if (!selectedCnes || !selectedComp) return;

        setLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const params = new URLSearchParams({
                cnes: selectedCnes,
                competencia: selectedComp
            });

            const response = await fetch(`/api/bpa/inconsistencies?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setReport(data);
            } else {
                const errData = await response.json();
                setError(errData.detail || 'Erro ao carregar relatório');
            }
        } catch (err) {
            console.error('Erro ao buscar inconsistências:', err);
            setError('Erro de conexão com o servidor');
        } finally {
            setLoading(false);
        }
    };

    const competenciaOptions = (() => {
        const options = [];
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;

        for (let i = 0; i < 12; i++) {
            let year = currentYear;
            let month = currentMonth - i;
            if (month <= 0) {
                month += 12;
                year -= 1;
            }
            const comp = `${year}${String(month).padStart(2, '0')}`;
            const monthName = new Date(year, month - 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
            options.push({ value: comp, label: monthName.charAt(0).toUpperCase() + monthName.slice(1) });
        }
        return options;
    })();

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            <Building2 className="w-4 h-4 inline mr-1" />
                            Estabelecimento
                        </label>
                        <select
                            value={selectedCnes}
                            onChange={(e) => setSelectedCnes(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">Selecione o estabelecimento</option>
                            {ESTABELECIMENTOS.map((estab) => (
                                <option key={estab.cnes} value={estab.cnes}>
                                    {estab.sigla} - {estab.cnes}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            <Calendar className="w-4 h-4 inline mr-1" />
                            Competência
                        </label>
                        <select
                            value={selectedComp}
                            onChange={(e) => setSelectedComp(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            {competenciaOptions.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-end">
                        <button
                            onClick={loadReport}
                            disabled={loading || !selectedCnes}
                            className="w-full h-[42px] bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    <Search className="w-5 h-5" />
                                    Analisar Inconsistências
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {report && (
                <>
                    <InconsistencySummary
                        total={report.summary.total}
                        critical={report.summary.critical}
                        warnings={report.summary.warnings}
                    />
                    <InconsistencyList details={report.details} />
                </>
            )}

            {!report && !loading && !error && (
                <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
                    <AlertTriangle className="w-12 h-12 text-blue-200 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-800">Selecione os filtros e clique em Analisar</h3>
                    <p className="text-gray-500 mt-2">
                        O sistema irá verificar inconsistências nos dados do banco usando as regras de correção do BPA.
                    </p>
                </div>
            )}
        </div>
    );
};

export default InconsistenciesTab;
