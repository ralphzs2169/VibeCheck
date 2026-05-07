import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { getDashboard } from "../../services/api";
import OwnerSidebar from "./OwnerSidebar";

function BusinessLayout() {
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
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) return <div>Error: {error}</div>;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50 relative overflow-hidden">
      <div className="relative z-10 h-[calc(100vh-64px)] flex">
        <OwnerSidebar business={business} />
        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export default BusinessLayout;