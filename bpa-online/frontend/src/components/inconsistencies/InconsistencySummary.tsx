import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';

interface SummaryProps {
    total: number;
    critical: number;
    warnings: number;
    loading?: boolean;
}

const InconsistencySummary: React.FC<SummaryProps> = ({ total, critical, warnings, loading }) => {
    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 animate-pulse">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-gray-100 h-24 rounded-xl border border-gray-200"></div>
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex items-center gap-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                    <AlertCircle className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                    <p className="text-sm text-gray-500 font-medium">Total de Inconsistências</p>
                    <p className="text-2xl font-bold text-gray-800">{total}</p>
                </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex items-center gap-4">
                <div className="bg-red-100 p-3 rounded-lg">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
                <div>
                    <p className="text-sm text-gray-500 font-medium">Críticos (Exclusão)</p>
                    <p className="text-2xl font-bold text-gray-800">{critical}</p>
                </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex items-center gap-4">
                <div className="bg-amber-100 p-3 rounded-lg">
                    <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                    <p className="text-sm text-gray-500 font-medium">Avisos de Correção</p>
                    <p className="text-2xl font-bold text-gray-800">{warnings}</p>
                </div>
            </div>
        </div>
    );
};

export default InconsistencySummary;
