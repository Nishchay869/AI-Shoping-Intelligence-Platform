import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { ComparePrices } from "@/components/compare-prices";
import { Icon } from "@/components/icons";
import { formatPrice, products } from "@/lib/mock-data";

/** Product detail page presents an explainable price trend and tracking controls. */
export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = products.find((p) => p.id === id);
  if (!product) notFound();
  const points = [70, 58, 64, 46, 54, 39, 31];
  const discount = Math.round((1 - product.currentPrice / product.previousPrice) * 100);

  return (
    <div>
      <Link href="/search" className="inline-flex items-center text-sm font-semibold text-slate-500 hover:text-brand-700">← Back to discover</Link>
      <div className="mt-5 grid gap-8 lg:grid-cols-2">
        <div className="card relative h-[360px] overflow-hidden">
          <Image className="object-cover" src={product.image} alt={product.title} fill priority sizes="(max-width: 1024px) 100vw, 50vw" />
        </div>
        <section>
          <p className="label-caps text-brand-600">{product.brand} · {product.category}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-ink">{product.title}</h1>
          <Link href={`/reviews/${product.id}`} className="mt-3 flex items-center gap-1 text-sm text-slate-500 hover:text-brand-700">
            <span className="data">★ {product.rating}</span> · {product.reviews.toLocaleString()} reviews · Verified on {product.retailer}
          </Link>
          <div className="mt-6 flex items-end gap-3">
            <span className="data text-4xl font-extrabold text-ink">{formatPrice(product.currentPrice)}</span>
            <span className="data mb-1 text-sm text-slate-400 line-through">{formatPrice(product.previousPrice)}</span>
            {discount > 0 && <span className="pill mb-1 bg-brand-50 text-brand-700">{discount}% lower</span>}
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <button className="btn-primary"><Icon name="bell" className="mr-2 h-4 w-4" />Track price</button>
            <button className="btn-secondary"><Icon name="heart" className="mr-2 h-4 w-4" />Save item</button>
          </div>
          <div className="card mt-6 p-6">
            <div className="flex justify-between">
              <div>
                <h2 className="font-bold text-ink">Price history</h2>
                <p className="mt-1 text-sm text-slate-500">Lowest price in 90 days: <span className="data">{formatPrice(product.currentPrice)}</span></p>
              </div>
              <span className="pill bg-brand-50 text-brand-700">Good time to buy</span>
            </div>
            <div className="mt-8 flex h-28 items-end gap-2">
              {points.map((height, index) => <div key={index} className="flex-1 rounded-t bg-brand-100" style={{ height: `${height}%` }} />)}
            </div>
            <div className="mt-2 flex justify-between text-xs text-slate-400">
              <span>90 days ago</span><span>Today</span>
            </div>
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
