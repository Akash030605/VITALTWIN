"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import { submitReport } from "../../lib/api";
import { saveSubmission } from "../../lib/profileApi";
import AppHeader from "../../components/layout/AppHeader";
import HeartModelView from "../../components/HeartModelView";

const DigitalTwinLoadingScene = dynamic(() => import("../../components/DigitalTwinLoadingScene"), { ssr: false });

const TAGLINES = [
  "[ Heart model loaded ]",
  "Questionnaire active.",
  "Answers refine your twin analysis.",
];

const HEALTH_QUESTIONS = [
  { id: "smoking", label: "Smoking status", type: "select", options: ["", "Never", "Occasional", "Daily"], placeholder: "Select", required: true },
  { id: "alcohol", label: "Alcohol consumption", type: "select", options: ["", "Never", "Daily", "Occasional", "Weekly"], placeholder: "Select", required: true },
  { id: "sleep", label: "Sleep (hours per night)", type: "select", options: ["", "4", "5", "6", "7", "8", "9", "10"], placeholder: "Select hours", optionLabels: { "4": "4 hours", "5": "5 hours", "6": "6 hours", "7": "7 hours", "8": "8 hours", "9": "9 hours", "10": "10 hours" }, required: true },
  { id: "stress", label: "Stress level", type: "select", options: ["", "Low", "Medium", "High"], placeholder: "Select", required: true },
];

const MEDICAL_CONDITIONS = [
  "Coronary Artery Disease - Mild", "Coronary Artery Disease - Moderate", "Coronary Artery Disease - Severe",
  "Heart Failure Stage A", "Heart Failure Stage B", "Heart Failure Stage C", "Heart Failure Stage D",
  "Hypertension Stage 1", "Hypertension Stage 2", "Hypertension Crisis", "Atrial Fibrillation", "Bradycardia", "Tachycardia", "Ventricular Tachycardia",
  "Aortic Stenosis - Mild", "Aortic Stenosis - Moderate", "Aortic Stenosis - Severe", "Mitral Regurgitation",
  "Heart Attack - STEMI", "Heart Attack - NSTEMI", "Dilated Cardiomyopathy", "Hypertrophic Cardiomyopathy",
  "Peripheral Artery Disease", "Congenital Heart Disease", "High Cholesterol - Borderline", "High Cholesterol - High", "High Cholesterol - Very High",
  "Fatty Liver Grade 1", "Fatty Liver Grade 2", "Fatty Liver Grade 3", "NASH", "Cirrhosis - Compensated", "Cirrhosis - Decompensated",
  "Hepatitis B - Acute", "Hepatitis B - Chronic", "Hepatitis B - Inactive", "Hepatitis C - Acute", "Hepatitis C - Chronic",
  "Alcoholic Liver Disease", "Alcoholic Hepatitis", "Gilbert Syndrome", "Autoimmune Hepatitis", "Primary Biliary Cholangitis", "Hemochromatosis", "Wilson Disease",
  "CKD Stage 1", "CKD Stage 2", "CKD Stage 3", "CKD Stage 4", "CKD Stage 5", "Acute Kidney Failure", "Chronic Kidney Failure", "Kidney Stones", "Recurrent UTIs",
  "Glomerulonephritis - Acute", "Glomerulonephritis - Chronic", "Polycystic Kidney Disease", "Diabetic Nephropathy", "Hypertensive Nephropathy",
  "COPD Gold Stage 1", "COPD Gold Stage 2", "COPD Gold Stage 3", "COPD Gold Stage 4",
  "Asthma - Intermittent", "Asthma - Mild Persistent", "Asthma - Moderate Persistent", "Asthma - Severe Persistent",
  "Pneumonia", "Pulmonary Fibrosis", "Lung Cancer Stage 1", "Lung Cancer Stage 2", "Lung Cancer Stage 3", "Lung Cancer Stage 4",
  "Sleep Apnea - Mild", "Sleep Apnea - Moderate", "Sleep Apnea - Severe", "Tuberculosis - Active", "Tuberculosis - Latent",
  "Pulmonary Embolism", "Chronic Bronchitis", "Emphysema",
  "Stroke - Ischemic", "Stroke - Hemorrhagic", "TIA", "Alzheimer's - Early Stage", "Alzheimer's - Moderate Stage", "Alzheimer's - Late Stage",
  "Parkinson's Disease", "Migraine - Chronic", "Migraine - With Aura", "Epilepsy - Generalized", "Epilepsy - Focal",
  "Multiple Sclerosis - Relapsing", "Multiple Sclerosis - Progressive", "Anxiety Disorder - Mild", "Anxiety Disorder - Moderate", "Anxiety Disorder - Severe",
  "Major Depression - Mild", "Major Depression - Moderate", "Major Depression - Severe", "Obstructive Sleep Apnea", "TBI - Mild", "TBI - Moderate", "TBI - Severe",
  "Type 1 Diabetes", "Type 2 Diabetes", "Prediabetes", "Gestational Diabetes", "Metabolic Syndrome",
  "Obesity Class 1", "Obesity Class 2", "Obesity Class 3", "Hypothyroidism", "Hyperthyroidism", "Hashimoto's Thyroiditis", "Graves Disease",
  "Autoimmune Disease", "Rheumatoid Arthritis", "Lupus", "Cancer - In Remission", "Cancer - Active Treatment",
  "Chronic Pain Syndrome", "Fibromyalgia", "Pregnant", "Postpartum", "Menopause", "PCOS",
];

function MedicalConditionsField({ conditions, onChange }) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  const filtered = useMemo(() => {
    const q = (search || "").trim().toLowerCase();
    if (!q) return MEDICAL_CONDITIONS;
    return MEDICAL_CONDITIONS.filter((c) => c.toLowerCase().includes(q));
  }, [search]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggle = (condition) => {
    if (conditions.includes(condition)) {
      onChange(conditions.filter((c) => c !== condition));
    } else {
      onChange([...conditions, condition]);
    }
  };

  return (
    <div data-field className={`space-y-2 pt-2 border-t border-white/10 ${open ? "relative z-[50]" : ""}`} ref={containerRef}>
      <label className="block text-sm font-medium text-[var(--foreground)]">Medical conditions (diseases)</label>
      <p className="text-xs text-[var(--color-muted)] mb-1">Search and select known conditions. Optional.</p>
      <div className="relative">
        <input
          type="text"
          placeholder="Search conditions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onFocus={() => setOpen(true)}
          className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-primary)]/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-autocomplete="list"
        />
        {open && (
          <ul
            className="absolute z-[100] mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-white/10 bg-[var(--color-bg)] shadow-xl py-1"
            role="listbox"
            aria-label="Medical conditions"
          >
            {filtered.length === 0 ? (
              <li className="px-4 py-3 text-sm text-[var(--color-muted)]">No matches</li>
            ) : (
              filtered.map((condition) => {
                const selected = conditions.includes(condition);
                return (
                  <li
                    key={condition}
                    role="option"
                    aria-selected={selected}
                    onClick={() => toggle(condition)}
                    className={`px-4 py-2.5 text-sm cursor-pointer select-none ${selected ? "bg-[var(--color-primary)]/20 text-[var(--color-primary)]" : "text-[var(--foreground)] hover:bg-white/10"}`}
                  >
                    {condition}{selected ? " ✓" : ""}
                  </li>
                );
              })
            )}
          </ul>
        )}
      </div>
      {conditions.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {conditions.map((item) => (
            <span
              key={item}
              className="inline-flex items-center gap-1.5 rounded-lg bg-white/10 border border-white/10 pl-3 pr-1 py-1.5 text-sm"
            >
              {item}
              <button type="button" onClick={() => toggle(item)} className="p-1 rounded text-[var(--color-muted)] hover:text-[var(--foreground)] focus:outline-none" aria-label={`Remove ${item}`}>×</button>
            </span>
          ))}
        </div>
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
  const { input, setInput, profile, setResult, clearResult } = useStore();

  // Send profile + input to backend as soon as user lands on step 2 (so data is persisted even before "Generate report").
  useEffect(() => {
    const hasProfile = profile && typeof profile === "object" && Object.keys(profile).some((k) => profile[k] != null && profile[k] !== "");
    if (!hasProfile) return;
    saveSubmission(profile, input).catch(() => {});
  }, []);

  const requiredHealthFields = ["smoking", "alcohol", "sleep", "stress"];
  const validateHealthInput = () => {
    const missing = requiredHealthFields.filter((id) => {
      const v = input[id];
      return v == null || String(v).trim() === "";
    });
    return missing;
  };

  const handleGenerateReport = (e) => {
    e?.preventDefault?.();
    setSubmitError(null);
    const missing = validateHealthInput();
    if (missing.length > 0) {
      setSubmitError("Please fill all fields: " + missing.map((id) => id.charAt(0).toUpperCase() + id.slice(1)).join(", ") + ".");
      return;
    }
    clearResult(); // Dashboard only shows after we receive the API response; clear any previous report.
    setShowLoadingScene(true);
    // Send form data to both: store endpoint (profile/submissions) and LLM endpoint (report).
    Promise.allSettled([
      saveSubmission(profile, input),
      submitReport(profile, input),
    ])
      .then(([storeResult, reportResult]) => {
        const reportRes = reportResult.status === "fulfilled" ? reportResult.value : null;
        const reportData = reportRes?.data;
        const hasValidReport = reportData && typeof reportData === "object" && (reportData.vital_score != null || reportData.overall_health_score != null);
        if (reportRes?.ok && hasValidReport) {
          setResult(reportData);
          setShowLoadingScene(false);
          router.push("/");
        } else {
          setShowLoadingScene(false);
          const err = reportResult.status === "rejected" ? reportResult.reason : null;
          setSubmitError(err?.message || "No report data returned. Please try again.");
        }
      });
  };

  /** Animation end — do not hide overlay or navigate; dashboard loads only when the LLM/API response arrives. */
  const handleLoadingComplete = () => {};

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
              {HEALTH_QUESTIONS.map(({ id, label, type = "text", placeholder, options, optionLabels, required }) => (
                <div key={id} data-field className="space-y-2">
                  <label htmlFor={id} className="block text-sm font-medium text-[var(--foreground)]">
                    {label}{required ? " *" : ""}
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