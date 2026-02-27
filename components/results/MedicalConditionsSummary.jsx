"use client";

import { useStore } from "../../store/useStore";

export default function MedicalConditionsSummary({ conditions: conditionsProp }) {
  const input = useStore((s) => s.input);
  const fromStore = Array.isArray(input?.medical_conditions) ? input.medical_conditions : [];
  const conditions = Array.isArray(conditionsProp) ? conditionsProp : fromStore;
  const filtered = conditions.filter((c) => c != null && String(c).trim() !== "");

  if (filtered.length === 0) return null;

  return (
    <div
      className="rounded-xl border border-amber-500/30 bg-amber-950/20 px-5 py-4 w-full"
      role="region"
      aria-label="Reported medical conditions"
    >
      <p className="text-xs font-semibold text-amber-400/90 uppercase tracking-wider mb-2">
        Reported conditions / previous diseases
      </p>
      <ul className="flex flex-wrap gap-2">
        {filtered.map((item, i) => (
          <li
            key={`${item}-${i}`}
            className="inline-flex items-center rounded-lg bg-white/10 border border-white/10 px-3 py-1.5 text-sm text-[var(--foreground)]"
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
