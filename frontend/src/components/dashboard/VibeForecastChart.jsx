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

import { GraphIcon } from "../icons/AnalyticsIcons";

/* -----------------------------
   HELPERS
------------------------------ */

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

    const lastHistory = history[history.length - 1]?.period;

    const historyPoints = history.map((item) => ({
        period: item.period,
        history: item.avg_score,
        forecast: null,
        type: "history",
    }));

    const forecastPoints = forecast.map((item) => ({
        period:
            typeof item.period === "string"
                ? item.period
                : toPeriodLabelFromOffset(lastHistory, Number(item.period)),
        history: null,
        forecast: item.predicted,
        type: "forecast",
    }));

    if (historyPoints.length && forecastPoints.length) {
        forecastPoints.unshift({
            period: historyPoints.at(-1).period,
            history: historyPoints.at(-1).history,
            forecast: historyPoints.at(-1).history,
            type: "forecast",
        });
    }

    return [...historyPoints, ...forecastPoints];
}

function getVibeLabel(score) {
    if (score >= 3.5) return "Positive";
    if (score <= 2.5) return "Negative";
    return "Mixed";
}

/* -----------------------------
   TOOLTIP
------------------------------ */

function CustomTooltip({ active, payload }) {
    if (!active || !payload?.length) return null;

    const point = payload[0].payload;
    const value = point.history ?? point.forecast ?? 0;

    return (
        <div className="bg-white border border-gray-100 shadow-xl rounded-xl px-3 py-2 text-xs">
            <p className="font-semibold text-gray-700">{point.period}</p>
            <p className="text-gray-500 mt-1">
                {point.type === "forecast" ? "Forecast" : "Historical"}
            </p>
            <p className="font-semibold text-[#004687] mt-1">
                Vibe Score: {value.toFixed(1)}
            </p>
            <p className="text-gray-500">Vibe: {getVibeLabel(value)}</p>
        </div>
    );
}

/* -----------------------------
   MAIN COMPONENT
------------------------------ */

export default function VibeForecastChart({ data = {} }) {
    const historyCount = data?.history?.length ?? 0;

    const isInsufficient =
        data?.meta?.is_reliable === false || historyCount < 6;

    const dataset = useMemo(
        () => mergeHistoryAndForecast(data),
        [data]
    );

    const futureMonths = data.forecast_months || 6;

    const forecastStart = dataset.find((i) => i.type === "forecast")?.period;
    const forecastEnd = dataset.at(-1)?.period;

    const vibe = data.predicted_vibe || "mixed";

    const vibeBadge = {
        positive: "bg-green-50 text-green-700",
        negative: "bg-red-50 text-red-700",
        mixed: "bg-gray-50 text-gray-700",
    }[vibe];

    const insightText =
        vibe === "positive"
            ? "Forecast suggests a positive trend in upcoming months."
            : vibe === "negative"
            ? "Forecast suggests a declining trend in upcoming months."
            : "Forecast shows no strong directional shift.";

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">

            {/* HEADER */}
            <div className="flex justify-between items-start mb-5">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                        Vibe Score Forecast
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Next {futureMonths} months projection
                    </p>
                </div>

                {!isInsufficient && (
                    <div className={`text-xs font-semibold px-3 py-1 rounded-full ${vibeBadge}`}>
                        {vibe.charAt(0).toUpperCase() + vibe.slice(1)}
                    </div>
                )}
            </div>

            {/* BODY */}
            <div className="h-[280px]">

                {isInsufficient ? (
                    <div className="h-full flex flex-col items-center justify-center text-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-300">
                            <GraphIcon className="w-6 h-6" />
                        </div>

                        <p className="font-medium text-gray-700">
                            Forecast not ready yet
                        </p>

                        <p className="text-xs text-gray-400">
                            Need at least{" "}
                            <span className="font-semibold text-[#004687]">
                                6 months of data
                            </span>{" "}
                            to generate predictions.
                        </p>
                    </div>

                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={dataset}>
                            <defs>
                                <linearGradient id="vibeGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#004687" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#004687" stopOpacity={0} />
                                </linearGradient>

                                <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.1} />
                                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                                </linearGradient>
                            </defs>

                            <CartesianGrid strokeDasharray="3 3" vertical={false} />

                            {forecastStart && (
                                <ReferenceArea x1={forecastStart} x2={forecastEnd} fill="#f8fafc" />
                            )}

                            <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                            <YAxis domain={[1, 5]} tick={{ fontSize: 12 }} />

                            <Tooltip content={<CustomTooltip />} />

                            <Area
                                type="monotone"
                                dataKey="history"
                                stroke="#004687"
                                fill="url(#vibeGradient)"
                                strokeWidth={2.5}
                                dot={false}
                                connectNulls={false}
                            />

                            <Area
                                type="monotone"
                                dataKey="forecast"
                                stroke="#0ea5e9"
                                fill="url(#forecastGradient)"
                                strokeDasharray="6 6"
                                strokeWidth={2.5}
                                dot={false}
                                connectNulls
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* INSIGHT */}
            {!isInsufficient && (
                <div className="mt-4 bg-gray-50 rounded-xl p-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">
                        Forecast Insight
                    </p>
                    <p className="text-sm text-gray-500">{insightText}</p>
                </div>
            )}
        </div>
    );
}