import { z } from "zod";
import { resolveListing } from "@/modules/catalog/application/resolve-listing";
import { retailerAdapters } from "@/modules/catalog/infrastructure/configured-adapter";
import { apiError, requireIdempotencyKey } from "@/shared/presentation/api";

const inputSchema = z.object({ url: z.string().url().max(2048) });

/** Resolves a supported user-submitted URL through an approved retailer adapter. */
export async function POST(request: Request) {
  try {
    if (!requireIdempotencyKey(request)) return Response.json({ error: "IDEMPOTENCY_KEY_REQUIRED" }, { status: 400 });
    const input = inputSchema.parse(await request.json());
    const listing = await resolveListing(input.url, retailerAdapters);
    return Response.json({ data: listing }, { status: 201 });
  } catch (error) { return apiError(error); }
}
