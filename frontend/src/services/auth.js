import axios from "axios";

export const login = async (username, password) => {
  const response = await axios.post("/api/auth/login", {
    username,
    password,
  });

  return response.data;
};

export const register = async (data) => {
  const response = await axios.post("/api/auth/register", data);
  return response.data;
};

export const registerOwner = async (payload) => {
  const response = await axios.post("/api/auth/owner/register", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};
