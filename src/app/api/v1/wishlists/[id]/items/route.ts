import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({ productId: z.string().uuid(), targetPriceMinor: z.number().int().nonnegative().optional() });

/** Proxies adding a catalog product to one of the shopper's wishlists. */
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const authorization = request.headers.get("authorization");
    const input = inputSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/wishlists/${id}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify({ product_id: input.productId, target_price_minor: input.targetPriceMinor }),
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
