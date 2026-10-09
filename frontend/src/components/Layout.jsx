import { NavLink } from "react-router-dom";
import { Activity, LayoutDashboard, AlertTriangle, TrendingUp, MessageSquare, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, enabled: true },
  { to: "/anomalies", label: "Anomalies", icon: AlertTriangle, enabled: true },
  { to: "/forecasts", label: "Forecasting", icon: TrendingUp, enabled: true },
  { to: "/assistant", label: "Ask PulseIQ", icon: MessageSquare, enabled: true },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-ink-950 flex">
      <aside className="w-60 border-r border-ink-800 flex flex-col">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="p-1.5 rounded-lg bg-signal-actual/10">
            <Activity className="w-4 h-4 text-signal-actual" strokeWidth={2.5} />
          </div>
          <span className="font-semibold text-ink-50 tracking-tight">PulseIQ</span>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, enabled }) =>
            enabled ? (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition ${
                    isActive
                      ? "bg-signal-actual/10 text-signal-actual"
                      : "text-ink-200 hover:bg-ink-800"
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {label}
              </NavLink>
            ) : (
              <div
                key={to}
                className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-ink-600 cursor-not-allowed"
                title="Coming soon"
              >
                <Icon className="w-4 h-4" />
                {label}
              </div>
            )
          )}
        </nav>

        <div className="px-3 pb-4 border-t border-ink-800 pt-3">
          {user && (
            <div className="px-3 pb-2">
              <p className="text-sm text-ink-50 truncate">{user.email}</p>
              <p className="text-xs text-ink-400">{user.role}</p>
            </div>
          )}
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-ink-200 hover:bg-ink-800 transition"
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}