import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

const POSTS = [
  { title: "How the AI recommendation engine actually works", excerpt: "A behind-the-scenes look at how Pricewise turns a budget and a wish list into a ranked shortlist.", date: "Jul 2026", readTime: "6 min read" },
  { title: "5 habits of shoppers who never overpay", excerpt: "Small, repeatable habits that consistently beat impulse buying - and how to automate them.", date: "Jun 2026", readTime: "4 min read" },
  { title: "Warranty tracking: the spending leak nobody notices", excerpt: "Why claim windows quietly expire, and what a five-second receipt scan fixes for good.", date: "May 2026", readTime: "5 min read" },
  { title: "Reading reviews at scale without losing your mind", excerpt: "How review intelligence separates a real pattern of complaints from a handful of outliers.", date: "Apr 2026", readTime: "7 min read" }
];

export const metadata = { title: "Blog | Pricewise" };

export default function BlogPage() {
  return (
    <div className="bg-surface">
      <SiteNav />
      <main className="page-enter pt-28">
        <section className="py-24">
          <div className="mx-auto max-w-3xl px-4 text-center sm:px-8">
            <p className="label-caps text-brand-600">Blog</p>
            <h1 className="mt-2 text-4xl font-bold text-ink lg:text-5xl">Notes on shopping smarter.</h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-slate-600">
              Product updates, buying guides, and the occasional deep dive into how Pricewise is built.
            </p>
          </div>
        </section>

        <section className="pb-24">
          <div className="mx-auto max-w-5xl px-4 sm:px-8">
            <div className="grid gap-6 sm:grid-cols-2">
              {POSTS.map((post) => (
                <article key={post.title} className="card h-full p-8">
                  <p className="label-caps text-brand-600">{post.date} · {post.readTime}</p>
                  <h2 className="mb-3 mt-2 text-xl font-bold text-ink">{post.title}</h2>
                  <p className="text-slate-600">{post.excerpt}</p>
                </article>
              ))}
            </div>
            <p className="mt-10 text-center text-sm text-slate-500">More posts coming soon.</p>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
