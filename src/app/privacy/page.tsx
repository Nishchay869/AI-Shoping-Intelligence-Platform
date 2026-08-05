import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

export const metadata = { title: "Privacy Policy | AI Shopping Intelligence Platform" };

export default function PrivacyPage() {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        <section className="py-20">
          <div className="mx-auto max-w-3xl px-4 sm:px-8">
            <p className="label-caps text-brand-600">Legal</p>
            <h1 className="mt-2 text-4xl font-bold text-ink">Privacy Policy</h1>
            <p className="mt-3 text-sm text-slate-500">Last updated: January 2026</p>

            <div className="card mt-10 space-y-8 p-8 sm:p-10">
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">1. Information we collect</h2>
                <p className="leading-7 text-slate-600">
                  When you create an account, we collect your name and email address. When you use AI Shopping Intelligence Platform, we store the products you search for, save to your wishlist, or ask about through Shopping Chat, so we can track prices and personalize recommendations on your behalf. If you use the receipt scanner, the receipt image and the details extracted from it are stored on your account.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">2. How we use your information</h2>
                <p className="leading-7 text-slate-600">
                  We use your data to run the core features you sign up for: tracking prices on saved products, generating AI recommendations, answering questions in Shopping Chat, and sending you price-drop alerts you&apos;ve opted into. We do not sell your personal data to third parties.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">3. Data security</h2>
                <p className="leading-7 text-slate-600">
                  Account credentials and session data are handled through industry-standard authentication providers with encryption in transit and at rest. Access to production data is restricted to the engineers who need it to operate the service.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">4. Your rights</h2>
                <p className="leading-7 text-slate-600">
                  You can review or update your account details from your profile at any time. You can request a copy of your data or ask us to delete your account by emailing <a href="mailto:privacy@pricewise.app" className="font-semibold text-brand-700 hover:underline">privacy@pricewise.app</a>.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">5. Changes to this policy</h2>
                <p className="leading-7 text-slate-600">
                  If we make material changes to how we handle your data, we&apos;ll notify you by email before the changes take effect.
                </p>
              </section>
              <section>
                <h2 className="mb-3 text-xl font-bold text-ink">6. Contact us</h2>
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
