"use client";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Icon } from "@/components/icons";
import { IconInput, PasswordInput } from "@/components/password-input";
import { supabase } from "@/shared/supabase/client";

/** Sign-in calls Supabase Auth directly; the resulting session (and its bearer access token) is what
 * unlocks every signed-in feature (wishlist, chat history, personalized recommendations). Card shape is a
 * fixed (not viewport-scaled) large border-radius rather than a literal geometric circle - a true circle
 * forces width to match height, which breaks down as soon as content height changes across breakpoints;
 * a big fixed radius keeps the same soft, heavily-rounded read at every viewport width. */
export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
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
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface p-4 py-16">
      <Link href="/" className="fixed left-4 top-4 inline-flex items-center gap-2 rounded-full py-1.5 pl-1.5 pr-4 text-sm font-semibold text-slate-500 transition-colors hover:text-brand-700 sm:left-6 sm:top-6">
        <span className="shadow-neu-sm grid h-7 w-7 place-items-center rounded-full">
          <Icon name="arrow" className="h-4 w-4 rotate-180" />
        </span>
        Back
      </Link>

      <section className="surface-elevated w-full max-w-[380px] rounded-[2.75rem] px-7 py-10 text-center sm:px-10 sm:py-12">
        <Link href="/" className="mx-auto mb-6 flex items-center justify-center">
          <Image src="/logo-icon.png" alt="Shopping AI" width={48} height={48} className="h-12 w-12" priority />
        </Link>
        <h1 className="text-2xl font-bold text-ink">Login</h1>
        <p className="mt-1 text-sm text-slate-500">Sign in to your account</p>

        <form onSubmit={submit} className="mt-8 space-y-4 text-left">
          <IconInput icon="mail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" required />
          <PasswordInput value={password} onChange={setPassword} placeholder="Password" required />

          <div className="flex items-center justify-between gap-3 pt-1 text-xs">
            <label className="flex cursor-pointer items-center gap-2 text-slate-500">
              <button
                type="button"
                role="checkbox"
                aria-checked={remember}
                aria-label="Remember me"
                onClick={() => setRemember((v) => !v)}
                className={`grid h-4 w-4 shrink-0 place-items-center rounded-md transition-colors duration-200 ${remember ? "bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-neu-brand" : "text-transparent shadow-neu-inset-sm"}`}
              >
                <Icon name="check" className="h-3 w-3" />
              </button>
              Remember me
            </label>
            <Link href="/auth/forgot-password" className="font-semibold text-brand-600 hover:underline">Forgot password?</Link>
          </div>

          {error && <p className="text-center text-sm text-rose-600">{error}</p>}

          <button className="btn-primary mt-2 w-full rounded-full text-xs uppercase tracking-widest" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="mt-8 text-sm text-slate-500">Don&apos;t have an account? <Link href="/auth/sign-up" className="font-bold text-brand-700 hover:underline">Sign up</Link></p>
      </section>
    </main>
  );
}
