import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies to the FastAPI single-product lookup used by the product detail page. */
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/products/${id}`, { cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
