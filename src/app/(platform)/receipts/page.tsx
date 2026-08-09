"use client";
import { ChangeEvent, useEffect, useState } from "react";
import { Icon } from "@/components/icons";
import { Tabs } from "@/components/form-controls";
import { authHeaders } from "@/shared/auth/token";

type ReceiptItem = { product_name: string; price_minor: number; quantity: number };
type ReceiptSummary = {
  id: string;
  store_name: string | null;
  purchase_date: string | null;
  subtotal_minor: number | null;
  tax_minor: number | null;
  total_minor: number | null;
  currency: string;
  warranty_text: string | null;
  warranty_expires_at: string | null;
  ocr_confidence: number | null;
  items: ReceiptItem[];
};
type ReceiptScanResult = ReceiptSummary & { saved: boolean };

const formatPrice = (minorUnits: number, currency: string) => new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(minorUnits / 100);

const TABS = [
  { id: "scan" as const, label: "Scan", icon: "receipt" as const },
  { id: "history" as const, label: "History", icon: "clock" as const },
];
type TabId = (typeof TABS)[number]["id"];

/** Shared read-only rendering for one receipt's structured fields - used by the just-scanned result and by
 * an expanded row in the history list, so both stay visually identical. */
function ReceiptDetailCard({ receipt, badge }: { receipt: ReceiptSummary; badge?: React.ReactNode }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="card p-5 lg:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-bold text-ink">{receipt.store_name ?? "Unknown store"}</h3>
          {badge}
        </div>
        <p className="mt-1 text-sm text-slate-500">{receipt.purchase_date ?? "Date not legible"} · OCR confidence <span className="data">{receipt.ocr_confidence !== null ? `${Math.round(receipt.ocr_confidence * 100)}%` : "n/a"}</span></p>

        <table className="mt-4 w-full text-sm">
          <thead><tr className="border-b border-slate-100 text-left"><th className="pb-2 label-caps">Product</th><th className="pb-2 text-center label-caps">Qty</th><th className="pb-2 text-right label-caps">Price</th></tr></thead>
          <tbody>
            {receipt.items.map((item, index) => (
              <tr key={index} className="border-b border-slate-100 last:border-0">
                <td className="py-2 text-ink">{item.product_name}</td>
                <td className="data py-2 text-center text-slate-500">{item.quantity}</td>
                <td className="data py-2 text-right font-medium text-ink">{formatPrice(item.price_minor, receipt.currency)}</td>
              </tr>
            ))}
            {receipt.items.length === 0 && <tr><td colSpan={3} className="py-4 text-center text-slate-400">No line items were legible on this receipt.</td></tr>}
          </tbody>
        </table>

        {receipt.warranty_text && (
          <div className="mt-4 rounded-xl bg-brand-50 p-3 text-sm text-brand-700">
            <span className="font-semibold">Warranty / return policy: </span>{receipt.warranty_text}
            {receipt.warranty_expires_at && <span className="mt-1 block text-xs text-brand-600">Expires {receipt.warranty_expires_at} - you&apos;ll get a WhatsApp alert before it lapses if enabled.</span>}
          </div>
        )}
      </div>

      <div className="card space-y-3 p-5">
        <h3 className="font-bold text-ink">Totals</h3>
        <div className="flex justify-between text-sm"><span className="text-slate-500">Subtotal</span><span className="data text-ink">{receipt.subtotal_minor !== null ? formatPrice(receipt.subtotal_minor, receipt.currency) : "—"}</span></div>
        <div className="flex justify-between text-sm"><span className="text-slate-500">Tax</span><span className="data text-ink">{receipt.tax_minor !== null ? formatPrice(receipt.tax_minor, receipt.currency) : "—"}</span></div>
        <div className="flex justify-between border-t border-slate-100 pt-3 text-base font-bold"><span className="text-ink">Total</span><span className="data text-ink">{receipt.total_minor !== null ? formatPrice(receipt.total_minor, receipt.currency) : "—"}</span></div>
      </div>
    </div>
  );
}

/** AI Receipt Scanner: Tesseract OCR reads the photo, then Gemini structures the raw text into JSON - product names, price, tax, date, store name, warranty. Signed-in scans are saved and browsable under History. */
export default function ReceiptsPage() {
  const [tab, setTab] = useState<TabId>("scan");

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ReceiptScanResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [historyList, setHistoryList] = useState<ReceiptSummary[] | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (tab !== "history" || historyList !== null) return;
    (async () => {
      try {
        const response = await fetch("/api/v1/receipts", { headers: await authHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not load your receipt history.");
        setHistoryList(data);
      } catch (err) {
        setHistoryError(err instanceof Error ? err.message : "Could not load your receipt history.");
        setHistoryList([]);
      }
    })();
  }, [tab, historyList]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  }

  function resetScan() {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
  }

  async function runScan() {
    if (!selectedFile) return;
    setScanning(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      const response = await fetch("/api/v1/receipts/scan", { method: "POST", body: formData, headers: await authHeaders() });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : data.error ?? "Could not read that receipt.");
      setResult(data);
      if (data.saved) setHistoryList(null); // invalidate the cached history list so it re-fetches and includes this scan
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setScanning(false);
    }
  }

  async function deleteReceipt(id: string) {
    setDeletingId(id);
    try {
      const response = await fetch(`/api/v1/receipts/${id}`, { method: "DELETE", headers: await authHeaders() });
      if (!response.ok) throw new Error("Could not delete that receipt.");
      setHistoryList((current) => current?.filter((receipt) => receipt.id !== id) ?? current);
      if (expandedId === id) setExpandedId(null);
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : "Could not delete that receipt.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <p className="label-caps text-brand-600">AI Receipt Scanner</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Scan a receipt</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">Upload a photo of a paper receipt. Tesseract OCR reads the raw text, then Gemini structures it into product names, price, tax, date, store name, and any warranty terms.</p>

      <div className="mt-6">
        <Tabs tabs={TABS} active={tab} onChange={setTab} />
      </div>

      {tab === "scan" && (
        <div className="card mt-6 p-6">
          <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border-2 border-dashed border-slate-200 p-6">
            <div>
              <h2 className="font-bold text-ink">Upload receipt photo</h2>
              <p className="mt-1 text-sm text-slate-500">JPG, PNG, or WEBP, up to 10MB.</p>
            </div>
            <label className="btn-primary cursor-pointer">
              <Icon name="receipt" className="mr-2 h-4 w-4" />
              {previewUrl ? "Choose a different photo" : "Upload receipt photo"}
              <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
            </label>
          </div>

          {previewUrl && (
            <div className="mt-4 flex flex-wrap items-start gap-4">
              <div className="relative h-40 w-40 shrink-0 overflow-hidden rounded-xl border border-slate-200">
                <img src={previewUrl} alt="Uploaded receipt" className="h-full w-full object-cover" />
                {scanning && (
                  <div className="absolute inset-0 bg-ink/15">
                    <span className="absolute inset-x-0 h-8 animate-scan-sweep bg-gradient-to-b from-transparent via-brand-400/80 to-transparent shadow-[0_0_12px_2px_rgba(99,102,241,0.6)]" />
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                {!result && (
                  <button type="button" onClick={runScan} disabled={scanning} className="btn-primary">
                    {scanning ? (<><Icon name="restart" className="mr-2 h-4 w-4 animate-spin" />Scanning receipt…</>) : (<><Icon name="receipt" className="mr-2 h-4 w-4" />Scan receipt</>)}
                  </button>
                )}
                {result && <button type="button" onClick={resetScan} className="btn-primary">Scan another receipt</button>}
                {!scanning && <button type="button" onClick={resetScan} className="btn-secondary">Remove photo</button>}
              </div>
            </div>
          )}
          {error && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

          {result && (
            <div className="mt-6">
              <ReceiptDetailCard
                receipt={result}
                badge={<span className={`pill ${result.saved ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{result.saved ? "Saved to history" : "Sign in to save to history"}</span>}
              />
            </div>
          )}
        </div>
      )}

      {tab === "history" && (
        <div className="card mt-6 p-6">
          <h2 className="font-bold text-ink">Scanned receipts</h2>
          {historyError && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{historyError}</div>}
          {historyList === null && !historyError && <p className="mt-4 text-sm text-slate-400">Loading your receipt history…</p>}
          {historyList !== null && historyList.length === 0 && <p className="mt-4 text-sm text-slate-400">No receipts scanned yet.</p>}
          <div className="mt-4 divide-y divide-slate-100">
            {historyList?.map((receipt) => {
              const expanded = expandedId === receipt.id;
              return (
                <div key={receipt.id} className="py-3">
                  <div className="flex w-full items-center justify-between gap-3">
                    <button type="button" onClick={() => setExpandedId(expanded ? null : receipt.id)} className="flex flex-1 items-center justify-between gap-3 text-left">
                      <span>
                        <span className="block text-sm font-semibold text-ink">{receipt.store_name ?? "Unknown store"}</span>
                        <span className="mt-0.5 block text-xs text-slate-500">{receipt.purchase_date ?? "Date not legible"} · {receipt.items.length} item{receipt.items.length === 1 ? "" : "s"}</span>
                      </span>
                      <span className="flex items-center gap-3">
                        <span className="data text-sm font-bold text-ink">{receipt.total_minor !== null ? formatPrice(receipt.total_minor, receipt.currency) : "—"}</span>
                        <Icon name="arrow" className={`h-4 w-4 text-slate-400 transition-transform ${expanded ? "rotate-90" : ""}`} />
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteReceipt(receipt.id)}
                      disabled={deletingId === receipt.id}
                      aria-label="Delete receipt"
                      className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"
                    >
                      <Icon name="x" className="h-4 w-4" />
                    </button>
                  </div>
                  {expanded && <div className="mt-4"><ReceiptDetailCard receipt={receipt} /></div>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
