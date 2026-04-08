"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState, useMemo } from "react";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import AppHeader from "../../components/layout/AppHeader";
import DashboardBackground from "../../components/ui/DashboardBackground";
import DashboardLayout from "../../components/results/DashboardLayout";
import BiologicalAgeCard from "../../components/results/BiologicalAgeCard";
import FutureSelfTimeline from "../../components/results/FutureSelfTimeline";

const BodyModelView = dynamic(() => import("../../components/BodyModelView"), { ssr: false });

function getInterpolatedTimelinePoint(timeline, year) {
  if (!timeline?.length || year <= 0) return timeline?.[0] ?? null;
  const sorted = [...timeline].sort((a, b) => a.year - b.year);
  if (year >= sorted[sorted.length - 1].year) return sorted[sorted.length - 1];
  let prev = sorted[0];
  let next = sorted.find((t) => t.year >= year) ?? sorted[sorted.length - 1];
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i].year <= year && sorted[i + 1].year >= year) {
      prev = sorted[i];
      next = sorted[i + 1];
      break;
    }
  }
  const t = prev.year === next.year ? 1 : (year - prev.year) / (next.year - prev.year);
  return {
    year,
    label: year <= 0 ? "Today" : `${Math.round(year)} year${Math.round(year) !== 1 ? "s" : ""} ahead`,
    vitality_score: Math.round(prev.vitality_score + t * (next.vitality_score - prev.vitality_score)),
    biological_age: Math.round(prev.biological_age + t * (next.biological_age - prev.biological_age)),
    changes: next.changes ?? prev.changes ?? [],
    visual_cues: next.visual_cues ?? prev.visual_cues ?? [],
  };
}

function getPreviewBiologicalAge(reportBio, interpolated, yearAhead) {
  if (!reportBio) return reportBio;
  if (yearAhead <= 0) return reportBio;
  if (!interpolated) return reportBio;
  const real_age = reportBio.real_age;
  const biological_age = interpolated.biological_age;
  const age_gap = biological_age - real_age;
  let gap_level = "GREEN";
  if (age_gap > 10) gap_level = "RED";
  else if (age_gap > 5) gap_level = "YELLOW";
  return {
    real_age,
    biological_age,
    age_gap,
    gap_level,
    message: yearAhead <= 0 ? reportBio.message : `${yearAhead.toFixed(1)} years ahead — preview`,
    factors: interpolated.changes?.length ? interpolated.changes.slice(0, 3) : reportBio.factors?.slice(0, 3) ?? [],
  };
}

export default function BodyAgeingPage() {
  const result = useStore((s) => s.result);
  const profile = useStore((s) => s.profile);
  const contentRef = useRef(null);
  const gender = profile?.gender || "";
  const [ageingLevel, setAgeingLevel] = useState(0);

  const yearAhead = ageingLevel * 10;
  const timeline = result?.future_self?.timeline ?? [];
  const interpolated = useMemo(() => getInterpolatedTimelinePoint(timeline, yearAhead), [timeline, yearAhead]);
  const previewBiologicalAge = useMemo(() => getPreviewBiologicalAge(result?.biological_age, interpolated, yearAhead), [result?.biological_age, interpolated, yearAhead]);

  const handleTimelineYearSelect = (year) => setAgeingLevel(year / 10);

  useEffect(() => {
    if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
  }, [result]);

  return (
    <div className="min-h-screen bg-(--color-bg) flex flex-col">
      <DashboardBackground />
      <AppHeader />

      <main className="flex-1 py-8 px-4 md:px-6">
        <div className="max-w-6xl mx-auto">
          <DashboardLayout>
            <div ref={contentRef}>

              {/* Page header */}
              <div className="mb-7">
                <h1 className="text-2xl font-bold text-slate-900 mb-1.5">Body Ageing</h1>
                <p className="text-(--color-muted) text-sm">See how your biological age compares to your real age, and preview how your body changes over time.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6">

                {/* Left: 3D Model + slider */}
                <div className="flex flex-col gap-4">
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden" style={{ height: "420px" }}>
                    <BodyModelView gender={gender} ageingLevel={ageingLevel} className="w-full h-full" showScanRing />
                  </div>

                  {/* Slider card */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-slate-800">Years ahead</p>
                      <span className="text-xl font-bold text-(--color-primary)">{yearAhead.toFixed(1)}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={ageingLevel * 100}
                      onChange={(e) => setAgeingLevel(Number(e.target.value) / 100)}
                      className="w-full h-2 rounded-full appearance-none bg-slate-100 accent-(--color-primary) cursor-pointer"
                      aria-label="Preview years ahead"
                    />
                    <div className="flex justify-between text-xs text-(--color-muted) mt-1.5">
                      <span>Today</span>
                      <span>10 years</span>
                    </div>
                    {yearAhead > 0 && (
                      <p className="text-xs text-(--color-muted) mt-2 bg-slate-50 rounded-lg px-3 py-2 border border-slate-100">
                        Previewing body state at {yearAhead.toFixed(1)} years ahead
                      </p>
                    )}
                  </div>
                </div>

                {/* Right: Bio age + timeline */}
                <div className="flex flex-col gap-5">
                  <BiologicalAgeCard biological_age={previewBiologicalAge} />
                  <FutureSelfTimeline
                    future_self={result?.future_self}
                    sliderYear={yearAhead}
                    onYearSelect={handleTimelineYearSelect}
                  />
                </div>
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
