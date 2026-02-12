import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Plus,
  Trash2,
  Key,
  ToggleLeft,
  ToggleRight,
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  Shield,
  Edit,
  Search,
  Building2,
  ExternalLink,
  ArrowLeft
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { adminListUsers, adminCreateUser, adminDeleteUser, adminToggleUser, adminResetPassword, adminUpdateUser, adminGetCBOs } from '../services/api';
import { ESTABELECIMENTOS } from '../constants/estabelecimentos';

// Utility debounce function
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout;
  return ((...args: any[]) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  }) as T;
}

interface User {
  id: number;
  email: string;
  nome: string;
  cbo?: string;
  cnes: string;
  nome_unidade?: string;
  is_admin: boolean;
  ativo: boolean;
  created_at: string;
}

interface CBO {
  codigo: string;
  descricao: string;
  total_procedimentos: number;
}

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    senha: '',
    nome: '',
    cnes: '',
    nome_unidade: '',
    cbo: ''
  });
  const [formLoading, setFormLoading] = useState(false);

  // Edit state
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showEditForm, setShowEditForm] = useState(false);

  // Reset password
  const [resetUserId, setResetUserId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');

  // CBOs - carregamento sob demanda
  const [cbosLoading, setCbosLoading] = useState(false);

  // Filter
  const [filterCnes, setFilterCnes] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  // Função de debounce para busca de CBOs
  const searchCBOsDebounced = useCallback(
    debounce(async (query: string, setCBOsList: (cbos: CBO[]) => void) => {
      try {
        setCbosLoading(true);
        const cbosData = await adminGetCBOs(query, 50);
        setCBOsList(cbosData);
      } catch (error) {
        console.error('Erro ao buscar CBOs:', error);
        setCBOsList([]);
      } finally {
        setCbosLoading(false);
      }
    }, 300),
    []
  );

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await adminListUsers();
      setUsers(data);
    } catch (error: any) {
      showMessage('error', 'Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const CBODropdown: React.FC<{
    value: string;
    onChange: (cbo: string) => void;
    placeholder?: string;
  }> = ({ value, onChange, placeholder = "Selecione um CBO" }) => {
    const [localFilter, setLocalFilter] = useState('');
    const [localCbos, setLocalCbos] = useState<CBO[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Carrega CBOs iniciais ao montar
    useEffect(() => {
      const loadInitial = async () => {
        try {
          setIsSearching(true);
          const cbosData = await adminGetCBOs('', 50);
          setLocalCbos(cbosData);
        } catch (error) {
          console.error('Erro ao carregar CBOs iniciais:', error);
        } finally {
          setIsSearching(false);
        }
      };
      loadInitial();
    }, []);

    const handleLocalFilter = async (filter: string) => {
      setLocalFilter(filter);
      setIsSearching(true);
      try {
        const cbosData = await adminGetCBOs(filter, 50);
        setLocalCbos(cbosData);
      } catch (error) {
        console.error('Erro ao buscar CBOs:', error);
      } finally {
        setIsSearching(false);
      }
    };

    // Debounce para busca
    const debouncedSearch = useCallback(
      debounce((filter: string) => handleLocalFilter(filter), 300),
      []
    );

    const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      setLocalFilter(val);
      debouncedSearch(val);
    };

    return (
      <div className="space-y-2">
        <div className="relative">
          <input
            type="text"
            value={localFilter}
            onChange={onInputChange}
            placeholder="Digite para buscar CBOs (ex: psicólogo, médico)..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
          />
          {isSearching ? (
            <div className="absolute right-3 top-2.5 w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          ) : (
            <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          )}
        </div>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          size={6}
        >
          <option value="">{placeholder}</option>
          {localCbos.map(cbo => (
            <option key={cbo.codigo} value={cbo.codigo}>
              {cbo.codigo} - {cbo.descricao} ({cbo.total_procedimentos} proc.)
            </option>
          ))}
        </select>
        {localCbos.length === 0 && !isSearching && localFilter && (
          <p className="text-sm text-gray-500">Nenhum CBO encontrado para "{localFilter}"</p>
        )}
      </div>
    );
  };
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email || !formData.senha || !formData.nome) {
      showMessage('error', 'Preencha email, senha e nome');
      return;
    }

    setFormLoading(true);
    try {
      await adminCreateUser(formData);
      showMessage('success', 'Usuário criado com sucesso!');
      setShowForm(false);
      setFormData({ email: '', senha: '', nome: '', cnes: '', nome_unidade: '', cbo: '' });
      loadUsers();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || 'Erro ao criar usuário');
    } finally {
      setFormLoading(false);
    }
  };

  const handleToggleUser = async (userId: number, currentStatus: boolean) => {
    try {
      await adminToggleUser(userId, !currentStatus);
      showMessage('success', `Usuário ${!currentStatus ? 'ativado' : 'desativado'}`);
      loadUsers();
    } catch (error) {
      showMessage('error', 'Erro ao alterar status');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('Tem certeza que deseja excluir este usuário?')) return;

    try {
      await adminDeleteUser(userId);
      showMessage('success', 'Usuário excluído');
      loadUsers();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setShowEditForm(true);
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!editingUser) return;

    setFormLoading(true);
    try {
      await adminUpdateUser(editingUser.id, {
        nome: editingUser.nome,
        email: editingUser.email,
        cbo: editingUser.cbo,
        cnes: editingUser.cnes,
        nome_unidade: editingUser.nome_unidade
      });

      showMessage('success', 'Usuário atualizado com sucesso!');
      setShowEditForm(false);
      setEditingUser(null);
      loadUsers();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || 'Erro ao atualizar usuário');
    } finally {
      setFormLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!resetUserId || !newPassword) return;

    try {
      await adminResetPassword(resetUserId, newPassword);
      showMessage('success', 'Senha resetada com sucesso!');
      setResetUserId(null);
      setNewPassword('');
    } catch (error) {
      showMessage('error', 'Erro ao resetar senha');
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <button
            onClick={() => navigate('/admin/unidades')}
            className="flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar para Unidades
          </button>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Shield className="w-7 h-7 text-primary-600" />
            Gestão de Usuários
          </h2>
        </div>

        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
        >
          <Plus className="w-4 h-4" />
          Novo Usuário
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-4 p-4 rounded-lg flex items-center gap-2 ${message.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
          {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5" />
            Cadastrar Novo Usuário
          </h3>

          <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="email@exemplo.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Senha *
              </label>
              <input
                type="password"
                value={formData.senha}
                onChange={(e) => setFormData({ ...formData, senha: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome *
              </label>
              <input
                type="text"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nome completo"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estabelecimento (CNES)
              </label>
              <select
                value={formData.cnes}
                onChange={(e) => {
                  const selected = ESTABELECIMENTOS.find(est => est.cnes === e.target.value);
                  setFormData({
                    ...formData,
                    cnes: e.target.value,
                    nome_unidade: selected ? selected.nome : ''
                  });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">Selecione o estabelecimento</option>
                {ESTABELECIMENTOS.map((est) => (
                  <option key={est.cnes} value={est.cnes}>
                    {est.cnes} - {est.sigla}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CBO *
              </label>
              <CBODropdown
                value={formData.cbo}
                onChange={(cbo) => setFormData({ ...formData, cbo })}
                placeholder="Selecione um CBO"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome da Unidade
              </label>
              <input
                type="text"
                value={formData.nome_unidade}
                onChange={(e) => setFormData({ ...formData, nome_unidade: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-gray-50"
                placeholder="Preenchido automaticamente"
                readOnly
              />
            </div>

            <div className="md:col-span-2 flex gap-3">
              <button
                type="submit"
                disabled={formLoading}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {formLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Cadastrar
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditForm && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Editar Usuário
            </h3>

            <form onSubmit={handleUpdateUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={editingUser.email}
                  onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome *
                </label>
                <input
                  type="text"
                  value={editingUser.nome}
                  onChange={(e) => setEditingUser({ ...editingUser, nome: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estabelecimento (CNES)
                </label>
                <select
                  value={editingUser.cnes}
                  onChange={(e) => {
                    const selected = ESTABELECIMENTOS.find(est => est.cnes === e.target.value);
                    setEditingUser({
                      ...editingUser,
                      cnes: e.target.value,
                      nome_unidade: selected ? selected.nome : ''
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">Selecione o estabelecimento</option>
                  {ESTABELECIMENTOS.map((est) => (
                    <option key={est.cnes} value={est.cnes}>
                      {est.cnes} - {est.sigla}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CBO *
                </label>
                <CBODropdown
                  value={editingUser.cbo || ''}
                  onChange={(cbo) => setEditingUser({ ...editingUser, cbo })}
                  placeholder="Selecione um CBO"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome da Unidade
                </label>
                <input
                  type="text"
                  value={editingUser.nome_unidade || ''}
                  onChange={(e) => setEditingUser({ ...editingUser, nome_unidade: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-gray-50"
                  readOnly
                />
              </div>

              <div className="md:col-span-2 flex gap-3">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {formLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  Atualizar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditForm(false);
                    setEditingUser(null);
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {resetUserId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Key className="w-5 h-5" />
              Resetar Senha
            </h3>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nova Senha
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="••••••••"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleResetPassword}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Resetar
              </button>
              <button
                onClick={() => { setResetUserId(null); setNewPassword(''); }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <Users className="w-5 h-5" />
            Usuários Cadastrados
          </h3>

          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-gray-500" />
            <select
              value={filterCnes}
              onChange={(e) => setFilterCnes(e.target.value)}
              className="text-sm border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Todas as Unidades</option>
              {ESTABELECIMENTOS.map(est => (
                <option key={est.cnes} value={est.cnes}>
                  {est.sigla}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto" />
          </div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            Nenhum usuário cadastrado
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Nome</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Email</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">CBO</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">CNES</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Unidade</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users
                  .filter(user => !filterCnes || user.cnes === filterCnes)
                  .map((user) => (
                    <tr key={user.id} className={!user.ativo ? 'bg-gray-50' : ''}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {user.nome}
                          {user.is_admin && (
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                              Admin
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{user.email}</td>
                      <td className="px-4 py-3 font-mono text-gray-600">{user.cbo || '-'}</td>
                      <td className="px-4 py-3 font-mono text-gray-600">{user.cnes || '-'}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {user.nome_unidade ? (
                          <div className="flex items-center gap-1 group relative">
                            <span className="truncate max-w-[150px]" title={user.nome_unidade}>
                              {user.nome_unidade}
                            </span>
                            {user.cnes && (
                              <button
                                onClick={() => navigate(`/admin/unidades/${user.cnes}`)}
                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded transition-opacity"
                                title="Ir para unidade"
                              >
                                <ExternalLink className="w-3 h-3 text-primary-600" />
                              </button>
                            )}
                          </div>
                        ) : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {user.ativo ? (
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                            Ativo
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
                            Inativo
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          {!user.is_admin && (
                            <>
                              <button
                                onClick={() => handleEditUser(user)}
                                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                title="Editar usuário"
                              >
                                <Edit className="w-5 h-5" />
                              </button>

                              <button
                                onClick={() => handleToggleUser(user.id, user.ativo)}
                                className={`p-1.5 rounded-lg transition-colors ${user.ativo
                                    ? 'text-orange-600 hover:bg-orange-50'
                                    : 'text-green-600 hover:bg-green-50'
                                  }`}
                                title={user.ativo ? 'Desativar' : 'Ativar'}
                              >
                                {user.ativo ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                              </button>

                              <button
                                onClick={() => setResetUserId(user.id)}
                                className="p-1.5 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                                title="Resetar senha"
                              >
                                <Key className="w-5 h-5" />
                              </button>

                              <button
                                onClick={() => handleDeleteUser(user.id)}
                                className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                title="Excluir"
                              >
                                <Trash2 className="w-5 h-5" />
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
    </div>
  );
};

export default AdminPage;
