
import React, { useState, useEffect } from 'react';
import { RefreshCw, Filter, DollarSign, Activity, Users, Building2 } from 'lucide-react';
import api from '../../services/api';
import StatCard from './StatCard';
import SimpleChart from './SimpleChart';
import { ESTABELECIMENTOS } from '../../constants/estabelecimentos';

interface DashboardStats {
    kpis: {
        total_faturado: number;
        total_procedimentos: number;
        total_cbos_atuantes: number;
    };
    graficos: {
        evolucao_faturamento: Array<{ competencia: string; valor: number; quantidade: number }>;
        top_procedimentos_valor: Array<{ codigo: string; nome: string; valor: number; quantidade: number }>;
        top_cbos_valor: Array<{ cbo: string; nome: string; valor: number; quantidade: number }>;
    };
}

interface FinancialDashboardProps {
    cnesList?: string[]; // Mantido para compatibilidade, mas vamos usar ESTABELECIMENTOS
}

const FinancialDashboard: React.FC<FinancialDashboardProps> = () => {
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<DashboardStats | null>(null);

    // Helpers de Data
    const getCompetenciaAtual = () => {
        const now = new Date();
        return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
    };

    const getCompetenciaOptions = () => {
        const options = [];
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;

        // Gera últimos 18 meses para ter um bom histórico
        for (let i = 0; i < 18; i++) {
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
    };

    const competenciaOptions = getCompetenciaOptions();
    const defaultComp = getCompetenciaAtual();

    // Filtros
    const [filters, setFilters] = useState({
        competencia_inicio: defaultComp,
        competencia_fim: defaultComp,
        cnes: [] as string[],
        tipo_bpa: '',
        cbo: '',
        procedimento: ''
    });

    const loadDashboard = async () => {
        setLoading(true);
        try {
            const params: any = {};
            if (filters.competencia_inicio) params.competencia_inicio = filters.competencia_inicio;
            if (filters.competencia_fim) params.competencia_fim = filters.competencia_fim;
            if (filters.tipo_bpa) params.tipo_bpa = filters.tipo_bpa;
            if (filters.cbo) params.cbo = filters.cbo;
            if (filters.procedimento) params.procedimento = filters.procedimento;
            if (filters.cnes.length > 0) params.cnes = filters.cnes;

            const response = await api.get('/admin/dashboard/stats', { params });

            if (response.data && response.data.success) {
                setData({
                    kpis: response.data.kpis,
                    graficos: response.data.graficos
                });
            }
        } catch (error) {
            console.error("Erro ao carregar dashboard", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDashboard();
    }, []);

    const handleFilterChange = (key: string, value: any) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Barra de Filtros */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                <div className="flex items-center gap-2 mb-4 text-gray-700 font-medium">
                    <Filter className="w-5 h-5" />
                    Filtros Avançados
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* CNES - Agora ocupando mais espaço e como primeiro filtro importante */}
                    <div className="lg:col-span-2">
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                            <Building2 className="w-3 h-3 inline mr-1" />
                            Estabelecimento (CNES)
                        </label>
                        <select
                            className="w-full px-3 py-2 border rounded-md text-sm bg-white"
                            value={filters.cnes[0] || ''} // Assume single select na UI por enquanto
                            onChange={e => handleFilterChange('cnes', e.target.value ? [e.target.value] : [])}
                        >
                            <option value="">Todos os Estabelecimentos</option>
                            {ESTABELECIMENTOS.map(estab => (
                                <option key={estab.cnes} value={estab.cnes}>
                                    {estab.sigla} - {estab.nome}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Competências */}
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Comp. Início</label>
                            <select
                                className="w-full px-3 py-2 border rounded-md text-sm bg-white"
                                value={filters.competencia_inicio}
                                onChange={e => handleFilterChange('competencia_inicio', e.target.value)}
                            >
                                <option value="">Geral</option>
                                {competenciaOptions.map(opt => (
                                    <option key={`inicio-${opt.value}`} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Comp. Fim</label>
                            <select
                                className="w-full px-3 py-2 border rounded-md text-sm bg-white"
                                value={filters.competencia_fim}
                                onChange={e => handleFilterChange('competencia_fim', e.target.value)}
                            >
                                <option value="">Geral</option>
                                {competenciaOptions.map(opt => (
                                    <option key={`fim-${opt.value}`} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Tipo */}
                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Tipo BPA</label>
                        <select
                            className="w-full px-3 py-2 border rounded-md text-sm bg-white"
                            value={filters.tipo_bpa}
                            onChange={e => handleFilterChange('tipo_bpa', e.target.value)}
                        >
                            <option value="">Conforme Filtro</option>
                            <option value="BPA-I">BPA Individualizado</option>
                            <option value="BPA-C">BPA Consolidado</option>
                        </select>
                    </div>

                    {/* Linha 2 de Filtros */}
                    <div className="lg:col-span-1">
                        <label className="block text-xs font-medium text-gray-500 mb-1">CBO (Ocupação)</label>
                        <input
                            type="text"
                            placeholder="Ex: 223505"
                            className="w-full px-3 py-2 border rounded-md text-sm"
                            value={filters.cbo}
                            onChange={e => handleFilterChange('cbo', e.target.value)}
                        />
                    </div>

                    <div className="lg:col-span-2">
                        <label className="block text-xs font-medium text-gray-500 mb-1">Procedimento</label>
                        <input
                            type="text"
                            placeholder="Ex: 0301010072"
                            className="w-full px-3 py-2 border rounded-md text-sm"
                            value={filters.procedimento}
                            onChange={e => handleFilterChange('procedimento', e.target.value)}
                        />
                    </div>

                    <div className="flex items-end">
                        <button
                            onClick={loadDashboard}
                            disabled={loading}
                            className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                            Atualizar Dados
                        </button>
                    </div>
                </div>
            </div>

            {data ? (
                <>
                    {/* KPIs */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <StatCard
                            title="Faturamento Agregado"
                            value={data.kpis.total_faturado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            icon={<DollarSign className="w-6 h-6" />}
                            color="green"
                        />
                        <StatCard
                            title="Total Procedimentos"
                            value={data.kpis.total_procedimentos.toLocaleString('pt-BR')}
                            icon={<Activity className="w-6 h-6" />}
                            color="blue"
                        />
                        <StatCard
                            title="Diversidade Profissional (CBOs)"
                            value={data.kpis.total_cbos_atuantes}
                            subValue="Categorias Ativas"
                            icon={<Users className="w-6 h-6" />}
                            color="purple"
                        />
                    </div>

                    {/* Gráficos */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <SimpleChart
                            type="line"
                            title="Evolução do Faturamento"
                            data={data.graficos.evolucao_faturamento.map(d => ({ label: d.competencia, value: d.valor }))}
                            currency
                        />
                        <div className="space-y-6">
                            <SimpleChart
                                type="bar"
                                title="Top 5 Procedimentos (por Valor)"
                                data={data.graficos.top_procedimentos_valor.slice(0, 5).map(d => ({
                                    label: d.nome,
                                    value: d.valor,
                                    tooltip: `Cod: ${d.codigo} | Qtd: ${d.quantidade}`
                                }))}
                                currency
                            />
                            <SimpleChart
                                type="bar"
                                title="Top 5 Ocupações (por Faturamento)"
                                data={data.graficos.top_cbos_valor.slice(0, 5).map(d => ({
                                    label: d.nome,
                                    value: d.valor,
                                    color: '#8B5CF6'
                                }))}
                                currency
                            />
                        </div>
                    </div>
                </>
            ) : (
                <div className="text-center py-12 text-gray-500">
                    Nenhuma estatística carregada. Clique em Atualizar Dados.
                </div>
            )}
        </div>
    );
};

export default FinancialDashboard;
