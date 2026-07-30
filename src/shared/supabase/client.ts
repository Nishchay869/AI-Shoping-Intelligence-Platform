import { createClient } from "@supabase/supabase-js";
import { env } from "@/shared/config/env";

/** Singleton browser client. Plain @supabase/supabase-js, not @supabase/ssr's cookie-based client - this
 * app has no server-rendered auth state anywhere; every consumer is a client component that reads the
 * current session's access token and forwards it as a bearer header to a same-origin proxy route. */
export const supabase = createClient(env.NEXT_PUBLIC_SUPABASE_URL, env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
