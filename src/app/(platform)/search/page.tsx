"use client";
import { ChangeEvent, useMemo, useState } from "react";
import { ComparePrices } from "@/components/compare-prices";
import { Icon } from "@/components/icons";
import { ProductCard } from "@/components/ui";
import { products } from "@/lib/mock-data";

type ImageSearchProduct = { id: string; title: string; brand: string | null; category: string | null; image_url: string | null; currency: string; current_price_minor: number; retailer: string; average_rating: number | null; review_count: number };
type ImageSearchResult = { product: ImageSearchProduct; similarity: number };
type WebListing = { retailer: string; price: number; currency: string; url: string };
type ImageSearchResponse = { results: ImageSearchResult[]; identified_as: string | null; web_listings: WebListing[] };

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);
// Live web listings (unlike catalog products) come priced in major units already, e.g. 4999 meaning ₹4,999 - no /100 step.
const formatMajorPrice = (price: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(price);

/** Upload a product photo to find visually similar catalog items - CLIP image embedding + pgvector cosine
 * search, real backend data. Upload and search are separate steps (matching the receipt scanner's pattern)
 * so picking a photo never fires a request on its own - you review the preview, then choose to search. */
function ImageSearch() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [response, setResponse] = useState<ImageSearchResponse | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResponse(null);
    setError(null);
  }

  function removePhoto() {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResponse(null);
    setError(null);
  }

  async function runSearch() {
    if (!selectedFile) return;
    setSearching(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      const res = await fetch("/api/v1/products/image-search", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not search by that image.");
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSearching(false);
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
          {previewUrl ? "Choose a different photo" : "Upload image"}
          <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
        </label>
      </div>

      {previewUrl && (
        <div className="mt-4 flex flex-wrap items-start gap-4">
          <div className="relative h-32 w-32 shrink-0 overflow-hidden rounded-xl border border-slate-200">
            <img src={previewUrl} alt="Uploaded query" className="h-full w-full object-cover" />
            {searching && (
              <div className="absolute inset-0 bg-ink/15">
                <span className="absolute inset-x-0 h-8 animate-scan-sweep bg-gradient-to-b from-transparent via-brand-400/80 to-transparent shadow-[0_0_12px_2px_rgba(99,102,241,0.6)]" />
              </div>
            )}
          </div>
          <div className="flex flex-col gap-2">
            {!response && (
              <button type="button" onClick={runSearch} disabled={searching} className="btn-primary">
                {searching ? (<><Icon name="restart" className="mr-2 h-4 w-4 animate-spin" />Searching Flipkart, Amazon, Myntra…</>) : (<><Icon name="search" className="mr-2 h-4 w-4" />Search by photo</>)}
              </button>
            )}
            {response && <button type="button" onClick={removePhoto} className="btn-primary">Search another photo</button>}
            {!searching && <button type="button" onClick={removePhoto} className="btn-secondary">Remove photo</button>}
          </div>
        </div>
      )}
      {error && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {response && (
        <>
          {response.identified_as && <p className="mt-4 text-sm text-slate-500">Identified as <span className="font-semibold text-ink">{response.identified_as}</span> — here&apos;s where to buy it:</p>}

          {response.web_listings.length > 0 && (
            <div className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-100">
              {response.web_listings.map((listing, index) => (
                <a key={`${listing.retailer}-${index}`} href={listing.url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between gap-4 p-3 hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    {index === 0 && <span className="pill bg-brand-100 text-brand-700">Best price</span>}
                    <span className="font-semibold text-ink">{listing.retailer}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="data text-lg font-bold text-ink">{formatMajorPrice(listing.price, listing.currency)}</span>
                    <Icon name="arrow" className="h-3.5 w-3.5 -rotate-45 text-slate-400" />
                  </div>
                </a>
              ))}
            </div>
          )}
          {response.identified_as && response.web_listings.length === 0 && (
            <p className="mt-3 rounded-xl bg-slate-50 p-3 text-sm text-slate-500">No live listings with a clear price were found for this product just now.</p>
          )}

          {response.results.length > 0 && (
            <div className="mt-6">
              <p className="label-caps text-brand-600">Also in this catalog</p>
              <div className="mt-3 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {response.results.map(({ product, similarity }) => (
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
              </div>
            </div>
          )}

          {!response.identified_as && response.results.length === 0 && (
            <div className="mt-4 rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-500">Couldn&apos;t identify a product in that photo — try a clearer, closer shot.</div>
          )}
        </>
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

      {query.trim().length > 1 && <ComparePrices productName={query.trim()} />}

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
