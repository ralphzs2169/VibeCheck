import { NavLink } from "react-router-dom";

function OwnerSidebar({ business }) {
  return (
    <div className="w-60 bg-white shadow-lg p-6 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{business?.name || "Business"}</h2>
        <p className="text-gray-600">{business?.location || "Location"}</p>
        <p className="text-gray-500 text-sm mt-1">{business?.short_description || "Description"}</p>
      </div>

      <nav className="space-y-2">
        <NavLink
          to="/business/dashboard"
          className={({ isActive }) =>
            `block px-4 py-2 rounded-lg transition ${
              isActive
                ? "bg-[#004687] text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`
          }
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/business/profile-management"
          className={({ isActive }) =>
            `block px-4 py-2 rounded-lg transition ${
              isActive
                ? "bg-[#004687] text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`
          }
        >
          Profile Management
        </NavLink>
        <NavLink
          to="/business/reviews"
          className={({ isActive }) =>
            `block px-4 py-2 rounded-lg transition ${
              isActive
                ? "bg-[#004687] text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`
          }
        >
          Reviews
        </NavLink>
         <NavLink
          to="/business/analytics"
          className={({ isActive }) =>
            `block px-4 py-2 rounded-lg transition ${
              isActive
                ? "bg-[#004687] text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`
          }
        >
          Analytics
        </NavLink>
      </nav>
    </div>
  );
}

export default OwnerSidebar;