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

/** Interpolate timeline data at a given year (0–10). */
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

/** Build biological_age shape for preview at yearAhead (real_age from report). */
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
  const interpolated = useMemo(
    () => getInterpolatedTimelinePoint(timeline, yearAhead),
    [timeline, yearAhead]
  );
  const previewBiologicalAge = useMemo(
    () => getPreviewBiologicalAge(result?.biological_age, interpolated, yearAhead),
    [result?.biological_age, interpolated, yearAhead]
  );

  const handleTimelineYearSelect = (year) => {
    setAgeingLevel(year / 10);
  };

  useEffect(() => {
    if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
  }, [result]);

  return (
    <div className="min-h-screen flex flex-col">
      <DashboardBackground />
      <AppHeader />

      <main className="flex-1 py-10 px-4 md:px-6 overflow-y-auto relative">
        <div className="max-w-5xl mx-auto">
          <DashboardLayout>
            <div ref={contentRef}>
              <h1 className="text-2xl font-semibold text-[var(--foreground)] mb-1 text-glow-primary">Body Ageing</h1>
              <p className="text-[var(--color-muted)] mb-8">How old your body is vs your real age, and how you age over time. Move the slider to preview.</p>

              <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr] gap-8 lg:gap-10">
                <div className="flex flex-col">
                  <div className="rounded-2xl overflow-hidden glass-card glass-card-glow h-[420px] w-full">
                    <BodyModelView gender={gender} ageingLevel={ageingLevel} className="w-full h-full" showScanRing />
                  </div>
                  <div className="mt-4 px-1 rounded-xl glass-card p-4">
                    <label className="block text-sm font-medium text-[var(--foreground)] mb-2">
                      Years ahead: <span className="text-[var(--color-primary)] text-glow-primary">{yearAhead.toFixed(1)}</span>
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={ageingLevel * 100}
                      onChange={(e) => setAgeingLevel(Number(e.target.value) / 100)}
                      className="w-full h-2.5 rounded-full appearance-none bg-white/10 accent-[var(--color-primary)] [&::-webkit-slider-thumb]:shadow-[0_0_12px_rgba(20,184,166,0.5)]"
                      aria-label="Years ahead"
                    />
                    <p className="text-xs text-[var(--color-muted)] mt-1.5">
                      {yearAhead <= 0 ? "Today" : `Preview at ${yearAhead.toFixed(1)} years — model and data update together`}
                    </p>
                  </div>
                </div>

                <div className="space-y-8">
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

      <footer className="h-12 flex items-center justify-center border-t border-white/10">
        <span className="text-xs text-[var(--color-muted)]">VitalTwin · Healthcare forensics</span>
      </footer>
    </div>
  );
}
