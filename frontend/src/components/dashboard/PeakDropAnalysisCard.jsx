import React from "react";
import { TrendingUp, TrendingDown, CalendarDays } from "lucide-react";

function formatSentiment(val) {
    if (typeof val !== "number") return "—";
    return `${val >= 0 ? "+" : ""}${val.toFixed(2)}`;
}

export default function PeakDropAnalysisCard({ data = null, loading = false }) {
    if (loading) {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-3" />
                <div className="h-4 bg-gray-200 rounded w-2/3 mb-6" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div className="h-36 bg-gray-200 rounded" />
                    <div className="h-36 bg-gray-200 rounded" />
                </div>
                <div className="h-8 bg-gray-200 rounded w-1/4" />
            </div>
        );
    }

    const payload = data || {};
    const peak = payload.peak || null;
    const drop = payload.drop || null;
    const meta = payload.meta || {};

    // empty state
    if (!peak && !drop) {
        return (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <div className="flex items-start justify-between mb-2">
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900">Peak & Drop Analysis</h2>
                        <p className="text-xs text-gray-400 mt-0.5">Track the biggest changes in customer sentiment over time</p>
                    </div>
                </div>

                <div className="h-[180px] flex flex-col items-center justify-center gap-3 text-center">
                    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-300">
                        <CalendarDays className="w-6 h-6" />
                    </div>
                    <p className="font-medium text-gray-700">Not enough review history yet to detect meaningful sentiment shifts.</p>
                    <p className="text-sm text-gray-400">Collect more review periods to enable this analysis.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">Peak & Drop Analysis</h2>
                    <p className="text-xs text-gray-400 mt-0.5">Track the biggest changes in customer sentiment over time</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {/* Positive shift */}
                <div className="rounded-xl border border-gray-100 bg-green-50 p-4">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-xs text-green-700 font-semibold">Biggest Positive Shift</p>
                            <p className="text-sm text-gray-800 font-medium mt-2">{peak?.date || '—'}</p>
                        </div>
                        <div className="flex items-center gap-2 text-green-700">
                            <TrendingUp className="w-6 h-6" />
                        </div>
                    </div>

                    <div className="mt-3">
                        <p className="text-2xl font-semibold text-green-800">{formatSentiment(peak?.change)} sentiment</p>
                        <p className="text-xs text-gray-500 mt-1">{peak?.review_count ?? 0} reviews</p>
                        {peak?.change >= 0 && (
                            <p className="text-xs text-green-700 mt-2">Strong improvement in customer feedback</p>
                        )}
                    </div>

                    <div className="mt-4">
                        <button className="text-sm text-green-700 border border-green-100 bg-white rounded-md px-3 py-1 hover:bg-green-50">Inspect reviews from this day</button>
                    </div>
                </div>

                {/* Negative shift */}
                <div className="rounded-xl border border-gray-100 bg-red-50 p-4">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-xs text-red-700 font-semibold">Biggest Negative Shift</p>
                            <p className="text-sm text-gray-800 font-medium mt-2">{drop?.date || '—'}</p>
                        </div>
                        <div className="flex items-center gap-2 text-red-700">
                            <TrendingDown className="w-6 h-6" />
                        </div>
                    </div>

                    <div className="mt-3">
                        <p className="text-2xl font-semibold text-red-800">{formatSentiment(drop?.change)} sentiment</p>
                        <p className="text-xs text-gray-500 mt-1">{drop?.review_count ?? 0} reviews</p>
                        {drop?.change < 0 && (
                            <p className="text-xs text-red-700 mt-2">Largest drop in customer sentiment detected</p>
                        )}
                    </div>

                    <div className="mt-4">
                        <button className="text-sm text-red-700 border border-red-100 bg-white rounded-md px-3 py-1 hover:bg-red-50">Inspect reviews from this day</button>
                    </div>
                </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex items-center gap-3">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${meta?.is_reliable ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-amber-50 text-amber-700 border border-amber-100'}`}>
                        {meta?.is_reliable ? 'Reliable' : 'Low Data Confidence'}
                    </span>
                    <p className="text-xs text-gray-500">{meta?.sample_size ?? 0} review periods analyzed</p>
                </div>
            </div>
        </div>
    );
}
