import { NextResponse } from "next/server";
import { ZodError } from "zod";

/** Converts expected application failures into one consistent, non-sensitive response shape. */
export function apiError(error: unknown) {
  if (error instanceof ZodError) return NextResponse.json({ error: "VALIDATION_ERROR", details: error.flatten() }, { status: 400 });
  if (error instanceof Error && error.name === "UnsupportedRetailerError") return NextResponse.json({ error: "UNSUPPORTED_RETAILER", message: error.message }, { status: 422 });
  console.error(JSON.stringify({ level: "error", message: error instanceof Error ? error.message : "Unknown API error" }));
  return NextResponse.json({ error: "INTERNAL_ERROR" }, { status: 500 });
}

/** Requires an idempotency key so clients can safely retry external or queue-backed mutations. */
export function requireIdempotencyKey(request: Request): string | null {
  const key = request.headers.get("idempotency-key");
  return key && /^[A-Za-z0-9_-]{16,128}$/.test(key) ? key : null;
}
