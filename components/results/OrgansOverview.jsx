"use client";

import Link from "next/link";
import { useState } from "react";

const ORGAN_NAMES = { heart: "Heart", brain: "Brain", liver: "Liver", kidney: "Kidney", lungs: "Lungs" };
const RISK_ORDER = { RED: 0, YELLOW: 1, GREEN: 2 };
const ORGAN_IDS = ["heart", "brain", "liver", "kidney", "lungs"];

const RISK_STYLES = {
  RED: { label: "text-red-400", bar: "bg-red-500", card: "border-red-500/30" },
  YELLOW: { label: "text-amber-400", bar: "bg-amber-500", card: "border-amber-500/30" },
  GREEN: { label: "text-emerald-400", bar: "bg-emerald-500", card: "border-emerald-500/30" },
};

/** Hard-coded possible issues per organ and risk level (for bar hover tooltip). */
const ORGAN_POSSIBLE_ISSUES = {
  heart: { RED: ["High cardiovascular risk; consider screenings.", "Watch blood pressure and cholesterol."], YELLOW: ["Moderate risk; diet and activity help.", "Manage stress and sleep."], GREEN: ["Keep a heart-healthy lifestyle.", "Annual check-ups recommended."] },
  brain: { RED: ["Cognitive/mental health risk; consider a check-up.", "Sleep and stress affect brain health."], YELLOW: ["Moderate risk; stay active and socially engaged.", "Limit alcohol and avoid smoking."], GREEN: ["Stay mentally and physically active.", "Good sleep supports cognition."] },
  liver: { RED: ["Liver stress may be high; reduce alcohol.", "Consider liver function tests."], YELLOW: ["Moderate load; limit alcohol and processed foods.", "Review meds with your doctor."], GREEN: ["Limit alcohol and maintain healthy weight.", "Avoid unnecessary medications."] },
  kidney: { RED: ["Kidney risk elevated; control BP and blood sugar.", "Ask for kidney function tests."], YELLOW: ["Moderate risk; stay hydrated, watch sodium.", "Avoid NSAID overuse."], GREEN: ["Stay hydrated and limit excess sodium.", "Keep BP and sugar in range."] },
  lungs: { RED: ["Lung risk high; quit smoking, avoid pollution.", "Consider lung function tests."], YELLOW: ["Moderate risk; avoid smoke and improve air quality.", "Cardio exercise helps."], GREEN: ["Avoid smoking and air pollution.", "Aerobic exercise supports lungs."] },
};

function sortOrgansByRisk(organs) {
  if (!organs) return ORGAN_IDS;
  return [...ORGAN_IDS].sort((a, b) => {
    const ra = RISK_ORDER[organs[a]?.risk_level] ?? 2;
    const rb = RISK_ORDER[organs[b]?.risk_level] ?? 2;
    return ra - rb;
  });
}

function OrganCard({ organId, data }) {
  const [barHover, setBarHover] = useState(false);
  const name = ORGAN_NAMES[organId] ?? organId;
  const riskLevel = data.risk_level || "GREEN";
  const style = RISK_STYLES[riskLevel] || RISK_STYLES.GREEN;
  const riskPct = Math.min(100, Math.round((data.current_risk ?? 0) * 100));
  const possibleIssues = ORGAN_POSSIBLE_ISSUES[organId]?.[riskLevel] ?? ORGAN_POSSIBLE_ISSUES[organId]?.GREEN ?? [];

  return (
    <Link
      href="/organs"
      className={`rounded-xl glass-card glass-card-glow hover-lift p-4 border ${style.card} transition-all duration-200 block relative`}
      aria-label={`${name} — ${data.health_score} score, ${riskLevel} risk`}
    >
      <p className={`text-sm font-semibold ${style.label} mb-1`}>{name}</p>
      <p className="text-lg font-semibold text-[var(--foreground)]">{data.health_score ?? "—"}<span className="text-xs font-normal text-[var(--color-muted)]">/100</span></p>
      <div
        className="mt-2 relative"
        onMouseEnter={(e) => { e.preventDefault(); e.stopPropagation(); setBarHover(true); }}
        onMouseLeave={(e) => { e.preventDefault(); e.stopPropagation(); setBarHover(false); }}
      >
        <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden cursor-help" title="Hover for possible issues">
          <div className={`h-full ${style.bar} transition-all duration-500 rounded-full`} style={{ width: `${riskPct}%` }} />
        </div>
        {barHover && possibleIssues.length > 0 && (
          <div
            className="absolute left-0 right-0 top-full mt-2 z-30 rounded-lg border border-white/20 bg-[var(--color-surface)] shadow-xl p-2.5 min-w-[180px]"
            role="tooltip"
            aria-live="polite"
          >
            <p className="text-[10px] font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-1.5">Possible issues</p>
            <ul className="space-y-1 text-[11px] text-[var(--foreground)]">
              {possibleIssues.map((issue, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-[var(--color-primary)] shrink-0">•</span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <p className="text-xs text-[var(--color-muted)] mt-1.5">{riskLevel}</p>
    </Link>
  );
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
          return (
            <OrganCard key={organId} organId={organId} data={data} />
          );
        })}
      </div>
    </div>
  );
}
