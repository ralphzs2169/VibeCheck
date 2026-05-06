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
