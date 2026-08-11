import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies to the FastAPI list-reviews endpoint (newest-first, paginated) for one product. */
export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const { search } = new URL(request.url);
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/products/${id}/reviews${search}`, { cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
