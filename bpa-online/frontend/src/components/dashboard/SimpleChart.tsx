
import React from 'react';

interface ChartData {
    label: string;
    value: number;
    tooltip?: string;
    color?: string;
}

interface SimpleChartProps {
    type: 'bar' | 'line';
    data: ChartData[];
    height?: number;
    title?: string;
    currency?: boolean;
}

const SimpleChart: React.FC<SimpleChartProps> = ({ type, data, height = 200, title, currency = false }) => {
    const maxValue = Math.max(...data.map(d => d.value), 1);

    const formatValue = (val: number) => {
        if (currency) return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        return val.toLocaleString('pt-BR');
    };

    if (type === 'bar') {
        return (
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                {title && <h3 className="text-sm font-medium text-gray-700 mb-4">{title}</h3>}
                <div className="flex flex-col gap-3">
                    {data.map((item, idx) => (
                        <div key={idx} className="w-full">
                            <div className="flex justify-between text-xs mb-1">
                                <span className="font-medium text-gray-600 truncate max-w-[70%]" title={item.label}>{item.label}</span>
                                <span className="text-gray-500">{formatValue(item.value)}</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all duration-500"
                                    style={{
                                        width: `${(item.value / maxValue) * 100}%`,
                                        backgroundColor: item.color || '#F97316'
                                    }}
                                    title={item.tooltip}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // Line Chart (Simplificado com SVG)
    if (type === 'line') {
        const points = data.map((d, i) => {
            const x = (i / (data.length - 1 || 1)) * 100;
            const y = 100 - ((d.value / maxValue) * 100);
            return `${x},${y}`;
        }).join(' ');

        return (
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                {title && <h3 className="text-sm font-medium text-gray-700 mb-4">{title}</h3>}
                <div className="relative w-full" style={{ height: height }}>
                    {/* Grid lines */}
                    <div className="absolute inset-0 flex flex-col justify-between text-xs text-gray-300 pointer-events-none">
                        <div className="border-b border-dashed border-gray-200 w-full h-0"></div>
                        <div className="border-b border-dashed border-gray-200 w-full h-0"></div>
                        <div className="border-b border-dashed border-gray-200 w-full h-0"></div>
                        <div className="border-b border-dashed border-gray-200 w-full h-0"></div>
                    </div>

                    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
                        <polyline
                            fill="none"
                            stroke="#F97316"
                            strokeWidth="2"
                            points={points}
                            vectorEffect="non-scaling-stroke"
                        />
                        {data.map((d, i) => {
                            const x = (i / (data.length - 1 || 1)) * 100;
                            const y = 100 - ((d.value / maxValue) * 100);
                            return (
                                <circle
                                    key={i}
                                    cx={x}
                                    cy={y}
                                    r="3"
                                    fill="#fff"
                                    stroke="#F97316"
                                    strokeWidth="2"
                                    vectorEffect="non-scaling-stroke"
                                    className="hover:r-4 transition-all"
                                >
                                    <title>{d.label}: {formatValue(d.value)}</title>
                                </circle>
                            )
                        })}
                    </svg>
                </div>

                {/* X Axis Labels */}
                <div className="flex justify-between mt-2 text-xs text-gray-500 px-1">
                    {data.map((d, i) => (
                        <span key={i} className="truncate max-w-[50px]">{d.label.split('-')[1] || d.label}</span> // Mostra só o Mês se for YYYY-MM
                    ))}
                </div>
            </div>
        );
    }

    return null;
};

export default SimpleChart;
