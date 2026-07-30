import { type RetailerAdapter, type Retailer, type RetailerListing } from "../domain/retailer-adapter";

/** Placeholder adapter deliberately fails closed until an approved retailer API/feed client is configured. */
export class ConfiguredRetailerAdapter implements RetailerAdapter {
  constructor(readonly retailer: Retailer, private readonly hostnames: readonly string[]) {}
  supports(url: URL): boolean { return this.hostnames.some((host) => url.hostname === host || url.hostname.endsWith(`.${host}`)); }
  async resolve(_input: { url?: string; externalId?: string }): Promise<RetailerListing> {
    throw new Error(`${this.retailer} integration is not configured with an approved data source`);
  }
}

export const retailerAdapters: RetailerAdapter[] = [
  new ConfiguredRetailerAdapter("amazon", ["amazon.com", "amazon.in"]),
  new ConfiguredRetailerAdapter("flipkart", ["flipkart.com"]),
  new ConfiguredRetailerAdapter("myntra", ["myntra.com"])
];
