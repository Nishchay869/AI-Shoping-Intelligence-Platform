import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import { middleware } from "@/middleware";

describe("CSP middleware", () => {
  it("sets a Content-Security-Policy header on every response", () => {
    const response = middleware(new NextRequest("http://localhost/dashboard"));
    expect(response.headers.get("Content-Security-Policy")).toBeTruthy();
  });

  it("generates a fresh, non-empty nonce on every request", () => {
    const first = middleware(new NextRequest("http://localhost/dashboard"));
    const second = middleware(new NextRequest("http://localhost/dashboard"));

    const firstNonce = first.headers.get("Content-Security-Policy")?.match(/nonce-([A-Za-z0-9+/=]+)/)?.[1];
    const secondNonce = second.headers.get("Content-Security-Policy")?.match(/nonce-([A-Za-z0-9+/=]+)/)?.[1];

    expect(firstNonce).toBeTruthy();
    expect(secondNonce).toBeTruthy();
    expect(firstNonce).not.toBe(secondNonce);
  });

  it("does NOT include 'strict-dynamic' - it would break every statically-prerendered page's unnonced script tags", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    expect(csp).not.toContain("strict-dynamic");
  });

  it("keeps 'self' in script-src so same-origin static chunks (no nonce, baked in at build time) still load", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    const scriptSrc = csp.match(/script-src ([^;]+);/)?.[1] ?? "";
    expect(scriptSrc).toContain("'self'");
  });

  it("never allows 'unsafe-inline' for scripts (that would defeat the entire point of the nonce)", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    const scriptSrc = csp.match(/script-src ([^;]+);/)?.[1] ?? "";
    expect(scriptSrc).not.toContain("unsafe-inline");
  });

  it("blocks framing entirely (frame-ancestors 'none') as clickjacking defense-in-depth alongside X-Frame-Options", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    expect(csp).toContain("frame-ancestors 'none'");
  });

  it("disallows any <object>/<embed>/<applet> plugin content", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    expect(csp).toContain("object-src 'none'");
  });

  it("restricts connect-src to same-origin plus the Supabase project - every other fetch in this app goes through a same-origin proxy route, but sign-in/sign-up call Supabase Auth directly from the browser", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    expect(csp).toContain("connect-src 'self' https://placeholder.supabase.co");
  });

  it("allows https/data/blob image sources (external product images and object-URL previews both need this)", () => {
    const csp = middleware(new NextRequest("http://localhost/dashboard")).headers.get("Content-Security-Policy") ?? "";
    const imgSrc = csp.match(/img-src ([^;]+);/)?.[1] ?? "";
    expect(imgSrc).toContain("https:");
    expect(imgSrc).toContain("data:");
    expect(imgSrc).toContain("blob:");
  });
});
