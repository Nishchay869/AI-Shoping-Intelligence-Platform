import { z } from "zod";

export const supportedRetailers = ["amazon", "flipkart", "myntra"] as const;
export type Retailer = (typeof supportedRetailers)[number];

/** Canonical, provider-neutral data returned by permitted retailer integrations. */
export const retailerListingSchema = z.object({
  retailer: z.enum(supportedRetailers), externalId: z.string().min(1), url: z.string().url(),
  title: z.string().min(1), brand: z.string().optional(), modelNumber: z.string().optional(),
  gtin: z.string().optional(), currency: z.string().length(3), priceMinor: z.number().int().nonnegative(),
  available: z.boolean(), imageUrl: z.string().url().optional(), checkedAt: z.coerce.date()
});
export type RetailerListing = z.infer<typeof retailerListingSchema>;

/** Port implemented only by approved retailer APIs or affiliate feeds. No HTML scraping belongs here. */
export interface RetailerAdapter {
  readonly retailer: Retailer;
  supports(url: URL): boolean;
  resolve(input: { url?: string; externalId?: string }): Promise<RetailerListing>;
}
