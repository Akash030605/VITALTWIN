"use client";

const LABELS = {
  cardiovascular: "Cardiovascular",
  metabolic: "Metabolic",
  sleep_debt: "Sleep debt",
  lifestyle: "Lifestyle",
  heart: "Heart",
  brain: "Brain",
  liver: "Liver",
  kidney: "Kidney",
  lungs: "Lungs",
};

export default function StressHeatmap({ body_stress }) {
  if (!body_stress?.systems && !body_stress?.heatmap_zones?.length) return null;

  const systems = body_stress.systems ? Object.entries(body_stress.systems) : [];
  const zones = body_stress.heatmap_zones ?? [];

  return (
    <div className="rounded-2xl p-5 glass-card glass-card-glow hover-lift h-full min-h-[200px] flex flex-col">
      <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-3">Stress heatmap</p>
      <p className="text-[var(--foreground)] font-semibold mb-3 text-sm">
        Overall: <span className="text-[var(--color-primary)] font-semibold">{body_stress.overall_level}</span> ({(body_stress.overall_stress * 100).toFixed(0)}%)
      </p>

      {/* Systems row */}
      {systems.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-[var(--color-muted)] uppercase tracking-wider mb-2">By system</p>
          <div className="grid grid-cols-4 gap-2">
            {systems.map(([key, s]) => (
              <div
                key={key}
                className={`rounded-lg flex flex-col items-center justify-center min-h-[52px] p-2.5 border ${
                  s.color === "RED" ? "bg-red-950/60 border-red-400/50" : s.color === "YELLOW" ? "bg-amber-950/50 border-amber-400/50" : "bg-emerald-950/50 border-emerald-400/50"
                }`}
                title={`${LABELS[key] ?? key}: ${s.level}`}
              >
                <span className="text-xs font-semibold text-white truncate w-full text-center drop-shadow-sm">{LABELS[key] ?? key}</span>
                <span className={`text-xs font-bold uppercase mt-1 ${s.color === "RED" ? "text-red-200" : s.color === "YELLOW" ? "text-amber-200" : "text-emerald-200"}`}>{s.level}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Organ zones row */}
      {zones.length > 0 && (
        <div className="flex-1">
          <p className="text-xs text-[var(--color-muted)] uppercase tracking-wider mb-2">By organ</p>
          <div className="grid grid-cols-5 gap-2">
            {zones.map((z) => (
              <div
                key={z.organ}
                className={`rounded-lg flex flex-col items-center justify-center min-h-[48px] p-2.5 border ${
                  z.color === "RED" ? "bg-red-950/60 border-red-400/50" : z.color === "YELLOW" ? "bg-amber-950/50 border-amber-400/50" : "bg-emerald-950/50 border-emerald-400/50"
                }`}
                style={{ opacity: 0.85 + (z.intensity ?? 0.5) * 0.15 }}
                title={`${LABELS[z.organ] ?? z.organ}: ${(z.strain * 100).toFixed(0)}%`}
              >
                <span className="text-xs font-semibold text-white truncate w-full text-center">{LABELS[z.organ] ?? z.organ}</span>
                <span className={`text-xs font-bold uppercase mt-1 ${z.color === "RED" ? "text-red-200" : z.color === "YELLOW" ? "text-amber-200" : "text-emerald-200"}`}>{z.color}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
