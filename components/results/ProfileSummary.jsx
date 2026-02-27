"use client";

const FIELDS = ["name", "age", "gender", "height", "weight", "diet", "activity"];
const LABELS = {
  name: "Name",
  age: "Age",
  gender: "Gender",
  height: "Height",
  weight: "Weight",
  diet: "Diet",
  activity: "Activity",
};

export default function ProfileSummary({ profile }) {
  const entries = FIELDS.filter((k) => profile?.[k] != null && String(profile[k]).trim() !== "");
  if (entries.length === 0) return null;

  return (
    <div className="flex flex-wrap items-baseline gap-x-1 gap-y-2 text-sm text-[var(--color-muted)]" aria-label="Profile summary">
      {entries.map((key, i) => (
        <span key={key} className="inline-flex items-baseline gap-2">
          {i > 0 && <span className="mx-2.5 text-[var(--color-muted)]/60 select-none" aria-hidden>•</span>}
          <span>{LABELS[key]}:</span>
          <span className="text-[var(--foreground)] font-medium">{profile[key]}</span>
        </span>
      ))}
    </div>
  );
}
