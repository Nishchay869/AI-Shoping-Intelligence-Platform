"use client";
import { useState } from "react";
import { Icon } from "./icons";

/** Password field with a show/hide toggle, shared by sign-in and sign-up. */
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
    <div className="relative mt-2">
      <input
        type={visible ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input pr-10"
        placeholder={placeholder}
        minLength={minLength}
        required={required}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-600"
      >
        <Icon name={visible ? "eye-off" : "eye"} className="h-4 w-4" />
      </button>
    </div>
  );
}
