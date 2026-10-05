import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
  withCredentials: true,
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    // /auth/me returning 401 just means "not logged in" — a normal,
    // expected outcome when checking auth status on page load. Redirecting
    // here would reload the page, remount the app, re-check /auth/me, get
    // 401 again, and redirect again — an infinite loop. Only redirect on
    // 401s from OTHER endpoints, where it means a session expired mid-use.
    const isAuthCheck = error.config && error.config.url === "/auth/me";
    if (error.response && error.response.status === 401 && !isAuthCheck) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default client;