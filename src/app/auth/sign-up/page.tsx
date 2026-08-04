"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Icon } from "@/components/icons";
import { supabase } from "@/shared/supabase/client";

/** Registration calls Supabase Auth directly. With "Confirm email" disabled in the Supabase project's
 * Auth settings, signUp returns a session immediately, so we sign that session back out and send the
 * shopper to the landing page to sign in deliberately instead of auto-logging them into the dashboard. */
export default function SignUpPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { display_name: displayName } },
      });
      if (signUpError) throw new Error(signUpError.message);
      await supabase.auth.signOut();
      router.push("/?registered=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface p-4">
      <Link href="/" className="fixed left-4 top-4 inline-flex items-center gap-2 rounded-full py-1.5 pl-1.5 pr-4 text-sm font-semibold text-slate-500 transition-colors hover:text-brand-700 sm:left-6 sm:top-6">
        <span className="shadow-neu-sm grid h-7 w-7 place-items-center rounded-full">
          <Icon name="arrow" className="h-4 w-4 rotate-180" />
        </span>
        Back
      </Link>

      <Link href="/" className="mb-8 flex flex-col items-center gap-1">
        <span className="flex items-center gap-2 text-xl font-bold text-brand-700">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-neu-brand">P</span>Pricewise
        </span>
        <span className="label-caps text-brand-600/70">AI Intelligence</span>
      </Link>

      <section className="surface-elevated w-full max-w-[420px] rounded-3xl p-8">
        <h1 className="text-2xl font-bold text-ink">Create your account</h1>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            <span className="label-caps">Full name</span>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="input mt-2" placeholder="Ada Lovelace" required />
          </label>
          <label className="block">
            <span className="label-caps">Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input mt-2" placeholder="you@example.com" required />
          </label>
          <label className="block">
            <span className="label-caps">Password</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input mt-2" placeholder="At least 12 characters" minLength={12} required />
          </label>
          {error && <p className="text-sm text-rose-600">{error}</p>}
          <button className="btn-primary w-full" disabled={loading}>{loading ? "Creating account…" : "Create account"}</button>
          <p className="text-center text-xs leading-relaxed text-slate-500">Save your searches, get price alerts, and pick up recommendations where you left off.</p>
        </form>
      </section>

      <p className="mt-8 text-sm text-slate-500">Already have an account? <Link href="/auth/sign-in" className="font-bold text-brand-700 hover:underline">Sign in</Link></p>
    </main>
  );
}
