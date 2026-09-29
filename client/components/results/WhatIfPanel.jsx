"use client";

import { useState, useEffect } from "react";
import { useStore } from "../../store/useStore";
import { fetchWhatIfScenario } from "../../lib/api";

const CURRENT_ID = "current";

// ── Input helpers (visibility only — no dummy values) ─────────────────────────
const isSmoking = (input) => { const s = (input?.smoking ?? "").toLowerCase().trim(); return s && s !== "never"; };
const isSmokingDaily = (input) => (input?.smoking ?? "").toLowerCase().trim() === "daily";
const drinksAlcohol = (input) => { const a = (input?.alcohol ?? "").toLowerCase().trim(); return a && a !== "never"; };
const needsBetterSleep = (input) => { const h = Number(input?.sleep); return Number.isFinite(h) && h < 8; };
const sleepLessThan7 = (input) => { const h = Number(input?.sleep); return Number.isFinite(h) && h < 7; };
const hasHighStress = (input) => { const s = (input?.stress ?? "").toLowerCase().trim(); return s && s !== "low"; };
const hasVeryHighStress = (input) => (input?.stress ?? "").toLowerCase().trim() === "high";
const isActive = (profile) => (profile?.activity ?? "").toLowerCase().trim() === "active";
const isSedentary = (profile) => (profile?.activity ?? "").toLowerCase().trim() === "sedentary";
const isGoodDiet = (profile) => (profile?.diet ?? "").toLowerCase().trim() === "good";
const isPoorDiet = (profile) => { const d = (profile?.diet ?? "").toLowerCase().trim(); return d === "poor" || d === "average"; };

// ── Scenario definitions: id, name, showWhen, changes sent to API ─────────────
const WHAT_IF_SCENARIOS = [
  { id: "quit_smoking",              name: "Quit Smoking",              showWhen: (_, i) => isSmoking(i),                                          changes: { HealthInfo: { Smoking: "Never" } } },
  { id: "reduce_smoking",            name: "Reduce to Occasional",      showWhen: (_, i) => isSmokingDaily(i),                                     changes: { HealthInfo: { Smoking: "Occasional" } } },
  { id: "sleep_8",                   name: "Sleep 8 Hours",             showWhen: (_, i) => needsBetterSleep(i),                                   changes: { HealthInfo: { Sleep: 8 } } },
  { id: "sleep_7_plus",              name: "Sleep at Least 7 Hours",    showWhen: (_, i) => sleepLessThan7(i),                                     changes: { HealthInfo: { Sleep: 7 } } },
  { id: "reduce_stress",             name: "Reduce Stress to Low",      showWhen: (_, i) => hasHighStress(i),                                      changes: { HealthInfo: { Stress: "Low" } } },
  { id: "reduce_stress_medium",      name: "Reduce Stress to Medium",   showWhen: (_, i) => hasVeryHighStress(i),                                  changes: { HealthInfo: { Stress: "Medium" } } },
  { id: "stop_alcohol",              name: "Stop Alcohol",              showWhen: (_, i) => drinksAlcohol(i),                                      changes: { HealthInfo: { Alcohol: "Never" } } },
  { id: "reduce_alcohol",            name: "Reduce Alcohol",            showWhen: (_, i) => drinksAlcohol(i),                                      changes: { HealthInfo: { Alcohol: "Occasional" } } },
  { id: "active_lifestyle",          name: "Become Active",             showWhen: (p) => !isActive(p),                                             changes: { ProfileInfo: { ActivityLevel: "Active" } } },
  { id: "moderate_activity",         name: "Moderate Activity",         showWhen: (p) => isSedentary(p),                                           changes: { ProfileInfo: { ActivityLevel: "Moderate" } } },
  { id: "healthy_diet",              name: "Healthy Diet",              showWhen: (p) => !isGoodDiet(p),                                           changes: { ProfileInfo: { Diet: "Good" } } },
  { id: "better_diet",               name: "Improve Diet",              showWhen: (p) => isPoorDiet(p),                                            changes: { ProfileInfo: { Diet: "Average" } } },
  { id: "quit_smoking_sleep_8",      name: "Quit Smoking + Sleep 8h",   showWhen: (_, i) => isSmoking(i) && needsBetterSleep(i),                   changes: { HealthInfo: { Smoking: "Never", Sleep: 8 } } },
  { id: "stop_alcohol_reduce_stress",name: "Stop Alcohol + Low Stress", showWhen: (_, i) => drinksAlcohol(i) && hasHighStress(i),                  changes: { HealthInfo: { Alcohol: "Never", Stress: "Low" } } },
  { id: "active_healthy_diet",       name: "Active + Healthy Diet",     showWhen: (p) => !isActive(p) || !isGoodDiet(p),                           changes: { ProfileInfo: { ActivityLevel: "Active", Diet: "Good" } } },
  { id: "sleep_stress",              name: "Sleep 8h + Low Stress",     showWhen: (_, i) => needsBetterSleep(i) && hasHighStress(i),               changes: { HealthInfo: { Sleep: 8, Stress: "Low" } } },
  { id: "complete_transformation",   name: "Complete Transformation",   showWhen: () => true,                                                      changes: { ProfileInfo: { ActivityLevel: "Active", Diet: "Good" }, HealthInfo: { Smoking: "Never", Alcohol: "Never", Sleep: 8, Stress: "Low" } } },
];

function summarizeReport(report) {
  if (!report || typeof report !== "object") return null;
  const bio = report.biological_age;
  const score = report.overall_health_score ?? report.vital_score?.current ?? "—";
  const bioNum = typeof bio === "object" ? bio?.biological_age : bio;
  const msg = report.vital_score?.message ?? report.vital_score?.interpretation ?? "—";
  const improvements = report.improvements ?? report.vital_score?.improvements;
  const yearsGained = improvements?.years_gained ?? improvements?.biological_age_reduction ?? null;
  const pointsGained = improvements?.health_score_increase ?? improvements?.points_gained ?? null;
  const recs = report.scenario_recommendations ?? report.recommendations ?? [];
  return {
    biological_age: bioNum ?? "—",
    health_score: score,
    message: msg,
    yearsGained,
    pointsGained,
    recommendations: Array.isArray(recs) ? recs : [],
  };
}

export default function WhatIfPanel() {
  const profile = useStore((s) => s.profile);
  const input = useStore((s) => s.input);
  const result = useStore((s) => s.result);

  const [selectedId, setSelectedId] = useState(CURRENT_ID);
  const [scenarioResults, setScenarioResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Pre-fill "Current" immediately when result is available
  useEffect(() => {
    if (result && scenarioResults[CURRENT_ID] == null) {
      setScenarioResults((prev) => ({ ...prev, [CURRENT_ID]: result }));
    }
  }, [result]);

  const visibleScenarios = WHAT_IF_SCENARIOS.filter((s) => s.showWhen(profile ?? {}, input ?? {}));

  const handleSelectScenario = async (id) => {
    if (id === selectedId) return;
    setSelectedId(id);
    setError(null);

    // Current — use cached result
    if (id === CURRENT_ID) {
      if (!scenarioResults[CURRENT_ID] && result) {
        setScenarioResults((prev) => ({ ...prev, [CURRENT_ID]: result }));
      }
      return;
    }

    // Already fetched — use cache
    if (scenarioResults[id] != null) return;

    const scenario = WHAT_IF_SCENARIOS.find((s) => s.id === id);
    if (!scenario) return;

    setLoading(true);
    try {
      const data = await fetchWhatIfScenario(profile, input, scenario.changes, {
        currentReport: result,
        scenarioId: id,
      });
      setScenarioResults((prev) => ({ ...prev, [id]: data }));
    } catch (err) {
      setError(err?.message || "Failed to load scenario. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const displayData = scenarioResults[selectedId] ?? (selectedId === CURRENT_ID ? result : null);
  const displaySummary = displayData ? summarizeReport(displayData) : null;

  return (
    <div
      className="rounded-2xl p-6 border-2 border-(--color-primary)/40 bg-(--color-surface)/80 shadow-[0_0_28px_rgba(20,184,166,0.12),inset_0_1px_0_rgba(255,255,255,0.04)] hover:border-(--color-primary)/60 transition-all duration-300 relative overflow-hidden"
      role="region"
      aria-label="What if scenarios"
    >
      <div className="absolute top-0 left-0 w-1 h-full bg-linear-to-b from-(--color-primary) to-(--color-primary)/40 rounded-l-2xl" aria-hidden />

      <div className="pl-4">
        <p className="text-xs font-semibold text-(--color-primary) uppercase tracking-wider mb-3">Compare scenarios</p>

        <div className="flex flex-wrap gap-2 mb-5">
          {/* Current button */}
          <button
            type="button"
            onClick={() => handleSelectScenario(CURRENT_ID)}
            className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-(--color-primary) focus:ring-offset-2 focus:ring-offset-(--color-bg) ${
              selectedId === CURRENT_ID
                ? "bg-(--color-primary) text-(--color-bg) shadow-[0_0_16px_rgba(20,184,166,0.35)] scale-105"
                : "bg-slate-100 text-(--color-muted) hover:bg-emerald-50 hover:text-foreground hover:border-emerald-200 hover:scale-[1.02] active:scale-[0.98]"
            }`}
          >
            Current
          </button>

          {/* Scenario buttons */}
          {visibleScenarios.map((s) => {
            const isSelected = selectedId === s.id;
            const isLoading = loading && selectedId === s.id;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => handleSelectScenario(s.id)}
                disabled={isLoading}
                className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-(--color-primary) focus:ring-offset-2 focus:ring-offset-white disabled:opacity-60 ${
                  isSelected
                    ? "bg-(--color-primary) text-white shadow-md shadow-emerald-200 scale-105"
                    : "bg-slate-100 text-(--color-muted) hover:bg-emerald-50 hover:text-foreground hover:scale-[1.02] active:scale-[0.98]"
                }`}
              >
                {s.name}
              </button>
            );
          })}
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600 mb-4" role="alert">
            {error}
          </div>
        )}

        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 space-y-3 min-h-20 transition-opacity duration-200">
          {loading ? (
            <div className="flex items-center gap-3 py-2">
              <svg className="w-4 h-4 animate-spin text-(--color-primary) shrink-0" fill="none" viewBox="0 0 24 24" aria-hidden>
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <p className="text-sm text-(--color-muted)">Calculating scenario with AI…</p>
            </div>
          ) : displaySummary ? (
            <>
              <p className="text-foreground font-medium leading-relaxed">{displaySummary.message}</p>

              {(displaySummary.yearsGained != null || displaySummary.pointsGained != null) && (
                <p className="text-sm text-(--color-primary) font-medium">
                  {displaySummary.yearsGained != null && <>Gain {displaySummary.yearsGained} year{Number(displaySummary.yearsGained) !== 1 ? "s" : ""} back</>}
                  {displaySummary.yearsGained != null && displaySummary.pointsGained != null && " · "}
                  {displaySummary.pointsGained != null && <>+{displaySummary.pointsGained} points</>}
                </p>
              )}

              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-foreground font-medium">
                  Bio age {displaySummary.biological_age}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-foreground font-medium">
                  Score {displaySummary.health_score}
                </span>
              </div>

              {displaySummary.recommendations.length > 0 && (
                <div className="pt-2 border-t border-slate-200">
                  <p className="text-xs font-semibold text-(--color-muted) uppercase tracking-wider mb-2">Recommendations</p>
                  <ul className="space-y-1.5 text-sm text-foreground">
                    {displaySummary.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-(--color-primary) mt-0.5">•</span>
                        <span>{typeof rec === "string" ? rec : rec?.text ?? rec?.message ?? String(rec)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p className="text-(--color-muted) text-sm">
              {profile && input ? "Select a scenario to see the AI-projected outcome." : "Complete the assessment to see what-if scenarios."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
