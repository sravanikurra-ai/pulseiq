import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="p-2 rounded-lg bg-signal-actual/10">
            <Activity className="w-5 h-5 text-signal-actual" strokeWidth={2.5} />
          </div>
          <span className="text-lg font-semibold tracking-tight text-ink-50">PulseIQ</span>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-ink-900 border border-ink-700 rounded-2xl p-8 shadow-2xl shadow-black/40"
        >
          <h1 className="text-xl font-semibold text-ink-50 mb-1">Welcome back</h1>
          <p className="text-sm text-ink-400 mb-6">Sign in to your analytics workspace.</p>

          {error && (
            <div className="mb-4 rounded-lg border border-signal-anomaly/30 bg-signal-anomaly/10 px-3 py-2 text-sm text-signal-anomaly">
              {error}
            </div>
          )}

          <label className="block text-xs font-medium text-ink-400 mb-1.5">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full mb-4 rounded-lg bg-ink-800 border border-ink-600 px-3 py-2.5 text-sm text-ink-50 placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-signal-actual/50 focus:border-signal-actual transition"
            placeholder="you@company.com"
          />

          <label className="block text-xs font-medium text-ink-400 mb-1.5">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full mb-6 rounded-lg bg-ink-800 border border-ink-600 px-3 py-2.5 text-sm text-ink-50 placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-signal-actual/50 focus:border-signal-actual transition"
            placeholder="••••••••"
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-signal-actual text-ink-950 font-medium py-2.5 text-sm hover:bg-signal-actual/90 disabled:opacity-60 transition"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="text-center text-xs text-ink-400 mt-6">
          Real-Time Business Intelligence & Anomaly Detection
        </p>
      </div>
    </div>
  );
}