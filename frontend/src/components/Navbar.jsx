import { Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import Home from "./icons/Home";
import Services from "./icons/Services";
import About from "./icons/About";
import Login from "./icons/Login";
import Register from "./icons/Register";
import Logout from "./icons/Logout";

function Navbar() {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem("token");
    setIsAuthenticated(!!token);
  }, []);

  const isLoginPage = location.pathname === "/login";
  const isRegisterPage = location.pathname === "/register";

  return (
    <>
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 w-full flex items-center justify-between px-6 md:px-12 py-4 bg-white border-b border-gray-100 shadow-sm z-50">
        {/* LEFT: Brand */}
        <Link to="/" className="text-2xl font-bold text-[#004687] hover:opacity-80 transition">
          VibeCheck
        </Link>

        {/* MIDDLE: Navigation Links */}
        <div className="hidden md:flex gap-10 items-center">
          <Link 
            to="/" 
            className="flex items-center gap-2 text-gray-700 font-medium hover:text-[#004687] transition group"
          >
            <Home className="w-5 h-5 group-hover:text-[#004687]" />
            Home
          </Link>
          <Link 
            to="/services" 
            className="flex items-center gap-2 text-gray-700 font-medium hover:text-[#004687] transition group"
          >
            <Services className="w-5 h-5 group-hover:text-[#004687]" />
            Services
          </Link>
          <Link 
            to="/about" 
            className="flex items-center gap-2 text-gray-700 font-medium hover:text-[#004687] transition group"
          >
            <About className="w-5 h-5 group-hover:text-[#004687]" />
            About
          </Link>
        </div>

        {/* RIGHT: Auth Links */}
        <div className="flex gap-3 items-center">
          {!isAuthenticated && !isLoginPage && (
            <Link
              to="/login"
              className="px-5 py-2 text-sm font-medium text-[#004687] border border-[#004687] rounded hover:bg-[#f0f7ff] transition group flex items-center gap-2"
            >
              <Login className="w-4 h-4" />
              Login
            </Link>
          )}

          {!isAuthenticated && !isRegisterPage && (
            <Link
              to="/register"
              className="px-6 py-2 text-sm font-bold bg-[#004687] text-white rounded hover:bg-[#003560] shadow-sm hover:shadow-md transition group flex items-center gap-2"
            >
              <Register className="w-4 h-4" />
              Register
            </Link>
          )}

          {isAuthenticated && (
            <button
              onClick={() => {
                localStorage.removeItem("token");
                setIsAuthenticated(false);
                window.location.href = "/";
              }}
              className="px-5 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50 hover:border-gray-400 transition group flex items-center gap-2"
            >
              <Logout className="w-4 h-4" />
              Logout
            </button>
          )}
        </div>
      </nav>

      {/* Spacer to prevent content overlap */}
      <div className="h-16" />
    </>
  );
}

export default Navbar;