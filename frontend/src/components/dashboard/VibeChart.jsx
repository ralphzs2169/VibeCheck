import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
} from "recharts";
import { useState } from "react";

const RANGES = ["7D", "30D", "90D"];

/* Tooltip for vibe score chart */
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const value = payload[0].value;

        return (
            <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-3 py-2 text-sm">
                <p className="text-gray-500">{label}</p>
                <p className="font-semibold text-[#004687]">
                    Vibe Score: {Number(value).toFixed(2)} / 5
                </p>
            </div>
        );
    }
    return null;
};

// Empty and insufficient data state containers
function EmptyState({ type, minRequired, sampleSize }) {
    if (type === "no_data") {
        return (
            <div className="h-[320px] flex flex-col items-center justify-center gap-3 text-center px-6">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-2xl">
                    📊
                </div>
                <div>
                    <p className="font-medium text-gray-700">No vibe data yet</p>
                    <p className="text-sm text-gray-400 mt-1">
                        once your first reviews come in, your vibe trend will appear here.
                    </p>
                </div>
            </div>
        );
    }

    if (type === "insufficient") {
        const remaining = (minRequired ?? 5) - (sampleSize ?? 1);

        return (
            <div className="h-[320px] flex flex-col items-center justify-center gap-3 text-center px-6">
                <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-2xl">
                    📈
                </div>
                <div>
                    <p className="font-medium text-gray-700">building your trend...</p>
                    <p className="text-sm text-gray-400 mt-1">
                        you need{" "}
                        <span className="font-semibold text-[#004687]">
                            {remaining} more review{remaining !== 1 ? "s" : ""}
                        </span>{" "}
                        across different days to see your vibe trend chart.
                    </p>
                </div>
            </div>
        );
    }

    return null;
}

// Main component
function VibeChart({ data = {}, vibeOverTime = {} }) {
    const [range, setRange] = useState("7D");

    const rawData = data?.[range] || [];

    const chartData = rawData.map((item) => ({
        period: item.period,
        vibe_score: Number(item.avg_score),
    }));

    const sampleSize = vibeOverTime?.meta?.sample_size ?? rawData.length;
    const minRequired = vibeOverTime?.meta?.min_required ?? 5;

    const isEmpty = chartData.length === 0;
    const isInsufficient = !isEmpty && chartData.length < 2;

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            {/* Header with range selector */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                        Vibe Over Time
                    </h2>

                    {!isEmpty && !isInsufficient && (
                        <p className="text-xs text-gray-400 mt-0.5">
                            Business Vibe Score (1–5 scale)
                        </p>
                    )}
                </div>

                {/* Range Selector */}
                <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                    {RANGES.map((r) => (
                        <button
                            key={r}
                            onClick={() => setRange(r)}
                            className={`text-xs font-medium px-3 py-1.5 rounded-md transition-all ${
                                range === r
                                    ? "bg-[#004687] text-white"
                                    : "text-gray-500 hover:text-gray-700"
                            }`}
                        >
                            {r}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart Content */}
            {isEmpty ? (
                <EmptyState type="no_data" />
            ) : isInsufficient ? (
                <EmptyState
                    type="insufficient"
                    sampleSize={sampleSize}
                    minRequired={minRequired}
                />
            ) : (
        
                <ResponsiveContainer width="100%" height={420}>
                    <AreaChart
                        data={chartData}
                        margin={{ top: 5, right: 5, left: -20, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient
                                id="vibeGradient"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="5%"
                                    stopColor="#004687"
                                    stopOpacity={0.15}
                                />
                                <stop
                                    offset="95%"
                                    stopColor="#004687"
                                    stopOpacity={0}
                                />
                            </linearGradient>
                        </defs>

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#f0f0f0"
                            vertical={false}
                        />

                        <XAxis
                            dataKey="period"
                            tick={{ fontSize: 12, fill: "#9ca3af" }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            domain={[1, 5]}
                            tick={{ fontSize: 12, fill: "#9ca3af" }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(v) => v.toFixed(1)}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        <Area
                            type="monotone"
                            dataKey="vibe_score"
                            stroke="#004687"
                            strokeWidth={2.5}
                            fill="url(#vibeGradient)"
                            dot={false}
                            activeDot={{
                                r: 5,
                                fill: "#004687",
                                stroke: "#fff",
                                strokeWidth: 2,
                            }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}

export default VibeChart;