import { FeaturePage } from "@/components/feature-page";
import { Icon } from "@/components/icons";

function AiPicksMockup() {
  return (
    <div className="card space-y-3 p-6">
      <div className="shadow-neu-inset-sm space-y-2 rounded-2xl p-4 text-xs text-slate-500">
        <p><span className="font-semibold text-ink">Budget:</span> $350</p>
        <p><span className="font-semibold text-ink">Purpose:</span> Noise-cancelling for daily commute</p>
      </div>
      <div className="flex justify-center text-brand-300">
        <Icon name="arrow" className="h-5 w-5 rotate-90" />
      </div>
      <div className="shadow-neu space-y-3 rounded-2xl p-5">
        <div className="flex items-center justify-between">
          <span className="label-caps text-brand-700">#1 match</span>
          <span className="pill bg-brand-100 text-brand-700">Best value</span>
        </div>
        <p className="font-bold text-ink">Sony WH-1000XM5</p>
        <p className="data text-2xl font-extrabold text-brand-700">$328.00</p>
        <p className="text-xs leading-relaxed text-slate-500">Matches your budget with class-leading noise cancellation and 30-hour battery life.</p>
      </div>
    </div>
  );
}

export const metadata = { title: "AI Picks | AI Shopping Intelligence Platform" };

export default function AiPicksFeaturePage() {
  return (
    <FeaturePage
      name="AI Picks"
      eyebrow="AI Picks"
      icon="sparkles"
      title="Describe what you need. Get a ranked shortlist."
      description="Tell the AI your budget, purpose, and must-have features - it searches the live catalog and hands back a ranked shortlist with a plain-English reason for every pick, not just a score."
      mockup={<AiPicksMockup />}
      howItWorks={[
        { title: "Describe your needs", body: "Fill in a budget, purpose, brand preference, and any must-have features - as little or as much detail as you want." },
        { title: "AI searches the catalog", body: "The engine checks live listings and reviews against what you described, not a static database." },
        { title: "Get ranked, explained picks", body: "Review up to ten real, purchasable options ranked by fit, each with a plain-English reason." }
      ]}
      guide={[
        { title: "Open AI Picks", body: "Sign in and select \"AI Picks\" from the sidebar." },
        { title: "Fill in the form", body: "Enter a category, budget, and purpose at minimum - brand preference and must-have features are optional but sharpen the results." },
        { title: "Tap \"Get recommendations\"", body: "The engine ranks matching products from the live catalog in a few seconds." },
        { title: "Read the reasoning", body: "Each pick includes why it was chosen, so you can judge the recommendation instead of just trusting a score." }
      ]}
      faqs={[
        { q: "How many products does it recommend?", a: "Up to ten ranked, real, purchasable listings per request - enough to compare without being overwhelming." },
        { q: "Does it consider reviews, not just price?", a: "Yes - recommendations weigh review sentiment and specs against your stated needs, not price alone." },
        { q: "Can I ask for alternatives to a pick?", a: "Yes - refine your budget or must-have features and re-run the request, or ask Shopping Chat for alternatives to any specific pick." },
        { q: "Is brand preference required?", a: "No - it's optional. Leave it blank and AI Picks will consider every brand in the catalog." }
      ]}
    />
  );
}
