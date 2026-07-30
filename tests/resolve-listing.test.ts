import { describe, expect, it } from "vitest";
import { resolveListing, UnsupportedRetailerError } from "@/modules/catalog/application/resolve-listing";

describe("resolveListing", () => {
  it("rejects arbitrary websites before an adapter can make an outbound request", async () => {
    await expect(resolveListing("https://evil.example/item", [])).rejects.toBeInstanceOf(UnsupportedRetailerError);
  });
  it("rejects non-HTTPS input", async () => {
    await expect(resolveListing("http://amazon.in/item", [])).rejects.toBeInstanceOf(UnsupportedRetailerError);
  });
});
