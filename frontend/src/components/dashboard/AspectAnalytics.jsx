import { useEffect, useState } from "react";
import {
    ImprovingIcon,
    DecliningIcon,
    StableIcon,
} from "../icons/TrendIcons";

const FIXED_ASPECT_ORDER = [
    "food",
    "service",
    "staff",
    "cleanliness",
    "price",
    "ambience",
    "location",
    "experience",
];

// -----------------------------
// SCORE LABEL
// -----------------------------
function formatAspect(score) {
    let label = "Mixed";

    if (score >= 0.8) label = "Highly Positive";
    else if (score >= 0.3) label = "Positive";
    else if (score <= -0.8) label = "Highly Negative";
    else if (score <= -0.3) label = "Negative";

    return {
        raw: score,
        label,
    };
}

// -----------------------------
// TREND FORMATTER
// -----------------------------
function formatTrend(trend) {
    switch (trend) {
        case "improving":
            return {
                label: "Improving",
                Icon: ImprovingIcon,
                color: "text-green-600",
                bg: "bg-green-50",
            };

        case "declining":
            return {
                label: "Declining",
                Icon: DecliningIcon,
                color: "text-red-600",
                bg: "bg-red-50",
            };

        default:
            return {
                label: "Stable",
                Icon: StableIcon,
                color: "text-gray-500",
                bg: "bg-gray-50",
            };
    }
}

// -----------------------------
// TOOLTIP (UPDATED)
// -----------------------------
function AspectTooltip({ data, trendUI }) {
    if (!data || !trendUI) return null;

    const Icon = trendUI.Icon;

    return (
        <div className="absolute z-20 -top-16 left-1/2 -translate-x-1/2 bg-white border border-gray-100 shadow-lg rounded-xl px-3 py-2 text-xs whitespace-nowrap">

            <p className="text-gray-500 mb-1">
                {data.label}
            </p>

            <div className={`flex items-center gap-1 font-semibold ${trendUI.color}`}>
                <Icon className="w-4 h-4" />
                <span>{trendUI.label}</span>
            </div>

            <p className="text-[#004687] mt-1 font-medium">
                Score: {data.raw.toFixed(2)}
            </p>
        </div>
    );
}

// -----------------------------
// MAIN COMPONENT
// -----------------------------
function AspectAnalytics({ aspects = [], onViewAll }) {
    const [hovered, setHovered] = useState(null);
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        const t = setTimeout(() => setAnimate(true), 150);
        return () => clearTimeout(t);
    }, []);

    const aspectMap = Object.fromEntries(
        aspects.map((a) => [a.name, a])
    );

    const sortedAspects = [...FIXED_ASPECT_ORDER].sort((a, b) => {
        const aHas = aspectMap[a] !== undefined;
        const bHas = aspectMap[b] !== undefined;
        if (aHas && !bHas) return -1;
        if (!aHas && bHas) return 1;
        return 0;
    });

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col">

            <h2 className="text-lg font-semibold text-gray-900 mb-5">
                Aspect Analytics
            </h2>

            <div className="flex flex-col gap-5 flex-1">

                {sortedAspects.slice(0, 4).map((aspectName, index) => {
                    const aspect = aspectMap[aspectName];
                    const hasData = !!aspect;

                    const score = aspect?.score;
                    const trend = aspect?.trend;

                    const data = hasData ? formatAspect(score) : null;
                    const trendUI = formatTrend(trend);

                    const Icon = trendUI.Icon;

                    const rawPercent = hasData
                        ? Math.round(((score + 1) / 2) * 100)
                        : 0;

                    // Ensure that when an aspect is highly negative we still show
                    // a small visible red segment instead of leaving the bar empty.
                    const MIN_NEGATIVE_PERCENT = 6; // small visible sliver

                    const percent = hasData
                        ? score <= -0.8
                            ? Math.max(rawPercent, MIN_NEGATIVE_PERCENT)
                            : rawPercent
                        : 0;

                    const barColor =
                        score >= 0.3
                            ? "bg-green-500"
                            : score <= -0.3
                            ? "bg-red-500"
                            : "bg-yellow-400";

                    return (
                        <div
                            key={aspectName}
                            className="relative"
                            onMouseEnter={() => setHovered(aspectName)}
                            onMouseLeave={() => setHovered(null)}
                        >

                            {/* TOOLTIP */}
                            {hovered === aspectName && hasData && (
                                <AspectTooltip
                                    data={data}
                                    trendUI={trendUI}
                                />
                            )}

                            {/* HEADER */}
                            <div className="flex justify-between items-center mb-1">

                                {/* LEFT: ICON + NAME */}
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-gray-700 font-medium capitalize">
                                        {aspectName}
                                    </span>

                                    {hasData && (
                                        <Icon
                                            className={`w-5 h-5 ${trendUI.color}`}
                                        />
                                    )}

                                    
                                </div>

                                {/* RIGHT: LABEL ONLY (NO TREND BADGE ANYMORE) */}
                                <span className="text-xs font-medium text-gray-800">
                                    {hasData ? data.label : "--"}
                                </span>

                            </div>

                            {/* BAR */}
                            <div className="relative h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
                                    style={{
                                        width: animate
                                            ? `${percent}%`
                                            : "0%",
                                        transitionDelay: `${index * 60}ms`,
                                    }}
                                />
                            </div>

                            {!hasData && (
                                <p className="text-xs text-gray-400 mt-1">
                                    No data yet
                                </p>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* BUTTON */}
            <button
                onClick={onViewAll}
                className="mt-6 w-full border border-gray-200 rounded-xl py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
                View All Aspects
            </button>
        </div>
    );
}

export default AspectAnalytics;