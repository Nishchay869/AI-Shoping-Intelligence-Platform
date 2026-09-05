"use client";
import { InputHTMLAttributes, useState } from "react";
import { Icon, type IconName } from "./icons";

/** Icon-prefixed text input shared by the sign-in/sign-up/forgot-password forms. The icon is purely
 * decorative (matches the reference design) so it's aria-hidden and sits behind the input via pointer-events-none. */
export function IconInput({ icon, className = "", ...props }: { icon: IconName } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="relative">
      <Icon name={icon} className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      <input {...props} className={`input pl-11 ${className}`} />
    </div>
  );
}

/** Password field with a leading lock icon and a trailing show/hide toggle, shared by sign-in, sign-up
 * and reset-password. */
export function PasswordInput({
  value,
  onChange,
  placeholder,
  minLength,
  required
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minLength?: number;
  required?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <Icon name="lock" className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      <input
        type={visible ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input pl-11 pr-11"
        placeholder={placeholder}
        minLength={minLength}
        required={required}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-600"
      >
        <Icon name={visible ? "eye-off" : "eye"} className="h-4 w-4" />
      </button>
    </div>
  );
}
