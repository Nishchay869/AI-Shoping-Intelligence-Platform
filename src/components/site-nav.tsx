"use client";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { Icon, type IconName } from "./icons";

// The four feature links point at public /features pages (description, how-it-works, usage guide,
// FAQ) rather than straight at the gated app route - a visitor who isn't signed in yet gets a chance
// to learn what the feature does before being asked to sign in. Home and Contact Us are fully public
// pages already, so they just link straight there - no sign-in wall involved either way.
const NAV_ITEMS: { href: string; label: string; icon: IconName }[] = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/features/discover", label: "Discover", icon: "search" },
  { href: "/features/ai-picks", label: "AI Picks", icon: "sparkles" },
  { href: "/features/shopping-chat", label: "Shopping Chat", icon: "message" },
  { href: "/features/receipt-scanner", label: "Receipt Scanner", icon: "receipt" },
  { href: "/contact", label: "Contact Us", icon: "mail" }
];

/** Public marketing navbar, shared by the landing page and every standalone marketing/legal page.
 * A floating pill rather than an edge-to-edge bar, with an entrance animation that plays once per
 * page load and an animated underline on each link's hover state.
 *
 * Below the `lg` breakpoint the nav links have nowhere to go (there's no room in the pill for them),
 * so a visitor on mobile used to see only the logo and a bare "Sign in" button - every other nav
 * destination was simply invisible, not just collapsed. A hamburger toggle now holds the same links
 * (plus sign in) in a dropdown instead of dropping them. */
export function SiteNav() {
  const [open, setOpen] = useState(false);

  return (
    <div className="animate-nav-in fixed inset-x-0 top-4 z-50 px-4 sm:top-5 sm:px-6">
      <nav className="nav-glass mx-auto flex h-16 max-w-7xl items-center justify-between rounded-full pl-4 pr-3 sm:pl-6 sm:pr-4">
        <Link href="/" className="group flex shrink-0 items-center gap-2.5" onClick={() => setOpen(false)}>
          <Image
            src="/logo-icon.png"
            alt=""
            width={36}
            height={36}
            className="h-9 w-9 transition-transform duration-500 ease-elastic group-hover:-rotate-6 group-hover:scale-110"
            priority
          />
          {/* "AI SIP" (AI Shopping Intelligence Platform) - the wordmark next to the logo. A shimmering
           * gradient fill sweeps through it continuously, like light gliding across water, and a tiny
           * caps subtitle underneath reads it out in full on the first pass. */}
          <span className="hidden sm:flex sm:flex-col sm:leading-none">
            <span
              className="animate-text-shimmer bg-gradient-to-r from-brand-700 via-violet-500 via-40% to-brand-600 bg-clip-text text-xl font-extrabold tracking-tight text-transparent"
              style={{ backgroundSize: "200% auto" }}
            >
              AI SIP
            </span>
            <span className="label-caps mt-1 text-[9px] tracking-[0.22em] text-brand-600/60">Shopping Intelligence</span>
          </span>
        </Link>

        <div className="hidden items-center lg:flex">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group relative flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-2 text-sm font-medium text-slate-600 transition-all duration-500 ease-elastic hover:scale-105 hover:bg-white/60 hover:text-brand-700 hover:shadow-[0_6px_18px_-6px_rgba(79,70,229,0.45)] active:scale-95 xl:px-4"
            >
              <Icon name={item.icon} className="h-4 w-4 text-slate-400 transition-all duration-500 ease-elastic group-hover:scale-125 group-hover:-rotate-6 group-hover:text-brand-600" />
              {item.label}
              <span className="absolute inset-x-3 -bottom-0.5 h-0.5 origin-left scale-x-0 rounded-full bg-gradient-to-r from-brand-500 to-violet-500 transition-transform duration-500 ease-elastic group-hover:scale-x-100 xl:inset-x-4" />
            </Link>
          ))}
        </div>

        <Link href="/auth/sign-in" className="btn-primary hidden shrink-0 rounded-full px-6 ring-1 ring-white/40 transition-transform duration-500 ease-elastic hover:scale-105 active:scale-95 lg:inline-flex">Sign in</Link>

        <button
          type="button"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full text-slate-600 transition-all duration-500 ease-elastic hover:scale-110 hover:bg-white/50 active:scale-90 lg:hidden"
        >
          <Icon name={open ? "x" : "menu"} className="h-5 w-5" />
        </button>
      </nav>

      {open && (
        <div className="nav-glass-panel animate-scale-in mx-auto mt-2 max-w-7xl origin-top rounded-3xl p-3 lg:hidden">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-600 transition-all duration-500 ease-elastic hover:scale-[1.02] hover:bg-white/60 hover:text-brand-700"
            >
              <Icon name={item.icon} className="h-4 w-4 text-slate-400" />
              {item.label}
            </Link>
          ))}
          <Link href="/auth/sign-in" onClick={() => setOpen(false)} className="btn-primary mt-2 w-full justify-center rounded-2xl">Sign in</Link>
        </div>
      )}
    </div>
  );
}
