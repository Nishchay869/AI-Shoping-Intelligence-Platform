"use client";
import { useState } from "react";
import { Icon } from "@/components/icons";

type ReviewSnippet = { source: string; quote: string; url: string };
type RecommendationItem = {
  rank: number;
  title: string;
  brand: string | null;
  retailer: string;
  price: number;
  currency: string;
  image_url: string | null;
  url: string;
  reason: string;
  is_best_pick: boolean;
  reviews: ReviewSnippet[];
};
type RecommendationResponse = { interpreted_intent: string; items: RecommendationItem[] };

const CATEGORIES = ["Smartphones", "Laptops", "Headphones & Earbuds", "Smartwatches & Wearables", "Tablets", "Cameras", "Gaming Consoles & Accessories", "TVs & Home Entertainment", "Home Appliances", "Other"];

const formatPrice = (price: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(price);

/** Product photo with a graceful fallback for both "no image_url at all" and "image_url present but fails to
 * load" (hotlink-blocked or dead links are common with web-search-sourced images). Uses object-contain rather
 * than object-cover - web listing photos vary wildly in aspect ratio, and cropping them to fill the frame is
 * what made unrelated marketing banners look like misaligned, cut-off product shots. Sized by aspect-ratio
 * rather than a fixed height so it never depends on flex-stretch from a sibling (the previous h-40/h-auto
 * setup could end up taller or shorter than the image's own box depending on layout context). */
function ProductThumbnail({ src, alt, className = "aspect-square w-full" }: { src: string | null; alt: string; className?: string }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <div className={`flex items-center justify-center bg-slate-50 ${className}`}>
        <Icon name="sparkles" className="h-8 w-8 text-slate-300" />
      </div>
    );
  }
  return (
    <div className={`bg-slate-50 p-3 ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} onError={() => setFailed(true)} className="h-full w-full object-contain" />
    </div>
  );
}

/** Collects budget/purpose/brand/features, then renders up to 10 real, live product listings ranked by fit -
 * the #1 pick is called out explicitly as the one to buy, with real review excerpts pulled from the web. */
export default function RecommendationsPage() {
  const [budget, setBudget] = useState("");
  const [purpose, setPurpose] = useState("");
  const [brand, setBrand] = useState("");
  const [features, setFeatures] = useState("");
  const [category, setCategory] = useState("");
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
          features: features.split(",").map((feature) => feature.trim()).filter(Boolean),
          category: category || undefined
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not generate recommendations");
      setResult(data);
      setBudget(""); setPurpose(""); setBrand(""); setFeatures(""); setCategory("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const bestPick = result?.items.find((item) => item.is_best_pick) ?? result?.items[0];
  const rest = result?.items.filter((item) => item !== bestPick) ?? [];

  return (
    <div>
      <p className="label-caps text-brand-600">AI Recommendations</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Tell us what you need</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">Your budget, purpose, brand preference, and must-have features are turned into a live web search - Gemini ranks up to 10 real, purchasable listings and picks the one best-suited to you.</p>
      <form onSubmit={submit} className="card mt-6 grid gap-4 p-6 sm:grid-cols-2">
        <label className="block"><span className="label-caps">Category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="input mt-2">
            <option value="">Any category</option>
            {CATEGORIES.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        </label>
        <label className="block"><span className="label-caps">Budget</span><input type="number" min={0} value={budget} onChange={(event) => setBudget(event.target.value)} className="input mt-2" placeholder="e.g. 25000" /></label>
        <label className="block"><span className="label-caps">Brand preference</span><input value={brand} onChange={(event) => setBrand(event.target.value)} className="input mt-2" placeholder="e.g. Sony (optional)" /></label>
        <label className="block sm:col-span-2"><span className="label-caps">Purpose</span><input required value={purpose} onChange={(event) => setPurpose(event.target.value)} className="input mt-2" placeholder="e.g. noise-cancelling headphones for daily commute" /></label>
        <label className="block sm:col-span-2"><span className="label-caps">Must-have features</span><input value={features} onChange={(event) => setFeatures(event.target.value)} className="input mt-2" placeholder="comma-separated, e.g. long battery life, lightweight" /></label>
        <button type="submit" disabled={loading || purpose.trim().length < 3} className="btn-primary sm:col-span-2">{loading ? "Searching the web…" : "Get recommendations"}</button>
      </form>
      {error && <div className="card mt-4 border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}
      {result && (
        <>
          <p className="mt-6 text-sm text-slate-500"><span className="font-semibold text-ink">Interpreted as:</span> {result.interpreted_intent}</p>

          {bestPick && (
            <article className="card mt-4 overflow-hidden border-2 border-brand-600">
              <div className="flex flex-col sm:flex-row">
                <ProductThumbnail src={bestPick.image_url} alt={bestPick.title} className="aspect-square w-full sm:w-72 sm:shrink-0" />
                <div className="p-6">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="pill inline-flex items-center gap-1 bg-brand-600 text-white"><Icon name="check" className="h-3 w-3" /> Best pick for you</span>
                    <p className="label-caps">{bestPick.brand ?? "Unbranded"} · {bestPick.retailer}</p>
                  </div>
                  <h3 className="mt-2 text-xl font-bold text-ink">{bestPick.title}</h3>
                  <span className="data mt-2 block text-2xl font-extrabold text-ink">{formatPrice(bestPick.price, bestPick.currency)}</span>
                  <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-600">{bestPick.reason}</p>
                  <a href={bestPick.url} target="_blank" rel="noopener noreferrer" className="btn-primary mt-4 inline-flex items-center gap-2">
                    You can buy this product <Icon name="arrow" className="h-3 w-3" />
                  </a>
                  {bestPick.reviews.length > 0 && (
                    <div className="mt-5 space-y-3 border-t border-slate-100 pt-4">
                      <p className="label-caps text-slate-400">What real reviews say</p>
                      {bestPick.reviews.map((review, index) => (
                        <a key={index} href={review.url} target="_blank" rel="noopener noreferrer" className="block rounded-lg bg-slate-50 p-3 text-sm text-slate-600 hover:bg-slate-100">
                          <Icon name="quote" className="mb-1 h-4 w-4 text-slate-300" />
                          <span className="italic">&ldquo;{review.quote}&rdquo;</span>
                          <span className="mt-1 block text-xs font-semibold text-brand-700">— {review.source}</span>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </article>
          )}

          {rest.length > 0 && (
            <>
              <p className="label-caps mt-8 text-slate-400">More options, ranked by fit</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {rest.map((item) => (
                  <a key={`${item.url}-${item.rank}`} href={item.url} target="_blank" rel="noopener noreferrer" className="card overflow-hidden">
                    <ProductThumbnail src={item.image_url} alt={item.title} />
                    <div className="p-5">
                      <div className="flex items-center gap-2">
                        <span className="pill bg-blue-50 text-blue-700">#{item.rank}</span>
                        <p className="label-caps">{item.brand ?? "Unbranded"} · {item.retailer}</p>
                      </div>
                      <h3 className="mt-2 line-clamp-2 min-h-10 text-sm font-semibold text-ink">{item.title}</h3>
                      <span className="data mt-2 block text-lg font-bold text-ink">{formatPrice(item.price, item.currency)}</span>
                      <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">{item.reason}</p>
                      <span className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-brand-700">
                        View deal <Icon name="arrow" className="h-3 w-3" />
                      </span>
                    </div>
                  </a>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
