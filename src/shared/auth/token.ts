import { supabase } from "@/shared/supabase/client";

/** Every real-backend fetch call attaches this via authHeaders(). Backed by Supabase's own session
 * storage (not a manual localStorage token) - signInWithPassword/signUp manage persistence themselves. */
export async function getToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession(); // local/cached read, no network round trip
  return data.session?.access_token ?? null;
}

export async function clearToken(): Promise<void> {
  await supabase.auth.signOut();
}

export async function authHeaders(): Promise<HeadersInit> {
  const token = await getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
