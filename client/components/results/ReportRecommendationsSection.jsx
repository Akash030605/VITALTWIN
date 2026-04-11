"use client";

import PriorityRecommendations from "./PriorityRecommendations";
import WhatIfPanel from "./WhatIfPanel";
import WellnessScoreCard from "./WellnessScoreCard";

export default function ReportRecommendationsSection({ result }) {
  const hasPriority = result?.priority_recommendations?.length > 0;
  const hasWhatIf = result != null;

  if (!hasPriority && !hasWhatIf) return null;

  return (
    <section className="mb-8" id="recommendations" aria-labelledby="recommendations-heading">
      <h2 id="recommendations-heading" className="text-xs font-medium text-(--color-primary) uppercase tracking-wider mb-4">Recommendations</h2>
      <p className="text-sm text-(--color-muted) mb-6">What to do next and how changes could improve your health.</p>

      {hasPriority && (
        <div className="mb-8">
          <h3 className="text-xs font-medium text-(--color-muted) uppercase tracking-wider mb-3">Priority actions</h3>
          <PriorityRecommendations priority_recommendations={result.priority_recommendations} />
        </div>
      )}

      {hasWhatIf && (
        <div className="relative">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-semibold text-(--color-primary) uppercase tracking-wider">What if</h3>
            <span className="text-[10px] text-(--color-muted) font-medium uppercase">Explore scenarios</span>
          </div>
          <WhatIfPanel />
        </div>
      )}

      {result && (
        <div className="mt-8">
          <h3 className="text-xs font-medium text-(--color-muted) uppercase tracking-wider mb-3">Wellness &amp; risk profile</h3>
          <WellnessScoreCard result={result} />
        </div>
      )}
    </section>
  );
}
