import { FeaturePage } from "@/components/feature-page";
import { Icon } from "@/components/icons";

function ReceiptMockup() {
  return (
    <div className="card space-y-4 p-6">
      <div className="shadow-neu-inset-sm space-y-2 rounded-2xl p-4 font-mono text-xs text-slate-600">
        <p className="flex justify-between"><span>WH-1000XM5 Headphones</span><span>₹24,990</span></p>
        <p className="flex justify-between"><span>Extended Warranty</span><span>₹1,500</span></p>
        <div className="my-1 border-t border-dashed border-slate-300" />
        <p className="flex justify-between font-bold text-ink"><span>Total</span><span>₹26,490</span></p>
      </div>
      <div className="shadow-neu-sm flex items-center gap-2 rounded-xl p-3 text-xs font-semibold text-brand-600">
        <Icon name="shield" className="h-4 w-4 shrink-0" />
        Warranty tracked - expires Jul 2027
      </div>
    </div>
  );
}

export const metadata = { title: "Receipt Scanner | AI Shopping Intelligence Platform" };

export default function ReceiptScannerFeaturePage() {
  return (
    <FeaturePage
      name="Receipt Scanner"
      eyebrow="Receipt Scanner"
      icon="receipt"
      title="Snap a receipt. Never lose track of a warranty again."
      description="Photograph a paper receipt and Shopping AI extracts the items, prices, and warranty terms automatically - so your spending is tracked and you get a reminder before a claim window closes."
      mockup={<ReceiptMockup />}
      howItWorks={[
        { title: "Upload a photo", body: "Take a picture of a paper receipt, or upload one you already have saved." },
        { title: "AI extracts the details", body: "Items, prices, retailer, and warranty terms are pulled from the receipt automatically." },
        { title: "Get tracked automatically", body: "The purchase is added to your spending history, with a warranty reminder set before it expires." }
      ]}
      guide={[
        { title: "Open Receipt Scanner", body: "Sign in and select \"Receipt Scanner\" from the sidebar." },
        { title: "Upload your receipt", body: "Tap upload and choose a photo of the receipt - a clear, well-lit shot works best." },
        { title: "Review the extracted items", body: "Check that the items, prices, and total were read correctly before saving." },
        { title: "Get reminded before it expires", body: "Shopping AI tracks the warranty window and alerts you before a claim deadline passes." }
      ]}
      faqs={[
        { q: "What file types are supported?", a: "Standard photo formats (JPEG, PNG) work well - a clear, flat, well-lit photo of the receipt gives the most accurate extraction." },
        { q: "Is my receipt data private?", a: "Yes - receipt images and extracted details are stored on your account only and are never sold to third parties. See the Privacy Policy for details." },
        { q: "Does it work with handwritten receipts?", a: "Printed receipts are read most reliably; handwritten receipts may need manual correction after extraction." },
        { q: "What happens as a warranty gets close to expiring?", a: "Shopping AI sends a reminder ahead of the claim window closing, based on the warranty terms extracted from the receipt." }
      ]}
    />
  );
}
