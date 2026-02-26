"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";

const HeartModelView = dynamic(() => import("../../components/HeartModelView"), { ssr: false });
const DigitalTwinLoadingScene = dynamic(() => import("../../components/DigitalTwinLoadingScene"), { ssr: false });

const HEALTH_QUESTIONS = [
  { id: "smoking", label: "Smoking status", type: "select", options: ["", "Never", "Occasional", "Regular"], placeholder: "Select" },
  { id: "alcohol", label: "Alcohol consumption", type: "select", options: ["", "None", "Moderate", "Heavy"], placeholder: "Select" },
  { id: "sleep", label: "Sleep quality", type: "select", options: ["", "Poor (<6h)", "Fair (6–7h)", "Good (7–8h)", "Excellent (8h+)"], placeholder: "Select" },
  { id: "stress", label: "Stress level", type: "select", options: ["", "Low", "Moderate", "High"], placeholder: "Select" },
];

const TAGLINES = [
  "Heart model loaded.",
  "Health questionnaire active.",
  "Your answers refine the analysis.",
];

export default function HealthQuestionsPage() {
  const router = useRouter();
  const [showLoadingScene, setShowLoadingScene] = useState(false);
  const pageRef = useRef(null);
  const modelWrapRef = useRef(null);
  const formRef = useRef(null);
  const { input, setInput } = useStore();

  const handleGenerateReport = (e) => {
    e.preventDefault();
    setShowLoadingScene(true);
  };

  const handleLoadingComplete = () => {
    setShowLoadingScene(false);
    router.push("/results");
  };

  useEffect(() => {
    if (!pageRef.current) return;
    gsap.fromTo(modelWrapRef.current, { opacity: 0, scale: 0.98 }, { opacity: 1, scale: 1, duration: 1, ease: "power3.out" });
    if (formRef.current) {
      gsap.fromTo(formRef.current, { opacity: 0, y: 28 }, { opacity: 1, y: 0, duration: 0.9, delay: 0.25, ease: "power3.out" });
    }
    const fields = formRef.current?.querySelectorAll("[data-field]");
    const btn = formRef.current?.querySelector("[data-cta]");
    if (fields?.length) {
      gsap.fromTo(fields, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, delay: 0.4, ease: "power3.out" });
    }
    if (btn) {
      gsap.fromTo(btn, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.9, ease: "power3.out" });
    }
  }, []);

  return (
    <div ref={pageRef} className="min-h-screen relative flex flex-col">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/40 to-transparent" aria-hidden />

      <header className="sticky top-0 z-20 flex items-center justify-between gap-4 px-4 py-3 md:px-8 md:py-4 border-b border-[var(--color-surface-border)]/40 bg-[var(--color-bg)]/80 backdrop-blur-md">
        <Link
          href="/"
          className="font-heading text-lg md:text-xl font-semibold tracking-tighter text-[var(--foreground)] transition hover:text-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] rounded"
        >
          VitalTwin
        </Link>
        <div className="flex items-center gap-6">
          <span className="hidden sm:inline font-mono text-[10px] md:text-xs text-[var(--color-muted)] tracking-[0.15em] uppercase">
            Digital twin · Healthcare forensics
          </span>
          <span className="font-mono text-xs font-medium uppercase tracking-wider text-[var(--color-primary)]">
            Health assessment
          </span>
        </div>
      </header>

      <main className="relative z-10 flex-1 grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-0 w-full max-w-7xl mx-auto min-h-0">
        <div ref={modelWrapRef} className="min-h-[50vh] lg:min-h-[calc(100vh-4rem)] lg:border-r border-[var(--color-surface-border)]/40 bg-gradient-to-br from-[var(--color-surface)]/20 to-transparent relative overflow-hidden">
          <HeartModelView fullHeight className="w-full h-full min-h-0" />
          <div className="absolute inset-0 pointer-events-none scan-line opacity-25" aria-hidden />
          <div className="absolute inset-0 cinematic-spotlight" aria-hidden />
          <div className="absolute bottom-6 left-6 space-y-1 font-mono text-xs text-[var(--color-primary)]/90 tracking-wide">
            <p className="text-[var(--color-primary)]">{TAGLINES[0]}</p>
            <p className="text-[var(--color-primary)]/80">{TAGLINES[1]}</p>
            <p className="text-[var(--color-muted)] text-[11px]">{TAGLINES[2]}</p>
          </div>
        </div>

        <div ref={formRef} className="flex flex-col justify-center py-8 lg:py-12 lg:px-12 shrink-0 border-t lg:border-t-0 border-[var(--color-surface-border)]/50">
          <div className="max-w-lg space-y-6">
            <div className="space-y-2">
              <h2 className="font-mono text-sm font-medium text-[var(--color-primary)] tracking-[0.1em] uppercase">
                Health Questionnaire
              </h2>
              <p className="text-sm text-[var(--color-muted)] leading-relaxed">
                These answers will refine your digital twin analysis.
              </p>
            </div>
            <form className="space-y-4">
              {HEALTH_QUESTIONS.map(({ id, label, type = "text", placeholder, options }) => (
                <div key={id} data-field className="space-y-2">
                  <label htmlFor={id} className="block font-mono text-xs text-[var(--color-primary)]/90 uppercase tracking-wider">
                    {label}
                  </label>
                  {type === "select" ? (
                    <select
                      id={id}
                      value={input[id] ?? ""}
                      onChange={(e) => setInput(id, e.target.value)}
                      className="select-lab w-full rounded px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:ring-offset-0 focus:ring-offset-[var(--color-bg)]"
                    >
                      <option value="">{placeholder}</option>
                      {options.filter(Boolean).map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id={id}
                      type="text"
                      placeholder={placeholder}
                      value={input[id] ?? ""}
                      onChange={(e) => setInput(id, e.target.value)}
                      className="w-full rounded border border-[var(--color-surface-border)] bg-[var(--color-surface)]/30 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 transition-colors focus:border-[var(--color-primary)]/60 focus:bg-[var(--color-surface)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
                    />
                  )}
                </div>
              ))}

              <div data-field className="space-y-2 pt-2 border-t border-[var(--color-surface-border)]/50">
                <h3 className="font-mono text-xs text-[var(--color-primary)]/90 uppercase tracking-wider">
                  Medical conditions
                </h3>
                <p className="text-xs text-[var(--color-muted)]">
                  Any known conditions, chronic illnesses, or current medications. Leave blank if none.
                </p>
                <textarea
                  id="conditions"
                  placeholder="e.g. Hypertension, Type 2 diabetes, Asthma, Beta-blockers..."
                  value={input.conditions ?? ""}
                  onChange={(e) => setInput("conditions", e.target.value)}
                  rows={3}
                  className="w-full rounded border border-[var(--color-surface-border)] bg-[var(--color-surface)]/30 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 transition-colors focus:border-[var(--color-primary)]/60 focus:bg-[var(--color-surface)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 resize-y min-h-[80px]"
                />
              </div>

              <div className="pt-4">
                <button
                  type="button"
                  onClick={handleGenerateReport}
                  data-cta
                  className="w-full flex items-center justify-center rounded bg-[var(--color-primary)] px-8 py-4 font-mono text-sm font-medium uppercase tracking-wide text-[var(--background)] transition-all hover:bg-[var(--color-primary)]/90 hover:shadow-lg hover:shadow-[var(--color-primary)]/20 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)]"
                >
                  Generate report
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>

      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/25 to-transparent" aria-hidden />

      {showLoadingScene && (
        <DigitalTwinLoadingScene onComplete={handleLoadingComplete} />
      )}
    </div>
  );
}
