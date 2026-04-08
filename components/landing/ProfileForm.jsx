"use client";

import { useRef, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "../../store/useStore";
import { saveSubmission } from "../../lib/profileApi";
import { gsap } from "gsap";

const GENDER_OPTIONS = ["", "Male", "Female", "Other"];
const DIET_OPTIONS = ["", "Poor", "Avg", "Good"];
const ACTIVITY_OPTIONS = ["", "Sedentary", "Moderate", "Active"];

const FIELDS = [
  { id: "name", label: "Full name", type: "text", placeholder: "Enter name", required: true },
  { id: "age", label: "Age", type: "number", placeholder: "Years", required: true, min: 1 },
  { id: "gender", label: "Gender", type: "select", options: GENDER_OPTIONS, placeholder: "Select gender", required: true },
  { id: "height", label: "Height (cm)", type: "number", placeholder: "cm", required: true, min: 1 },
  { id: "weight", label: "Weight (kg)", type: "number", placeholder: "kg", required: true, min: 1 },
  { id: "diet", label: "Diet", type: "select", options: DIET_OPTIONS, placeholder: "Select diet", required: true },
  { id: "activity", label: "Activity level", type: "select", options: ACTIVITY_OPTIONS, placeholder: "Select activity level", required: true },
];

export default function ProfileForm() {
  const formRef = useRef(null);
  const [saveError, setSaveError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const router = useRouter();
  const { profile, setProfile, input } = useStore();

  const validate = () => {
    const errors = {};
    FIELDS.forEach(({ id, required, min }) => {
      if (!required) return;
      const v = profile[id];
      const empty = v == null || String(v).trim() === "";
      if (empty) {
        errors[id] = "Required";
        return;
      }
      if (min != null && (id === "age" || id === "height" || id === "weight")) {
        const n = Number(v);
        if (Number.isNaN(n) || n < min) errors[id] = `Enter at least ${min}`;
      }
    });
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleContinue = (e) => {
    e.preventDefault();
    setSaveError(null);
    setFieldErrors({});
    if (!validate()) return;
    saveSubmission(profile, input ?? {})
      .then(() => router.push("/health-questions"))
      .catch((err) => setSaveError(err?.message || "Failed to save. Check backend."));
  };

  useEffect(() => {
    const fields = formRef.current?.querySelectorAll("[data-field]");
    const btn = formRef.current?.querySelector("[data-cta]");
    if (fields?.length) {
      gsap.fromTo(fields, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, delay: 0.35, ease: "power3.out" });
    }
    if (btn) {
      gsap.fromTo(btn, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.85, ease: "power3.out" });
    }
  }, []);

  return (
    <div className="max-w-lg space-y-8">
      <div className="space-y-2">
        <h2 className="font-heading text-sm font-medium text-(--color-primary) tracking-[0.1em] uppercase">
          Your Profile
        </h2>
        <p className="font-heading text-sm text-(--color-muted) leading-relaxed">
          Enter your vitals and baseline data so we can build your personal health profile.
        </p>
      </div>

      <form ref={formRef} className="space-y-6">
        <div className="space-y-5">
          {FIELDS.map(({ id, label, type, placeholder, options, required }) => (
            <div key={id} data-field className="space-y-2">
              <label htmlFor={id} className="block text-sm font-medium text-(--foreground)">
                {label}{required ? " *" : ""}
              </label>
              {type === "select" ? (
                <select
                  id={id}
                  value={profile[id] ?? ""}
                  onChange={(e) => { setProfile(id, e.target.value); setFieldErrors((prev) => ({ ...prev, [id]: null })); }}
                  className={`form-select w-full rounded-lg border px-4 py-3 text-sm text-(--foreground) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15 ${fieldErrors[id] ? "border-red-300 bg-red-50" : "border-slate-200 bg-white focus:border-(--color-primary)"}`}
                  aria-invalid={!!fieldErrors[id]}
                  aria-describedby={fieldErrors[id] ? `${id}-error` : undefined}
                >
                  <option value="">{placeholder}</option>
                  {options.filter(Boolean).map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              ) : (
                <input
                  id={id}
                  type={type}
                  placeholder={placeholder}
                  value={profile[id] ?? ""}
                  onChange={(e) => { setProfile(id, e.target.value); setFieldErrors((prev) => ({ ...prev, [id]: null })); }}
                  className={`w-full rounded-lg border px-4 py-3 text-sm text-(--foreground) placeholder:text-(--color-muted-dim) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15 ${fieldErrors[id] ? "border-red-300 bg-red-50" : "border-slate-200 bg-white focus:border-(--color-primary)"}`}
                  aria-invalid={!!fieldErrors[id]}
                  aria-describedby={fieldErrors[id] ? `${id}-error` : undefined}
                />
              )}
              {fieldErrors[id] && (
                <p id={`${id}-error`} className="text-xs text-red-600" role="alert">{fieldErrors[id]}</p>
              )}
            </div>
          ))}
        </div>

        {saveError && (
          <p className="text-sm text-red-400" role="alert">{saveError}</p>
        )}
        <div className="pt-4">
          <button
            type="button"
            onClick={handleContinue}
            data-cta
            className="font-heading w-full flex items-center justify-center gap-2 rounded-xl bg-(--color-primary) px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-(--color-primary-deep) focus:outline-none focus:ring-2 focus:ring-(--color-primary) focus:ring-offset-2 focus:ring-offset-white"
          >
            Continue to Health Assessment
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
          </button>
        </div>
      </form>
    </div>
  );
}
