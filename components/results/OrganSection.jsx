"use client";

import dynamic from "next/dynamic";
import { useRef, useState } from "react";

const OrganModelView = dynamic(() => import("../OrganModelView"), { ssr: false });

const ORGAN_NAMES = { heart: "Heart", brain: "Brain", liver: "Liver", kidney: "Kidney", lungs: "Lungs" };

/** Hard-coded possible issues per organ and risk level (score band). Shown on hover at the risk bar. */
const ORGAN_POSSIBLE_ISSUES = {
  heart: {
    RED: [
      "Elevated cardiovascular risk; consider ECG and lipid panel.",
      "High blood pressure or cholesterol may be affecting heart health.",
      "Smoking, stress, or sedentary lifestyle can worsen outcomes.",
      "Speak to a doctor about heart-health screenings.",
    ],
    YELLOW: [
      "Moderate risk; keep an eye on blood pressure and cholesterol.",
      "Diet and activity improvements can lower risk further.",
      "Stress and poor sleep can strain the heart over time.",
    ],
    GREEN: [
      "Maintain a heart-healthy diet and regular activity.",
      "Limit sodium and saturated fat to keep risk low.",
      "Annual check-ups help catch any changes early.",
    ],
  },
  brain: {
    RED: [
      "Cognitive or mental health risk may be elevated.",
      "Poor sleep, stress, or lack of activity can affect brain health.",
      "Consider a check-up and lifestyle changes.",
      "Stay socially and mentally active to support cognition.",
    ],
    YELLOW: [
      "Moderate risk; focus on sleep, stress, and exercise.",
      "Mental stimulation and social connection support brain health.",
      "Limit alcohol and avoid smoking for better outcomes.",
    ],
    GREEN: [
      "Keep a consistent sleep schedule and stay mentally active.",
      "Physical activity and a balanced diet support brain health.",
      "Manage stress to protect long-term cognitive function.",
    ],
  },
  liver: {
    RED: [
      "Liver stress may be high; alcohol, meds, or diet could be factors.",
      "Consider liver function tests and reducing alcohol intake.",
      "Fatty liver risk may be elevated; weight and diet matter.",
      "Speak to a doctor before taking new supplements.",
    ],
    YELLOW: [
      "Moderate liver load; reduce alcohol and processed foods.",
      "Stay within recommended alcohol limits and avoid excess sugar.",
      "Some medications can affect the liver; review with a doctor.",
    ],
    GREEN: [
      "Limit alcohol and avoid unnecessary medications.",
      "Maintain a healthy weight and balanced diet.",
      "Get liver function checked if you have risk factors.",
    ],
  },
  kidney: {
    RED: [
      "Kidney function may be at risk; blood pressure and diabetes are key factors.",
      "High sodium, dehydration, or certain meds can strain kidneys.",
      "Ask for a kidney function test (e.g. eGFR, creatinine).",
      "Control blood pressure and blood sugar with your doctor.",
    ],
    YELLOW: [
      "Moderate risk; watch sodium intake and stay hydrated.",
      "Manage blood pressure and avoid NSAID overuse.",
      "Annual blood work can track kidney function.",
    ],
    GREEN: [
      "Stay well hydrated and limit excess sodium.",
      "Keep blood pressure and blood sugar in a healthy range.",
      "Avoid prolonged use of NSAIDs without medical advice.",
    ],
  },
  lungs: {
    RED: [
      "Lung or breathing risk may be high; smoking and pollution are common causes.",
      "Consider lung function tests if you have symptoms.",
      "Quit smoking and avoid secondhand smoke and heavy pollution.",
      "See a doctor for persistent cough or shortness of breath.",
    ],
    YELLOW: [
      "Moderate risk; avoid smoking and improve indoor air quality.",
      "Regular cardio exercise can support lung capacity.",
      "Limit exposure to dust, chemicals, and pollution.",
    ],
    GREEN: [
      "Avoid smoking and limit exposure to air pollution.",
      "Aerobic exercise helps maintain lung health.",
      "Get flu and recommended vaccines to protect the lungs.",
    ],
  },
};

const DEGRADE_STYLES = {
  RED: {
    status: "Critical",
    border: "border-red-500/80 shadow-[0_0_20px_rgba(239,68,68,0.15)]",
    overlay: "bg-red-950/50",
    label: "text-red-300 font-semibold",
    bar: "bg-red-500",
    badge: "bg-red-500/20 text-red-300 border border-red-500/50",
  },
  YELLOW: {
    status: "Warning",
    border: "border-amber-400/60 shadow-[0_0_16px_rgba(251,191,36,0.12)]",
    overlay: "bg-amber-950/35",
    label: "text-amber-300 font-semibold",
    bar: "bg-amber-400",
    badge: "bg-amber-500/20 text-amber-300 border border-amber-400/50",
  },
  GREEN: {
    status: "Normal",
    border: "border-emerald-400/50 shadow-[0_0_12px_rgba(52,211,153,0.1)]",
    overlay: "bg-emerald-950/20",
    label: "text-emerald-300 font-semibold",
    bar: "bg-emerald-400",
    badge: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/40",
  },
};

export default function OrganSection({ organId, organData }) {
  const sectionRef = useRef(null);
  const [barHover, setBarHover] = useState(false);
  if (!organData) return null;

  const name = ORGAN_NAMES[organId] ?? organId;
  const riskLevel = organData.risk_level || "GREEN";
  const style = DEGRADE_STYLES[riskLevel] || DEGRADE_STYLES.GREEN;
  const { health_score, current_risk, metrics, risk_progression, recommendations, score_reason, factors } = organData;
  const hasReasons = (score_reason && typeof score_reason === "string") || (Array.isArray(factors) && factors.length > 0);
  const factorImpactClass = (impact) =>
    impact === "positive" ? "text-emerald-300" : impact === "negative" ? "text-red-300" : "text-[var(--color-muted)]";

  const possibleIssues = ORGAN_POSSIBLE_ISSUES[organId]?.[riskLevel] ?? ORGAN_POSSIBLE_ISSUES[organId]?.GREEN ?? [];

  return (
    <section
      ref={sectionRef}
      className={`rounded-2xl overflow-hidden border glass-card glass-card-glow hover-lift ${style.border}`}
      data-organ={organId}
    >
      <div className="flex flex-col lg:flex-row min-h-[280px]">
        <div className="relative w-full lg:w-[40%] min-h-[240px] flex-shrink-0">
          <OrganModelView organId={organId} className="absolute inset-0" />
          <div className={`absolute inset-0 pointer-events-none ${style.overlay}`} aria-hidden />
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
            <span className={`text-sm ${style.label}`}>{name}</span>
            <span className={`text-[10px] uppercase tracking-wider font-medium px-2 py-1 rounded ${style.badge}`}>{style.status}</span>
          </div>
        </div>
        <div className="flex-1 p-6 flex flex-col justify-center border-t lg:border-t-0 lg:border-l border-white/10">
          <p className="text-2xl font-semibold text-[var(--foreground)] mb-1">{health_score} <span className="text-base font-normal text-[var(--color-muted)]">/ 100</span></p>
          <p className={`text-sm mb-2 ${style.label}`}>Risk {(current_risk * 100).toFixed(0)}%</p>
          <div
            className="relative mb-3"
            onMouseEnter={() => setBarHover(true)}
            onMouseLeave={() => setBarHover(false)}
          >
            <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden cursor-help" title="Hover for possible issues">
              <div className={`h-full ${style.bar} transition-all`} style={{ width: `${Math.min(100, current_risk * 100)}%` }} />
            </div>
            {barHover && possibleIssues.length > 0 && (
              <div
                className="absolute left-0 right-0 top-full mt-2 z-20 rounded-lg border border-white/20 bg-[var(--color-surface)] shadow-xl p-3"
                role="tooltip"
                aria-live="polite"
              >
                <p className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-2">Possible issues at this score</p>
                <ul className="space-y-1.5 text-xs text-[var(--foreground)]">
                  {possibleIssues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-[var(--color-primary)] shrink-0 mt-0.5">•</span>
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {risk_progression && (
            <p className="text-xs text-[var(--color-muted)] mb-2">
              Risk over time: 1y {(risk_progression.year_1 * 100).toFixed(0)}% · 3y {(risk_progression.year_3 * 100).toFixed(0)}% · 5y {(risk_progression.year_5 * 100).toFixed(0)}% · 10y {(risk_progression.year_10 * 100).toFixed(0)}%
            </p>
          )}
          {metrics && Object.keys(metrics).length > 0 && (
            <p className="text-xs text-[var(--color-muted)] mb-2">
              {Object.entries(metrics).map(([k, v]) => `${k.replace(/_/g, " ")}: ${(Number(v) * 100).toFixed(0)}%`).join(" · ")}
            </p>
          )}
          {hasReasons && (
            <div className="mb-3 pt-2 border-t border-white/10">
              <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-1.5">Why this score</p>
              {score_reason && typeof score_reason === "string" && (
                <p className="text-sm text-[var(--foreground)]/90 leading-relaxed">{score_reason}</p>
              )}
              {!score_reason && Array.isArray(factors) && factors.length > 0 && (
                <ul className="space-y-1 text-sm">
                  {factors.map((f, i) => (
                    <li key={i} className={`flex items-baseline gap-2 ${factorImpactClass(f.impact)}`}>
                      <span className="shrink-0 w-2 h-2 rounded-full bg-current opacity-80" aria-hidden />
                      <span>{f.factor}</span>
                      {f.detail && <span className="text-[var(--color-muted)] text-xs">— {f.detail}</span>}
                    </li>
                  ))}
                </ul>
              )}
              {score_reason && Array.isArray(factors) && factors.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm text-[var(--color-muted)]">
                  {factors.map((f, i) => (
                    <li key={i} className={`flex items-baseline gap-2 ${factorImpactClass(f.impact)}`}>
                      <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-current opacity-70" aria-hidden />
                      {f.factor}{f.detail ? ` — ${f.detail}` : ""}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {recommendations?.length > 0 && (
            <p className="text-sm text-[var(--foreground)]">{recommendations[0]}</p>
          )}
        </div>
      </div>
    </section>
  );
}
