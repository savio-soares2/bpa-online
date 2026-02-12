import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  ChevronRight, 
  ChevronDown, 
  Trash2, 
  Edit,
  Loader2,
  Calendar,
  User,
  Filter,
  ArrowLeft
} from 'lucide-react';
import { listBPAIndividualizado, deleteBPAIndividualizado } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import FormBPA from './FormBPA';

interface Producao {
  id: number;
  folha: number;
  cns_paciente: string;
  nome_paciente: string;
  procedimento: string;
  procedimento_descricao?: string;
  data_atendimento: string;
  quantidade: number;
  cns_profissional: string;
  nome_profissional?: string;
  exportado: boolean;
}

interface FolhaGroup {
  folha: number;
  producoes: Producao[];
  total: number;
  exportados: number;
}

const BPAIndividualizadoPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [folhas, setFolhas] = useState<FolhaGroup[]>([]);
  const [expandedFolha, setExpandedFolha] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [competencia, setCompetencia] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [selectedFolha, setSelectedFolha] = useState<number>(1);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (user?.cnes) {
      loadProducoes();
    }
  }, [user?.cnes, competencia]);

  const loadProducoes = async () => {
    if (!user?.cnes) return;
    
    setLoading(true);
    try {
      const data = await listBPAIndividualizado(user.cnes, competencia);
      
      // Agrupa por folha
      const grouped: Record<number, Producao[]> = {};
      data.forEach((item: any) => {
        const folha = item.folha || 1;
        if (!grouped[folha]) {
          grouped[folha] = [];
        }
        grouped[folha].push({
          id: item.id,
          folha,
          cns_paciente: item.cns_paciente,
          nome_paciente: item.nome_paciente,
          procedimento: item.procedimento,
          procedimento_descricao: item.procedimento_descricao,
          data_atendimento: item.data_atendimento,
          quantidade: item.quantidade,
          cns_profissional: item.cns_profissional,
          nome_profissional: item.nome_profissional,
          exportado: item.exportado
        });
      });

      // Converte para array de FolhaGroup
      const folhasArray: FolhaGroup[] = Object.entries(grouped)
        .map(([folha, producoes]) => ({
          folha: parseInt(folha),
          producoes,
          total: producoes.length,
          exportados: producoes.filter(p => p.exportado).length
        }))
        .sort((a, b) => a.folha - b.folha);

      setFolhas(folhasArray);
    } catch (error) {
      console.error('Erro ao carregar produções:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Excluir esta produção?')) return;
    
    try {
      await deleteBPAIndividualizado(id);
      showMessage('success', 'Produção excluída');
      loadProducoes();
    } catch (error) {
      showMessage('error', 'Erro ao excluir');
    }
  };

  const handleNovaProducao = (folha?: number) => {
    setSelectedFolha(folha || (folhas.length > 0 ? Math.max(...folhas.map(f => f.folha)) + 1 : 1));
    setEditingId(null);
    setShowForm(true);
  };

  const handleEditProducao = (id: number) => {
    setEditingId(id);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingId(null);
    loadProducoes();
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
  };

  const totalProducoes = folhas.reduce((sum, f) => sum + f.total, 0);
  const totalExportados = folhas.reduce((sum, f) => sum + f.exportados, 0);

  // Se mostrar form, renderiza o FormBPA
  if (showForm) {
    return (
      <div className="p-6">
        <button
          onClick={handleFormClose}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar para lista
        </button>
        <FormBPA 
          initialFolha={selectedFolha} 
          editingId={editingId}
          onSave={handleFormClose}
        />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <FileText className="w-7 h-7 text-primary-600" />
            BPA Individualizado
          </h2>
          <p className="text-gray-500 mt-1">
            {user?.nome_unidade || `CNES: ${user?.cnes}`}
          </p>
        </div>
        
        <button
          onClick={() => handleNovaProducao()}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
        >
          <Plus className="w-5 h-5" />
          Nova Produção
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-600">Filtros:</span>
          </div>
          
          <div>
            <label className="block text-xs text-gray-500 mb-1">Competência</label>
            <input
              type="month"
              value={`${competencia.slice(0, 4)}-${competencia.slice(4)}`}
              onChange={(e) => setCompetencia(e.target.value.replace('-', ''))}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {message.text}
        </div>
      )}

      {/* Resumo */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total de Folhas</p>
          <p className="text-2xl font-bold text-gray-800">{folhas.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total de Produções</p>
          <p className="text-2xl font-bold text-gray-800">{totalProducoes}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Exportados</p>
          <p className="text-2xl font-bold text-green-600">{totalExportados}</p>
        </div>
      </div>

      {/* Lista de Folhas */}
      {loading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      ) : folhas.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Nenhuma produção cadastrada para esta competência</p>
          <button
            onClick={() => handleNovaProducao(1)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            Cadastrar primeira produção
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {folhas.map((folhaGroup) => (
            <div key={folhaGroup.folha} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              {/* Header da Folha */}
              <button
                onClick={() => setExpandedFolha(expandedFolha === folhaGroup.folha ? null : folhaGroup.folha)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedFolha === folhaGroup.folha ? (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  )}
                  <span className="font-medium text-gray-800">
                    Folha {folhaGroup.folha}
                  </span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-sm rounded-full">
                    {folhaGroup.total} {folhaGroup.total === 1 ? 'produção' : 'produções'}
                  </span>
                  {folhaGroup.exportados > 0 && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-sm rounded-full">
                      {folhaGroup.exportados} exportado{folhaGroup.exportados > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                
                <button
                  onClick={(e) => { e.stopPropagation(); handleNovaProducao(folhaGroup.folha); }}
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  + Adicionar
                </button>
              </button>

              {/* Produções da Folha */}
              {expandedFolha === folhaGroup.folha && (
                <div className="border-t border-gray-200">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Paciente</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Procedimento</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Qtd</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {folhaGroup.producoes.map((prod) => (
                        <tr key={prod.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <User className="w-4 h-4 text-gray-400" />
                              <div>
                                <p className="text-sm font-medium text-gray-800">{prod.nome_paciente || 'Sem nome'}</p>
                                <p className="text-xs text-gray-500">{prod.cns_paciente}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <p className="text-sm text-gray-800">{prod.procedimento}</p>
                            {prod.procedimento_descricao && (
                              <p className="text-xs text-gray-500 truncate max-w-xs">{prod.procedimento_descricao}</p>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 text-sm text-gray-600">
                              <Calendar className="w-4 h-4" />
                              {formatDate(prod.data_atendimento)}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-sm font-medium text-gray-800">{prod.quantidade}</span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {prod.exportado ? (
                              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                                Exportado
                              </span>
                            ) : (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                                Pendente
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-center gap-2">
                              {!prod.exportado && (
                                <>
                                  <button
                                    onClick={() => handleEditProducao(prod.id)}
                                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                    title="Editar"
                                  >
                                    <Edit className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => handleDelete(prod.id)}
                                    className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Excluir"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}

          {/* Botão Nova Folha */}
          <button
            onClick={() => handleNovaProducao()}
            className="w-full py-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-primary-400 hover:text-primary-600 transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Nova Folha
          </button>
        </div>
      )}
    </div>
  );
};

export default BPAIndividualizadoPage;
