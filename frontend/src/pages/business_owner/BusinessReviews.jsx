import { useEffect, useMemo, useState } from "react";
import { getDashboard } from "../../services/api";
import VibeSummaryCard from "../../components/business_profile/VibeSummaryCard";
import ReviewCard from "../../components/business_profile/ReviewCard";
import { Smile, Frown, Search, Filter, SlidersHorizontal } from "lucide-react";

function BusinessReviews() {
    const [business, setBusiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Filters / search
    const [query, setQuery] = useState("");
    const [sentimentFilter, setSentimentFilter] = useState("all");
    const [ratingMin, setRatingMin] = useState(0);
    const [ratingMax, setRatingMax] = useState(5);
    const [aspectFilter, setAspectFilter] = useState("");
    const [sortOrder, setSortOrder] = useState("newest");

    useEffect(() => {
        const fetchData = async () => {
            try {
                const dashboardData = await getDashboard();
                // getDashboard returns a dashboard object similar to BusinessDashboard
                setBusiness(dashboardData);
            } catch (err) {
                setError(err.message || "Failed to load dashboard");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Ensure reviews page starts at the top when navigated to
    useEffect(() => {
        try {
            window.scrollTo({ top: 0, left: 0, behavior: "auto" });
        } catch (e) {
            // noop in non-browser contexts
        }
    }, []);

    // Derived data and memoized computations (must run before any early returns)
    const reviews = business?.all_reviews || business?.latest_reviews || [];

    // Build list of aspect options from available aspect_frequency
    const aspectOptions = (business?.aspect_frequency?.aspects || []).map(a => a.term);

    // Compute keyword insights
    const positiveKeywords = useMemo(() => {
        // Prefer explicit positive drivers if present
        if (business?.positive_drivers && Array.isArray(business.positive_drivers)) return business.positive_drivers;
        if (business?.positive_drivers?.driver) return [{ term: business.positive_drivers.driver, score: business.positive_drivers.score }];
        // fallback to top aspects
        return (business?.aspect_frequency?.aspects || []).slice(0, 6).map(a => ({ term: a.term, score: a.count }));
    }, [business]);

    const negativeKeywords = useMemo(() => {
        if (business?.negative_drivers && Array.isArray(business.negative_drivers)) return business.negative_drivers;
        if (business?.negative_drivers?.driver) return [{ term: business.negative_drivers.driver, score: business.negative_drivers.score }];
        // fallback: empty or lowest-count aspects
        const aspects = business?.aspect_frequency?.aspects || [];
        return aspects.slice(-6).reverse().map(a => ({ term: a.term, score: a.count }));
    }, [business]);

    // Filtered reviews
    const filteredReviews = useMemo(() => {
        let list = reviews || [];
        if (query && query.trim().length > 0) {
            const q = query.toLowerCase();
            list = list.filter(r => (
                (r.content || "").toLowerCase().includes(q) ||
                (r.user?.firstname || "").toLowerCase().includes(q) ||
                (r.user?.lastname || "").toLowerCase().includes(q)
            ));
        }

        if (sentimentFilter !== "all") {
            list = list.filter(r => (r.sentiment_label || "neutral").toLowerCase() === sentimentFilter);
        }

        if (aspectFilter) {
            list = list.filter(r => (r.aspect_sentiments || []).some(a => a.aspect === aspectFilter));
        }

        list = list.filter(r => (r.rating || 0) >= ratingMin && (r.rating || 0) <= ratingMax);

        list = list.sort((a, b) => {
            const ta = new Date(a.created_at).getTime();
            const tb = new Date(b.created_at).getTime();
            return sortOrder === "newest" ? tb - ta : ta - tb;
        });

        return list;
    }, [reviews, query, sentimentFilter, ratingMin, ratingMax, aspectFilter, sortOrder]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004687] mx-auto mb-4" />
                    <p className="text-gray-600">Loading customer reviews...</p>
                </div>
            </div>
        );
    }

    if (error) return <div className="p-6 text-red-600">Error: {error}</div>;

    return (
        <div className="px-6 py-8">
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Customer Reviews</h1>
                        <p className="text-gray-600">Insights and raw reviews to help you act fast.</p>
                    </div>
                </div>

                {/* TOP TWO-COLUMN: Vibe Summary + Keyword Insights */}
                <div className="grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-4">
                    <div>
                        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                            <VibeSummaryCard
                                summary={business?.vibe_summary || business?.summary}
                                reviewCount={business?.review_count}
                            />
                        </div>
                    </div>

                    <aside>
                        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">Keyword Insights</h3>
                                <div className="text-sm text-gray-500">At-a-glance</div>
                            </div>

                            <div className="grid grid-cols-1 gap-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="p-2 rounded-md bg-green-50 text-green-700">
                                            <Smile className="w-4 h-4" />
                                        </div>
                                        <h4 className="font-semibold">Top Positive Keywords</h4>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {positiveKeywords.length === 0 && (
                                            <div className="text-sm text-gray-400">No positive keywords available</div>
                                        )}
                                        {positiveKeywords.map((k, idx) => (
                                            <div key={idx} className="inline-flex items-center gap-2 bg-green-50 text-green-800 px-3 py-1.5 rounded-full text-sm">
                                                <span className="font-medium">{k.term}</span>
                                                {k.score != null && (
                                                    <span className="text-xs text-green-700 opacity-80">{k.score}</span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="p-2 rounded-md bg-red-50 text-red-700">
                                            <Frown className="w-4 h-4" />
                                        </div>
                                        <h4 className="font-semibold">Top Negative Keywords</h4>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {negativeKeywords.length === 0 && (
                                            <div className="text-sm text-gray-400">No negative keywords available</div>
                                        )}
                                        {negativeKeywords.map((k, idx) => (
                                            <div key={idx} className="inline-flex items-center gap-2 bg-red-50 text-red-800 px-3 py-1.5 rounded-full text-sm">
                                                <span className="font-medium">{k.term}</span>
                                                {k.score != null && (
                                                    <span className="text-xs text-red-700 opacity-80">{k.score}</span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </aside>
                </div>

                {/* SEARCH / FILTER BAR */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
                    <div className="flex flex-col md:flex-row md:items-center md:gap-4">
                        <div className="flex-1 flex items-center gap-3">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                                <input
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Search reviews, user, or content"
                                    className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-2 mt-3 md:mt-0">
                            <div className="flex items-center gap-2">
                                <Filter className="w-4 h-4 text-gray-500" />
                                <select value={sentimentFilter} onChange={(e) => setSentimentFilter(e.target.value)} className="border border-gray-200 rounded-md px-2 py-1 text-sm">
                                    <option value="all">All Sentiments</option>
                                    <option value="positive">Positive</option>
                                    <option value="neutral">Neutral</option>
                                    <option value="negative">Negative</option>
                                </select>
                            </div>

                            <div className="flex items-center gap-2">
                                <SlidersHorizontal className="w-4 h-4 text-gray-500" />
                                <div className="flex items-center gap-2">
                                    <input type="number" value={ratingMin} min={0} max={5} onChange={(e) => setRatingMin(Number(e.target.value))} className="w-16 border border-gray-200 rounded-md px-2 py-1 text-sm" />
                                    <span className="text-sm text-gray-400">to</span>
                                    <input type="number" value={ratingMax} min={0} max={5} onChange={(e) => setRatingMax(Number(e.target.value))} className="w-16 border border-gray-200 rounded-md px-2 py-1 text-sm" />
                                </div>
                            </div>

                            <div className="hidden md:block">
                                <select value={aspectFilter} onChange={(e) => setAspectFilter(e.target.value)} className="border border-gray-200 rounded-md px-2 py-1 text-sm">
                                    <option value="">All aspects</option>
                                    {aspectOptions.map((a, i) => (
                                        <option key={i} value={a}>{a}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} className="border border-gray-200 rounded-md px-2 py-1 text-sm">
                                    <option value="newest">Newest</option>
                                    <option value="oldest">Oldest</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* REVIEWS LIST */}
                <div className="grid grid-cols-1 gap-4">
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                        <h3 className="text-lg font-semibold mb-4">Reviews ({filteredReviews.length})</h3>

                        {filteredReviews.length === 0 ? (
                            <div className="text-gray-500">No reviews match your filters.</div>
                        ) : (
                            <div className="flex flex-col gap-4">
                                {filteredReviews.map((r) => (
                                    <ReviewCard key={r.id} review={r} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}

export default BusinessReviews;