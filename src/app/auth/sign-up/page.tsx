"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
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
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-4">
      <Link href="/" className="mb-8 flex flex-col items-center gap-1">
        <span className="flex items-center gap-2 text-xl font-bold text-brand-700">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-700 text-white">P</span>Pricewise
        </span>
        <span className="label-caps text-brand-600/70">AI Intelligence</span>
      </Link>

      <section className="card w-full max-w-[420px] p-8">
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
