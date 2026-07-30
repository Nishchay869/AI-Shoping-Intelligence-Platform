import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({ query: z.string().min(1).max(300) });

/** Records a shopper's search query - one of the four personalization signals (search/wishlist/purchase/click). */
export async function POST(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const input = inputSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/activity/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify(input),
    });
    if (backendResponse.status === 204) return new Response(null, { status: 204 });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
