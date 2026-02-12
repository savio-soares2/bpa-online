import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Plus,
  Trash2,
  Search,
  RefreshCw,
  User,
  FileText,
  CheckCircle,
  Clock,
  X,
  ChevronDown
} from 'lucide-react';
import {
  getProfissional,
  getPaciente,
  searchProcedimentos,
  getUserProcedimentos,
  saveBPAIndividualizado,
  listBPAIndividualizado,
  deleteBPAIndividualizado
} from '../services/api';
import { listProfissionais, Profissional } from '../services/adminService';
import type {
  BPACabecalho,
  BPARegistro,
  BPAIndividualizado,
  Procedimento,
  Message
} from '../types';
import { RACAS, SEXOS, CARATER_ATENDIMENTO } from '../types';
import { useAuth } from '../contexts/AuthContext';

const initialCabecalho: BPACabecalho = {
  cnes: '',
  cns_profissional: '',
  nome_profissional: '',
  cbo: '',
  ine: '',
  competencia: '',
  folha: 1
};

const initialRegistro: BPARegistro = {
  cns_paciente: '',
  cpf_paciente: '',
  nome_paciente: '',
  data_nascimento: '',
  sexo: '',
  raca_cor: '99',
  nacionalidade: '010',
  municipio_ibge: '172100',
  cep: '',
  logradouro_codigo: '',
  endereco: '',
  numero: '',
  complemento: '',
  bairro: '',
  telefone: '',
  email: '',
  data_atendimento: '',
  procedimento: '',
  procedimento_descricao: '',
  quantidade: 1,
  cid: '',
  carater_atendimento: '01',
  numero_autorizacao: '',
  cnpj: '',
  servico: '',
  classificacao: ''
};

interface FormBPAProps {
  initialFolha?: number;
  editingId?: number | null;
  onSave?: () => void;
}

const FormBPA: React.FC<FormBPAProps> = ({ initialFolha = 1, editingId = null, onSave }) => {
  const { user } = useAuth();
  const [cabecalho, setCabecalho] = useState<BPACabecalho>({
    ...initialCabecalho,
    folha: initialFolha,
    cnes: user?.cnes || '',
    cbo: user?.cbo || ''
  });
  const [registro, setRegistro] = useState<BPARegistro>(initialRegistro);
  const [registros, setRegistros] = useState<BPAIndividualizado[]>([]);
  const [profissionaisList, setProfissionaisList] = useState<Profissional[]>([]);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const [activeTab, setActiveTab] = useState<'paciente' | 'procedimento'>('paciente');
  const [searchResults, setSearchResults] = useState<Procedimento[]>([]);
  const [showProcedimentoSearch, setShowProcedimentoSearch] = useState(false);
  const [allUserProcedimentos, setAllUserProcedimentos] = useState<Procedimento[]>([]);
  const [filteredProcedimentos, setFilteredProcedimentos] = useState<Procedimento[]>([]);
  const [procedimentoFilter, setProcedimentoFilter] = useState('');

  const procedimentoDropdownRef = useRef<HTMLDivElement>(null);

  // Fecha dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (procedimentoDropdownRef.current && !procedimentoDropdownRef.current.contains(event.target as Node)) {
        setShowProcedimentoSearch(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Carrega dados iniciais do usuário logado
  useEffect(() => {
    if (user) {
      setCabecalho(prev => ({
        ...prev,
        cnes: user.cnes || '',
        cbo: user.cbo || ''
      }));

      // Carrega profissionais da unidade
      if (user.cnes) {
        listProfissionais(user.cnes).then(setProfissionaisList).catch(console.error);
      }

      // Carrega todos os procedimentos permitidos ao usuário
      loadUserProcedimentos();
    }
  }, [user]);

  const loadUserProcedimentos = async () => {
    try {
      const procedimentos = await getUserProcedimentos();
      setAllUserProcedimentos(procedimentos);
      setFilteredProcedimentos(procedimentos);
    } catch (error) {
      console.error('Erro ao carregar procedimentos do usuário:', error);
    }
  };

  // Filtra procedimentos localmente
  const handleProcedimentoFilter = (filter: string) => {
    setProcedimentoFilter(filter);
    if (!filter.trim()) {
      setFilteredProcedimentos(allUserProcedimentos);
    } else {
      const filtered = allUserProcedimentos.filter(proc =>
        proc.codigo.toLowerCase().includes(filter.toLowerCase()) ||
        (proc.descricao || '').toLowerCase().includes(filter.toLowerCase())
      );
      setFilteredProcedimentos(filtered);
    }
  };

  // Busca profissional pelo CNS
  const buscarProfissional = useCallback(async (cns: string) => {
    if (cns.length < 15) return;

    const prof = await getProfissional(cns);
    if (prof) {
      setCabecalho(prev => ({
        ...prev,
        nome_profissional: prof.nome || '',
        cbo: prof.cbo || '',
        ine: prof.ine || '',
        cnes: prof.cnes || prev.cnes
      }));
    }
  }, []);

  // Busca paciente pelo CNS
  const buscarPaciente = useCallback(async (cns: string) => {
    if (cns.length < 15) return;

    const pac = await getPaciente(cns);
    if (pac) {
      setRegistro(prev => ({
        ...prev,
        nome_paciente: pac.nome || '',
        cpf_paciente: pac.cpf || '',
        data_nascimento: pac.data_nascimento || '',
        sexo: pac.sexo || '',
        raca_cor: pac.raca_cor || '99',
        municipio_ibge: pac.municipio_ibge || prev.municipio_ibge,
        cep: pac.cep || '',
        endereco: pac.endereco || '',
        numero: pac.numero || '',
        complemento: pac.complemento || '',
        bairro: pac.bairro || '',
        telefone: pac.telefone || '',
        email: pac.email || ''
      }));
    }
  }, []);

  // Busca procedimento
  const buscarProcedimento = async (termo: string) => {
    if (termo.length < 2) {
      setSearchResults([]);
      setShowProcedimentoSearch(false);
      return;
    }

    const results = await searchProcedimentos(termo);
    setSearchResults(results);
    setShowProcedimentoSearch(true); // Sempre mostra, mesmo se vazio
  };

  // Seleciona procedimento
  const selecionarProcedimento = (proc: Procedimento) => {
    setRegistro(prev => ({
      ...prev,
      procedimento: proc.codigo,
      procedimento_descricao: proc.descricao || ''
    }));
    setShowProcedimentoSearch(false);
    setSearchResults([]);
  };

  // Inclui registro
  const incluirRegistro = async () => {
    if (!cabecalho.cnes || !cabecalho.cns_profissional || !cabecalho.cbo || !cabecalho.competencia) {
      setMessage({ type: 'error', text: 'Preencha o cabeçalho (CNES, CNS Profissional, CBO e Competência)' });
      return;
    }

    if (!registro.cns_paciente || !registro.nome_paciente || !registro.data_nascimento ||
      !registro.sexo || !registro.procedimento || !registro.data_atendimento) {
      setMessage({ type: 'error', text: 'Preencha todos os campos obrigatórios do paciente e procedimento' });
      return;
    }

    setLoading(true);

    try {
      const data = {
        ...cabecalho,
        ...registro,
        nome_paciente: registro.nome_paciente.toUpperCase().substring(0, 30)
      };

      const result = await saveBPAIndividualizado(data);
      setRegistros(prev => [...prev, result]);

      // Limpa apenas dados do paciente/procedimento
      setRegistro({
        ...initialRegistro,
        municipio_ibge: registro.municipio_ibge,
        data_atendimento: registro.data_atendimento
      });

      setMessage({ type: 'success', text: 'Registro incluído com sucesso!' });
      setActiveTab('paciente');

      // Chama callback se definido
      if (onSave) {
        setTimeout(() => onSave(), 1000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao incluir registro' });
    } finally {
      setLoading(false);
    }
  };

  // Exclui registro
  const excluirRegistro = async (id: number) => {
    if (!window.confirm('Deseja realmente excluir este registro?')) return;

    try {
      await deleteBPAIndividualizado(id);
      setRegistros(prev => prev.filter(r => r.id !== id));
      setMessage({ type: 'success', text: 'Registro excluído' });
    } catch {
      setMessage({ type: 'error', text: 'Erro ao excluir registro' });
    }
  };

  // Limpa formulário
  const limparFormulario = () => {
    setRegistro(initialRegistro);
    setMessage(null);
  };

  // Carrega registros existentes
  useEffect(() => {
    if (cabecalho.cnes && cabecalho.competencia) {
      const loadRegistros = async () => {
        try {
          const data = await listBPAIndividualizado(cabecalho.cnes, cabecalho.competencia);
          setRegistros(data);
        } catch (error) {
          console.error('Erro ao carregar registros:', error);
        }
      };
      loadRegistros();
    }
  }, [cabecalho.cnes, cabecalho.competencia]);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <FileText className="w-7 h-7 text-primary-600" />
        BPA Individualizado - Cadastro
      </h2>

      {/* Mensagem */}
      {message && (
        <div className={`p-4 rounded-lg mb-6 flex justify-between items-center ${message.type === 'success' ? 'bg-success-50 text-success-700 border border-success-500' :
          message.type === 'error' ? 'bg-danger-50 text-danger-600 border border-danger-500' :
            'bg-warning-50 text-warning-600 border border-warning-500'
          }`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="text-xl font-bold hover:opacity-70">×</button>
        </div>
      )}

      {/* Cabeçalho */}
      <div className="bg-gray-100 p-5 rounded-lg mb-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">
              CNES *
              <span className="text-xs text-green-600 ml-1">(Preenchido automaticamente)</span>
            </label>
            <input
              type="text"
              value={cabecalho.cnes}
              onChange={(e) => setCabecalho({ ...cabecalho, cnes: e.target.value })}
              maxLength={7}
              placeholder="0000000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
              readOnly
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Profissional *</label>
            <select
              value={cabecalho.cns_profissional}
              onChange={(e) => {
                const cns = e.target.value;
                const prof = profissionaisList.find(p => p.cns === cns);
                if (prof) {
                  setCabecalho(prev => ({
                    ...prev,
                    cns_profissional: prof.cns,
                    nome_profissional: prof.nome,
                    cbo: prof.cbo || '',
                    ine: prof.ine || ''
                  }));
                } else {
                  setCabecalho(prev => ({ ...prev, cns_profissional: cns }));
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Selecione...</option>
              {profissionaisList.map(p => (
                <option key={p.id} value={p.cns}>
                  {p.nome} ({p.cbo})
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-gray-600 mb-1">Nome Profissional</label>
            <input
              type="text"
              value={cabecalho.nome_profissional}
              readOnly
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
            />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">
              CBO *
              <span className="text-xs text-green-600 ml-1">(Auto)</span>
            </label>
            <input
              type="text"
              value={cabecalho.cbo}
              maxLength={6}
              readOnly
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Código INE</label>
            <input
              type="text"
              value={cabecalho.ine}
              onChange={(e) => setCabecalho({ ...cabecalho, ine: e.target.value })}
              maxLength={10}
              placeholder="0000000000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Competência * (YYYYMM)</label>
            <input
              type="text"
              value={cabecalho.competencia}
              onChange={(e) => setCabecalho({ ...cabecalho, competencia: e.target.value })}
              maxLength={6}
              placeholder="202512"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Folha</label>
            <input
              type="number"
              value={cabecalho.folha}
              onChange={(e) => setCabecalho({ ...cabecalho, folha: parseInt(e.target.value) || 1 })}
              min={1}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-0">
        <button
          className={`px-5 py-3 rounded-t-lg font-medium transition-colors flex items-center gap-2 ${activeTab === 'paciente'
            ? 'bg-primary-600 text-white'
            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          onClick={() => setActiveTab('paciente')}
        >
          <User className="w-4 h-4" />
          [F6] Identificação do Paciente
        </button>
        <button
          className={`px-5 py-3 rounded-t-lg font-medium transition-colors flex items-center gap-2 ${activeTab === 'procedimento'
            ? 'bg-primary-600 text-white'
            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          onClick={() => setActiveTab('procedimento')}
        >
          <FileText className="w-4 h-4" />
          [F7] Procedimento Realizado
        </button>
      </div>

      {/* Tab Paciente */}
      {activeTab === 'paciente' && (
        <div className="bg-white border border-gray-200 rounded-b-lg rounded-tr-lg p-6 mb-6">
          <div className="bg-primary-600 text-white px-4 py-2 -mx-6 -mt-6 mb-4 rounded-t-lg font-medium">
            IDENTIFICAÇÃO DO PACIENTE
          </div>
          <p className="text-sm text-gray-500 mb-4">Usuário Sequência: {registros.length + 1}</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">CNS Paciente *</label>
              <input
                type="text"
                value={registro.cns_paciente}
                onChange={(e) => {
                  setRegistro({ ...registro, cns_paciente: e.target.value });
                  if (e.target.value.length === 15) buscarPaciente(e.target.value);
                }}
                maxLength={15}
                placeholder="000000000000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">CPF Paciente</label>
              <input
                type="text"
                value={registro.cpf_paciente}
                onChange={(e) => setRegistro({ ...registro, cpf_paciente: e.target.value })}
                maxLength={11}
                placeholder="00000000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Nome *</label>
              <input
                type="text"
                value={registro.nome_paciente}
                onChange={(e) => setRegistro({ ...registro, nome_paciente: e.target.value.toUpperCase() })}
                maxLength={30}
                placeholder="NOME COMPLETO DO PACIENTE"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Sexo *</label>
              <select
                value={registro.sexo}
                onChange={(e) => setRegistro({ ...registro, sexo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Selecione</option>
                {SEXOS.map(s => (
                  <option key={s.codigo} value={s.codigo}>{s.codigo} - {s.descricao}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Data Nascimento *</label>
              <input
                type="date"
                value={registro.data_nascimento}
                onChange={(e) => setRegistro({ ...registro, data_nascimento: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Nacionalidade</label>
              <input
                type="text"
                value={registro.nacionalidade}
                onChange={(e) => setRegistro({ ...registro, nacionalidade: e.target.value })}
                maxLength={3}
                placeholder="010"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Raça/Cor *</label>
              <select
                value={registro.raca_cor}
                onChange={(e) => setRegistro({ ...registro, raca_cor: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {RACAS.map(r => (
                  <option key={r.codigo} value={r.codigo}>{r.codigo} - {r.descricao}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Município IBGE *</label>
              <input
                type="text"
                value={registro.municipio_ibge}
                onChange={(e) => setRegistro({ ...registro, municipio_ibge: e.target.value })}
                maxLength={6}
                placeholder="172100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">CEP</label>
              <input
                type="text"
                value={registro.cep}
                onChange={(e) => setRegistro({ ...registro, cep: e.target.value })}
                maxLength={8}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Endereço</label>
              <input
                type="text"
                value={registro.endereco}
                onChange={(e) => setRegistro({ ...registro, endereco: e.target.value })}
                maxLength={200}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Número</label>
              <input
                type="text"
                value={registro.numero}
                onChange={(e) => setRegistro({ ...registro, numero: e.target.value })}
                maxLength={20}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Bairro</label>
              <input
                type="text"
                value={registro.bairro}
                onChange={(e) => setRegistro({ ...registro, bairro: e.target.value })}
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Telefone</label>
              <input
                type="text"
                value={registro.telefone}
                onChange={(e) => setRegistro({ ...registro, telefone: e.target.value })}
                maxLength={20}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-600 mb-1">E-mail</label>
              <input
                type="email"
                value={registro.email}
                onChange={(e) => setRegistro({ ...registro, email: e.target.value })}
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Tab Procedimento */}
      {activeTab === 'procedimento' && (
        <div className="bg-white border border-gray-200 rounded-b-lg rounded-tr-lg p-6 mb-6">
          <div className="bg-primary-600 text-white px-4 py-2 -mx-6 -mt-6 mb-4 rounded-t-lg font-medium">
            PROCEDIMENTO SOLICITADO
          </div>
          <p className="text-sm text-gray-500 mb-4">Procedimento Sequência: {registros.length + 1}</p>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Data Atendimento *</label>
              <input
                type="date"
                value={registro.data_atendimento}
                onChange={(e) => setRegistro({ ...registro, data_atendimento: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div className="relative col-span-2">
              <label className="block text-xs font-semibold text-gray-600 mb-1">
                Código Procedimento *
                <span className="text-xs text-primary-600 ml-1">
                  ({filteredProcedimentos.length} procedimentos disponíveis para CBO {user?.cbo || 'N/A'})
                </span>
              </label>

              {/* Dropdown customizado com pesquisa */}
              <div className="relative" ref={procedimentoDropdownRef}>
                <div className="relative">
                  <input
                    type="text"
                    value={procedimentoFilter || (registro.procedimento ? `${registro.procedimento} - ${registro.procedimento_descricao}` : '')}
                    onChange={(e) => {
                      handleProcedimentoFilter(e.target.value);
                      if (registro.procedimento) {
                        setRegistro({ ...registro, procedimento: '', procedimento_descricao: '' });
                      }
                    }}
                    onFocus={() => setShowProcedimentoSearch(true)}
                    placeholder="Digite código ou nome do procedimento..."
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                  <div className="absolute right-2 top-2 flex items-center gap-1">
                    {registro.procedimento && (
                      <button
                        type="button"
                        onClick={() => {
                          setRegistro({ ...registro, procedimento: '', procedimento_descricao: '' });
                          setProcedimentoFilter('');
                          setFilteredProcedimentos(allUserProcedimentos);
                        }}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <X className="w-4 h-4 text-gray-400" />
                      </button>
                    )}
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  </div>
                </div>

                {/* Lista dropdown */}
                {showProcedimentoSearch && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-64 overflow-y-auto">
                    {filteredProcedimentos.length > 0 ? (
                      filteredProcedimentos.map(proc => (
                        <div
                          key={proc.codigo}
                          onClick={() => {
                            setRegistro({
                              ...registro,
                              procedimento: proc.codigo,
                              procedimento_descricao: proc.descricao || ''
                            });
                            setProcedimentoFilter('');
                            setShowProcedimentoSearch(false);
                          }}
                          className={`px-3 py-2 cursor-pointer hover:bg-primary-50 border-b border-gray-100 last:border-b-0 ${registro.procedimento === proc.codigo ? 'bg-primary-100' : ''
                            }`}
                        >
                          <div className="font-medium text-sm text-gray-900">{proc.codigo}</div>
                          <div className="text-xs text-gray-600 mt-0.5">{proc.descricao || 'Sem descrição'}</div>
                        </div>
                      ))
                    ) : (
                      <div className="px-3 py-4 text-center text-sm text-gray-500">
                        {procedimentoFilter
                          ? `Nenhum procedimento encontrado para "${procedimentoFilter}"`
                          : 'Nenhum procedimento disponível'
                        }
                      </div>
                    )}
                  </div>
                )}
              </div>

              {allUserProcedimentos.length === 0 && (
                <p className="text-sm text-red-500 mt-1">
                  Nenhum procedimento disponível para seu CBO ({user?.cbo || 'N/A'})
                </p>
              )}
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Quantidade *</label>
              <input
                type="number"
                value={registro.quantidade}
                onChange={(e) => setRegistro({ ...registro, quantidade: parseInt(e.target.value) || 1 })}
                min={1}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">CID</label>
              <input
                type="text"
                value={registro.cid}
                onChange={(e) => setRegistro({ ...registro, cid: e.target.value.toUpperCase() })}
                maxLength={4}
                placeholder="A000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {registro.procedimento_descricao && (
            <div className="mb-4">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Descrição do Procedimento</label>
              <input
                type="text"
                value={registro.procedimento_descricao}
                disabled
                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-600"
              />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Caráter Atendimento *</label>
              <select
                value={registro.carater_atendimento}
                onChange={(e) => setRegistro({ ...registro, carater_atendimento: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {CARATER_ATENDIMENTO.map(c => (
                  <option key={c.codigo} value={c.codigo}>{c.codigo} - {c.descricao}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Autorização</label>
              <input
                type="text"
                value={registro.numero_autorizacao}
                onChange={(e) => setRegistro({ ...registro, numero_autorizacao: e.target.value })}
                maxLength={13}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">CNPJ</label>
              <input
                type="text"
                value={registro.cnpj}
                onChange={(e) => setRegistro({ ...registro, cnpj: e.target.value })}
                maxLength={14}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Serviço</label>
              <input
                type="text"
                value={registro.servico}
                onChange={(e) => setRegistro({ ...registro, servico: e.target.value })}
                maxLength={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Classificação</label>
              <input
                type="text"
                value={registro.classificacao}
                onChange={(e) => setRegistro({ ...registro, classificacao: e.target.value })}
                maxLength={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Botões de ação */}
      <div className="flex gap-3 mb-6">
        <button
          className="flex items-center gap-2 px-6 py-3 bg-success-600 text-white rounded-lg font-semibold hover:bg-success-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          onClick={incluirRegistro}
          disabled={loading}
        >
          {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
          {loading ? 'Salvando...' : 'Incluir'}
        </button>
        <button
          className="flex items-center gap-2 px-6 py-3 bg-gray-500 text-white rounded-lg font-semibold hover:bg-gray-600 transition-colors"
          onClick={limparFormulario}
        >
          <RefreshCw className="w-5 h-5" />
          Limpar
        </button>
      </div>

      {/* Tabela de registros */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-600" />
          Registros Incluídos ({registros.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Seq</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">CNS Paciente</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Nome</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Dt.Atend</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Procedimento</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">QTD</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Status</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Ação</th>
              </tr>
            </thead>
            <tbody>
              {registros.map((reg, idx) => (
                <tr key={reg.id || idx} className={`border-b border-gray-100 hover:bg-gray-50 ${reg.exportado ? 'bg-success-50' : ''}`}>
                  <td className="px-3 py-2">{idx + 1}</td>
                  <td className="px-3 py-2 font-mono text-xs">{reg.cns_paciente}</td>
                  <td className="px-3 py-2">{reg.nome_paciente}</td>
                  <td className="px-3 py-2">{reg.data_atendimento}</td>
                  <td className="px-3 py-2 font-mono">{reg.procedimento}</td>
                  <td className="px-3 py-2">{reg.quantidade}</td>
                  <td className="px-3 py-2">
                    {reg.exportado ? (
                      <span className="inline-flex items-center gap-1 text-success-600">
                        <CheckCircle className="w-4 h-4" /> Exportado
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-warning-600">
                        <Clock className="w-4 h-4" /> Pendente
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => reg.id && excluirRegistro(reg.id)}
                      className="text-danger-600 hover:text-danger-700 p-1"
                      title="Excluir"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {registros.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-3 py-8 text-center text-gray-500">
                    Nenhum registro incluído
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FormBPA;
