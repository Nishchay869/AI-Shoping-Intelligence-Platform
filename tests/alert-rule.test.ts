import { describe, expect, it } from "vitest";
import { Money } from "@/shared/domain/money";
import { ruleMatches } from "@/modules/tracking/domain/alert-rule";

describe("ruleMatches", () => {
  const oldOffer = { price: Money.fromMinor(10000, "INR"), available: true };
  it("matches a target price reached", () => expect(ruleMatches({ id: "1", kind: "target_price", targetPrice: Money.fromMinor(9000, "INR"), enabled: true }, oldOffer, { price: Money.fromMinor(9000, "INR"), available: true })).toBe(true));
  it("does not compare prices across currencies", () => expect(() => ruleMatches({ id: "1", kind: "any_drop", enabled: true }, oldOffer, { price: Money.fromMinor(1, "USD"), available: true })).toThrow());
  it("matches a restock only on an availability transition", () => expect(ruleMatches({ id: "1", kind: "restock", enabled: true }, { ...oldOffer, available: false }, oldOffer)).toBe(true));
});
