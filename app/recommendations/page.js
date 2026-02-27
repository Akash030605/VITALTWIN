"use client";

import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import AppHeader from "../../components/layout/AppHeader";
import DashboardBackground from "../../components/ui/DashboardBackground";
import DashboardLayout from "../../components/results/DashboardLayout";
import PriorityRecommendations from "../../components/results/PriorityRecommendations";
import WhatIfPanel from "../../components/results/WhatIfPanel";

export default function RecommendationsPage() {
  const result = useStore((s) => s.result);
  const contentRef = useRef(null);

  useEffect(() => {
    if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
  }, [result]);

  return (
    <div className="min-h-screen flex flex-col">
      <DashboardBackground />
      <AppHeader />

      <main className="flex-1 py-8 md:py-10 px-4 md:px-6 overflow-y-auto relative">
        <div className="max-w-2xl mx-auto w-full">
          <DashboardLayout>
            <div ref={contentRef} className="pb-24">
              <header className="mb-8">
                <h1 className="text-2xl md:text-3xl font-semibold text-[var(--foreground)] mb-2 text-glow-primary">Recommendations</h1>
                <p className="text-[var(--color-muted)] text-sm md:text-base">What to do next and how changes could improve your health.</p>
              </header>

              <section className="mb-10" aria-labelledby="priority-heading">
                <h2 id="priority-heading" className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-4">Priority actions</h2>
                <PriorityRecommendations priority_recommendations={result?.priority_recommendations} />
              </section>

              <section aria-labelledby="whatif-heading">
                <h2 id="whatif-heading" className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-4">What if</h2>
                <WhatIfPanel what_if_simulations={result?.what_if_simulations} />
              </section>
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
