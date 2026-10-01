const STYLES = {
  critical: "bg-signal-anomaly/15 text-signal-anomaly border-signal-anomaly/30",
  high: "bg-signal-anomaly/10 text-signal-anomaly/90 border-signal-anomaly/20",
  medium: "bg-signal-forecast/10 text-signal-forecast border-signal-forecast/25",
  low: "bg-ink-700 text-ink-200 border-ink-600",
};

export default function SeverityBadge({ severity }) {
  const style = STYLES[severity] || STYLES.low;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${style}`}>
      {severity}
    </span>
  );
}