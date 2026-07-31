import { ProductCard } from "@/components/ui";
import { products } from "@/lib/mock-data";
/** Wishlist groups items the user wants to watch and buy later. */
export default function WishlistPage() {
  return (
    <div>
      <p className="label-caps text-brand-600">Your collection</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Wishlist</h1>
      <p className="mt-2 text-slate-500">You are tracking {products.length} products across 3 stores.</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {products.map((p) => <ProductCard product={p} saved key={p.id} />)}
      </div>
    </div>
  );
}
