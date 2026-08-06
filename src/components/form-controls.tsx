"use client";
import { useState } from "react";
import { Icon, type IconName } from "./icons";

/** Generic form primitives for settings-style pages (tabs, switches, tag lists, sliders, segmented
 * pickers) - nothing like this existed yet; src/components/ui.tsx only holds the product-domain
 * ProductCard. Styled from the same neumorphic tokens as globals.css's .card/.input/.pill. */

export function Tabs<T extends string>({ tabs, active, onChange }: { tabs: { id: T; label: string; icon?: IconName }[]; active: T; onChange: (id: T) => void }) {
  return (
    <div role="tablist" className="flex flex-wrap gap-1.5 rounded-2xl bg-surface p-1.5 shadow-neu-inset-sm">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 ${
            active === tab.id ? "bg-surface text-brand-700 shadow-neu-sm" : "text-slate-500 hover:text-slate-800"
          }`}
        >
          {tab.icon && <Icon name={tab.icon} className="h-4 w-4" />}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export function Toggle({ checked, onChange, label, description }: { checked: boolean; onChange: (value: boolean) => void; label: string; description?: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <span>
        <span className="block text-sm font-semibold text-ink">{label}</span>
        {description && <span className="mt-0.5 block text-xs text-slate-500">{description}</span>}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative h-7 w-12 shrink-0 rounded-full transition-colors duration-200 ${checked ? "bg-gradient-to-br from-brand-500 to-brand-600 shadow-neu-brand" : "bg-surface shadow-neu-inset-sm"}`}
      >
        <span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-neu-sm transition-transform duration-200 ${checked ? "translate-x-6" : "translate-x-1"}`} />
      </button>
    </div>
  );
}

export function TagInput({ values, onChange, placeholder }: { values: string[]; onChange: (values: string[]) => void; placeholder?: string }) {
  const [draft, setDraft] = useState("");

  function commit() {
    const tag = draft.trim();
    if (tag && !values.includes(tag)) onChange([...values, tag]);
    setDraft("");
  }

  return (
    <div className="input flex h-auto min-h-11 flex-wrap items-center gap-1.5 py-1.5">
      {values.map((tag) => (
        <span key={tag} className="pill flex items-center gap-1 bg-brand-50 text-brand-700">
          {tag}
          <button type="button" onClick={() => onChange(values.filter((value) => value !== tag))} aria-label={`Remove ${tag}`} className="hover:text-brand-900">
            <Icon name="x" className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") { e.preventDefault(); commit(); }
          else if (e.key === "Backspace" && !draft && values.length > 0) onChange(values.slice(0, -1));
        }}
        onBlur={commit}
        placeholder={values.length === 0 ? placeholder : undefined}
        className="min-w-24 flex-1 border-0 bg-transparent p-1 text-sm outline-none placeholder:text-slate-400"
      />
    </div>
  );
}

export function Slider({ value, onChange, min = 0, max = 100, step = 5, label, formatValue }: { value: number; onChange: (value: number) => void; min?: number; max?: number; step?: number; label: string; formatValue?: (value: number) => string }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">{label}</span>
        <span className="data pill bg-brand-50 text-brand-700">{formatValue ? formatValue(value) : value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-3 h-2 w-full cursor-pointer appearance-none rounded-full bg-surface shadow-neu-inset-sm accent-brand-600"
      />
    </div>
  );
}

export function Segmented<T extends string>({ options, value, onChange }: { options: { value: T; label: string }[]; value: T; onChange: (value: T) => void }) {
  return (
    <div className="inline-flex flex-wrap gap-1.5 rounded-xl bg-surface p-1.5 shadow-neu-inset-sm">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-200 ${value === option.value ? "bg-surface text-brand-700 shadow-neu-sm" : "text-slate-500 hover:text-slate-800"}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
