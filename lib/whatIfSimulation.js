/**
 * Derive what-if report from the user's actual report.
 * No backend call: we simulate scenario outcomes by adjusting scores, bio age, organs, stress, etc.
 */

function deepClone(obj) {
  if (obj == null || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj.map(deepClone);
  const out = {};
  for (const k of Object.keys(obj)) out[k] = deepClone(obj[k]);
  return out;
}

function clamp(num, min, max) {
  if (typeof num !== "number" || Number.isNaN(num)) return min;
  return Math.min(max, Math.max(min, num));
}

function round1(v) {
  return typeof v === "number" && !Number.isNaN(v) ? Math.round(v * 10) / 10 : v;
}

/** Scenario id -> { scoreDelta, bioAgeDelta, message, organImprovements, stressImprovements } */
const SCENARIO_EFFECTS = {
  quit_smoking: {
    scoreDelta: 5,
    bioAgeDelta: -1,
    message: "Quitting smoking would improve your lung and heart health and lower overall risk.",
    organs: ["lungs", "heart"],
    systems: ["cardiovascular"],
    heatmapOrgans: ["lungs", "heart"],
  },
  sleep_8: {
    scoreDelta: 4,
    bioAgeDelta: -1,
    message: "Consistent 8 hours of sleep would support brain health and reduce sleep debt.",
    organs: ["brain"],
    systems: ["sleep_debt"],
    heatmapOrgans: ["brain"],
  },
  reduce_stress: {
    scoreDelta: 3,
    bioAgeDelta: -1,
    message: "Lower stress would benefit your heart and brain and slow biological aging.",
    organs: ["heart", "brain"],
    systems: ["cardiovascular"],
    heatmapOrgans: ["heart", "brain"],
  },
  stop_alcohol: {
    scoreDelta: 4,
    bioAgeDelta: -1,
    message: "Stopping alcohol would improve liver health and reduce metabolic stress.",
    organs: ["liver"],
    systems: ["metabolic", "lifestyle"],
    heatmapOrgans: ["liver"],
  },
  active_lifestyle: {
    scoreDelta: 6,
    bioAgeDelta: -2,
    message: "Regular activity would boost cardiovascular and metabolic health and vitality.",
    organs: ["heart", "liver", "lungs"],
    systems: ["cardiovascular", "metabolic", "lifestyle"],
    heatmapOrgans: ["heart", "liver", "lungs"],
  },
  healthy_diet: {
    scoreDelta: 5,
    bioAgeDelta: -2,
    message: "A healthier diet would improve metabolic health and organ resilience.",
    organs: ["liver", "kidney", "heart"],
    systems: ["metabolic"],
    heatmapOrgans: ["liver", "kidney", "heart"],
  },
  complete_transformation: {
    scoreDelta: 14,
    bioAgeDelta: -4,
    message: "Combining all positive changes would significantly improve your vitality and biological age.",
    organs: ["heart", "brain", "liver", "kidney", "lungs"],
    systems: ["cardiovascular", "metabolic", "sleep_debt", "lifestyle"],
    heatmapOrgans: ["heart", "brain", "liver", "kidney", "lungs"],
  },
};

function getBaseScore(report) {
  const v = report?.overall_health_score ?? report?.vital_score?.current;
  return typeof v === "number" && !Number.isNaN(v) ? v : 70;
}

function getBaseBioAge(report) {
  const bio = report?.biological_age;
  const num = typeof bio === "object" ? bio?.biological_age : bio;
  return typeof num === "number" && !Number.isNaN(num) ? num : 30;
}

function improveOrgan(organData, factor) {
  if (!organData || typeof organData !== "object") return organData;
  const out = { ...organData };
  if (typeof organData.health_score === "number") {
    out.health_score = clamp(Math.round(organData.health_score + (100 - organData.health_score) * factor), 0, 100);
  }
  if (typeof organData.current_risk === "number") {
    out.current_risk = round1(clamp(organData.current_risk * (1 - factor), 0, 1));
  }
  if (organData.risk_level && ["RED", "YELLOW"].includes(organData.risk_level)) {
    out.risk_level = factor >= 0.5 ? "GREEN" : "YELLOW";
  }
  if (Array.isArray(organData.recommendations) && organData.recommendations.length > 0) {
    out.recommendations = organData.recommendations.slice(0, -1);
  }
  return out;
}

function improveSystem(systemData, factor) {
  if (!systemData || typeof systemData !== "object") return systemData;
  const out = { ...systemData };
  if (typeof systemData.stress === "number") {
    out.stress = round1(clamp(systemData.stress * (1 - factor), 0, 1));
  }
  if (systemData.level && systemData.level !== "LOW") {
    out.level = factor >= 0.5 ? "LOW" : systemData.level;
  }
  if (systemData.color && systemData.color !== "GREEN") {
    out.color = factor >= 0.5 ? "GREEN" : systemData.color;
  }
  return out;
}

/**
 * Returns a full report-shaped object for the given scenario, derived from the user's report.
 * @param {object} report - The main report from /predict (or stored result).
 * @param {string} scenarioId - e.g. "current", "quit_smoking", "stop_alcohol", "complete_transformation".
 * @returns {object} Report-like object with vital_score, biological_age, body_stress, organs, future_self, etc.
 */
export function deriveWhatIfReport(report, scenarioId) {
  if (!report || typeof report !== "object") return report;
  if (!scenarioId || scenarioId === "current") return deepClone(report);

  const effect = SCENARIO_EFFECTS[scenarioId];
  if (!effect) return deepClone(report);

  const out = deepClone(report);
  const baseScore = getBaseScore(report);
  const baseBio = getBaseBioAge(report);
  const score = clamp(baseScore + effect.scoreDelta, 0, 100);
  const bioAge = Math.max(0, baseBio + effect.bioAgeDelta);
  const factor = Math.min(1, (effect.scoreDelta + effect.bioAgeDelta * 2) / 20);

  out.overall_health_score = score;

  if (out.vital_score && typeof out.vital_score === "object") {
    out.vital_score = { ...out.vital_score, current: score };
    if (effect.message) {
      out.vital_score.message = effect.message;
      out.vital_score.interpretation = effect.message;
    }
    if (out.vital_score.gauge && typeof out.vital_score.gauge === "object") {
      out.vital_score.gauge = {
        ...out.vital_score.gauge,
        value: score,
        needle: out.vital_score.gauge.needle ? { ...out.vital_score.gauge.needle, value: score } : { value: score, color: "#333333" },
      };
      if (out.vital_score.gauge.current_segment) {
        const label = score >= 80 ? "Good" : score >= 50 ? "Fair" : "Critical";
        const color = score >= 80 ? "#4CAF50" : score >= 50 ? "#FFC107" : "#F44336";
        out.vital_score.gauge.current_segment = { label, color };
      }
    }
    if (out.vital_score.category) {
      out.vital_score.category = score >= 80 ? "Excellent" : score >= 50 ? "Fair" : "Critical";
    }
    if (out.vital_score.color) {
      out.vital_score.color = score >= 80 ? "GREEN" : score >= 50 ? "YELLOW" : "RED";
    }
  }

  if (out.biological_age) {
    const bio = typeof out.biological_age === "object" ? { ...out.biological_age } : { biological_age: out.biological_age, real_age: 0, age_gap: 0, gap_level: "GREEN", message: "", factors: [] };
    bio.biological_age = bioAge;
    if (typeof bio.real_age === "number") {
      bio.age_gap = bioAge - bio.real_age;
      bio.gap_level = bio.age_gap <= 0 ? "GREEN" : bio.age_gap <= 3 ? "YELLOW" : "RED";
    }
    if (effect.message) bio.message = `✅ ${effect.message}`;
    out.biological_age = bio;
  }

  if (out.body_stress && typeof out.body_stress === "object") {
    out.body_stress = { ...out.body_stress };
    if (typeof out.body_stress.overall_stress === "number") {
      out.body_stress.overall_stress = round1(clamp(out.body_stress.overall_stress * (1 - factor * 0.5), 0, 1));
    }
    if (out.body_stress.overall_level && out.body_stress.overall_level !== "LOW") {
      out.body_stress.overall_level = factor >= 0.6 ? "LOW" : out.body_stress.overall_level;
    }
    if (out.body_stress.systems && typeof out.body_stress.systems === "object") {
      const systems = { ...out.body_stress.systems };
      for (const sys of effect.systems || []) {
        if (systems[sys]) systems[sys] = improveSystem(systems[sys], factor);
      }
      out.body_stress.systems = systems;
    }
    if (Array.isArray(out.body_stress.heatmap_zones)) {
      out.body_stress.heatmap_zones = out.body_stress.heatmap_zones.map((z) => {
        if (!effect.heatmapOrgans || !effect.heatmapOrgans.includes(z.organ)) return z;
        return {
          ...z,
          strain: round1(clamp((z.strain || 0) * (1 - factor), 0, 1)),
          color: "GREEN",
          intensity: Math.max(0, (z.intensity || 0.3) - factor * 0.2),
        };
      });
    }
  }

  if (out.organs && typeof out.organs === "object") {
    const organs = { ...out.organs };
    const organKeys = ["heart", "brain", "liver", "kidney", "kidneys", "lungs"];
    for (const key of organKeys) {
      const organId = key === "kidneys" ? "kidney" : key;
      if (organs[organId] && effect.organs && effect.organs.includes(organId)) {
        organs[organId] = improveOrgan(organs[organId], factor);
      }
    }
    if (organs.kidneys && !organs.kidney) {
      if (effect.organs && effect.organs.includes("kidney")) {
        organs.kidney = improveOrgan(organs.kidneys, factor);
      }
    }
    out.organs = organs;
  }

  if (out.future_self && out.future_self.timeline && Array.isArray(out.future_self.timeline)) {
    out.future_self = {
      ...out.future_self,
      timeline: out.future_self.timeline.map((t) => ({
        ...t,
        vitality_score: typeof t.vitality_score === "number" ? clamp(t.vitality_score + effect.scoreDelta * 0.5, 0, 100) : t.vitality_score,
        biological_age: typeof t.biological_age === "number" ? Math.max(0, t.biological_age + effect.bioAgeDelta * 0.3) : t.biological_age,
        organ_status: typeof t.organ_status === "object" && t.organ_status
          ? Object.fromEntries(
              Object.entries(t.organ_status).map(([organ, status]) => [
                organ,
                effect.organs && effect.organs.includes(organ) && status !== "GREEN" ? "GREEN" : status,
              ])
            )
          : t.organ_status,
      })),
    };
    if (out.future_self.overall_trajectory === "declining_rapidly" && effect.scoreDelta >= 10) {
      out.future_self.overall_trajectory = "improving";
    } else if (out.future_self.overall_trajectory === "declining" && effect.scoreDelta >= 6) {
      out.future_self.overall_trajectory = "stable";
    }
  }

  if (Array.isArray(out.priority_recommendations) && out.priority_recommendations.length > 0 && factor >= 0.5) {
    out.priority_recommendations = out.priority_recommendations.slice(0, Math.max(0, out.priority_recommendations.length - 2));
  }

  return out;
}
