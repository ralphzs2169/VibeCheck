import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import BusinessProfile from "./pages/BusinessProfile";
import Navbar from "./components/Navbar.jsx";
import OwnerRegister from "./pages/OwnerRegister.jsx";
import BusinessLayout from "./components/business_owner/BusinessLayout.jsx";
import BusinessDashboard from "./pages/business_owner/BusinessDashboard.jsx";
import BusinessProfileManagement from "./pages/business_owner/BusinessProfileManagement.jsx";
import BusinessReviews from "./pages/business_owner/BusinessReviews.jsx";
import RoleProtectedRoute from "./components/security/RoleProtectedRoute.jsx";
import GuestRoute from "./components/security/GuestRoute.jsx";
import BusinessAnalytics from "./pages/business_owner/BusinessAnalytics.jsx";
import ResortsDiscovery from "./pages/ResortsDiscovery";
import NotFound from "./pages/NotFound";
import ServerError from "./pages/ServerError";


function ScrollManager() {
  const location = useLocation();

  useEffect(() => {
    const targetId = location.hash.replace("#", "");

    if (!targetId) {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      return;
    }

    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [location.pathname, location.hash]);

  return null;
}

function App() {
  return (
    <>
      <ScrollManager />
      <Navbar />

      <Routes>
        {/* Error pages - checked first, bypass all protection */}
        <Route path="/500" element={<ServerError />} />

        <Route 
          path="/" element={
           <RoleProtectedRoute notAllowedRoles={["owner"]} requireAuth={false}>
              <Home />
            </RoleProtectedRoute>
          } />

        <Route
          path="/login"
          element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          }
        />

        <Route
          path="/register"
          element={
            <GuestRoute>
              <Register />
            </GuestRoute>
          }
        />

        <Route 
          path="/register-business" 
          element={
            <GuestRoute >
              <OwnerRegister />
            </GuestRoute>
          } />

        <Route 
          path="/business/:id" 
          element={
            <RoleProtectedRoute notAllowedRoles={["owner"]} requireAuth={false}>
              <BusinessProfile />
            </RoleProtectedRoute>
          } />

        <Route
          path="/businesses"
          element={
            <RoleProtectedRoute notAllowedRoles={["owner"]} requireAuth={false}>
              <ResortsDiscovery />
            </RoleProtectedRoute>
          }
        />

        <Route path="/business" element={<RoleProtectedRoute allowedRoles={["owner"]}><BusinessLayout /></RoleProtectedRoute>}>
          <Route path="dashboard" element={<BusinessDashboard />} />
          <Route path="profile-management" element={<BusinessProfileManagement />} />
          <Route path="reviews" element={<BusinessReviews />} />
          <Route path="analytics" element={<BusinessAnalytics />} />
        </Route>

        {/* Catch-all route for 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>



    </>
  );
}

export default App;