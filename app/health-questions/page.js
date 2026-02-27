"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import { submitReport } from "../../lib/api";
import AppHeader from "../../components/layout/AppHeader";
import HeartModelView from "../../components/HeartModelView";

const DigitalTwinLoadingScene = dynamic(() => import("../../components/DigitalTwinLoadingScene"), { ssr: false });

const TAGLINES = [
  "[ Heart model loaded ]",
  "Questionnaire active.",
  "Answers refine your twin analysis.",
];

const HEALTH_QUESTIONS = [
  { id: "smoking", label: "Smoking status", type: "select", options: ["", "Never", "Occasional", "Daily"], placeholder: "Select" },
  { id: "alcohol", label: "Alcohol consumption", type: "select", options: ["", "Never", "Daily", "Occasional", "Weekly"], placeholder: "Select" },
  { id: "sleep", label: "Sleep (hours per night)", type: "select", options: ["", "4", "5", "6", "7", "8", "9", "10"], placeholder: "Select hours", optionLabels: { "4": "4 hours", "5": "5 hours", "6": "6 hours", "7": "7 hours", "8": "8 hours", "9": "9 hours", "10": "10 hours" } },
  { id: "stress", label: "Stress level", type: "select", options: ["", "Low", "Medium", "High"], placeholder: "Select" },
];

function MedicalConditionsField({ conditions, onChange }) {
  const [newCondition, setNewCondition] = useState("");
  const add = () => {
    const trimmed = (newCondition || "").trim();
    if (!trimmed) return;
    if (conditions.includes(trimmed)) return;
    onChange([...conditions, trimmed]);
    setNewCondition("");
  };
  const remove = (index) => onChange(conditions.filter((_, i) => i !== index));
  return (
    <div data-field className="space-y-2 pt-2 border-t border-white/10">
      <label className="block text-sm font-medium text-[var(--foreground)]">Medical conditions (diseases)</label>
      <p className="text-xs text-[var(--color-muted)] mb-1">Add known conditions or diseases. Sent as an array to the backend.</p>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="e.g. Hypertension, Type 2 diabetes"
          value={newCondition}
          onChange={(e) => setNewCondition(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-primary)]/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
        />
        <button type="button" onClick={add} className="shrink-0 rounded-lg border border-[var(--color-primary)]/60 bg-[var(--color-primary)]/10 px-4 py-3 text-sm font-medium text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50">
          Add
        </button>
      </div>
      {conditions.length > 0 && (
        <ul className="flex flex-wrap gap-2 mt-2">
          {conditions.map((item, i) => (
            <li key={`${item}-${i}`} className="inline-flex items-center gap-1.5 rounded-lg bg-white/10 border border-white/10 pl-3 pr-1 py-1.5 text-sm">
              <span>{item}</span>
              <button type="button" onClick={() => remove(i)} className="p-1 rounded text-[var(--color-muted)] hover:text-[var(--foreground)] focus:outline-none" aria-label={`Remove ${item}`}>×</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function HealthQuestionsPage() {
  const router = useRouter();
  const [showLoadingScene, setShowLoadingScene] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const heroRef = useRef(null);
  const formRef = useRef(null);
  const { input, setInput, profile, setResult } = useStore();

  const handleGenerateReport = (e) => {
    e?.preventDefault?.();
    setSubmitError(null);
    setShowLoadingScene(true);
    submitReport(profile, input)
      .then((res) => {
        if (res?.ok && res?.data) setResult(res.data);
      })
      .catch((err) => {
        setShowLoadingScene(false);
        setSubmitError(err?.message || "Something went wrong. Please try again.");
      });
  };

  const handleLoadingComplete = () => {
    setShowLoadingScene(false);
    router.push("/");
  };

  useEffect(() => {
    if (heroRef.current) {
      gsap.fromTo(heroRef.current, { opacity: 0, scale: 0.98 }, { opacity: 1, scale: 1, duration: 1, ease: "power3.out" });
    }
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
    <div className="min-h-screen relative flex flex-col">
      <AppHeader />

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-0 w-full max-w-6xl mx-auto min-h-0 py-8 px-4 md:px-8">
        <div ref={heroRef} className="min-h-[50vh] lg:min-h-[calc(100vh-8rem)] lg:border-r border-[var(--color-primary)]/20 bg-gradient-to-br from-[var(--color-surface)]/30 to-transparent relative overflow-hidden">
          <HeartModelView fullHeight className="w-full h-full min-h-0" />
          <div className="absolute inset-0 pointer-events-none scan-line opacity-25" aria-hidden />
          <div className="absolute inset-0 cinematic-spotlight" aria-hidden />
          <div className="absolute bottom-6 left-6 space-y-1 font-heading text-[10px] text-[var(--color-primary)]/90 tracking-wide">
            <p className="text-[var(--color-primary)]">{TAGLINES[0]}</p>
            <p className="text-[var(--color-primary)]/80">{TAGLINES[1]}</p>
            <p className="text-[var(--color-muted)] text-[11px]">{TAGLINES[2]}</p>
          </div>
        </div>
        <div ref={formRef} className="flex flex-col justify-center py-8 lg:py-12 lg:px-12">
          <div className="max-w-md">
            <Link
              href="/"
              className="text-sm text-[var(--color-muted)] hover:text-[var(--color-primary)] transition-colors inline-flex items-center gap-1.5 mb-6"
              aria-label="Back to profile"
            >
              ← Back to profile
            </Link>
            <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-1">Step 2 of 2</p>
            <h2 className="font-heading text-xl font-semibold text-[var(--foreground)] mb-2">Your body decoded</h2>
            <p className="font-heading text-sm text-[var(--color-muted)] mb-6">
              Lifestyle & conditions. Enter your habits and known conditions so we can refine your digital twin analysis.
            </p>
            <form className="space-y-4" onSubmit={handleGenerateReport}>
              {HEALTH_QUESTIONS.map(({ id, label, type = "text", placeholder, options, optionLabels }) => (
                <div key={id} data-field className="space-y-2">
                  <label htmlFor={id} className="block text-sm font-medium text-[var(--foreground)]">
                    {label}
                  </label>
                  {type === "select" ? (
                    <select
                      id={id}
                      value={input[id] ?? ""}
                      onChange={(e) => setInput(id, e.target.value)}
                      className="form-select w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--foreground)] focus:border-[var(--color-primary)]/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
                    >
                      <option value="">{placeholder}</option>
                      {options.filter(Boolean).map((opt) => (
                        <option key={opt} value={opt}>{optionLabels?.[opt] ?? opt}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id={id}
                      type="text"
                      placeholder={placeholder}
                      value={input[id] ?? ""}
                      onChange={(e) => setInput(id, e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-primary)]/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
                    />
                  )}
                </div>
              ))}

              <MedicalConditionsField conditions={Array.isArray(input.medical_conditions) ? input.medical_conditions : []} onChange={(arr) => setInput("medical_conditions", arr)} />

              {submitError && (
                <div className="rounded-lg bg-red-950/40 border border-red-500/40 px-4 py-3 text-sm text-red-200" role="alert">
                  {submitError}
                </div>
              )}
              <div className="pt-4">
                <button
                  type="submit"
                  data-cta
                  disabled={showLoadingScene}
                  aria-label="Generate report"
                  className="w-full flex items-center justify-center rounded-lg border border-[var(--color-primary)]/60 bg-[var(--color-primary)]/10 px-8 py-4 text-sm font-medium text-[var(--color-primary)] transition-all hover:bg-[var(--color-primary)]/20 hover:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] disabled:opacity-50 disabled:pointer-events-none"
                >
                  {showLoadingScene ? "Generating…" : "Generate report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>

      <footer className="h-12 flex items-center justify-center border-t border-white/10">
        <span className="text-xs text-[var(--color-muted)]">VitalTwin · Healthcare forensics</span>
      </footer>

      {showLoadingScene && (
        <DigitalTwinLoadingScene onComplete={handleLoadingComplete} />
      )}
    </div>
  );
}