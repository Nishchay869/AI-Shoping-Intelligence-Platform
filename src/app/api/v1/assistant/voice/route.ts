import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies a recorded voice message to the FastAPI voice pipeline (Whisper speech-to-text -> the LangGraph assistant -> OpenAI text-to-speech). */
export async function POST(request: Request) {
  try {
    const incoming = await request.formData();
    const audio = incoming.get("audio");
    if (!(audio instanceof Blob)) return Response.json({ error: "AUDIO_REQUIRED" }, { status: 400 });
    const threadId = incoming.get("threadId");

    const outgoing = new FormData();
    outgoing.append("audio", audio, "recording.webm");
    if (typeof threadId === "string" && threadId) outgoing.append("thread_id", threadId);

    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/assistant/voice`, {
      method: "POST",
      headers: { ...(authorization ? { Authorization: authorization } : {}) },
      body: outgoing
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
