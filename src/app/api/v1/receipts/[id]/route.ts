import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies one previously scanned receipt, owned by the current user, to the FastAPI backend. */
export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/receipts/${id}`, { headers: authorization ? { Authorization: authorization } : undefined, cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}

/** Proxies deleting one owned receipt from history. A successful delete is 204 (no body). */
export async function DELETE(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/receipts/${id}`, { method: "DELETE", headers: authorization ? { Authorization: authorization } : undefined });
    if (backendResponse.status === 204) return new Response(null, { status: 204 });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
