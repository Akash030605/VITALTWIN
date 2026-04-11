"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import { useStore } from "../../store/useStore";
import { submitReport } from "../../lib/api";
import { saveSubmission } from "../../lib/profileApi";
import AppHeader from "../../components/layout/AppHeader";
import HeartModelView from "../../components/HeartModelView";
import MedicationsField from "../../components/results/MedicationsField";
import MedicalDocumentUpload from "../../components/MedicalDocumentUpload";

const DigitalTwinLoadingScene = dynamic(() => import("../../components/DigitalTwinLoadingScene"), { ssr: false });

const HEALTH_QUESTIONS = [
  { id: "smoking", label: "Smoking status", type: "select", options: ["", "Never", "Occasional", "Daily"], placeholder: "Select", required: true },
  { id: "alcohol", label: "Alcohol consumption", type: "select", options: ["", "Never", "Daily", "Occasional", "Weekly"], placeholder: "Select", required: true },
  { id: "sleep", label: "Sleep per night", type: "select", options: ["", "4", "5", "6", "7", "8", "9", "10"], placeholder: "Select hours", optionLabels: { "4": "4 hours", "5": "5 hours", "6": "6 hours", "7": "7 hours", "8": "8 hours", "9": "9 hours", "10": "10 hours" }, required: true },
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
    <div data-field className={`space-y-2 ${open ? "relative z-50" : ""}`} ref={containerRef}>
      <label className="block text-sm font-semibold text-slate-800">Medical conditions <span className="font-normal text-(--color-muted)">(optional)</span></label>
      <p className="text-xs text-(--color-muted)">Search and select any known diagnoses.</p>
      <div className="relative">
        <input
          type="text"
          placeholder="Search conditions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onFocus={() => setOpen(true)}
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-(--color-muted-dim) focus:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15"
          aria-expanded={open}
          aria-haspopup="listbox"
        />
        {open && (
          <ul
            className="absolute z-100 mt-1 w-full max-h-52 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl py-1"
            role="listbox"
          >
            {filtered.length === 0 ? (
              <li className="px-4 py-3 text-sm text-(--color-muted)">No matches found</li>
            ) : (
              filtered.map((condition) => {
                const selected = conditions.includes(condition);
                return (
                  <li
                    key={condition}
                    role="option"
                    aria-selected={selected}
                    onClick={() => toggle(condition)}
                    className={`px-4 py-2.5 text-sm cursor-pointer select-none transition-colors ${selected ? "bg-emerald-50 text-(--color-primary) font-medium" : "text-slate-700 hover:bg-slate-50"}`}
                  >
                    <span className="flex items-center justify-between gap-2">
                      {condition}
                      {selected && (
                        <svg className="w-4 h-4 text-(--color-primary) shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </span>
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
            <span key={item} className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-200 pl-3 pr-2 py-1 text-sm text-slate-700">
              {item}
              <button type="button" onClick={() => toggle(item)} className="w-4 h-4 rounded flex items-center justify-center text-(--color-muted) hover:text-red-500 transition-colors" aria-label={`Remove ${item}`}>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
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
  const { input, setInput, profile, setProfile, setResult, clearResult } = useStore();

  // Handle lab values extracted from uploaded PDF
  const handleLabValues = useCallback((values) => {
    // All numeric lab keys — including new ones (ggt, alp, vitamins, tsh, iron, etc.)
    const labKeys = [
      "creatinine", "ast", "alt", "ggt", "alp", "bilirubin_total",
      "platelets", "cholesterol", "ldl", "hdl", "hba1c", "glucose",
      "systolic_bp", "diastolic_bp", "fev1_percent", "hemoglobin",
      "uric_acid", "egfr", "bun", "triglycerides", "albumin",
      "vitamin_b12", "vitamin_d", "tsh", "iron", "transferrin_saturation",
    ];
    labKeys.forEach((key) => {
      if (values[key] !== null && values[key] !== undefined) {
        setInput(key, values[key]);
      }
    });
    setInput("lab_source", "uploaded");

    // Auto-fill demographics from the report if the profile fields are currently empty
    // This fixes: gender showing "Male" for a female patient, wrong age, missing name
    if (values.gender && !profile.gender) {
      setProfile("gender", values.gender);
    }
    if (values.age && !profile.age) {
      setProfile("age", values.age);
    }
    if (values.patient_name && !profile.name) {
      setProfile("name", values.patient_name);
    }
  }, [setInput, setProfile, profile.gender, profile.age, profile.name]);

  // Handle prescription data extracted from uploaded PDF
  const handlePrescriptionData = useCallback(({ medications, conditions }) => {
    // Merge with existing medications (avoid duplicates)
    const existingMeds = Array.isArray(input.medications) ? input.medications : [];
    const newMeds = [...new Set([...existingMeds, ...medications])];
    setInput("medications", newMeds);

    // Merge with existing conditions (avoid duplicates)
    const existingConds = Array.isArray(input.medical_conditions) ? input.medical_conditions : [];
    const newConds = [...new Set([...existingConds, ...conditions])];
    setInput("medical_conditions", newConds);
  }, [setInput, input.medications, input.medical_conditions]);

  useEffect(() => {
    const hasProfile = profile && typeof profile === "object" && Object.keys(profile).some((k) => profile[k] != null && profile[k] !== "");
    if (!hasProfile) return;
    saveSubmission(profile, input).catch(() => {});
  }, []);

  const requiredHealthFields = ["smoking", "alcohol", "sleep", "stress"];
  const validateHealthInput = () => {
    return requiredHealthFields.filter((id) => {
      const v = input[id];
      return v == null || String(v).trim() === "";
    });
  };

  const handleGenerateReport = (e) => {
    e?.preventDefault?.();
    setSubmitError(null);
    const missing = validateHealthInput();
    if (missing.length > 0) {
      setSubmitError("Please fill all required fields: " + missing.map((id) => id.charAt(0).toUpperCase() + id.slice(1)).join(", ") + ".");
      return;
    }
    clearResult();
    setShowLoadingScene(true);
    Promise.allSettled([
      saveSubmission(profile, input),
      submitReport(profile, input),
    ]).then(([, reportResult]) => {
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
        setSubmitError(err?.message || "No report returned. Please try again.");
      }
    });
  };

  const handleLoadingComplete = () => {};

  useEffect(() => {
    if (heroRef.current) gsap.fromTo(heroRef.current, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.8, ease: "power3.out" });
    if (formRef.current) gsap.fromTo(formRef.current, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.7, delay: 0.15, ease: "power3.out" });
  }, []);

  return (
    <div className="min-h-screen bg-(--color-bg) flex flex-col">
      <AppHeader />

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_500px] overflow-hidden">

        {/* Left: Heart model panel */}
        <div ref={heroRef} className="relative bg-linear-to-br from-rose-50 via-white to-emerald-50 overflow-hidden min-h-[40vh] lg:min-h-0 flex flex-col">
          <div className="flex-1">
            <HeartModelView fullHeight className="w-full h-full min-h-0" />
          </div>

          {/* Info overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-8 bg-linear-to-t from-white/95 to-transparent">
            <div className="inline-flex items-center gap-2 bg-rose-50 border border-rose-200 text-xs font-semibold text-rose-700 uppercase tracking-wider px-3 py-1.5 rounded-full mb-3">
              <div className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" aria-hidden />
              Heart model active
            </div>
            <p className="text-base font-semibold text-slate-900 mb-1">Cardiovascular &amp; lifestyle assessment</p>
            <p className="text-sm text-(--color-muted)">Your lifestyle inputs directly influence the organ health predictions.</p>
          </div>
        </div>

        {/* Right: Form panel */}
        <div className="bg-white border-l border-slate-200 flex flex-col overflow-y-auto">
          <div ref={formRef} className="flex-1 p-8 md:p-10">

            {/* Back link + step indicator */}
            <div className="flex items-center justify-between mb-6">
              <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-(--color-muted) hover:text-foreground transition-colors font-medium">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
                Back
              </Link>
              <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-xs font-semibold text-(--color-primary) uppercase tracking-wider px-3 py-1.5 rounded-full">
                <div className="w-1.5 h-1.5 rounded-full bg-(--color-primary)" aria-hidden />
                Step 2 of 2
              </div>
            </div>

            <h2 className="text-2xl font-bold text-slate-900 mb-1.5">Lifestyle &amp; Health</h2>
            <p className="text-sm text-(--color-muted) mb-7">Tell us about your daily habits and any known conditions.</p>

            <form className="space-y-7" onSubmit={handleGenerateReport}>

              {/* Medical document upload — optional, improves accuracy */}
              <MedicalDocumentUpload
                onLabValues={handleLabValues}
                onPrescriptionData={handlePrescriptionData}
              />

              {/* Lifestyle section */}
              <div>
                <p className="text-xs font-bold text-(--color-primary) uppercase tracking-wider mb-4">Daily habits</p>
                <div className="grid grid-cols-2 gap-4">
                  {HEALTH_QUESTIONS.map(({ id, label, type, placeholder, options, optionLabels, required }) => (
                    <div key={id} data-field className="space-y-1.5">
                      <label htmlFor={id} className="block text-sm font-semibold text-slate-800">
                        {label}{required ? <span className="text-red-500 ml-0.5">*</span> : ""}
                      </label>
                      <select
                        id={id}
                        value={input[id] ?? ""}
                        onChange={(e) => setInput(id, e.target.value)}
                        className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15 appearance-none"
                        style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2364748B' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E\")", backgroundRepeat: "no-repeat", backgroundPosition: "right 0.75rem center", backgroundSize: "1rem", paddingRight: "2.5rem" }}
                      >
                        <option value="">{placeholder}</option>
                        {options.filter(Boolean).map((opt) => (
                          <option key={opt} value={opt}>{optionLabels?.[opt] ?? opt}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>

                {/* Smoking detail — only shown when user selects Daily or Occasional */}
                {(input.smoking === "Daily" || input.smoking === "Occasional") && (
                  <div className="mt-4 grid grid-cols-2 gap-4 rounded-xl border border-amber-100 bg-amber-50 p-4">
                    <p className="col-span-2 text-xs font-semibold text-amber-700 uppercase tracking-wider mb-1">
                      Smoking detail <span className="font-normal normal-case text-amber-600">(improves lung model accuracy)</span>
                    </p>
                    <div className="space-y-1.5">
                      <label htmlFor="cigarettes_per_day" className="block text-sm font-semibold text-slate-800">
                        Cigarettes per day
                      </label>
                      <input
                        id="cigarettes_per_day"
                        type="number"
                        min="1"
                        max="100"
                        placeholder="e.g. 10"
                        value={input.cigarettes_per_day ?? ""}
                        onChange={(e) => setInput("cigarettes_per_day", e.target.value === "" ? null : Number(e.target.value))}
                        className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label htmlFor="years_smoked" className="block text-sm font-semibold text-slate-800">
                        Years smoked
                      </label>
                      <input
                        id="years_smoked"
                        type="number"
                        min="1"
                        max="70"
                        placeholder="e.g. 5"
                        value={input.years_smoked ?? ""}
                        onChange={(e) => setInput("years_smoked", e.target.value === "" ? null : Number(e.target.value))}
                        className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Medical history section */}
              <div className="pt-5 border-t border-slate-100 space-y-5">
                <p className="text-xs font-bold text-(--color-primary) uppercase tracking-wider">Medical history</p>
                <MedicalConditionsField conditions={Array.isArray(input.medical_conditions) ? input.medical_conditions : []} onChange={(arr) => setInput("medical_conditions", arr)} />
                <MedicationsField medications={Array.isArray(input.medications) ? input.medications : []} onChange={(arr) => setInput("medications", arr)} />
              </div>

              {submitError && (
                <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-start gap-2" role="alert">
                  <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  {submitError}
                </div>
              )}

              <button
                type="submit"
                data-cta
                disabled={showLoadingScene}
                className="w-full flex items-center justify-center gap-2 bg-(--color-primary) hover:bg-(--color-primary-deep) text-white font-semibold text-sm px-6 py-3.5 rounded-xl shadow-sm transition-all disabled:opacity-50 disabled:pointer-events-none focus:outline-none focus:ring-2 focus:ring-(--color-primary) focus:ring-offset-2"
              >
                {showLoadingScene ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
                    Generating your report…
                  </>
                ) : (
                  <>
                    Generate My Health Report
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </main>

      {showLoadingScene && <DigitalTwinLoadingScene onComplete={handleLoadingComplete} />}
    </div>
  );
}
