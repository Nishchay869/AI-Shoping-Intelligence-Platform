import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies to the behavioral, embeddings-only recommendation engine - built from the shopper's own tracked activity. */
export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/recommendations/personalized`, { headers: authorization ? { Authorization: authorization } : undefined, cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
