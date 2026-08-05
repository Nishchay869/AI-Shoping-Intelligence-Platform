"use client";
import Link from "next/link";
import Image from "next/image";
import { ProductCard } from "@/components/ui";
import { Icon, type IconName } from "@/components/icons";
import { products, formatPrice } from "@/lib/mock-data";
import { displayNameFor, useCurrentUser } from "@/shared/auth/use-current-user";

const drops = products.filter((p) => p.trend === "down");

/** Dashboard summarizes tracked offers and routes users to their most useful next action. */
export default function DashboardPage() {
  const name = displayNameFor(useCurrentUser());
  const stats: { label: string; value: string; icon: IconName; emphasize?: boolean }[] = [
    { label: "WISHLIST ITEMS", value: "12", icon: "heart" },
    { label: "ACTIVE ALERTS", value: `${drops.length}`, icon: "trend" },
    { label: "POTENTIAL SAVINGS", value: "₹8,400", icon: "sparkles", emphasize: true },
    { label: "TRACKED STORES", value: "3", icon: "home" }
  ];

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold text-ink">Welcome back{name && `, ${name}`}</h1>
        <div className="mt-2 flex items-center gap-2">
          <span className="flex h-2 w-2 animate-pulse rounded-full bg-brand-600" />
          <p className="text-slate-500">{drops.length} price drops this week on items you&apos;re watching</p>
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
            <h2 className="text-lg font-bold text-ink">Recent price drops</h2>
            <Link href="/wishlist" className="label-caps text-brand-600 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-slate-100">
            {drops.map((p) => (
              <Link key={p.id} href={`/products/${p.id}`} className="group flex items-center gap-4 p-4 transition-colors hover:bg-slate-50 sm:p-6">
                <Image src={p.image} width={64} height={64} alt="" className="h-16 w-16 flex-shrink-0 rounded-lg border border-slate-100 object-cover" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-ink group-hover:text-brand-700">{p.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{p.retailer}</p>
                </div>
                <div className="text-right">
                  <p className="data text-xs text-slate-400 line-through">{formatPrice(p.previousPrice, p.currency)}</p>
                  <div className="mt-1 flex items-center justify-end gap-2">
                    <span className="pill bg-brand-50 text-brand-700">{Math.round((1 - p.currentPrice / p.previousPrice) * 100)}% off</span>
                    <p className="data font-bold text-brand-700">{formatPrice(p.currentPrice, p.currency)}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <aside className="space-y-6">
          <div className="card p-6">
            <div className="mb-4 flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-100 text-brand-700"><Icon name="sparkles" className="h-4 w-4" /></span>
              <h3 className="font-bold text-ink">Your AI picks</h3>
            </div>
            <div className="mb-6 space-y-3">
              {products.slice(0, 2).map((p) => (
                <div key={p.id} className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
                  <Image src={p.image} width={48} height={48} alt="" className="h-12 w-12 rounded-lg border border-slate-200 object-cover" />
                  <p className="truncate text-sm font-bold text-ink">{p.title}</p>
                </div>
              ))}
            </div>
            <Link href="/recommendations" className="btn-primary label-caps w-full">View all recommendations</Link>
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

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-ink">Recently viewed</h2>
          <Link href="/search" className="label-caps text-brand-600 hover:underline">Discover more</Link>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {products.map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      </section>
    </div>
  );
}
