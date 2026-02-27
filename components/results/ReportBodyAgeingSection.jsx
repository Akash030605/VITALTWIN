"use client";

import dynamic from "next/dynamic";
import { useState, useMemo } from "react";
import BiologicalAgeCard from "./BiologicalAgeCard";
import FutureSelfTimeline from "./FutureSelfTimeline";

const BodyModelView = dynamic(() => import("../BodyModelView"), { ssr: false });

/** Interpolate timeline data at a given year (0–10). */
function getInterpolatedTimelinePoint(timeline, year) {
  if (!timeline?.length || year <= 0) return timeline?.[0] ?? null;
  const sorted = [...timeline].sort((a, b) => a.year - b.year);
  if (year >= sorted[sorted.length - 1].year) return sorted[sorted.length - 1];
  let prev = sorted[0];
  let next = sorted.find((t) => t.year >= year) ?? sorted[sorted.length - 1];
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
    label: year <= 0 ? "Today" : `${Math.round(year)} year${Math.round(year) !== 1 ? "s" : ""} ahead`,
    vitality_score: Math.round(prev.vitality_score + t * (next.vitality_score - prev.vitality_score)),
    biological_age: Math.round(prev.biological_age + t * (next.biological_age - prev.biological_age)),
    changes: next.changes ?? prev.changes ?? [],
    visual_cues: next.visual_cues ?? prev.visual_cues ?? [],
  };
}

/** Build biological_age shape for preview at yearAhead. Real age advances with years ahead. */
function getPreviewBiologicalAge(reportBio, interpolated, yearAhead) {
  if (!reportBio) return reportBio;
  if (yearAhead <= 0) return reportBio;
  if (!interpolated) return reportBio;
  const real_age = Math.round(reportBio.real_age + yearAhead);
  const biological_age = interpolated.biological_age;
  const age_gap = biological_age - real_age;
  let gap_level = "GREEN";
  if (age_gap > 10) gap_level = "RED";
  else if (age_gap > 5) gap_level = "YELLOW";
  return {
    real_age,
    biological_age,
    age_gap,
    gap_level,
    message: `${yearAhead.toFixed(1)} years ahead — preview`,
    factors: interpolated.changes?.length ? interpolated.changes.slice(0, 3) : reportBio.factors?.slice(0, 3) ?? [],
  };
}

export default function ReportBodyAgeingSection({ result, gender }) {
  const [ageingLevel, setAgeingLevel] = useState(0);

  const yearAhead = ageingLevel * 10;
  const timeline = result?.future_self?.timeline ?? [];
  const interpolated = useMemo(
    () => getInterpolatedTimelinePoint(timeline, yearAhead),
    [timeline, yearAhead]
  );
  const previewBiologicalAge = useMemo(
    () => getPreviewBiologicalAge(result?.biological_age, interpolated, yearAhead),
    [result?.biological_age, interpolated, yearAhead]
  );

  const handleTimelineYearSelect = (year) => {
    setAgeingLevel(year / 10);
  };

  if (!result?.biological_age && !timeline?.length) return null;

  return (
    <section className="mb-8" id="body-ageing" aria-labelledby="body-ageing-heading">
      <div className="w-full grid grid-cols-1 lg:grid-cols-[minmax(300px,0.42fr)_1fr] gap-6 lg:gap-8 min-h-[420px] lg:min-h-[520px] items-stretch">
        {/* Left: Model — full height of section (same as first section) */}
        <div className="min-h-[380px] lg:min-h-0 flex flex-col gap-2">
          <div className="rounded-2xl overflow-hidden glass-card glass-card-glow flex-1 min-h-[340px] flex flex-col">
            <div className="flex-1 min-h-[280px]">
              <BodyModelView gender={gender} ageingLevel={ageingLevel} className="w-full h-full min-h-[280px]" showScanRing />
            </div>
            <div className="shrink-0 border-t border-white/10 p-4">
              <div className="flex items-center justify-between gap-3 mb-2">
                <span className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider">Years ahead</span>
                <span className="text-lg font-semibold text-[var(--color-primary)] tabular-nums">{yearAhead.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={ageingLevel * 100}
                onChange={(e) => setAgeingLevel(Number(e.target.value) / 100)}
                className="w-full h-2.5 rounded-full appearance-none bg-white/10 accent-[var(--color-primary)] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--color-primary)] [&::-webkit-slider-thumb]:cursor-pointer"
                aria-label="Preview years ahead"
              />
            </div>
          </div>
          <p className="text-xs font-mono text-[var(--color-primary)]/60 uppercase tracking-wider px-1 shrink-0">Body ageing · Clinical preview</p>
        </div>

        {/* Right: Title, then Biological age, then Future self — same height as left (same as first section) */}
        <div className="min-w-0 flex flex-col gap-6 min-h-[380px] lg:min-h-0">
          <div className="shrink-0">
            <h2 id="body-ageing-heading" className="text-xl md:text-2xl font-semibold text-[var(--foreground)] mb-1 text-glow-primary">Body Ageing</h2>
            <p className="text-sm text-[var(--color-muted)]">Objective comparison of calendar age vs biological age, based on your current assessment data.</p>
          </div>
          <div className="shrink-0">
            <BiologicalAgeCard biological_age={previewBiologicalAge} />
          </div>
          <div className="flex-1 min-h-[200px]">
            <FutureSelfTimeline
              future_self={result?.future_self}
              sliderYear={yearAhead}
              onYearSelect={handleTimelineYearSelect}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
