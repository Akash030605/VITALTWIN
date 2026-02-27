"use client";

import { useState } from "react";

export default function WhatIfPanel({ what_if_simulations }) {
  const [selectedId, setSelectedId] = useState("current");
  if (!what_if_simulations) return null;

  const { current, scenarios, quick_wins } = what_if_simulations;
  const selected = selectedId === "current" ? current : scenarios?.find((s) => s.id === selectedId) ?? current;

  return (
    <div
      className="rounded-2xl p-6 border-2 border-[var(--color-primary)]/40 bg-[var(--color-surface)]/80 shadow-[0_0_28px_rgba(20,184,166,0.12),inset_0_1px_0_rgba(255,255,255,0.04)] hover:border-[var(--color-primary)]/60 hover:shadow-[0_0_32px_rgba(20,184,166,0.18)] transition-all duration-300 relative overflow-hidden"
      role="region"
      aria-label="What if scenarios"
    >
      {/* Accent bar */}
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-[var(--color-primary)] to-[var(--color-primary)]/40 rounded-l-2xl" aria-hidden />

      <div className="pl-4">
        {quick_wins?.length > 0 && (
          <div className="mb-5 pb-4 border-b border-[var(--color-primary)]/20">
            <p className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-2">Quick wins</p>
            <ul className="flex flex-wrap gap-2">
              {quick_wins.map((w, i) => (
                <li key={i}>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-sm text-[var(--foreground)] hover:bg-[var(--color-primary)]/20 hover:border-[var(--color-primary)]/50 transition-colors cursor-default">
                    <span className="text-[var(--color-primary)] font-medium">{w.name}</span>
                    {w.gain != null && <span className="text-[var(--color-muted)] text-xs">+{w.gain} score</span>}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-3">Compare scenarios</p>
        <div className="flex flex-wrap gap-2 mb-5">
          <button
            type="button"
            onClick={() => setSelectedId("current")}
            className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] ${
              selectedId === "current"
                ? "bg-[var(--color-primary)] text-[var(--color-bg)] shadow-[0_0_16px_rgba(20,184,166,0.35)] scale-105"
                : "bg-white/5 text-[var(--color-muted)] hover:bg-white/10 hover:text-[var(--foreground)] hover:scale-[1.02] active:scale-[0.98]"
            }`}
          >
            Current
          </button>
          {scenarios?.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setSelectedId(s.id)}
              className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] ${
                selectedId === s.id
                  ? "bg-[var(--color-primary)] text-[var(--color-bg)] shadow-[0_0_16px_rgba(20,184,166,0.35)] scale-105"
                  : "bg-white/5 text-[var(--color-muted)] hover:bg-white/10 hover:text-[var(--foreground)] hover:scale-[1.02] active:scale-[0.98]"
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>

        {selected && (
          <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3 transition-opacity duration-200">
            <p className="text-[var(--foreground)] font-medium leading-relaxed">{selected.description}</p>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[var(--foreground)] font-medium">
                Bio age {selected.biological_age}
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[var(--foreground)] font-medium">
                Score {selected.health_score}
              </span>
            </div>
            {selected.improvements && (
              <div className="flex flex-wrap gap-2 pt-1">
                <span className="inline-flex items-center px-3 py-1.5 rounded-lg bg-[var(--color-primary)]/15 text-[var(--color-primary)] text-sm font-medium">
                  −{selected.improvements.biological_age_reduction} years
                </span>
                <span className="inline-flex items-center px-3 py-1.5 rounded-lg bg-[var(--color-primary)]/15 text-[var(--color-primary)] text-sm font-medium">
                  +{selected.improvements.health_score_increase} score
                </span>
                {selected.improvements.years_gained != null && (
                  <span className="inline-flex items-center px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-300 text-sm font-medium">
                    {selected.improvements.years_gained} years gained
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
