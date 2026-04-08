"use client";

import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import AppHeader from "../../components/layout/AppHeader";
import DashboardBackground from "../../components/ui/DashboardBackground";
import DashboardLayout from "../../components/results/DashboardLayout";
import PriorityRecommendations from "../../components/results/PriorityRecommendations";
import WhatIfPanel from "../../components/results/WhatIfPanel";
import WellnessScoreCard from "../../components/results/WellnessScoreCard";

export default function RecommendationsPage() {
  const result = useStore((s) => s.result);
  const contentRef = useRef(null);

  useEffect(() => {
    if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
  }, [result]);

  const hasPriority = result?.priority_recommendations?.length > 0;

  return (
    <div className="min-h-screen bg-(--color-bg) flex flex-col">
      <DashboardBackground />
      <AppHeader />

      <main className="flex-1 py-8 px-4 md:px-6">
        <div className="max-w-3xl mx-auto">
          <DashboardLayout>
            <div ref={contentRef} className="space-y-8 pb-16">

              {/* Page header */}
              <div>
                <h1 className="text-2xl font-bold text-slate-900 mb-1.5">Recommendations</h1>
                <p className="text-(--color-muted) text-sm">Personalised actions to improve your health, and scenarios showing what changes could achieve.</p>
              </div>

              {/* Priority actions */}
              {hasPriority && (
                <section aria-labelledby="priority-heading">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-5 h-5 rounded-md bg-(--color-primary) flex items-center justify-center shrink-0">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd"/>
                      </svg>
                    </div>
                    <h2 id="priority-heading" className="text-sm font-bold text-slate-900">Priority actions</h2>
                  </div>
                  <PriorityRecommendations priority_recommendations={result?.priority_recommendations} />
                </section>
              )}

              {/* What-if scenarios */}
              <section aria-labelledby="whatif-heading">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-5 h-5 rounded-md bg-emerald-100 flex items-center justify-center shrink-0">
                    <svg className="w-3 h-3 text-(--color-primary)" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                    </svg>
                  </div>
                  <h2 id="whatif-heading" className="text-sm font-bold text-slate-900">What-if scenarios</h2>
                </div>
                <WhatIfPanel />
              </section>

              {/* Wellness & risk profile */}
              {result && (
                <section aria-labelledby="wellness-heading">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-5 h-5 rounded-md bg-slate-100 flex items-center justify-center shrink-0">
                      <svg className="w-3 h-3 text-(--color-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                      </svg>
                    </div>
                    <h2 id="wellness-heading" className="text-sm font-bold text-slate-900">Wellness &amp; risk profile</h2>
                  </div>
                  <WellnessScoreCard result={result} />
                </section>
              )}

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
