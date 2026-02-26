"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { useStore } from "../../store/useStore";
import { gsap } from "gsap";

const GENDER_OPTIONS = ["", "Male", "Female", "Non-binary", "Other", "Prefer not to say"];
const DIET_OPTIONS = ["", "Balanced", "Vegetarian", "Vegan", "Pescatarian", "Keto", "Low-carb", "Other"];
const ACTIVITY_OPTIONS = ["", "Sedentary", "Light", "Moderate", "Active", "Very active"];

const FIELDS = [
  { id: "name", label: "Full name", type: "text", placeholder: "Enter name" },
  { id: "age", label: "Age", type: "number", placeholder: "Years" },
  { id: "gender", label: "Gender", type: "select", options: GENDER_OPTIONS, placeholder: "Select gender" },
  { id: "height", label: "Height (cm)", type: "number", placeholder: "cm" },
  { id: "weight", label: "Weight (kg)", type: "number", placeholder: "kg" },
  { id: "diet", label: "Diet", type: "select", options: DIET_OPTIONS, placeholder: "Select diet" },
  { id: "activity", label: "Activity level", type: "select", options: ACTIVITY_OPTIONS, placeholder: "Select activity level" },
];

export default function ProfileForm() {
  const formRef = useRef(null);
  const { profile, setProfile } = useStore();

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
        <h2 className="font-mono text-sm font-medium text-[var(--color-primary)] tracking-[0.1em] uppercase">
          Subject Profile
        </h2>
        <p className="text-sm text-[var(--color-muted)] leading-relaxed">
          Enter your vitals and baseline data to initialize your digital twin for forensic analysis.
        </p>
      </div>
      
      <form ref={formRef} className="space-y-6">
        <div className="space-y-5">
          {FIELDS.map(({ id, label, type, placeholder, options }) => (
            <div key={id} data-field className="space-y-2">
              <label htmlFor={id} className="block font-mono text-xs text-[var(--color-primary)]/90 uppercase tracking-wider">
                {label}
              </label>
              {type === "select" ? (
                <select
                  id={id}
                  value={profile[id] ?? ""}
                  onChange={(e) => setProfile(id, e.target.value)}
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
                  type={type}
                  placeholder={placeholder}
                  value={profile[id] ?? ""}
                  onChange={(e) => setProfile(id, e.target.value)}
                  className="w-full rounded border border-[var(--color-surface-border)] bg-[var(--color-surface)]/30 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 transition-colors focus:border-[var(--color-primary)]/60 focus:bg-[var(--color-surface)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
                />
              )}
            </div>
          ))}
        </div>
        
        <div className="pt-4">
          <Link
            href="/health-questions"
            data-cta
            className="w-full flex items-center justify-center rounded bg-[var(--color-primary)] px-8 py-4 font-mono text-sm font-medium uppercase tracking-wide text-[var(--background)] transition-all hover:bg-[var(--color-primary)]/90 hover:shadow-lg hover:shadow-[var(--color-primary)]/20 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--background)]"
          >
            Continue to Health Assessment
          </Link>
        </div>
      </form>
    </div>
  );
}
