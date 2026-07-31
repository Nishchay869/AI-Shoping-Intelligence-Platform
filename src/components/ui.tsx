"use client";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { Icon } from "./icons";
import { formatPrice, type Product } from "@/lib/mock-data";

/** Reusable product card used by search, dashboard recommendations, and wishlist. */
export function ProductCard({ product, saved = false }: { product: Product; saved?: boolean }) { const [isSaved, setSaved] = useState(saved); const discount = Math.round((1 - product.currentPrice / product.previousPrice) * 100); return <article className="card overflow-hidden"><div className="relative h-44 bg-slate-100"><Image src={product.image} alt={product.title} fill sizes="(max-width: 640px) 100vw, (max-width: 1280px) 50vw, 25vw" className="object-cover" /><button onClick={() => setSaved(!isSaved)} aria-label={isSaved ? "Remove from wishlist" : "Add to wishlist"} className="absolute right-3 top-3 rounded-full bg-white p-2 text-slate-700 shadow-sm"><Icon name="heart" className={`h-4 w-4 ${isSaved ? "fill-rose-500 text-rose-500" : ""}`} /></button></div><div className="p-4"><p className="label-caps text-brand-600">{product.brand} · {product.retailer}</p><Link href={`/products/${product.id}`} className="mt-1 block line-clamp-2 min-h-10 text-sm font-semibold hover:text-brand-600">{product.title}</Link><div className="mt-3 flex items-end justify-between"><div className="flex items-center gap-2"><span className="data text-lg font-bold text-ink">{formatPrice(product.currentPrice, product.currency)}</span>{discount > 0 && <span className="pill bg-brand-50 text-brand-700">↓ {discount}%</span>}</div><span className="data text-xs text-slate-500">★ {product.rating}</span></div></div></article>; }
