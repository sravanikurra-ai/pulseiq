import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function Placeholder() {
  const { logout } = useAuth();
  return (
    <div className="min-h-screen bg-ink-950 text-ink-50 p-8">
      <h1 className="text-2xl font-semibold mb-2">PulseIQ Dashboard</h1>
      <p className="text-ink-400 mb-6">Logged in successfully. Dashboard content coming in the next stage.</p>
      <button
        onClick={logout}
        className="rounded-lg border border-ink-600 px-4 py-2 text-sm hover:bg-ink-800 transition"
      >
        Log Out
      </button>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Placeholder /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}