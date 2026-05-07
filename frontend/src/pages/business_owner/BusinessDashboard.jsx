import { getDashboard } from "../../services/api";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import MetricCard from "../../components/dashboard/MetricCard";
import VibeChart from "../../components/dashboard/VibeChart";
import AspectAnalytics from "../../components/dashboard/AspectAnalytics";
import SentimentChart from "../../components/dashboard/SentimentChart";
import SentimentPieChart from "../../components/dashboard/SentimentPieChart";
import VibeForecastChart from "../../components/dashboard/VibeForecastChart";
import ReviewCard from "../../components/business_profile/ReviewCard";
import HealthGauge from "../../components/dashboard/HealthGauge";

function BusinessDashboard() {
    const [business, setBusiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const dashboardData = await getDashboard();

                setBusiness(dashboardData);

            } catch (err) {
                setError(err.message || "Something went wrong");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004687] mx-auto mb-4" />
                    <p className="text-gray-500 text-sm">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="bg-white rounded-2xl border border-red-100 p-8 text-center max-w-sm">
                    <p className="text-red-500 font-medium">
                        Failed to load dashboard
                    </p>
                    <p className="text-gray-400 text-sm mt-1">{error}</p>
                </div>
            </div>
        );
    }

    // Safe defaults
    const vibe = business?.vibe || {};
    const vibe_ui = business?.vibe_ui || { type: "new", ui_label: "New" };
    const spike = business?.spike_analysis || {};
    const vibeChart = business?.vibe_chart || {};
    const aspects = business?.aspects || [];
    const business_health = business?.business_health || {};

    const sentimentOverTime = business?.get_sentiment_over_time || {};
    const forecastSentiment = business?.forecast_vibe || business?.forecast_sentiment || {};

    const sentimentDistribution = business?.get_sentiment_distribution?.distribution || {};

    const vibeTrend = business?.vibe_score_trend || {};

    const trendLabel =
        vibeTrend.trend === "improving"
            ? "Improving"
            : vibeTrend.trend === "declining"
            ? "Declining"
            : "Stable";

    const trendValue =
    vibeTrend.slope !== undefined && vibeTrend.slope !== null
        ? vibeTrend.slope.toFixed(2)
        : null;

    // For vibe trend tooltip and empty states
    const vibeMinRequired = vibeTrend?.meta?.min_required ?? 7;
    let vibeSubtitle = "";

    // Determine subtitle based on vibe status and review count
    if (business.review_count < vibeMinRequired) {
        vibeSubtitle = "Not enough reviews yet";
    } 
    else if (vibe?.status === "no_data" || vibe?.vibe_score == null) {
        vibeSubtitle = "Processing vibe analysis...";
    } 
    else if (vibe.reviews_analyzed > 0) {
        vibeSubtitle = `${vibe.reviews_analyzed} reviews analyzed`;
    } 
    else {
        vibeSubtitle = "Analyzing reviews...";
    }

    const isReliable = spike?.meta?.is_reliable;

    // derive UI label and type for spike card based on spike analysis
    //  event type and reliability
    const getSpikeUI = () => {
        const isReliable = spike?.meta?.is_reliable;

        // 1. FIRST CHECK: data quality
        if (!isReliable || spike?.event_type === "insufficient_data") {
            return {
                label: "Building insights",
                subtitle: "Not enough data yet",
                type: "new"
            };
        }

        // 2. THEN interpret signal
        switch (spike.event_type) {
            case "true_event":
                return {
                    label: "Spike Detected",
                    subtitle: `Strong activity (${spike.confidence}%)`,
                    type: "alert"
                };

            case "volume_only_spike":
                return {
                    label: "Activity Spike",
                    subtitle: "Unusual review volume detected",
                    type: "warning"
                };

            case "sentiment_only_spike":
                return {
                    label: "Sentiment Shift",
                    subtitle: "Emotional change detected",
                    type: "warning"
                };

            case "no_anomaly":
            default:
                return {
                    label: "Stable",
                    subtitle: "No significant activity",
                    type: "stable"
                };
        }
    };

    const spikeUi = getSpikeUI();

    return (
        <div className="min-h-screen bg-[#f8f9fb] px-6 py-8">
            <div className="max-w-7xl mx-auto space-y-6">

                <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)] gap-4 items-start">
                    <div className="space-y-4 min-w-0">
                        {/* Metric Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">

                            {/* VIBE SCORE */}
                            <MetricCard
                               label="Vibe Score"
                               value={
                                    vibe.vibe_score != null
                                        ? vibe.vibe_score.toFixed(1)
                                        : "--"
                                }
                                subtitle={vibeSubtitle}
                                badge={{
                                    type: vibe_ui.type,
                                    label: vibe_ui.ui_label
                                }}
                               trend={
                                    vibeTrend?.trend
                                        ? {
                                            direction: vibeTrend.trend,
                                            value: trendValue
                                        }
                                        : null
                                }
                                vibeStatus={vibe?.status}
                            />

                            {/* TOTAL REVIEWS */}
                            <MetricCard
                                label="Total Reviews"
                                value={business.review_count || 0}
                                subtitle="All-time reviews collected"
                            />

                        </div>

                        <VibeChart
                            data={vibeChart}
                            vibeOverTime={business?.vibe_over_time || []}
                        />
                    </div>

                    <div className="space-y-4 min-w-0">
                        <HealthGauge data={business_health} />

                        <AspectAnalytics
                            aspects={aspects}
                            onViewAll={() => {}}
                        />
                    </div>
                </div>

                <div className="flex flex-col xl:flex-row gap-4 items-start">

                    {/* PIE - 30% */}
                    <div className="w-full xl:w-[35%]">
                        <SentimentPieChart
                            distribution={sentimentDistribution}
                        />
                    </div>

                    {/* LINE - 70% */}
                    <div className="w-full xl:w-[65%]">
                        <SentimentChart
                            data={sentimentOverTime.data || []}
                            meta={sentimentOverTime.meta || {}}
                        />
                    </div>

                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
                    <VibeForecastChart data={forecastSentiment} />

                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 h-[480px] flex flex-col">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">Latest Reviews</h3>
                                <p className="text-xs text-gray-500">Recent guest feedback — preview of newest reviews</p>
                            </div>

                            <div className="flex items-center gap-1">

                                <button
                                    onClick={() => navigate('/business/reviews')}
                                    className="text-sm bg-[#004687] hover:bg-[#003f66] text-white px-3 py-1.5 rounded-md"
                                >
                                    View More reviews
                                </button>
                            </div>
                        </div>

                        <div className="divide-y divide-gray-100 flex-1 overflow-y-auto min-h-0">
                            {(() => {
                                const latestReviews = business?.latest_reviews || [];

                                if (latestReviews.length === 0) {
                                    return (
                                        <div className="p-12 text-center">
                                          
                                            <>
                                                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                                                </svg>
                                                <h3 className="text-lg font-semibold text-gray-900 mb-2">No reviews yet</h3>
                                                <p className="text-gray-600">This business doesn't have any reviews yet.</p>
                                            </>
                                            
                                        </div>
                                    );
                                }

                                return latestReviews.slice(0, 5).map((review) => (
                                    <div key={review.id} className="px-4 py-2">
                                        <ReviewCard review={review} compact />
                                    </div>
                                ));
                            })()}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}

export default BusinessDashboard;