"use client";

import { useRef, useEffect, useMemo } from "react";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import AppHeader from "../../components/layout/AppHeader";
import DashboardBackground from "../../components/ui/DashboardBackground";
import DashboardLayout from "../../components/results/DashboardLayout";
import OrganSection from "../../components/results/OrganSection";

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

export default function OrgansPage() {
  const result = useStore((s) => s.result);
  const contentRef = useRef(null);
  const organOrder = useMemo(() => sortOrgansByDegradation(result?.organs), [result?.organs]);

  useEffect(() => {
    if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
  }, [result]);

  return (
    <div className="min-h-screen flex flex-col">
      <DashboardBackground />
      <AppHeader />

      <main className="flex-1 py-10 px-4 md:px-6 overflow-y-auto relative">
        <div className="max-w-4xl mx-auto">
          <DashboardLayout>
            <div ref={contentRef}>
              <h1 className="text-2xl font-semibold text-[var(--foreground)] mb-1 text-glow-primary">Organs</h1>
              <p className="text-[var(--color-muted)] mb-10">Organ health and risk. Shown by risk level (highest first).</p>
              <div className="space-y-8">
                {organOrder.map((organId) => (
                  <OrganSection key={organId} organId={organId} organData={result?.organs?.[organId]} />
                ))}
              </div>
            </div>
          </DashboardLayout>
        </div>
      </main>

      <footer className="h-12 flex items-center justify-center border-t border-white/10">
        <span className="text-xs text-[var(--color-muted)]">VitalTwin · Healthcare forensics</span>
      </footer>
    </div>
  );
}
