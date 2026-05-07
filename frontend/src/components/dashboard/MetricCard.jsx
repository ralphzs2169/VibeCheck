import {
    ImprovingIcon,
    DecliningIcon,
    StableIcon,
} from "../icons/TrendIcons";

function MetricCard({ label, value, subtitle, badge, trend, vibeStatus }) {
    const badgeColor =
        badge?.type === "stable"
            ? "bg-green-50 text-green-600"
            : badge?.type === "alert"
            ? "bg-red-50 text-red-600"
            : badge?.type === "warning"
            ? "bg-yellow-50 text-yellow-600"
            : "bg-blue-50 text-[#004687]";

    const BadgeIcon = null; // (optional: you can later replace this too with SVG system)

    const hasTrend =
        trend?.direction && vibeStatus !== "no_data";

    const isStable =
        trend?.direction === "stable" ||
        (trend?.direction &&
            Math.abs(Number(trend?.value ?? 0)) < 0.01);

    const TrendIcon =
        trend?.direction === "improving"
            ? ImprovingIcon
            : trend?.direction === "declining"
            ? DecliningIcon
            : StableIcon;

    const trendColor =
        trend?.direction === "improving"
            ? "text-green-600"
            : trend?.direction === "declining"
            ? "text-red-600"
            : "text-gray-500";

    const trendLabel =
        trend?.direction === "improving"
            ? "Improving"
            : trend?.direction === "declining"
            ? "Declining"
            : "Stable";

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col gap-1">

            {/* header */}
            <div className="flex items-center justify-between mb-1">
                <p className="text-sm text-gray-500 font-medium">
                    {label}
                </p>

                {badge && (
                    <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${badgeColor}`}
                    >
                        {badge.label}
                    </span>
                )}
            </div>

            {/* main value */}
            <h3 className="text-4xl font-bold text-gray-900 tracking-tight">
                {value}
            </h3>

            {/* subtitle + trend */}
            <div className="mt-1 flex flex-col gap-1">

                <p className="text-sm text-gray-400">
                    {subtitle}
                </p>

                {hasTrend && (
                    <div
                        className={`text-xs font-medium flex items-center gap-1 ${trendColor}`}
                    >
                        <TrendIcon className="w-4 h-4" />

                        <span>
                            {isStable
                                ? `Stable (${trend.value ?? "0.00"})`
                                : `${trendLabel}${
                                      trend.value
                                          ? ` (${trend.value})`
                                          : ""
                                  }`}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

export default MetricCard;