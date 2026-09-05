"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AssistantWidget } from "./assistant-widget";
import { Icon, type IconName } from "./icons";
import { authHeaders, clearToken } from "@/shared/auth/token";
import { displayNameFor, initialsFor } from "@/shared/auth/use-current-user";
import { supabase } from "@/shared/supabase/client";
import type { User } from "@supabase/supabase-js";

type Notification = { id: string; message: string; product_title: string; is_read: boolean; created_at: string };

function timeAgo(iso: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

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
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[] | null>(null);
  const [confirmingLogout, setConfirmingLogout] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

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

  async function toggleNotifications() {
    const opening = !notifOpen;
    setNotifOpen(opening);
    if (opening && notifications === null) {
      try {
        const response = await fetch("/api/v1/notifications", { headers: await authHeaders() });
        setNotifications(response.ok ? await response.json() : []);
      } catch {
        setNotifications([]);
      }
    }
  }

  async function confirmSignOut() {
    setSigningOut(true);
    await clearToken();
    router.push("/auth/sign-in");
  }

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
            <div className="relative">
              <button aria-label="Notifications" onClick={toggleNotifications} className="relative text-slate-500 transition-colors hover:text-slate-700">
                <Icon name="bell" className="h-5 w-5" />
                {notifications?.some((n) => !n.is_read) !== false && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
                  </span>
                )}
              </button>

              {notifOpen && (
                <>
                  <button aria-label="Close notifications" className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />
                  <div className="surface-elevated animate-scale-in absolute right-0 top-full z-50 mt-3 w-80 origin-top-right rounded-2xl p-2">
                    <p className="label-caps px-3 py-2 text-slate-400">Notifications</p>
                    {notifications === null && <p className="px-3 py-4 text-sm text-slate-400">Loading…</p>}
                    {notifications !== null && notifications.length === 0 && (
                      <p className="px-3 py-4 text-sm text-slate-400">No price-drop alerts yet - they&apos;ll show up here once a wishlisted item drops in price.</p>
                    )}
                    {notifications?.map((n) => (
                      <div key={n.id} className={`rounded-xl px-3 py-2.5 text-sm ${n.is_read ? "text-slate-500" : "text-ink"}`}>
                        <p className="leading-5">{n.message}</p>
                        <p className="mt-0.5 text-xs text-slate-400">{timeAgo(n.created_at)}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
            <Link href="/profile" className="hidden items-center gap-3 pl-4 sm:flex md:pl-6">
              <span className="text-right leading-tight">
                <span className="label-caps block text-slate-700">{name}</span>
                <span className="block text-[10px] tracking-wide text-slate-400">MEMBER</span>
              </span>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-brand-100 to-brand-200 text-sm font-bold text-brand-700 shadow-neu-sm">{initialsFor(name)}</span>
            </Link>
            <button aria-label="Sign out" onClick={() => setConfirmingLogout(true)} className="text-slate-500 transition-colors hover:text-rose-600"><Icon name="logout" className="h-5 w-5" /></button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-4 sm:p-8">{children}</main>
      </div>
      <AssistantWidget />

      {confirmingLogout && (
        <>
          <button aria-label="Cancel sign out" className="animate-fade-in fixed inset-0 z-[60] bg-slate-950/40 backdrop-blur-sm" onClick={() => setConfirmingLogout(false)} />
          {/* Centered via flexbox on this outer fixed layer, not transform: translate - a translate-based
           * centering trick on the card itself would conflict with animate-scale-in's own keyframe
           * transform (CSS animations replace the whole transform property, not compose with it), which
           * silently dropped the centering offset and pushed the dialog off-screen. */}
          <div className="fixed inset-0 z-[70] grid place-items-center p-4">
            <div className="animate-scale-in card w-full max-w-sm p-6 text-center">
              <span className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-rose-50 text-rose-600"><Icon name="logout" className="h-5 w-5" /></span>
              <h2 className="mt-4 text-lg font-bold text-ink">Sign out?</h2>
              <p className="mt-1 text-sm text-slate-500">You&apos;ll need to sign in again to get back to your wishlist, chat history, and preferences.</p>
              <div className="mt-6 grid grid-cols-2 gap-3">
                <button onClick={() => setConfirmingLogout(false)} className="btn-secondary">Cancel</button>
                <button onClick={confirmSignOut} disabled={signingOut} className="rounded-xl bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-rose-700 disabled:opacity-60">
                  {signingOut ? "Signing out…" : "Sign out"}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
