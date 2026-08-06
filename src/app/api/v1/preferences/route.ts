import { z } from "zod";
import { env } from "@/shared/config/env";
import { apiError } from "@/shared/presentation/api";

/** Proxies the shopper's alert/AI-persona/smart-rule preferences to the FastAPI backend.
 *
 * Field names stay snake_case end-to-end (unlike the small ad-hoc wishlist calls, which convert
 * camelCase to snake_case) - this is a config-object round trip (fetch it, edit it, PATCH the same
 * shape back), so there's no local camelCase state to convert from. */
export async function GET(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/preferences`, { headers: authorization ? { Authorization: authorization } : undefined, cache: "no-store" });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}

const updateSchema = z.object({
  notify_email: z.boolean().optional(),
  notify_push: z.boolean().optional(),
  notify_sms: z.boolean().optional(),
  notify_whatsapp: z.boolean().optional(),
  min_discount_percentage: z.number().min(0).max(95).nullable().optional(),
  alert_all_time_low: z.boolean().optional(),
  alert_below_90d_average: z.boolean().optional(),
  notification_frequency: z.enum(["instant", "daily_digest", "weekly_summary"]).optional(),
  favorite_brands: z.array(z.string()).max(50).optional(),
  blacklisted_brands: z.array(z.string()).max(50).optional(),
  preferred_retailers: z.array(z.string()).max(20).optional(),
  budget_tier: z.enum(["budget", "balanced", "premium"]).nullable().optional(),
  sizing_profile: z.record(z.string()).optional(),
  include_refurbished: z.boolean().optional(),
  restock_alerts_enabled: z.boolean().optional(),
  auto_buy_enabled: z.boolean().optional(),
});

export async function PATCH(request: Request) {
  try {
    const authorization = request.headers.get("authorization");
    const input = updateSchema.parse(await request.json());
    const backendResponse = await fetch(`${env.BACKEND_API_URL}/preferences`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...(authorization ? { Authorization: authorization } : {}) },
      body: JSON.stringify(input),
    });
    const data = await backendResponse.json();
    return Response.json(data, { status: backendResponse.status });
  } catch (error) { return apiError(error); }
}
