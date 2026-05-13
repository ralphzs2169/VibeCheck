import axios from "axios";

export const BASE_URL = "http://localhost:8000";

export const getBusiness = async (id) => {
  const response = await axios.get(`/api/businesses/${id}/dashboard`);
  return response.data;
};

export const getDashboard = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`/api/business/dashboard`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getBusinessReviewsPage = async ({
  offset = 0,
  limit = 20,
  includeKeywords = true,
} = {}) => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`/api/business/reviews`, {
    params: {
      offset,
      limit,
      include_keywords: includeKeywords,
    },
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getAnalytics = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`/api/business/analytics`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const updateBusinessProfile = async (payload) => {
  const token = localStorage.getItem("token");
  const response = await axios.patch("/api/businesses/profile", payload, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return response.data;
};

export const updateReview = async (reviewId, payload) => {
  const token = localStorage.getItem("token");
  const response = await axios.patch(`/api/reviews/${reviewId}`, payload, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return response.data;
};

export const deleteReview = async (reviewId) => {
  const token = localStorage.getItem("token");
  await axios.delete(`/api/reviews/${reviewId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};
