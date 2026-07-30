import { type RetailerAdapter, type RetailerListing } from "../domain/retailer-adapter";

export class UnsupportedRetailerError extends Error {}

/** Finds the responsible adapter and delegates only after URL parsing has succeeded. */
export async function resolveListing(url: string, adapters: readonly RetailerAdapter[]): Promise<RetailerListing> {
  let parsed: URL;
  try { parsed = new URL(url); } catch { throw new UnsupportedRetailerError("A valid HTTPS retailer URL is required"); }
  if (parsed.protocol !== "https:") throw new UnsupportedRetailerError("Only HTTPS URLs are supported");
  const adapter = adapters.find((candidate) => candidate.supports(parsed));
  if (!adapter) throw new UnsupportedRetailerError("This retailer is not enabled");
  return adapter.resolve({ url: parsed.toString() });
}
