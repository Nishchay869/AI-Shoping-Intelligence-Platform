"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { AssistantWidget } from "./assistant-widget";
import { Icon, type IconName } from "./icons";
import { clearToken } from "@/shared/auth/token";

const navigation: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Overview", icon: "home" }, { href: "/search", label: "Discover", icon: "search" }, { href: "/recommendations", label: "AI Picks", icon: "sparkles" }, { href: "/for-you", label: "For You", icon: "trend" }, { href: "/wishlist", label: "Wishlist", icon: "heart" }, { href: "/chat", label: "Shopping Chat", icon: "message" }, { href: "/receipts", label: "Receipt Scanner", icon: "receipt" }, { href: "/profile", label: "Profile", icon: "user" }
];
/** Responsive authenticated layout with a desktop sidebar and accessible mobile drawer. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname(); const router = useRouter(); const [open, setOpen] = useState(false);
  async function signOut() { await clearToken(); router.push("/auth/sign-in"); }

  const logo = (
    <Link href="/dashboard" className="mb-8 flex items-center gap-3 px-2">
      <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-700 text-white"><Icon name="sparkles" className="h-5 w-5" /></span>
      <span>
        <span className="block text-lg font-bold text-brand-700">Pricewise</span>
        <span className="label-caps block text-brand-600/70">AI Intelligence</span>
      </span>
    </Link>
  );

  const nav = (
    <nav className="flex-1 space-y-1 px-2">
      {navigation.map((item) => {
        const active = path === item.href;
        return (
          <Link
            onClick={() => setOpen(false)}
            key={item.href}
            href={item.href}
            className={`flex items-center gap-4 rounded-lg px-4 py-3 text-sm transition-colors ${
              active ? "border-r-4 border-brand-600 bg-brand-50 font-bold text-brand-700" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Icon name={item.icon} className="h-5 w-5" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-slate-200 bg-white py-8 lg:flex">
        {logo}
        {nav}
        <div className="mx-4 mt-auto rounded-xl bg-slate-900 p-4 text-sm text-white">
          <p className="font-semibold">Need a second opinion?</p>
          <Link href="/chat" className="mt-2 flex items-center text-brand-300">
            Ask Shopping Chat <Icon name="arrow" className="ml-1 h-4 w-4" />
          </Link>
        </div>
      </aside>

      {open && (
        <>
          <button aria-label="Close navigation" className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden" onClick={() => setOpen(false)} />
          <aside className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-white py-8 lg:hidden">
            <button aria-label="Close navigation" onClick={() => setOpen(false)} className="absolute right-4 top-4"><Icon name="x" className="h-5 w-5" /></button>
            {logo}
            {nav}
          </aside>
        </>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6">
          <div className="flex flex-1 items-center gap-4">
            <button aria-label="Open navigation" onClick={() => setOpen(true)} className="lg:hidden"><Icon name="menu" className="h-6 w-6" /></button>
            <Link href="/search" className="hidden max-w-md flex-1 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-400 hover:border-slate-300 sm:flex">
              <Icon name="search" className="h-4 w-4" />
              Search products, stores, or alerts…
            </Link>
          </div>
          <div className="flex items-center gap-4 sm:gap-6">
            <button aria-label="Notifications" className="relative text-slate-500 hover:text-slate-700">
              <Icon name="bell" className="h-5 w-5" />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-rose-500" />
            </button>
            <Link href="/profile" className="hidden items-center gap-3 border-l border-slate-200 pl-4 sm:flex md:pl-6">
              <span className="text-right leading-tight">
                <span className="label-caps block text-slate-700">Nishchay</span>
                <span className="block text-[10px] tracking-wide text-slate-400">MEMBER</span>
              </span>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">NS</span>
            </Link>
            <button aria-label="Sign out" onClick={signOut} className="text-slate-500 hover:text-slate-700"><Icon name="logout" className="h-5 w-5" /></button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-4 sm:p-8">{children}</main>
      </div>
      <AssistantWidget />
    </div>
  );
}
