import React from 'react';
import { AlertCircle, AlertTriangle, User, FileText, Info } from 'lucide-react';

interface InconsistencyDetail {
    id: number;
    paciente: string;
    procedimento: string;
    data: string;
    tipo: 'critical' | 'warning';
    mensagem: string;
    corrections: string[];
}

interface InconsistencyListProps {
    details: InconsistencyDetail[];
}

const InconsistencyList: React.FC<InconsistencyListProps> = ({ details }) => {
    if (details.length === 0) {
        return (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Info className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-800">Nenhuma inconsistência encontrada</h3>
                <p className="text-gray-500 mt-2">
                    Os dados para este filtro estão consistentes de acordo com as regras de validação.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="font-semibold text-gray-800">Detalhes das Inconsistências</h3>
            </div>
            <div className="divide-y divide-gray-200">
                {details.map((item) => (
                    <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-start justify-between">
                            <div className="flex gap-4">
                                <div className={`mt-1 p-2 rounded-lg ${item.tipo === 'critical' ? 'bg-red-100' : 'bg-amber-100'}`}>
                                    {item.tipo === 'critical' ? (
                                        <AlertCircle className={`w-5 h-5 text-red-600`} />
                                    ) : (
                                        <AlertTriangle className={`w-5 h-5 text-amber-600`} />
                                    )}
                                </div>
                                <div>
                                    <div className="flex items-center gap-3 mb-1">
                                        <span className="font-bold text-gray-800 flex items-center gap-1">
                                            <User className="w-4 h-4 text-gray-400" />
                                            {item.paciente || 'PACIENTE NÃO IDENTIFICADO'}
                                        </span>
                                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                                            ID: {item.id}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${item.tipo === 'critical' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                                            }`}>
                                            {item.tipo === 'critical' ? 'CRÍTICO / EXCLUSÃO' : 'AVISO / CORREÇÃO'}
                                        </span>
                                    </div>

                                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-2">
                                        <span className="flex items-center gap-1">
                                            <FileText className="w-4 h-4" />
                                            PA: {item.procedimento}
                                        </span>
                                        <span>•</span>
                                        <span>Data: {item.data ? new Date(item.data).toLocaleDateString('pt-BR') : 'N/A'}</span>
                                    </div>

                                    <div className={`p-3 rounded-lg border ${item.tipo === 'critical' ? 'bg-red-50 border-red-100' : 'bg-amber-50 border-amber-100'
                                        }`}>
                                        <p className={`text-sm font-medium ${item.tipo === 'critical' ? 'text-red-800' : 'text-amber-800'
                                            }`}>
                                            {item.mensagem}
                                        </p>
                                    </div>

                                    {item.corrections.length > 1 && (
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            {item.corrections.map((corr, idx) => (
                                                <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded border border-gray-200">
                                                    {corr}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default InconsistencyList;
