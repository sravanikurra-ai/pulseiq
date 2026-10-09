import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Layout from "./components/Layout";
import Anomalies from "./pages/Anomalies";
import Forecasts from "./pages/Forecasts";
import Assistant from "./pages/Assistant";

function ProtectedRoute({ children }) {
  const { isAuthenticated, checked } = useAuth();
  if (!checked) return <div className="min-h-screen bg-ink-950" />;
  return isAuthenticated ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
  path="/anomalies"
  element={
    <ProtectedRoute>
      <Layout>
        <Anomalies />
      </Layout>
    </ProtectedRoute>
  }
/>
<Route
  path="/forecasts"
  element={
    <ProtectedRoute>
      <Layout>
        <Forecasts />
      </Layout>
    </ProtectedRoute>
  }
/>
<Route
  path="/assistant"
  element={
    <ProtectedRoute>
      <Layout>
        <Assistant />
      </Layout>
    </ProtectedRoute>
  }
/>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}