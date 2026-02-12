import React, { useState, useRef, useEffect } from 'react';
import { 
  Cloud, 
  Download, 
  Loader2, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  RefreshCw,
  Info,
  Building2,
  Clock,
  Filter,
  Zap,
  Save,
  Terminal
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ESTABELECIMENTOS, getEstabelecimentoByCnes } from '../constants/estabelecimentos';

interface SaveResult {
  success: boolean;
  saved: number;
  errors: string[];
  message: string;
}

// Tipos para os logs
interface LogEntry {
  id: number;
  timestamp: Date;
  phase: 'connect' | 'download' | 'filter' | 'process' | 'save' | 'complete' | 'error';
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  details?: string;
}

// Componente de Log Visual
const ExtractionLog: React.FC<{ logs: LogEntry[], isExtracting: boolean }> = ({ logs, isExtracting }) => {
  const logEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getPhaseIcon = (phase: LogEntry['phase']) => {
    switch (phase) {
      case 'connect': return <Cloud className="w-4 h-4" />;
      case 'download': return <Download className="w-4 h-4" />;
      case 'filter': return <Filter className="w-4 h-4" />;
      case 'process': return <Zap className="w-4 h-4" />;
      case 'save': return <Save className="w-4 h-4" />;
      case 'complete': return <CheckCircle className="w-4 h-4" />;
      case 'error': return <XCircle className="w-4 h-4" />;
      default: return <Terminal className="w-4 h-4" />;
    }
  };

  const getTypeColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'success': return 'text-green-600 bg-green-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  if (logs.length === 0 && !isExtracting) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-gray-400">
        <Terminal className="w-10 h-10 mb-2 opacity-50" />
        <p className="text-sm">Aguardando extração...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-3 font-mono text-xs max-h-64 overflow-y-auto">
      {logs.map((log) => (
        <div key={log.id} className="flex items-start gap-2 py-1 border-b border-gray-800 last:border-0">
          <span className="text-gray-500 shrink-0">[{formatTime(log.timestamp)}]</span>
          <span className={`shrink-0 p-1 rounded ${getTypeColor(log.type)}`}>
            {getPhaseIcon(log.phase)}
          </span>
          <div className="flex-1">
            <span className={`${
              log.type === 'success' ? 'text-green-400' :
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
      {isExtracting && (
        <div className="flex items-center gap-2 py-2 text-blue-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="animate-pulse">Processando...</span>
        </div>
      )}
      <div ref={logEndRef} />
    </div>
  );
};

// Componente de Progresso por Fases
const ExtractionProgress: React.FC<{ currentPhase: string, stats: any }> = ({ currentPhase, stats }) => {
  const phases = [
    { id: 'connect', label: 'Conectando', icon: Cloud },
    { id: 'download', label: 'Baixando', icon: Download },
    { id: 'filter', label: 'Filtrando SIGTAP', icon: Filter },
    { id: 'process', label: 'Processando', icon: Zap },
    { id: 'save', label: 'Salvando', icon: Save },
    { id: 'complete', label: 'Concluído', icon: CheckCircle },
  ];

  const getPhaseStatus = (phaseId: string) => {
    const phaseIndex = phases.findIndex(p => p.id === phaseId);
    const currentIndex = phases.findIndex(p => p.id === currentPhase);
    
    if (currentPhase === 'error') return 'error';
    if (phaseIndex < currentIndex) return 'completed';
    if (phaseIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between">
        {phases.map((phase, index) => {
          const status = getPhaseStatus(phase.id);
          const Icon = phase.icon;
          
          return (
            <React.Fragment key={phase.id}>
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  status === 'completed' ? 'bg-green-500 text-white' :
                  status === 'active' ? 'bg-blue-500 text-white animate-pulse' :
                  status === 'error' ? 'bg-red-500 text-white' :
                  'bg-gray-200 text-gray-400'
                }`}>
                  {status === 'active' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>
                <span className={`text-xs mt-1 ${
                  status === 'completed' ? 'text-green-600 font-medium' :
                  status === 'active' ? 'text-blue-600 font-medium' :
                  'text-gray-400'
                }`}>
                  {phase.label}
                </span>
              </div>
              {index < phases.length - 1 && (
                <div className={`flex-1 h-1 mx-2 rounded transition-all duration-500 ${
                  getPhaseStatus(phases[index + 1].id) !== 'pending' ? 'bg-green-500' : 'bg-gray-200'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
      
      {/* Stats em tempo real */}
      {stats && (
        <div className="grid grid-cols-4 gap-2 mt-4 text-center">
          <div className="bg-blue-50 rounded p-2">
            <div className="text-lg font-bold text-blue-600">{stats.total_api || 0}</div>
            <div className="text-xs text-blue-500">Da API</div>
          </div>
          <div className="bg-green-50 rounded p-2">
            <div className="text-lg font-bold text-green-600">{stats.bpa_i || 0}</div>
            <div className="text-xs text-green-500">BPA-I</div>
          </div>
          <div className="bg-purple-50 rounded p-2">
            <div className="text-lg font-bold text-purple-600">{stats.bpa_c || 0}</div>
            <div className="text-xs text-purple-500">BPA-C</div>
          </div>
          <div className="bg-orange-50 rounded p-2">
            <div className="text-lg font-bold text-orange-600">{stats.removed || 0}</div>
            <div className="text-xs text-orange-500">Removidos</div>
          </div>
        </div>
      )}
    </div>
  );
};

const BiServerExtractionPage: React.FC = () => {
  const { user } = useAuth();
  const [extracting, setExtracting] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'error'>('unknown');
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  
  // Estados para logs e progresso
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [currentPhase, setCurrentPhase] = useState<string>('');
  const [liveStats, setLiveStats] = useState<any>(null);
  const [saveResult, setSaveResult] = useState<SaveResult | null>(null);
  const logIdRef = useRef(0);
  
  // Form state
  const [cnes, setCnes] = useState(user?.cnes || '');
  const [competencia, setCompetencia] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

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

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const testConnection = async () => {
    setTestingConnection(true);
    try {
      const response = await fetch('/api/biserver/test-connection', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.success) {
        setConnectionStatus('connected');
        if (data.mock) {
          showMessage('info', 'Modo MOCK ativo - usando dados simulados para desenvolvimento');
        } else {
          showMessage('success', 'Conexão com BiServer estabelecida!');
        }
      } else {
        setConnectionStatus('error');
        showMessage('error', `Erro de conexão: ${data.error}`);
      }
    } catch (error) {
      setConnectionStatus('error');
      showMessage('error', 'Erro ao testar conexão com BiServer');
    } finally {
      setTestingConnection(false);
    }
  };

  // NOVO: Extração unificada com logs em tempo real
  const extractAndSave = async () => {
    if (!cnes || !competencia) {
      showMessage('error', 'Preencha CNES e Competência');
      return;
    }

    // Limpa estado anterior
    setLogs([]);
    setLiveStats(null);
    setSaveResult(null);
    setExtracting(true);
    
    const estabelecimento = getEstabelecimentoByCnes(cnes);
    const nomeEstab = estabelecimento?.sigla || cnes;
    
    try {
      // Fase 1: Conectando
      setCurrentPhase('connect');
      addLog('connect', `Iniciando extração para ${nomeEstab}`, 'info', `CNES: ${cnes}, Competência: ${competencia}`);
      addLog('connect', 'Conectando à API BiServer...', 'info');
      await new Promise(resolve => setTimeout(resolve, 500)); // Pequena pausa para UX
      addLog('connect', 'Conexão estabelecida com bi.eSUS', 'success');

      // Fase 2: Download
      setCurrentPhase('download');
      addLog('download', 'Iniciando download dos dados...', 'info');
      addLog('download', 'Buscando páginas da API (10.000 registros por página)', 'info');
      
      // Chama o endpoint unificado
      const startTime = Date.now();
      const response = await fetch(
        `/api/biserver/extract-and-separate?cnes=${cnes}&competencia=${competencia}`,
        {
          method: 'POST',
          headers: getAuthHeaders()
        }
      );
      
      const data = await response.json();
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      
      if (!response.ok) {
        throw new Error(data.detail || 'Erro na extração');
      }

      // Mapeia stats da API (formato: stats.extracted e stats.saved)
      const extractedStats = data.stats?.extracted || {};
      const savedStats = data.stats?.saved || {};
      const valoresStats = data.stats?.valores || {};
      const correctionsStats = data.stats?.corrections || {};
      
      const totalExtracted = extractedStats.total || 0;
      const bpaI = savedStats.bpa_i || 0;
      const bpaC = savedStats.bpa_c || 0;
      const removed = extractedStats.removed || extractedStats.removed_sem_registro || 0;
      const converted = extractedStats.converted || 0;
      
      setLiveStats({
        total_api: totalExtracted,
        bpa_i: bpaI,
        bpa_c: bpaC,
        removed: removed
      });

      addLog('download', `Download concluído em ${elapsed}s`, 'success', `${totalExtracted} registros da API`);

      // Fase 3: Filtro SIGTAP
      setCurrentPhase('filter');
      addLog('filter', 'Aplicando filtros SIGTAP...', 'info');
      
      if (removed > 0) {
        addLog('filter', `${removed} registros sem tipo BPA (e-SUS, RAAS, etc)`, 'warning');
      }
      
      addLog('filter', 'Classificando procedimentos por tipo de registro', 'info');
      await new Promise(resolve => setTimeout(resolve, 300));
      addLog('filter', 'Filtro SIGTAP aplicado', 'success');

      // Fase 4: Processamento
      setCurrentPhase('process');
      addLog('process', 'Separando BPA-I e BPA-C...', 'info');
      
      if (bpaI > 0) {
        addLog('process', `${bpaI} registros BPA Individualizado`, 'info');
      }
      if (bpaC > 0) {
        addLog('process', `${bpaC} registros BPA Consolidado (agregados)`, 'info');
      }
      
      if (converted > 0) {
        addLog('process', `${converted} procedimentos dual convertidos para BPA-C`, 'info');
      }

      // Correções aplicadas
      const corrBpi = correctionsStats.bpai || null;
      const corrBpc = correctionsStats.bpac || null;

      if (corrBpi) {
        const corrInfo = `corrigidos=${corrBpi.corrected || 0}, removidos=${corrBpi.deleted || 0}`;
        addLog('process', `Correções BPA-I aplicadas (${corrInfo})`, 'info');

        if (corrBpi.correction_types) {
          const top = Object.entries(corrBpi.correction_types)
            .sort((a: any, b: any) => b[1] - a[1])
            .slice(0, 3)
            .map(([k, v]) => `${k}=${v}`)
            .join(', ');
          if (top) {
            addLog('process', 'Tipos de correção BPA-I (top 3)', 'info', top);
          }
        }
      }

      if (corrBpc) {
        const corrInfo = `corrigidos=${corrBpc.corrected || 0}, removidos=${corrBpc.deleted || 0}`;
        addLog('process', `Correções BPA-C aplicadas (${corrInfo})`, 'info');
      }

      // Fase 5: Salvamento
      setCurrentPhase('save');
      addLog('save', 'Salvando no banco de dados...', 'info');
      
      await new Promise(resolve => setTimeout(resolve, 300));
      
      if (bpaI > 0) {
        addLog('save', `${bpaI} registros BPA-I salvos`, 'success');
      }
      if (bpaC > 0) {
        addLog('save', `${bpaC} registros BPA-C salvos`, 'success');
      }

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
      if (data.errors && data.errors.length > 0) {
        addLog('error', `${data.errors.length} erros durante o processo`, 'warning');
        data.errors.slice(0, 3).forEach((err: string) => {
          addLog('error', err, 'error');
        });
      }

      // Atualiza resultado
      setSaveResult({
        success: true,
        saved: bpaI + bpaC,
        errors: data.errors || [],
        message: data.message || 'Extração concluída'
      });

      showMessage('success', `Extração concluída: ${bpaI} BPA-I + ${bpaC} BPA-C salvos`);
      
    } catch (error: any) {
      setCurrentPhase('error');
      addLog('error', 'Falha na extração', 'error', error.message);
      showMessage('error', error.message || 'Erro ao conectar com o servidor');
    } finally {
      setExtracting(false);
    }
  };

  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Cloud className="w-7 h-7 text-primary-600" />
          Extração BiServer (bi.eSUS)
        </h2>
        <p className="text-gray-500 mt-1">
          Extrai dados de produção da API do Genie para importação no Firebird
        </p>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-4 p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
          message.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>
          {message.type === 'success' && <CheckCircle className="w-5 h-5" />}
          {message.type === 'error' && <XCircle className="w-5 h-5" />}
          {message.type === 'info' && <Info className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Resultado da Inserção no Banco */}
      {saveResult && (
        <div className={`mb-4 p-4 rounded-lg border ${
          saveResult.success 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            {saveResult.success ? (
              <CheckCircle className="w-6 h-6 text-green-500" />
            ) : (
              <XCircle className="w-6 h-6 text-red-500" />
            )}
            <h3 className={`font-semibold ${saveResult.success ? 'text-green-800' : 'text-red-800'}`}>
              {saveResult.success ? 'Inserção Concluída!' : 'Erro na Inserção'}
            </h3>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mt-3">
            <div className="bg-white rounded p-3 border">
              <div className="text-2xl font-bold text-green-600">{saveResult.saved}</div>
              <div className="text-sm text-gray-500">Registros salvos</div>
            </div>
            <div className="bg-white rounded p-3 border">
              <div className={`text-2xl font-bold ${saveResult.errors.length > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                {saveResult.errors.length}
              </div>
              <div className="text-sm text-gray-500">Erros</div>
            </div>
          </div>

          {saveResult.errors.length > 0 && (
            <div className="mt-3">
              <div className="text-sm font-medium text-red-700 mb-1">Erros encontrados:</div>
              <div className="max-h-32 overflow-y-auto bg-white rounded p-2 border border-red-200">
                {saveResult.errors.map((err, idx) => (
                  <div key={idx} className="text-xs text-red-600 py-1 border-b border-red-100 last:border-0">
                    {err}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => setSaveResult(null)}
            className="mt-3 text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Fechar
          </button>
        </div>
      )}

      {/* Fluxo de trabalho */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
          <Info className="w-5 h-5" />
          Extração Automática Unificada
        </h3>
        <p className="text-sm text-blue-700">
          O sistema extrai automaticamente todos os dados, separa BPA-I e BPA-C usando SIGTAP, 
          agrega consolidados para evitar duplicações e salva diretamente no banco.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Painel de Configuração */}
        <div className="lg:col-span-1 space-y-6">
          {/* Status Conexão */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="font-medium text-gray-800 mb-3">Status da API</h3>
            
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                {connectionStatus === 'connected' && (
                  <>
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-green-600 text-sm">Conectado</span>
                  </>
                )}
                {connectionStatus === 'error' && (
                  <>
                    <XCircle className="w-5 h-5 text-red-500" />
                    <span className="text-red-600 text-sm">Erro</span>
                  </>
                )}
                {connectionStatus === 'unknown' && (
                  <>
                    <AlertCircle className="w-5 h-5 text-gray-400" />
                    <span className="text-gray-500 text-sm">Não testado</span>
                  </>
                )}
              </div>
              
              <button
                onClick={testConnection}
                disabled={testingConnection}
                className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                {testingConnection ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <RefreshCw className="w-5 h-5" />
                )}
              </button>
            </div>
            
            <p className="text-xs text-gray-500">
              API: biserver.rb.adm.br
            </p>
          </div>

          {/* Formulário de Extração Simplificado */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="font-medium text-gray-800 mb-4">Parâmetros de Extração</h3>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="cnes-select" className="block text-sm font-medium text-gray-700 mb-1">
                  <Building2 className="w-4 h-4 inline mr-1" />
                  Estabelecimento
                </label>
                <select
                  id="cnes-select"
                  value={cnes}
                  onChange={(e) => setCnes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  disabled={extracting}
                  title="Selecione o estabelecimento"
                >
                  <option value="">Selecione o estabelecimento</option>
                  {ESTABELECIMENTOS.map((estab) => (
                    <option key={estab.cnes} value={estab.cnes}>
                      {estab.sigla} - {estab.cnes}
                    </option>
                  ))}
                </select>
                {cnes && getEstabelecimentoByCnes(cnes) && (
                  <p className="text-xs text-gray-500 mt-1">
                    {getEstabelecimentoByCnes(cnes)?.nome}
                  </p>
                )}
              </div>
              
              <div>
                <label htmlFor="competencia-input" className="block text-sm font-medium text-gray-700 mb-1">
                  <Clock className="w-4 h-4 inline mr-1" />
                  Competência
                </label>
                <input
                  id="competencia-input"
                  type="month"
                  value={`${competencia.slice(0, 4)}-${competencia.slice(4)}`}
                  onChange={(e) => setCompetencia(e.target.value.replace('-', ''))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  disabled={extracting}
                  title="Selecione a competência (mês/ano)"
                  placeholder="Selecione o mês"
                />
              </div>

              {/* Info box */}
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-700 mb-1">Extração sem limite</p>
                    <p>Todos os registros serão extraídos automaticamente. Procedimentos que são BPA-I e BPA-C ao mesmo tempo serão salvos apenas como BPA-C (agregado).</p>
                  </div>
                </div>
              </div>
              
              <button
                onClick={extractAndSave}
                disabled={extracting || !cnes || !competencia}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {extracting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Extraindo...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    Extrair e Salvar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Painel de Progresso e Logs */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 h-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-800 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-gray-600" />
                Console de Extração
              </h3>
              
              {logs.length > 0 && !extracting && (
                <button
                  onClick={() => { setLogs([]); setCurrentPhase(''); setLiveStats(null); setSaveResult(null); }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Limpar
                </button>
              )}
            </div>
            
            {/* Barra de Progresso */}
            {(extracting || currentPhase) && (
              <ExtractionProgress currentPhase={currentPhase} stats={liveStats} />
            )}
            
            {/* Log Visual */}
            <ExtractionLog logs={logs} isExtracting={extracting} />
            
            {/* Resultado Final */}
            {saveResult && !extracting && (
              <div className={`mt-4 p-4 rounded-lg border ${
                saveResult.success 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {saveResult.success ? (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  ) : (
                    <XCircle className="w-6 h-6 text-red-500" />
                  )}
                  <h3 className={`font-semibold ${saveResult.success ? 'text-green-800' : 'text-red-800'}`}>
                    {saveResult.success ? 'Extração Concluída!' : 'Erro na Extração'}
                  </h3>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div className="bg-white rounded p-3 border">
                    <div className="text-2xl font-bold text-green-600">{saveResult.saved}</div>
                    <div className="text-sm text-gray-500">Registros salvos</div>
                  </div>
                  <div className="bg-white rounded p-3 border">
                    <div className={`text-2xl font-bold ${saveResult.errors.length > 0 ? 'text-orange-600' : 'text-gray-400'}`}>
                      {saveResult.errors.length}
                    </div>
                    <div className="text-sm text-gray-500">Avisos/Erros</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BiServerExtractionPage;
