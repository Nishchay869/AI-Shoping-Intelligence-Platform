import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { env } from "@/shared/config/env";

/** Nonce-based Content-Security-Policy - the primary XSS defense-in-depth layer beyond React's own escaping.
 * A fresh nonce is generated per request (so it can't be reused/predicted).
 *
 * Deliberately NOT using 'strict-dynamic' here, even though it's the gold-standard pairing with a nonce:
 * almost every page in this app is statically prerendered at build time (Next's "○ Static" output), so its
 * <script> tags are baked in before any per-request nonce exists and can never carry one. 'strict-dynamic'
 * revokes the 'self' fallback entirely, which would leave those scripts with no valid source expression and
 * break the app - verified by actually serving the built static homepage and finding zero nonce attributes
 * on its script tags. Keeping 'self' means those scripts still load (same-origin allowlisting), while the
 * nonce still covers anything rendered by a dynamic route. Forcing every page into dynamic rendering just to
 * unlock 'strict-dynamic' would trade away static generation for a marginal gain and is out of scope here. */
export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  // Next.js's dev-mode webpack build wraps every module in eval(...) for Fast Refresh - blocking eval
  // outright in development doesn't harden anything real (this bundle never ships), it just breaks the
  // dev server's own JS from running at all. Production builds don't use eval and never get this token.
  const devEval = process.env.NODE_ENV === "development" ? " 'unsafe-eval'" : "";

  const csp = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}'${devEval};
    style-src 'self' 'unsafe-inline';
    img-src 'self' https: data: blob:;
    font-src 'self';
    connect-src 'self' ${env.NEXT_PUBLIC_SUPABASE_URL};
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
  `.replace(/\s{2,}/g, " ").trim();

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    // Run on every page/document request; skip static assets and image optimization files, which don't
    // need a per-request nonce and would just waste a middleware invocation.
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
