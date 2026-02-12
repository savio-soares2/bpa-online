import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  File,
  FolderOpen,
  Calendar,
  Building2,
  Printer,
  FileSpreadsheet,
  FileClock,
  Database
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ESTABELECIMENTOS, getEstabelecimentoByCnes } from '../constants/estabelecimentos';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Extensões por mês (baseado no padrão do BPA)
const EXTENSOES_MES: Record<string, string> = {
  '01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR',
  '05': 'MAI', '06': 'JUN', '07': 'JUL', '08': 'AGO',
  '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'
};

interface ReportFile {
  name: string;
  size: number;
  download_url: string;
}

interface ReportFolder {
  folder: string;
  cnes: string;
  competencia: string;
  files: ReportFile[];
  created_at: string;
}

interface GenerateResponse {
  success: boolean;
  message: string;
  stats: {
    total_registros: number;
    total_bpas: number;
    bpai_count: number;
    bpac_count: number;
    campo_controle: string;
  };
  files: Record<string, string>;
}

type ReportType = 'remessa' | 'relexp' | 'bpai' | 'bpac' | 'all';

const ReportsPage: React.FC = () => {
  const { user } = useAuth();
  const [selectedCnes, setSelectedCnes] = useState(user?.cnes || '');
  const [competencia, setCompetencia] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  
  // Define sigla baseada no estabelecimento selecionado
  const getDefaultSigla = (cnes: string) => {
    if (!cnes) return 'BPA';
    const estab = getEstabelecimentoByCnes(cnes);
    if (estab) {
      return estab.sigla
        .replace(/[^a-zA-Z0-9]/g, '')
        .substring(0, 10)
        .toUpperCase();
    }
    return 'BPA';
  };
  
  const [sigla, setSigla] = useState(() => getDefaultSigla(user?.cnes || ''));
  const [loading, setLoading] = useState<ReportType | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [reports, setReports] = useState<ReportFolder[]>([]);
  const [lastGenerated, setLastGenerated] = useState<GenerateResponse | null>(null);

  // Atualiza sigla quando muda o CNES
  useEffect(() => {
    setSigla(getDefaultSigla(selectedCnes));
  }, [selectedCnes]);

  // Obtém extensão baseada no mês da competência
  const getExtensaoMes = (comp: string) => {
    if (comp.length === 6) {
      const mes = comp.substring(4, 6);
      return EXTENSOES_MES[mes] || 'TXT';
    }
    return 'TXT';
  };

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

  // Carrega lista de relatórios
  const loadReports = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/reports/list`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setReports(data.reports || []);
      }
    } catch (error) {
      console.error('Erro ao carregar relatórios:', error);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  // Gera relatório específico
  const handleGenerate = async (tipo: ReportType) => {
    if (!competencia) {
      setMessage({ type: 'error', text: 'Selecione uma competência' });
      return;
    }
    if (!selectedCnes) {
      setMessage({ type: 'error', text: 'Selecione um estabelecimento' });
      return;
    }

    setLoading(tipo);
    setMessage(null);
    setLastGenerated(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/reports/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          competencia,
          sigla,
          cnes: selectedCnes,
          tipo // tipo de relatório: 'remessa', 'relexp', 'bpai', 'bpac', 'all'
        })
      });

      const data: GenerateResponse = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        setLastGenerated(data);
        loadReports();
      } else {
        setMessage({ type: 'error', text: data.message });
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Erro ao gerar relatórios' });
    } finally {
      setLoading(null);
    }
  };

  // Download de arquivo
  const handleDownload = (downloadUrl: string, filename: string) => {
    const token = localStorage.getItem('token');
    
    fetch(`${API_URL}${downloadUrl.replace('/api', '')}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => response.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    })
    .catch(error => {
      console.error('Erro ao baixar:', error);
      setMessage({ type: 'error', text: 'Erro ao baixar arquivo' });
    });
  };

  // Formata tamanho do arquivo
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Formata competência
  const formatCompetencia = (comp: string) => {
    if (comp.length === 6) {
      return `${comp.substring(4)}/${comp.substring(0, 4)}`;
    }
    return comp;
  };

  // Nome do arquivo de remessa com extensão correta
  const getRemessaFilename = () => {
    const ext = getExtensaoMes(competencia);
    return `PA${sigla}.${ext}`;
  };

  // Descrição dos arquivos
  const getFileDescription = (filename: string) => {
    if (filename.includes('PA') && !filename.includes('REL') && !filename.includes('PRN')) {
      return 'Arquivo de remessa para importação no SIA/SUS';
    }
    if (filename.includes('RELEXP')) {
      return 'Relatório de controle de remessa';
    }
    if (filename.includes('BPAI')) {
      return 'Relatório de BPA Individualizado';
    }
    if (filename.includes('BPAC')) {
      return 'Relatório de BPA Consolidado';
    }
    return 'Arquivo de relatório';
  };

  const estabelecimentoSelecionado = getEstabelecimentoByCnes(selectedCnes);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
          <Printer className="w-8 h-8 text-primary-600" />
          Relatórios BPA
        </h1>
        <p className="text-gray-500 mt-1">
          Gere os arquivos de exportação no formato do BPA Magnético
        </p>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-primary-600" />
          Configurações
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* CNES */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estabelecimento (CNES)
            </label>
            <select
              value={selectedCnes}
              onChange={(e) => setSelectedCnes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="">Selecione...</option>
              {ESTABELECIMENTOS.map(estab => (
                <option key={estab.cnes} value={estab.cnes}>
                  {estab.sigla} - {estab.cnes}
                </option>
              ))}
            </select>
          </div>

          {/* Competência */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Competência
            </label>
            <select
              value={competencia}
              onChange={(e) => setCompetencia(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              {getCompetencias().map(comp => (
                <option key={comp.value} value={comp.value}>
                  {comp.label}
                </option>
              ))}
            </select>
          </div>

          {/* Sigla */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sigla do Arquivo
            </label>
            <input
              type="text"
              value={sigla}
              onChange={(e) => setSigla(e.target.value.toUpperCase())}
              maxLength={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="Ex: CAPSAD"
            />
          </div>

          {/* Preview do nome */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Arquivo de Remessa
            </label>
            <div className="px-3 py-2 bg-gray-100 border border-gray-200 rounded-lg text-sm font-mono text-gray-700">
              {getRemessaFilename()}
            </div>
          </div>
        </div>

        {estabelecimentoSelecionado && (
          <div className="mt-3 p-3 bg-primary-50 rounded-lg">
            <p className="text-sm text-primary-800">
              <Building2 className="w-4 h-4 inline mr-1" />
              <strong>{estabelecimentoSelecionado.nome}</strong>
            </p>
          </div>
        )}
      </div>

      {/* Mensagem */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200' 
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          {message.text}
        </div>
      )}

      {/* Botões de Geração - 4 tipos + todos */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-600" />
          Gerar Relatórios
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Arquivo de Remessa */}
          <button
            onClick={() => handleGenerate('remessa')}
            disabled={loading !== null || !selectedCnes}
            className="p-4 border-2 border-blue-200 bg-blue-50 hover:bg-blue-100 hover:border-blue-300 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-left group"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                <Database className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-800">Remessa + Controle</p>
                <p className="text-xs text-blue-600 font-mono">{getRemessaFilename()} + RELEXP.PRN</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Arquivo de remessa para SIA/SUS e relatório de controle para assinaturas
            </p>
            {loading === 'remessa' && (
              <div className="mt-2 flex items-center gap-2 text-blue-600">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-xs">Gerando...</span>
              </div>
            )}
          </button>

          {/* BPAI_REL.TXT - movido para segunda posição */}
          <button
            onClick={() => handleGenerate('bpai')}
            disabled={loading !== null || !selectedCnes}
            className="p-4 border-2 border-purple-200 bg-purple-50 hover:bg-purple-100 hover:border-purple-300 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-left group"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
                <FileSpreadsheet className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-800">Relatório BPA-I</p>
                <p className="text-xs text-purple-600 font-mono">BPAI_REL.TXT</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Listagem detalhada dos atendimentos individualizados
            </p>
            {loading === 'bpai' && (
              <div className="mt-2 flex items-center gap-2 text-purple-600">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-xs">Gerando...</span>
              </div>
            )}
          </button>

          {/* BPAC_REL.TXT - movido para terceira posição */}
          <button
            onClick={() => handleGenerate('bpac')}
            disabled={loading !== null || !selectedCnes}
            className="p-4 border-2 border-orange-200 bg-orange-50 hover:bg-orange-100 hover:border-orange-300 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-left group"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-orange-100 rounded-lg group-hover:bg-orange-200 transition-colors">
                <FileClock className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-800">Relatório BPA-C</p>
                <p className="text-xs text-orange-600 font-mono">BPAC_REL.TXT</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Relatório consolidado agrupado por CBO
            </p>
            {loading === 'bpac' && (
              <div className="mt-2 flex items-center gap-2 text-orange-600">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-xs">Gerando...</span>
              </div>
            )}
          </button>
        </div>

        {/* Botão gerar todos */}
        <button
          onClick={() => handleGenerate('all')}
          disabled={loading !== null || !selectedCnes}
          className="w-full p-4 bg-primary-600 hover:bg-primary-700 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 font-medium"
        >
          {loading === 'all' ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" />
              Gerando todos os relatórios...
            </>
          ) : (
            <>
              <Printer className="w-5 h-5" />
              Gerar Todos os Relatórios
            </>
          )}
        </button>
      </div>

      {/* Resultado da última geração */}
      {lastGenerated && lastGenerated.success && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Arquivos Gerados
          </h3>
          
          {/* Estatísticas */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500">Total Registros</p>
              <p className="text-xl font-bold text-gray-800">{lastGenerated.stats.total_registros}</p>
            </div>
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <p className="text-xs text-gray-500">BPA-I</p>
              <p className="text-xl font-bold text-blue-600">{lastGenerated.stats.bpai_count}</p>
            </div>
            <div className="bg-green-50 p-3 rounded-lg border border-green-200">
              <p className="text-xs text-gray-500">BPA-C</p>
              <p className="text-xl font-bold text-green-600">{lastGenerated.stats.bpac_count}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500">Campo Controle</p>
              <p className="text-xl font-bold text-gray-800">{lastGenerated.stats.campo_controle}</p>
            </div>
          </div>

          {/* Links de download */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(lastGenerated.files).map(([filename, url]) => (
              <button
                key={filename}
                onClick={() => handleDownload(url, filename)}
                className="p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-primary-50 hover:border-primary-300 transition-colors text-left group"
              >
                <div className="flex items-center gap-2 mb-1">
                  <File className="w-4 h-4 text-primary-600" />
                  <span className="text-sm font-medium text-gray-800 truncate">{filename}</span>
                </div>
                <p className="text-xs text-gray-500 truncate">{getFileDescription(filename)}</p>
                <div className="flex items-center gap-1 mt-2 text-primary-600 text-xs">
                  <Download className="w-3 h-3" />
                  Baixar
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Lista de Relatórios Anteriores */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-primary-600" />
            Relatórios Gerados
          </h3>
          <button
            onClick={loadReports}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Atualizar lista"
          >
            <RefreshCw className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {reports.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FolderOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Nenhum relatório gerado ainda</p>
            <p className="text-sm">Selecione um estabelecimento e competência e clique em um dos botões acima</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report, index) => (
              <div 
                key={index} 
                className="border border-gray-200 rounded-lg p-4 hover:border-primary-200 transition-colors"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="bg-primary-100 p-2 rounded-lg">
                      <Calendar className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">
                        Competência {formatCompetencia(report.competencia)}
                      </p>
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <Building2 className="w-3 h-3" />
                        CNES: {report.cnes}
                        {getEstabelecimentoByCnes(report.cnes) && (
                          <span className="ml-1">
                            ({getEstabelecimentoByCnes(report.cnes)?.sigla})
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400">
                    {new Date(report.created_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {report.files.map((file, fileIndex) => (
                    <button
                      key={fileIndex}
                      onClick={() => handleDownload(file.download_url, file.name)}
                      className="p-2 bg-gray-50 border border-gray-100 rounded-lg hover:bg-primary-50 hover:border-primary-200 transition-colors text-left group"
                    >
                      <div className="flex items-center gap-2">
                        <File className="w-4 h-4 text-gray-400 group-hover:text-primary-600" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-700 truncate">{file.name}</p>
                          <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
                        </div>
                        <Download className="w-4 h-4 text-gray-300 group-hover:text-primary-600" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Informações sobre os arquivos */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-3">
          Sobre os Arquivos Gerados
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
          <div>
            <p className="font-medium">PA[SIGLA].[MÊS]</p>
            <p className="text-blue-600">
              Arquivo de remessa para importação no SIA/SUS. A extensão varia conforme o mês 
              (JAN, FEV, MAR, ABR, MAI, JUN, JUL, AGO, SET, OUT, NOV, DEZ).
            </p>
          </div>
          <div>
            <p className="font-medium">RELEXP.PRN</p>
            <p className="text-blue-600">Relatório de controle de remessa. Deve ser impresso e assinado para acompanhar o arquivo de remessa.</p>
          </div>
          <div>
            <p className="font-medium">BPAI_REL.TXT</p>
            <p className="text-blue-600">Relatório detalhado de BPA Individualizado. Lista todos os atendimentos com dados do paciente.</p>
          </div>
          <div>
            <p className="font-medium">BPAC_REL.TXT</p>
            <p className="text-blue-600">Relatório de BPA Consolidado. Agrupa procedimentos por CBO para conferência.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
