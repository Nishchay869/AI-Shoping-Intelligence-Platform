"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { ComparePrices } from "@/components/compare-prices";
import { Icon } from "@/components/icons";
import { authHeaders } from "@/shared/auth/token";
import { useCurrentUser } from "@/shared/auth/use-current-user";

type CatalogProduct = {
  id: string;
  title: string;
  brand: string | null;
  category: string | null;
  image_url: string | null;
  currency: string;
  current_price_minor: number;
  retailer: string;
  average_rating: number | null;
  review_count: number;
};

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);
const RETAILER_LABELS: Record<string, string> = { amazon: "Amazon", flipkart: "Flipkart", myntra: "Myntra" };

/** Product detail page: real catalog data (title, price, retailer) plus two genuinely live features -
 * cross-retailer price comparison (Tavily + Gemini web search) and an AI review summary - rather than an
 * invented price-history chart this app has no real time series to back yet. */
export default function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const user = useCurrentUser();
  const [product, setProduct] = useState<CatalogProduct | null>(null);
  const [notFoundState, setNotFoundState] = useState(false);
  const [wishlistId, setWishlistId] = useState<string | null>(null);
  const [wishlistItemId, setWishlistItemId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/v1/products/${id}`)
      .then(async (response) => {
        if (!response.ok) { if (!cancelled) setNotFoundState(true); return; }
        const data = await response.json();
        if (!cancelled) setProduct(data);
      })
      .catch(() => { if (!cancelled) setNotFoundState(true); });
    return () => { cancelled = true; };
  }, [id]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/v1/wishlists", { headers: await authHeaders() });
        if (!response.ok || cancelled) return;
        const lists: { id: string; items: { id: string; product: { id: string } }[] }[] = await response.json();
        if (lists.length > 0) setWishlistId(lists[0].id);
        for (const list of lists) {
          const match = list.items.find((item) => item.product.id === id);
          if (match) { setWishlistId(list.id); setWishlistItemId(match.id); break; }
        }
      } catch { /* leave un-wishlisted - the save button still works, just without pre-filled state */ }
    })();
    return () => { cancelled = true; };
  }, [id, user]);

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

  async function toggleWishlist() {
    if (!user) { setStatus("Sign in to save items to your wishlist."); return; }
    setSaving(true);
    setStatus(null);
    try {
      if (wishlistItemId && wishlistId) {
        const response = await fetch(`/api/v1/wishlists/${wishlistId}/items/${wishlistItemId}`, { method: "DELETE", headers: await authHeaders() });
        if (response.ok) { setWishlistItemId(null); setStatus("Removed from your wishlist."); }
        else setStatus("Could not update your wishlist.");
      } else {
        const id_ = await ensureWishlistId();
        const response = await fetch(`/api/v1/wishlists/${id_}/items`, { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ productId: id }) });
        if (response.ok) { const created: { id: string } = await response.json(); setWishlistItemId(created.id); setStatus("Saved to your wishlist."); }
        else setStatus("Could not save this item.");
      }
    } catch {
      setStatus("Could not update your wishlist.");
    } finally {
      setSaving(false);
    }
  }

  if (notFoundState) notFound();
  if (!product) return <div className="card p-10 text-center text-sm text-slate-500">Loading product…</div>;

  return (
    <div>
      <Link href="/search" className="inline-flex items-center text-sm font-semibold text-slate-500 hover:text-brand-700">← Back to discover</Link>
      <div className="mt-5 grid gap-8 lg:grid-cols-2">
        <div className="card relative h-[360px] overflow-hidden bg-slate-100">
          {product.image_url && <Image className="object-cover" src={product.image_url} alt={product.title} fill priority sizes="(max-width: 1024px) 100vw, 50vw" />}
        </div>
        <section>
          <p className="label-caps text-brand-600">{product.brand ?? "Unbranded"} · {product.category ?? "Uncategorized"}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-ink">{product.title}</h1>
          <Link href={`/reviews/${product.id}`} className="mt-3 flex items-center gap-1 text-sm text-slate-500 hover:text-brand-700">
            {product.review_count > 0 ? <><span className="data">★ {product.average_rating ?? "n/a"}</span> · {product.review_count.toLocaleString()} reviews</> : "No reviews yet"} · Sold on {RETAILER_LABELS[product.retailer] ?? product.retailer}
          </Link>
          <div className="mt-6 flex items-end gap-3">
            <span className="data text-4xl font-extrabold text-ink">{formatPrice(product.current_price_minor, product.currency)}</span>
          </div>
          <div className="mt-6">
            <button onClick={toggleWishlist} disabled={saving} className={wishlistItemId ? "btn-secondary" : "btn-primary"}>
              <Icon name="heart" className={`mr-2 h-4 w-4 ${wishlistItemId ? "fill-rose-500 text-rose-500" : ""}`} />
              {saving ? "Saving…" : wishlistItemId ? "Remove from wishlist" : "Save to wishlist"}
            </button>
            {status && <p className="mt-2 text-xs text-slate-500">{status}</p>}
          </div>
          <Link href={`/reviews/${product.id}`} className="mt-6 inline-flex items-center gap-1 text-sm font-bold text-brand-700 hover:underline">
            See what reviewers say <Icon name="arrow" className="h-4 w-4" />
          </Link>
          <ComparePrices productName={product.title} />
        </section>
      </div>
    </div>
  );
}
