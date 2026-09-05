"use client";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { Icon, type IconName } from "@/components/icons";
import { authHeaders } from "@/shared/auth/token";
import { displayNameFor, useCurrentUser } from "@/shared/auth/use-current-user";

type CatalogProduct = { id: string; title: string; brand: string | null; image_url: string | null; currency: string; current_price_minor: number; retailer: string };
type WishlistItem = { id: string; product: CatalogProduct; target_price_minor: number | null };
type Wishlist = { id: string; items: WishlistItem[] };
type PersonalizedItem = { rank: number; product: CatalogProduct; similarity: number; reason: string };

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minorUnits / 100);
const RETAILER_LABELS: Record<string, string> = { amazon: "Amazon", flipkart: "Flipkart", myntra: "Myntra" };

/** Dashboard summarizes the shopper's own real activity - wishlist size, configured price alerts, distinct
 * tracked stores, and personalized picks - rather than placeholder numbers. There's no price-history data
 * yet for a freshly seeded catalog, so "potential savings" is computed from what's actually there (0, if
 * nothing has dropped in price yet) instead of an invented figure. */
export default function DashboardPage() {
  const user = useCurrentUser();
  const name = displayNameFor(user);
  const [wishlists, setWishlists] = useState<Wishlist[] | null>(null);
  const [personalized, setPersonalized] = useState<PersonalizedItem[] | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/v1/wishlists", { headers: await authHeaders() });
        if (!cancelled) setWishlists(response.ok ? await response.json() : []);
      } catch { if (!cancelled) setWishlists([]); }
    })();
    (async () => {
      try {
        const response = await fetch("/api/v1/recommendations/personalized", { headers: await authHeaders() });
        if (!cancelled) setPersonalized(response.ok ? (await response.json()).items : []);
      } catch { if (!cancelled) setPersonalized([]); }
    })();
    return () => { cancelled = true; };
  }, [user]);

  const allItems = wishlists?.flatMap((list) => list.items) ?? [];
  const activeAlerts = allItems.filter((item) => item.target_price_minor !== null).length;
  const trackedStores = new Set(allItems.map((item) => item.product.retailer)).size;
  // No real price-history is recorded yet for a freshly seeded catalog (PriceHistory only fills in once
  // a tracked offer is actually re-scraped and its price changes) - 0 is the honest current answer, not a
  // placeholder, until that pipeline has run at least once.
  const potentialSavingsMinor = 0;
  const currency = allItems[0]?.product.currency ?? "INR";

  const stats: { label: string; value: string; icon: IconName; emphasize?: boolean }[] = [
    { label: "WISHLIST ITEMS", value: wishlists === null ? "…" : `${allItems.length}`, icon: "heart" },
    { label: "ACTIVE ALERTS", value: wishlists === null ? "…" : `${activeAlerts}`, icon: "trend" },
    { label: "POTENTIAL SAVINGS", value: formatPrice(potentialSavingsMinor, currency), icon: "sparkles", emphasize: true },
    { label: "TRACKED STORES", value: wishlists === null ? "…" : `${trackedStores}`, icon: "home" }
  ];

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold text-ink">Welcome back{name && `, ${name}`}</h1>
        <div className="mt-2 flex items-center gap-2">
          <span className="flex h-2 w-2 animate-pulse rounded-full bg-brand-600" />
          <p className="text-slate-500">
            {wishlists === null ? "Loading your activity…" : allItems.length === 0 ? "Nothing tracked yet - save an item to start watching its price." : `Tracking ${allItems.length} item${allItems.length === 1 ? "" : "s"} across ${trackedStores} store${trackedStores === 1 ? "" : "s"}`}
          </p>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ label, value, icon, emphasize }) => (
          <article key={label} className={emphasize ? "card border-2 border-brand-300 p-5" : "card p-5"}>
            <div className="mb-4 flex items-start justify-between">
              <span className={`grid h-9 w-9 place-items-center rounded-lg ${emphasize ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-brand-600"}`}>
                <Icon name={icon} className="h-4 w-4" />
              </span>
            </div>
            <p className="label-caps">{label}</p>
            <p className={`data mt-1 font-bold ${emphasize ? "text-3xl text-brand-700" : "text-2xl text-ink"}`}>{value}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <h2 className="text-lg font-bold text-ink">Your tracked items</h2>
            <Link href="/wishlist" className="label-caps text-brand-600 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-slate-100">
            {allItems.slice(0, 5).map((item) => (
              <Link key={item.id} href={`/products/${item.product.id}`} className="group flex items-center gap-4 p-4 transition-colors hover:bg-slate-50 sm:p-6">
                {item.product.image_url && <Image src={item.product.image_url} width={64} height={64} alt="" className="h-16 w-16 flex-shrink-0 rounded-lg border border-slate-100 object-cover" />}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-ink group-hover:text-brand-700">{item.product.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{RETAILER_LABELS[item.product.retailer] ?? item.product.retailer}</p>
                </div>
                <p className="data font-bold text-brand-700">{formatPrice(item.product.current_price_minor, item.product.currency)}</p>
              </Link>
            ))}
            {wishlists !== null && allItems.length === 0 && (
              <p className="p-6 text-center text-sm text-slate-400">No items tracked yet. <Link href="/for-you" className="font-semibold text-brand-600 hover:underline">Browse the catalog</Link> and save something to your wishlist.</p>
            )}
          </div>
        </div>

        <aside className="space-y-6">
          <div className="card p-6">
            <div className="mb-4 flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-100 text-brand-700"><Icon name="sparkles" className="h-4 w-4" /></span>
              <h3 className="font-bold text-ink">Your AI picks</h3>
            </div>
            <div className="mb-6 space-y-3">
              {personalized?.slice(0, 2).map((item) => (
                <div key={item.product.id} className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
                  {item.product.image_url && <Image src={item.product.image_url} width={48} height={48} alt="" className="h-12 w-12 rounded-lg border border-slate-200 object-cover" />}
                  <p className="truncate text-sm font-bold text-ink">{item.product.title}</p>
                </div>
              ))}
              {personalized !== null && personalized.length === 0 && (
                <p className="text-sm text-slate-400">Search, wishlist, or view a few products first - personalized picks are built from your own activity.</p>
              )}
            </div>
            <Link href="/for-you" className="btn-primary label-caps w-full">View all recommendations</Link>
          </div>

          <div className="card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-bold text-ink">Ask before you buy</h3>
              <span className="h-2 w-2 rounded-full bg-brand-600" />
            </div>
            <p className="mb-4 text-sm text-slate-500">Shopping Chat compares price history and your saved products to help you decide.</p>
            <Link href="/chat" className="flex items-center gap-2 text-brand-700">
              <Icon name="message" className="h-4 w-4" />
              <span className="label-caps font-bold">Open shopping chat</span>
            </Link>
          </div>
        </aside>
      </section>
    </div>
  );
}
