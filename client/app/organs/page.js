"use client";

import { useRef, useEffect, useMemo } from "react";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import AppHeader from "../../components/layout/AppHeader";
import DashboardBackground from "../../components/ui/DashboardBackground";
import DashboardLayout from "../../components/results/DashboardLayout";
import OrganSection from "../../components/results/OrganSection";
import YourInputsSummary from "../../components/results/YourInputsSummary";

const RISK_ORDER = { RED: 0, YELLOW: 1, GREEN: 2 };
const ORGAN_IDS = ["heart", "brain", "liver", "kidney", "lungs"];

function sortOrgansByDegradation(organs) {
  if (!organs) return ORGAN_IDS;
  return [...ORGAN_IDS].sort((a, b) => {
    const ra = RISK_ORDER[organs[a]?.risk_level] ?? 2;
    const rb = RISK_ORDER[organs[b]?.risk_level] ?? 2;
    return ra - rb;
  });
}

const RISK_SUMMARY_CONFIG = {
  RED:    { text: "Critical",  color: "text-red-700",     bg: "bg-red-50",     border: "border-red-200",     dot: "bg-red-500" },
  YELLOW: { text: "Warning",   color: "text-amber-700",   bg: "bg-amber-50",   border: "border-amber-200",   dot: "bg-amber-400" },
  GREEN:  { text: "Normal",    color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500" },
};

export default function OrgansPage() {
  const result = useStore((s) => s.result);
  const profile = useStore((s) => s.profile);
  const input = useStore((s) => s.input);
  const contentRef = useRef(null);
  const organOrder = useMemo(() => sortOrgansByDegradation(result?.organs), [result?.organs]);

  useEffect(() => {
    if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
  }, [result]);

  // Count organs by risk
  const organs = result?.organs ?? {};
  const riskCounts = { RED: 0, YELLOW: 0, GREEN: 0 };
  Object.values(organs).forEach((o) => {
    const r = o?.risk_level ?? "GREEN";
    if (riskCounts[r] !== undefined) riskCounts[r]++;
  });

  return (
    <div className="min-h-screen bg-(--color-bg) flex flex-col">
      <DashboardBackground />
      <AppHeader />

      <main className="flex-1 py-8 px-4 md:px-6">
        <div className="max-w-4xl mx-auto">
          <DashboardLayout>
            <div ref={contentRef}>

              {/* Page header */}
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-slate-900 mb-1.5">Organ Health</h1>
                <p className="text-(--color-muted) text-sm mb-5">Detailed analysis of each organ. Shown by risk level — highest risk first.</p>

                {/* Risk summary pills */}
                {Object.keys(organs).length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-5">
                    {Object.entries(riskCounts).filter(([, count]) => count > 0).map(([risk, count]) => {
                      const cfg = RISK_SUMMARY_CONFIG[risk];
                      return (
                        <div key={risk} className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 border text-xs font-semibold ${cfg.bg} ${cfg.border} ${cfg.color}`}>
                          <div className={`w-2 h-2 rounded-full ${cfg.dot}`} aria-hidden />
                          {count} {cfg.text}
                        </div>
                      );
                    })}
                  </div>
                )}

                <YourInputsSummary profile={profile} input={input} />
              </div>

              {/* Organ detail sections */}
              <div className="space-y-6">
                {organOrder.map((organId) => (
                  <OrganSection key={organId} organId={organId} organData={result?.organs?.[organId]} />
                ))}
              </div>

            </div>
          </DashboardLayout>
        </div>
      </main>

      <footer className="h-12 flex items-center justify-center border-t border-slate-200">
        <span className="text-xs text-(--color-muted)">VitalTwin · Intelligent Health Analysis</span>
      </footer>
    </div>
  );
}
