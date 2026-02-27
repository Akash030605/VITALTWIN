"use client";

const PRIORITY_COLORS = { CRITICAL: "text-red-400 border-red-400/50", HIGH: "text-amber-400 border-amber-400/50", MEDIUM: "text-[var(--color-primary)] border-[var(--color-primary)]/50" };

export default function PriorityRecommendations({ priority_recommendations }) {
  if (!priority_recommendations?.length) return null;

  return (
    <ul className="space-y-3">
      {priority_recommendations.map((rec, i) => (
        <li key={i} className={`rounded-xl glass-card px-4 py-3 border-l-4 ${PRIORITY_COLORS[rec.priority] ?? "border-[var(--color-primary)]"} hover-lift transition-all duration-200`}>
          <span className="text-xs font-medium text-[var(--color-muted)]">{rec.priority}</span>
          <p className="text-[var(--foreground)] font-medium mt-0.5">{rec.action}</p>
          {rec.impact && <p className="text-sm text-[var(--color-muted)] mt-1">{rec.impact}</p>}
        </li>
      ))}
    </ul>
  );
}
