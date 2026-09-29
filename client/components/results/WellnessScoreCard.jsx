"use client";

/**
 * Wellness & Insurance Score Card
 * Derives a risk multiplier from the existing report data (no extra API calls).
 * Shows: Wellness Tier, Health Cost Index vs population average, Insurance Risk Band.
 */

const WELLNESS_TIERS = [
  { min: 80, label: "Excellent", color: "emerald", textClass: "text-emerald-600", bgClass: "bg-emerald-50", borderClass: "border-emerald-200", barClass: "bg-emerald-500" },
  { min: 65, label: "Good", color: "teal", textClass: "text-(--color-primary-deep)", bgClass: "bg-emerald-50", borderClass: "border-(--color-primary)/30", barClass: "bg-(--color-primary)" },
  { min: 50, label: "Moderate", color: "amber", textClass: "text-amber-600", bgClass: "bg-amber-50", borderClass: "border-amber-200", barClass: "bg-amber-400" },
  { min: 0, label: "High-Risk", color: "red", textClass: "text-red-600", bgClass: "bg-red-50", borderClass: "border-red-200", barClass: "bg-red-500" },
];

const RISK_BANDS = [
  { max: 1.15, label: "Low", textClass: "text-emerald-600" },
  { max: 1.35, label: "Standard", textClass: "text-(--color-primary-deep)" },
  { max: 1.6, label: "Elevated", textClass: "text-amber-600" },
  { max: Infinity, label: "High", textClass: "text-red-600" },
];

function computeWellnessData(result) {
  const vitalScore = result?.vital_score?.current ?? result?.overall_health_score ?? 50;
  const bio = result?.biological_age;
  const ageGap = typeof bio === "object" ? (bio?.age_gap ?? 0) : 0;
  const organs = result?.organs ?? {};

  let multiplier = 1.0;

  // Vital score penalty
  if (vitalScore < 40) multiplier += 0.35;
  else if (vitalScore < 55) multiplier += 0.20;
  else if (vitalScore < 70) multiplier += 0.08;

  // Age gap penalty
  if (ageGap > 10) multiplier += 0.18;
  else if (ageGap > 5) multiplier += 0.09;
  else if (ageGap < -3) multiplier -= 0.05; // biologically younger is a bonus

  // Organ risk penalties
  const organEntries = Object.entries(organs);
  const redOrgans = [];
  const yellowOrgans = [];
  organEntries.forEach(([name, data]) => {
    const risk = data?.risk_level;
    if (risk === "RED") redOrgans.push(name);
    else if (risk === "YELLOW") yellowOrgans.push(name);
  });
  multiplier += redOrgans.length * 0.15;
  multiplier += yellowOrgans.length * 0.05;

  multiplier = Math.max(0.7, Math.min(2.5, multiplier));

  const tier = WELLNESS_TIERS.find((t) => vitalScore >= t.min) ?? WELLNESS_TIERS[WELLNESS_TIERS.length - 1];
  const band = RISK_BANDS.find((b) => multiplier <= b.max) ?? RISK_BANDS[RISK_BANDS.length - 1];

  // Build rationale sentence
  const reasons = [];
  if (redOrgans.length > 0) reasons.push(`${redOrgans.map((o) => o.charAt(0).toUpperCase() + o.slice(1)).join(" & ")} at critical risk`);
  if (yellowOrgans.length > 0 && redOrgans.length === 0) reasons.push(`${yellowOrgans.map((o) => o.charAt(0).toUpperCase() + o.slice(1)).join(" & ")} at elevated risk`);
  if (ageGap > 5) reasons.push(`biological age ${ageGap} years above chronological`);
  if (vitalScore < 55) reasons.push(`vital score below average`);
  const rationale = reasons.length > 0
    ? reasons.join(", ") + " elevate projected healthcare utilisation."
    : "No major risk flags detected — maintain current habits.";

  // Cost index bar width (1.0 = 50%, 2.5 = 100%)
  const barPct = Math.min(100, Math.max(8, ((multiplier - 0.7) / (2.5 - 0.7)) * 100));

  return { vitalScore, tier, band, multiplier, rationale, barPct, redOrgans, yellowOrgans };
}

export default function WellnessScoreCard({ result }) {
  if (!result) return null;

  const { tier, band, multiplier, rationale, barPct, redOrgans, yellowOrgans } = computeWellnessData(result);

  return (
    <div className={`rounded-2xl p-5 border ${tier.bgClass} ${tier.borderClass}`}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-(--color-primary) uppercase tracking-wider">Wellness &amp; Risk Profile</p>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${tier.bgClass} ${tier.borderClass} ${tier.textClass}`}>
          {tier.label}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        {/* Health Cost Index */}
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-(--color-muted) uppercase tracking-wider">Health Cost Index</p>
          <p className="text-2xl font-semibold text-foreground">
            {multiplier.toFixed(2)}
            <span className="text-sm font-normal text-(--color-muted)">× avg</span>
          </p>
          <div className="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${tier.barClass}`}
              style={{ width: `${barPct}%` }}
            />
          </div>
          <p className="text-xs text-(--color-muted)">Relative to population baseline</p>
        </div>

        {/* Insurance Risk Band */}
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-(--color-muted) uppercase tracking-wider">Insurance Risk Band</p>
          <p className={`text-2xl font-semibold ${band.textClass}`}>{band.label}</p>
          <div className="flex gap-1 mt-1">
            {RISK_BANDS.map((b) => (
              <div
                key={b.label}
                className={`h-1.5 flex-1 rounded-full transition-opacity duration-300 ${
                  band.label === b.label ? "opacity-100" : "opacity-20"
                } ${
                  b.label === "Low" ? "bg-emerald-400" :
                  b.label === "Standard" ? "bg-teal-400" :
                  b.label === "Elevated" ? "bg-amber-400" : "bg-red-400"
                }`}
              />
            ))}
          </div>
          <p className="text-xs text-(--color-muted)">Actuarial risk estimate</p>
        </div>
      </div>

      {/* Risk factors summary */}
      {(redOrgans.length > 0 || yellowOrgans.length > 0) && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {redOrgans.map((o) => (
            <span key={o} className="text-xs px-2 py-0.5 rounded-full bg-red-100 border border-red-200 text-red-600">
              {o.charAt(0).toUpperCase() + o.slice(1)} · Critical
            </span>
          ))}
          {yellowOrgans.map((o) => (
            <span key={o} className="text-xs px-2 py-0.5 rounded-full bg-amber-100 border border-amber-200 text-amber-700">
              {o.charAt(0).toUpperCase() + o.slice(1)} · Elevated
            </span>
          ))}
        </div>
      )}

      <p className="text-xs text-(--color-muted) leading-relaxed border-t border-slate-200 pt-3">
        <span className="text-foreground font-medium">Analysis: </span>
        {rationale}
      </p>
      <p className="text-[10px] text-(--color-muted)/50 mt-2">
        Indicative estimate only. Not a substitute for professional actuarial or medical advice.
      </p>
    </div>
  );
}
