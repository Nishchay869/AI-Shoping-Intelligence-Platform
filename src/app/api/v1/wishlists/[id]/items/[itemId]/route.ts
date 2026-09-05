import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies removing one item from a shopper's wishlist. */
export async function DELETE(request: Request, { params }: { params: Promise<{ id: string; itemId: string }> }) {
  try {
    const { id, itemId } = await params;
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/wishlists/${id}/items/${itemId}`, {
      method: "DELETE",
      headers: authorization ? { Authorization: authorization } : undefined,
    });
    if (backendResponse.status === 204) return new Response(null, { status: 204 });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
