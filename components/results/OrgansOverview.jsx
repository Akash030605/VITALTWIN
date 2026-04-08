"use client";

import Link from "next/link";
import { useState } from "react";

const ORGAN_NAMES = { heart: "Heart", brain: "Brain", liver: "Liver", kidney: "Kidney", lungs: "Lungs" };
const ORGAN_ICONS = {
  heart: "M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z",
  brain: "M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.357 2.059l1.893.893M14.25 3.104c.251.023.501.05.75.082M19.5 14.5l-4.091-4.091a2.25 2.25 0 00-1.659-.659H10.25M19.5 14.5c.667.667 1 1.5 1 2.5s-.333 1.833-1 2.5-1.5 1-2.5 1-1.833-.333-2.5-1-1-1.5-1-2.5.333-1.833 1-2.5M19.5 14.5l-4.5 4.5M4.5 14.5c-.667.667-1 1.5-1 2.5s.333 1.833 1 2.5 1.5 1 2.5 1 1.833-.333 2.5-1 1-1.5 1-2.5-.333-1.833-1-2.5M4.5 14.5l4.5 4.5",
  liver: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
  kidney: "M12 3c-4.97 0-9 3.185-9 7.115 0 2.557 1.522 4.82 3.889 6.115L6 19.5l3.5-2.385C10.285 17.37 11.129 17.5 12 17.5s1.715-.13 2.5-.385L18 19.5l-.889-3.27C19.478 14.935 21 12.672 21 10.115 21 6.185 16.97 3 12 3z",
  lungs: "M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25",
};
const RISK_ORDER = { RED: 0, YELLOW: 1, GREEN: 2 };
const ORGAN_IDS = ["heart", "brain", "liver", "kidney", "lungs"];

const RISK_STYLES = {
  RED:    { scoreTxt: "text-red-600",     barBg: "bg-red-500",     cardBorder: "border-red-200",     badge: "bg-red-50 text-red-700 border-red-200",     statusDot: "bg-red-500",     label: "Critical" },
  YELLOW: { scoreTxt: "text-amber-600",   barBg: "bg-amber-400",   cardBorder: "border-amber-200",   badge: "bg-amber-50 text-amber-700 border-amber-200", statusDot: "bg-amber-400",   label: "Warning" },
  GREEN:  { scoreTxt: "text-emerald-600", barBg: "bg-emerald-500", cardBorder: "border-emerald-200", badge: "bg-emerald-50 text-emerald-700 border-emerald-200", statusDot: "bg-emerald-500", label: "Normal" },
};

const ORGAN_POSSIBLE_ISSUES = {
  heart: { RED: ["High cardiovascular risk; consider screenings.", "Watch blood pressure and cholesterol."], YELLOW: ["Moderate risk; diet and activity help.", "Manage stress and sleep."], GREEN: ["Keep a heart-healthy lifestyle.", "Annual check-ups recommended."] },
  brain: { RED: ["Cognitive risk elevated; consider a check-up.", "Sleep and stress affect brain health."], YELLOW: ["Moderate risk; stay active.", "Limit alcohol."], GREEN: ["Stay mentally active.", "Good sleep supports cognition."] },
  liver: { RED: ["Liver stress high; reduce alcohol.", "Consider liver function tests."], YELLOW: ["Moderate load; limit alcohol.", "Review meds with your doctor."], GREEN: ["Limit alcohol.", "Maintain healthy weight."] },
  kidney: { RED: ["Kidney risk elevated; control BP.", "Ask for kidney function tests."], YELLOW: ["Moderate risk; stay hydrated.", "Avoid NSAID overuse."], GREEN: ["Stay hydrated.", "Keep BP in range."] },
  lungs: { RED: ["Lung risk high; quit smoking.", "Consider lung function tests."], YELLOW: ["Moderate risk; avoid smoke.", "Cardio exercise helps."], GREEN: ["Avoid smoking.", "Exercise supports lungs."] },
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
  const [hover, setHover] = useState(false);
  const name = ORGAN_NAMES[organId] ?? organId;
  const riskLevel = data.risk_level || "GREEN";
  const style = RISK_STYLES[riskLevel] ?? RISK_STYLES.GREEN;
  const riskPct = Math.min(100, Math.round((data.current_risk ?? 0) * 100));
  const issues = ORGAN_POSSIBLE_ISSUES[organId]?.[riskLevel] ?? [];
  const iconPath = ORGAN_ICONS[organId];

  return (
    <div className="relative">
      <Link
        href="/organs"
        className={`block bg-white rounded-2xl border ${style.cardBorder} shadow-sm p-4 hover:shadow-md transition-all duration-200`}
        aria-label={`${name} — ${data.health_score ?? "—"} score, ${style.label} risk`}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        {/* Icon + name */}
        <div className="flex items-center gap-2 mb-3">
          {iconPath && (
            <svg className={`w-4 h-4 ${style.scoreTxt} shrink-0`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" d={iconPath} />
            </svg>
          )}
          <p className="text-sm font-semibold text-slate-800">{name}</p>
        </div>

        {/* Score */}
        <p className={`text-2xl font-bold ${style.scoreTxt} mb-1`}>
          {data.health_score ?? "—"}
          <span className="text-xs font-normal text-(--color-muted) ml-0.5">/100</span>
        </p>

        {/* Risk bar */}
        <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden mb-2">
          <div className={`h-full ${style.barBg} rounded-full transition-all duration-500`} style={{ width: `${riskPct}%` }} />
        </div>

        {/* Status badge */}
        <div className={`inline-flex items-center gap-1.5 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${style.badge}`}>
          <div className={`w-1.5 h-1.5 rounded-full ${style.statusDot} shrink-0`} aria-hidden />
          {style.label}
        </div>
      </Link>

      {/* Hover tooltip */}
      {hover && issues.length > 0 && (
        <div
          className="absolute left-0 right-0 top-full mt-2 z-30 bg-white rounded-xl border border-slate-200 shadow-xl p-3"
          role="tooltip"
        >
          <p className="text-[10px] font-bold text-(--color-primary) uppercase tracking-wider mb-2">Possible concerns</p>
          <ul className="space-y-1.5">
            {issues.map((issue, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-slate-700">
                <div className="w-1 h-1 rounded-full bg-(--color-primary) shrink-0 mt-1.5" aria-hidden />
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function OrgansOverview({ organs }) {
  if (!organs || Object.keys(organs).length === 0) return null;
  const order = sortOrgansByRisk(organs);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider">Organ Health</p>
        <Link href="/organs" className="text-xs font-semibold text-(--color-primary) hover:text-(--color-primary-deep) transition-colors">
          View details →
        </Link>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {order.map((organId) => {
          const data = organs[organId];
          if (!data) return null;
          return <OrganCard key={organId} organId={organId} data={data} />;
        })}
      </div>
    </div>
  );
}
