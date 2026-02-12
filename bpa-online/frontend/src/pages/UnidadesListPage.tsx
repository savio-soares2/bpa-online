import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Building2,
    Users,
    UserCheck,
    Search,
    ChevronRight,
    Stethoscope,
    Heart,
    Sparkles,
    Activity
} from 'lucide-react';
import api from '../services/api';

// Mapa de ícones por tipo de unidade
const TIPO_ICONS: Record<string, React.ReactNode> = {
    'CAPS': <Heart className="w-6 h-6" />,
    'AMBULATORIO': <Stethoscope className="w-6 h-6" />,
    'POLICLINICA': <Building2 className="w-6 h-6" />,
    'UPA': <Activity className="w-6 h-6" />,
    'CEO': <Sparkles className="w-6 h-6" />,
    'LABORATORIO': <Building2 className="w-6 h-6" />,
    'CENTRO_REF': <Building2 className="w-6 h-6" />
};

const TIPO_COLORS: Record<string, string> = {
    'CAPS': 'bg-purple-100 text-purple-600 border-purple-200',
    'AMBULATORIO': 'bg-blue-100 text-blue-600 border-blue-200',
    'POLICLINICA': 'bg-green-100 text-green-600 border-green-200',
    'UPA': 'bg-red-100 text-red-600 border-red-200',
    'CEO': 'bg-amber-100 text-amber-600 border-amber-200',
    'LABORATORIO': 'bg-gray-100 text-gray-600 border-gray-200',
    'CENTRO_REF': 'bg-teal-100 text-teal-600 border-teal-200'
};

interface Unidade {
    cnes: string;
    nome: string;
    sigla: string;
    tipo: string;
    profissionais: number;
    usuarios: number;
}

const UnidadesListPage: React.FC = () => {
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');
    const [unidades, setUnidades] = useState<Unidade[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadUnidades();
    }, []);

    const loadUnidades = async () => {
        try {
            const response = await api.get('/admin/unidades');
            setUnidades(response.data);
        } catch (error) {
            console.error('Erro ao carregar unidades:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredUnidades = unidades.filter(est =>
        est.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
        est.sigla.toLowerCase().includes(searchTerm.toLowerCase()) ||
        est.cnes.includes(searchTerm)
    );

    const handleUnidadeClick = (cnes: string) => {
        navigate(`/admin/unidades/${cnes}`);
    };

    return (
        <div className="p-6 max-w-7xl mx-auto animate-fadeIn">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <Building2 className="w-7 h-7 text-primary-600" />
                    Gestão de Unidades
                </h1>
                <p className="text-gray-500 mt-1">
                    Visualize e gerencie as unidades de saúde cadastradas
                </p>
            </div>

            {/* Search */}
            <div className="relative mb-6">
                <Search className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    placeholder="Buscar por nome, sigla ou CNES..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white shadow-sm"
                />
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary-100 rounded-lg">
                            <Building2 className="w-5 h-5 text-primary-600" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-gray-800">{unidades.length}</p>
                            <p className="text-sm text-gray-500">Unidades Cadastradas</p>
                        </div>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <UserCheck className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-gray-800">
                                {unidades.reduce((acc, s) => acc + s.profissionais, 0)}
                            </p>
                            <p className="text-sm text-gray-500">Profissionais Totais</p>
                        </div>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <Users className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-gray-800">
                                {unidades.reduce((acc, s) => acc + s.usuarios, 0)}
                            </p>
                            <p className="text-sm text-gray-500">Usuários do Sistema</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Unidades Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="bg-white p-6 rounded-xl border border-gray-200 animate-pulse">
                            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredUnidades.map(unidade => (
                        <div
                            key={unidade.cnes}
                            onClick={() => handleUnidadeClick(unidade.cnes)}
                            className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-primary-300 transition-all cursor-pointer group"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className={`p-3 rounded-xl ${TIPO_COLORS[unidade.tipo] || 'bg-gray-100 text-gray-600'}`}>
                                    {TIPO_ICONS[unidade.tipo] || <Building2 className="w-6 h-6" />}
                                </div>
                                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
                            </div>

                            {/* Info */}
                            <h3 className="font-semibold text-gray-800 mb-1 line-clamp-2">
                                {unidade.sigla}
                            </h3>
                            <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                                {unidade.nome}
                            </p>

                            {/* CNES Badge */}
                            <div className="flex items-center gap-2 mb-4">
                                <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                    CNES: {unidade.cnes}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded capitalize ${TIPO_COLORS[unidade.tipo] || 'bg-gray-100 text-gray-600'}`}>
                                    {unidade.tipo.replace('_', ' ').toLowerCase()}
                                </span>
                            </div>

                            {/* Stats */}
                            <div className="flex items-center gap-4 pt-4 border-t border-gray-100">
                                <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                    <UserCheck className="w-4 h-4 text-green-500" />
                                    <span>{unidade.profissionais} profissionais</span>
                                </div>
                                <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                    <Users className="w-4 h-4 text-blue-500" />
                                    <span>{unidade.usuarios} usuários</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {filteredUnidades.length === 0 && !loading && (
                <div className="text-center py-12">
                    <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">Nenhuma unidade encontrada para "{searchTerm}"</p>
                </div>
            )}
        </div>
    );
};

export default UnidadesListPage;
