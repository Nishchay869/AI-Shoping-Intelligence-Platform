import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

export const metadata = { title: "Cookie Policy | AI Shopping Intelligence Platform" };

export default function CookiesPage() {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        <section className="py-20">
          <div className="mx-auto max-w-3xl px-4 sm:px-8">
            <p className="label-caps text-brand-600">Legal</p>
            <h1 className="mt-2 text-4xl font-bold text-ink">Cookie Policy</h1>
            <p className="mt-3 text-sm text-slate-500">Last updated: January 2026</p>

            <div className="card mt-10 space-y-8 p-8 sm:p-10">
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">1. What cookies are</h2>
                <p className="leading-7 text-slate-600">
                  Cookies are small text files stored in your browser that let a site remember information between visits, like whether you&apos;re signed in.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">2. How we use cookies</h2>
                <p className="leading-7 text-slate-600">
                  AI Shopping Intelligence Platform uses strictly necessary cookies to keep you signed in and to protect your session. We do not use third-party advertising or tracking cookies.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">3. Types of cookies we set</h2>
                <ul className="list-disc space-y-2 pl-5 leading-7 text-slate-600">
                  <li><span className="font-semibold text-ink">Essential:</span> keeps you signed in and secures your session. The service won&apos;t function correctly without these.</li>
                  <li><span className="font-semibold text-ink">Preference:</span> remembers small settings, like a dismissed banner, so you don&apos;t see it again.</li>
                </ul>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">4. Managing cookies</h2>
                <p className="leading-7 text-slate-600">
                  Most browsers let you block or delete cookies in their settings. Blocking essential cookies will prevent you from staying signed in to AI Shopping Intelligence Platform.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">5. Contact us</h2>
                <p className="leading-7 text-slate-600">
                  Questions about this policy can be sent to <a href="mailto:privacy@pricewise.app" className="font-semibold text-brand-700 hover:underline">privacy@pricewise.app</a>.
                </p>
              </section>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
