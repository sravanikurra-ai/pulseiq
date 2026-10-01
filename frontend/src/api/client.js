import axios from "axios";

const client = axios.create({ baseURL: "http://127.0.0.1:8000" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("pulseiq_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("pulseiq_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default client;