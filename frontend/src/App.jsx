import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import BusinessProfile from "./pages/BusinessProfile";
import Navbar from "./components/Navbar.jsx";
import OwnerRegister from "./pages/OwnerRegister.jsx";
import BusinessDashboard from "./pages/business/BusinessDashboard.jsx";
import RoleProtectedRoute from "./components/security/RoleProtectedRoute.jsx";
import GuestRoute from "./components/security/GuestRoute.jsx";

function App() {
  return (
    <>
      <Navbar />

      <Routes>
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
          path="/business/dashboard" 
          element={
            <RoleProtectedRoute allowedRoles={["owner"]} requireAuth={true}>
              <BusinessDashboard />
            </RoleProtectedRoute>
          } />
      </Routes>

    </>
  );
}

export default App;