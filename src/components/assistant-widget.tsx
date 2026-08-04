"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/icons";

type Source = { label: string; title: string; url: string };
type Message = { role: "assistant" | "user"; content: string; toolCalls?: string[]; sources?: Source[] };

const GREETING = "Ask me to compare products, explain specs, suggest alternatives, or recommend something.";

const SUGGESTIONS = [
  "Compare the Sony headphones with the Bose earbuds",
  "What do reviews say about the Fitbit's battery life?",
  "Suggest alternatives to the Kindle Paperwhite",
  "Recommend a fitness tracker under $150 with GPS"
];

/** The assistant is prompted to wrap the one key fact per answer (a product name, price, spec) in markdown
 * **bold**, and sometimes adds stray "#" headers or "*"/"-" list markers despite being told to write plain
 * prose (an LLM's formatting instructions aren't always followed to the letter). This renders those markers
 * as actual formatting instead of showing the literal characters. */
function renderWithBold(text: string) {
  const cleaned = text
    .split("\n")
    .map((line) => line.replace(/^\s{0,3}#{1,6}\s+/, "").replace(/^\s{0,3}[-*]\s+/, "• "))
    .join("\n");
  return cleaned.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={index}>{part.slice(2, -2)}</strong> : <span key={index}>{part}</span>
  );
}

/** AI Shopping Assistant, as a floating chat widget (round launcher, bottom-right) rather than a dedicated
 * page - a LangGraph tool-calling agent (compare/explain/suggest/recommend) with persistent per-thread
 * memory, reachable by typing. */
export function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [closing, setClosing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: GREETING }]);
  const [value, setValue] = useState("");
  const [threadId, setThreadId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  function closePanel() {
    setClosing(true);
    setTimeout(() => { setOpen(false); setClosing(false); }, 180);
  }

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, open]);

  async function sendMessage(text: string) {
    if (!text || loading) return;
    setMessages((all) => [...all, { role: "user", content: text }]);
    setValue("");
    setLoading(true);
    try {
      const response = await fetch("/api/v1/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, threadId })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "The assistant couldn't respond.");
      setThreadId(data.thread_id);
      setMessages((all) => [...all, { role: "assistant", content: data.answer, toolCalls: data.tool_calls, sources: data.sources }]);
    } catch (err) {
      setMessages((all) => [...all, { role: "assistant", content: err instanceof Error ? err.message : "Something went wrong." }]);
    } finally {
      setLoading(false);
    }
  }

  function startNewConversation() {
    setMessages([{ role: "assistant", content: GREETING }]);
    setThreadId(undefined);
    setValue("");
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    sendMessage(value.trim());
  }

  return (
    <>
      {open && (
        <div className={`surface-elevated fixed bottom-24 right-6 z-50 flex h-[560px] w-[380px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-3xl ${closing ? "animate-scale-out" : "animate-scale-in"}`} style={{ transformOrigin: "bottom right" }}>
          <div className="flex items-center justify-between bg-gradient-to-r from-brand-700 to-brand-600 px-4 py-3 text-white">
            <div className="flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-white/15"><Icon name="sparkles" className="h-4 w-4" /></span>
              <div>
                <p className="text-sm font-bold leading-tight">AI Shopping Assistant</p>
                <p className="label-caps text-brand-100">Always online</p>
              </div>
            </div>
            <button aria-label="Close assistant" onClick={closePanel} className="rounded-full p-1 transition-colors hover:bg-white/20"><Icon name="x" className="h-5 w-5" /></button>
          </div>

          {messages.length <= 1 && (
            <div className="flex flex-wrap gap-1.5 border-b border-slate-200/70 p-3">
              {SUGGESTIONS.map((suggestion) => (
                <button key={suggestion} onClick={() => sendMessage(suggestion)} className="shadow-neu-sm rounded-full px-2.5 py-1 text-[11px] font-medium text-slate-600 transition-all hover:text-brand-600 active:shadow-neu-inset-sm">
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] px-3 py-2 text-sm leading-6 ${message.role === "user" ? "rounded-2xl rounded-tr-sm bg-brand-600 text-white shadow-neu-sm" : "shadow-neu-inset-sm rounded-2xl rounded-tl-sm bg-surface text-ink"}`}>
                  <p className="whitespace-pre-wrap">{message.role === "assistant" ? renderWithBold(message.content) : message.content}</p>
                  {message.toolCalls && message.toolCalls.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {message.toolCalls.map((toolName, i) => <span key={`${toolName}-${i}`} className="pill bg-slate-200/70 text-slate-600">{toolName}</span>)}
                    </div>
                  )}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {message.sources.map((source) => (
                        <a key={source.label} href={source.url} target="_blank" rel="noopener noreferrer" className="pill bg-slate-200/70 text-blue-600 underline hover:text-blue-700" title={source.title}>
                          {source.label} ↗
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && <div className="flex justify-start"><p className="shadow-neu-inset-sm max-w-[85%] rounded-2xl rounded-tl-sm bg-surface px-3 py-2 text-sm text-slate-400">Thinking…</p></div>}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSubmit} className="border-t border-slate-200/70 p-3">
            <div className="flex gap-2">
              <label className="sr-only" htmlFor="assistant-widget-message">Ask the shopping assistant</label>
              <input id="assistant-widget-message" value={value} onChange={(event) => setValue(event.target.value)} className="input min-w-0 flex-1" placeholder="Ask me anything…" disabled={loading} />
              <button
                type="button"
                onClick={startNewConversation}
                aria-label="Start a new conversation"
                title="Start a new conversation"
                disabled={loading}
                className="btn-secondary"
              >
                <Icon name="restart" className="h-4 w-4" />
              </button>
              <button type="submit" className="btn-primary" aria-label="Send message" disabled={loading}><Icon name="send" className="h-4 w-4" /></button>
            </div>
          </form>
        </div>
      )}

      {!open && (
        <button
          onClick={() => setOpen(true)}
          aria-label="Open AI shopping assistant"
          className="fixed bottom-6 right-6 z-50 grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-neu-brand transition-all duration-200 hover:scale-110 active:scale-95 active:shadow-neu-brand-inset"
        >
          <Icon name="message" className="h-6 w-6" />
        </button>
      )}
    </>
  );
}
