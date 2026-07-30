import { Money } from "@/shared/domain/money";

export type AlertKind = "any_drop" | "target_price" | "percentage_drop" | "restock";
export interface AlertRule { id: string; kind: AlertKind; targetPrice?: Money; percentage?: number; enabled: boolean; }

/** Returns whether an observation should create an alert; delivery deduplication happens separately. */
export function ruleMatches(rule: AlertRule, previous: { price: Money; available: boolean } | null, current: { price: Money; available: boolean }): boolean {
  if (!rule.enabled) return false;
  if (rule.kind === "restock") return current.available && !previous?.available;
  if (!current.available || !previous) return false;
  if (rule.kind === "any_drop") return current.price.isLessThan(previous.price);
  if (rule.kind === "target_price") return !!rule.targetPrice && (current.price.isLessThan(rule.targetPrice) || current.price.amount === rule.targetPrice.amount);
  return !!rule.percentage && previous.price.currency === current.price.currency && ((previous.price.amount - current.price.amount) / previous.price.amount) * 100 >= rule.percentage;
}
