import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";
import { Icon } from "@/components/icons";

const ROLES = [
  { title: "Senior Frontend Engineer", team: "Engineering", location: "Remote" },
  { title: "ML Engineer, Recommendations", team: "AI/ML", location: "Remote" },
  { title: "Product Designer", team: "Design", location: "Remote" },
  { title: "Backend Engineer, Pricing Data", team: "Engineering", location: "Remote" }
];

const PERKS = [
  "Fully remote, async-friendly team",
  "Flexible hours - work when you're sharpest",
  "Health coverage and annual learning budget",
  "A small team where your work ships fast"
];

export const metadata = { title: "Careers | AI Shopping Intelligence Platform" };

export default function CareersPage() {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        <section className="py-24">
          <div className="mx-auto max-w-3xl px-4 text-center sm:px-8">
            <p className="label-caps text-brand-600">Careers</p>
            <h1 className="mt-2 text-4xl font-bold text-ink lg:text-5xl">Help us build the smartest way to shop.</h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-slate-600">
              We&apos;re a small, remote-first team obsessed with making purchase decisions easier. If that sounds like your kind of problem, we&apos;d like to hear from you.
            </p>
          </div>
        </section>

        <section className="pb-16">
          <div className="mx-auto max-w-4xl px-4 sm:px-8">
            <div className="card grid grid-cols-2 gap-6 p-8 sm:grid-cols-4">
              {PERKS.map((perk) => (
                <div key={perk} className="flex items-start gap-2 text-sm text-slate-600">
                  <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />
                  {perk}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto max-w-4xl px-4 sm:px-8">
            <h2 className="mb-8 text-2xl font-bold text-ink">Open roles</h2>
            <div className="space-y-4">
              {ROLES.map((role) => (
                <a
                  key={role.title}
                  href={`mailto:careers@pricewise.app?subject=${encodeURIComponent(`Application: ${role.title}`)}`}
                  className="card flex flex-col items-start justify-between gap-3 p-6 sm:flex-row sm:items-center"
                >
                  <div>
                    <p className="font-bold text-ink">{role.title}</p>
                    <p className="mt-1 text-sm text-slate-500">{role.team} · {role.location}</p>
                  </div>
                  <span className="btn-secondary shrink-0">Apply <Icon name="arrow" className="ml-2 h-4 w-4" /></span>
                </a>
              ))}
            </div>
            <p className="mt-8 text-sm text-slate-500">
              Don&apos;t see a fit? Reach out anyway at <a href="mailto:careers@pricewise.app" className="font-semibold text-brand-700 hover:underline">careers@pricewise.app</a>.
            </p>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
