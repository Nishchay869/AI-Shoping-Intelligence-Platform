import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({
  message: z.string().min(1).max(2000),
  productId: z.string().uuid().optional(),
  conversationId: z.string().uuid().optional()
});

/** Proxies a shopper's question to the FastAPI RAG pipeline (retriever + prompt template + LLM answer generation). */
export async function POST(request: Request) {
  try {
    const input = inputSchema.parse(await request.json());
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify({ message: input.message, product_id: input.productId, conversation_id: input.conversationId })
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
