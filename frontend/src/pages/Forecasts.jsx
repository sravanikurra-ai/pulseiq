import { useEffect, useState } from "react";
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import client from "../api/client";

const money = (v) => `$${Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

export default function Forecasts() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    client
      .get("/forecasts/?limit=14")
      .then((res) => setItems(res.data.items))
      .catch(() => setError("Could not load forecasts."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-ink-400 text-sm">Loading…</div>;
  if (error) return <div className="p-8 text-signal-anomaly text-sm">{error}</div>;

  const chartData = items.map((f) => ({
    date: f.forecast_date,
    predicted: f.predicted_value,
    lower: f.lower_bound,
    upper: f.upper_bound,
    range: f.upper_bound - f.lower_bound, // stacked on top of `lower` to draw the band
  }));

  const modelName = items[0]?.model_name;

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-50">Forecasting</h1>
        <p className="text-sm text-ink-400">
          14-day revenue forecast{modelName ? ` · model: ${modelName}` : ""}
        </p>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-ink-400">No forecast generated yet.</p>
      ) : (
        <>
          <div className="bg-ink-900 border border-ink-700 rounded-xl p-5">
            <h2 className="text-sm font-medium text-ink-50 mb-4">Predicted Revenue with Confidence Range</h2>
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262c3b" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b7488" }} />
                <YAxis tick={{ fontSize: 11, fill: "#6b7488" }} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip
                  contentStyle={{ background: "#11151d", border: "1px solid #262c3b", borderRadius: 8 }}
                  labelStyle={{ color: "#f4f5f7" }}
                  formatter={(value, name) =>
                    name === "predicted" ? [money(value), "Predicted"] : [money(value), name]
                  }
                />
                {/* Confidence band: invisible base (lower) + filled range stacked on top */}
                <Area type="monotone" dataKey="lower" stackId="band" stroke="none" fill="transparent" />
                <Area
                  type="monotone"
                  dataKey="range"
                  stackId="band"
                  stroke="none"
                  fill="#ba8fef"
                  fillOpacity={0.15}
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#ba8fef"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ r: 3, fill: "#ba8fef" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-ink-900 border border-ink-700 rounded-xl divide-y divide-ink-800">
            {items.map((f) => (
              <div key={f.id} className="p-4 flex items-center justify-between text-sm">
                <span className="text-ink-200">{f.forecast_date}</span>
                <span className="text-ink-50 font-medium">{money(f.predicted_value)}</span>
                <span className="text-ink-400 text-xs">
                  {money(f.lower_bound)} – {money(f.upper_bound)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}