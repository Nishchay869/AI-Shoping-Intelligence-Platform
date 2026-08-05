import Link from "next/link";
import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";
import { Icon, type IconName } from "@/components/icons";

const PRINCIPLES: { icon: IconName; title: string; body: string }[] = [
  { icon: "sparkles", title: "Clarity over noise", body: "Every recommendation comes with a plain-English reason - no black-box scores." },
  { icon: "shield", title: "Your data stays yours", body: "We track prices and products, not you. No selling data to third parties, ever." },
  { icon: "heart", title: "Built for real decisions", body: "We optimize for the purchase you won't regret, not the click you'll make fastest." }
];

const STATS = [
  { value: "12K+", label: "Products tracked" },
  { value: "9", label: "Retailers compared" },
  { value: "2024", label: "Founded" }
];

export const metadata = { title: "About | AI Shopping Intelligence Platform" };

export default function AboutPage() {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        <section className="py-24">
          <div className="mx-auto max-w-3xl px-4 text-center sm:px-8">
            <p className="label-caps text-brand-600">About AI Shopping Intelligence Platform</p>
            <h1 className="mt-2 text-4xl font-bold text-ink lg:text-5xl">Shopping intelligence, built to save you time and money.</h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-slate-600">
              AI Shopping Intelligence Platform started with a simple frustration: comparing prices and reviews across a dozen tabs before every purchase. We built the tool we wished existed - one place that reads the reviews, tracks the prices, and tells you straight what&apos;s actually worth buying.
            </p>
          </div>
        </section>

        <section className="pb-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <div className="card grid grid-cols-1 divide-y divide-slate-200/70 p-2 sm:grid-cols-3 sm:divide-y-0 sm:divide-x">
              {STATS.map((stat) => (
                <div key={stat.label} className="p-6 text-center">
                  <p className="data text-3xl font-extrabold text-brand-700">{stat.value}</p>
                  <p className="mt-1 text-sm text-slate-500">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <h2 className="mb-16 text-center text-3xl font-bold text-ink">What we believe</h2>
            <div className="grid gap-6 md:grid-cols-3">
              {PRINCIPLES.map((principle) => (
                <article key={principle.title} className="card h-full p-8">
                  <div className="shadow-neu-sm mb-5 grid h-12 w-12 place-items-center rounded-xl text-brand-600">
                    <Icon name={principle.icon} className="h-5 w-5" />
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-ink">{principle.title}</h3>
                  <p className="text-slate-600">{principle.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-gradient-to-br from-brand-700 to-violet-900 py-24">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-8">
            <h2 className="mb-6 text-3xl font-bold text-white">Want to work on this with us?</h2>
            <p className="mx-auto mb-10 max-w-xl text-brand-100">We&apos;re a small team hiring for a few key roles.</p>
            <Link href="/careers" className="inline-flex rounded-lg bg-white px-10 py-4 text-lg font-bold text-brand-700 shadow-xl transition-transform duration-200 hover:scale-105 active:scale-100">
              View open roles
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
