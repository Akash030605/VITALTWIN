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
    border: "border-red-300 shadow-[0_2px_12px_rgba(239,68,68,0.10)]",
    overlay: "bg-red-50",
    label: "text-red-600 font-semibold",
    bar: "bg-red-500",
    badge: "bg-red-100 text-red-600 border border-red-200",
  },
  YELLOW: {
    status: "Warning",
    border: "border-amber-300 shadow-[0_2px_12px_rgba(251,191,36,0.08)]",
    overlay: "bg-amber-50",
    label: "text-amber-600 font-semibold",
    bar: "bg-amber-400",
    badge: "bg-amber-100 text-amber-700 border border-amber-200",
  },
  GREEN: {
    status: "Normal",
    border: "border-emerald-200 shadow-[0_2px_8px_rgba(16,185,129,0.08)]",
    overlay: "bg-emerald-50",
    label: "text-emerald-600 font-semibold",
    bar: "bg-emerald-500",
    badge: "bg-emerald-100 text-emerald-700 border border-emerald-200",
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
    impact === "positive" ? "text-emerald-600" : impact === "negative" ? "text-red-600" : "text-(--color-muted)";

  const possibleIssues = ORGAN_POSSIBLE_ISSUES[organId]?.[riskLevel] ?? ORGAN_POSSIBLE_ISSUES[organId]?.GREEN ?? [];

  return (
    <section
      ref={sectionRef}
      className={`rounded-2xl overflow-hidden border glass-card glass-card-glow hover-lift ${style.border}`}
      data-organ={organId}
    >
      <div className="flex flex-col lg:flex-row min-h-[280px]">
        <div className="relative w-full lg:w-[40%] h-[280px] lg:h-auto flex-shrink-0">
          <OrganModelView organId={organId} className="absolute inset-0 w-full h-full" />
          <div className={`absolute inset-0 pointer-events-none opacity-20 ${style.overlay}`} aria-hidden />
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
            <span className={`text-sm ${style.label}`}>{name}</span>
            <span className={`text-[10px] uppercase tracking-wider font-medium px-2 py-1 rounded ${style.badge}`}>{style.status}</span>
          </div>
        </div>
        <div className="flex-1 p-6 flex flex-col justify-center border-t lg:border-t-0 lg:border-l border-slate-200">
          <p className="text-2xl font-semibold text-(--foreground) mb-1">{health_score} <span className="text-base font-normal text-(--color-muted)">/ 100</span></p>
          <p className={`text-sm mb-2 ${style.label}`}>Risk {(current_risk * 100).toFixed(0)}%</p>
          <div
            className="relative mb-3"
            onMouseEnter={() => setBarHover(true)}
            onMouseLeave={() => setBarHover(false)}
          >
            <div className="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden cursor-help" title="Hover for possible issues">
              <div className={`h-full ${style.bar} transition-all`} style={{ width: `${Math.min(100, current_risk * 100)}%` }} />
            </div>
            {barHover && possibleIssues.length > 0 && (
              <div
                className="absolute left-0 right-0 top-full mt-2 z-20 rounded-lg border border-slate-200 bg-white shadow-lg p-3"
                role="tooltip"
                aria-live="polite"
              >
                <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider mb-2">Possible issues at this score</p>
                <ul className="space-y-1.5 text-xs text-(--foreground)">
                  {possibleIssues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-(--color-primary) shrink-0 mt-0.5">•</span>
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {risk_progression && (
            <p className="text-xs text-(--color-muted) mb-2">
              Risk over time: 1y {(risk_progression.year_1 * 100).toFixed(0)}% · 3y {(risk_progression.year_3 * 100).toFixed(0)}% · 5y {(risk_progression.year_5 * 100).toFixed(0)}% · 10y {(risk_progression.year_10 * 100).toFixed(0)}%
            </p>
          )}
          {metrics && Object.keys(metrics).length > 0 && (() => {
            // Keys that are raw scores/values (not 0-1 probabilities) — display as-is
            const RAW_VALUE_KEYS = new Set([
              "fib4_score", "nafld_lfs", "ast_alt_ratio", "ggt",
              "ilpd_indian_model_score", "turkish_nash_model_score",
              "fib4_category", "fib4_citation", "method_sources",
              "ilpd_population", "lean_nafld_note", "lean_nafld_source",
              "lean_nafld_detected", "fatty_liver_likely",
            ]);
            // Only show numeric entries that are real finite numbers — skip objects/strings/booleans
            const validEntries = Object.entries(metrics).filter(([k, v]) =>
              !RAW_VALUE_KEYS.has(k) &&
              v !== null && v !== undefined && typeof v === "number" &&
              !isNaN(v) && isFinite(v) &&
              v >= 0 && v <= 1  // only show 0-1 probability/fraction values as %
            );
            // Also show key raw values with proper labels
            const rawEntries = [
              metrics.fib4_score != null ? `FIB-4: ${Number(metrics.fib4_score).toFixed(2)}${metrics.fib4_category ? ` (${metrics.fib4_category})` : ""}` : null,
              metrics.ast_alt_ratio != null ? `AST/ALT: ${Number(metrics.ast_alt_ratio).toFixed(2)}` : null,
              metrics.ggt != null ? `GGT: ${Number(metrics.ggt).toFixed(0)} U/L` : null,
            ].filter(Boolean);

            if (validEntries.length === 0 && rawEntries.length === 0) return null;
            return (
              <p className="text-xs text-(--color-muted) mb-2">
                {[
                  ...rawEntries,
                  ...validEntries.map(([k, v]) => `${k.replace(/_/g, " ")}: ${(Number(v) * 100).toFixed(0)}%`)
                ].join(" · ")}
              </p>
            );
          })()}
          {hasReasons && (
            <div className="mb-3 pt-2 border-t border-slate-200">
              <p className="text-xs font-medium text-(--color-primary) uppercase tracking-wider mb-1.5">Why this score</p>
              {score_reason && typeof score_reason === "string" && (
                <p className="text-sm text-(--foreground)/90 leading-relaxed">{score_reason}</p>
              )}
              {!score_reason && Array.isArray(factors) && factors.length > 0 && (
                <ul className="space-y-1 text-sm">
                  {factors.map((f, i) => (
                    <li key={i} className={`flex items-baseline gap-2 ${factorImpactClass(f.impact)}`}>
                      <span className="shrink-0 w-2 h-2 rounded-full bg-current opacity-80" aria-hidden />
                      <span>{f.factor}</span>
                      {f.detail && <span className="text-(--color-muted) text-xs">— {f.detail}</span>}
                    </li>
                  ))}
                </ul>
              )}
              {score_reason && Array.isArray(factors) && factors.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm text-(--color-muted)">
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
            <p className="text-sm text-(--foreground)">{recommendations[0]}</p>
          )}
        </div>
      </div>
    </section>
  );
}
