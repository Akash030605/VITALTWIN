"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState } from "react";
import { gsap } from "gsap";
import { useStore } from "../store/useStore";
import HeroWithModel from "../components/landing/HeroWithModel";
import ProfileForm from "../components/landing/ProfileForm";
import HealthDataImport from "../components/landing/HealthDataImport";
import DashboardLayout from "../components/results/DashboardLayout";
import StressHeatmap from "../components/results/StressHeatmap";
import ReportBodyAgeingSection from "../components/results/ReportBodyAgeingSection";
import ReportOrgansSection from "../components/results/ReportOrgansSection";
import ReportRecommendationsSection from "../components/results/ReportRecommendationsSection";
import AppHeader from "../components/layout/AppHeader";
import DashboardBackground from "../components/ui/DashboardBackground";
import AnimatedCounter from "../components/ui/AnimatedCounter";
import OrgansOverview from "../components/results/OrgansOverview";
import TwinChatPanel from "../components/results/TwinChatPanel";
import PdfExportButton from "../components/results/PdfExportButton";
import ShareCardButton from "../components/results/ShareCardButton";
import ProfileSummary from "../components/results/ProfileSummary";

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
  const input = useStore((s) => s.input);
  const clearAll = useStore((s) => s.clearAll);
  const setProfile = useStore((s) => s.setProfile);
  const setInput = useStore((s) => s.setInput);

  const handleHealthImport = (profileFields, inputFields) => {
    Object.entries(profileFields).forEach(([k, v]) => setProfile(k, v));
    Object.entries(inputFields).forEach(([k, v]) => setInput(k, v));
  };

  const [copyStatus, setCopyStatus] = useState(null);
  const [mounted, setMounted] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const pageRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (result && contentRef.current) {
      gsap.fromTo(contentRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
    }
  }, [result]);

  const vitalScore = result?.vital_score?.current ?? result?.overall_health_score;
  const gauge = result?.vital_score?.gauge;
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

  const hasReport = mounted && result && typeof result === "object" && (result.vital_score != null || result.overall_health_score != null);

  // Calculate bio age for display
  const bio = result?.biological_age;
  const bioAge = typeof bio === "object" ? bio?.biological_age : bio;
  const bmi = (profile?.height && profile?.weight)
    ? (Number(profile.weight) / Math.pow(Number(profile.height) / 100, 2)).toFixed(1)
    : null;

  return (
    <div ref={pageRef} className="min-h-screen flex flex-col bg-(--color-bg)">
      <AppHeader />

      {hasReport ? (
        <>
          <DashboardBackground />

          {/* Patient summary bar */}
          <div className="bg-white border-b border-slate-200 px-4 md:px-6 py-3">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
              <ProfileSummary profile={profile} />
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={handleCopySummary}
                  className="text-xs text-(--color-muted) hover:text-foreground font-medium px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
                >
                  {copyStatus ?? "Copy summary"}
                </button>
                <PdfExportButton />
                <ShareCardButton />
                <button
                  type="button"
                  onClick={() => clearAll()}
                  className="text-xs text-(--color-muted) hover:text-red-600 font-medium px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-red-50 hover:border-red-200 transition-colors"
                >
                  Clear report
                </button>
              </div>
            </div>
          </div>

          <main className="flex-1 py-6 px-4 md:px-6 relative w-full">
            <div ref={contentRef} className="max-w-7xl mx-auto space-y-6">
              <DashboardLayout>

                {/* Hero row: 3D model + vital metrics */}
                <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-5">

                  {/* Left: 3D body model */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-120">
                    <div className="flex-1">
                      <DashboardMaleBodyView className="w-full h-full min-h-100" showScanRing />
                    </div>
                    <div className="px-4 py-3 border-t border-slate-100 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-(--color-primary) animate-pulse" aria-hidden />
                      <p className="text-xs text-(--color-muted) font-medium">3D Body Model · {profile?.name ?? "Your Twin"}</p>
                    </div>
                  </div>

                  {/* Right: metrics grid */}
                  <div className="flex flex-col gap-5">

                    {/* Vital Score */}
                    {vitalScore != null && (
                      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                        <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider mb-3">Vital Score</p>
                        <div className="flex items-baseline gap-2 mb-3">
                          <span className="text-5xl font-bold text-slate-900">
                            <AnimatedCounter value={vitalScore} duration={1400} />
                          </span>
                          <span className="text-lg text-(--color-muted) font-normal">/ 100</span>
                          {result.vital_score?.category && (
                            <span className="ml-2 text-sm font-semibold text-(--color-primary) bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                              {result.vital_score.category}
                            </span>
                          )}
                        </div>
                        {gauge?.segments?.length > 0 && (
                          <div className="h-3 w-full rounded-full overflow-hidden flex mb-3 bg-slate-100 gap-px">
                            {gauge.segments.map((seg, i) => (
                              <div
                                key={i}
                                className="h-full transition-opacity rounded-sm"
                                style={{
                                  width: `${seg.to - seg.from}%`,
                                  backgroundColor: seg.color,
                                  opacity: vitalScore >= seg.from && vitalScore <= seg.to ? 1 : 0.25,
                                }}
                              />
                            ))}
                          </div>
                        )}
                        {result.vital_score?.message && (
                          <p className="text-sm text-(--color-muted)">{result.vital_score.message}</p>
                        )}
                      </div>
                    )}

                    {/* Organs overview */}
                    {result.organs && (
                      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex-1">
                        <OrgansOverview organs={result.organs} />
                      </div>
                    )}
                  </div>
                </div>

                {/* Stress heatmap row */}
                {result.body_stress && (
                  <div>
                    <StressHeatmap body_stress={result.body_stress} />
                  </div>
                )}

                {/* Detail sections */}
                <ReportBodyAgeingSection result={result} gender={gender} />
                <ReportOrgansSection result={result} />
                <ReportRecommendationsSection result={result} />

              </DashboardLayout>
            </div>
          </main>

          {/* Floating chat button */}
          <button
            type="button"
            onClick={() => setChatOpen((o) => !o)}
            className="fixed bottom-6 right-5 z-50 flex items-center gap-2 bg-(--color-primary) hover:bg-(--color-primary-deep) text-white font-semibold text-sm px-4 py-2.5 rounded-full shadow-lg shadow-emerald-900/20 transition-all focus:outline-none focus:ring-2 focus:ring-(--color-primary)/50"
            aria-label={chatOpen ? "Close Twin Chat" : "Chat with your Twin"}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
            {chatOpen ? "Close" : "Ask your Twin"}
          </button>

          <TwinChatPanel profile={profile} input={input} result={result} isOpen={chatOpen} onClose={() => setChatOpen(false)} />
        </>
      ) : (
        /* LANDING */
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_440px] overflow-hidden min-h-[calc(100vh-56px)]">

          {/* Left: Hero with 3D model */}
          <div className="relative bg-linear-to-br from-emerald-50 via-white to-teal-50 overflow-hidden min-h-[55vh] lg:min-h-0">
            <HeroWithModel />

            {/* Hero text overlay at bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-8 md:p-12 bg-linear-to-t from-white/90 to-transparent">
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-3 leading-tight">
                Know your health,<br />
                <span className="text-(--color-primary)">before it surprises you.</span>
              </h1>
              <p className="text-base text-(--color-muted) mb-5 max-w-md">
                AI-powered organ health analysis, biological age prediction, and personalised lifestyle recommendations.
              </p>
              <div className="flex flex-wrap gap-4">
                {["AI-powered analysis", "Evidence-based predictions", "5 organ health models"].map((feat) => (
                  <div key={feat} className="flex items-center gap-1.5 text-sm text-slate-700">
                    <div className="w-4 h-4 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                      <svg className="w-2.5 h-2.5 text-(--color-primary)" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    {feat}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Form panel */}
          <div className="bg-white border-l border-slate-200 flex flex-col overflow-y-auto">
            <div className="flex-1 flex flex-col justify-center p-8 md:p-10">
              <div className="mb-6">
                <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-xs font-semibold text-(--color-primary) uppercase tracking-wider px-3 py-1.5 rounded-full mb-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-(--color-primary)" aria-hidden />
                  Step 1 of 2
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Create your profile</h2>
                <p className="text-sm text-(--color-muted)">Enter your basic information to get a personalised health analysis.</p>
              </div>
              <ProfileForm />
              <div className="mt-4">
                <HealthDataImport onImport={handleHealthImport} />
              </div>
            </div>
            <div className="px-8 md:px-10 py-4 border-t border-slate-100">
              <p className="text-xs text-(--color-muted) text-center">Your data is used only for analysis and is never shared.</p>
            </div>
          </div>
        </main>
      )}
    </div>
  );
}
