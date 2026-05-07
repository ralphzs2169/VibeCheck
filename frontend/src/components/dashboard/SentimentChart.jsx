import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
    Legend,
} from "recharts";

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-3 py-2 text-sm space-y-1">
                <p className="text-gray-500 font-medium mb-1">{label}</p>
                {payload.map((p) => (
                    <p key={p.dataKey} style={{ color: p.color }} className="font-semibold">
                        {p.name}: {p.value}%
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

// Convert raw avg_score (-1 to 1) into per-period positive/neutral/negative buckets
function transformData(rawData = []) {
    return rawData.map((item) => {
        const score = item.avg_score;
        let positive = 0, neutral = 0, negative = 0;

        if (score >= 0.05) positive = Math.round(score * 100);
        else if (score <= -0.05) negative = Math.round(Math.abs(score) * 100);
        else neutral = 100;

        // Format period label — shorten to MM/DD
        const label = item.period?.slice(5) ?? item.period;

        return { period: label, positive, neutral, negative };
    });
}

function SentimentChart({ data = [], meta = {} }) {
    console.log("Raw sentiment over time data:", data);
    const chartData = transformData(data);
    const isInsufficient = !meta?.is_reliable || chartData.length < 2;
    const remaining = Math.max((meta?.min_required ?? 5) - (meta?.sample_size ?? 0), 0);

    if (chartData.length === 0) {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Sentiment Over Time</h2>
                <div className="h-[260px] flex flex-col items-center justify-center gap-3 text-center">
                    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-2xl">📉</div>
                    <p className="font-medium text-gray-700">No sentiment data yet</p>
                    <p className="text-sm text-gray-400">Reviews will populate this chart over time.</p>
                </div>
            </div>
        );
    }

    if (isInsufficient) {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Sentiment Over Time</h2>
                <div className="h-[260px] flex flex-col items-center justify-center gap-3 text-center px-6">
                    <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-2xl">📈</div>
                    <p className="font-medium text-gray-700">Almost there...</p>
                    <p className="text-sm text-gray-400">
                        Need <span className="font-semibold text-[#004687]">{remaining} more review{remaining !== 1 ? "s" : ""}</span> for a reliable trend.
                    </p>
                    <div className="w-full max-w-xs">
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>{meta?.sample_size ?? 0} collected</span>
                            <span>{meta?.min_required ?? 5} needed</span>
                        </div>
                        <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-[#004687] rounded-full"
                                style={{ width: `${Math.min(((meta?.sample_size ?? 0) / (meta?.min_required ?? 5)) * 100, 100)}%` }}
                            />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Show every Nth label to avoid crowding
    const step = Math.ceil(chartData.length / 10);
    const tickFormatter = (_, index) => index % step === 0 ? chartData[index]?.period : "";

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <div className="flex items-center justify-between mb-1">
                <h2 className="text-lg font-semibold text-gray-900">Sentiment Over Time</h2>
            </div>
            <p className="text-xs text-gray-400 mb-5">Daily breakdown of positive, neutral, and negative signals</p>

            <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id="gradPos" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradNeg" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradNeu" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />

                    <XAxis
                        dataKey="period"
                        tick={{ fontSize: 11, fill: "#9ca3af" }}
                        axisLine={false}
                        tickLine={false}
                        interval={step - 1}
                    />

                    <YAxis
                        domain={[0, 100]}
                        tick={{ fontSize: 11, fill: "#9ca3af" }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                    />

                    <Tooltip content={<CustomTooltip />} />

                    <Legend
                        iconType="circle"
                        iconSize={8}
                        wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
                    />

                    <Area type="monotone" dataKey="positive" name="Positive" stroke="#22c55e" strokeWidth={2} fill="url(#gradPos)" dot={false} />
                    <Area type="monotone" dataKey="neutral"  name="Neutral"  stroke="#94a3b8" strokeWidth={2} fill="url(#gradNeu)" dot={false} />
                    <Area type="monotone" dataKey="negative" name="Negative" stroke="#ef4444" strokeWidth={2} fill="url(#gradNeg)" dot={false} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}

export default SentimentChart;