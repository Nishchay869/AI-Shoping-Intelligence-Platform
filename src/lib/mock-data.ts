export type Product = { id: string; title: string; brand: string; image: string; category: string; currentPrice: number; previousPrice: number; currency: string; rating: number; reviews: number; retailer: string; trend: "down" | "up"; }; 

export const products: Product[] = [
  { id: "sony-wh-1000xm5", title: "WH-1000XM5 Wireless Headphones", brand: "Sony", image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=700&q=80", category: "Audio", currentPrice: 24990, previousPrice: 29990, currency: "₹", rating: 4.8, reviews: 2841, retailer: "Amazon", trend: "down" },
  { id: "apple-watch-se", title: "Watch SE GPS 40mm", brand: "Apple", image: "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?auto=format&fit=crop&w=700&q=80", category: "Wearables", currentPrice: 27900, previousPrice: 27900, currency: "₹", rating: 4.7, reviews: 1920, retailer: "Flipkart", trend: "up" },
  { id: "nike-air-max", title: "Air Max 90 Lifestyle Shoes", brand: "Nike", image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80", category: "Fashion", currentPrice: 7595, previousPrice: 9995, currency: "₹", rating: 4.6, reviews: 731, retailer: "Myntra", trend: "down" },
  { id: "kindle-paperwhite", title: "Kindle Paperwhite 16 GB", brand: "Amazon", image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=700&q=80", category: "Electronics", currentPrice: 14999, previousPrice: 16999, currency: "₹", rating: 4.7, reviews: 815, retailer: "Amazon", trend: "down" }
];
export const formatPrice = (price: number, currency = "₹") => `${currency}${new Intl.NumberFormat("en-IN").format(price)}`;
