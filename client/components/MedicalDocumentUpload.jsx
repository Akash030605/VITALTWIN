"use client";

import { useRef, useState } from "react";
import { extractTextFromPdf } from "../lib/parsePdf";

/**
 * MedicalDocumentUpload
 *
 * Two-tab upload component for the health-questions page:
 *   Tab 1 — Blood Test Report PDF → extracts lab values → fills store
 *   Tab 2 — Prescription PDF → extracts medications + conditions → fills store
 *
 * Props:
 *   onLabValues(values)         — called with { creatinine, ast, alt, ... }
 *   onPrescriptionData(data)    — called with { medications: [], conditions: [] }
 */

const LAB_VALUE_LABELS = {
  creatinine:    { label: "Creatinine",    unit: "mg/dL",    organ: "Kidney" },
  ast:           { label: "AST",           unit: "U/L",      organ: "Liver"  },
  alt:           { label: "ALT",           unit: "U/L",      organ: "Liver"  },
  platelets:     { label: "Platelets",     unit: "×10³/µL",  organ: "Liver"  },
  cholesterol:   { label: "Cholesterol",   unit: "mg/dL",    organ: "Heart"  },
  ldl:           { label: "LDL",           unit: "mg/dL",    organ: "Heart"  },
  hdl:           { label: "HDL",           unit: "mg/dL",    organ: "Heart"  },
  hba1c:         { label: "HbA1c",         unit: "%",        organ: "Multi"  },
  glucose:       { label: "Glucose",       unit: "mg/dL",    organ: "Multi"  },
  systolic_bp:   { label: "Systolic BP",   unit: "mmHg",     organ: "Heart"  },
  diastolic_bp:  { label: "Diastolic BP",  unit: "mmHg",     organ: "Heart"  },
  fev1_percent:  { label: "FEV1",          unit: "%",        organ: "Lungs"  },
  hemoglobin:    { label: "Hemoglobin",    unit: "g/dL",     organ: "BioAge" },
  uric_acid:     { label: "Uric Acid",     unit: "mg/dL",    organ: "Kidney" },
  egfr:          { label: "eGFR",          unit: "mL/min",   organ: "Kidney" },
  bun:           { label: "BUN",           unit: "mg/dL",    organ: "Kidney" },
  triglycerides: { label: "Triglycerides", unit: "mg/dL",    organ: "Heart"  },
  albumin:       { label: "Albumin",       unit: "g/dL",     organ: "Liver"  },
};

// Confidence impact descriptions for key values
const CONFIDENCE_IMPACT = {
  creatinine:  "Kidney accuracy: 55% → 92%",
  ast:         "Liver FIB-4: estimated → exact",
  alt:         "Liver APRI: estimated → exact",
  cholesterol: "Heart PCE: improved accuracy",
  hba1c:       "Multi-organ: diabetes risk exact",
  systolic_bp: "Heart PCE: Stage 2 HTN detection",
};

const ORGAN_COLORS = {
  Kidney: "bg-blue-50 text-blue-700 border-blue-200",
  Liver:  "bg-amber-50 text-amber-700 border-amber-200",
  Heart:  "bg-rose-50 text-rose-700 border-rose-200",
  Lungs:  "bg-cyan-50 text-cyan-700 border-cyan-200",
  Multi:  "bg-violet-50 text-violet-700 border-violet-200",
  BioAge: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

function StatusBadge({ type, message }) {
  if (!message) return null;
  const isError = type === "error";
  return (
    <div
      className={`rounded-lg px-3 py-2.5 text-sm flex items-start gap-2 ${
        isError
          ? "bg-red-50 border border-red-200 text-red-700"
          : "bg-emerald-50 border border-emerald-200 text-emerald-700"
      }`}
      role="status"
    >
      {isError ? (
        <svg className="w-4 h-4 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ) : (
        <svg className="w-4 h-4 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      )}
      <span>{message}</span>
    </div>
  );
}

function LabValueGrid({ values }) {
  const found = Object.entries(values).filter(([, v]) => v !== null);
  if (found.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
        Extracted values ({found.length} found)
      </p>
      <div className="grid grid-cols-2 gap-2">
        {found.map(([key, value]) => {
          const meta = LAB_VALUE_LABELS[key];
          if (!meta) return null;
          const colorClass = ORGAN_COLORS[meta.organ] || ORGAN_COLORS.Multi;
          const impact = CONFIDENCE_IMPACT[key];
          return (
            <div
              key={key}
              className={`rounded-lg border px-2.5 py-2 text-xs ${colorClass}`}
            >
              <div className="flex items-center justify-between gap-1">
                <span className="font-semibold">{meta.label}</span>
                <span className="font-bold">{value} {meta.unit}</span>
              </div>
              {impact && (
                <p className="text-[10px] mt-0.5 opacity-75">{impact}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PrescriptionResultGrid({ medications, conditions }) {
  const hasMeds = medications.length > 0;
  const hasConds = conditions.length > 0;
  if (!hasMeds && !hasConds) return null;

  return (
    <div className="mt-3 space-y-3">
      {hasMeds && (
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            Medications ({medications.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {medications.map((med, i) => (
              <span key={i} className="inline-flex items-center rounded-lg bg-blue-50 border border-blue-200 px-2.5 py-1 text-xs text-blue-700 font-medium">
                💊 {med}
              </span>
            ))}
          </div>
        </div>
      )}
      {hasConds && (
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            Conditions ({conditions.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {conditions.map((cond, i) => (
              <span key={i} className="inline-flex items-center rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1 text-xs text-amber-700 font-medium">
                🩺 {cond}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function UploadDropzone({ onFile, loading, accept = ".pdf", label, hint }) {
  const fileRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return;
    }
    onFile(file);
  };

  return (
    <div
      className={`relative rounded-xl border-2 border-dashed px-4 py-5 text-center cursor-pointer transition-all duration-200 ${
        dragging
          ? "border-(--color-primary) bg-(--color-primary)/8"
          : "border-slate-300 bg-slate-50 hover:border-(--color-primary)/50 hover:bg-emerald-50/50"
      } ${loading ? "pointer-events-none opacity-60" : ""}`}
      onClick={() => !loading && fileRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && !loading && fileRef.current?.click()}
      aria-label={label}
    >
      <input
        ref={fileRef}
        type="file"
        accept={accept}
        onChange={(e) => { handleFile(e.target.files?.[0]); e.target.value = ""; }}
        className="hidden"
        aria-hidden
      />
      <div className="flex flex-col items-center gap-2">
        {loading ? (
          <>
            <svg className="w-6 h-6 text-(--color-primary) animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden>
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            <p className="text-sm text-(--color-muted) font-medium">AI reading your document…</p>
            <p className="text-xs text-(--color-muted)/60">This takes 2–4 seconds</p>
          </>
        ) : (
          <>
            <svg className="w-7 h-7 text-(--color-primary)/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm text-(--color-muted)">{label}</p>
            {hint && <p className="text-xs text-(--color-muted)/60">{hint}</p>}
          </>
        )}
      </div>
    </div>
  );
}

export default function MedicalDocumentUpload({ onLabValues, onPrescriptionData }) {
  const [activeTab, setActiveTab] = useState("lab"); // "lab" | "prescription"

  // Lab report state
  const [labLoading, setLabLoading] = useState(false);
  const [labStatus, setLabStatus] = useState(null); // { type, message }
  const [labValues, setLabValues] = useState(null);

  // Prescription state
  const [rxLoading, setRxLoading] = useState(false);
  const [rxStatus, setRxStatus] = useState(null);
  const [rxData, setRxData] = useState(null);

  // ── Lab Report handler ────────────────────────────────────────────────────
  const handleLabFile = async (file) => {
    setLabLoading(true);
    setLabStatus(null);
    setLabValues(null);

    try {
      // Step 1: Extract text from PDF (browser-side)
      let text;
      try {
        text = await extractTextFromPdf(file);
      } catch (err) {
        throw new Error("Could not read PDF. Make sure it is a text-based PDF (not a scanned image).");
      }

      if (!text || text.trim().length < 20) {
        throw new Error("No readable text found in this PDF. It may be a scanned image — text-based PDFs only.");
      }

      // Step 2: Send to Groq via /api/parse-lab
      const res = await fetch("/api/parse-lab", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || `Server error ${res.status}`);
      }

      const { values, found_count } = data;

      if (!found_count || found_count === 0) {
        setLabStatus({ type: "error", message: "No lab values found. Make sure this is a blood test report." });
        return;
      }

      setLabValues(values);
      setLabStatus({
        type: "success",
        message: `✓ Found ${found_count} lab value${found_count !== 1 ? "s" : ""} — applied to your report.`,
      });

      // Notify parent to update the store
      onLabValues?.(values);

    } catch (err) {
      setLabStatus({ type: "error", message: err?.message || "Upload failed. Please try again." });
    } finally {
      setLabLoading(false);
    }
  };

  // ── Prescription handler ──────────────────────────────────────────────────
  const handleRxFile = async (file) => {
    setRxLoading(true);
    setRxStatus(null);
    setRxData(null);

    try {
      // Step 1: Extract text from PDF (browser-side)
      let text;
      try {
        text = await extractTextFromPdf(file);
      } catch (err) {
        throw new Error("Could not read PDF. Make sure it is a text-based PDF (not a scanned image).");
      }

      if (!text || text.trim().length < 10) {
        throw new Error("No readable text found in this PDF.");
      }

      // Step 2: Send to Groq via /api/parse-prescription
      const res = await fetch("/api/parse-prescription", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || `Server error ${res.status}`);
      }

      const { medications, conditions, found_count } = data;

      if (!found_count || found_count === 0) {
        setRxStatus({ type: "error", message: "No medications or conditions found. Make sure this is a prescription." });
        return;
      }

      setRxData({ medications, conditions });
      const parts = [];
      if (medications.length > 0) parts.push(`${medications.length} medication${medications.length !== 1 ? "s" : ""}`);
      if (conditions.length > 0) parts.push(`${conditions.length} condition${conditions.length !== 1 ? "s" : ""}`);
      setRxStatus({
        type: "success",
        message: `✓ Found ${parts.join(" and ")} — added to your profile.`,
      });

      // Notify parent to update the store
      onPrescriptionData?.({ medications, conditions });

    } catch (err) {
      setRxStatus({ type: "error", message: err?.message || "Upload failed. Please try again." });
    } finally {
      setRxLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-emerald-50/30 overflow-hidden">
      {/* Header */}
      <div className="px-5 pt-4 pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2 mb-0.5">
          <svg className="w-4 h-4 text-(--color-primary)" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
          </svg>
          <p className="text-sm font-semibold text-slate-800">Upload Medical Documents</p>
          <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
            Optional
          </span>
        </div>
        <p className="text-xs text-(--color-muted)">
          PDF only · AI extracts values automatically · Improves accuracy up to 92%
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          type="button"
          onClick={() => setActiveTab("lab")}
          className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === "lab"
              ? "bg-white text-(--color-primary) border-b-2 border-(--color-primary)"
              : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
          }`}
        >
          🧪 Blood Test Report
          {labValues && (
            <span className="ml-1 w-4 h-4 rounded-full bg-(--color-primary) text-white text-[9px] flex items-center justify-center font-bold">
              ✓
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("prescription")}
          className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === "prescription"
              ? "bg-white text-(--color-primary) border-b-2 border-(--color-primary)"
              : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
          }`}
        >
          💊 Prescription
          {rxData && (
            <span className="ml-1 w-4 h-4 rounded-full bg-(--color-primary) text-white text-[9px] flex items-center justify-center font-bold">
              ✓
            </span>
          )}
        </button>
      </div>

      {/* Tab content */}
      <div className="p-4">
        {activeTab === "lab" ? (
          <div className="space-y-3">
            <UploadDropzone
              onFile={handleLabFile}
              loading={labLoading}
              accept=".pdf"
              label="Drop blood test PDF here or click to browse"
              hint="Supports: Dr. Lal PathLabs, SRL, Metropolis, Apollo, AIIMS, government hospital reports"
            />
            <StatusBadge type={labStatus?.type} message={labStatus?.message} />
            {labValues && <LabValueGrid values={labValues} />}
            {!labValues && !labLoading && (
              <p className="text-[11px] text-slate-400 text-center">
                Extracts: Creatinine · Cholesterol · HbA1c · AST/ALT · Hemoglobin · BP · and more
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <UploadDropzone
              onFile={handleRxFile}
              loading={rxLoading}
              accept=".pdf"
              label="Drop prescription PDF here or click to browse"
              hint="Auto-fills your medications and adds diagnosed conditions"
            />
            <StatusBadge type={rxStatus?.type} message={rxStatus?.message} />
            {rxData && <PrescriptionResultGrid medications={rxData.medications} conditions={rxData.conditions} />}
            {!rxData && !rxLoading && (
              <p className="text-[11px] text-slate-400 text-center">
                Extracts: Drug names · Dosages · Diagnosed conditions
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
