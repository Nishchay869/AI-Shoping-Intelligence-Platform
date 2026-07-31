"use client";
import { ChangeEvent, useState } from "react";
import { Icon } from "@/components/icons";

type ReceiptItem = { product_name: string; price_minor: number; quantity: number };
type ReceiptScanResult = {
  id: string;
  store_name: string | null;
  purchase_date: string | null;
  subtotal_minor: number | null;
  tax_minor: number | null;
  total_minor: number | null;
  currency: string;
  warranty_text: string | null;
  ocr_confidence: number | null;
  items: ReceiptItem[];
  saved: boolean;
};

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(minorUnits / 100);

/** AI Receipt Scanner: Tesseract OCR reads the photo, then Gemini structures the raw text into JSON - product names, price, tax, date, store name, warranty. */
export default function ReceiptsPage() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ReceiptScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await fetch("/api/v1/receipts/scan", { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not read that receipt.");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p className="label-caps text-brand-600">AI Receipt Scanner</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Scan a receipt</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">Upload a photo of a paper receipt. Tesseract OCR reads the raw text, then Gemini structures it into product names, price, tax, date, store name, and any warranty terms.</p>

      <div className="card mt-6 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border-2 border-dashed border-slate-200 p-6">
          <div>
            <h2 className="font-bold text-ink">Upload receipt photo</h2>
            <p className="mt-1 text-sm text-slate-500">JPG, PNG, or WEBP, up to 10MB.</p>
          </div>
          <label className="btn-primary cursor-pointer">
            <Icon name="receipt" className="mr-2 h-4 w-4" />
            Upload receipt photo
            <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
          </label>
        </div>

        {previewUrl && (
          <div className="mt-4 flex items-center gap-4">
            <img src={previewUrl} alt="Uploaded receipt" className="h-24 w-24 rounded-xl border border-slate-200 object-cover" />
            {loading && <p className="text-sm text-slate-400">Running OCR and extracting structured fields…</p>}
          </div>
        )}
        {error && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

        {result && (
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            <div className="card p-5 lg:col-span-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-bold text-ink">{result.store_name ?? "Unknown store"}</h3>
                <span className={`pill ${result.saved ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{result.saved ? "Saved to history" : "Sign in to save to history"}</span>
              </div>
              <p className="mt-1 text-sm text-slate-500">{result.purchase_date ?? "Date not legible"} · OCR confidence <span className="data">{result.ocr_confidence !== null ? `${Math.round(result.ocr_confidence * 100)}%` : "n/a"}</span></p>

              <table className="mt-4 w-full text-sm">
                <thead><tr className="border-b border-slate-100 text-left"><th className="pb-2 label-caps">Product</th><th className="pb-2 text-center label-caps">Qty</th><th className="pb-2 text-right label-caps">Price</th></tr></thead>
                <tbody>
                  {result.items.map((item, index) => (
                    <tr key={index} className="border-b border-slate-100 last:border-0">
                      <td className="py-2 text-ink">{item.product_name}</td>
                      <td className="data py-2 text-center text-slate-500">{item.quantity}</td>
                      <td className="data py-2 text-right font-medium text-ink">{formatPrice(item.price_minor, result.currency)}</td>
                    </tr>
                  ))}
                  {result.items.length === 0 && <tr><td colSpan={3} className="py-4 text-center text-slate-400">No line items were legible on this receipt.</td></tr>}
                </tbody>
              </table>

              {result.warranty_text && <div className="mt-4 rounded-xl bg-brand-50 p-3 text-sm text-brand-700"><span className="font-semibold">Warranty / return policy: </span>{result.warranty_text}</div>}
            </div>

            <div className="card space-y-3 p-5">
              <h3 className="font-bold text-ink">Totals</h3>
              <div className="flex justify-between text-sm"><span className="text-slate-500">Subtotal</span><span className="data text-ink">{result.subtotal_minor !== null ? formatPrice(result.subtotal_minor, result.currency) : "—"}</span></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">Tax</span><span className="data text-ink">{result.tax_minor !== null ? formatPrice(result.tax_minor, result.currency) : "—"}</span></div>
              <div className="flex justify-between border-t border-slate-100 pt-3 text-base font-bold"><span className="text-ink">Total</span><span className="data text-ink">{result.total_minor !== null ? formatPrice(result.total_minor, result.currency) : "—"}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
