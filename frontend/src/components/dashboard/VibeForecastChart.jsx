import React, { useMemo } from "react";
import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    ReferenceArea,
} from "recharts";

function toPeriodLabelFromOffset(baseLabel, offset) {
    try {
        const [y, m] = baseLabel.split("-").map(Number);
        const date = new Date(Date.UTC(y, m - 1, 1));
        date.setUTCMonth(date.getUTCMonth() + offset);

        return `${date.getUTCFullYear()}-${String(
            date.getUTCMonth() + 1
        ).padStart(2, "0")}`;
    } catch {
        return String(offset);
    }
}

function mergeHistoryAndForecast(payload = {}) {
    const history = Array.isArray(payload.history) ? payload.history : [];
    const forecast = Array.isArray(payload.forecast) ? payload.forecast : [];
    const future_months = payload.forecast_months || 6;

    const lastHistory = history[history.length - 1]?.period;

    const historyPoints = history.map((item) => ({
        period: item.period,
        history: item.avg_score,
        forecast: null,
        future_months: null,
        type: "history",
    }));

    const forecastPoints = forecast.map((item) => ({
        period:
            typeof item.period === "string"
                ? item.period
                : toPeriodLabelFromOffset(lastHistory, Number(item.period)),
        history: null,
        forecast: item.predicted,
        future_months: null,
        type: "forecast",
    }));

    // Connect forecast line from last historical point
    if (historyPoints.length && forecastPoints.length) {
        forecastPoints.unshift({
            period: historyPoints[historyPoints.length - 1].period,
            history: null,
            forecast: historyPoints[historyPoints.length - 1].history,
            type: "forecast",
            future_months: null,
        });
    }

    return [...historyPoints, ...forecastPoints];
}

function getVibeLabel(score) {
    if (score >= 3.5) return "Positive";
    if (score <= 2.5) return "Negative";
    return "Mixed";
}

function CustomTooltip({ active, payload }) {
    if (!active || !payload?.length) return null;

    const point = payload[0].payload;
    const value = point.history ?? point.forecast ?? 0;
    const vibeLabel = getVibeLabel(value);

    return (
        <div className="bg-white border border-gray-100 shadow-xl rounded-xl px-3 py-2 text-xs">
            <p className="font-semibold text-gray-700">{point.period}</p>

            <p className="text-gray-500 mt-1">
                {point.type === "forecast" ? "Forecast" : "Historical"}
            </p>

            <p className="font-semibold text-[#004687] mt-1">
                Vibe Score: {value.toFixed(1)}
            </p>

            <p className="text-gray-500">
                Vibe: {vibeLabel}
            </p>
        </div>
    );
}

function ForecastLegend() {
    return (
        <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-2">
                <div className="w-4 h-[2px] bg-sky-500" />
                Historical
            </div>

            <div className="flex items-center gap-2">
                <div className="w-4 h-[2px] border-t-2 border-dashed border-sky-500 opacity-70" />
                Forecast
            </div>
        </div>
    );
}

export default function VibeForecastChart({ data = {} }) {
    const dataset = useMemo(() => mergeHistoryAndForecast(data), [data]);

    const primaryColor = "#0ea5e9";
    const future_months = data.forecast_months || 6;

    const forecastStart = dataset.find(
        (item) => item.type === "forecast"
    )?.period;

    const forecastEnd = dataset[dataset.length - 1]?.period;

    const vibe = data.predicted_vibe || "mixed";

    const vibeBadge = {
        positive: {
            label: "Forecast: Positive",
            className: "bg-green-50 text-green-700",
        },
        negative: {
            label: "Forecast: Negative",
            className: "bg-red-50 text-red-700",
        },
        mixed: {
            label: "Forecast: Mixed",
            className: "bg-gray-50 text-gray-700",
        },
    }[vibe];

    const insightText =
        vibe === "positive"
            ? "Forecast suggests the business vibe may remain positive in upcoming months."
            : vibe === "negative"
            ? "Forecast suggests the business vibe may continue declining in upcoming months."
            : "Forecast shows no strong directional shift in overall vibe.";

    return (
        <div className="min-w-0 bg-white rounded-2xl border border-gray-100 shadow-sm p-6 h-full flex flex-col">
            {/* HEADER */}
            <div className="flex items-start justify-between mb-5">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                        Vibe Score Forecast
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                       Historical vibe score with trend forecasting for next {future_months} months
                    </p>
                </div>

                <div
                    className={`text-xs font-semibold px-3 py-1 rounded-full ${vibeBadge.className}`}
                >
                    {vibeBadge.label}
                </div>
            </div>

            {/* LEGEND */}
            <div className="mb-4">
                <ForecastLegend />
            </div>

            {/* CHART */}
            <div className="min-w-0 flex-1 min-h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                        data={dataset}
                        margin={{
                            top: 5,
                            right: 5,
                            left: -20,
                            bottom: 0,
                        }}
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
                            <linearGradient
                                id="forecastGradient"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="5%"
                                    stopColor="#0ea5e9"
                                    stopOpacity={0.08}
                                />
                                <stop
                                    offset="95%"
                                    stopColor="#0ea5e9"
                                    stopOpacity={0}
                                />
                            </linearGradient>
                        </defs>

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#f0f0f0"
                            vertical={false}
                        />

                        {forecastStart && (
                            <ReferenceArea
                                x1={forecastStart}
                                x2={forecastEnd}
                                fill="#f8fafc"
                            />
                        )}

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
                            tickFormatter={(value) => value.toFixed(1)}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        {/* Historical */}
                        <Area
                            type="monotone"
                            dataKey="history"
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
                            connectNulls={false}
                        />

                        {/* Forecast */}
                        <Area
                            type="monotone"
                            dataKey="forecast"
                            stroke="#0ea5e9"
                            strokeWidth={2.5}
                            strokeDasharray="6 6"
                            fill="url(#forecastGradient)"
                            strokeOpacity={0.65}
                            dot={false}
                            activeDot={{
                                r: 5,
                                fill: "#0ea5e9",
                                stroke: "#fff",
                                strokeWidth: 2,
                            }}
                            connectNulls
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* INSIGHT */}
            <div className="mt-4 bg-gray-50 rounded-xl p-3">
                <p className="text-sm font-medium text-gray-700 mb-1">
                    Forecast Insight
                </p>
                <p className="text-sm text-gray-500">
                    {insightText}
                </p>
            </div>
        </div>
    );
}