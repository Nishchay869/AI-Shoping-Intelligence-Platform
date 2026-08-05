"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AssistantWidget } from "./assistant-widget";
import { Icon, type IconName } from "./icons";
import { clearToken } from "@/shared/auth/token";
import { displayNameFor, initialsFor } from "@/shared/auth/use-current-user";
import { supabase } from "@/shared/supabase/client";
import type { User } from "@supabase/supabase-js";

const navigation: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Overview", icon: "home" },
  { href: "/search", label: "Discover", icon: "search" },
  { href: "/recommendations", label: "AI Picks", icon: "sparkles" },
  { href: "/for-you", label: "For You", icon: "trend" },
  { href: "/wishlist", label: "Wishlist", icon: "heart" },
  { href: "/chat", label: "Shopping Chat", icon: "message" },
  { href: "/receipts", label: "Receipt Scanner", icon: "receipt" },
  { href: "/profile", label: "Profile", icon: "user" }
];

/** Nav links with a sliding active-state indicator that reads as "pressed into" the sidebar surface.
 * Rendered separately for the desktop sidebar and mobile drawer so each measures its own DOM - sharing
 * one ref map across both would let whichever renders last clobber the other's measurement. */
function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const path = usePathname();
  const itemRefs = useRef<Record<string, HTMLAnchorElement | null>>({});
  const [indicator, setIndicator] = useState<{ top: number; height: number } | null>(null);

  useEffect(() => {
    const el = itemRefs.current[path];
    if (el) setIndicator({ top: el.offsetTop, height: el.offsetHeight });
  }, [path]);

  return (
    <nav className="relative flex-1 space-y-1 px-3">
      {indicator && (
        <span
          aria-hidden
          style={{ top: indicator.top, height: indicator.height }}
          className="surface-pressed absolute inset-x-3 rounded-xl transition-all duration-300 ease-out"
        />
      )}
      {navigation.map((item) => {
        const active = path === item.href;
        return (
          <Link
            ref={(el) => { itemRefs.current[item.href] = el; }}
            onClick={onNavigate}
            key={item.href}
            href={item.href}
            className={`group relative z-10 flex items-center gap-4 rounded-xl px-4 py-3 text-sm transition-colors duration-200 ${
              active ? "font-bold text-brand-700" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Icon name={item.icon} className={`h-5 w-5 shrink-0 transition-transform duration-200 ${active ? "scale-110 text-brand-600" : "text-slate-500 group-hover:scale-110 group-hover:text-brand-600"}`} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Responsive authenticated layout: a neumorphic (soft-UI) desktop sidebar and an animated mobile drawer.
 * Session check happens here (not per-page) so every route under (platform) is gated from one place -
 * this app has no server-rendered auth state (see shared/supabase/client.ts), so the guard has to run
 * client-side on mount rather than in middleware. Nothing signed-in renders until it resolves, which
 * keeps an unauthenticated visitor who lands on e.g. /dashboard from a stale link from ever seeing it. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [closing, setClosing] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      if (!data.session) {
        router.replace("/auth/sign-in");
        return;
      }
      setUser(data.session.user);
      setAuthorized(true);
    });
    return () => { active = false; };
  }, [router]);

  const name = displayNameFor(user);

  async function signOut() { await clearToken(); router.push("/auth/sign-in"); }

  function closeDrawer() {
    setClosing(true);
    setTimeout(() => { setOpen(false); setClosing(false); }, 200);
  }

  const logo = (
    <Link href="/dashboard" className="mb-8 flex items-center gap-3 px-3">
      <Image src="/logo-icon.png" alt="" width={40} height={40} className="h-10 w-10" priority />
      <span>
        <span className="block text-lg font-bold text-brand-700">Shopping AI</span>
        <span className="label-caps block text-brand-600/70">AI Intelligence</span>
      </span>
    </Link>
  );

  if (!authorized) {
    return (
      <div className="grid min-h-screen place-items-center bg-surface">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-surface">
      <aside className="surface-raised fixed inset-y-0 left-0 hidden w-64 flex-col py-8 lg:flex">
        {logo}
        <NavList />
        <div className="mx-3 mt-auto rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-4 text-sm text-white shadow-neu">
          <p className="font-semibold">Need a second opinion?</p>
          <Link href="/chat" className="mt-2 flex items-center text-brand-300 transition-colors hover:text-brand-200">
            Ask Shopping Chat <Icon name="arrow" className="ml-1 h-4 w-4" />
          </Link>
        </div>
      </aside>

      {open && (
        <>
          <button
            aria-label="Close navigation"
            className={`fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm lg:hidden ${closing ? "animate-fade-out" : "animate-fade-in"}`}
            onClick={closeDrawer}
          />
          <aside className={`surface-elevated fixed inset-y-0 left-0 z-50 flex w-72 flex-col py-8 lg:hidden ${closing ? "animate-drawer-out" : "animate-drawer-in"}`}>
            <button aria-label="Close navigation" onClick={closeDrawer} className="absolute right-4 top-4 rounded-full p-1.5 text-slate-500 transition-colors hover:bg-slate-900/5 hover:text-slate-900">
              <Icon name="x" className="h-5 w-5" />
            </button>
            {logo}
            <NavList onNavigate={closeDrawer} />
          </aside>
        </>
      )}

      <div className="lg:pl-64">
        <header className="surface-raised sticky top-0 z-30 flex h-16 items-center justify-between px-4 sm:px-6">
          <div className="flex flex-1 items-center gap-4">
            <button aria-label="Open navigation" onClick={() => setOpen(true)} className="rounded-lg p-1.5 text-slate-600 transition-colors hover:bg-slate-900/5 lg:hidden"><Icon name="menu" className="h-6 w-6" /></button>
          </div>
          <div className="flex items-center gap-4 sm:gap-6">
            <button aria-label="Notifications" className="relative text-slate-500 transition-colors hover:text-slate-700">
              <Icon name="bell" className="h-5 w-5" />
              <span className="absolute -right-0.5 -top-0.5 flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
              </span>
            </button>
            <Link href="/profile" className="hidden items-center gap-3 pl-4 sm:flex md:pl-6">
              <span className="text-right leading-tight">
                <span className="label-caps block text-slate-700">{name}</span>
                <span className="block text-[10px] tracking-wide text-slate-400">MEMBER</span>
              </span>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-brand-100 to-brand-200 text-sm font-bold text-brand-700 shadow-neu-sm">{initialsFor(name)}</span>
            </Link>
            <button aria-label="Sign out" onClick={signOut} className="text-slate-500 transition-colors hover:text-rose-600"><Icon name="logout" className="h-5 w-5" /></button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-4 sm:p-8">{children}</main>
      </div>
      <AssistantWidget />
    </div>
  );
}
