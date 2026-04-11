"use client";

const LABELS = { name: "Name", age: "Age", gender: "Gender", height: "Height (cm)", weight: "Weight (kg)", diet: "Diet", activity: "Activity" };
const FIELDS = ["name", "age", "gender", "height", "weight", "diet", "activity"];

export default function ProfileSummary({ profile }) {
  const entries = FIELDS.filter((k) => profile?.[k] != null && String(profile[k]).trim() !== "");
  if (entries.length === 0) return null;

  // Build compact summary
  const name = profile.name;
  const age = profile.age;
  const gender = profile.gender;
  const bmi = (profile.height && profile.weight)
    ? (profile.weight / Math.pow(profile.height / 100, 2)).toFixed(1)
    : null;

  return (
    <div className="flex flex-wrap items-center gap-3" aria-label="Patient profile summary">
      {name && (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-(--color-primary)">
              {name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)}
            </span>
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900">{name}</p>
            {(age || gender) && (
              <p className="text-xs text-(--color-muted)">
                {[age && `${age}y`, gender, bmi && `BMI ${bmi}`].filter(Boolean).join(" · ")}
              </p>
            )}
          </div>
        </div>
      )}
      {entries.filter(k => !["name","age","gender","height","weight"].includes(k)).map((key) => (
        <div key={key} className="flex items-center gap-1.5 bg-slate-50 rounded-lg px-3 py-1.5 border border-slate-200">
          <span className="text-xs text-(--color-muted)">{LABELS[key]}:</span>
          <span className="text-xs font-semibold text-slate-800">{profile[key]}</span>
        </div>
      ))}
    </div>
  );
}
