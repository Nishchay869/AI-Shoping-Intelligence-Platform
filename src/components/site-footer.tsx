import Link from "next/link";
import { Icon, type IconName } from "./icons";

const FOOTER_LINKS: { title: string; links: { label: string; href: string }[] }[] = [
  {
    title: "Product",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Discover", href: "/search" },
      { label: "AI Picks", href: "/recommendations" },
      { label: "Shopping Chat", href: "/chat" },
      { label: "Receipt Scanner", href: "/receipts" }
    ]
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      // { label: "Careers", href: "/careers" },
      { label: "Blog", href: "/blog" },
      { label: "Contact", href: "/contact" }
    ]
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
      { label: "Cookie Policy", href: "/cookies" }
    ]
  }
];

const SOCIALS: { icon: IconName; label: string }[] = [
  { icon: "social-x", label: "X (Twitter)" },
  { icon: "social-instagram", label: "Instagram" },
  { icon: "social-linkedin", label: "LinkedIn" },
  { icon: "social-facebook", label: "Facebook" }
];

/** Public marketing footer, shared by the landing page and every standalone marketing/legal page.
 * "Product" links point at real in-app routes; everything else points at real pages in this app
 * (about/careers/blog/contact/privacy/terms/cookies) rather than dead "#" placeholders. */
export function SiteFooter() {
  return (
    <footer className="pb-10 pt-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-8">
        <div className="grid gap-12 lg:grid-cols-[2fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2 text-lg font-bold text-brand-700">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-neu-brand">P</span>
              Pricewise
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-6 text-slate-500">
              AI-powered price intelligence that helps you compare, decide, and buy with confidence - across every store you shop.
            </p>
            <div className="mt-6 flex items-center gap-2">
              {SOCIALS.map((social) => (
                <a
                  key={social.label}
                  href="#"
                  aria-label={`Pricewise on ${social.label}`}
                  className="shadow-neu-sm grid h-10 w-10 place-items-center rounded-full text-slate-500 transition-all hover:text-brand-600 active:shadow-neu-inset-sm"
                >
                  <Icon name={social.icon} className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          {FOOTER_LINKS.map((column) => (
            <div key={column.title}>
              <p className="label-caps text-slate-400">{column.title}</p>
              <ul className="mt-4 space-y-3">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-sm text-slate-600 transition-colors hover:text-brand-700">{link.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-slate-200/70 pt-8 sm:flex-row">
          <p className="text-sm text-slate-500">© {new Date().getFullYear()} Pricewise. All rights reserved.</p>
          <p className="text-xs text-slate-400">Made for shoppers who like a good deal.</p>
        </div>
      </div>
    </footer>
  );
}
