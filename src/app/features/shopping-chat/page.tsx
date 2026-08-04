import { FeaturePage } from "@/components/feature-page";
import { Icon } from "@/components/icons";

function ChatMockup() {
  return (
    <div className="card space-y-3 p-6">
      <div className="flex justify-end">
        <div className="shadow-neu-sm max-w-[75%] rounded-2xl rounded-tr-sm bg-brand-600 px-3 py-2 text-sm leading-6 text-white">
          Compare the Sony headphones with the Bose earbuds
        </div>
      </div>
      <div className="flex justify-start">
        <div className="shadow-neu-inset-sm max-w-[85%] rounded-2xl rounded-tl-sm bg-surface px-3 py-2 text-sm leading-6 text-ink">
          The Sony WH-1000XM5 has stronger noise cancellation and a 30-hour battery; the Bose is lighter and about $40 cheaper.
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="pill bg-slate-200/70 text-blue-600">Amazon ↗</span>
            <span className="pill bg-slate-200/70 text-blue-600">Reviews ↗</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export const metadata = { title: "Shopping Chat | Pricewise" };

export default function ShoppingChatFeaturePage() {
  return (
    <FeaturePage
      name="Shopping Chat"
      eyebrow="Shopping Chat"
      icon="message"
      title="Ask before you buy - and get a grounded answer."
      description="A conversational assistant that compares products, explains specs, and answers questions about reviews or the market, with every answer citing the source it came from."
      mockup={<ChatMockup />}
      howItWorks={[
        { title: "Ask a question", body: "Type anything in plain English - compare two products, ask about a spec, or request alternatives." },
        { title: "It searches the catalog, reviews, and web", body: "The assistant pulls from the live product catalog, buyer reviews, and general market info to ground its answer." },
        { title: "Get a cited answer", body: "Responses come with source links so you can verify anything before you rely on it." }
      ]}
      guide={[
        { title: "Open Shopping Chat", body: "Sign in and select \"Shopping Chat\" from the sidebar, or tap the floating chat button on any page." },
        { title: "Ask your question", body: "Type your own question, or tap one of the suggested prompts to get started." },
        { title: "Keep the conversation going", body: "Ask follow-up questions naturally - the assistant remembers the thread's context." },
        { title: "Check the sources", body: "Tap any cited source pill under an answer to see exactly where that information came from." }
      ]}
      faqs={[
        { q: "Does it remember earlier questions in the conversation?", a: "Yes - each conversation has persistent memory for its thread, so follow-up questions carry context." },
        { q: "Are the cited sources real?", a: "Yes - every source pill links to the actual listing, review, or page the answer drew from." },
        { q: "Can it compare products from different stores?", a: "Yes - ask it to compare any two products regardless of which retailer lists them." },
        { q: "Can I start a fresh conversation?", a: "Yes - use the restart button in the chat window to clear the thread and start over." }
      ]}
    />
  );
}
