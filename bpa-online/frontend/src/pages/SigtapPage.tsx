import React, { useState } from 'react';
import { BookOpen, Settings, Info } from 'lucide-react';
import SigtapDashboard from '../components/sigtap/SigtapDashboard';
import SigtapManager from '../components/sigtap/SigtapManager';

const SigtapPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'consulta' | 'gestao'>('consulta');

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <BookOpen className="w-8 h-8 text-primary-600" />
                        Gestão SIGTAP
                    </h1>
                    <p className="text-gray-500">
                        Consulta de procedimentos e gerenciamento de tabelas unificadas.
                    </p>
                </div>
            </header>

            {/* Abas */}
            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => setActiveTab('consulta')}
                        className={`
                            whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                            ${activeTab === 'consulta'
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                        `}
                    >
                        <BookOpen className="w-4 h-4" />
                        Consulta de Procedimentos
                    </button>
                    <button
                        onClick={() => setActiveTab('gestao')}
                        className={`
                            whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                            ${activeTab === 'gestao'
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                        `}
                    >
                        <Settings className="w-4 h-4" />
                        Gerenciar Tabelas
                    </button>
                </nav>
            </div>

            {/* Conteúdo */}
            <div className="min-h-[500px]">
                {activeTab === 'consulta' ? (
                    <SigtapDashboard />
                ) : (
                    <SigtapManager />
                )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4 flex items-start gap-3 text-sm text-blue-800">
                <Info className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <p>
                    As tabelas SIGTAP são fundamentais para validação dos registros BPA. Certifique-se de manter a competência ativa atualizada mensalmente.
                </p>
            </div>
        </div>
    );
};

export default SigtapPage;
