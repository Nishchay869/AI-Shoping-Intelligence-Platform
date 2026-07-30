"use client";
import Link from "next/link";
import { useState } from "react";

type RecommendationItem = {
  rank: number;
  reason: string;
  product: { id: string; title: string; brand: string | null; category: string | null; currency: string; current_price_minor: number; retailer: string; average_rating: number | null; review_count: number };
};
type RecommendationResponse = { interpreted_intent: string; items: RecommendationItem[]; unavailable_brand: string | null };

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);

/** Collects budget/purpose/brand/features, then renders the AI engine's top-5 picks with attribute-grounded explanations. */
export default function RecommendationsPage() {
  const [budget, setBudget] = useState("");
  const [purpose, setPurpose] = useState("");
  const [brand, setBrand] = useState("");
  const [features, setFeatures] = useState("");
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await fetch("/api/v1/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget: budget ? Number(budget) : undefined,
          purpose,
          brandPreference: brand || undefined,
          features: features.split(",").map((feature) => feature.trim()).filter(Boolean)
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not generate recommendations");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p className="text-sm font-semibold text-brand-600">AI RECOMMENDATIONS</p>
      <h1 className="mt-1 text-3xl font-bold">Tell us what you need</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">Your budget, purpose, brand preference, and must-have features are turned into a semantic product search, then Gemini picks and explains the best 5 matches from the catalog.</p>
      <form onSubmit={submit} className="card mt-6 grid gap-4 p-6 sm:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">Budget<input type="number" min={0} value={budget} onChange={(event) => setBudget(event.target.value)} className="input mt-1" placeholder="e.g. 25000" /></label>
        <label className="text-sm font-medium text-slate-700">Brand preference<input value={brand} onChange={(event) => setBrand(event.target.value)} className="input mt-1" placeholder="e.g. Sony (optional)" /></label>
        <label className="text-sm font-medium text-slate-700 sm:col-span-2">Purpose<input required value={purpose} onChange={(event) => setPurpose(event.target.value)} className="input mt-1" placeholder="e.g. noise-cancelling headphones for daily commute" /></label>
        <label className="text-sm font-medium text-slate-700 sm:col-span-2">Must-have features<input value={features} onChange={(event) => setFeatures(event.target.value)} className="input mt-1" placeholder="comma-separated, e.g. long battery life, lightweight" /></label>
        <button type="submit" disabled={loading || purpose.trim().length < 3} className="btn-primary sm:col-span-2">{loading ? "Thinking…" : "Get recommendations"}</button>
      </form>
      {error && <div className="card mt-4 border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}
      {result && (
        <>
          {result.unavailable_brand && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              We don&apos;t have any {result.unavailable_brand} products in stock — showing the closest alternatives instead.
            </div>
          )}
          <p className="mt-6 text-sm text-slate-500"><span className="font-semibold text-slate-700">Interpreted as:</span> {result.interpreted_intent}</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {result.items.map((item) => (
              <article key={item.product.id} className="card overflow-hidden p-4">
                <p className="text-xs font-semibold text-brand-600">#{item.rank} match · {item.product.brand ?? "Unbranded"} · {item.product.retailer}</p>
                <h3 className="mt-1 line-clamp-2 min-h-10 text-sm font-semibold">{item.product.title}</h3>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold">{formatPrice(item.product.current_price_minor, item.product.currency)}</span>
                  {item.product.average_rating !== null && <span className="text-xs text-slate-500">★ {item.product.average_rating} ({item.product.review_count})</span>}
                </div>
                <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">{item.reason}</p>
                <Link href={`/reviews/${item.product.id}`} className="mt-3 inline-block text-xs font-semibold text-brand-600 hover:underline">See what reviewers say →</Link>
              </article>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
