"use client";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Icon } from "@/components/icons";
import { PasswordInput } from "@/components/password-input";
import { supabase } from "@/shared/supabase/client";

/** Landing page for the link in the reset-password email. supabase-js parses the recovery token out of
 * the URL hash on load (detectSessionInUrl defaults to true) and fires a PASSWORD_RECOVERY auth event -
 * only once that's happened do we know updateUser({ password }) has a session to attach the change to. */
export default function ResetPasswordPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const { data: listener } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") setReady(true);
    });
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) setReady(true);
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { error: updateError } = await supabase.auth.updateUser({ password });
      if (updateError) throw new Error(updateError.message);
      setDone(true);
      await supabase.auth.signOut();
      setTimeout(() => router.push("/auth/sign-in"), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface p-4 py-16">
      <section className="surface-elevated w-full max-w-[380px] rounded-[2.75rem] px-7 py-10 text-center sm:px-10 sm:py-12">
        <span className="mx-auto mb-6 grid h-14 w-14 place-items-center rounded-full bg-brand-50 text-brand-600 shadow-neu-sm">
          <Icon name="lock" className="h-6 w-6" />
        </span>
        <h1 className="text-2xl font-bold text-ink">Set a new password</h1>
        <p className="mt-1 text-sm text-slate-500">Choose something you haven&apos;t used before.</p>

        {!ready && !done && <p className="mt-8 text-sm text-slate-400">Verifying your reset link…</p>}

        {ready && !done && (
          <form onSubmit={submit} className="mt-8 space-y-4 text-left">
            <PasswordInput value={password} onChange={setPassword} placeholder="New password" minLength={12} required />
            <PasswordInput value={confirmPassword} onChange={setConfirmPassword} placeholder="Confirm new password" minLength={12} required />
            {error && <p className="text-center text-sm text-rose-600">{error}</p>}
            <button className="btn-primary w-full rounded-full text-xs uppercase tracking-widest" disabled={loading}>
              {loading ? "Updating…" : "Update password"}
            </button>
          </form>
        )}

        {done && <p className="mt-8 rounded-2xl bg-brand-50 p-4 text-sm text-brand-700">Password updated. Redirecting you to sign in…</p>}
      </section>
    </main>
  );
}
