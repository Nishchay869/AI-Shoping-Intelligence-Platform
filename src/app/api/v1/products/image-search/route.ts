import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

// CLIP model load (first call after a cold start) plus embedding + search can run past Vercel's default
// 10s function timeout - see recommendations/route.ts for the failure mode.
export const maxDuration = 60;

/** Proxies an uploaded product photo to the FastAPI image-based search endpoint (CLIP embedding + pgvector cosine search). */
export async function POST(request: Request) {
  try {
    const incoming = await request.formData();
    const image = incoming.get("image");
    if (!(image instanceof Blob)) return Response.json({ error: "IMAGE_REQUIRED" }, { status: 400 });

    const outgoing = new FormData();
    outgoing.append("image", image, "upload.jpg");

    const backendResponse = await fetch(`${env.BACKEND_API_URL}/products/image-search`, { method: "POST", body: outgoing });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
