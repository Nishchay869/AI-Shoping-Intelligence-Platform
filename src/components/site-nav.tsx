import Link from "next/link";
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
 * page load and an animated underline on each link's hover state. */
export function SiteNav() {
  return (
    <div className="animate-nav-in fixed inset-x-0 top-4 z-50 px-4 sm:top-5 sm:px-6">
      <nav className="surface-raised mx-auto flex h-16 max-w-7xl items-center justify-between rounded-full pl-4 pr-3 sm:pl-6 sm:pr-4">
        <Link href="/" className="flex shrink-0 items-center gap-2 text-lg font-bold text-brand-700">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-neu-brand">P</span>
          <span className="hidden sm:inline">Pricewise</span>
        </Link>

        <div className="hidden items-center lg:flex">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group relative flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-2 text-sm font-medium text-slate-600 transition-colors duration-200 hover:text-brand-700 xl:px-4"
            >
              <Icon name={item.icon} className="h-4 w-4 text-slate-400 transition-colors duration-200 group-hover:text-brand-600" />
              {item.label}
              <span className="absolute inset-x-3 -bottom-0.5 h-0.5 origin-left scale-x-0 rounded-full bg-brand-600 transition-transform duration-300 ease-out group-hover:scale-x-100 xl:inset-x-4" />
            </Link>
          ))}
        </div>

        <Link href="/auth/sign-in" className="btn-primary shrink-0 rounded-full px-6">Sign in</Link>
      </nav>
    </div>
  );
}
