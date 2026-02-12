import React, { useState, useEffect, useRef } from 'react';
import {
  Database,
  Trash2,
  RefreshCw,
  Building2,
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  Cloud,
  FileText,
  TrendingUp,
  Calendar,
  Info,
  Activity,
  Filter,
  Zap,
  Save
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getEstabelecimentoByCnes, ESTABELECIMENTOS } from '../constants/estabelecimentos';
import FinancialDashboard from '../components/dashboard/FinancialDashboard';
import InconsistenciesTab from '../components/inconsistencies/InconsistenciesTab';
import { AlertCircle } from 'lucide-react';

// Tipos para logs de extração
interface LogEntry {
  id: number;
  timestamp: Date;
  phase: 'connect' | 'download' | 'filter' | 'process' | 'save' | 'complete' | 'error';
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  details?: string;
}

interface DatabaseOverview {
  success: boolean;
  cnes_list: string[];
  total_cnes: number;
  bpa_i: Array<{
    cnes: string;
    competencia: string;
    total: number;
    pendentes: number;
    exportados: number;
    primeira_insercao: string;
    ultima_insercao: string;
  }>;
  bpa_c: Array<{
    cnes: string;
    competencia: string;
    total: number;
    pendentes: number;
    exportados: number;
    primeira_insercao: string;
    ultima_insercao: string;
  }>;
  totals: {
    bpa_i: number;
    bpa_c: number;
    profissionais: number;
    pacientes: number;
  };
}

const DataManagementPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<DatabaseOverview | null>(null);
  const [selectedCnes, setSelectedCnes] = useState<string>('');
  const [selectedTab, setSelectedTab] = useState<'dashboard' | 'visao' | 'extracao' | 'inconsistencias' | 'historico'>('dashboard');

  // Histórico
  const [historico, setHistorico] = useState<any>(null);
  const [historicoPage, setHistoricoPage] = useState(0);
  const [historicoLimit] = useState(20);
  const [loadingHistorico, setLoadingHistorico] = useState(false);

  // Extração
  const [extracting, setExtracting] = useState(false);
  const [extractionCnes, setExtractionCnes] = useState(user?.cnes || '');
  const [extractionComp, setExtractionComp] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [extractionTipo, setExtractionTipo] = useState<'bpa_i' | 'bpa_c'>('bpa_i');
  const [sigtapFilter, setSigtapFilter] = useState(true);
  const [extractionResult, setExtractionResult] = useState<any>(null);

  // Sistema de Logs
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [currentPhase, setCurrentPhase] = useState<string>('');
  const [liveStats, setLiveStats] = useState<any>(null);
  const logIdRef = useRef(0);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Helper para adicionar log
  const addLog = (phase: LogEntry['phase'], message: string, type: LogEntry['type'] = 'info', details?: string) => {
    logIdRef.current += 1;
    setLogs(prev => [...prev, {
      id: logIdRef.current,
      timestamp: new Date(),
      phase,
      message,
      type,
      details
    }]);
  };

  // Deletar
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    cnes: string;
    competencia?: string;
    tipo: string;
  } | null>(null);

  // Correção de encoding
  const [fixingEncoding, setFixingEncoding] = useState(false);

  const loadDatabaseOverview = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/database-overview', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOverview(data);
      }
    } catch (error) {
      console.error('Erro ao carregar visão do banco:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatabaseOverview();
  }, []);

  const loadHistorico = async (page: number = 0) => {
    setLoadingHistorico(true);
    try {
      const token = localStorage.getItem('token');
      const offset = page * historicoLimit;
      const params = new URLSearchParams({
        limit: historicoLimit.toString(),
        offset: offset.toString()
      });

      const response = await fetch(`/api/admin/historico-extracoes?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setHistorico(data);
        setHistoricoPage(page);
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    } finally {
      setLoadingHistorico(false);
    }
  };

  const handleFixEncoding = async () => {
    setFixingEncoding(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/fix-encoding', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ ${result.message}`);
        // Recarrega histórico para mostrar nomes corrigidos
        loadHistorico(historicoPage);
      } else {
        alert('❌ Erro ao corrigir encoding');
      }
    } catch (error) {
      console.error('Erro ao corrigir encoding:', error);
      alert('❌ Erro ao corrigir encoding');
    } finally {
      setFixingEncoding(false);
    }
  };

  useEffect(() => {
    if (selectedTab === 'historico') {
      loadHistorico(0);
    }
  }, [selectedTab]);

  const handleDelete = async () => {
    if (!deleteConfirm) return;

    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        cnes: deleteConfirm.cnes,
        tipo: deleteConfirm.tipo
      });

      if (deleteConfirm.competencia) {
        params.append('competencia', deleteConfirm.competencia);
      }

      const response = await fetch(`/api/admin/delete-data?${params}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ ${result.message}`);
        setDeleteConfirm(null);
        loadDatabaseOverview();
      } else {
        alert('❌ Erro ao deletar dados');
      }
    } catch (error) {
      console.error('Erro ao deletar:', error);
      alert('❌ Erro ao deletar dados');
    } finally {
      setDeleting(false);
    }
  };

  const handleExtractAll = async () => {
    // Limpa estado anterior
    setLogs([]);
    setLiveStats(null);
    setExtractionResult(null);
    setExtracting(true);

    const estabelecimento = getEstabelecimentoByCnes(extractionCnes);
    const nomeEstab = estabelecimento?.sigla || extractionCnes;

    try {
      const token = localStorage.getItem('token');

      // Fase 1: Conectando
      setCurrentPhase('connect');
      addLog('connect', `Iniciando extração para ${nomeEstab}`, 'info', `CNES: ${extractionCnes}, Competência: ${extractionComp}`);
      addLog('connect', 'Conectando à API BiServer...', 'info');
      await new Promise(resolve => setTimeout(resolve, 300));
      addLog('connect', 'Conexão estabelecida com bi.eSUS', 'success');

      // Fase 2: Download
      setCurrentPhase('download');
      addLog('download', 'Iniciando download dos dados...', 'info');
      addLog('download', 'Buscando páginas da API (10.000 registros por página)', 'info');

      // Chama endpoint unificado SEM LIMITE
      const params = new URLSearchParams({
        cnes: extractionCnes,
        competencia: extractionComp
      });

      const startTime = Date.now();
      const response = await fetch(`/api/biserver/extract-and-separate?${params}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const result = await response.json();
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      if (!response.ok) {
        throw new Error(result.detail || 'Erro na extração');
      }

      // Atualiza stats
      const stats = result.stats || {};
      const extractedStats = stats.extracted || {};
      const savedStats = stats.saved || {};
      const valoresStats = stats.valores || {};

      setLiveStats({
        total_api: extractedStats.total || 0,
        bpa_i: savedStats.bpa_i || 0,
        bpa_c: savedStats.bpa_c || 0,
        removed: extractedStats.removed || extractedStats.removed_sem_registro || 0
      });

      addLog('download', `Download concluído em ${elapsed}s`, 'success', `${extractedStats.total || 0} registros`);

      // Fase 3: Filtro SIGTAP
      setCurrentPhase('filter');
      addLog('filter', 'Aplicando filtros SIGTAP...', 'info');

      if (extractedStats.removed > 0 || extractedStats.removed_sem_registro > 0) {
        addLog('filter', `${extractedStats.removed || extractedStats.removed_sem_registro || 0} registros sem tipo BPA (e-SUS, RAAS, etc)`, 'warning');
      }

      addLog('filter', 'Classificando procedimentos por tipo de registro', 'info');
      await new Promise(resolve => setTimeout(resolve, 200));
      addLog('filter', 'Filtro SIGTAP aplicado', 'success');

      // Fase 4: Processamento
      setCurrentPhase('process');
      addLog('process', 'Separando BPA-I e BPA-C...', 'info');

      const bpaI = savedStats.bpa_i || 0;
      const bpaC = savedStats.bpa_c || 0;

      if (bpaI > 0) {
        addLog('process', `${bpaI.toLocaleString()} registros BPA Individualizado`, 'info');
      }
      if (bpaC > 0) {
        addLog('process', `${bpaC.toLocaleString()} registros BPA Consolidado (agregados)`, 'info');
      }

      if ((extractedStats.converted ?? 0) > 0) {
        addLog('process', `${(extractedStats.converted ?? 0).toLocaleString()} procedimentos dual convertidos para BPA-C`, 'info');
      }

      // Fase 5: Salvamento
      setCurrentPhase('save');
      addLog('save', 'Dados salvos no banco de dados', 'success');

      // Valor financeiro
      const valorTotal = valoresStats.total || 0;
      if (valorTotal > 0) {
        const valorFormatado = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorTotal);
        addLog('save', `Valor total estimado: ${valorFormatado}`, 'success');
      }

      // Fase 6: Concluído
      setCurrentPhase('complete');
      addLog('complete', 'Extração concluída com sucesso!', 'success', `Tempo total: ${elapsed}s`);

      // Erros durante o processo
      if (result.errors && result.errors.length > 0) {
        addLog('error', `${result.errors.length} avisos durante o processo`, 'warning');
        result.errors.slice(0, 3).forEach((err: string) => {
          addLog('error', err, 'warning');
        });
      }

      setExtractionResult({
        success: result.success,
        message: result.message,
        stats: result.stats
      });

      // Recarrega a visão do banco
      loadDatabaseOverview();

    } catch (error: any) {
      setCurrentPhase('error');
      addLog('error', 'Falha na extração', 'error', error.message);
      setExtractionResult({
        success: false,
        message: error.message || 'Erro de conexão'
      });
    } finally {
      setExtracting(false);
    }
  };

  // Agrupa dados por CNES
  const getDataByCnes = (cnes: string) => {
    if (!overview) return { bpa_i: [], bpa_c: [] };

    return {
      bpa_i: overview.bpa_i.filter(item => item.cnes === cnes),
      bpa_c: overview.bpa_c.filter(item => item.cnes === cnes)
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Carregando dados...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <Database className="w-7 h-7 text-blue-600" />
                Gerenciamento de Dados
              </h1>
              <p className="text-gray-500 mt-1">
                Visualize, extraia e gerencie dados do sistema
              </p>
            </div>

            <button
              onClick={loadDatabaseOverview}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4" />
              Atualizar
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mt-6 border-b border-gray-200">
            <button
              onClick={() => setSelectedTab('dashboard')}
              className={`pb-3 px-2 font-medium transition-colors ${selectedTab === 'dashboard'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
                }`}
            >
              <Activity className="w-4 h-4 inline mr-2" />
              Dashboard Financeiro
            </button>
            <button
              onClick={() => setSelectedTab('visao')}
              className={`pb-3 px-2 font-medium transition-colors ${selectedTab === 'visao'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
                }`}
            >
              <Database className="w-4 h-4 inline mr-2" />
              Visão do Banco
            </button>
            <button
              onClick={() => setSelectedTab('extracao')}
              className={`pb-3 px-2 font-medium transition-colors ${selectedTab === 'extracao'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
                }`}
            >
              <Cloud className="w-4 h-4 inline mr-2" />
              Extração BiServer
            </button>
            <button
              onClick={() => setSelectedTab('inconsistencias')}
              className={`pb-3 px-2 font-medium transition-colors ${selectedTab === 'inconsistencias'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
                }`}
            >
              <AlertCircle className="w-4 h-4 inline mr-2" />
              Inconsistências
            </button>
            <button
              onClick={() => setSelectedTab('historico')}
              className={`pb-3 px-2 font-medium transition-colors ${selectedTab === 'historico'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
                }`}
            >
              <Calendar className="w-4 h-4 inline mr-2" />
              Histórico de Extrações
            </button>
          </div>
        </div>

        {/* Aba Dashboard */}
        {
          selectedTab === 'dashboard' && (
            <FinancialDashboard cnesList={overview?.cnes_list || []} />
          )
        }

        {/* Estatísticas Gerais */}
        {
          selectedTab === 'visao' && overview && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <Building2 className="w-5 h-5 text-blue-600" />
                    <span className="text-xs text-gray-500">CNES</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-800">{overview.total_cnes}</p>
                  <p className="text-xs text-gray-500 mt-1">Estabelecimentos</p>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <span className="text-xs text-gray-500">BPA-I</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-800">{(overview.totals?.bpa_i ?? 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-500 mt-1">Registros</p>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                    <span className="text-xs text-gray-500">BPA-C</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-800">{(overview.totals?.bpa_c ?? 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-500 mt-1">Registros</p>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <Database className="w-5 h-5 text-purple-600" />
                    <span className="text-xs text-gray-500">Total</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-800">
                    {((overview.totals?.bpa_i ?? 0) + (overview.totals?.bpa_c ?? 0)).toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Registros BPA</p>
                </div>
              </div>

              {/* Lista de CNES */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <h3 className="font-semibold text-gray-800">Dados por Estabelecimento</h3>
                </div>

                <div className="divide-y divide-gray-200">
                  {overview.cnes_list.map(cnes => {
                    const data = getDataByCnes(cnes);
                    const estabelecimento = getEstabelecimentoByCnes(cnes);
                    const totalBpaI = data.bpa_i.reduce((sum, item) => sum + item.total, 0);
                    const totalBpaC = data.bpa_c.reduce((sum, item) => sum + item.total, 0);

                    return (
                      <div key={cnes} className="p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <Building2 className="w-5 h-5 text-blue-600" />
                            <div>
                              <p className="font-semibold text-gray-800">
                                {estabelecimento?.nome || `CNES ${cnes}`}
                              </p>
                              <p className="text-sm text-gray-500">CNES: {cnes}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <p className="text-sm text-gray-500">BPA-I</p>
                              <p className="font-semibold text-blue-600">{totalBpaI.toLocaleString()}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-gray-500">BPA-C</p>
                              <p className="font-semibold text-green-600">{totalBpaC.toLocaleString()}</p>
                            </div>

                            <button
                              onClick={() => setSelectedCnes(selectedCnes === cnes ? '' : cnes)}
                              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                            >
                              {selectedCnes === cnes ? 'Ocultar' : 'Detalhes'}
                            </button>
                          </div>
                        </div>

                        {/* Detalhes expandidos */}
                        {selectedCnes === cnes && (
                          <div className="mt-4 pl-8 space-y-3">
                            {/* BPA-I por competência */}
                            {data.bpa_i.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                                  <FileText className="w-4 h-4" />
                                  BPA Individualizado
                                </p>
                                <div className="space-y-2">
                                  {data.bpa_i.map(item => (
                                    <div key={`${item.cnes}-${item.competencia}`}
                                      className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                                      <div className="flex items-center gap-4">
                                        <Calendar className="w-4 h-4 text-blue-600" />
                                        <span className="font-medium text-gray-800">
                                          {item.competencia.slice(0, 4)}/{item.competencia.slice(4)}
                                        </span>
                                        <span className="text-sm text-gray-600">
                                          {item.total.toLocaleString()} registros
                                        </span>
                                        <span className="text-xs text-gray-500">
                                          Pendentes: {item.pendentes} | Exportados: {item.exportados}
                                        </span>
                                      </div>

                                      <button
                                        onClick={() => setDeleteConfirm({
                                          cnes: item.cnes,
                                          competencia: item.competencia,
                                          tipo: 'bpa_i'
                                        })}
                                        className="text-red-600 hover:text-red-700 p-2"
                                        title="Deletar competência"
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* BPA-C por competência */}
                            {data.bpa_c.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                                  <TrendingUp className="w-4 h-4" />
                                  BPA Consolidado
                                </p>
                                <div className="space-y-2">
                                  {data.bpa_c.map(item => (
                                    <div key={`${item.cnes}-${item.competencia}`}
                                      className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                                      <div className="flex items-center gap-4">
                                        <Calendar className="w-4 h-4 text-green-600" />
                                        <span className="font-medium text-gray-800">
                                          {item.competencia.slice(0, 4)}/{item.competencia.slice(4)}
                                        </span>
                                        <span className="text-sm text-gray-600">
                                          {item.total.toLocaleString()} registros
                                        </span>
                                        <span className="text-xs text-gray-500">
                                          Pendentes: {item.pendentes} | Exportados: {item.exportados}
                                        </span>
                                      </div>

                                      <button
                                        onClick={() => setDeleteConfirm({
                                          cnes: item.cnes,
                                          competencia: item.competencia,
                                          tipo: 'bpa_c'
                                        })}
                                        className="text-red-600 hover:text-red-700 p-2"
                                        title="Deletar competência"
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Ações para todo o CNES */}
                            <div className="pt-2 border-t border-gray-200 flex gap-2">
                              <button
                                onClick={() => setDeleteConfirm({ cnes, tipo: 'all' })}
                                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                              >
                                <Trash2 className="w-4 h-4" />
                                Deletar todos os dados deste CNES
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )
        }

        {/* Aba de Extração */}
        {
          selectedTab === 'extracao' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center gap-2">
                  <Cloud className="w-5 h-5 text-blue-600" />
                  Extração Automática BiServer
                </h3>
                <p className="text-sm text-gray-500">
                  🆕 Extrai e separa automaticamente BPA-I e BPA-C em uma única operação usando SIGTAP
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Building2 className="w-4 h-4 inline mr-1" />
                    Estabelecimento
                  </label>
                  <select
                    value={extractionCnes}
                    onChange={(e) => setExtractionCnes(e.target.value)}
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
                    Competência
                  </label>
                  <select
                    value={extractionComp}
                    onChange={(e) => setExtractionComp(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {(() => {
                      const options = [];
                      const now = new Date();
                      const currentYear = now.getFullYear();
                      const currentMonth = now.getMonth() + 1;

                      // Gera últimos 12 meses
                      for (let i = 0; i < 12; i++) {
                        let year = currentYear;
                        let month = currentMonth - i;

                        if (month <= 0) {
                          month += 12;
                          year -= 1;
                        }

                        const comp = `${year}${String(month).padStart(2, '0')}`;
                        const monthName = new Date(year, month - 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });

                        options.push(
                          <option key={comp} value={comp}>
                            {monthName.charAt(0).toUpperCase() + monthName.slice(1)}
                          </option>
                        );
                      }

                      return options;
                    })()}
                  </select>
                </div>
              </div>

              {/* Info SIGTAP */}
              <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg mb-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-purple-600 mt-0.5" />
                  <div>
                    <span className="text-sm font-medium text-gray-800">
                      ✅ Extração automática sem limite
                    </span>
                    <p className="text-xs text-gray-600 mt-0.5">
                      Todos os registros serão extraídos automaticamente. O sistema separa BPA-I e BPA-C usando SIGTAP e agrega consolidados para evitar duplicações.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleExtractAll}
                disabled={extracting || !extractionCnes || !extractionComp}
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
              >
                {extracting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Extraindo e separando automaticamente...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    Extrair e Salvar Tudo
                  </>
                )}
              </button>

              {/* Console de Extração com Logs */}
              {(extracting || logs.length > 0) && (
                <div className="mt-6">
                  {/* Barra de Progresso */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      {['connect', 'download', 'filter', 'process', 'save', 'complete'].map((phase, index, arr) => {
                        const phaseIndex = arr.indexOf(phase);
                        const currentIndex = arr.indexOf(currentPhase);
                        const isCompleted = currentPhase === 'error' ? false : phaseIndex < currentIndex;
                        const isActive = phase === currentPhase;
                        const isError = currentPhase === 'error';

                        const icons: Record<string, React.ReactNode> = {
                          connect: <Cloud className="w-4 h-4" />,
                          download: <Download className="w-4 h-4" />,
                          filter: <Filter className="w-4 h-4" />,
                          process: <Zap className="w-4 h-4" />,
                          save: <Save className="w-4 h-4" />,
                          complete: <CheckCircle className="w-4 h-4" />
                        };

                        const labels: Record<string, string> = {
                          connect: 'Conectar',
                          download: 'Baixar',
                          filter: 'Filtrar',
                          process: 'Processar',
                          save: 'Salvar',
                          complete: 'Concluir'
                        };

                        return (
                          <React.Fragment key={phase}>
                            <div className="flex flex-col items-center">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${isCompleted ? 'bg-green-500 text-white' :
                                  isActive ? 'bg-blue-500 text-white animate-pulse' :
                                    isError && phase === currentPhase ? 'bg-red-500 text-white' :
                                      'bg-gray-200 text-gray-400'
                                }`}>
                                {isActive && !isError ? <Loader2 className="w-4 h-4 animate-spin" /> : icons[phase]}
                              </div>
                              <span className={`text-xs mt-1 ${isCompleted ? 'text-green-600' :
                                  isActive ? 'text-blue-600 font-medium' :
                                    'text-gray-400'
                                }`}>{labels[phase]}</span>
                            </div>
                            {index < arr.length - 1 && (
                              <div className={`flex-1 h-0.5 mx-1 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'
                                }`} />
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>

                    {/* Stats em tempo real */}
                    {liveStats && (
                      <div className="grid grid-cols-4 gap-2 mt-3 text-center">
                        <div className="bg-blue-50 rounded p-2">
                          <div className="text-lg font-bold text-blue-600">{(liveStats.total_api || 0).toLocaleString()}</div>
                          <div className="text-xs text-blue-500">Da API</div>
                        </div>
                        <div className="bg-green-50 rounded p-2">
                          <div className="text-lg font-bold text-green-600">{(liveStats.bpa_i || 0).toLocaleString()}</div>
                          <div className="text-xs text-green-500">BPA-I</div>
                        </div>
                        <div className="bg-purple-50 rounded p-2">
                          <div className="text-lg font-bold text-purple-600">{(liveStats.bpa_c || 0).toLocaleString()}</div>
                          <div className="text-xs text-purple-500">BPA-C</div>
                        </div>
                        <div className="bg-orange-50 rounded p-2">
                          <div className="text-lg font-bold text-orange-600">{(liveStats.removed || 0).toLocaleString()}</div>
                          <div className="text-xs text-orange-500">Removidos</div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Log Terminal */}
                  <div className="bg-gray-900 rounded-lg p-3 font-mono text-xs max-h-48 overflow-y-auto">
                    {logs.map((log) => (
                      <div key={log.id} className="flex items-start gap-2 py-1 border-b border-gray-800 last:border-0">
                        <span className="text-gray-500 shrink-0">
                          [{log.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
                        </span>
                        <span className={`shrink-0 p-1 rounded ${log.type === 'success' ? 'text-green-600 bg-green-900/30' :
                            log.type === 'warning' ? 'text-yellow-600 bg-yellow-900/30' :
                              log.type === 'error' ? 'text-red-600 bg-red-900/30' :
                                'text-blue-600 bg-blue-900/30'
                          }`}>
                          {log.phase === 'connect' && <Cloud className="w-3 h-3" />}
                          {log.phase === 'download' && <Download className="w-3 h-3" />}
                          {log.phase === 'filter' && <Filter className="w-3 h-3" />}
                          {log.phase === 'process' && <Zap className="w-3 h-3" />}
                          {log.phase === 'save' && <Save className="w-3 h-3" />}
                          {log.phase === 'complete' && <CheckCircle className="w-3 h-3" />}
                          {log.phase === 'error' && <XCircle className="w-3 h-3" />}
                        </span>
                        <div className="flex-1">
                          <span className={`${log.type === 'success' ? 'text-green-400' :
                              log.type === 'warning' ? 'text-yellow-400' :
                                log.type === 'error' ? 'text-red-400' :
                                  'text-gray-300'
                            }`}>
                            {log.message}
                          </span>
                          {log.details && (
                            <span className="text-gray-500 ml-2">{log.details}</span>
                          )}
                        </div>
                      </div>
                    ))}
                    {extracting && (
                      <div className="flex items-center gap-2 py-2 text-blue-400">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span className="animate-pulse">Processando...</span>
                      </div>
                    )}
                    <div ref={logEndRef} />
                  </div>

                  {/* Botão Limpar */}
                  {!extracting && logs.length > 0 && (
                    <button
                      onClick={() => { setLogs([]); setCurrentPhase(''); setLiveStats(null); }}
                      className="mt-2 text-sm text-gray-500 hover:text-gray-700"
                    >
                      Limpar console
                    </button>
                  )}
                </div>
              )}

              {/* Resultado da extração */}
              {extractionResult && (
                <div className={`mt-6 p-4 rounded-lg ${extractionResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                  }`}>
                  <div className="flex items-start gap-3">
                    {extractionResult.success ? (
                      <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className={`font-medium ${extractionResult.success ? 'text-green-800' : 'text-red-800'
                        }`}>
                        {extractionResult.message}
                      </p>
                      {extractionResult.success && extractionResult.stats && (
                        <div className="mt-3 space-y-3">
                          {/* Totais */}
                          <div className="grid grid-cols-3 gap-2">
                            <div className="bg-white rounded p-2 border border-green-200">
                              <p className="text-xs text-gray-600">BPA-I</p>
                              <p className="font-semibold text-blue-700">{extractionResult.stats.saved?.bpa_i?.toLocaleString()}</p>
                              {extractionResult.stats.valores?.bpa_i && (
                                <p className="text-xs text-gray-500">R$ {extractionResult.stats.valores.bpa_i.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                              )}
                            </div>
                            <div className="bg-white rounded p-2 border border-green-200">
                              <p className="text-xs text-gray-600">BPA-C</p>
                              <p className="font-semibold text-green-700">{extractionResult.stats.saved?.bpa_c?.toLocaleString()}</p>
                              {extractionResult.stats.valores?.bpa_c && (
                                <p className="text-xs text-gray-500">R$ {extractionResult.stats.valores.bpa_c.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                              )}
                            </div>
                            <div className="bg-white rounded p-2 border border-green-200">
                              <p className="text-xs text-gray-600">Valor Total</p>
                              <p className="font-semibold text-purple-700">
                                R$ {extractionResult.stats.valores?.total?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </p>
                              <p className="text-xs text-gray-500">{extractionResult.stats.duracao_segundos}s</p>
                            </div>
                          </div>

                          {/* Top procedimentos */}
                          {extractionResult.stats.procedimentos_mais_usados && extractionResult.stats.procedimentos_mais_usados.length > 0 && (
                            <div className="bg-white rounded p-3 border border-green-200">
                              <p className="text-xs font-medium text-gray-700 mb-2">🏆 Procedimentos Mais Realizados:</p>
                              <div className="space-y-1">
                                {extractionResult.stats.procedimentos_mais_usados.map((proc: any, idx: number) => (
                                  <div key={idx} className="flex justify-between text-xs">
                                    <span className="text-gray-700 truncate max-w-[60%]">
                                      {idx + 1}. {proc.codigo} - {proc.nome}
                                    </span>
                                    <span className="text-gray-600">
                                      {proc.quantidade}x | R$ {(proc.valor_total ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        }

        {/* Aba de Inconsistências */}
        {
          selectedTab === 'inconsistencias' && (
            <InconsistenciesTab />
          )
        }

        {/* Aba de Histórico */}
        {
          selectedTab === 'historico' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  Histórico de Extrações
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleFixEncoding}
                    disabled={fixingEncoding || loadingHistorico}
                    className="flex items-center gap-2 px-4 py-2 text-orange-600 border border-orange-600 rounded-lg hover:bg-orange-50 disabled:opacity-50"
                    title="Corrige caracteres especiais nos nomes dos procedimentos"
                  >
                    <FileText className={`w-4 h-4 ${fixingEncoding ? 'animate-pulse' : ''}`} />
                    {fixingEncoding ? 'Corrigindo...' : 'Corrigir Encoding'}
                  </button>
                  <button
                    onClick={() => loadHistorico(0)}
                    disabled={loadingHistorico}
                    className="flex items-center gap-2 px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${loadingHistorico ? 'animate-spin' : ''}`} />
                    Atualizar
                  </button>
                </div>
              </div>

              {loadingHistorico ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  <span className="ml-2 text-gray-600">Carregando histórico...</span>
                </div>
              ) : historico && historico.records.length > 0 ? (
                <>
                  <div className="space-y-4">
                    {historico.records.map((record: any) => (
                      <div key={record.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-blue-600" />
                              CNES: {record.cnes}
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">
                              Competência: {record.competencia} | {new Date(record.created_at).toLocaleString('pt-BR')}
                            </p>
                            {record.usuario_nome && (
                              <p className="text-xs text-gray-400">Por: {record.usuario_nome}</p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-blue-600">
                              R$ {record.valor_total_geral.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            <p className="text-xs text-gray-500">{record.duracao_segundos}s</p>
                          </div>
                        </div>

                        {/* Estatísticas */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                          <div className="bg-blue-50 rounded p-2">
                            <p className="text-xs text-gray-600">BPA-I</p>
                            <p className="text-lg font-semibold text-blue-700">{record.total_bpa_i.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">R$ {record.valor_total_bpa_i.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                          </div>
                          <div className="bg-green-50 rounded p-2">
                            <p className="text-xs text-gray-600">BPA-C</p>
                            <p className="text-lg font-semibold text-green-700">{record.total_bpa_c.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">R$ {record.valor_total_bpa_c.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                          </div>
                          <div className="bg-yellow-50 rounded p-2">
                            <p className="text-xs text-gray-600">Removidos</p>
                            <p className="text-lg font-semibold text-yellow-700">{record.total_removido.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">SIGTAP</p>
                          </div>
                          <div className="bg-purple-50 rounded p-2">
                            <p className="text-xs text-gray-600">Total</p>
                            <p className="text-lg font-semibold text-purple-700">{record.total_geral.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">Registros</p>
                          </div>
                        </div>

                        {/* Procedimentos mais usados */}
                        {record.procedimentos_mais_usados && record.procedimentos_mais_usados.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-600 mb-2">Top Procedimentos:</p>
                            <div className="space-y-1">
                              {record.procedimentos_mais_usados.slice(0, 3).map((proc: any, idx: number) => (
                                <div key={idx} className="flex justify-between text-xs">
                                  <span className="text-gray-700 truncate max-w-[60%]">
                                    {proc.codigo} - {proc.nome}
                                  </span>
                                  <span className="text-gray-500">
                                    {proc.quantidade}x | R$ {proc.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Paginação */}
                  {historico.total > historicoLimit && (
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                      <p className="text-sm text-gray-600">
                        Mostrando {historicoPage * historicoLimit + 1} - {Math.min((historicoPage + 1) * historicoLimit, historico.total)} de {historico.total}
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => loadHistorico(historicoPage - 1)}
                          disabled={historicoPage === 0}
                          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Anterior
                        </button>
                        <button
                          onClick={() => loadHistorico(historicoPage + 1)}
                          disabled={(historicoPage + 1) * historicoLimit >= historico.total}
                          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Próxima
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Nenhuma extração realizada ainda</p>
                </div>
              )}
            </div>
          )
        }

        {/* Modal de Confirmação de Deleção */}
        {
          deleteConfirm && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                  <h3 className="text-lg font-semibold text-gray-800">Confirmar Deleção</h3>
                </div>

                <p className="text-gray-600 mb-4">
                  Tem certeza que deseja deletar os seguintes dados?
                </p>

                <div className="bg-gray-50 p-4 rounded-lg mb-6 space-y-2 text-sm">
                  <p><span className="font-medium">CNES:</span> {deleteConfirm.cnes}</p>
                  {deleteConfirm.competencia && (
                    <p><span className="font-medium">Competência:</span> {deleteConfirm.competencia}</p>
                  )}
                  <p><span className="font-medium">Tipo:</span> {
                    deleteConfirm.tipo === 'all' ? 'Todos os dados' :
                      deleteConfirm.tipo === 'bpa_i' ? 'BPA Individualizado' :
                        deleteConfirm.tipo === 'bpa_c' ? 'BPA Consolidado' :
                          deleteConfirm.tipo
                  }</p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteConfirm(null)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                    disabled={deleting}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {deleting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Deletando...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4" />
                        Deletar
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )
        }
      </div >
    </div >
  );
};

export default DataManagementPage;
