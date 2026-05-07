import React, { useMemo } from "react";
import {
	ResponsiveContainer,
	LineChart,
	Line,
	XAxis,
	YAxis,
	Tooltip,
	CartesianGrid,
} from "recharts";

function addMonths(period, monthsToAdd) {
	if (typeof period !== "string" || !period.includes("-")) {
		return String(period);
	}

	const [year, month] = period.split("-").map((value) => parseInt(value, 10));
	if (Number.isNaN(year) || Number.isNaN(month)) return period;

	const date = new Date(Date.UTC(year, month - 1, 1));
	date.setUTCMonth(date.getUTCMonth() + monthsToAdd);

	const nextYear = date.getUTCFullYear();
	const nextMonth = String(date.getUTCMonth() + 1).padStart(2, "0");

	return `${nextYear}-${nextMonth}`;
}

function buildForecastDataset(payload = {}) {
	const history = Array.isArray(payload.history) ? payload.history : [];
	const forecast = Array.isArray(payload.forecast) ? payload.forecast : [];

	const historyRows = history.map((item) => ({
		period: item.period,
		value: Number(item.avg_score ?? 0),
		type: "history",
		actual: Number(item.avg_score ?? 0),
		forecast: null,
	}));

	const lastHistoryPeriod = historyRows.at(-1)?.period;

	const forecastRows = forecast.map((item, index) => ({
		period: typeof item.period === "string" && item.period.includes("-")
			? item.period
			: lastHistoryPeriod
				? addMonths(lastHistoryPeriod, index + 1)
				: String(item.period),
		value: Number(item.predicted ?? 0),
		type: "forecast",
		actual: null,
		forecast: Number(item.predicted ?? 0),
	}));

	return [...historyRows, ...forecastRows].sort((left, right) => {
		if (left.period < right.period) return -1;
		if (left.period > right.period) return 1;
		if (left.type === right.type) return 0;
		return left.type === "history" ? -1 : 1;
	});
}

function ForecastTooltip({ active, payload }) {
	if (!active || !payload?.length) return null;

	const point = payload[0].payload;

	return (
		<div className="rounded-xl border border-gray-100 bg-white px-3 py-2 shadow-lg">
			<div className="text-xs font-semibold text-gray-700">{point.period}</div>
			<div className="mt-0.5 text-[11px] text-gray-500">
				{point.type === "history" ? "Historical" : "Forecast"}
			</div>
			<div className="mt-1 text-sm font-semibold text-[#004687]">
				{Number(point.value ?? 0).toFixed(2)}
			</div>
		</div>
	);
}

export default function SentimentForecastChart({ data = {} }) {
	const chartData = useMemo(() => buildForecastDataset(data), [data]);

	const isReliable = data?.meta?.is_reliable !== false;
	const predictedVibe = data?.predicted_vibe || "mixed";
	const forecastScore = Number(data?.forecast_score);

	const vibeBadge = {
		positive: "bg-green-50 text-green-700 border-green-100",
		negative: "bg-red-50 text-red-700 border-red-100",
		mixed: "bg-gray-50 text-gray-700 border-gray-100",
	}[predictedVibe] || "bg-gray-50 text-gray-700 border-gray-100";

	return (
		<div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
			<div className="mb-4 flex flex-wrap items-start justify-between gap-3">
				<div>
					<h3 className="text-sm font-semibold text-gray-900">Sentiment Forecast</h3>
					<p className="mt-1 text-xs text-gray-500">
						Historical sentiment versus projected future movement
					</p>
				</div>

				<div className="flex flex-wrap items-center gap-2">
					<span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${vibeBadge}`}>
						{predictedVibe.charAt(0).toUpperCase() + predictedVibe.slice(1)}
					</span>

					{!isReliable && (
						<span className="rounded-full border border-amber-100 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
							Low confidence forecast
						</span>
					)}

					{Number.isFinite(forecastScore) && (
						<span className="rounded-full border border-sky-100 bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">
							Forecast score: {forecastScore.toFixed(2)}
						</span>
					)}
				</div>
			</div>

			<div className="h-72">
				<ResponsiveContainer width="100%" height="100%">
					<LineChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
						<CartesianGrid stroke="#eef2f7" strokeDasharray="3 3" />
						<XAxis dataKey="period" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
						<YAxis domain={[-1, 1]} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
						<Tooltip content={<ForecastTooltip />} />

						<Line
							type="monotone"
							dataKey="actual"
							name="Historical"
							stroke="#0f766e"
							strokeWidth={2.5}
							dot={{ r: 3, fill: "#0f766e", strokeWidth: 0 }}
							activeDot={{ r: 5 }}
							connectNulls={false}
						/>

						<Line
							type="monotone"
							dataKey="forecast"
							name="Forecast"
							stroke="#0f766e"
							strokeOpacity={0.55}
							strokeWidth={2.5}
							strokeDasharray="6 6"
							dot={{ r: 3, fill: "#0f766e", strokeWidth: 0 }}
							activeDot={{ r: 5 }}
							connectNulls={false}
						/>
					</LineChart>
				</ResponsiveContainer>
			</div>
		</div>
	);
}
