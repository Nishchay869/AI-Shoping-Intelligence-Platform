import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/v1/activity/search/route";

describe("POST /api/v1/activity/search route handler", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("forwards a valid query and the Authorization header to the backend, and passes through a 204", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    const request = new Request("http://localhost/api/v1/activity/search", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer test-token" },
      body: JSON.stringify({ query: "wireless headphones" }),
    });

    const response = await POST(request);
    expect(response.status).toBe(204);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/activity/search");
    expect(init.headers.Authorization).toBe("Bearer test-token");
    expect(JSON.parse(init.body)).toEqual({ query: "wireless headphones" });
  });

  it("does not forward any Authorization header when the request has none", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    const request = new Request("http://localhost/api/v1/activity/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "wireless headphones" }),
    });
    await POST(request);

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });

  it("rejects an empty query before ever calling the backend", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const request = new Request("http://localhost/api/v1/activity/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "" }),
    });
    const response = await POST(request);

    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects an oversized query before ever calling the backend", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const request = new Request("http://localhost/api/v1/activity/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "a".repeat(1000) }),
    });
    const response = await POST(request);

    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("propagates a non-204 backend response body and status", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Too many requests" }), { status: 429 }));
    vi.stubGlobal("fetch", fetchMock);

    const request = new Request("http://localhost/api/v1/activity/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "wireless headphones" }),
    });
    const response = await POST(request);

    expect(response.status).toBe(429);
    expect(await response.json()).toEqual({ detail: "Too many requests" });
  });
});
