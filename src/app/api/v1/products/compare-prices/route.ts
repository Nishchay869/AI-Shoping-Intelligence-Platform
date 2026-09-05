import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

// Live web search + LLM extraction can run past Vercel's default 10s function timeout - see
// recommendations/route.ts for the failure mode.
export const maxDuration = 60;

const inputSchema = z.object({ productName: z.string().min(2).max(200) });

/** Proxies to the FastAPI live price-comparison endpoint (Tavily web search + Gemini extraction). */
export async function POST(request: Request) {
  try {
    const input = inputSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/products/compare-prices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_name: input.productName })
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
