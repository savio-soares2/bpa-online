
import React from 'react';

interface StatCardProps {
    title: string;
    value: string | number;
    subValue?: string;
    icon?: React.ReactNode;
    color?: 'blue' | 'green' | 'orange' | 'purple';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subValue, icon, color = 'blue' }) => {
    const colorClasses = {
        blue: 'bg-blue-50 text-blue-700 border-blue-100',
        green: 'bg-green-50 text-green-700 border-green-100',
        orange: 'bg-orange-50 text-orange-700 border-orange-100',
        purple: 'bg-purple-50 text-purple-700 border-purple-100',
    };

    const textColors = {
        blue: 'text-blue-900',
        green: 'text-green-900',
        orange: 'text-orange-900',
        purple: 'text-purple-900',
    };

    return (
        <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-sm font-medium opacity-80">{title}</p>
                    <h3 className={`text-2xl font-bold mt-1 ${textColors[color]}`}>{value}</h3>
                    {subValue && (
                        <p className="text-xs mt-1 opacity-70">{subValue}</p>
                    )}
                </div>
                {icon && <div className="opacity-50">{icon}</div>}
            </div>
        </div>
    );
};

export default StatCard;
