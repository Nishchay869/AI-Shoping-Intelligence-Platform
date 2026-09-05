import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

// OCR plus LLM structured extraction can run past Vercel's default 10s function timeout on a large or
// noisy image - see recommendations/route.ts for the failure mode.
export const maxDuration = 60;

/** Proxies an uploaded receipt photo to the FastAPI receipt scanner (Tesseract OCR + LLM structured extraction). */
export async function POST(request: Request) {
  try {
    const incoming = await request.formData();
    const image = incoming.get("image");
    if (!(image instanceof Blob)) return Response.json({ error: "IMAGE_REQUIRED" }, { status: 400 });

    const outgoing = new FormData();
    outgoing.append("image", image, "receipt.jpg");

    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/receipts/scan`, {
      method: "POST",
      headers: authorization ? { Authorization: authorization } : undefined,
      body: outgoing,
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
