"use client";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Icon } from "@/components/icons";
import { PasswordInput } from "@/components/password-input";
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
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface p-4">
      <Link href="/" className="fixed left-4 top-4 inline-flex items-center gap-2 rounded-full py-1.5 pl-1.5 pr-4 text-sm font-semibold text-slate-500 transition-colors hover:text-brand-700 sm:left-6 sm:top-6">
        <span className="shadow-neu-sm grid h-7 w-7 place-items-center rounded-full">
          <Icon name="arrow" className="h-4 w-4 rotate-180" />
        </span>
        Back
      </Link>

      <Link href="/" className="mb-8 flex flex-col items-center gap-1">
        <span className="flex items-center gap-2 text-xl font-bold text-brand-700">
          <Image src="/logo-icon.png" alt="" width={36} height={36} className="h-9 w-9" priority />Shopping AI
        </span>
        <span className="label-caps text-brand-600/70">AI Intelligence</span>
      </Link>

      <section className="surface-elevated w-full max-w-[420px] rounded-3xl p-8">
        <h1 className="text-2xl font-bold text-ink">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-500">Log in to manage your price alerts and intelligence.</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            <span className="label-caps">Email address</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input mt-2" placeholder="you@gmail.com" required />
          </label>
          <label className="block">
            <span className="label-caps">Password</span>
            <PasswordInput value={password} onChange={setPassword} placeholder="Test@123" required />
          </label>
          {error && <p className="text-sm text-rose-600">{error}</p>}
          <button className="btn-primary w-full gap-2" disabled={loading}>
            {loading ? "Signing in…" : <>Sign in <Icon name="arrow" className="h-4 w-4" /></>}
          </button>
        </form>
      </section>

      <p className="mt-8 text-sm text-slate-500">New to Shopping AI? <Link href="/auth/sign-up" className="font-bold text-brand-700 hover:underline">Create an account</Link></p>
    </main>
  );
}
