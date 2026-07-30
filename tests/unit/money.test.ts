import { describe, expect, it } from "vitest";
import { Money } from "@/shared/domain/money";

describe("Money", () => {
  it("constructs from a valid non-negative integer minor-unit amount and ISO currency", () => {
    const money = Money.fromMinor(1999, "USD");
    expect(money.amount).toBe(1999);
    expect(money.currency).toBe("USD");
  });

  it("rejects a negative amount", () => {
    expect(() => Money.fromMinor(-100, "USD")).toThrow();
  });

  it("rejects a non-integer amount (floating point prices are the exact bug this class prevents)", () => {
    expect(() => Money.fromMinor(19.99, "USD")).toThrow();
  });

  it("rejects an unsafe (non-integer-representable) amount", () => {
    expect(() => Money.fromMinor(Number.MAX_SAFE_INTEGER + 1, "USD")).toThrow();
  });

  it("rejects a malformed currency code", () => {
    expect(() => Money.fromMinor(1000, "usd")).toThrow();
    expect(() => Money.fromMinor(1000, "US")).toThrow();
    expect(() => Money.fromMinor(1000, "USDD")).toThrow();
    expect(() => Money.fromMinor(1000, "")).toThrow();
  });

  it("compares two amounts in the same currency", () => {
    const cheaper = Money.fromMinor(1000, "USD");
    const pricier = Money.fromMinor(2000, "USD");
    expect(cheaper.isLessThan(pricier)).toBe(true);
    expect(pricier.isLessThan(cheaper)).toBe(false);
  });

  it("refuses to compare two different currencies", () => {
    const usd = Money.fromMinor(1000, "USD");
    const inr = Money.fromMinor(1000, "INR");
    expect(() => usd.isLessThan(inr)).toThrow();
  });
});
