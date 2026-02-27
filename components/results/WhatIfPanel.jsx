"use client";

import { useState, useEffect, useRef } from "react";
import { useStore } from "../../store/useStore";
import { fetchWhatIfScenario } from "../../lib/api";

const WHAT_IF_SCENARIOS = [
  { id: "quit_smoking", name: "Quit Smoking", changes: { HealthInfo: { Smoking: "Never" } } },
  { id: "sleep_8", name: "Sleep 8 Hours", changes: { HealthInfo: { Sleep: 8 } } },
  { id: "reduce_stress", name: "Reduce Stress", changes: { HealthInfo: { Stress: "Low" } } },
  { id: "stop_alcohol", name: "Stop Alcohol", changes: { HealthInfo: { Alcohol: "Never" } } },
  { id: "active_lifestyle", name: "Active Lifestyle", changes: { ProfileInfo: { ActivityLevel: "Active" } } },
  { id: "healthy_diet", name: "Healthy Diet", changes: { ProfileInfo: { Diet: "Good" } } },
  {
    id: "complete_transformation",
    name: "Complete Transformation",
    changes: {
      HealthInfo: { Smoking: "Never", Sleep: 8, Stress: "Low", Alcohol: "Never" },
      ProfileInfo: { ActivityLevel: "Active", Diet: "Good" },
    },
  },
];

const CURRENT_ID = "current";

function summarizeReport(report) {
  if (!report || typeof report !== "object") return { biological_age: "—", health_score: "—", message: "—" };
  const bio = report.biological_age;
  const score = report.overall_health_score ?? report.vital_score?.current ?? "—";
  const bioNum = typeof bio === "object" ? bio?.biological_age : bio;
  const msg = report.vital_score?.message ?? report.vital_score?.interpretation ?? "—";
  return { biological_age: bioNum ?? "—", health_score: score, message: msg };
}

export default function WhatIfPanel({ what_if_simulations }) {
  const profile = useStore((s) => s.profile);
  const input = useStore((s) => s.input);

  const [selectedId, setSelectedId] = useState(CURRENT_ID);
  const [scenarioResults, setScenarioResults] = useState({});
  const [loadingId, setLoadingId] = useState(null);
  const [error, setError] = useState(null);

  const isCurrent = selectedId === CURRENT_ID;
  const selectedScenario = isCurrent ? null : WHAT_IF_SCENARIOS.find((s) => s.id === selectedId);
  const cachedData = scenarioResults[selectedId] ?? null;
  const displaySummary = cachedData ? summarizeReport(cachedData) : null;
  const isLoading = loadingId != null;

  const currentFetched = useRef(false);

  const loadScenario = async (id) => {
    if (scenarioResults[id]) return;
    const changes = id === CURRENT_ID ? {} : WHAT_IF_SCENARIOS.find((s) => s.id === id)?.changes;
    if (id !== CURRENT_ID && !changes) return;
    setLoadingId(id);
    try {
      const data = await fetchWhatIfScenario(profile, input, changes ?? {});
      setScenarioResults((prev) => ({ ...prev, [id]: data }));
    } catch (err) {
      setError(err?.message || "Failed to load scenario.");
    } finally {
      setLoadingId(null);
    }
  };

  const handleSelectScenario = (id) => {
    setSelectedId(id);
    setError(null);
    if (scenarioResults[id]) return;
    loadScenario(id);
  };

  useEffect(() => {
    if (!profile || !input || currentFetched.current) return;
    currentFetched.current = true;
    loadScenario(CURRENT_ID);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile, input]);

  const showChanges = selectedScenario && !isCurrent && (
    <p className="text-xs text-[var(--color-muted)] mt-1">
      Changes applied: {selectedScenario.name}
    </p>
  );

  return (
    <div
      className="rounded-2xl p-6 border-2 border-[var(--color-primary)]/40 bg-[var(--color-surface)]/80 shadow-[0_0_28px_rgba(20,184,166,0.12),inset_0_1px_0_rgba(255,255,255,0.04)] hover:border-[var(--color-primary)]/60 transition-all duration-300 relative overflow-hidden"
      role="region"
      aria-label="What if scenarios"
    >
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-[var(--color-primary)] to-[var(--color-primary)]/40 rounded-l-2xl" aria-hidden />

      <div className="pl-4">
        <p className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider mb-3">Compare scenarios</p>
        <div className="flex flex-wrap gap-2 mb-5">
          <button
            type="button"
            onClick={() => handleSelectScenario(CURRENT_ID)}
            className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] ${
              selectedId === CURRENT_ID
                ? "bg-[var(--color-primary)] text-[var(--color-bg)] shadow-[0_0_16px_rgba(20,184,166,0.35)] scale-105"
                : "bg-white/5 text-[var(--color-muted)] hover:bg-white/10 hover:text-[var(--foreground)] hover:scale-[1.02] active:scale-[0.98]"
            }`}
          >
            Current
          </button>
          {WHAT_IF_SCENARIOS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => handleSelectScenario(s.id)}
              disabled={isLoading}
              className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] disabled:opacity-60 ${
                selectedId === s.id
                  ? "bg-[var(--color-primary)] text-[var(--color-bg)] shadow-[0_0_16px_rgba(20,184,166,0.35)] scale-105"
                  : "bg-white/5 text-[var(--color-muted)] hover:bg-white/10 hover:text-[var(--foreground)] hover:scale-[1.02] active:scale-[0.98]"
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-lg bg-red-950/40 border border-red-500/40 px-4 py-3 text-sm text-red-200 mb-4" role="alert">
            {error}
          </div>
        )}

        <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3 transition-opacity duration-200">
          {isLoading && !displaySummary && (
            <p className="text-[var(--color-muted)] text-sm">Loading scenario…</p>
          )}
          {!isLoading && displaySummary && (
            <>
              <p className="text-[var(--foreground)] font-medium leading-relaxed">{displaySummary.message}</p>
              {showChanges}
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[var(--foreground)] font-medium">
                  Bio age {displaySummary.biological_age}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[var(--foreground)] font-medium">
                  Score {displaySummary.health_score}
                </span>
              </div>
            </>
          )}
          {!isLoading && !displaySummary && (
            <p className="text-[var(--color-muted)] text-sm">
              {profile && input ? "Select a scenario to see the projected outcome." : "Complete the assessment to see what-if scenarios."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
