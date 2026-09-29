"use client";

import { useState, useEffect } from "react";

const RISK_THRESHOLDS = [
  { score: 40, label: "Critical Risk", color: "red", textClass: "text-red-600", borderClass: "border-red-300", bgClass: "bg-red-50", dotClass: "bg-red-500" },
  { score: 60, label: "Elevated Risk", color: "amber", textClass: "text-amber-600", borderClass: "border-amber-300", bgClass: "bg-amber-50", dotClass: "bg-amber-400" },
];

/** Interpolate between two timeline entries by year. */
function interpolate(timeline, year) {
  if (!timeline?.length || year <= 0) return timeline?.[0] ?? null;
  const sorted = [...timeline].sort((a, b) => a.year - b.year);
  if (year >= sorted[sorted.length - 1].year) return sorted[sorted.length - 1];
  let prev = sorted[0];
  let next = sorted[sorted.length - 1];
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i].year <= year && sorted[i + 1].year >= year) {
      prev = sorted[i];
      next = sorted[i + 1];
      break;
    }
  }
  const t = prev.year === next.year ? 1 : (year - prev.year) / (next.year - prev.year);
  return {
    year,
    label: year <= 0 ? "Today" : `${Math.round(year)}y`,
    vitality_score: Math.round(prev.vitality_score + t * (next.vitality_score - prev.vitality_score)),
    biological_age: Math.round(prev.biological_age + t * (next.biological_age - prev.biological_age)),
    changes: next.changes ?? prev.changes ?? [],
    visual_cues: next.visual_cues ?? prev.visual_cues ?? [],
  };
}

/** Find the fractional year when vitality_score first crosses below a threshold value. */
function findThresholdCrossing(timeline, threshold) {
  const sorted = [...timeline].sort((a, b) => a.year - b.year);
  for (let i = 0; i < sorted.length - 1; i++) {
    const a = sorted[i];
    const b = sorted[i + 1];
    if (a.vitality_score >= threshold && b.vitality_score < threshold) {
      // Linear interpolation of exact crossing year
      const t = (a.vitality_score - threshold) / (a.vitality_score - b.vitality_score);
      return a.year + t * (b.year - a.year);
    }
  }
  // Already below threshold from start
  if (sorted[0]?.vitality_score < threshold) return 0;
  return null;
}

export default function FutureSelfTimeline({ future_self, sliderYear, onYearSelect }) {
  const timeline = future_self?.timeline ?? [];
  const [selectedYear, setSelectedYear] = useState(timeline[0]?.year ?? 0);

  const yearToUse = sliderYear != null ? sliderYear : selectedYear;
  const interpolated = sliderYear != null && sliderYear > 0 ? interpolate(timeline, sliderYear) : null;
  const selected = interpolated ?? timeline.find((t) => t.year === selectedYear) ?? timeline[0];

  useEffect(() => {
    if (sliderYear != null) setSelectedYear(sliderYear);
  }, [sliderYear]);

  if (!timeline.length) return null;

  const handleYearClick = (year) => {
    setSelectedYear(year);
    onYearSelect?.(year);
  };

  // Compute risk threshold crossings
  const crossings = RISK_THRESHOLDS.map((thresh) => {
    const crossYear = findThresholdCrossing(timeline, thresh.score);
    return crossYear !== null ? { ...thresh, crossYear } : null;
  }).filter(Boolean);

  const maxYear = timeline[timeline.length - 1]?.year ?? 10;

  return (
    <div className="rounded-2xl p-6 glass-card border border-slate-200">
      <p className="text-xs font-medium text-(--color-primary) uppercase tracking-wider mb-3">Future self trajectory</p>

      {/* Risk threshold alerts */}
      {crossings.length > 0 && (
        <div className="space-y-1.5 mb-4">
          {crossings.map((c) => (
            <div
              key={c.label}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 border text-xs ${c.bgClass} ${c.borderClass}`}
              role="alert"
            >
              <svg className={`w-3.5 h-3.5 shrink-0 ${c.textClass}`} fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              <span className={c.textClass}>
                <span className="font-medium">{c.label}</span>
                {c.crossYear === 0
                  ? " — already below threshold"
                  : ` threshold crossed at ~${c.crossYear < 1 ? "<1" : c.crossYear.toFixed(1)} year${c.crossYear >= 2 ? "s" : ""}`}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Year buttons with threshold marker pins */}
      <div className="relative mb-4">
        <div className="flex gap-2 flex-wrap">
          {timeline.map((t) => {
            const isActive = sliderYear != null ? Math.abs(t.year - sliderYear) < 0.5 : selectedYear === t.year;
            return (
              <button
                key={t.year}
                type="button"
                onClick={() => handleYearClick(t.year)}
                className={`px-4 py-1.5 text-sm rounded-md border transition-colors duration-150 ${
                  isActive
                    ? "border-(--color-primary) text-(--color-primary) bg-transparent"
                    : "border-slate-200 text-(--color-muted) bg-transparent hover:text-foreground hover:border-slate-300"
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Threshold marker dots below the button row */}
        {crossings.filter((c) => c.crossYear > 0).length > 0 && (
          <div className="relative h-4 mt-1">
            {crossings
              .filter((c) => c.crossYear > 0)
              .map((c) => {
                const pct = Math.min(98, Math.max(2, (c.crossYear / maxYear) * 100));
                return (
                  <div
                    key={c.label}
                    className="absolute flex flex-col items-center -translate-x-1/2"
                    style={{ left: `${pct}%` }}
                    title={`${c.label} at ~${c.crossYear.toFixed(1)}y`}
                  >
                    <div className={`w-2 h-2 rounded-full ${c.dotClass}`} aria-hidden />
                  </div>
                );
              })}
          </div>
        )}
      </div>

      {selected && (
        <>
          <p className="text-foreground font-medium">Score {selected.vitality_score} · Bio age {selected.biological_age}</p>
          {selected.visual_cues?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2" aria-label="Visual cues">
              {selected.visual_cues.map((cue, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded border border-slate-200 text-(--color-muted) bg-slate-50">
                  {cue.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          )}
          {selected.changes?.length > 0 && (
            <ul className="text-sm text-(--color-muted) list-disc list-inside mt-2 space-y-1">
              {selected.changes.slice(0, 3).map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
