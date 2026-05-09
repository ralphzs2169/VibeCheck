import { useEffect, useState } from "react";
import { getDashboard, getAnalytics } from "../../services/api";

import HealthDiagnostic from "../../components/analytics/HealthDiagnostic";
import ExecutiveSummary from "../../components/analytics/ExecutiveSummary";
import PrimaryRiskDriver from "../../components/dashboard/PrimaryRiskDriver";
import NegativeSignals from "../../components/dashboard/NegativeSignals";
import PositiveDrivers from "../../components/dashboard/PositiveDrivers";
import AspectIntelligenceGrid from "../../components/dashboard/AspectIntelligenceGrid";
import FrequentAspectAnalysis from "../../components/dashboard/FrequentAspectAnalysis";
import ReviewEventDetectionCard from "../../components/dashboard/ReviewEventDetectionCard";
import PeakDropAnalysisCard from "../../components/dashboard/PeakDropAnalysisCard";
import BusinessStabilityCard from "../../components/dashboard/BusinessStabilityCard";

function BusinessAnalytics() {
    const [business, setBusiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const analyticsData = await getAnalytics();
                setBusiness(analyticsData);
            } catch (err) {
                setError(err.message);
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
                    <p className="text-gray-600">Loading business analytics...</p>
                </div>
            </div>
        );
    }

    if (error) return <div>Error: {error}</div>;

    return (
        <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

            {/* HEADER */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">
                    Business Analytics
                </h1>
                <p className="mt-2 text-gray-600">
                    View analytics and insights for your business.
                </p>
            </div>

            {/* EXECUTIVE SUMMARY */}
            <ExecutiveSummary dashboard={business || {}} loading={loading} />

            {/* TOP: HEALTH */}
            <HealthDiagnostic data={business?.business_health || {}} />

            {/* MIDDLE GRID: CORE DRIVERS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <PrimaryRiskDriver
                    data={business?.primary_risk_driver || {}}
                />

                <NegativeSignals
                    data={business?.negative_signals || {}}
                />

                <PositiveDrivers
                    data={business?.positive_drivers || {}}
                />
            </div>

            {/* FREQUENT ASPECT ANALYSIS */}
            <FrequentAspectAnalysis
                data={business?.frequent_aspect_mining || {}}
            />

            {/* REVIEW EVENT DETECTION */}
            <ReviewEventDetectionCard
                data={business?.review_event_detection || {}}
            />

            {/* PEAK & DROP ANALYSIS */}
            <PeakDropAnalysisCard
                data={business?.peak_and_drop || {}}
            />

            {/* BUSINESS STABILITY */}
            <BusinessStabilityCard
                vibe={business?.vibe_volatility || {}}
                sentiment={business?.sentiment_volatility || {}}
            />

            {/* ASPECT INTELLIGENCE */}
            <AspectIntelligenceGrid
                data={business?.aspect_intelligence || []}
            />

        </div>
    );
}

export default BusinessAnalytics;