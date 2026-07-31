"use client";
import { useState } from "react";
/** Profile page manages user-visible preferences and explicit notification consent. */
export default function ProfilePage() {
  const [saved, setSaved] = useState(false);
  return (
    <div className="max-w-3xl">
      <p className="label-caps text-brand-600">Account</p>
      <h1 className="mt-1 text-3xl font-bold text-ink">Profile &amp; preferences</h1>

      <section className="card mt-8 p-6">
        <h2 className="text-lg font-bold text-ink">Personal details</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="block"><span className="label-caps">Name</span><input className="input mt-2" defaultValue="Nischay" /></label>
          <label className="block"><span className="label-caps">Email</span><input className="input mt-2" type="email" defaultValue="nischay@example.com" /></label>
        </div>
      </section>

      <section className="card mt-5 p-6">
        <h2 className="text-lg font-bold text-ink">Alerts</h2>
        <p className="mt-1 text-sm text-slate-500">Choose how you receive price alerts. SMS and WhatsApp require verified opt-in.</p>
        <div className="mt-5 divide-y divide-slate-100">
          {[["Email", true], ["Browser notifications", true], ["SMS", false], ["WhatsApp", false]].map(([label, enabled]) => (
            <label key={String(label)} className="flex items-center justify-between py-3 text-sm font-medium text-ink">
              <span>{label}</span>
              <input className="h-5 w-5 accent-brand-600" type="checkbox" defaultChecked={Boolean(enabled)} />
            </label>
          ))}
        </div>
      </section>

      <button onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 1800); }} className="btn-primary mt-6">{saved ? "Saved preferences" : "Save changes"}</button>
    </div>
  );
}
