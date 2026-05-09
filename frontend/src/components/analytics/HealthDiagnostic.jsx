import HealthGauge from "../dashboard/HealthGauge";

function formatPercent(value) {
	if (value == null || Number.isNaN(Number(value))) return "--";

	const normalized = Number(value) <= 1 ? Number(value) * 100 : Number(value);
	return `${normalized.toFixed(1)}%`;
}

function getImpactLabel(value) {
	if (value == null || Number.isNaN(Number(value))) return "unknown impact";

	const normalized = Number(value) <= 1 ? Number(value) : Number(value) / 100;

	if (normalized >= 0.7) return "high impact";
	if (normalized >= 0.4) return "moderate impact";
	return "low impact";
}

function getRiskLevel(score) {
	if (score == null || Number.isNaN(Number(score))) return "Unknown";
	if (score >= 0.7) return "Low";
	if (score >= 0.45) return "Medium";
	return "High";
}

function getPrimaryRiskDriver(breakdown = {}, raw = {}) {
	const entries = Object.entries(breakdown).filter(([, value]) => typeof value === "number");

	if (!entries.length) return "Insufficient signal";

	const [weakestKey] = entries.sort((a, b) => a[1] - b[1])[0];

	const labels = {
		vibe: raw.vibe_score != null && raw.vibe_score < 3 ? "Vibe / sentiment softness" : "Vibe pressure",
		trend: raw.trend_label === "declining" ? "Trend decline" : "Trend stability",
		consistency: "Consistency drift",
		confidence: "Data confidence gap",
	};

	return labels[weakestKey] || weakestKey;
}

function InsightRow({ label, meaning, level }) {
	const levelStyles = {
		good: "bg-green-50 text-green-700 border-green-100",
		reliable: "bg-blue-50 text-blue-700 border-blue-100",
		moderate: "bg-amber-50 text-amber-700 border-amber-100",
		weak: "bg-red-50 text-red-700 border-red-100",
	};

	return (
		<div className="rounded-xl border border-gray-100 bg-white p-4">
			<div className="flex items-start justify-between gap-4">
				<div>
					<p className="text-sm font-semibold text-gray-900">{label}</p>
					<p className="text-sm text-gray-500 mt-1">{meaning}</p>
				</div>
				<span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${levelStyles[level] || levelStyles.moderate}`}>
					{level}
				</span>
			</div>
		</div>
	);
}

function BreakdownItem({ label, value, descriptor }) {
	return (
		<div className="rounded-xl border border-gray-100 bg-white p-4">
			<div className="flex items-center justify-between gap-4">
				<div>
					<p className="text-sm font-semibold text-gray-900">{label}</p>
					<p className="text-xs text-gray-500 mt-1 capitalize">{descriptor}</p>
				</div>
				<div className="text-right">
					<p className="text-lg font-bold text-gray-900">{formatPercent(value)}</p>
					<p className="text-xs text-gray-400">weighted contribution</p>
				</div>
			</div>
		</div>
	);
}

export default function HealthDiagnostic({ data = {} }) {
	const score = data?.score;
	const label = data?.label || "Unknown";
	const breakdown = data?.breakdown || {};
	const insights = data?.insights || {};
	const raw = data?.raw || {};

	const overallScore = score == null ? "--" : (Number(score) <= 1 ? Number(score) * 100 : Number(score)).toFixed(1);
	const riskLevel = getRiskLevel(score);
	const primaryRiskDriver = getPrimaryRiskDriver(breakdown, raw);

	const summary =
		insights?.health?.meaning ||
		`Business health is currently assessed as ${label.toLowerCase()} based on the balance of vibe, trend, consistency, and confidence signals.`;

	const keyInsight =
		`Health is being driven most strongly by ${primaryRiskDriver.toLowerCase()}, while ${raw.data_quality || "the available data"} shapes how much confidence we should place in the diagnosis.`;

	return (
		<section className="w-full rounded-2xl border border-gray-100 bg-white shadow-sm p-5 xl:p-6">
			<div className="space-y-5">
				<div className="flex flex-col gap-4 border-b border-gray-100 pb-4">
					<div className="flex flex-col gap-2">
						<p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#004687]">Deep Analysis</p>
						<h2 className="text-2xl font-semibold text-gray-900">Business Health Diagnostic</h2>
						<p className="max-w-3xl text-sm text-gray-500">
							Analytical breakdown of the business health score, its strongest drivers, and the reliability of the signal.
						</p>
					</div>

					<div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)] xl:items-start">
						<HealthGauge data={data} />

						<div className="grid gap-3 rounded-2xl bg-gray-50 p-4">
							<div className="flex flex-wrap items-center gap-4">
								<div>
									<p className="text-xs font-medium uppercase tracking-wide text-gray-400">Overall Health Score</p>
									<p className="text-3xl font-bold text-gray-900">
										{overallScore}
										{overallScore !== "--" ? "%" : ""}
									</p>
								</div>
								<div>
									<p className="text-xs font-medium uppercase tracking-wide text-gray-400">Status</p>
									<p className="mt-1 inline-flex rounded-full bg-[#004687] px-3 py-1 text-sm font-semibold text-white">{label}</p>
								</div>
								<div>
									<p className="text-xs font-medium uppercase tracking-wide text-gray-400">Risk Level</p>
									<p className="mt-1 text-lg font-semibold text-gray-900">{riskLevel}</p>
								</div>
							</div>

							<p className="text-sm leading-6 text-gray-600">{summary}</p>
							<p className="text-sm leading-6 text-gray-600">{keyInsight}</p>
						</div>
					</div>
				</div>

				<div className="grid gap-4 xl:grid-cols-2">
					<div>
						<p className="mb-3 text-sm font-semibold text-gray-900">Drivers of Health</p>
						<div className="grid gap-3 sm:grid-cols-2">
							<BreakdownItem label="Vibe" value={breakdown.vibe} descriptor={getImpactLabel(breakdown.vibe)} />
							<BreakdownItem label="Trend" value={breakdown.trend} descriptor={getImpactLabel(breakdown.trend)} />
							<BreakdownItem label="Consistency" value={breakdown.consistency} descriptor={getImpactLabel(breakdown.consistency)} />
							<BreakdownItem label="Confidence" value={breakdown.confidence} descriptor={getImpactLabel(breakdown.confidence)} />
						</div>
					</div>

					<div className="grid gap-3">
						<p className="text-sm font-semibold text-gray-900">Insight Interpretation Layer</p>
						<InsightRow
							label={insights?.consistency?.label || "Consistency"}
							meaning={insights?.consistency?.meaning || "No consistency interpretation available."}
							level={insights?.consistency?.level || "moderate"}
						/>
						<InsightRow
							label={insights?.confidence?.label || "Confidence"}
							meaning={insights?.confidence?.meaning || "No confidence interpretation available."}
							level={insights?.confidence?.level || "moderate"}
						/>
						<InsightRow
							label={insights?.health?.label || label}
							meaning={insights?.health?.meaning || summary}
							level={insights?.health?.level || "moderate"}
						/>
					</div>
				</div>

				<div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
					<div className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
						<p className="text-sm font-semibold text-gray-900">Risk Analysis</p>
						<div className="mt-3 space-y-3 text-sm text-gray-600">
							<div className="flex items-center justify-between gap-4">
								<span>Primary Risk Driver</span>
								<span className="font-semibold text-gray-900 text-right">{primaryRiskDriver}</span>
							</div>
							<div className="flex items-center justify-between gap-4">
								<span>Risk Direction</span>
								<span className="font-semibold text-gray-900">{riskLevel}</span>
							</div>
						</div>
					</div>

					<div className="rounded-2xl border border-gray-100 bg-white p-4">
						<p className="text-sm font-semibold text-gray-900">Data Context</p>
						<div className="mt-3 grid gap-3 sm:grid-cols-3 text-sm text-gray-600">
							<div className="rounded-xl bg-gray-50 p-3">
								<p className="text-xs uppercase tracking-wide text-gray-400">Review Count</p>
								<p className="mt-1 text-lg font-semibold text-gray-900">{raw.review_count ?? "--"}</p>
							</div>
							<div className="rounded-xl bg-gray-50 p-3">
								<p className="text-xs uppercase tracking-wide text-gray-400">Data Quality</p>
								<p className="mt-1 text-lg font-semibold text-gray-900 capitalize">{raw.data_quality ?? "--"}</p>
							</div>
							<div className="rounded-xl bg-gray-50 p-3">
								<p className="text-xs uppercase tracking-wide text-gray-400">Cold Start</p>
								<p className="mt-1 text-lg font-semibold text-gray-900">{raw.is_cold_start ? "Yes" : "No"}</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>
	);
}
