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
import { BarChart3 } from "lucide-react";

import { GraphIcon } from "../icons/AnalyticsIcons";
import ReviewProgressState from "./ReviewProgressState";

/* TOOLTIP */
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

/* TRANSFORM */
function transformData(rawData = []) {
    return rawData.map((item) => {
        const score = item.avg_score;
        let positive = 0, negative = 0;

        if (score >= 0.05) positive = Math.round(score * 100);
        else if (score <= -0.05) negative = Math.round(Math.abs(score) * 100);

        const label = item.period?.slice(5) ?? item.period;

        return { period: label, positive, negative };
    });
}

/* MAIN COMPONENT */
function SentimentChart({ data = [], meta = {} }) {
    const chartData = transformData(data);

    const isEmpty = chartData.length === 0;
    const isInsufficient = !meta?.is_reliable || chartData.length < 2;

    const sampleSize = meta?.sample_size ?? 0;
    const minRequired = meta?.min_required ?? 5;

    const step = Math.ceil(chartData.length / 10);

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">

            {/* HEADER */}
            <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-gray-700" />
                    <h2 className="text-lg font-semibold text-gray-900">
                        Customer Sentiment Trend
                    </h2>
                </div>
            </div>

            <p className="text-xs text-gray-400 mb-5">
                Monitor positive and negative feedback patterns over time
            </p>

            {/* BODY */}
            {isEmpty ? (
                <div className="h-[260px] flex flex-col items-center justify-center gap-3 text-center">
                    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-300">
                        <GraphIcon className="w-6 h-6" />
                    </div>
                    <p className="font-medium text-gray-700">No sentiment data yet</p>
                    <p className="text-sm text-gray-400">
                        Reviews will populate this chart over time.
                    </p>
                </div>

            ) : isInsufficient ? (
                <ReviewProgressState
                    sampleSize={sampleSize}
                    minRequired={minRequired}
                    title="Almost there..."
                    description="Need more reviews to generate reliable sentiment insights."
                />

            ) : (
                <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />

                        <XAxis
                            dataKey="period"
                            tick={{ fontSize: 11, fill: "#9ca3af" }}
                            interval={step - 1}
                        />

                        <YAxis
                            domain={[0, 100]}
                            tick={{ fontSize: 11, fill: "#9ca3af" }}
                            tickFormatter={(v) => `${v}%`}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        <Legend />

                                <Area dataKey="positive" stroke="#22c55e" fill="#22c55e" />
                                <Area dataKey="negative" stroke="#ef4444" fill="#ef4444" />
                    </AreaChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}

export default SentimentChart;