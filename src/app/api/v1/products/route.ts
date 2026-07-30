import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies catalog search/listing to the FastAPI product search system. */
export async function GET(request: Request) {
  try {
    const { search } = new URL(request.url);
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/products${search}`, { cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
