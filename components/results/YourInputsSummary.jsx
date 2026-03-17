"use client";

/**
 * Compact summary of user's health inputs (lifestyle, habits, conditions) for personalization context.
 * Use above organs or recommendations so relations between inputs and scores are clear.
 */
const INPUT_LABELS = {
  smoking: "Smoking",
  alcohol: "Alcohol",
  sleep: "Sleep",
  stress: "Stress",
  medical_conditions: "Conditions",
};

function formatValue(key, value) {
  if (key === "medical_conditions" && Array.isArray(value)) {
    return value.length ? value.join(", ") : "None";
  }
  if (key === "sleep" && (typeof value === "number" || (typeof value === "string" && value.trim() !== "")))
    return `${value}h`;
  return value == null || String(value).trim() === "" ? "—" : String(value);
}

export default function YourInputsSummary({ profile = {}, input = {} }) {
  const lifestyle = [
    { key: "smoking", value: input.smoking },
    { key: "alcohol", value: input.alcohol },
    { key: "sleep", value: input.sleep ?? input.sleep === 0 ? 0 : null },
    { key: "stress", value: input.stress },
  ].filter(({ value }) => value != null && String(value).trim() !== "");
  const conditions = Array.isArray(input.medical_conditions) ? input.medical_conditions.filter(Boolean) : [];
  const diet = profile?.diet;
  const activity = profile?.activity;
  const hasLifestyle = lifestyle.length > 0 || conditions.length > 0 || diet || activity;
  if (!hasLifestyle) return null;

  return (
    <div
      className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 mb-6"
      role="region"
      aria-label="Your inputs summary"
    >
      <p className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-2">Based on your profile</p>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--color-muted)]">
        {lifestyle.map(({ key, value }) => (
          <span key={key}>
            <span className="text-[var(--foreground)]/80">{INPUT_LABELS[key]}:</span>{" "}
            <span className="text-[var(--foreground)] font-medium">{formatValue(key, value)}</span>
          </span>
        ))}
        {conditions.length > 0 && (
          <span>
            <span className="text-[var(--foreground)]/80">Conditions:</span>{" "}
            <span className="text-[var(--foreground)] font-medium">{conditions.join(", ")}</span>
          </span>
        )}
        {diet && (
          <span>
            <span className="text-[var(--foreground)]/80">Diet:</span>{" "}
            <span className="text-[var(--foreground)] font-medium">{diet}</span>
          </span>
        )}
        {activity && (
          <span>
            <span className="text-[var(--foreground)]/80">Activity:</span>{" "}
            <span className="text-[var(--foreground)] font-medium">{activity}</span>
          </span>
        )}
      </div>
    </div>
  );
}
