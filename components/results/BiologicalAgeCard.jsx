"use client";

import AnimatedCounter from "../ui/AnimatedCounter";

const GAP_COLORS = { RED: "text-red-400 border-red-400/50", YELLOW: "text-amber-400 border-amber-400/50", GREEN: "text-emerald-400 border-emerald-400/50" };

export default function BiologicalAgeCard({ biological_age }) {
  if (!biological_age) return null;
  const { real_age, biological_age: bioAge, age_gap, gap_level, message, factors } = biological_age;
  const colorClass = GAP_COLORS[gap_level] || GAP_COLORS.YELLOW;

  return (
    <div className={`rounded-2xl p-6 border glass-card ${colorClass}`}>
      <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-2">Biological age (clinical)</p>
      <div className="flex flex-wrap items-baseline gap-4 mb-2">
        <span className="text-[var(--foreground)]">Real age <strong><AnimatedCounter value={real_age} duration={800} /></strong></span>
        <span className={colorClass}>Biological age <strong><AnimatedCounter value={bioAge} duration={800} /></strong></span>
        <span className="text-sm text-[var(--color-muted)]">Gap {age_gap > 0 ? "+" : ""}<AnimatedCounter value={age_gap} duration={800} /> years</span>
      </div>
      {message && <p className="text-sm text-[var(--color-muted)] mb-3">{message}</p>}
      {factors?.length > 0 && (
        <ul className="text-sm text-[var(--color-muted)] space-y-1 list-disc list-inside">
          {factors.slice(0, 3).map((f, i) => (
            <li key={i}>{f}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
