import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies the shopper's scanned-receipt history to the FastAPI backend. */
export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/receipts`, { headers: authorization ? { Authorization: authorization } : undefined, cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
