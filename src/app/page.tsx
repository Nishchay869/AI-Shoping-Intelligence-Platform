import Link from "next/link";
import { Reveal } from "@/components/reveal";
import { Icon, type IconName } from "@/components/icons";
import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

const HOW_IT_WORKS: { icon: IconName; title: string; body: string }[] = [
  { icon: "search", title: "1. Describe & search", body: "Describe what you need in plain English, or search for a specific model." },
  { icon: "cpu", title: "2. AI analysis", body: "Our engine parses thousands of reviews and the live catalog against your budget and needs." },
  { icon: "check", title: "3. Decision ready", body: "Get a ranked shortlist with plain-English reasons for every pick." }
];

const FEATURES: { icon: IconName; title: string; body: string; wide?: boolean }[] = [
  { icon: "sparkles", title: "AI Recommendations", body: "Describe your budget, purpose, and must-have features - get ranked picks with plain-English reasons for each one.", wide: true },
  { icon: "quote", title: "Review Intelligence", body: "Thousands of buyer reviews summarized into pros, cons, and common complaints in seconds." },
  { icon: "message", title: "Shopping Chat", body: "Ask anything about the catalog, reviews, or general market info - grounded answers with cited sources." },
  { icon: "receipt", title: "Receipt Scanner", body: "Snap a photo of a paper receipt - get warranty terms and itemized spending tracked automatically." }
];

const USE_CASES: { icon: IconName; title: string; body: string; flow: string[] }[] = [
  { icon: "cpu", title: "Big-ticket electronics", body: "Laptops, TVs, headphones - the purchases you research for weeks before buying.", flow: ["Compare specs", "Read AI review summary", "Buy at the best price"] },
  { icon: "bag", title: "Fashion & lifestyle", body: "Save what you love and let Pricewise watch the price for you.", flow: ["Save to wishlist", "Get a price-drop alert", "Check out"] },
  { icon: "gift", title: "Gifting made easy", body: "Describe who it's for and what you'd like to spend - get a shortlist in seconds.", flow: ["Describe the recipient", "Get ranked AI picks", "Order in minutes"] },
  { icon: "shield", title: "Warranty & spending", body: "Snap a receipt and never lose track of a warranty claim window again.", flow: ["Scan your receipt", "Auto-track warranty", "Get renewal alerts"] }
];

const RETAILERS = ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa", "Croma", "Meesho", "Tata CLiQ", "Reliance Digital"];

const STATS = [
  { value: "12K+", label: "Products tracked" },
  { value: "₹50L+", label: "Saved by shoppers" },
  { value: "4.8★", label: "Average rating" },
  { value: "24/7", label: "AI availability" }
];

const TESTIMONIALS = [
  { quote: "I compared three headphones in the time it used to take me to read one review thread. The AI picks are scarily on-point.", name: "Priya", role: "Frequent online shopper" },
  { quote: "The receipt scanner alone is worth it - I finally know when my warranties actually expire.", name: "Arjun", role: "Home & electronics buyer" },
  { quote: "Shopping Chat talked me out of an impulse buy and into a better one for less money. That's rare.", name: "Meera", role: "Budget-conscious shopper" }
];

const FAQS = [
  { q: "Is Pricewise free to use?", a: "Yes - creating an account and using price tracking, AI recommendations, and Shopping Chat is free." },
  { q: "Which stores does Pricewise compare?", a: "Pricewise tracks listings across major Indian retailers, including Amazon, Flipkart, Myntra, Ajio, Nykaa, Croma, Meesho, Tata CLiQ, and Reliance Digital." },
  { q: "How does the AI recommendation engine work?", a: "Describe your budget, purpose, and must-have features - the engine ranks matching products from the live catalog and explains each pick in plain English." },
  { q: "Is my data safe?", a: "Your account data is protected with industry-standard authentication and encryption, and is never sold to third parties." },
  { q: "Can I get notified about a specific price drop?", a: "Yes - save any product to your wishlist and Pricewise will track its price and alert you when it drops." }
];

/** Marketing landing page; authenticated dashboard routes can be added without changing domain code.
 * Sign-up redirects here (rather than straight into the dashboard) so the shopper signs in deliberately;
 * `registered=1` shows a one-time banner nudging them toward the sign-in page. */
export default async function HomePage({ searchParams }: { searchParams: Promise<{ registered?: string }> }) {
  const { registered } = await searchParams;
  return (
    <div className="bg-surface">
      <SiteNav />

      <main className="pt-28">
        {registered && (
          <div className="mx-auto mt-6 max-w-4xl rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-center text-sm font-semibold text-brand-700">
            Account created! Please <Link href="/auth/sign-in" className="underline">sign in</Link> to continue.
          </div>
        )}

        {/* Hero */}
        <section className="py-24">
          <div className="mx-auto flex max-w-7xl flex-col items-center gap-16 px-4 sm:px-8 lg:flex-row">
            <div className="z-10 flex-1 space-y-8">
              <span className="pill gap-1.5 bg-brand-100 text-brand-700">
                <Icon name="sparkles" className="h-3.5 w-3.5" /> Next-gen intelligence
              </span>
              <h1 className="text-4xl leading-tight text-ink lg:text-5xl lg:leading-[1.1]" style={{ textWrap: "balance" }}>
                Make confident purchase decisions with{" "}
                <span className="text-mark animate-mark-highlight">AI-powered price intelligence</span>.
              </h1>
              <p className="max-w-xl text-lg leading-8 text-slate-600">
                Compare prices across retailers, read AI-summarized reviews, and get personalized recommendations tailored to your budget and needs.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link href="/auth/sign-in" className="btn-primary px-8">Sign in</Link>
                <Link href="#how-it-works" className="btn-secondary px-8">See how it works</Link>
              </div>
            </div>
            <div className="relative flex-1">
              <div className="card relative z-10 animate-float-slow space-y-4 p-6">
                <div className="flex items-center justify-between">
                  <span className="label-caps text-brand-700">AI Picks · #1 match</span>
                  <span className="pill bg-brand-100 text-brand-700">Best value</span>
                </div>
                <p className="text-lg font-bold text-ink">Sony WH-1000XM5</p>
                <p className="data text-3xl font-extrabold text-brand-700">$328.00</p>
                <p className="shadow-neu-inset-sm rounded-lg p-3 text-sm text-slate-600">Matches your $350 budget with class-leading noise cancellation and 30-hour battery life.</p>
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <Reveal className="mb-16 space-y-4 text-center">
              <h2 className="text-3xl font-bold text-ink">Streamlined intelligence</h2>
              <p className="mx-auto max-w-2xl text-slate-600">Three simple steps to smarter spending and better products.</p>
            </Reveal>
            <div className="grid gap-8 md:grid-cols-3">
              {HOW_IT_WORKS.map((step, index) => (
                <Reveal key={step.title} delay={index * 100} className="flex flex-col items-center p-8 text-center">
                  <div className="shadow-neu mb-6 grid h-16 w-16 place-items-center rounded-2xl text-brand-600">
                    <Icon name={step.icon} className="h-7 w-7" />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-ink">{step.title}</h3>
                  <p className="text-slate-600">{step.body}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* Feature grid */}
        <section className="py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <Reveal><h2 className="mb-16 text-center text-3xl font-bold text-ink">Built for precision</h2></Reveal>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {FEATURES.map((feature, index) => (
                <Reveal key={feature.title} delay={index * 80} className={feature.wide ? "md:col-span-2" : ""}>
                  <article className="card h-full p-8">
                    <div className="shadow-neu-sm mb-5 grid h-12 w-12 place-items-center rounded-xl text-brand-600">
                      <Icon name={feature.icon} className="h-5 w-5" />
                    </div>
                    <h3 className="mb-3 text-xl font-bold text-ink">{feature.title}</h3>
                    <p className="max-w-md text-slate-600">{feature.body}</p>
                  </article>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* Use cases */}
        <section className="py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <Reveal className="mb-16 space-y-4 text-center">
              <h2 className="text-3xl font-bold text-ink">Built around how you actually shop</h2>
              <p className="mx-auto max-w-2xl text-slate-600">Whatever you&apos;re buying, Pricewise adapts the flow to fit.</p>
            </Reveal>
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
              {USE_CASES.map((useCase, index) => (
                <Reveal key={useCase.title} delay={index * 80}>
                  <article className="card h-full p-6">
                    <div className="shadow-neu-sm mb-5 grid h-11 w-11 place-items-center rounded-xl text-brand-600">
                      <Icon name={useCase.icon} className="h-5 w-5" />
                    </div>
                    <h3 className="mb-2 font-bold text-ink">{useCase.title}</h3>
                    <p className="mb-6 text-sm text-slate-600">{useCase.body}</p>
                    <ol className="space-y-2">
                      {useCase.flow.map((step, stepIndex) => (
                        <li key={step} className="flex items-center gap-2 text-xs font-medium text-slate-500">
                          <span className="shadow-neu-inset-sm grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-bold text-brand-600">{stepIndex + 1}</span>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </article>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* Trusted retailer strip - floating marquee */}
        <section className="overflow-hidden py-16">
          <Reveal className="mx-auto mb-10 max-w-7xl px-4 text-center sm:px-8">
            <p className="label-caps text-brand-600">Compare across the stores you already shop</p>
            <h2 className="mt-2 text-2xl font-bold text-ink sm:text-3xl">Every price, one place</h2>
          </Reveal>
          <div className="relative">
            <div aria-hidden className="pointer-events-none absolute inset-y-0 left-0 z-10 w-24 bg-gradient-to-r from-surface to-transparent" />
            <div aria-hidden className="pointer-events-none absolute inset-y-0 right-0 z-10 w-24 bg-gradient-to-l from-surface to-transparent" />
            <div className="flex w-max animate-marquee gap-4 hover:[animation-play-state:paused]">
              {[...RETAILERS, ...RETAILERS].map((name, index) => (
                <span key={`${name}-${index}`} className="shadow-neu-sm flex shrink-0 items-center rounded-2xl px-8 py-4 text-lg font-bold tracking-tight text-slate-500">
                  {name}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <Reveal>
              <div className="card grid grid-cols-2 divide-y divide-slate-200/70 p-2 sm:grid-cols-4 sm:divide-y-0 sm:divide-x">
                {STATS.map((stat) => (
                  <div key={stat.label} className="p-6 text-center">
                    <p className="data text-3xl font-extrabold text-brand-700">{stat.value}</p>
                    <p className="mt-1 text-sm text-slate-500">{stat.label}</p>
                  </div>
                ))}
              </div>
            </Reveal>
          </div>
        </section>

        {/* Testimonials */}
        <section className="py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <Reveal className="mb-16 space-y-4 text-center">
              <h2 className="text-3xl font-bold text-ink">Shoppers like what they see</h2>
              <p className="mx-auto max-w-2xl text-slate-600">A few words from people using Pricewise to shop smarter.</p>
            </Reveal>
            <div className="grid gap-6 md:grid-cols-3">
              {TESTIMONIALS.map((testimonial, index) => (
                <Reveal key={testimonial.name} delay={index * 100}>
                  <article className="card h-full p-6">
                    <Icon name="quote" className="h-6 w-6 text-brand-300" />
                    <p className="mt-4 text-sm leading-6 text-slate-600">&ldquo;{testimonial.quote}&rdquo;</p>
                    <div className="mt-6 flex items-center gap-3">
                      <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-brand-100 to-brand-200 text-xs font-bold text-brand-700 shadow-neu-sm">
                        {testimonial.name[0]}
                      </span>
                      <div>
                        <p className="text-sm font-bold text-ink">{testimonial.name}</p>
                        <p className="text-xs text-slate-500">{testimonial.role}</p>
                      </div>
                    </div>
                  </article>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-24">
          <div className="mx-auto max-w-3xl px-4 sm:px-8">
            <Reveal className="mb-16 space-y-4 text-center">
              <h2 className="text-3xl font-bold text-ink">Frequently asked questions</h2>
              <p className="mx-auto max-w-2xl text-slate-600">Everything you need to know before you start.</p>
            </Reveal>
            <div className="space-y-4">
              {FAQS.map((faq, index) => (
                <Reveal key={faq.q} delay={index * 60}>
                  <details className="card group p-6 [&_summary::-webkit-details-marker]:hidden">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-ink">
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

        {/* Bottom CTA */}
        <section className="bg-gradient-to-br from-brand-700 to-violet-900 py-24">
          <Reveal className="mx-auto max-w-4xl px-4 text-center sm:px-8">
            <h2 className="mb-6 text-3xl font-bold text-white">Ready for smarter intelligence?</h2>
            <p className="mx-auto mb-10 max-w-xl text-brand-100">Sign in to start comparing prices and get personalized recommendations tailored to you.</p>
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
