"use client";

const LABELS = {
  cardiovascular: "Cardio",
  metabolic: "Metabolic",
  sleep_debt: "Sleep",
  lifestyle: "Lifestyle",
  heart: "Heart",
  brain: "Brain",
  liver: "Liver",
  kidney: "Kidney",
  lungs: "Lungs",
};

const COLOR_CONFIG = {
  RED:    { bg: "bg-red-50",     border: "border-red-200",     text: "text-red-700",     dot: "bg-red-500",     label: "High" },
  YELLOW: { bg: "bg-amber-50",   border: "border-amber-200",   text: "text-amber-700",   dot: "bg-amber-400",   label: "Moderate" },
  GREEN:  { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", dot: "bg-emerald-500", label: "Low" },
};

function StressBadge({ label, color }) {
  const cfg = COLOR_CONFIG[color] ?? COLOR_CONFIG.GREEN;
  return (
    <div className={`rounded-xl border ${cfg.bg} ${cfg.border} p-3 flex flex-col items-center gap-1`}>
      <div className={`w-2 h-2 rounded-full ${cfg.dot}`} aria-hidden />
      <p className="text-xs font-semibold text-slate-700 text-center leading-tight">{label}</p>
      <p className={`text-[10px] font-bold uppercase ${cfg.text}`}>{cfg.label}</p>
    </div>
  );
}

export default function StressHeatmap({ body_stress }) {
  if (!body_stress?.systems && !body_stress?.heatmap_zones?.length) return null;

  const systems = body_stress.systems ? Object.entries(body_stress.systems) : [];
  const zones = body_stress.heatmap_zones ?? [];
  const overallPct = Math.round((body_stress.overall_stress ?? 0) * 100);
  const overallCfg = COLOR_CONFIG[
    overallPct > 65 ? "RED" : overallPct > 40 ? "YELLOW" : "GREEN"
  ] ?? COLOR_CONFIG.GREEN;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider">Body Stress</p>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${overallCfg.bg} ${overallCfg.border} ${overallCfg.text}`}>
          <div className={`w-1.5 h-1.5 rounded-full ${overallCfg.dot}`} aria-hidden />
          {body_stress.overall_level ?? "—"} · {overallPct}%
        </div>
      </div>

      {/* Overall stress bar */}
      <div className="mb-4">
        <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${overallCfg.dot}`}
            style={{ width: `${overallPct}%` }}
          />
        </div>
      </div>

      {systems.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-(--color-muted) font-medium uppercase tracking-wider mb-2">By System</p>
          <div className="grid grid-cols-4 gap-2">
            {systems.map(([key, s]) => (
              <StressBadge key={key} label={LABELS[key] ?? key} color={s.color} />
            ))}
          </div>
        </div>
      )}

      {zones.length > 0 && (
        <div className="flex-1">
          <p className="text-xs text-(--color-muted) font-medium uppercase tracking-wider mb-2">By Organ</p>
          <div className="grid grid-cols-5 gap-2">
            {zones.map((z) => (
              <StressBadge key={z.organ} label={LABELS[z.organ] ?? z.organ} color={z.color} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
