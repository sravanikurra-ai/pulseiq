import { useEffect, useState } from "react";
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import client from "../api/client";
import KpiCard from "../components/KpiCard";
import SeverityBadge from "../components/SeverityBadge";

const money = (v) => `$${Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
const pct = (v) => `${v}%`;

function buildChartData(trend, forecastItems, anomalyItems) {
  const map = {};
  trend.forEach((d) => {
    map[d.date] = { date: d.date, actual: d.revenue };
  });
  forecastItems.forEach((f) => {
    map[f.forecast_date] = {
      ...(map[f.forecast_date] || { date: f.forecast_date }),
      forecast: f.predicted_value,
    };
  });
  anomalyItems.forEach((a) => {
    const day = a.detected_at.slice(0, 10); // "2026-09-15T00:00:00+00:00" -> "2026-09-15"
    if (map[day]) {
      map[day].isAnomaly = true;
      map[day].anomalyNote = a.explanation;
    }
  });
  return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [summaryRes, trendRes, anomaliesRes, forecastsRes, alertsRes] = await Promise.all([
          client.get("/dashboard/summary"),
          client.get("/kpis/revenue/trend?days=120"),
          client.get("/anomalies/?limit=50"),
          client.get("/forecasts/?limit=14"),
          client.get("/alerts/?status=OPEN&limit=10"),
        ]);
        setSummary(summaryRes.data);
        setChartData(
          buildChartData(trendRes.data.items, forecastsRes.data.items, anomaliesRes.data.items)
        );
        setAlerts(alertsRes.data.items);
      } catch (err) {
        console.error("Dashboard load error:", err);
        setError("Could not load dashboard data. Is the backend running?");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="p-8 text-ink-400 text-sm">Loading dashboard…</div>;
  }
  if (error) {
    return <div className="p-8 text-signal-anomaly text-sm">{error}</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-50">Overview</h1>
        <p className="text-sm text-ink-400">
          {summary.period.start} to {summary.period.end}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Revenue" value={summary.kpis.revenue.value} formatter={money} />
        <KpiCard label="Orders" value={summary.kpis.orders.value} />
        <KpiCard label="Avg Order Value" value={summary.kpis.aov.value} formatter={money} />
        <KpiCard
          label="Marketing ROI"
          value={summary.kpis.marketing_roi.value}
          formatter={pct}
          note={summary.kpis.marketing_roi.note}
        />
        <KpiCard
          label="Conversion Rate"
          value={summary.kpis.conversion_rate.value}
          formatter={pct}
          note={summary.kpis.conversion_rate.note}
        />
        <KpiCard label="CAC" value={summary.kpis.cac.value} formatter={money} note={summary.kpis.cac.note} />
        <KpiCard label="Retention" value={summary.kpis.retention_rate.value} formatter={pct} />
        <KpiCard label="Growth Rate" value={summary.kpis.growth_rate.value} formatter={pct} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-ink-900 border border-ink-700 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-ink-50">Revenue: Actual vs Forecast</h2>
            <div className="flex items-center gap-4 text-xs text-ink-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-signal-actual" /> Actual
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-0.5 bg-signal-forecast" /> Forecast
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-signal-anomaly" /> Anomaly
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262c3b" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b7488" }} minTickGap={30} />
              <YAxis tick={{ fontSize: 11, fill: "#6b7488" }} tickFormatter={(v) => `$${v / 1000}k`} />
              <Tooltip
                contentStyle={{ background: "#11151d", border: "1px solid #262c3b", borderRadius: 8 }}
                labelStyle={{ color: "#f4f5f7" }}
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#5b8def"
                strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  if (!payload.isAnomaly) return null;
                  return (
                    <circle
                      key={`anomaly-${payload.date}`}
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill="#ef5b5b"
                      stroke="#0b0e14"
                      strokeWidth={1}
                    />
                  );
                }}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#ba8fef"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-ink-900 border border-ink-700 rounded-xl p-5">
          <h2 className="text-sm font-medium text-ink-50 mb-4">Open Alerts ({summary.open_alerts.total})</h2>
          <div className="space-y-3 max-h-[280px] overflow-y-auto">
            {alerts.length === 0 && <p className="text-xs text-ink-400">No open alerts.</p>}
            {alerts.map((a) => (
              <div key={a.id} className="border-b border-ink-800 pb-3 last:border-0">
                <div className="flex items-center justify-between mb-1">
                  <SeverityBadge severity={a.severity} />
                  <span className="text-[11px] text-ink-400">
                    {new Date(a.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-ink-200 leading-snug">{a.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}