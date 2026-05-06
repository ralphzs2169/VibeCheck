import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import BusinessProfile from "./pages/BusinessProfile";
import Navbar from "./components/Navbar.jsx";
import OwnerRegister from "./pages/OwnerRegister.jsx";

function App() {
  return (
    <>
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/resort/:id" element={<BusinessProfile />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/register-business" element={<OwnerRegister />} />
      </Routes>

    </>
  );
}

export default App;