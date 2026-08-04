import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";
import { Icon, type IconName } from "@/components/icons";

const CHANNELS: { icon: IconName; title: string; body: string; action: { label: string; href: string } }[] = [
  { icon: "message", title: "General support", body: "Questions about your account, price tracking, or how a feature works.", action: { label: "hello@pricewise.app", href: "mailto:hello@pricewise.app" } },
  { icon: "bag", title: "Careers", body: "Interested in joining the team? See open roles or reach out directly.", action: { label: "careers@pricewise.app", href: "mailto:careers@pricewise.app" } },
  { icon: "shield", title: "Privacy & data", body: "Questions about how your data is handled, or a request under our privacy policy.", action: { label: "privacy@pricewise.app", href: "mailto:privacy@pricewise.app" } }
];

export const metadata = { title: "Contact | Pricewise" };

export default function ContactPage() {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        <section className="py-24">
          <div className="mx-auto max-w-3xl px-4 text-center sm:px-8">
            <p className="label-caps text-brand-600">Contact</p>
            <h1 className="mt-2 text-4xl font-bold text-ink lg:text-5xl">We&apos;d like to hear from you.</h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-slate-600">
              Pick the right inbox below and we&apos;ll get back to you as soon as we can - usually within a business day.
            </p>
          </div>
        </section>

        <section className="pb-24">
          <div className="mx-auto max-w-5xl px-4 sm:px-8">
            <div className="grid gap-6 md:grid-cols-3">
              {CHANNELS.map((channel) => (
                <article key={channel.title} className="card flex h-full flex-col p-8">
                  <div className="shadow-neu-sm mb-5 grid h-12 w-12 place-items-center rounded-xl text-brand-600">
                    <Icon name={channel.icon} className="h-5 w-5" />
                  </div>
                  <h2 className="mb-2 text-lg font-bold text-ink">{channel.title}</h2>
                  <p className="mb-6 flex-1 text-sm text-slate-600">{channel.body}</p>
                  <a href={channel.action.href} className="text-sm font-bold text-brand-700 hover:underline">{channel.action.label}</a>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
