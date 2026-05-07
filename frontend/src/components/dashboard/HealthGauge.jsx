import React from "react";
import {
    ResponsiveContainer,
    RadialBarChart,
    RadialBar,
    PolarAngleAxis,
    Tooltip,
} from "recharts";

/* -----------------------------
   HELPERS
------------------------------ */
function clamp01(value) {
    if (value == null) return 0;
    return Math.max(0, Math.min(1, value));
}

function getColor(score) {
    if (score >= 0.75) return "#22c55e";
    if (score >= 0.55) return "#84cc16";
    if (score >= 0.35) return "#facc15";
    if (score >= 0.15) return "#f97316";
    return "#ef4444";
}

function getLabel(score) {
    if (score >= 0.75) return "Excellent";
    if (score >= 0.55) return "Healthy";
    if (score >= 0.35) return "Fair";
    if (score >= 0.15) return "Weak";
    return "Critical";
}

/* -----------------------------
   TOOLTIP (FULL INSIGHTS)
------------------------------ */
function InsightsTooltip({ active, payload }) {
    if (!active || !payload?.length) return null;

    const data = payload[0]?.payload;
    const insights = data?.insights || {};
    const breakdown = data?.breakdown || {};

    return (
        <div className="bg-white border border-gray-100 shadow-xl rounded-xl p-3 text-xs w-64">
            <p className="font-semibold text-gray-700 mb-2">
                Business Health Insights
            </p>

            <div className="space-y-2 text-gray-600">

                <div>
                    <p className="font-medium">Overall Health</p>
                    <p>{insights.health?.label}</p>
                    <p className="text-gray-400">{insights.health?.meaning}</p>
                </div>

                <div>
                    <p className="font-medium">Vibe Score</p>
                    <p>{data?.raw?.vibe_score ?? "--"}</p>
                </div>

                <div>
                    <p className="font-medium">Trend</p>
                    <p>{breakdown.trend?.toFixed?.(2) ?? "--"}</p>
                </div>

                <div>
                    <p className="font-medium">Consistency</p>
                    <p>{insights.consistency?.label}</p>
                    <p className="text-gray-400">{insights.consistency?.meaning}</p>
                </div>

                <div>
                    <p className="font-medium">Confidence</p>
                    <p>{insights.confidence?.label}</p>
                    <p className="text-gray-400">{insights.confidence?.meaning}</p>
                </div>
            </div>
        </div>
    );
}

/* -----------------------------
   MAIN COMPONENT
------------------------------ */
function HealthGauge({ data }) {
    const score = clamp01(data?.score);
    const color = getColor(score);
    const label = data?.label || getLabel(score);

    const breakdown = data?.breakdown || {};
    const insights = data?.insights || {};

    const chartData = [
        {
            name: "health",
            value: score * 100,
            fill: color,
            breakdown,
            insights,
        },
    ];

    return (
        <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">

            {/* HEADER */}
            <div className="mb-3">
                <h3 className="text-sm font-semibold text-gray-900">
                    Business Health
                </h3>
                <p className="text-xs text-gray-500">
                    Composite performance score
                </p>
            </div>

            {/* GAUGE */}
            <div className="relative w-full h-[140px] border border-amber-200">
                <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                        innerRadius="75%"
                        outerRadius="100%"
                        data={chartData}
                        startAngle={180}
                        endAngle={0}
                    >
                        <PolarAngleAxis
                            type="number"
                            domain={[0, 100]}
                            tick={false}
                        />

                        <RadialBar
                            dataKey="value"
                            cornerRadius={12}
                            background={{ fill: "#f1f5f9" }}
                        />

                        <Tooltip content={<InsightsTooltip />} />
                    </RadialBarChart>
                </ResponsiveContainer>

                {/* CENTER */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <div className="text-3xl font-bold text-gray-900">
                        {score.toFixed(2)}
                    </div>

                    <div
                        className="text-sm font-semibold mt-1"
                        style={{ color }}
                    >
                        {label}
                    </div>
                </div>
            </div>

            {/* BREAKDOWN TITLE */}
            <div className="mt-4">
                <p className="text-xs font-semibold text-gray-700 mb-2">
                    Score Breakdown
                </p>

                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">

                    <div className="bg-gray-50 rounded-lg p-2">
                        <p className="font-medium">Vibe Score</p>
                        <p>{data?.raw?.vibe_score ?? "--"}</p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-2">
                        <p className="font-medium">Trend</p>
                        <p>{breakdown.trend?.toFixed?.(2) ?? "--"}</p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-2">
                        <p className="font-medium">Consistency</p>
                        <p>{insights.consistency?.label ?? "--"}</p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-2">
                        <p className="font-medium">Confidence</p>
                        <p>{insights.confidence?.label ?? "--"}</p>
                    </div>

                </div>
            </div>
        </div>
    );
}

export default HealthGauge;