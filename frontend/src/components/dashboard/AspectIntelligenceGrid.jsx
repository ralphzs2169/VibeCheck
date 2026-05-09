import { useEffect, useState } from "react";

/* ===========================
   HELPERS
=========================== */

function formatAspectName(name) {
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

function getActionStyle(action) {
    switch (action) {
        case "fix":
            return {
                bg: "bg-red-50",
                text: "text-red-700",
                border: "border-red-100",
                dot: "bg-red-500"
            };
        case "leverage":
            return {
                bg: "bg-green-50",
                text: "text-green-700",
                border: "border-green-100",
                dot: "bg-green-500"
            };
        case "monitor":
        default:
            return {
                bg: "bg-gray-50",
                text: "text-gray-700",
                border: "border-gray-100",
                dot: "bg-gray-500"
            };
    }
}

function getScoreColor(score, scoreType, isReliable = true) {
    // De-emphasize color coding for early-stage data
    if (!isReliable) {
        return "text-gray-600";  // All early-stage scores shown in neutral gray
    }
    
    if (scoreType === "risk") {
        if (score >= 70) return "text-red-600";
        if (score >= 40) return "text-orange-600";
        return "text-gray-600";
    }
    if (scoreType === "positive") {
        if (score >= 70) return "text-green-600";
        if (score >= 40) return "text-lime-600";
        return "text-gray-600";
    }
    return "text-gray-600";
}

function getProgressBarColor(scoreType, value, isReliable = true) {
    // De-emphasize colors for early-stage data
    if (!isReliable) {
        return "bg-gray-300";  // All early-stage progress bars in neutral gray
    }
    
    if (scoreType === "risk") {
        if (value >= 70) return "bg-red-500";
        if (value >= 40) return "bg-orange-500";
        return "bg-gray-300";
    }
    if (scoreType === "positive") {
        if (value >= 70) return "bg-green-500";
        if (value >= 40) return "bg-lime-500";
        return "bg-gray-300";
    }
    return "bg-gray-300";
}

/* ===========================
   ASPECT CARD
=========================== */
function AspectCard({ name, aspect, isReliable = true }) {
    const [hovered, setHovered] = useState(false);

    const actionStyle = getActionStyle(aspect.action_priority);

    // Pass isReliable flag to color functions
    const riskColor = getScoreColor(aspect.risk_score, "risk", isReliable);
    const positiveColor = getScoreColor(aspect.positive_score, "positive", isReliable);

    const riskBarColor = getProgressBarColor("risk", aspect.risk_score, isReliable);
    const positiveBarColor = getProgressBarColor("positive", aspect.positive_score, isReliable);
    
    // Determine which signal is dominant (backend logic)
    const maxScore = Math.max(aspect.risk_score, aspect.positive_score, aspect.neutral_score);
    const dominantSignal = maxScore === aspect.risk_score ? "risk" : maxScore === aspect.positive_score ? "positive" : "neutral";

    return (
        <div
            className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow duration-200"
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            {/* Header with aspect name and action badge */}
            <div className="flex items-start justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-900">
                    {formatAspectName(name)}
                </h3>
                <div className={`text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1 ${actionStyle.bg} ${actionStyle.text} ${actionStyle.border} border`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${actionStyle.dot}`} />
                    {aspect.action_priority === "fix"
                        ? "Fix"
                        : aspect.action_priority === "leverage"
                        ? "Leverage"
                        : "Monitor"}
                </div>
            </div>

            {/* Risk Score */}
            <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                    <p className="text-xs text-gray-600 font-medium">Risk</p>
                    <p className={`text-xs font-semibold ${riskColor}`}>
                        {aspect.risk_score.toFixed(0)}%
                    </p>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-300 ${riskBarColor}`}
                        style={{ width: `${Math.min(aspect.risk_score, 100)}%` }}
                    />
                </div>
            </div>

            {/* Positive Score */}
            <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                    <p className="text-xs text-gray-600 font-medium">Positive</p>
                    <p className={`text-xs font-semibold ${positiveColor}`}>
                        {aspect.positive_score.toFixed(0)}%
                    </p>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-300 ${positiveBarColor}`}
                        style={{ width: `${Math.min(aspect.positive_score, 100)}%` }}
                    />
                </div>
            </div>

            {/* Neutral Score (subtle) */}
            <div className="pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">Neutral</p>
                    <p className="text-xs font-semibold text-gray-600">
                        {aspect.neutral_score.toFixed(0)}%
                    </p>
                </div>
            </div>

            {/* Tooltip on hover - updated with dominance logic and maturity awareness */}
            {hovered && (
                <div className="absolute z-20 -top-32 left-1/2 -translate-x-1/2 bg-white border border-gray-200 shadow-lg rounded-lg px-3 py-2 text-xs w-56">
                    <p className="font-semibold text-gray-900 mb-1">Probability Model</p>
                    <p className="text-gray-600 mb-2">
                        Risk: {aspect.risk_score.toFixed(0)}% | Positive: {aspect.positive_score.toFixed(0)}% | Neutral: {aspect.neutral_score.toFixed(0)}%
                    </p>
                    <p className="text-gray-500 text-[10px]">
                        {!isReliable && "⚠️ Early-stage data: colors muted"}
                    </p>
                    <p className="text-gray-500 text-[10px] mt-1">
                        Action: <span className="font-semibold capitalize">{dominantSignal}</span> (dominant signal)
                    </p>
                </div>
            )}
        </div>
    );
}

/* ===========================
   MAIN GRID COMPONENT
=========================== */
function AspectIntelligenceGrid({ data = {} }) {
    const aspects = data.aspects || {};

    // Handle empty state
    if (!aspects || Object.keys(aspects).length === 0) {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                    Aspect Intelligence Grid
                </h2>
                <p className="text-xs text-gray-400 mb-6">
                    Per-aspect analytics showing risk, positive, and uncertainty scores
                </p>

                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">No aspect data yet</h3>
                    <p className="text-xs text-gray-400">Data will appear once reviews are analyzed</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                    Aspect Intelligence Grid
                </h2>
                <p className="text-xs text-gray-400">
                    Per-aspect analytics showing risk, positive, and uncertainty scores
                </p>
            </div>

            {/* Legend */}
            <div className="mb-6 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                <p className="text-xs text-blue-800 font-medium mb-2">Probability Model</p>
                <div className="grid grid-cols-3 gap-4 text-xs text-blue-700">
                    <div>
                        <span className="font-semibold text-red-600">Risk</span>: Potential issues
                    </div>
                    <div>
                        <span className="font-semibold text-green-600">Positive</span>: Strengths
                    </div>
                    <div>
                        <span className="font-semibold text-gray-600">Neutral</span>: Uncertainty
                    </div>
                </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(aspects).map(([name, aspect]) => (
                    <div key={name} className="relative">
                        <AspectCard
                            name={name}
                            aspect={aspect}
                                isReliable={data.meta?.is_reliable ?? false}
                            />
                    </div>
                ))}
            </div>

            {/* Meta information */}
            {data.meta && (
                <div className="mt-6 pt-6 border-t border-gray-100 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0zm3 0a1 1 0 11-2 0 1 1 0 012 0zm3 0a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
                    </svg>
                    <p className="text-xs text-gray-600">
                        {data.meta.is_reliable ? "Reliable analysis" : "Limited data quality"}
                    </p>
                </div>
            )}
        </div>
    );
}

export default AspectIntelligenceGrid;
