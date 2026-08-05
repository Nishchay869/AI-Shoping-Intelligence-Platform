"use client";
import type { User } from "@supabase/supabase-js";
import { useEffect, useState } from "react";
import { supabase } from "@/shared/supabase/client";

/** Signed-in user for the current browser session, kept in sync with sign-in/sign-out. `null` means
 * "no session yet" - which covers both "still loading" and "signed out", since every consumer of this
 * hook lives behind AppShell's own session gate and only renders once a session is confirmed to exist. */
export function useCurrentUser(): User | null {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setUser(data.session?.user ?? null));
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => setUser(session?.user ?? null));
    return () => subscription.subscription.unsubscribe();
  }, []);

  return user;
}

/** display_name is set at sign-up (see auth/sign-up/page.tsx) and stored as Supabase user_metadata -
 * there's no separate profiles table wired up yet, so this is the single source of truth for a user's
 * name. Falls back to the email's local part for accounts that predate the sign-up form asking for it. */
export function displayNameFor(user: User | null): string {
  if (!user) return "";
  const metaName = user.user_metadata?.display_name;
  if (typeof metaName === "string" && metaName.trim()) return metaName.trim();
  return user.email?.split("@")[0] ?? "";
}

/** Two-letter avatar initials from a display name ("Test User" -> "TU", "nishchay" -> "NI"). */
export function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}
