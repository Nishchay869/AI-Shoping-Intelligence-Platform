"use client";
import { ChangeEvent, useMemo, useState } from "react";
import { Icon } from "@/components/icons";
import { ProductCard } from "@/components/ui";
import { products } from "@/lib/mock-data";

type ImageSearchProduct = { id: string; title: string; brand: string | null; category: string | null; image_url: string | null; currency: string; current_price_minor: number; retailer: string; average_rating: number | null; review_count: number };
type ImageSearchResult = { product: ImageSearchProduct; similarity: number };

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);

/** Upload a product photo to find visually similar catalog items - CLIP image embedding + pgvector cosine search, real backend data. */
function ImageSearch() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<ImageSearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
    setResults(null);
    setError(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await fetch("/api/v1/products/image-search", { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not search by that image.");
      setResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card mt-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-bold text-ink">Search by photo</h2>
          <p className="mt-1 text-sm text-slate-500">Upload a picture of a product to find visually similar items in the catalog.</p>
        </div>
        <label className="btn-secondary cursor-pointer">
          <Icon name="search" className="mr-2 h-4 w-4" />
          Upload image
          <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
        </label>
      </div>

      {previewUrl && (
        <div className="mt-4 flex items-center gap-4">
          <img src={previewUrl} alt="Uploaded query" className="h-20 w-20 rounded-xl border border-slate-200 object-cover" />
          {loading && <p className="text-sm text-slate-400">Embedding image and searching…</p>}
        </div>
      )}
      {error && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {results && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {results.map(({ product, similarity }) => (
            <article key={product.id} className="card overflow-hidden p-4">
              {product.image_url && <img src={product.image_url} alt={product.title} className="mb-3 h-32 w-full rounded-lg object-cover" />}
              <p className="label-caps text-brand-600">{Math.round(similarity * 100)}% visual match · {product.brand ?? "Unbranded"}</p>
              <h3 className="mt-1 line-clamp-2 min-h-10 text-sm font-semibold text-ink">{product.title}</h3>
              <div className="mt-2 flex items-center justify-between">
                <span className="data text-lg font-bold text-ink">{formatPrice(product.current_price_minor, product.currency)}</span>
                {product.average_rating !== null && <span className="data text-xs text-slate-500">★ {product.average_rating} ({product.review_count})</span>}
              </div>
            </article>
          ))}
          {results.length === 0 && <div className="card col-span-full p-8 text-center text-sm text-slate-500">No visually similar products found in the indexed catalog yet.</div>}
        </div>
      )}
    </div>
  );
}

/** Discover screen filters the typed catalog locally; replace the derived list with an API query when catalog search is connected. */
export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const results = useMemo(() => products.filter((p) => (category === "All" || p.category === category) && `${p.title} ${p.brand}`.toLowerCase().includes(query.toLowerCase())), [query, category]);

  return (
    <div>
      <p className="label-caps text-brand-600">Discover</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Find the best time to buy</h1>

      <div className="card mt-6 flex flex-col gap-3 p-3 sm:flex-row">
        <label className="relative flex-1">
          <span className="sr-only">Search products</span>
          <Icon name="search" className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} className="h-11 w-full rounded-full border-none bg-slate-50 pl-11 pr-4 text-sm outline-none transition focus:ring-4 focus:ring-brand-50" placeholder="Search for a product, brand, or category…" />
        </label>
        <select aria-label="Filter category" className="input h-11 rounded-full sm:w-44" value={category} onChange={(e) => setCategory(e.target.value)}>
          {["All", "Audio", "Wearables", "Fashion", "Electronics"].map((option) => <option key={option}>{option}</option>)}
        </select>
      </div>

      <ImageSearch />

      <div className="mt-8 flex items-center justify-between">
        <p className="data text-sm text-slate-500">{results.length} verified products</p>
        <p className="text-xs text-slate-400">Prices sourced from approved retailer feeds</p>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {results.map((p) => <ProductCard product={p} key={p.id} />)}
      </div>
      {!results.length && <div className="card mt-4 p-10 text-center text-slate-500">No products match that search — try widening your filters.</div>}
    </div>
  );
}
