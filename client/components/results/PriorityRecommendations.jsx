"use client";

const PRIORITY_CONFIG = {
  CRITICAL: { bg: "bg-red-50",     border: "border-red-200",     accent: "bg-red-500",     text: "text-red-700",     badge: "bg-red-100 text-red-700 border-red-200" },
  HIGH:     { bg: "bg-amber-50",   border: "border-amber-200",   accent: "bg-amber-400",   text: "text-amber-700",   badge: "bg-amber-100 text-amber-700 border-amber-200" },
  MEDIUM:   { bg: "bg-emerald-50", border: "border-emerald-200", accent: "bg-emerald-500", text: "text-emerald-700", badge: "bg-emerald-100 text-emerald-700 border-emerald-200" },
};

export default function PriorityRecommendations({ priority_recommendations }) {
  if (!priority_recommendations?.length) return null;

  return (
    <ul className="space-y-3 list-none p-0 m-0">
      {priority_recommendations.map((rec, i) => {
        const cfg = PRIORITY_CONFIG[rec.priority] ?? PRIORITY_CONFIG.MEDIUM;
        return (
          <li key={i} className={`rounded-2xl border ${cfg.bg} ${cfg.border} p-4 flex gap-4`}>
            <div className={`w-1 shrink-0 rounded-full ${cfg.accent} mt-0.5`} aria-hidden />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <span className={`inline-block text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                  {rec.priority}
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-900 leading-snug">{rec.action}</p>
              {rec.impact && <p className="text-sm text-(--color-muted) mt-1.5 leading-relaxed">{rec.impact}</p>}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
