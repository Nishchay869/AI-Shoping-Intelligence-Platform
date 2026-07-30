import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({
  budget: z.number().nonnegative().optional(),
  purpose: z.string().min(3).max(300),
  brandPreference: z.string().max(120).optional(),
  features: z.array(z.string().max(80)).max(10).default([]),
  currency: z.string().length(3).default("INR")
});

/** Proxies shopper intent to the FastAPI AI recommendation engine (LLM query understanding + embeddings + pgvector search + LLM ranking). */
export async function POST(request: Request) {
  try {
    const input = inputSchema.parse(await request.json());
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify({ budget: input.budget, purpose: input.purpose, brand_preference: input.brandPreference, features: input.features, currency: input.currency })
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
