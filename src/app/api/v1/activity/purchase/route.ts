import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({ productId: z.string().uuid() });

/** Records a shopper's purchase - the strongest-intent personalization signal. */
export async function POST(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const input = inputSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/activity/purchase`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify({ product_id: input.productId }),
    });
    if (backendResponse.status === 204) return new Response(null, { status: 204 });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
