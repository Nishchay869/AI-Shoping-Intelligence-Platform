"use client";
import { useState } from "react";
import { Icon } from "@/components/icons";

type PriceListing = { retailer: string; price: number; currency: string; url: string };

const formatPrice = (price: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(price);

/** Live cross-retailer price comparison: searches the web for this product and extracts real listings
 * (retailer, price, source link) via the FastAPI backend - not from the app's own catalog. */
export function ComparePrices({ productName }: { productName: string }) {
  const [listings, setListings] = useState<PriceListing[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadComparison() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/products/compare-prices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ productName })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not compare prices right now.");
      setListings(data.listings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card mt-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-bold text-ink">Compare prices</h2>
          <p className="mt-1 text-sm text-slate-500">Live prices found across the web for this exact product.</p>
        </div>
        <button onClick={loadComparison} disabled={loading} className="btn-secondary">
          {loading ? "Searching the web…" : listings ? "Refresh prices" : "Compare prices"}
        </button>
      </div>

      {error && <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

      {listings && listings.length === 0 && !error && (
        <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-500">No live listings with a clear price were found for this product just now.</p>
      )}

      {listings && listings.length > 0 && (
        <div className="mt-4 divide-y divide-slate-100">
          {listings.map((listing, index) => (
            <a key={`${listing.retailer}-${index}`} href={listing.url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between gap-4 py-3 hover:bg-slate-50">
              <div className="flex items-center gap-2">
                {index === 0 && <span className="pill bg-brand-100 text-brand-700">Best price</span>}
                <span className="font-semibold text-ink">{listing.retailer}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="data text-lg font-bold text-ink">{formatPrice(listing.price, listing.currency)}</span>
                <Icon name="arrow" className="h-3.5 w-3.5 -rotate-45 text-slate-400" />
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
