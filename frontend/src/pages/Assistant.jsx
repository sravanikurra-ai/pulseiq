import { useState, useRef, useEffect } from "react";
import { Send, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import client from "../api/client";

const SUGGESTIONS = [
  "What was our revenue in September 2026?",
  "Have there been any unusual patterns in orders recently?",
  "What's the average daily revenue in August 2026?",
];

function Evidence({ evidence }) {
  const [open, setOpen] = useState(false);
  if (!evidence || evidence.length === 0) return null;
  return (
    <div className="mt-3 border-t border-ink-700 pt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs text-ink-400 hover:text-ink-200 transition"
      >
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        Evidence ({evidence.length} tool call{evidence.length > 1 ? "s" : ""})
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {evidence.map((e, i) => (
            <pre
              key={i}
              className="text-[11px] leading-snug bg-ink-950 border border-ink-800 rounded-lg p-3 overflow-x-auto text-ink-200"
            >
              {e.tool}({JSON.stringify(e.args)}){"\n"}
              {"→ "}
              {JSON.stringify(e.result, null, 2)}
            </pre>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Assistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const ask = async (question) => {
    const q = question.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await client.post(
        "/analytics/query",
        { question: q },
        { timeout: 180000 } // local CPU inference can take a minute or more
      );
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.data.answer, evidence: res.data.evidence },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: "Sorry, I couldn't get an answer. The language model may be offline or too slow.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 flex flex-col h-screen">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold text-ink-50">Ask PulseIQ</h1>
        <p className="text-sm text-ink-400">
          Answers come from real backend calculations. The model only explains the numbers it is given.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-ink-400">Try asking:</p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="block text-left text-sm text-ink-200 bg-ink-900 border border-ink-700 rounded-lg px-4 py-2 hover:bg-ink-800 transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={`max-w-[75%] rounded-xl px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-signal-actual/15 text-ink-50 border border-signal-actual/30"
                  : m.error
                  ? "bg-signal-anomaly/10 text-signal-anomaly border border-signal-anomaly/30"
                  : "bg-ink-900 text-ink-50 border border-ink-700"
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
              {m.role === "assistant" && !m.error && <Evidence evidence={m.evidence} />}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-ink-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Thinking... a local model can take a minute or more.
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="mt-4 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your business data..."
          className="flex-1 rounded-lg bg-ink-900 border border-ink-700 px-4 py-2.5 text-sm text-ink-50 placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-signal-actual/50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-lg bg-signal-actual text-ink-950 px-4 py-2.5 disabled:opacity-50 transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}