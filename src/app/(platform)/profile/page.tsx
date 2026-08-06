"use client";
import { useEffect, useRef, useState } from "react";
import { Icon, type IconName } from "@/components/icons";
import { Segmented, Slider, TagInput, Tabs, Toggle } from "@/components/form-controls";
import { authHeaders } from "@/shared/auth/token";
import { displayNameFor, useCurrentUser } from "@/shared/auth/use-current-user";

type Preferences = {
  notify_email: boolean;
  notify_push: boolean;
  notify_sms: boolean;
  notify_whatsapp: boolean;
  phone_number: string | null;
  phone_verified: boolean;
  min_discount_percentage: number | null;
  alert_all_time_low: boolean;
  alert_below_90d_average: boolean;
  notification_frequency: "instant" | "daily_digest" | "weekly_summary";
  favorite_brands: string[];
  blacklisted_brands: string[];
  preferred_retailers: string[];
  budget_tier: "budget" | "balanced" | "premium" | null;
  sizing_profile: Record<string, string>;
  include_refurbished: boolean;
  restock_alerts_enabled: boolean;
  auto_buy_enabled: boolean;
};

const DEFAULT_PREFERENCES: Preferences = {
  notify_email: true, notify_push: true, notify_sms: false, notify_whatsapp: false,
  phone_number: null, phone_verified: false,
  min_discount_percentage: 15, alert_all_time_low: false, alert_below_90d_average: false,
  notification_frequency: "instant",
  favorite_brands: [], blacklisted_brands: [], preferred_retailers: [],
  budget_tier: null, sizing_profile: {},
  include_refurbished: false, restock_alerts_enabled: false, auto_buy_enabled: false,
};

const RETAILERS = [{ code: "amazon", label: "Amazon" }, { code: "flipkart", label: "Flipkart" }, { code: "myntra", label: "Myntra" }];

const INTEGRATIONS: { label: string; icon: IconName }[] = [
  { label: "Import Amazon Wishlist", icon: "bag" },
  { label: "Browser extension", icon: "cpu" },
  { label: "Email receipt scanning", icon: "mail" },
];

const TABS = [
  { id: "general" as const, label: "General & Alerts", icon: "bell" as const },
  { id: "ai" as const, label: "AI Preferences", icon: "sparkles" as const },
  { id: "smart" as const, label: "Smart Rules", icon: "cpu" as const },
  { id: "integrations" as const, label: "Integrations", icon: "gift" as const },
];
type TabId = (typeof TABS)[number]["id"];

/** Profile page manages user-visible preferences and explicit notification consent - alert trigger
 * rules, AI shopping persona, smart-rule toggles, and (placeholder) integrations, all backed by the
 * real /api/v1/preferences endpoint. */
export default function ProfilePage() {
  const user = useCurrentUser();
  const [tab, setTab] = useState<TabId>("general");
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFERENCES);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [phoneStatus, setPhoneStatus] = useState<string | null>(null);

  const [editingName, setEditingName] = useState(false);
  const [editingEmail, setEditingEmail] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (editingName) { nameInputRef.current?.focus(); nameInputRef.current?.select(); } }, [editingName]);
  useEffect(() => { if (editingEmail) { emailInputRef.current?.focus(); emailInputRef.current?.select(); } }, [editingEmail]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      const response = await fetch("/api/v1/preferences", { headers: await authHeaders() });
      if (cancelled || !response.ok) return;
      const data: Preferences = await response.json();
      setPrefs(data);
      setPhone(data.phone_number ?? "");
      setLoaded(true);
    })();
    return () => { cancelled = true; };
  }, [user]);

  function set<K extends keyof Preferences>(key: K, value: Preferences[K]) {
    setPrefs((current) => ({ ...current, [key]: value }));
  }

  function setSizing(key: string, value: string) {
    setPrefs((current) => ({ ...current, sizing_profile: { ...current.sizing_profile, [key]: value } }));
  }

  function toggleRetailer(code: string) {
    setPrefs((current) => ({
      ...current,
      preferred_retailers: current.preferred_retailers.includes(code)
        ? current.preferred_retailers.filter((value) => value !== code)
        : [...current.preferred_retailers, code],
    }));
  }

  async function save() {
    setSaving(true);
    setSaveError(null);
    try {
      const response = await fetch("/api/v1/preferences", { method: "PATCH", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify(prefs) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Could not save your preferences.");
      setPrefs(data);
      setEditingName(false);
      setEditingEmail(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 1800);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save your preferences.");
    } finally {
      setSaving(false);
    }
  }

  async function sendCode() {
    setSendingCode(true);
    setPhoneStatus(null);
    try {
      const response = await fetch("/api/v1/preferences/phone/verify", { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ phone_number: phone }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Could not send a verification code.");
      setOtpSent(true);
      setPhoneStatus(data.dev_code ? `No SMS provider is configured yet - your dev code is ${data.dev_code}.` : "Code sent.");
    } catch (err) {
      setPhoneStatus(err instanceof Error ? err.message : "Could not send a verification code.");
    } finally {
      setSendingCode(false);
    }
  }

  async function confirmCode() {
    setPhoneStatus(null);
    try {
      const response = await fetch("/api/v1/preferences/phone/confirm", { method: "POST", headers: { "Content-Type": "application/json", ...(await authHeaders()) }, body: JSON.stringify({ code: otp }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Incorrect or expired code.");
      setPrefs(data);
      setOtpSent(false);
      setOtp("");
      setPhoneStatus("Phone verified.");
    } catch (err) {
      setPhoneStatus(err instanceof Error ? err.message : "Could not verify that code.");
    }
  }

  return (
    <div className="max-w-3xl">
      <p className="label-caps text-brand-600">Account</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Profile &amp; preferences</h1>

      <div className="mt-6">
        <Tabs tabs={TABS} active={tab} onChange={setTab} />
      </div>

      {!loaded && <p className="mt-6 text-sm text-slate-400">Loading your preferences…</p>}

      {tab === "general" && (
        <>
          <section className="card mt-6 p-6">
            <h2 className="text-lg font-bold text-ink">Personal details</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {/* key remounts the (uncontrolled) input once the real user loads, so its defaultValue - only applied on mount - picks up the fetched name/email instead of staying blank. Disabled by
              default so an accidental keystroke can't change either field - the pencil button unlocks it for editing. */}
              <label className="block">
                <span className="label-caps">Name</span>
                <div className="mt-2 flex items-center gap-2">
                  <input ref={nameInputRef} key={user?.id ?? "loading"} className="input flex-1 disabled:cursor-not-allowed disabled:text-slate-500 disabled:opacity-80" defaultValue={displayNameFor(user)} disabled={!editingName} />
                  <button
                    type="button"
                    onClick={() => setEditingName((value) => !value)}
                    aria-label={editingName ? "Lock name field" : "Edit name"}
                    aria-pressed={editingName}
                    className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl transition-colors ${editingName ? "bg-brand-50 text-brand-600 shadow-neu-inset-sm" : "bg-surface text-slate-500 shadow-neu-sm hover:text-brand-600"}`}
                  >
                    <Icon name="edit" className="h-4 w-4" />
                  </button>
                </div>
              </label>
              <label className="block">
                <span className="label-caps">Email</span>
                <div className="mt-2 flex items-center gap-2">
                  <input ref={emailInputRef} key={user?.id ?? "loading"} className="input flex-1 disabled:cursor-not-allowed disabled:text-slate-500 disabled:opacity-80" type="email" defaultValue={user?.email ?? ""} disabled={!editingEmail} />
                  <button
                    type="button"
                    onClick={() => setEditingEmail((value) => !value)}
                    aria-label={editingEmail ? "Lock email field" : "Edit email"}
                    aria-pressed={editingEmail}
                    className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl transition-colors ${editingEmail ? "bg-brand-50 text-brand-600 shadow-neu-inset-sm" : "bg-surface text-slate-500 shadow-neu-sm hover:text-brand-600"}`}
                  >
                    <Icon name="edit" className="h-4 w-4" />
                  </button>
                </div>
              </label>
            </div>
          </section>

          <section className="card mt-5 p-6">
            <h2 className="text-lg font-bold text-ink">Notification channels</h2>
            <p className="mt-1 text-sm text-slate-500">Choose how you receive price alerts. SMS and WhatsApp require a verified phone number.</p>
            <div className="mt-5 divide-y divide-slate-100">
              {([["Email", "notify_email"], ["Browser notifications", "notify_push"], ["SMS", "notify_sms"], ["WhatsApp", "notify_whatsapp"]] as const).map(([label, key]) => (
                <label key={key} className="flex items-center justify-between py-3 text-sm font-medium text-ink">
                  <span>{label}</span>
                  <input className="h-5 w-5 accent-brand-600" type="checkbox" checked={prefs[key]} onChange={(e) => set(key, e.target.checked)} />
                </label>
              ))}
            </div>

            <div className="mt-4 rounded-xl border border-slate-200 p-4">
              <p className="label-caps">Verified phone number</p>
              <p className="mt-1 text-xs text-slate-500">Needed to actually receive SMS/WhatsApp alerts.</p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <input className="input max-w-56" placeholder="+91 98765 43210" value={phone} onChange={(e) => setPhone(e.target.value)} disabled={otpSent} />
                {prefs.phone_verified && phone === prefs.phone_number ? (
                  <span className="pill flex items-center gap-1 bg-emerald-50 text-emerald-700"><Icon name="check" className="h-3 w-3" />Verified</span>
                ) : otpSent ? (
                  <>
                    <input className="input w-28" placeholder="6-digit code" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value)} />
                    <button type="button" onClick={confirmCode} className="btn-secondary">Verify</button>
                  </>
                ) : (
                  <button type="button" onClick={sendCode} disabled={!phone.trim() || sendingCode} className="btn-secondary">{sendingCode ? "Sending…" : "Send code"}</button>
                )}
              </div>
              {phoneStatus && <p className="mt-2 text-xs text-slate-500">{phoneStatus}</p>}
            </div>
          </section>

          <section className="card mt-5 p-6">
            <h2 className="text-lg font-bold text-ink">Alert trigger rules</h2>
            <p className="mt-1 text-sm text-slate-500">Control when the AI actually pings you, so alerts stay worth opening.</p>
            <div className="mt-5">
              <Slider label="Minimum discount to alert on" value={prefs.min_discount_percentage ?? 0} onChange={(value) => set("min_discount_percentage", value)} min={0} max={90} step={5} formatValue={(value) => `≥ ${value}%`} />
            </div>
            <div className="mt-2 divide-y divide-slate-100">
              <Toggle label="Only alert at an all-time low" description="Skip everyday drops - only notify when the price hits its lowest point ever tracked." checked={prefs.alert_all_time_low} onChange={(value) => set("alert_all_time_low", value)} />
              <Toggle label="Only alert below the 90-day average" description="Filters out noise from short-lived promo pricing." checked={prefs.alert_below_90d_average} onChange={(value) => set("alert_below_90d_average", value)} />
            </div>
            <div className="mt-4">
              <p className="label-caps mb-2">Notification frequency</p>
              <Segmented value={prefs.notification_frequency} onChange={(value) => set("notification_frequency", value)} options={[{ value: "instant", label: "Instant" }, { value: "daily_digest", label: "Daily digest" }, { value: "weekly_summary", label: "Weekly summary" }]} />
            </div>
          </section>
        </>
      )}

      {tab === "ai" && (
        <section className="card mt-6 p-6">
          <h2 className="text-lg font-bold text-ink">AI shopping persona</h2>
          <p className="mt-1 text-sm text-slate-500">Feeds recommendations and alerts so they stay relevant to what you&apos;d actually buy.</p>

          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <label className="block"><span className="label-caps">Favorite brands</span><div className="mt-2"><TagInput values={prefs.favorite_brands} onChange={(value) => set("favorite_brands", value)} placeholder="e.g. Apple, Nike" /></div></label>
            <label className="block"><span className="label-caps">Blacklisted brands</span><div className="mt-2"><TagInput values={prefs.blacklisted_brands} onChange={(value) => set("blacklisted_brands", value)} placeholder="Never show me these" /></div></label>
          </div>

          <div className="mt-5">
            <p className="label-caps mb-2">Preferred stores</p>
            <div className="flex flex-wrap gap-2">
              {RETAILERS.map((retailer) => (
                <label key={retailer.code} className={`flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition-colors ${prefs.preferred_retailers.includes(retailer.code) ? "bg-brand-50 text-brand-700 shadow-neu-inset-sm" : "bg-surface text-slate-600 shadow-neu-sm"}`}>
                  <input type="checkbox" className="h-4 w-4 accent-brand-600" checked={prefs.preferred_retailers.includes(retailer.code)} onChange={() => toggleRetailer(retailer.code)} />
                  {retailer.label}
                </label>
              ))}
            </div>
          </div>

          <div className="mt-5">
            <p className="label-caps mb-2">Budget &amp; quality tier</p>
            <Segmented value={prefs.budget_tier ?? "balanced"} onChange={(value) => set("budget_tier", value)} options={[{ value: "budget", label: "Budget-conscious" }, { value: "balanced", label: "Best value" }, { value: "premium", label: "Premium" }]} />
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <label className="block"><span className="label-caps">Shoe size</span><input className="input mt-2" value={prefs.sizing_profile.shoe_size ?? ""} onChange={(e) => setSizing("shoe_size", e.target.value)} placeholder="e.g. UK 9" /></label>
            <label className="block"><span className="label-caps">Clothing size</span><input className="input mt-2" value={prefs.sizing_profile.top_size ?? ""} onChange={(e) => setSizing("top_size", e.target.value)} placeholder="e.g. M" /></label>
          </div>
        </section>
      )}

      {tab === "smart" && (
        <section className="card mt-6 p-6">
          <h2 className="text-lg font-bold text-ink">Smart agent &amp; automation</h2>
          <div className="mt-3 divide-y divide-slate-100">
            <Toggle label="Auto-buy target price rules" description="Flag items on your watchlist as ready-to-buy the moment they hit your target price." checked={prefs.auto_buy_enabled} onChange={(value) => set("auto_buy_enabled", value)} />
            <Toggle label="Include refurbished / open-box" description="Show certified refurbished, open-box, and used listings in price intelligence." checked={prefs.include_refurbished} onChange={(value) => set("include_refurbished", value)} />
            <Toggle label="Restock alerts" description="Alert me as soon as a tracked item is back in stock, regardless of price." checked={prefs.restock_alerts_enabled} onChange={(value) => set("restock_alerts_enabled", value)} />
          </div>
        </section>
      )}

      {tab === "integrations" && (
        <section className="card mt-6 p-6">
          <h2 className="text-lg font-bold text-ink">Connected accounts</h2>
          <p className="mt-1 text-sm text-slate-500">Not connected yet - these need an external provider (OAuth, browser extension, email access) this app doesn&apos;t have configured.</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {INTEGRATIONS.map((integration) => (
              <div key={integration.label} className="rounded-xl border border-dashed border-slate-300 p-4 text-center">
                <Icon name={integration.icon} className="mx-auto h-6 w-6 text-slate-400" />
                <p className="mt-2 text-sm font-semibold text-ink">{integration.label}</p>
                <p className="mt-2 pill inline-flex bg-slate-100 text-slate-500">Not connected</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="mt-6 flex items-center gap-3">
        <button onClick={save} disabled={!loaded || saving} className="btn-primary">{saving ? "Saving…" : saved ? "Saved preferences" : "Save changes"}</button>
        {saveError && <p className="text-sm text-rose-600">{saveError}</p>}
      </div>
    </div>
  );
}
