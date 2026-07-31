"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/icons";

type Source = { label: string; source_type: string; product_id: string | null; similarity: number | null; title: string | null; url: string | null };
type Message = { role: "assistant" | "user"; content: string; sources?: Source[] };

/** Shopping Chat: a RAG assistant grounded in the product catalog, buyer reviews, and a live web search, via the FastAPI backend. */
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: "Ask me anything about products in the catalog or what buyers are saying in their reviews." }]);
  const [value, setValue] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(event: FormEvent) {
    event.preventDefault();
    const text = value.trim();
    if (!text || loading) return;
    setMessages((all) => [...all, { role: "user", content: text }]);
    setValue("");
    setLoading(true);
    try {
      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, conversationId })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "The assistant couldn't answer that.");
      if (data.conversation_id) setConversationId(data.conversation_id);
      setMessages((all) => [...all, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch (err) {
      setMessages((all) => [...all, { role: "assistant", content: err instanceof Error ? err.message : "Something went wrong." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <div>
        <p className="label-caps text-brand-600">AI Shopping Copilot</p>
        <h1 className="mt-1 text-3xl font-bold text-ink">Shopping Chat</h1>
        <p className="mt-2 text-slate-500">Answers are retrieved from the product catalog, buyer reviews, and a live web search, with sources cited.</p>
      </div>
      <div className="card mt-6 flex h-[560px] flex-col overflow-hidden">
        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-brand-600 text-white" : "bg-slate-100 text-ink"}`}>
                <p>{message.content}</p>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {message.sources.map((source) =>
                      source.source_type === "web" && source.url ? (
                        <a key={source.label} href={source.url} target="_blank" rel="noopener noreferrer" className="rounded-full bg-white/60 px-2 py-0.5 text-xs font-semibold text-blue-600 underline hover:text-blue-700" title={source.title ?? undefined}>
                          {source.label} ↗
                        </a>
                      ) : (
                        <span key={source.label} className="rounded-full bg-white/60 px-2 py-0.5 text-xs font-semibold text-slate-500">{source.label}</span>
                      )
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && <div className="flex justify-start"><p className="max-w-[85%] rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-400">Thinking…</p></div>}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={send} className="border-t p-4">
          <label className="sr-only" htmlFor="chat-message">Ask Shopping Chat</label>
          <div className="flex gap-2">
            <input id="chat-message" value={value} onChange={(event) => setValue(event.target.value)} className="input" placeholder="What do buyers say about battery life?" disabled={loading} />
            <button type="submit" className="btn-primary" aria-label="Send message" disabled={loading}><Icon name="send" className="h-4 w-4" /></button>
          </div>
          <p className="mt-2 text-xs text-slate-400">AI can make mistakes. Verify final retailer details before buying.</p>
        </form>
      </div>
    </div>
  );
}
