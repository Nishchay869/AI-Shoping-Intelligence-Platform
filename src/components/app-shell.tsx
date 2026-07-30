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
  const nav = <nav className="space-y-1">{navigation.map((item) => <Link onClick={() => setOpen(false)} key={item.href} href={item.href} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${path === item.href ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"}`}><Icon name={item.icon} className="h-5 w-5" />{item.label}</Link>)}</nav>;
  return <div className="min-h-screen bg-slate-50"><aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-white p-5 lg:block"><Link href="/dashboard" className="mb-10 flex items-center gap-2 text-xl font-bold"><span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">P</span>Pricewise</Link>{nav}<div className="absolute bottom-6 left-5 right-5 rounded-xl bg-slate-900 p-4 text-sm text-white"><p className="font-semibold">Need a second opinion?</p><Link href="/chat" className="mt-2 flex items-center text-brand-300">Ask Shopping Chat <Icon name="arrow" className="ml-1 h-4 w-4" /></Link></div></aside>
    {open && <><button aria-label="Close navigation" className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden" onClick={() => setOpen(false)} /><aside className="fixed inset-y-0 left-0 z-50 w-72 bg-white p-5 lg:hidden"><button aria-label="Close navigation" onClick={() => setOpen(false)} className="absolute right-4 top-4"><Icon name="x" className="h-5 w-5" /></button><Link href="/dashboard" className="mb-10 flex items-center gap-2 text-xl font-bold"><span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">P</span>Pricewise</Link>{nav}</aside></>}
    <div className="lg:pl-64"><header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-white/95 px-4 backdrop-blur sm:px-8"><button aria-label="Open navigation" onClick={() => setOpen(true)} className="lg:hidden"><Icon name="menu" className="h-6 w-6" /></button><div className="hidden text-sm text-slate-500 sm:block">Your personal shopping intelligence</div><div className="flex items-center gap-4"><button aria-label="Notifications" className="relative text-slate-500"><Icon name="bell" className="h-5 w-5" /><span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-rose-500" /></button><Link href="/profile" className="grid h-9 w-9 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">NS</Link><button aria-label="Sign out" onClick={signOut} className="text-slate-500 hover:text-slate-700"><Icon name="logout" className="h-5 w-5" /></button></div></header><main className="mx-auto max-w-7xl p-4 sm:p-8">{children}</main></div>
    <AssistantWidget /></div>;
}
