import { useEffect, useState } from "react";
import { AlertTriangle, ChevronLeft, ChevronRight } from "lucide-react";
import client from "../api/client";

const PAGE_SIZE = 10;

export default function Anomalies() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    client
      .get(`/anomalies/?limit=${PAGE_SIZE}&offset=${offset}`)
      .then((res) => {
        setItems(res.data.items);
        setTotal(res.data.total);
      })
      .catch(() => setError("Could not load anomalies."))
      .finally(() => setLoading(false));
  }, [offset]);

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-50">Anomalies</h1>
        <p className="text-sm text-ink-400">
          {total} detected across the full order history, most recent first.
        </p>
      </div>

      {error && <p className="text-signal-anomaly text-sm">{error}</p>}
      {loading && <p className="text-ink-400 text-sm">Loading…</p>}

      {!loading && !error && (
        <>
          <div className="bg-ink-900 border border-ink-700 rounded-xl divide-y divide-ink-800">
            {items.length === 0 && (
              <p className="p-6 text-sm text-ink-400">No anomalies detected yet.</p>
            )}
            {items.map((a) => (
              <div key={a.id} className="p-5 flex items-start gap-4">
                <div className="p-2 rounded-lg bg-signal-anomaly/10 shrink-0">
                  <AlertTriangle className="w-4 h-4 text-signal-anomaly" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm font-medium text-ink-50">
                      {a.metric_name.replace("_", " ")}
                    </span>
                    <span className="text-xs text-ink-400 shrink-0">
                      {new Date(a.detected_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-ink-200 mt-1 leading-snug">{a.explanation}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-ink-400">
                    <span>Observed: {a.observed_value}</span>
                    {a.expected_value !== null && <span>Expected: {a.expected_value}</span>}
                    <span>Score: {a.anomaly_score}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-ink-400">
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
                className="p-2 rounded-lg border border-ink-700 text-ink-200 disabled:opacity-40 hover:bg-ink-800 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total}
                className="p-2 rounded-lg border border-ink-700 text-ink-200 disabled:opacity-40 hover:bg-ink-800 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}