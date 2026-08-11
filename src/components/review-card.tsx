import { Icon } from "./icons";
import type { Review } from "@/shared/domain/review";

const TRUST_STYLE: Record<string, { label: string; className: string }> = {
  trusted: { label: "Trusted", className: "bg-emerald-50 text-emerald-700" },
  uncertain: { label: "Unverified", className: "bg-amber-50 text-amber-700" },
  likely_fake: { label: "Likely fake", className: "bg-rose-50 text-rose-700" },
};

/** One shopper review, with a fake-review-detection trust badge (backend/ml/fake_review_detection ensemble). */
export function ReviewCard({ review }: { review: Review }) {
  const trust = review.trust_tier ? TRUST_STYLE[review.trust_tier] : null;
  return (
    <article className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="data text-sm font-bold text-ink">★ {review.rating}</span>
          {review.is_verified_purchase && (
            <span className="pill flex items-center gap-1 bg-emerald-50 text-emerald-700"><Icon name="check" className="h-3 w-3" />Verified</span>
          )}
        </div>
        {trust && (
          <span className={`pill flex items-center gap-1 ${trust.className}`} title={review.trust_score != null ? `${(review.trust_score * 100).toFixed(0)}% fake-probability` : undefined}>
            <Icon name="shield" className="h-3 w-3" />{trust.label}
          </span>
        )}
      </div>
      {review.title && <h3 className="mt-3 font-semibold text-ink">{review.title}</h3>}
      {review.body && <p className="mt-1 text-sm text-slate-600">{review.body}</p>}
      <p className="mt-3 text-xs text-slate-400">{new Date(review.created_at).toLocaleDateString()}</p>
    </article>
  );
}
