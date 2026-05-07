import { getDashboard } from "../../services/api";
import { useEffect, useState } from "react";
function BusinessDashboard() {
    const [business, setBusiness] = useState(null);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const dashboardData = await getDashboard();
                setBusiness(dashboardData.profile);

                const userData = JSON.parse(localStorage.getItem("user"));
                setUser(userData);
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
                    <p className="text-gray-600">Loading business dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) return <div>Error: {error}</div>;

    return (
        <div className="min-h-screen bg-gray-100">
            <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">Business Dashboard</h1>
                <p className="text-gray-700 mb-4">Welcome to your {business?.name || "Business"} dashboard! Here you can view insights and manage your business profile.</p>
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-2xl font-semibold text-gray-900 mb-4">Your Business Insights</h2>
                    <p className="text-gray-700 mb-6">Here you can see an overview of your business performance, including sentiment analysis, review trends, and more.</p>
                    <button className="px-4 py-2 bg-[#004687] text-white rounded-lg font-medium hover:bg-blue-800 transition shadow-sm">
                        View Detailed Insights
                    </button>
                </div>
            </div>
        </div>
    );
}

export default BusinessDashboard;