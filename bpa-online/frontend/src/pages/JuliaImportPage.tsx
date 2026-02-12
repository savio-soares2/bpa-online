import React, { useState } from 'react';
import { 
  Cloud, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  Server,
  Calendar,
  Database,
  Info
} from 'lucide-react';
import { importFromJulia, checkJuliaConnection } from '../services/api';
import type { Message } from '../types';

interface JuliaConfig {
  url_base: string;
  usuario: string;
  senha: string;
  unidade_saude_id: string;
}

interface ImportResult {
  success: boolean;
  total_importado: number;
  bpai_importado: number;
  bpac_importado: number;
  erros: string[];
}

const JuliaImportPage: React.FC = () => {
  const [config, setConfig] = useState<JuliaConfig>({
    url_base: 'https://julia.api.com/api/v1',
    usuario: '',
    senha: '',
    unidade_saude_id: ''
  });
  
  const [competencia, setCompetencia] = useState('');
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'error'>('unknown');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  // Testa conexão com a API Julia
  const testConnection = async () => {
    if (!config.url_base || !config.usuario || !config.senha) {
      setMessage({ type: 'error', text: 'Preencha URL, usuário e senha' });
      return;
    }

    setChecking(true);
    setMessage(null);

    try {
      const result = await checkJuliaConnection(config);
      
      if (result.success) {
        setConnectionStatus('connected');
        setMessage({ type: 'success', text: 'Conexão estabelecida com sucesso!' });
      } else {
        setConnectionStatus('error');
        setMessage({ type: 'error', text: result.error || 'Falha na conexão' });
      }
    } catch (error) {
      setConnectionStatus('error');
      setMessage({ type: 'error', text: 'Erro ao testar conexão' });
    } finally {
      setChecking(false);
    }
  };

  // Importa dados da API Julia
  const handleImport = async () => {
    if (!competencia || competencia.length !== 6) {
      setMessage({ type: 'error', text: 'Informe a competência no formato YYYYMM' });
      return;
    }

    if (!config.unidade_saude_id) {
      setMessage({ type: 'error', text: 'Informe o ID da Unidade de Saúde' });
      return;
    }

    setLoading(true);
    setMessage(null);
    setImportResult(null);

    try {
      const result = await importFromJulia({
        ...config,
        competencia
      });
      
      setImportResult(result);
      
      if (result.success) {
        setMessage({ 
          type: 'success', 
          text: `Importação concluída! ${result.total_importado} registros importados.` 
        });
      } else {
        setMessage({ 
          type: 'error', 
          text: `Importação com erros: ${result.erros.join(', ')}` 
        });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao importar dados' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <Cloud className="w-7 h-7 text-primary-600" />
        Importar da API Julia
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

      {/* Informações */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
          <Info className="w-5 h-5" />
          Sobre a Importação
        </h3>
        <ul className="text-blue-700 text-sm space-y-1 list-disc list-inside">
          <li>Conecta à API Julia para baixar dados de atendimentos</li>
          <li>Converte automaticamente para o formato BPA (Individualizado e Consolidado)</li>
          <li>Registros são salvos no banco local para posterior exportação ao Firebird</li>
          <li>Não duplica registros já importados</li>
        </ul>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuração da API */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-primary-600" />
            Configuração da API
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">URL Base da API *</label>
              <input
                type="text"
                value={config.url_base}
                onChange={(e) => setConfig({...config, url_base: e.target.value})}
                placeholder="https://julia.api.com/api/v1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Usuário *</label>
              <input
                type="text"
                value={config.usuario}
                onChange={(e) => setConfig({...config, usuario: e.target.value})}
                placeholder="usuario@email.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Senha *</label>
              <input
                type="password"
                value={config.senha}
                onChange={(e) => setConfig({...config, senha: e.target.value})}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">ID Unidade de Saúde *</label>
              <input
                type="text"
                value={config.unidade_saude_id}
                onChange={(e) => setConfig({...config, unidade_saude_id: e.target.value})}
                placeholder="123"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <button
              onClick={testConnection}
              disabled={checking}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            >
              {checking ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Server className="w-4 h-4" />}
              {checking ? 'Testando...' : 'Testar Conexão'}
            </button>

            {/* Status da conexão */}
            {connectionStatus !== 'unknown' && (
              <div className={`flex items-center gap-2 p-3 rounded-lg ${
                connectionStatus === 'connected' 
                  ? 'bg-success-50 text-success-700' 
                  : 'bg-danger-50 text-danger-600'
              }`}>
                {connectionStatus === 'connected' ? (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    <span>Conectado</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-5 h-5" />
                    <span>Desconectado</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Importação */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary-600" />
            Importar Dados
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Competência * (YYYYMM)</label>
              <input
                type="text"
                value={competencia}
                onChange={(e) => setCompetencia(e.target.value)}
                maxLength={6}
                placeholder="202512"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">Informe a competência para buscar os atendimentos</p>
            </div>

            <button
              onClick={handleImport}
              disabled={loading || connectionStatus !== 'connected'}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Cloud className="w-5 h-5" />}
              {loading ? 'Importando...' : 'Importar da Julia'}
            </button>

            {connectionStatus !== 'connected' && (
              <p className="text-xs text-warning-600 text-center">
                Teste a conexão antes de importar
              </p>
            )}
          </div>

          {/* Resultado da importação */}
          {importResult && (
            <div className="mt-6 bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Resultado da Importação
              </h4>
              
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-primary-600">{importResult.total_importado}</p>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{importResult.bpai_importado}</p>
                  <p className="text-xs text-gray-500">BPA-I</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{importResult.bpac_importado}</p>
                  <p className="text-xs text-gray-500">BPA-C</p>
                </div>
              </div>

              {importResult.erros.length > 0 && (
                <div className="mt-3 p-3 bg-danger-50 rounded text-danger-600 text-sm">
                  <p className="font-semibold mb-1">Erros:</p>
                  <ul className="list-disc list-inside">
                    {importResult.erros.map((erro, idx) => (
                      <li key={idx}>{erro}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Instruções */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Fluxo de Trabalho
        </h3>
        <ol className="text-yellow-700 text-sm space-y-1 list-decimal list-inside">
          <li>Configure as credenciais da API Julia</li>
          <li>Teste a conexão para verificar se está tudo certo</li>
          <li>Selecione a competência desejada</li>
          <li>Clique em "Importar da Julia" para baixar os dados</li>
          <li>Após a importação, vá em "Exportar Firebird" para gerar o SQL</li>
          <li>Importe o SQL no Firebird usando IBExpert</li>
        </ol>
      </div>
    </div>
  );
};

export default JuliaImportPage;
