import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies the shopper's private wishlists to the FastAPI backend. */
export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/wishlists`, { headers: authorization ? { Authorization: authorization } : undefined, cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}

const createSchema = z.object({ name: z.string().min(1).max(80).optional() });

export async function POST(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const input = createSchema.parse(await request.json().catch(() => ({})));
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/wishlists`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify(input),
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
