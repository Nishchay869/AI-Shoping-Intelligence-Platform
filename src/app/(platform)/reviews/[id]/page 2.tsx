"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";

type ReviewSummary = {
  product_id: string;
  reviews_analyzed: number;
  rating_breakdown: { average_rating: number | null; total_reviews: number; histogram: Record<string, number>; positive_pct: number; neutral_pct: number; negative_pct: number };
  top_keywords: { keyword: string; mentions: number }[];
  pros: string[];
  cons: string[];
  common_complaints: { complaint: string; mention_count: number }[];
  overall_sentiment: { label: string; summary: string };
  recommendation: { verdict: string; rationale: string };
};

const sentimentTone: Record<string, string> = {
  very_positive: "bg-emerald-50 text-emerald-700",
  positive: "bg-emerald-50 text-emerald-700",
  mixed: "bg-amber-50 text-amber-700",
  negative: "bg-rose-50 text-rose-700",
  very_negative: "bg-rose-50 text-rose-700"
};
const verdictLabel: Record<string, string> = { recommended: "Recommended", recommended_with_caveats: "Recommended with caveats", not_recommended: "Not recommended" };

/** Fetches the AI review summary (pros/cons/complaints/sentiment/recommendation) for one real catalog product. */
export default function ReviewSummaryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError(null);
    fetch(`/api/v1/products/${id}/reviews/summary`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail ?? data.error ?? "Could not summarize reviews for this product");
        if (!cancelled) setSummary(data);
      })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Something went wrong"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  return (
    <div>
      <Link href="/recommendations" className="inline-flex items-center text-sm font-semibold text-slate-500 hover:text-brand-700">← Back to AI picks</Link>
      <p className="mt-4 label-caps text-brand-600">Review insights</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">What buyers are saying</h1>

      {loading && <div className="card mt-6 p-10 text-center text-sm text-slate-500">Analyzing reviews with the AI summarizer…</div>}
      {error && <div className="card mt-6 border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}

      {summary && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="card p-5"><p className="label-caps">Reviews analyzed</p><p className="data mt-1 text-2xl font-bold text-ink">{summary.reviews_analyzed.toLocaleString()}</p></div>
            <div className="card p-5"><p className="label-caps">Average rating</p><p className="data mt-1 text-2xl font-bold text-ink">★ {summary.rating_breakdown.average_rating ?? "n/a"}</p></div>
            <div className={`card p-5 ${sentimentTone[summary.overall_sentiment.label] ?? ""}`}><p className="label-caps opacity-80">Overall sentiment</p><p className="mt-1 text-2xl font-bold capitalize">{summary.overall_sentiment.label.replace(/_/g, " ")}</p></div>
          </div>

          <div className="card mt-4 p-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-bold text-ink">Recommendation</h2>
              <span className="pill bg-brand-50 text-brand-700">{verdictLabel[summary.recommendation.verdict] ?? summary.recommendation.verdict}</span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{summary.recommendation.rationale}</p>
            <p className="mt-3 text-sm text-slate-500">{summary.overall_sentiment.summary}</p>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="card p-6">
              <h2 className="font-bold text-emerald-700">Pros</h2>
              <ul className="mt-2 space-y-2 text-sm text-slate-600">{summary.pros.map((pro) => <li key={pro}>+ {pro}</li>)}</ul>
            </div>
            <div className="card p-6">
              <h2 className="font-bold text-rose-700">Cons</h2>
              <ul className="mt-2 space-y-2 text-sm text-slate-600">{summary.cons.map((con) => <li key={con}>− {con}</li>)}</ul>
            </div>
          </div>

          <div className="card mt-4 p-6">
            <h2 className="font-bold text-ink">Common complaints</h2>
            <ul className="mt-2 space-y-2 text-sm text-slate-600">
              {summary.common_complaints.map((item) => (
                <li key={item.complaint} className="flex items-center justify-between gap-4">
                  <span>{item.complaint}</span>
                  <span className="data pill whitespace-nowrap bg-slate-100 text-slate-500">{item.mention_count}x</span>
                </li>
              ))}
              {summary.common_complaints.length === 0 && <li className="text-slate-400">No recurring complaints found.</li>}
            </ul>
          </div>

          {summary.top_keywords.length > 0 && (
            <div className="card mt-4 p-6">
              <h2 className="font-bold text-ink">Frequently mentioned</h2>
              <div className="mt-2 flex flex-wrap gap-2">{summary.top_keywords.map((keyword) => <span key={keyword.keyword} className="pill bg-slate-100 text-slate-600">{keyword.keyword} · {keyword.mentions}</span>)}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
