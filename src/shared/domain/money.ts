/** Currency-aware amount expressed in minor units to avoid floating point price errors. */
export class Money {
  private constructor(readonly amount: number, readonly currency: string) {}
  static fromMinor(amount: number, currency: string): Money {
    if (!Number.isSafeInteger(amount) || amount < 0) throw new Error("Money must be a non-negative integer in minor units");
    if (!/^[A-Z]{3}$/.test(currency)) throw new Error("Money requires an ISO 4217 currency");
    return new Money(amount, currency);
  }
  isLessThan(other: Money): boolean {
    if (this.currency !== other.currency) throw new Error("Cannot compare different currencies");
    return this.amount < other.amount;
  }
}
