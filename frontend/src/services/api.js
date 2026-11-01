import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const getDashboardData = async () => {
  const response = await api.get("/dashboard");
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export default api;
// Fetch Root Cause Analysis results
export const getRootCauses = async () => {
  try {
    const response = await api.get("/root-causes");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch root cause results:", error);
    throw error;
  }
};