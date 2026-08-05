import type { Metadata } from "next";
import { JetBrains_Mono, Manrope } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "AI Shopping Intelligence Platform",
  description: "Track prices and make better buying decisions."
};

/** Root document shell shared by every route.
 *
 * Reading the per-request nonce here (set by middleware.ts) is required for the nonce-based CSP to
 * work at all: Next.js only threads a script nonce through - and only re-renders per request - for
 * routes it treats as dynamic. Without touching a dynamic API like `headers()` somewhere in the tree,
 * pages with no other dynamic dependency (most of this app) get statically prerendered *once* at
 * build time, baking in whatever nonce existed then. Every subsequent request gets a fresh nonce from
 * middleware, and the CSP header only allows scripts tagged with *that* nonce - so the stale
 * build-time one gets rejected, hydration fails, and the page silently loses all interactivity
 * (verified: this broke the sign-in form itself, not just a lint-level concern). Calling `headers()`
 * opts every route in this tree into dynamic rendering, keeping the nonce fresh on every request. */
export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  await headers();
  return <html lang="en" className={`${manrope.variable} ${jetbrainsMono.variable}`}><body>{children}</body></html>;
}
