import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({ email: z.string().email(), password: z.string().min(12).max(128), displayName: z.string().min(1).max(80) });

/** Proxies real registration to the FastAPI JWT auth backend. */
export async function POST(request: Request) {
  try {
    const input = inputSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: input.email, password: input.password, display_name: input.displayName }),
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
