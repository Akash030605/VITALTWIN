"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import { gsap } from "gsap";
import { useStore } from "../store/useStore";
import HeroWithModel from "../components/landing/HeroWithModel";
import ProfileForm from "../components/landing/ProfileForm";
import DashboardLayout from "../components/results/DashboardLayout";
import StressHeatmap from "../components/results/StressHeatmap";
import ReportBodyAgeingSection from "../components/results/ReportBodyAgeingSection";
import ReportOrgansSection from "../components/results/ReportOrgansSection";
import ReportRecommendationsSection from "../components/results/ReportRecommendationsSection";
import AppHeader from "../components/layout/AppHeader";
import DashboardBackground from "../components/ui/DashboardBackground";
import AnimatedCounter from "../components/ui/AnimatedCounter";

const BodyModelView = dynamic(() => import("../components/BodyModelView"), { ssr: false });
const DashboardMaleBodyView = dynamic(() => import("../components/DashboardMaleBodyView"), { ssr: false });

function buildReportSummary(result) {
  if (!result) return "";
  const vs = result.vital_score;
  const bio = result.biological_age;
  const lines = [
    "VitalTwin Report Summary",
    `Vital score: ${vs?.current ?? result.overall_health_score ?? "—"} / 100${vs?.category ? ` (${vs.category})` : ""}`,
    vs?.message ? vs.message : "",
    bio ? `Biological age: ${bio.real_age} (real) vs ${bio.biological_age} (biological), gap ${bio.age_gap} years` : "",
    bio?.message ? bio.message : "",
  ];
  if (result.priority_recommendations?.length) {
    lines.push("Priority actions:", ...result.priority_recommendations.map((r) => `- [${r.priority}] ${r.action}`));
  }
  return lines.filter(Boolean).join("\n");
}

export default function HomePage() {
  const result = useStore((s) => s.result);
  const profile = useStore((s) => s.profile);
  const clearAll = useStore((s) => s.clearAll);
  const [copyStatus, setCopyStatus] = useState(null);
  const [mounted, setMounted] = useState(false);
  const pageRef = useRef(null);

  useEffect(() => setMounted(true), []);

  const heroRef = useRef(null);
  const formRef = useRef(null);
  const contentRef = useRef(null);

  const handleHeroReady = () => {
    if (formRef.current) {
      gsap.fromTo(formRef.current, { opacity: 0, y: 32 }, { opacity: 1, y: 0, duration: 1, ease: "power3.out" });
    }
  };

  useEffect(() => {
    if (!pageRef.current) return;
    if (result) {
      if (contentRef.current) gsap.fromTo(contentRef.current, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" });
    } else {
      if (heroRef.current) gsap.fromTo(heroRef.current, { opacity: 0, scale: 0.98 }, { opacity: 1, scale: 1, duration: 1, delay: 0.15, ease: "power2.out" });
    }
  }, [result]);

  const vitalScore = result?.vital_score?.current ?? result?.overall_health_score;
  const gauge = result?.vital_score?.gauge;
  const trend = result?.vital_score?.trend;
  const trendPercent = result?.vital_score?.trend_percent;
  const gender = profile?.gender ?? "";

  const handleCopySummary = async () => {
    const text = buildReportSummary(result);
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("Copied!");
      setTimeout(() => setCopyStatus(null), 2000);
    } catch {
      setCopyStatus("Copy failed");
      setTimeout(() => setCopyStatus(null), 2000);
    }
  };

  // Dashboard only when we have a real report from the API (vital_score or overall_health_score).
  const hasReport = mounted && result && typeof result === "object" && (result.vital_score != null || result.overall_health_score != null);

  return (
    <div ref={pageRef} className="min-h-screen flex flex-col">
      <AppHeader />

      {hasReport ? (
        <>
          <DashboardBackground />
          <main className="flex-1 py-6 px-4 md:px-6 lg:px-8 overflow-y-auto relative w-full">
            <div ref={contentRef} className="w-full">
              {/* First section: left = model, right = Vital Score (top) + Stress Heatmap (bottom) — equal height */}
              <div className="w-full grid grid-cols-1 lg:grid-cols-[minmax(300px,0.42fr)_1fr] gap-6 lg:gap-8 mb-8 min-h-[420px] lg:min-h-[520px] items-stretch">
                {/* Left: Model — full height of section */}
                <div className="min-h-[380px] lg:min-h-0 flex flex-col gap-2">
                  <div className="rounded-2xl overflow-hidden glass-card glass-card-glow flex-1 min-h-[340px]">
                    <DashboardMaleBodyView className="w-full h-full min-h-[340px]" showScanRing />
                  </div>
                  <p className="text-xs font-mono text-[var(--color-primary)]/80 uppercase tracking-wider px-1 shrink-0">Subject · Digital twin</p>
                </div>

                {/* Right: Report title, then Vital Score, then Stress Heatmap — same height as left */}
                <div className="min-w-0 flex flex-col gap-6 min-h-[380px] lg:min-h-0">
                  <div className="shrink-0">
                    <h1 className="text-xl md:text-2xl font-semibold text-[var(--foreground)] mb-1 text-glow-primary">Health Forensic Report</h1>
                    <p className="text-sm text-[var(--color-muted)]">Digital twin analysis. Interactive sections below.</p>
                  </div>
                  {vitalScore != null && (
                    <div className="p-5 rounded-2xl glass-card glass-card-glow hover-lift animate-float-subtle shrink-0">
                      <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-1">Vital score</p>
                      <p className="text-3xl md:text-4xl font-semibold text-[var(--foreground)]">
                        <AnimatedCounter value={vitalScore} duration={1400} />
                        <span className="text-base md:text-lg font-normal text-[var(--color-muted)]"> / 100</span>
                      </p>
                      {gauge?.segments?.length > 0 && (
                        <div className="h-2.5 w-full rounded-full overflow-hidden flex mt-3 bg-white/10 gauge-pulse">
                          {gauge.segments.map((seg, i) => (
                            <div key={i} className="gauge-fill h-full transition-opacity rounded-full" style={{ width: `${seg.to - seg.from}%`, backgroundColor: seg.color, opacity: vitalScore >= seg.from && vitalScore <= seg.to ? 1 : 0.35 }} />
                          ))}
                        </div>
                      )}
                      {trend && (
                        <p className="text-xs text-[var(--color-muted)] mt-2">Trend: {trend}{trendPercent != null ? ` (${trendPercent > 0 ? "+" : ""}${trendPercent.toFixed(1)}%)` : ""}</p>
                      )}
                      {result.vital_score?.message && <p className="text-sm text-[var(--color-muted)] mt-2">{result.vital_score.message}</p>}
                      {result.vital_score?.interpretation && <p className="text-xs text-[var(--color-muted)] mt-1">{result.vital_score.interpretation}</p>}
                    </div>
                  )}
                  {result.body_stress && (
                    <div className="flex-1 min-h-[200px]">
                      <StressHeatmap body_stress={result.body_stress} />
                    </div>
                  )}
                </div>
              </div>

              {/* Rest of report: aligns with first section width */}
              <div className="w-full">
                <DashboardLayout>
                  <ReportBodyAgeingSection result={result} gender={gender} />

                  <ReportOrgansSection result={result} />

                  <ReportRecommendationsSection result={result} />

                  <div className="flex flex-wrap gap-3 items-center mt-auto pt-4 border-t border-white/10">
                    <button type="button" onClick={handleCopySummary} className="text-sm text-[var(--color-primary)] font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 rounded py-1.5 px-2 transition-opacity hover:opacity-90" aria-label="Copy report summary">
                      {copyStatus ?? "Copy report summary"}
                    </button>
                    <button type="button" onClick={() => clearAll()} className="text-sm text-[var(--color-muted)] hover:text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 rounded py-1.5 px-2 transition-colors" aria-label="Clear report">
                      Clear report
                    </button>
                  </div>
                </DashboardLayout>
              </div>
            </div>
          </main>
        </>
      ) : (
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-0 w-full max-w-6xl mx-auto min-h-0 py-8 px-4 md:px-8">
          <div ref={heroRef} className="min-h-[50vh] lg:min-h-[calc(100vh-8rem)] flex flex-col">
            <HeroWithModel onAnimationsReady={handleHeroReady} />
          </div>
          <div ref={formRef} className="flex flex-col justify-center py-8 lg:py-12 lg:px-12">
            <div className="max-w-md">
              <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-1">Step 1 of 2</p>
              <h2 className="font-heading text-xl font-semibold text-[var(--foreground)] mb-2">Your body decoded</h2>
              <p className="font-heading text-sm text-[var(--color-muted)] mb-6">Enter your vitals and baseline data to initialize your digital twin. Then continue to the health assessment.</p>
              <ProfileForm />
            </div>
          </div>
        </main>
      )}

      <footer className="h-12 flex items-center justify-center border-t border-white/10">
        <span className="text-xs text-[var(--color-muted)]">VitalTwin · Healthcare forensics</span>
      </footer>
    </div>
  );
}
