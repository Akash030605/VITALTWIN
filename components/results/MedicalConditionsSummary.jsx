"use client";

import { useStore } from "../../store/useStore";

export default function MedicalConditionsSummary({ conditions: conditionsProp, medications: medicationsProp }) {
  const input = useStore((s) => s.input);

  const conditions = Array.isArray(conditionsProp)
    ? conditionsProp
    : Array.isArray(input?.medical_conditions) ? input.medical_conditions : [];

  const medications = Array.isArray(medicationsProp)
    ? medicationsProp
    : Array.isArray(input?.medications) ? input.medications : [];

  const filteredConditions = conditions.filter((c) => c != null && String(c).trim() !== "");
  const filteredMedications = medications.filter((m) => m != null && String(m).trim() !== "");

  if (filteredConditions.length === 0 && filteredMedications.length === 0) return null;

  return (
    <div className="space-y-3">
      {filteredConditions.length > 0 && (
        <div
          className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 w-full"
          role="region"
          aria-label="Reported medical conditions"
        >
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">
            Medical conditions
          </p>
          <ul className="flex flex-wrap gap-2">
            {filteredConditions.map((item, i) => (
              <li
                key={`${item}-${i}`}
                className="inline-flex items-center rounded-lg bg-amber-100/60 border border-amber-200 px-3 py-1.5 text-sm text-foreground"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {filteredMedications.length > 0 && (
        <div
          className="rounded-xl border border-(--color-primary)/20 bg-emerald-50 px-5 py-4 w-full"
          role="region"
          aria-label="Current medications"
        >
          <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider mb-2">
            Current medications
          </p>
          <ul className="flex flex-wrap gap-2">
            {filteredMedications.map((item, i) => (
              <li
                key={`${item}-${i}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-(--color-primary)/10 border border-(--color-primary)/20 px-3 py-1.5 text-sm text-foreground"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-(--color-primary) shrink-0" aria-hidden />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
