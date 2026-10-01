export default function KpiCard({ label, value, suffix = "", note, formatter }) {
  const display = formatter ? formatter(value) : value;
  return (
    <div className="bg-ink-900 border border-ink-700 rounded-xl p-4 flex flex-col gap-1">
      <span className="text-xs text-ink-400 font-medium">{label}</span>
      <span className="text-2xl font-semibold text-ink-50 tracking-tight">
        {display}
        {suffix}
      </span>
      {note && <span className="text-[11px] text-ink-400 mt-1 leading-snug">{note}</span>}
    </div>
  );
}