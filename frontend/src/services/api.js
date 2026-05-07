import axios from "axios";

export const BASE_URL = "http://localhost:8000";

export const getBusiness = async (id) => {
  const response = await axios.get(`/api/businesses/${id}/dashboard`);
  return response.data;
};

export const getDashboard = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`/api/businesses/dashboard`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};
