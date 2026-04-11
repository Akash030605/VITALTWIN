"use client";

import AnimatedCounter from "../ui/AnimatedCounter";

const GAP_CONFIG = {
  RED:    { text: "text-red-600",     bg: "bg-red-50",     border: "border-red-200",     label: "Older than average", icon: "↑" },
  YELLOW: { text: "text-amber-600",   bg: "bg-amber-50",   border: "border-amber-200",   label: "Slightly older",      icon: "→" },
  GREEN:  { text: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", label: "Younger than average", icon: "↓" },
};

export default function BiologicalAgeCard({ biological_age }) {
  if (!biological_age) return null;
  const { real_age, biological_age: bioAge, age_gap, gap_level, message, factors } = biological_age;
  const cfg = GAP_CONFIG[gap_level] ?? GAP_CONFIG.YELLOW;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider mb-4">Biological Age</p>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-(--color-muted) mb-1">Chronological</p>
          <p className="text-3xl font-bold text-slate-900">
            <AnimatedCounter value={real_age} duration={800} />
            <span className="text-base font-normal text-(--color-muted) ml-1">yrs</span>
          </p>
        </div>
        <div>
          <p className="text-xs text-(--color-muted) mb-1">Biological</p>
          <p className={`text-3xl font-bold ${cfg.text}`}>
            <AnimatedCounter value={bioAge} duration={800} />
            <span className="text-base font-normal ml-1">yrs</span>
          </p>
        </div>
      </div>

      <div className={`flex items-center gap-2 rounded-xl px-3 py-2.5 border ${cfg.bg} ${cfg.border} mb-3`}>
        <span className={`text-base font-bold ${cfg.text}`}>{cfg.icon}</span>
        <div>
          <p className={`text-sm font-semibold ${cfg.text}`}>
            {age_gap > 0 ? `+${age_gap}` : age_gap} years gap · {cfg.label}
          </p>
          {message && <p className="text-xs text-(--color-muted) mt-0.5">{message}</p>}
        </div>
      </div>

      {factors?.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-(--color-muted) uppercase tracking-wider">Contributing factors</p>
          {factors.slice(0, 3).map((f, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-(--color-muted)">
              <div className="w-1.5 h-1.5 rounded-full bg-(--color-primary) shrink-0 mt-1.5" aria-hidden />
              <span>{f}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
