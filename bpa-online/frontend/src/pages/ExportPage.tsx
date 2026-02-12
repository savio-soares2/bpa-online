import React, { useState, useEffect } from 'react';
import { 
  Download, 
  FileText, 
  RefreshCw, 
  CheckCircle, 
  Clock,
  Database,
  Server,
  AlertCircle,
  File,
  Building2,
  Calendar
} from 'lucide-react';
import { 
  exportBPA, 
  listExports, 
  getBPAStats,
  resetExportStatus
} from '../services/api';
import { ESTABELECIMENTOS, getEstabelecimentoByCnes } from '../constants/estabelecimentos';
import type { 
  ExportRequest, 
  ExportFile, 
  BPAStats,
  Message 
} from '../types';

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

const ExportPage: React.FC = () => {
  const [cnes, setCnes] = useState('');
  const [competencia, setCompetencia] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [tipo, setTipo] = useState<'individualizado' | 'consolidado' | 'all'>('individualizado');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const [exports, setExports] = useState<ExportFile[]>([]);
  const [stats, setStats] = useState<BPAStats | null>(null);

  // Carrega estatísticas
  const loadStats = async () => {
    if (!cnes || !competencia) return;
    
    try {
      const data = await getBPAStats(cnes, competencia);
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const handleResetExports = async () => {
    if (!cnes || !competencia) {
      setMessage({ type: 'error', text: 'Informe CNES e Competência' });
      return;
    }

    const confirmReset = window.confirm(
      'Isso irá limpar o status de exportação para permitir nova exportação nesta competência. Deseja continuar?'
    );
    if (!confirmReset) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await resetExportStatus(cnes, competencia, 'all');
      setMessage({
        type: 'success',
        text: `Status de exportação resetado. BPA-I: ${result.bpai_reset} | BPA-C: ${result.bpac_reset}`
      });
      await loadStats();
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao limpar exportações' });
    } finally {
      setLoading(false);
    }
  };

  // Carrega lista de exportações
  const loadExports = async () => {
    try {
      const data = await listExports();
      setExports(data);
    } catch (error) {
      console.error('Erro ao carregar exportações:', error);
    }
  };

  // Exporta dados
  const handleExport = async () => {
    if (!cnes || !competencia) {
      setMessage({ type: 'error', text: 'Informe CNES e Competência' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const request: ExportRequest = { cnes, competencia, tipo };
      const result = await exportBPA(request);
      
      setMessage({ 
        type: 'success', 
        text: `Exportação concluída! ${result.total_registros} registros exportados para ${result.arquivo}` 
      });
      
      // Recarrega lista de exportações
      await loadExports();
      await loadStats();
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao exportar dados' });
    } finally {
      setLoading(false);
    }
  };

  // Baixa arquivo
  const handleDownload = (arquivo: string) => {
    window.open(`/api/export/download/${arquivo}`, '_blank');
  };

  useEffect(() => {
    loadExports();
  }, []);

  useEffect(() => {
    loadStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cnes, competencia]);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <Download className="w-7 h-7 text-primary-600" />
        Exportar para Firebird
      </h2>

      {/* Mensagem */}
      {message && (
        <div className={`p-4 rounded-lg mb-6 flex justify-between items-center ${
          message.type === 'success' ? 'bg-success-50 text-success-700 border border-success-500' :
          message.type === 'error' ? 'bg-danger-50 text-danger-600 border border-danger-500' :
          'bg-warning-50 text-warning-600 border border-warning-500'
        }`}>
          <span className="flex items-center gap-2">
            {message.type === 'success' && <CheckCircle className="w-5 h-5" />}
            {message.type === 'error' && <AlertCircle className="w-5 h-5" />}
            {message.text}
          </span>
          <button onClick={() => setMessage(null)} className="text-xl font-bold hover:opacity-70">×</button>
        </div>
      )}

      {/* Instruções */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
          <Server className="w-5 h-5" />
          Como funciona a exportação
        </h3>
        <ol className="text-blue-700 text-sm space-y-1 list-decimal list-inside">
          <li>Selecione o CNES e a competência que deseja exportar</li>
          <li>Escolha o tipo de BPA (Individualizado, Consolidado ou Ambos)</li>
          <li>Clique em "Exportar" para gerar o arquivo SQL</li>
          <li>Baixe o arquivo SQL gerado</li>
          <li>Importe no Firebird usando IBExpert ou similar</li>
        </ol>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Formulário de exportação */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-primary-600" />
            Parâmetros de Exportação
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">
                <Building2 className="w-3 h-3 inline mr-1" />
                Estabelecimento *
              </label>
              <select
                value={cnes}
                onChange={(e) => setCnes(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
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
              <label className="block text-xs font-semibold text-gray-600 mb-1">
                <Calendar className="w-3 h-3 inline mr-1" />
                Competência *
              </label>
              <select
                value={competencia}
                onChange={(e) => setCompetencia(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {getCompetencias().map((comp) => (
                  <option key={comp.value} value={comp.value}>
                    {comp.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-xs font-semibold text-gray-600 mb-2">Tipo de BPA</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="tipo"
                  value="individualizado"
                  checked={tipo === 'individualizado'}
                  onChange={(e) => setTipo(e.target.value as 'individualizado')}
                  className="w-4 h-4 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700">BPA-I (Individualizado)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="tipo"
                  value="consolidado"
                  checked={tipo === 'consolidado'}
                  onChange={(e) => setTipo(e.target.value as 'consolidado')}
                  className="w-4 h-4 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700">BPA-C (Consolidado)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="tipo"
                  value="all"
                  checked={tipo === 'all'}
                  onChange={(e) => setTipo(e.target.value as 'all')}
                  className="w-4 h-4 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700">Ambos</span>
              </label>
            </div>
          </div>

          <button
            onClick={handleExport}
            disabled={loading || !cnes || !competencia}
            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
            {loading ? 'Exportando...' : 'Exportar para SQL'}
          </button>
        </div>

        {/* Estatísticas */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-600" />
            Estatísticas
          </h3>

          {stats ? (
            <div className="space-y-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-xs font-semibold text-blue-600 mb-1">BPA Individualizado</p>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total:</span>
                  <span className="text-xl font-bold text-blue-800">{stats.bpai_total}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Pendentes:</span>
                  <span className="font-semibold text-warning-600">{stats.bpai_pendente}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Exportados:</span>
                  <span className="font-semibold text-success-600">{stats.bpai_exportado}</span>
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-xs font-semibold text-green-600 mb-1">BPA Consolidado</p>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total:</span>
                  <span className="text-xl font-bold text-green-800">{stats.bpac_total}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Pendentes:</span>
                  <span className="font-semibold text-warning-600">{stats.bpac_pendente}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Exportados:</span>
                  <span className="font-semibold text-success-600">{stats.bpac_exportado}</span>
                </div>
              </div>

              <button
                onClick={loadStats}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                <RefreshCw className="w-4 h-4" />
                Atualizar
              </button>

              <button
                onClick={handleResetExports}
                disabled={loading || !cnes || !competencia}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors text-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Limpar exportações
              </button>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Informe CNES e Competência para ver estatísticas</p>
            </div>
          )}
        </div>
      </div>

      {/* Lista de exportações */}
      <div className="mt-6 bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <File className="w-5 h-5 text-primary-600" />
          Arquivos Exportados
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Arquivo</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">CNES</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Competência</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Tipo</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Registros</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Data</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Ação</th>
              </tr>
            </thead>
            <tbody>
              {exports.map((exp, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs">{exp.arquivo}</td>
                  <td className="px-3 py-2">{exp.cnes}</td>
                  <td className="px-3 py-2">{exp.competencia}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      exp.tipo === 'BPA-I' || exp.tipo === 'individualizado' ? 'bg-blue-100 text-blue-700' :
                      exp.tipo === 'BPA-C' || exp.tipo === 'consolidado' ? 'bg-green-100 text-green-700' :
                      'bg-purple-100 text-purple-700'
                    }`}>
                      {exp.tipo === 'BPA-I' || exp.tipo === 'individualizado' ? 'BPA-I' : 
                       exp.tipo === 'BPA-C' || exp.tipo === 'consolidado' ? 'BPA-C' : 
                       exp.tipo === 'COMPLETO' ? 'Ambos' : exp.tipo}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-semibold">{exp.total_registros}</td>
                  <td className="px-3 py-2 text-gray-500">{new Date(exp.data_exportacao).toLocaleString()}</td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => handleDownload(exp.arquivo)}
                      className="flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium"
                    >
                      <Download className="w-4 h-4" />
                      Baixar
                    </button>
                  </td>
                </tr>
              ))}
              {exports.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-gray-500">
                    Nenhuma exportação realizada
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Instruções de importação */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Instruções de Importação no Firebird
        </h3>
        <div className="text-yellow-700 text-sm space-y-2">
          <p><strong>1. IBExpert:</strong></p>
          <ol className="list-decimal list-inside pl-4 space-y-1">
            <li>Abra o IBExpert e conecte ao banco BPAMAG.GDB</li>
            <li>Vá em "Tools" → "Script Executive"</li>
            <li>Abra o arquivo SQL exportado</li>
            <li>Execute (F9) para inserir os registros</li>
          </ol>
          <p className="mt-2"><strong>2. ISQL (linha de comando):</strong></p>
          <pre className="bg-yellow-100 p-2 rounded text-xs overflow-x-auto">
{`isql -i "caminho/do/arquivo.sql" -u SYSDBA -p masterkey "C:\\BPA\\BPAMAG.GDB"`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default ExportPage;
