"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { useStore } from "../../store/useStore";
import { gsap } from "gsap";

const GENDER_OPTIONS = ["", "Male", "Female", "Other"];
const DIET_OPTIONS = ["", "Poor", "Avg", "Good"];
const ACTIVITY_OPTIONS = ["", "Sedentary", "Moderate", "Active"];

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
        <h2 className="font-heading text-sm font-medium text-[var(--color-primary)] tracking-[0.1em] uppercase">
          Subject Profile
        </h2>
        <p className="font-heading text-sm text-[var(--color-muted)] leading-relaxed">
          Enter your vitals and baseline data to initialize your digital twin for forensic analysis.
        </p>
      </div>

      <form ref={formRef} className="space-y-6">
        <div className="space-y-5">
          {FIELDS.map(({ id, label, type, placeholder, options }) => (
            <div key={id} data-field className="space-y-2">
              <label htmlFor={id} className="block text-sm font-medium text-[var(--foreground)]">
                {label}
              </label>
              {type === "select" ? (
                <select
                  id={id}
                  value={profile[id] ?? ""}
                  onChange={(e) => setProfile(id, e.target.value)}
                  className="form-select w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--foreground)] focus:border-[var(--color-primary)]/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
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
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-primary)]/60 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
                />
              )}
            </div>
          ))}
        </div>

        <div className="pt-4">
          <Link
            href="/health-questions"
            data-cta
            className="landing-cta font-heading w-full flex items-center justify-center rounded-sm border border-[var(--color-primary)]/60 bg-[var(--color-primary)]/10 px-8 py-4 text-sm font-medium uppercase tracking-wider text-[var(--color-primary)] transition-all hover:bg-[var(--color-primary)]/20 hover:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)]"
          >
            [ Continue to Health Assessment ]
          </Link>
        </div>
      </form>
    </div>
  );
}
