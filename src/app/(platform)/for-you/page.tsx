"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/icons";
import { authHeaders } from "@/shared/auth/token";
import { supabase } from "@/shared/supabase/client";

type CatalogProduct = { id: string; title: string; brand: string | null; category: string | null; image_url: string | null; currency: string; current_price_minor: number; retailer: string; average_rating: number | null; review_count: number };
type PersonalizedItem = { rank: number; product: CatalogProduct; similarity: number; reason: string };
type PersonalizedResponse = { items: PersonalizedItem[]; signal_counts: Record<string, number> };
type WishlistApiResponse = { id: string; items: { id: string; product: { id: string } }[] }[];

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);

/** Personalized Shopping Recommendation Engine: tracks search/wishlist/purchase/click signals, then generates
 * picks from a pure embeddings-based "taste vector" of the shopper's own behavior - no LLM in this loop. */
export default function ForYouPage() {
  const [signedIn, setSignedIn] = useState(false);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [wishlistId, setWishlistId] = useState<string | null>(null);
  // productId -> that item's wishlist-item id, so an already-wishlisted product can be un-wishlisted
  // (DELETE needs the item id, not the product id) instead of only ever being addable.
  const [wishlisted, setWishlisted] = useState<Map<string, string>>(new Map());
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [personalized, setPersonalized] = useState<PersonalizedResponse | null>(null);
  const [personalizedError, setPersonalizedError] = useState<string | null>(null);
  const [loadingPicks, setLoadingPicks] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSignedIn(!!data.session));
    fetch("/api/v1/products?limit=8").then((r) => r.json()).then(setProducts).catch(() => setProducts([]));
    (async () => {
      try {
        const response = await fetch("/api/v1/wishlists", { headers: await authHeaders() });
        if (!response.ok) return;
        const lists: WishlistApiResponse = await response.json();
        if (lists.length > 0) setWishlistId(lists[0].id);
        const map = new Map<string, string>();
        for (const list of lists) for (const item of list.items) map.set(item.product.id, item.id);
        setWishlisted(map);
      } catch { /* leave wishlisted empty - toggling will still work, just without pre-filled state */ }
    })();
  }, []);

  async function ensureWishlistId(): Promise<string> {
    if (wishlistId) return wishlistId;
    const listResponse = await fetch("/api/v1/wishlists", { headers: await authHeaders() });
    const lists = await listResponse.json();
    if (Array.isArray(lists) && lists.length > 0) { setWishlistId(lists[0].id); return lists[0].id; }
    const createResponse = await fetch("/api/v1/wishlists", { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({}) });
    const created = await createResponse.json();
    setWishlistId(created.id);
    return created.id;
  }

  async function logSearch() {
    if (!query.trim()) return;
    setStatus("Logging search…");
    const response = await fetch("/api/v1/activity/search", { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ query: query.trim() }) });
    setStatus(response.ok ? `Logged search: "${query.trim()}"` : "Could not log that search.");
  }

  async function logClick(product: CatalogProduct) {
    setStatus(`Logging click on ${product.title}…`);
    const response = await fetch("/api/v1/activity/click", { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ productId: product.id }) });
    setStatus(response.ok ? `Logged a click on ${product.title}` : "Could not log that click.");
  }

  async function logPurchase(product: CatalogProduct) {
    setStatus(`Logging purchase of ${product.title}…`);
    const response = await fetch("/api/v1/activity/purchase", { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ productId: product.id }) });
    setStatus(response.ok ? `Logged a purchase of ${product.title}` : "Could not log that purchase.");
  }

  async function toggleWishlist(product: CatalogProduct) {
    const existingItemId = wishlisted.get(product.id);
    try {
      const id = await ensureWishlistId();
      if (existingItemId) {
        setStatus(`Removing ${product.title} from your wishlist…`);
        const response = await fetch(`/api/v1/wishlists/${id}/items/${existingItemId}`, { method: "DELETE", headers: await authHeaders() });
        if (!response.ok) { setStatus("Could not update your wishlist."); return; }
        setWishlisted((current) => { const next = new Map(current); next.delete(product.id); return next; });
        setStatus(`Removed ${product.title} from your wishlist`);
      } else {
        setStatus(`Adding ${product.title} to your wishlist…`);
        const response = await fetch(`/api/v1/wishlists/${id}/items`, { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ productId: product.id }) });
        if (!response.ok) { setStatus("Could not update your wishlist."); return; }
        const created: { id: string } = await response.json();
        setWishlisted((current) => new Map(current).set(product.id, created.id));
        setStatus(`Wishlisted ${product.title}`);
      }
    } catch {
      setStatus("Could not update your wishlist.");
    }
  }

  async function loadPersonalizedPicks() {
    setLoadingPicks(true);
    setPersonalizedError(null);
    try {
      const response = await fetch("/api/v1/recommendations/personalized", { headers: await authHeaders() });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not generate personalized picks.");
      setPersonalized(data);
    } catch (err) {
      setPersonalizedError(err instanceof Error ? err.message : "Something went wrong.");
      setPersonalized(null);
    } finally {
      setLoadingPicks(false);
    }
  }

  if (!signedIn) {
    return (
      <div className="card mx-auto mt-12 max-w-md p-8 text-center">
        <Icon name="trend" className="mx-auto h-8 w-8 text-brand-600" />
        <h1 className="mt-4 text-xl font-bold">Sign in to unlock personalized picks</h1>
        <p className="mt-2 text-sm text-slate-500">This engine builds a taste vector from your own search, wishlist, purchase, and click history - it needs a real signed-in identity to track against.</p>
        <Link href="/auth/sign-in" className="btn-primary mt-6 inline-flex">Sign in</Link>
      </div>
    );
  }

  return (
    <div>
      <p className="label-caps text-brand-600">Personalized for you</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Your taste, as a vector</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">Every search, wishlist add, purchase, and click below is tracked as a real embedding signal. Try a few, then generate your personalized picks - a pure embeddings pipeline with no LLM in the loop.</p>

      <div className="card mt-6 p-6">
        <h2 className="font-bold text-ink">1. Generate some activity</h2>
        <div className="mt-3 flex gap-2">
          <input value={query} onChange={(e) => setQuery(e.target.value)} className="input flex-1" placeholder="Search for something, e.g. wireless headphones" />
          <button onClick={logSearch} className="btn-secondary whitespace-nowrap">Log search</button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {products.map((product) => (
            <article key={product.id} className="rounded-xl border border-slate-200 p-3">
              <p className="label-caps text-brand-600">{product.brand ?? "Unbranded"}</p>
              <p className="mt-1 line-clamp-2 min-h-10 text-sm font-semibold text-ink">{product.title}</p>
              <p className="data mt-1 text-sm font-bold text-ink">{formatPrice(product.current_price_minor, product.currency)}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <button onClick={() => logClick(product)} className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-200">View</button>
                <button onClick={() => toggleWishlist(product)} className={`rounded-lg px-2 py-1 text-xs font-semibold ${wishlisted.has(product.id) ? "bg-rose-100 text-rose-600" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>{wishlisted.has(product.id) ? "Wishlisted ✕" : "Wishlist"}</button>
                <button onClick={() => logPurchase(product)} className="rounded-lg bg-brand-50 px-2 py-1 text-xs font-semibold text-brand-700 hover:bg-brand-100">Buy</button>
                <Link href={`/reviews/${product.id}`} className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-200">
                  Reviews{product.review_count > 0 ? ` (${product.review_count})` : ""}
                </Link>
              </div>
            </article>
          ))}
          {products.length === 0 && <p className="col-span-full text-sm text-slate-400">No catalog products are indexed yet.</p>}
        </div>
        {status && <p className="mt-3 text-xs text-slate-500">{status}</p>}
      </div>

      <div className="card mt-6 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-ink">2. Your personalized picks</h2>
          <button onClick={loadPersonalizedPicks} className="btn-primary" disabled={loadingPicks}>{loadingPicks ? "Building your taste vector…" : "Get personalized picks"}</button>
        </div>

        {personalizedError && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{personalizedError}</div>}

        {personalized && (
          <>
            <p className="mt-4 text-xs text-slate-500">Built from {personalized.signal_counts.search ?? 0} searches · {personalized.signal_counts.wishlist ?? 0} wishlisted · {personalized.signal_counts.purchase ?? 0} purchases · {personalized.signal_counts.click ?? 0} clicks</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {personalized.items.map((item) => (
                <article key={item.product.id} className="card overflow-hidden p-4">
                  <div className="flex items-center gap-2">
                    <span className="pill bg-brand-100 text-brand-700">#{item.rank}</span>
                    <span className="data text-xs text-slate-500">{Math.round(item.similarity * 100)}% match</span>
                  </div>
                  <h3 className="mt-2 line-clamp-2 min-h-10 text-sm font-semibold text-ink">{item.product.title}</h3>
                  <span className="data mt-2 block text-lg font-bold text-ink">{formatPrice(item.product.current_price_minor, item.product.currency)}</span>
                  <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">{item.reason}</p>
                </article>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
