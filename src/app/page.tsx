import Link from "next/link";

const HOW_IT_WORKS = [
  { icon: "🔍", title: "1. Describe & search", body: "Describe what you need in plain English, or search for a specific model." },
  { icon: "🧠", title: "2. AI analysis", body: "Our engine parses thousands of reviews and the live catalog against your budget and needs." },
  { icon: "✅", title: "3. Decision ready", body: "Get a ranked shortlist with plain-English reasons for every pick." }
];

const FEATURES = [
  { title: "AI Recommendations", body: "Describe your budget, purpose, and must-have features - get ranked picks with plain-English reasons for each one.", wide: true },
  { title: "Review Intelligence", body: "Thousands of buyer reviews summarized into pros, cons, and common complaints in seconds." },
  { title: "Shopping Chat", body: "Ask anything about the catalog, reviews, or general market info - grounded answers with cited sources." },
  { title: "Receipt Scanner", body: "Snap a photo of a paper receipt - get warranty terms and itemized spending tracked automatically." }
];

/** Marketing landing page; authenticated dashboard routes can be added without changing domain code.
 * Sign-up redirects here (rather than straight into the dashboard) so the shopper signs in deliberately;
 * `registered=1` shows a one-time banner nudging them toward the sign-in page. */
export default async function HomePage({ searchParams }: { searchParams: Promise<{ registered?: string }> }) {
  const { registered } = await searchParams;
  return (
    <div className="bg-white">
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
          <Link href="/" className="flex items-center gap-2 text-lg font-bold text-brand-700">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-700 text-white">P</span>Pricewise
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/auth/sign-in" className="label-caps text-slate-500 hover:text-brand-700">Sign in</Link>
            <Link href="/auth/sign-up" className="btn-primary">Get started free</Link>
          </div>
        </div>
      </nav>

      <main className="pt-16">
        {registered && (
          <div className="mx-auto mt-6 max-w-4xl rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-center text-sm font-semibold text-brand-700">
            Account created! Please <Link href="/auth/sign-in" className="underline">sign in</Link> to continue.
          </div>
        )}

        {/* Hero */}
        <section className="relative overflow-hidden bg-slate-50 py-24">
          <div className="mx-auto flex max-w-7xl flex-col items-center gap-16 px-4 sm:px-8 lg:flex-row">
            <div className="z-10 flex-1 space-y-8">
              <span className="pill border border-brand-200 bg-brand-100 text-brand-700">✨ Next-gen intelligence</span>
              <h1 className="text-4xl leading-tight text-ink lg:text-5xl lg:leading-[1.1]" style={{ textWrap: "balance" }}>
                Make confident purchase decisions with AI-powered price intelligence.
              </h1>
              <p className="max-w-xl text-lg leading-8 text-slate-600">
                Compare prices across retailers, read AI-summarized reviews, and get personalized recommendations tailored to your budget and needs.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link href="/auth/sign-up" className="btn-primary px-8">Get started free</Link>
                <Link href="#how-it-works" className="btn-secondary px-8">See how it works</Link>
              </div>
            </div>
            <div className="relative flex-1">
              <div className="absolute -right-12 -top-12 h-64 w-64 rounded-full bg-brand-200/40 blur-3xl" />
              <div className="absolute -bottom-12 -left-12 h-48 w-48 rounded-full bg-slate-300/30 blur-3xl" />
              <div className="card relative z-10 space-y-4 p-6">
                <div className="flex items-center justify-between">
                  <span className="label-caps text-brand-700">AI Picks · #1 match</span>
                  <span className="pill bg-brand-100 text-brand-700">Best value</span>
                </div>
                <p className="text-lg font-bold text-ink">Sony WH-1000XM5</p>
                <p className="data text-3xl font-extrabold text-brand-700">$328.00</p>
                <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">Matches your $350 budget with class-leading noise cancellation and 30-hour battery life.</p>
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <div className="mb-16 space-y-4 text-center">
              <h2 className="text-3xl font-bold text-ink">Streamlined intelligence</h2>
              <p className="mx-auto max-w-2xl text-slate-600">Three simple steps to smarter spending and better products.</p>
            </div>
            <div className="grid gap-8 md:grid-cols-3">
              {HOW_IT_WORKS.map((step) => (
                <div key={step.title} className="flex flex-col items-center p-8 text-center">
                  <div className="mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-brand-50 text-3xl">{step.icon}</div>
                  <h3 className="mb-2 text-lg font-bold text-ink">{step.title}</h3>
                  <p className="text-slate-600">{step.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Feature grid */}
        <section className="bg-slate-50 py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <h2 className="mb-16 text-center text-3xl font-bold text-ink">Built for precision</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {FEATURES.map((feature) => (
                <article key={feature.title} className={`card p-8 ${feature.wide ? "md:col-span-2" : ""}`}>
                  <h3 className="mb-3 text-xl font-bold text-ink">{feature.title}</h3>
                  <p className="max-w-md text-slate-600">{feature.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="bg-brand-700 py-24">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-8">
            <h2 className="mb-6 text-3xl font-bold text-white">Ready for smarter intelligence?</h2>
            <p className="mx-auto mb-10 max-w-xl text-brand-100">Join shoppers who use Pricewise to save time and money on every purchase.</p>
            <Link href="/auth/sign-up" className="inline-flex rounded-lg bg-white px-10 py-4 text-lg font-bold text-brand-700 shadow-xl transition hover:scale-105">
              Get started free
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-brand-700">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-700 text-white">P</span>Pricewise
          </Link>
          <p className="text-sm text-slate-500">© {new Date().getFullYear()} Pricewise. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
