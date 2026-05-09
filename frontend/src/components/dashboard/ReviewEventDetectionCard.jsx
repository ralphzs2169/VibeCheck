import React from "react";
import { AlertTriangle, Activity, Zap, CheckCircle, Info, TrendingUp } from "lucide-react";
import { GraphIcon } from "../icons/AnalyticsIcons";

const STATUS_MAP = {
    true_event: { label: "Major Event Detected", style: "bg-red-50 text-red-700 border-red-100", Icon: AlertTriangle },
    sentiment_event: { label: "Sentiment Shift", style: "bg-orange-50 text-orange-700 border-orange-100", Icon: TrendingUp },
    activity_event: { label: "Activity Spike", style: "bg-blue-50 text-blue-700 border-blue-100", Icon: Activity },
    emerging_event: { label: "Emerging Pattern", style: "bg-amber-50 text-amber-700 border-amber-100", Icon: Zap },
    no_anomaly: { label: "Stable", style: "bg-green-50 text-green-700 border-green-100", Icon: CheckCircle },
    insufficient_data: { label: "Insufficient Data", style: "bg-gray-50 text-gray-700 border-gray-100", Icon: Info },
};

function Badge({ type }) {
    const key = STATUS_MAP[type] ? type : "insufficient_data";
    const { label, style, Icon } = STATUS_MAP[key];
    return (
        <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${style}`}>
            <div className="flex items-center gap-2">
                <Icon className="w-4 h-4" />
                <span>{label}</span>
            </div>
        </span>
    );
}

function MiniStat({ label, value }) {
    return (
        <div className="rounded-xl border border-gray-100 bg-white px-3 py-2 text-center">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-sm font-semibold text-gray-800">{value}</p>
        </div>
    );
}

export default function ReviewEventDetectionCard({ data = null, loading = false }) {
    // loading skeleton
    if (loading) {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-3" />
                <div className="h-4 bg-gray-200 rounded w-2/3 mb-6" />
                <div className="h-28 bg-gray-200 rounded mb-4" />
                <div className="flex gap-3">
                    <div className="h-12 bg-gray-200 rounded w-24" />
                    <div className="h-12 bg-gray-200 rounded w-24" />
                </div>
            </div>
        );
    }

    const payload = data || {};
    const eventType = payload.event_type || "insufficient_data";

    // empty / insufficient data state
    if (eventType === "insufficient_data") {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <div className="flex items-start justify-between mb-2">
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900">Customer Trend Events</h2>
                        <p className="text-xs text-gray-400 mt-0.5">Detect unusual shifts in customer sentiment and review activity</p>
                    </div>
                    <Badge type="insufficient_data" />
                </div>

                <div className="h-[220px] flex flex-col items-center justify-center gap-3 text-center">
                    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-300">
                        <GraphIcon className="w-6 h-6" />
                    </div>
                    <p className="font-medium text-gray-700">Not enough customer reviews yet to detect meaningful changes.</p>
                    <p className="text-sm text-gray-400">Collect more review periods to enable anomaly detection.</p>
                </div>
            </div>
        );
    }

    const confidence = typeof payload.confidence === "number" ? payload.confidence : 0;
    const interp = payload.interpretation || "No interpretation available.";
    const sentimentZ = payload?.z_scores?.sentiment_z;
    const volumeZ = payload?.z_scores?.volume_z;
    const baselineNote = payload?.baseline?.note;
    const meta = payload?.meta || {};

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">Customer Trend Events</h2>
                    <p className="text-xs text-gray-400 mt-0.5">Detect unusual shifts in customer sentiment and review activity</p>
                </div>
                <Badge type={eventType} />
            </div>

            {/* Confidence */}
            <div className="flex items-center gap-4 mb-4">
                <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-2">Detection Confidence</p>

                    <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                        <div
                            className={`h-full rounded-full ${confidence >= 70 ? "bg-blue-500" : confidence >= 40 ? "bg-amber-400" : "bg-gray-300"}`}
                            style={{ width: `${Math.max(0, Math.min(100, confidence))}%`, transition: "width 700ms ease" }}
                        />
                    </div>
                </div>

                <div className="w-20 text-right">
                    <p className="text-sm font-semibold text-gray-900">{Math.round(confidence)}%</p>
                    <p className="text-xs text-gray-400">confidence</p>
                </div>
            </div>

            {/* Interpretation / Insight */}
            <div className="rounded-xl border border-gray-100 bg-blue-50 p-3 mb-4">
                <p className="text-sm font-medium text-gray-900">Insight</p>
                <p className="text-xs text-gray-700 mt-1">{interp}</p>
            </div>

            {/* Technical signals */}
            <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-xl border border-gray-100 bg-white px-3 py-2">
                    <p className="text-xs text-gray-500">Sentiment Change</p>
                    <p className="text-sm font-semibold text-gray-800">{typeof sentimentZ === 'number' ? `${sentimentZ > 0 ? '+' : ''}${sentimentZ.toFixed(2)}σ` : '—'}</p>
                </div>

                <div className="rounded-xl border border-gray-100 bg-white px-3 py-2">
                    <p className="text-xs text-gray-500">Activity Change</p>
                    <p className="text-sm font-semibold text-gray-800">{typeof volumeZ === 'number' ? `${volumeZ > 0 ? '+' : ''}${volumeZ.toFixed(2)}σ` : '—'}</p>
                </div>
            </div>

            {/* Baseline note */}
            {baselineNote && (
                <p className="text-xs text-gray-400 mb-4">{baselineNote}</p>
            )}

            {/* Footer: reliability */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex items-center gap-3">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${meta?.is_reliable ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-amber-50 text-amber-700 border border-amber-100'}`}>
                        {meta?.is_reliable ? 'Reliable' : 'Low Data Confidence'}
                    </span>
                    <p className="text-xs text-gray-500">{(meta?.sample_size ?? 0)} review periods analyzed</p>
                </div>

                <div className="text-xs text-gray-400">&nbsp;</div>
            </div>
        </div>
    );
}
