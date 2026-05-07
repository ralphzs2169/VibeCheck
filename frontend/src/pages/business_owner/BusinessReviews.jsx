import { useEffect, useState } from "react";
import { getDashboard } from "../../services/api";
import OwnerSidebar from "../../components/business_owner/OwnerSidebar";

function BusinessReviews() {
    const [business, setBusiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const dashboardData = await getDashboard();
                setBusiness(dashboardData.profile);
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
                    <p className="text-gray-600">Loading reviews...</p>
                </div>
            </div>
        );
    }

    if (error) return <div>Error: {error}</div>;

    return (
        <div className="max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900 mb-6">Business Reviews</h1>
            <p className="text-gray-700 mb-4">View and manage reviews for your business.</p>
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">Recent Reviews</h2>
                <p className="text-gray-700">List of reviews (Placeholder)</p>
            </div>
        </div>
    );
}

export default BusinessReviews;