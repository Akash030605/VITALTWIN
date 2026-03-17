"use client";

import { useState, useEffect, useRef } from "react";
import { useStore } from "../../store/useStore";

const CURRENT_ID = "current";

/** Get dummy content for a scenario; can be object or function(profile, input) for input-based tailoring. */
function getDummyContent(scenario, profile, input) {
  const d = scenario.dummy;
  if (typeof d === "function") return d(profile, input);
  return d;
}

// ----- Input helpers (used in showWhen and in dummy functions) -----
function isSmoking(input) {
  const s = (input?.smoking ?? "").toString().trim().toLowerCase();
  return s && s !== "never";
}
function isSmokingDaily(input) {
  return (input?.smoking ?? "").toString().trim().toLowerCase() === "daily";
}
function drinksAlcohol(input) {
  const a = (input?.alcohol ?? "").toString().trim().toLowerCase();
  return a && a !== "never";
}
function needsBetterSleep(input) {
  const h = Number(input?.sleep);
  return Number.isFinite(h) && h < 8;
}
function sleepLessThan7(input) {
  const h = Number(input?.sleep);
  return Number.isFinite(h) && h < 7;
}
function hasHighStress(input) {
  const s = (input?.stress ?? "").toString().trim().toLowerCase();
  return s && s !== "low";
}
function hasVeryHighStress(input) {
  return (input?.stress ?? "").toString().trim().toLowerCase() === "high";
}
function isActive(profile) {
  const a = (profile?.activity ?? "").toString().trim().toLowerCase();
  return a === "active";
}
function isSedentary(profile) {
  return (profile?.activity ?? "").toString().trim().toLowerCase() === "sedentary";
}
function isGoodDiet(profile) {
  const d = (profile?.diet ?? "").toString().trim().toLowerCase();
  return d === "good";
}
function isPoorDiet(profile) {
  const d = (profile?.diet ?? "").toString().trim().toLowerCase();
  return d === "poor" || d === "average";
}

/** 15+ what-if scenarios: visibility and dummy content based on user inputs. All hard-coded. */
const WHAT_IF_SCENARIOS = [
  {
    id: "quit_smoking",
    name: "Quit Smoking",
    showWhen: (_, input) => isSmoking(input),
    dummy: (profile, input) =>
      isSmokingDaily(input)
        ? { message: "If you quit smoking completely, your lungs and heart can recover significantly. You could gain about 3–5 years in biological age and 12–18 points in health score.", years_gained: 4, points_gained: 15, recommendations: ["Set a quit date and use nicotine replacement if needed.", "Avoid alcohol and caffeine in the first weeks; they trigger cravings.", "Tell family and friends so they can support you."] }
        : { message: "If you stop smoking altogether (even occasional), you could gain about 1–3 years in biological age and 6–12 points in health score.", years_gained: 2, points_gained: 9, recommendations: ["Treat occasional urges with a walk or gum.", "Remove cigarettes from home and car.", "Celebrate smoke-free milestones."] },
  },
  {
    id: "reduce_smoking",
    name: "Reduce to Occasional",
    showWhen: (_, input) => isSmokingDaily(input),
    dummy: { message: "If you cut down from daily to occasional smoking, you could gain about 1–2 years in biological age and 4–8 points. Quitting fully would give even more.", years_gained: 1.5, points_gained: 6, recommendations: ["Delay the first cigarette of the day by an hour each week.", "Replace one smoke break with a short walk.", "Consider nicotine gum for cravings."] },
  },
  {
    id: "sleep_8",
    name: "Sleep 8 Hours",
    showWhen: (_, input) => needsBetterSleep(input),
    dummy: (profile, input) => {
      const h = Number(input?.sleep);
      const gap = Number.isFinite(h) && h < 8 ? Math.min(4, 8 - h) : 1;
      const y = gap >= 2 ? 2 : 1;
      const p = gap >= 2 ? 10 : 6;
      return { message: `If you consistently sleep 8 hours (you're at ${h || "?"} now), you could gain about ${y}–${y + 1} years in biological age and ${p}–12 points in health score.`, years_gained: y, points_gained: p, recommendations: ["Fix a bedtime and wake time, including weekends.", "No screens 1 hour before bed; avoid caffeine after 2 p.m.", "Keep the bedroom dark, cool, and quiet."] };
    },
  },
  {
    id: "sleep_7_plus",
    name: "Sleep at Least 7 Hours",
    showWhen: (_, input) => sleepLessThan7(input),
    dummy: { message: "If you get at least 7 hours of sleep most nights, you could gain about 1 year in biological age and 4–8 points. Aim for 8 for even more benefit.", years_gained: 1, points_gained: 6, recommendations: ["Short naps (20 min) can help if you can't get 7h at night.", "Reduce late-night eating and alcohol.", "Try a wind-down routine 30 minutes before bed."] },
  },
  {
    id: "reduce_stress",
    name: "Reduce Stress to Low",
    showWhen: (_, input) => hasHighStress(input),
    dummy: (profile, input) =>
      hasVeryHighStress(input)
        ? { message: "If you bring stress down to a low level, you could gain about 2–3 years in biological age and 10–15 points. High stress affects heart, immunity, and aging.", years_gained: 2.5, points_gained: 12, recommendations: ["Identify top 3 stressors and tackle one at a time.", "Add 10–15 min meditation or breathing daily.", "Consider a therapist or coach for ongoing support."] }
        : { message: "If you reduce stress to low, you could gain about 1–2 years in biological age and 6–10 points in health score.", years_gained: 1.5, points_gained: 8, recommendations: ["Schedule short breaks during the day.", "Practice saying no to nonessential demands.", "Try yoga or walking to unwind."] },
  },
  {
    id: "reduce_stress_medium",
    name: "Reduce Stress to Medium",
    showWhen: (_, input) => hasVeryHighStress(input),
    dummy: { message: "If you lower stress from high to medium, you could gain about 1 year in biological age and 5–8 points. Going to low would add more.", years_gained: 1, points_gained: 6, recommendations: ["Set boundaries at work and home.", "Use a to-do list to reduce mental load.", "Add one relaxing activity per day."] },
  },
  {
    id: "stop_alcohol",
    name: "Stop Alcohol",
    showWhen: (_, input) => drinksAlcohol(input),
    dummy: { message: "If you stop alcohol completely, you could gain about 1.5–3 years in biological age and 8–14 points in health score. Liver and heart benefit most.", years_gained: 2, points_gained: 10, recommendations: ["Replace drinks with sparkling water or non-alcoholic options.", "Avoid situations where you usually drink at first.", "Talk to a doctor if cutting back is difficult."] },
  },
  {
    id: "reduce_alcohol",
    name: "Reduce Alcohol",
    showWhen: (_, input) => drinksAlcohol(input),
    dummy: { message: "If you cut alcohol to occasional or weekly in moderation, you could gain about 0.5–1.5 years in biological age and 4–8 points.", years_gained: 1, points_gained: 6, recommendations: ["Set a limit (e.g. 1 drink per day max) and track it.", "Have alcohol-free days each week.", "Choose smaller servings and alternate with water."] },
  },
  {
    id: "active_lifestyle",
    name: "Become Active",
    showWhen: (profile) => !isActive(profile),
    dummy: { message: "If you become regularly active (150+ min moderate activity per week), you could gain about 2–3 years in biological age and 10–16 points in health score.", years_gained: 2.5, points_gained: 13, recommendations: ["Start with brisk walking 20–30 min most days.", "Add strength training 2x per week.", "Pick activities you enjoy so you stick with them."] },
  },
  {
    id: "moderate_activity",
    name: "Moderate Activity",
    showWhen: (profile) => isSedentary(profile),
    dummy: { message: "If you move from sedentary to moderate activity (e.g. walking, light exercise), you could gain about 1–2 years in biological age and 6–12 points.", years_gained: 1.5, points_gained: 9, recommendations: ["Take the stairs, walk after meals, or do 10-min stretches.", "Aim for 30 minutes of movement most days.", "Use a step counter to track progress."] },
  },
  {
    id: "healthy_diet",
    name: "Healthy Diet",
    showWhen: (profile) => !isGoodDiet(profile),
    dummy: { message: "If you switch to a balanced, nutrient-rich diet, you could gain about 1.5–2.5 years in biological age and 8–14 points in health score.", years_gained: 2, points_gained: 10, recommendations: ["Eat more vegetables, whole grains, and lean protein.", "Limit ultra-processed foods and added sugar.", "Plan meals so you're not relying on fast food."] },
  },
  {
    id: "better_diet",
    name: "Improve Diet (Average → Good)",
    showWhen: (profile) => isPoorDiet(profile),
    dummy: { message: "If you improve your diet from average or poor to good, you could gain about 1–2 years in biological age and 5–10 points.", years_gained: 1.5, points_gained: 7, recommendations: ["Add one extra serving of vegetables per day.", "Swap sugary drinks for water or unsweetened options.", "Cook at home more often."] },
  },
  {
    id: "quit_smoking_sleep_8",
    name: "Quit Smoking + Sleep 8h",
    showWhen: (_, input) => isSmoking(input) && needsBetterSleep(input),
    dummy: { message: "If you quit smoking and get 8 hours of sleep, combined you could gain about 4–6 years in biological age and 18–25 points. These two changes have strong effects.", years_gained: 5, points_gained: 21, recommendations: ["Tackle one change first, then add the other.", "Better sleep can reduce cigarette cravings.", "Track both habits in one app or journal."] },
  },
  {
    id: "stop_alcohol_reduce_stress",
    name: "Stop Alcohol + Reduce Stress",
    showWhen: (_, input) => drinksAlcohol(input) && hasHighStress(input),
    dummy: { message: "If you stop alcohol and reduce stress, you could gain about 3–4 years in biological age and 15–22 points. Both help heart and mental health.", years_gained: 3.5, points_gained: 18, recommendations: ["Replace drinking with a relaxing routine (tea, bath, reading).", "Practice breathing or meditation when stressed.", "Consider counseling if stress or drinking is hard to change alone."] },
  },
  {
    id: "active_healthy_diet",
    name: "Active + Healthy Diet",
    showWhen: (profile) => !isActive(profile) || !isGoodDiet(profile),
    dummy: { message: "If you become active and improve your diet together, you could gain about 3–5 years in biological age and 18–28 points. Synergy is real.", years_gained: 4, points_gained: 22, recommendations: ["Meal prep on weekends so healthy eating is easy.", "Schedule workouts like meetings.", "Reward yourself with non-food treats."] },
  },
  {
    id: "sleep_stress",
    name: "Sleep 8h + Low Stress",
    showWhen: (_, input) => needsBetterSleep(input) && hasHighStress(input),
    dummy: { message: "If you sleep 8 hours and keep stress low, you could gain about 2.5–4 years in biological age and 14–20 points. Sleep helps stress and vice versa.", years_gained: 3, points_gained: 16, recommendations: ["Prioritize a fixed bedtime to improve stress resilience.", "Wind down with reading or stretching, not screens.", "Say no to late-night work or scrolling."] },
  },
  {
    id: "complete_transformation",
    name: "Complete Transformation",
    showWhen: () => true,
    dummy: (profile, input) => {
      const hasRisks = isSmoking(input) || drinksAlcohol(input) || needsBetterSleep(input) || hasHighStress(input) || !isActive(profile) || !isGoodDiet(profile);
      const y = hasRisks ? 6 : 3;
      const p = hasRisks ? 30 : 18;
      return { message: `If you combine all positive changes (no smoking, little/no alcohol, 8h sleep, low stress, active, good diet), you could gain about ${y}–${y + 2} years in biological age and ${p}–40 points.`, years_gained: y, points_gained: p, recommendations: ["Change one habit at a time; don't overwhelm yourself.", "Track progress in one place (app or journal).", "Get a health coach or doctor to support your plan."] };
    },
  },
];

function filterScenariosByInput(scenarios, profile, input) {
  return scenarios.filter((s) => (s.showWhen ? s.showWhen(profile, input) : true));
}

function summarizeReport(report) {
  if (!report || typeof report !== "object") return { biological_age: "—", health_score: "—", message: "—", yearsGained: null, pointsGained: null, recommendations: [], isDummy: false };
  const bio = report.biological_age;
  const score = report.overall_health_score ?? report.vital_score?.current ?? "—";
  const bioNum = typeof bio === "object" ? bio?.biological_age : bio;
  const msg = report.vital_score?.message ?? report.vital_score?.interpretation ?? "—";
  const improvements = report.improvements ?? report.vital_score?.improvements;
  const yearsGained = improvements?.years_gained ?? improvements?.biological_age_reduction ?? null;
  const pointsGained = improvements?.health_score_increase ?? improvements?.points_gained ?? null;
  const recommendations = report.scenario_recommendations ?? report.recommendations ?? [];
  const recList = Array.isArray(recommendations) ? recommendations : [];
  return { biological_age: bioNum ?? "—", health_score: score, message: msg, yearsGained, pointsGained, recommendations: recList, isDummy: !!report.isDummy };
}

/** Build a report-shaped object from scenario dummy content + current result. */
function buildWhatIfReportFromDummy(scenario, currentReport, profile, input) {
  const dummy = getDummyContent(scenario, profile, input);
  if (!dummy) return null;
  const currentBio = typeof currentReport?.biological_age === "object" ? currentReport.biological_age?.biological_age : currentReport?.biological_age;
  const currentScore = currentReport?.overall_health_score ?? currentReport?.vital_score?.current ?? 70;
  const bioNum = typeof currentBio === "number" && dummy.years_gained != null ? Math.max(18, Math.round((currentBio - dummy.years_gained) * 10) / 10) : currentBio ?? "—";
  const scoreNum = typeof currentScore === "number" && dummy.points_gained != null ? Math.min(100, Math.round(currentScore + dummy.points_gained)) : currentScore ?? "—";
  return {
    ...(typeof currentReport === "object" && currentReport ? currentReport : {}),
    biological_age: bioNum,
    overall_health_score: scoreNum,
    vital_score: { message: dummy.message, current: scoreNum },
    improvements: { years_gained: dummy.years_gained, health_score_increase: dummy.points_gained },
    scenario_recommendations: dummy.recommendations ?? [],
    isDummy: true,
  };
}

export default function WhatIfPanel({ what_if_simulations }) {
  const profile = useStore((s) => s.profile);
  const input = useStore((s) => s.input);
  const result = useStore((s) => s.result);

  const [selectedId, setSelectedId] = useState(CURRENT_ID);
  const [scenarioResults, setScenarioResults] = useState({});
  const [error, setError] = useState(null);

  const visibleScenarios = filterScenariosByInput(WHAT_IF_SCENARIOS, profile ?? {}, input ?? {});
  const isCurrent = selectedId === CURRENT_ID;
  const selectedScenario = isCurrent ? null : WHAT_IF_SCENARIOS.find((s) => s.id === selectedId);

  // All what-if outcomes are hard-coded dummy data based on user inputs (no API).
  const getDisplayData = (id) => {
    if (id === CURRENT_ID) return result ?? null;
    const scenario = WHAT_IF_SCENARIOS.find((s) => s.id === id);
    if (!scenario) return null;
    return buildWhatIfReportFromDummy(scenario, result ?? {}, profile ?? {}, input ?? {});
  };

  const cachedData = scenarioResults[selectedId] ?? null;
  const displayData = cachedData != null ? cachedData : getDisplayData(selectedId);
  const displaySummary = displayData ? summarizeReport(displayData) : null;

  const handleSelectScenario = (id) => {
    setSelectedId(id);
    setError(null);
    const existing = scenarioResults[id];
    if (existing != null) return;
    if (id === CURRENT_ID) {
      if (result != null) setScenarioResults((prev) => ({ ...prev, [CURRENT_ID]: result }));
      return;
    }
    const scenario = WHAT_IF_SCENARIOS.find((s) => s.id === id);
    if (scenario) {
      const data = buildWhatIfReportFromDummy(scenario, result ?? {}, profile ?? {}, input ?? {});
      if (data) setScenarioResults((prev) => ({ ...prev, [id]: data }));
    }
  };

  // Prefill "Current" when we have a result so the panel shows something immediately.
  useEffect(() => {
    if (result && profile && input && scenarioResults[CURRENT_ID] == null) {
      setScenarioResults((prev) => ({ ...prev, [CURRENT_ID]: result }));
    }
  }, [result, profile, input]);

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
          {visibleScenarios.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => handleSelectScenario(s.id)}
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
          {displaySummary && (
            <>
              <p className="text-[var(--foreground)] font-medium leading-relaxed">{displaySummary.message}</p>
              {(displaySummary.yearsGained != null || displaySummary.pointsGained != null) && (
                <p className="text-sm text-[var(--color-primary)] font-medium">
                  {displaySummary.yearsGained != null && <>Gain {displaySummary.yearsGained} year{Number(displaySummary.yearsGained) !== 1 ? "s" : ""} back</>}
                  {displaySummary.yearsGained != null && displaySummary.pointsGained != null && " · "}
                  {displaySummary.pointsGained != null && <>+{displaySummary.pointsGained} points</>}
                </p>
              )}
              {showChanges}
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[var(--foreground)] font-medium">
                  Bio age {displaySummary.biological_age}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[var(--foreground)] font-medium">
                  Score {displaySummary.health_score}
                </span>
              </div>
              {displaySummary.recommendations?.length > 0 && (
                <div className="pt-2 border-t border-white/10">
                  <p className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-2">Recommendations</p>
                  <ul className="space-y-1.5 text-sm text-[var(--foreground)]">
                    {displaySummary.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-[var(--color-primary)] mt-0.5">•</span>
                        <span>{typeof rec === "string" ? rec : rec?.text ?? rec?.message ?? String(rec)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
          {!displaySummary && (
            <p className="text-[var(--color-muted)] text-sm">
              {profile && input ? "Select a scenario to see the projected outcome." : "Complete the assessment to see what-if scenarios."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
