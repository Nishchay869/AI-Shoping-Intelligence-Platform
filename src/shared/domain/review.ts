export type TrustTier = "trusted" | "uncertain" | "likely_fake";

/** One shopper's review of a product, as returned by GET /products/{id}/reviews. trust_score/trust_tier come
 * from the fake-review-detection ensemble (backend/ml/fake_review_detection); null until scored. */
export type Review = {
  id: string;
  rating: number;
  title: string | null;
  body: string | null;
  is_verified_purchase: boolean;
  created_at: string;
  trust_score: number | null;
  trust_tier: TrustTier | null;
};
