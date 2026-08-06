import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

const inputSchema = z.object({ phone_number: z.string().min(6).max(20) });

/** Proxies a request to send (generate) a phone verification code. No SMS provider is configured in this
 * app yet - see backend/app/services/preferences.py for the dev-mode code delivery caveat. */
export async function POST(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const input = inputSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/preferences/phone/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify(input),
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
