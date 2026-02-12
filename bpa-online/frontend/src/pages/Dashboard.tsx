import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  TrendingUp,
  Calendar,
  RefreshCw,
  Building2,
  Filter
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getDashboardStats } from '../services/api';
import { ESTABELECIMENTOS, getEstabelecimentoByCnes } from '../constants/estabelecimentos';

interface DashboardStats {
  cnes: string;
  nome_unidade: string;
  usuario: string;
  bpai: {
    total: number;
    pendentes: number;
    exportados: number;
    competencias: string[];
  };
  bpac: {
    total: number;
    pendentes: number;
    exportados: number;
    competencias: string[];
  };
  profissionais: number;
  pacientes: number;
  ultimas_exportacoes: any[];
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCnes, setSelectedCnes] = useState<string>('');
  const [selectedCompetencia, setSelectedCompetencia] = useState<string>('');

  // Gera lista de competências (últimos 12 meses)
  const getCompetencias = () => {
    const competencias = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      competencias.push({
        value: `${year}${month}`,
        label: `${month}/${year}`
      });
    }
    return competencias;
  };

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await getDashboardStats(selectedCnes || undefined);
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCnes, selectedCompetencia]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
          <LayoutDashboard className="w-8 h-8 text-primary-600" />
          Dashboard
        </h1>
        <p className="text-gray-500 mt-1">
          Bem-vindo(a), <span className="font-semibold">{user?.nome}</span>
        </p>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filtros:</span>
          </div>
          
          {/* Filtro por Estabelecimento */}
          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">Estabelecimento</label>
            <select
              value={selectedCnes}
              onChange={(e) => setSelectedCnes(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="">Todos</option>
              {ESTABELECIMENTOS.map((estab) => (
                <option key={estab.cnes} value={estab.cnes}>
                  {estab.sigla} - {estab.cnes}
                </option>
              ))}
            </select>
          </div>
          
          {/* Filtro por Competência */}
          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">Competência</label>
            <select
              value={selectedCompetencia}
              onChange={(e) => setSelectedCompetencia(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="">Todas</option>
              {getCompetencias().map((comp) => (
                <option key={comp.value} value={comp.value}>
                  {comp.label}
                </option>
              ))}
            </select>
          </div>
          
          <button
            onClick={loadStats}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors self-end"
            title="Atualizar"
          >
            <RefreshCw className={`w-5 h-5 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        {selectedCnes && getEstabelecimentoByCnes(selectedCnes) && (
          <p className="text-xs text-gray-500 mt-2 ml-9">
            <Building2 className="w-3 h-3 inline mr-1" />
            {getEstabelecimentoByCnes(selectedCnes)?.nome}
          </p>
        )}
      </div>

      {/* Info CNES */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-6 mb-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-primary-100 text-sm">Unidade de Saúde</p>
            <h2 className="text-2xl font-bold mt-1">
              {selectedCnes 
                ? getEstabelecimentoByCnes(selectedCnes)?.sigla || stats?.nome_unidade 
                : stats?.nome_unidade || 'Todas as Unidades'}
            </h2>
            <p className="text-primary-200 mt-2">
              CNES: {selectedCnes || stats?.cnes || 'Todos'}
            </p>
          </div>
        </div>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* BPA-I Total */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
              BPA-I
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-800">{stats?.bpai.total || 0}</p>
          <p className="text-gray-500 text-sm mt-1">BPA Individualizado</p>
          <p className="text-xs text-gray-400 mt-1">Com identificação do paciente</p>
        </div>

        {/* BPA-C Total */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-green-100 p-3 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
              BPA-C
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-800">{stats?.bpac.total || 0}</p>
          <p className="text-gray-500 text-sm mt-1">BPA Consolidado</p>
          <p className="text-xs text-gray-400 mt-1">Agregado por procedimento</p>
        </div>

        {/* Profissionais */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-purple-100 p-3 rounded-lg">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-3xl font-bold text-gray-800">{stats?.profissionais || 0}</p>
          <p className="text-gray-500 text-sm mt-1">Profissionais Cadastrados</p>
        </div>

        {/* Competências */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-orange-100 p-3 rounded-lg">
              <Calendar className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <p className="text-3xl font-bold text-gray-800">
            {stats?.bpai.competencias?.length || 0}
          </p>
          <p className="text-gray-500 text-sm mt-1">Competências com Dados</p>
          {stats?.bpai.competencias && stats.bpai.competencias.length > 0 && (
            <p className="text-xs text-gray-400 mt-2">
              Última: {stats.bpai.competencias[0]}
            </p>
          )}
        </div>
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Ações Rápidas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="/bpa-i"
            className="flex items-center gap-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
          >
            <FileText className="w-6 h-6 text-blue-600" />
            <div>
              <p className="font-medium text-gray-800">Novo BPA-I</p>
              <p className="text-xs text-gray-500">Cadastrar registro individualizado</p>
            </div>
          </a>
          
          <a
            href="/bpa-c"
            className="flex items-center gap-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
          >
            <TrendingUp className="w-6 h-6 text-green-600" />
            <div>
              <p className="font-medium text-gray-800">Novo BPA-C</p>
              <p className="text-xs text-gray-500">Cadastrar registro consolidado</p>
            </div>
          </a>
        </div>
      </div>

      {/* Competências Ativas */}
      {stats?.bpai.competencias && stats.bpai.competencias.length > 0 && (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Competências com Dados</h3>
          <div className="flex flex-wrap gap-2">
            {stats.bpai.competencias.map(comp => (
              <span
                key={comp}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium"
              >
                {comp.substring(0, 4)}/{comp.substring(4)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
