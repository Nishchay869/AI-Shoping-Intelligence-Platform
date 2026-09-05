"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { Icon } from "@/components/icons";
import { IconInput } from "@/components/password-input";
import { supabase } from "@/shared/supabase/client";

/** Real Supabase password-reset request (resetPasswordForEmail), not a decorative link - the sign-in
 * page's "Forgot password?" points here, and the email it sends links to /auth/reset-password. */
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`
      });
      if (resetError) throw new Error(resetError.message);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface p-4 py-16">
      <Link href="/auth/sign-in" className="fixed left-4 top-4 inline-flex items-center gap-2 rounded-full py-1.5 pl-1.5 pr-4 text-sm font-semibold text-slate-500 transition-colors hover:text-brand-700 sm:left-6 sm:top-6">
        <span className="shadow-neu-sm grid h-7 w-7 place-items-center rounded-full">
          <Icon name="arrow" className="h-4 w-4 rotate-180" />
        </span>
        Back
      </Link>

      <section className="surface-elevated w-full max-w-[380px] rounded-[2.75rem] px-7 py-10 text-center sm:px-10 sm:py-12">
        <span className="mx-auto mb-6 grid h-14 w-14 place-items-center rounded-full bg-brand-50 text-brand-600 shadow-neu-sm">
          <Icon name="lock" className="h-6 w-6" />
        </span>
        <h1 className="text-2xl font-bold text-ink">Forgot password?</h1>
        <p className="mt-1 text-sm text-slate-500">We&apos;ll email you a link to reset it.</p>

        {sent ? (
          <p className="mt-8 rounded-2xl bg-brand-50 p-4 text-sm leading-relaxed text-brand-700">
            Check <span className="font-semibold">{email}</span> for a password reset link.
          </p>
        ) : (
          <form onSubmit={submit} className="mt-8 space-y-4 text-left">
            <IconInput icon="mail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" required />
            {error && <p className="text-center text-sm text-rose-600">{error}</p>}
            <button className="btn-primary w-full rounded-full text-xs uppercase tracking-widest" disabled={loading}>
              {loading ? "Sending…" : "Send reset link"}
            </button>
          </form>
        )}

        <p className="mt-8 text-sm text-slate-500">Remembered it? <Link href="/auth/sign-in" className="font-bold text-brand-700 hover:underline">Back to login</Link></p>
      </section>
    </main>
  );
}
