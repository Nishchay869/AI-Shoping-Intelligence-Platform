"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { supabase } from "@/shared/supabase/client";

/** Sign-in calls Supabase Auth directly; the resulting session (and its bearer access token) is what
 * unlocks every signed-in feature (wishlist, chat history, personalized recommendations). */
export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
      if (signInError) throw new Error(signInError.message);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center p-4">
      <section className="card w-full max-w-md p-7">
        <Link href="/" className="flex items-center gap-2 text-xl font-bold"><span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">P</span>Pricewise</Link>
        <h1 className="mt-8 text-2xl font-bold">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-500">Sign in to see your saved products and alerts.</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block text-sm font-semibold">Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input mt-2" placeholder="you@example.com" required /></label>
          <label className="block text-sm font-semibold">Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input mt-2" placeholder="••••••••" required /></label>
          {error && <p className="text-sm text-rose-600">{error}</p>}
          <button className="btn-primary w-full" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-500">New to Pricewise? <Link href="/auth/sign-up" className="font-bold text-brand-600">Create an account</Link></p>
      </section>
    </main>
  );
}
