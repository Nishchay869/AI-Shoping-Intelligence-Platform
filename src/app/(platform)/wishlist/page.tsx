"use client";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
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
type WishlistItem = { id: string; product: CatalogProduct; target_price_minor: number | null };
type Wishlist = { id: string; name: string; items: WishlistItem[] };

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);

const RETAILER_LABELS: Record<string, string> = { amazon: "Amazon", flipkart: "Flipkart", myntra: "Myntra" };
const RETAILER_ORDER = ["amazon", "flipkart", "myntra"];

/** Wishlist groups items the user wants to watch and buy later - backed by the real /api/v1/wishlists
 * endpoint, one row per (wishlist, product). Items are grouped by the product's own retailer field
 * (set at catalog-ingestion time) into an Amazon section, a Flipkart section, etc. - there's no live
 * account import from those stores here, just a per-item source label already on the product. */
export default function WishlistPage() {
  const user = useCurrentUser();
  const [wishlists, setWishlists] = useState<Wishlist[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/v1/wishlists", { headers: await authHeaders() });
        const data = await response.json();
        if (cancelled) return;
        if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not load your wishlist.");
        setWishlists(data);
      } catch (err) {
        if (!cancelled) { setError(err instanceof Error ? err.message : "Could not load your wishlist."); setWishlists([]); }
      }
    })();
    return () => { cancelled = true; };
  }, [user]);

  async function removeItem(wishlistId: string, itemId: string) {
    setRemovingId(itemId);
    try {
      const response = await fetch(`/api/v1/wishlists/${wishlistId}/items/${itemId}`, { method: "DELETE", headers: await authHeaders() });
      if (!response.ok) throw new Error("Could not remove that item.");
      setWishlists((current) => current?.map((list) => (list.id === wishlistId ? { ...list, items: list.items.filter((item) => item.id !== itemId) } : list)) ?? current);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove that item.");
    } finally {
      setRemovingId(null);
    }
  }

  if (!user) {
    return (
      <div className="card mx-auto mt-12 max-w-md p-8 text-center">
        <Icon name="heart" className="mx-auto h-8 w-8 text-brand-600" />
        <h1 className="mt-4 text-xl font-bold">Sign in to see your wishlist</h1>
        <p className="mt-2 text-sm text-slate-500">Your saved items and target prices are tied to your account.</p>
        <Link href="/auth/sign-in" className="btn-primary mt-6 inline-flex">Sign in</Link>
      </div>
    );
  }

  const allItems = wishlists?.flatMap((list) => list.items.map((item) => ({ ...item, wishlistId: list.id }))) ?? [];
  const byRetailer = new Map<string, typeof allItems>();
  for (const item of allItems) {
    const key = item.product.retailer;
    byRetailer.set(key, [...(byRetailer.get(key) ?? []), item]);
  }
  const retailerKeys = [...RETAILER_ORDER.filter((code) => byRetailer.has(code)), ...[...byRetailer.keys()].filter((code) => !RETAILER_ORDER.includes(code))];

  return (
    <div>
      <p className="label-caps text-brand-600">Your collection</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Wishlist</h1>
      <p className="mt-2 text-slate-500">
        {wishlists === null ? "Loading…" : allItems.length === 0 ? "Nothing saved yet." : `Tracking ${allItems.length} product${allItems.length === 1 ? "" : "s"} across ${retailerKeys.length} store${retailerKeys.length === 1 ? "" : "s"}.`}
      </p>

      {error && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {wishlists !== null && allItems.length === 0 && !error && (
        <div className="card mt-8 p-8 text-center">
          <Icon name="heart" className="mx-auto h-8 w-8 text-slate-300" />
          <p className="mt-3 text-sm text-slate-500">You haven&apos;t saved anything yet. Browse the catalog and tap the heart icon on a product to track its price here.</p>
          <Link href="/for-you" className="btn-secondary mt-4 inline-flex">Browse products</Link>
        </div>
      )}

      {retailerKeys.map((retailer) => (
        <section key={retailer} className="mt-8">
          <h2 className="mb-4 text-lg font-bold text-ink">{RETAILER_LABELS[retailer] ?? retailer}</h2>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {byRetailer.get(retailer)!.map((item) => (
              <article key={item.id} className="card group overflow-hidden">
                <div className="relative h-44 overflow-hidden bg-slate-100">
                  {item.product.image_url && (
                    <Image src={item.product.image_url} alt={item.product.title} fill sizes="(max-width: 640px) 100vw, (max-width: 1280px) 50vw, 25vw" className="object-cover transition-transform duration-500 ease-out group-hover:scale-110" />
                  )}
                  <button
                    onClick={() => removeItem(item.wishlistId, item.id)}
                    disabled={removingId === item.id}
                    aria-label="Remove from wishlist"
                    className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-white/90 text-slate-700 shadow-neu-sm backdrop-blur transition-transform duration-150 hover:scale-110 active:scale-90 disabled:opacity-50"
                  >
                    <Icon name="heart" className="h-4 w-4 fill-rose-500 text-rose-500" />
                  </button>
                </div>
                <div className="p-4">
                  <p className="label-caps text-brand-600">{item.product.brand ?? "Unbranded"} · {RETAILER_LABELS[item.product.retailer] ?? item.product.retailer}</p>
                  <Link href={`/products/${item.product.id}`} className="mt-1 block line-clamp-2 min-h-10 text-sm font-semibold transition-colors hover:text-brand-600">
                    {item.product.title}
                  </Link>
                  <div className="mt-3 flex items-end justify-between">
                    <span className="data text-lg font-bold text-ink">{formatPrice(item.product.current_price_minor, item.product.currency)}</span>
                    {item.product.average_rating !== null && <span className="data text-xs text-slate-500">★ {item.product.average_rating}</span>}
                  </div>
                  {item.target_price_minor !== null && (
                    <p className="mt-2 text-xs text-slate-500">Alert below {formatPrice(item.target_price_minor, item.product.currency)}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
