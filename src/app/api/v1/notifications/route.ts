import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies to the FastAPI notifications feed - real price-drop alerts already sent to this user over WhatsApp. */
export async function GET(request: Request) {
  try {
    const { search } = new URL(request.url);
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/notifications${search}`, { headers: authorization ? { Authorization: authorization } : undefined, cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
