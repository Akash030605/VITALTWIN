"use client";

const LEVEL_COLORS = { RED: "text-red-600", YELLOW: "text-amber-600", GREEN: "text-emerald-600" };
const LABELS = {
  cardiovascular: "Cardiovascular",
  metabolic: "Metabolic",
  sleep_debt: "Sleep debt",
  lifestyle: "Lifestyle",
};

export default function BodyStressSection({ body_stress }) {
  if (!body_stress?.systems) return null;
  const systems = body_stress.systems;

  return (
    <div className="rounded-2xl p-6 glass-card glass-card-glow hover-lift">
      <p className="text-xs font-medium text-(--color-primary) uppercase tracking-wider mb-2">Body stress</p>
      <p className="text-(--foreground) font-medium mb-3">
        Overall: <span className="text-(--color-primary)">{body_stress.overall_level}</span> ({(body_stress.overall_stress * 100).toFixed(0)}%)
      </p>
      <ul className="space-y-2.5" aria-label="Stress by system">
        {Object.entries(systems).map(([key, s]) => (
          <li key={key} className="flex items-center justify-between text-sm py-1 border-b border-slate-100 last:border-0">
            <span className="text-(--foreground)">{LABELS[key] ?? key}</span>
            <span className={LEVEL_COLORS[s.color] ?? "text-(--color-muted)"}>{s.level}</span>
          </li>
        ))}
      </ul>
      {body_stress.heatmap_zones?.length > 0 && (
        <p className="text-xs text-(--color-muted) mt-3">
          By organ: {body_stress.heatmap_zones.map((z) => `${z.organ} (${z.color})`).join(", ")}
        </p>
      )}
    </div>
  );
}
