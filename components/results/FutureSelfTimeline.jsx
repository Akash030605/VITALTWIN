"use client";

import { useState, useEffect } from "react";

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

  return (
    <div className="rounded-2xl p-6 glass-card border border-white/10">
      <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-4">Future self trajectory</p>
      <div className="flex gap-2 mb-4 flex-wrap">
        {timeline.map((t) => {
          const isActive = sliderYear != null ? Math.abs(t.year - sliderYear) < 0.5 : selectedYear === t.year;
          return (
            <button
              key={t.year}
              type="button"
              onClick={() => handleYearClick(t.year)}
              className={`px-4 py-1.5 text-sm rounded-md border transition-colors duration-150 ${
                isActive
                  ? "border-[var(--color-primary)] text-[var(--color-primary)] bg-transparent"
                  : "border-white/10 text-[var(--color-muted)] bg-transparent hover:text-[var(--foreground)]"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      {selected && (
        <>
          <p className="text-[var(--foreground)] font-medium">Score {selected.vitality_score} · Bio age {selected.biological_age}</p>
          {selected.visual_cues?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2" aria-label="Visual cues">
              {selected.visual_cues.map((cue, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded border border-white/10 text-[var(--color-muted)]">
                  {cue.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          )}
          {selected.changes?.length > 0 && (
            <ul className="text-sm text-[var(--color-muted)] list-disc list-inside mt-2 space-y-1">
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
