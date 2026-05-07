import { Navigate } from "react-router-dom";

function GuestRoute({ children }) {
  const token = localStorage.getItem("token");
  const userData = localStorage.getItem("user");

  if (token && userData) {
    const user = JSON.parse(userData);

    // If user is authenticated, redirect based on role
    if (user?.role === "owner") {
      return <Navigate to={`/business/${user.business_id}/dashboard`} replace />;
    }

    return <Navigate to="/" replace />;
  }

  return children;
}

export default GuestRoute;