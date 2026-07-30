/** Liveness endpoint suitable for platform checks; it intentionally exposes no secrets or provider status. */
export function GET() { return Response.json({ status: "ok", timestamp: new Date().toISOString() }); }
