"use client";

import Link from "next/link";

const ORGAN_NAMES = { heart: "Heart", brain: "Brain", liver: "Liver", kidney: "Kidney", lungs: "Lungs" };
const RISK_ORDER = { RED: 0, YELLOW: 1, GREEN: 2 };
const ORGAN_IDS = ["heart", "brain", "liver", "kidney", "lungs"];

const RISK_STYLES = {
  RED: { label: "text-red-400", bar: "bg-red-500", card: "border-red-500/30" },
  YELLOW: { label: "text-amber-400", bar: "bg-amber-500", card: "border-amber-500/30" },
  GREEN: { label: "text-emerald-400", bar: "bg-emerald-500", card: "border-emerald-500/30" },
};

function sortOrgansByRisk(organs) {
  if (!organs) return ORGAN_IDS;
  return [...ORGAN_IDS].sort((a, b) => {
    const ra = RISK_ORDER[organs[a]?.risk_level] ?? 2;
    const rb = RISK_ORDER[organs[b]?.risk_level] ?? 2;
    return ra - rb;
  });
}

export default function OrgansOverview({ organs }) {
  if (!organs || Object.keys(organs).length === 0) return null;

  const order = sortOrgansByRisk(organs);

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider">Organs</p>
        <Link
          href="/organs"
          className="text-sm text-[var(--color-primary)] font-medium hover:underline transition-opacity"
          aria-label="View all organs"
        >
          View all →
        </Link>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {order.map((organId) => {
          const data = organs[organId];
          if (!data) return null;
          const name = ORGAN_NAMES[organId] ?? organId;
          const riskLevel = data.risk_level || "GREEN";
          const style = RISK_STYLES[riskLevel] || RISK_STYLES.GREEN;
          const riskPct = Math.min(100, Math.round((data.current_risk ?? 0) * 100));
          return (
            <Link
              key={organId}
              href="/organs"
              className={`rounded-xl glass-card glass-card-glow hover-lift p-4 border ${style.card} transition-all duration-200 block`}
              aria-label={`${name} — ${data.health_score} score, ${riskLevel} risk`}
            >
              <p className={`text-sm font-semibold ${style.label} mb-1`}>{name}</p>
              <p className="text-lg font-semibold text-[var(--foreground)]">{data.health_score ?? "—"}<span className="text-xs font-normal text-[var(--color-muted)]">/100</span></p>
              <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden mt-2">
                <div className={`h-full ${style.bar} transition-all duration-500 rounded-full`} style={{ width: `${riskPct}%` }} />
              </div>
              <p className="text-xs text-[var(--color-muted)] mt-1.5">{riskLevel}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
