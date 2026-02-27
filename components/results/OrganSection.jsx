"use client";

import dynamic from "next/dynamic";
import { useRef } from "react";

const OrganModelView = dynamic(() => import("../OrganModelView"), { ssr: false });

const ORGAN_NAMES = { heart: "Heart", brain: "Brain", liver: "Liver", kidney: "Kidney", lungs: "Lungs" };

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
  if (!organData) return null;

  const name = ORGAN_NAMES[organId] ?? organId;
  const riskLevel = organData.risk_level || "GREEN";
  const style = DEGRADE_STYLES[riskLevel] || DEGRADE_STYLES.GREEN;
  const { health_score, current_risk, metrics, risk_progression, recommendations } = organData;

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
          <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden mb-3">
            <div className={`h-full ${style.bar} transition-all`} style={{ width: `${Math.min(100, current_risk * 100)}%` }} />
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
          {recommendations?.length > 0 && (
            <p className="text-sm text-[var(--foreground)]">{recommendations[0]}</p>
          )}
        </div>
      </div>
    </section>
  );
}
