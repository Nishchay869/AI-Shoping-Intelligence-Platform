import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({
  message: z.string().min(1).max(2000),
  threadId: z.string().optional()
});

/** Proxies to the FastAPI LangGraph shopping assistant (tool-calling agent: compare/explain/suggest/recommend, with per-thread memory). */
export async function POST(request: Request) {
  try {
    const input = inputSchema.parse(await request.json());
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify({ message: input.message, thread_id: input.threadId })
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
