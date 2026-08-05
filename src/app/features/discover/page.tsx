import Image from "next/image";
import { FeaturePage } from "@/components/feature-page";
import { Icon } from "@/components/icons";

const RESULTS = [
  { title: "WH-1000XM5", price: "₹24,990", image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=300&q=80" },
  { title: "Air Max 90", price: "₹7,595", image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=300&q=80" }
];

function DiscoverMockup() {
  return (
    <div className="card space-y-4 p-6">
      <div className="shadow-neu-inset-sm flex items-center gap-2 rounded-full px-4 py-2.5 text-sm text-slate-400">
        <Icon name="search" className="h-4 w-4" />
        Wireless headphones under ₹25,000
      </div>
      <div className="grid grid-cols-2 gap-3">
        {RESULTS.map((product) => (
          <div key={product.title} className="shadow-neu-sm overflow-hidden rounded-2xl">
            <div className="relative h-24 w-full">
              <Image src={product.image} alt={product.title} fill sizes="200px" className="object-cover" />
            </div>
            <div className="p-2.5">
              <p className="truncate text-xs font-semibold text-ink">{product.title}</p>
              <p className="data text-xs font-bold text-brand-700">{product.price}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="shadow-neu-sm flex items-center justify-between rounded-xl p-3 text-xs">
        <span className="flex items-center gap-1.5 font-semibold text-brand-600">
          <Icon name="sparkles" className="h-3.5 w-3.5" /> 96% visual match
        </span>
        <span className="text-slate-400">Search by photo</span>
      </div>
    </div>
  );
}

export const metadata = { title: "Discover | AI Shopping Intelligence Platform" };

export default function DiscoverFeaturePage() {
  return (
    <FeaturePage
      name="Discover"
      eyebrow="Discover"
      icon="search"
      title="Find the right product in seconds, not tabs."
      description="Search the live catalog by keyword or by photo, filter down to what matters, and see verified prices from every store you shop - without twenty browser tabs open."
      mockup={<DiscoverMockup />}
      howItWorks={[
        { title: "Search or upload a photo", body: "Type what you're looking for, or upload a picture of a product to find visually similar items in the catalog." },
        { title: "Filter to what matters", body: "Narrow results by category, price range, or retailer until you're only looking at real contenders." },
        { title: "Compare and decide", body: "Open any result to see full specs, price history, and an AI-summarized read on the reviews." }
      ]}
      guide={[
        { title: "Open Discover", body: "Sign in and select \"Discover\" from the sidebar, or use the search bar in the header." },
        { title: "Search by text or photo", body: "Type a product name, brand, or category - or tap \"Upload image\" to search visually using a photo." },
        { title: "Apply filters", body: "Use the category dropdown to narrow results to the kind of product you actually want." },
        { title: "Open a result", body: "Tap any product card to see its full price history, specs, and review summary before deciding." }
      ]}
      faqs={[
        { q: "Which categories can I search?", a: "Discover covers electronics, fashion, wearables, books, and home goods, with more categories added as the catalog grows." },
        { q: "Can I really search by photo?", a: "Yes - upload any product photo and Discover finds visually similar items already indexed in the catalog." },
        { q: "How fresh are the prices shown?", a: "Prices are sourced from approved retailer feeds and refreshed regularly, so what you see closely tracks what you'd pay at checkout." },
        { q: "Can I save a search for later?", a: "Save any individual product to your wishlist from its result card, and Shopping AI will track its price for you." }
      ]}
    />
  );
}
