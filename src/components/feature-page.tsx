import Link from "next/link";
import type { ReactNode } from "react";
import { SiteNav } from "./site-nav";
import { SiteFooter } from "./site-footer";
import { Reveal } from "./reveal";
import { Icon, type IconName } from "./icons";

export type FeatureStep = { title: string; body: string };
export type FeatureFaq = { q: string; a: string };

/** Shared template for the public "learn about a feature" pages linked from the pre-login navbar.
 * Each feature supplies its own copy and a small custom mockup visual (kept feature-specific since a
 * search results grid, a chat thread, and a receipt card don't share a layout); everything else -
 * hero shell, how-it-works steps, usage guide, FAQ accordion, closing CTA - is standardized here so
 * the four pages stay visually and structurally consistent. */
export function FeaturePage({
  name,
  eyebrow,
  icon,
  title,
  description,
  mockup,
  howItWorks,
  guide,
  faqs
}: {
  name: string;
  eyebrow: string;
  icon: IconName;
  title: string;
  description: string;
  mockup: ReactNode;
  howItWorks: FeatureStep[];
  guide: FeatureStep[];
  faqs: FeatureFaq[];
}) {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        {/* Hero */}
        <section className="py-16">
          <div className="mx-auto grid max-w-7xl gap-16 px-4 sm:px-8 lg:grid-cols-2 lg:items-center">
            <div className="space-y-6">
              <span className="pill gap-1.5 bg-brand-100 text-brand-700">
                <Icon name={icon} className="h-3.5 w-3.5" /> {eyebrow}
              </span>
              <h1 className="text-4xl font-bold leading-tight text-ink lg:text-5xl" style={{ textWrap: "balance" }}>{title}</h1>
              <p className="max-w-xl text-lg leading-8 text-slate-600">{description}</p>
              <div className="flex flex-wrap gap-3">
                <Link href="/auth/sign-in" className="btn-primary px-8">Sign in to try it</Link>
                <Link href="#how-it-works" className="btn-secondary px-8">See how it works</Link>
              </div>
            </div>
            <div className="relative">{mockup}</div>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <Reveal className="mb-16 text-center">
              <h2 className="text-3xl font-bold text-ink">How it works</h2>
            </Reveal>
            <div className="grid gap-8 md:grid-cols-3">
              {howItWorks.map((step, index) => (
                <Reveal key={step.title} delay={index * 100} className="flex flex-col items-center p-8 text-center">
                  <div className="data shadow-neu mb-6 grid h-12 w-12 place-items-center rounded-2xl text-lg font-bold text-brand-600">{index + 1}</div>
                  <h3 className="mb-2 text-lg font-bold text-ink">{step.title}</h3>
                  <p className="text-slate-600">{step.body}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* Usage guide */}
        <section className="py-16">
          <div className="mx-auto max-w-4xl px-4 sm:px-8">
            <Reveal className="mb-12 text-center">
              <h2 className="text-3xl font-bold text-ink">How to use it</h2>
              <p className="mt-3 text-slate-600">A quick walkthrough for your first time using {name}.</p>
            </Reveal>
            <div className="card divide-y divide-slate-200/70 p-2">
              {guide.map((step, index) => (
                <div key={step.title} className="flex gap-4 p-6">
                  <span className="data shadow-neu-sm grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-bold text-brand-600">{index + 1}</span>
                  <div>
                    <p className="font-bold text-ink">{step.title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">{step.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-16">
          <div className="mx-auto max-w-3xl px-4 sm:px-8">
            <Reveal className="mb-12 text-center">
              <h2 className="text-3xl font-bold text-ink">Frequently asked questions</h2>
            </Reveal>
            <div className="space-y-4">
              {faqs.map((faq, index) => (
                <Reveal key={faq.q} delay={index * 60}>
                  <details className="card group p-6">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-ink [&::-webkit-details-marker]:hidden">
                      {faq.q}
                      <span className="shadow-neu-sm grid h-7 w-7 shrink-0 rotate-45 place-items-center rounded-full text-brand-600 transition-transform duration-200 group-open:rotate-0">
                        <Icon name="x" className="h-3.5 w-3.5" />
                      </span>
                    </summary>
                    <p className="mt-4 text-sm leading-6 text-slate-600">{faq.a}</p>
                  </details>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-gradient-to-br from-brand-700 to-violet-900 py-24">
          <Reveal className="mx-auto max-w-4xl px-4 text-center sm:px-8">
            <h2 className="mb-6 text-3xl font-bold text-white">Ready to try {name}?</h2>
            <p className="mx-auto mb-10 max-w-xl text-brand-100">Sign in to start using it in your own account - it only takes a minute.</p>
            <Link href="/auth/sign-in" className="inline-flex rounded-lg bg-white px-10 py-4 text-lg font-bold text-brand-700 shadow-xl transition-transform duration-200 hover:scale-105 active:scale-100">
              Sign in
            </Link>
          </Reveal>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
