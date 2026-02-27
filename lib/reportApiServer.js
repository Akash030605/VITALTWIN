/**
 * Server-only helpers for report and what-if API routes.
 * Uses process.env; do not import in client components.
 */

const REPORT_API_ENV =
  (typeof process !== "undefined" && (process.env.REPORT_API_URL?.trim() || process.env.NEXT_PUBLIC_REPORT_API_URL?.trim())) || null;

export function getLlmBaseUrl() {
  if (!REPORT_API_ENV) return null;
  const url = REPORT_API_ENV.replace(/\/$/, "");
  if (/\/predict\/?$/i.test(url)) return url.replace(/\/predict\/?$/i, "");
  return url;
}

export function getPredictUrl() {
  if (!REPORT_API_ENV) return null;
  const url = REPORT_API_ENV.replace(/\/$/, "");
  if (/\/predict\/?$/i.test(url)) return url.replace(/predict\/?$/i, "predict");
  const base = getLlmBaseUrl();
  const p = typeof process !== "undefined" && process.env.REPORT_API_PREDICT_PATH?.trim();
  const path = p ? (p.startsWith("/") ? p : `/${p}`) : "/predict";
  return `${base}${path}`;
}

export function getWhatIfPath() {
  const p = typeof process !== "undefined" && process.env.REPORT_API_WHATIF_PATH?.trim();
  return p ? (p.startsWith("/") ? p : `/${p}`) : "/what-if";
}

export function getWhatIfUrl() {
  const full = typeof process !== "undefined" && process.env.REPORT_API_WHATIF_URL?.trim();
  if (full) return full.replace(/\/$/, "");
  const base = getLlmBaseUrl();
  if (!base) return null;
  return `${base}${getWhatIfPath()}`;
}

/** When REPORT_API_WHATIF_URL is not set, use predict URL so backend only needs /predict. */
export function getWhatIfTargetUrl() {
  const dedicated = typeof process !== "undefined" && process.env.REPORT_API_WHATIF_URL?.trim();
  if (dedicated) return { url: dedicated.replace(/\/$/, ""), usePredict: false };
  const predictUrl = getPredictUrl();
  if (predictUrl) return { url: predictUrl, usePredict: true };
  return null;
}

/** Merge what-if changes into predict payload. For use when calling /predict as what-if fallback. */
export function mergeWhatIfIntoPredictPayload(payload, changes) {
  const c = typeof changes === "object" && changes !== null ? changes : {};
  return {
    ProfileInfo: { ...(payload?.ProfileInfo || {}), ...(c.ProfileInfo || {}) },
    HealthInfo: { ...(payload?.HealthInfo || {}), ...(c.HealthInfo || {}) },
  };
}

export function llmHeaders() {
  const base = getLlmBaseUrl();
  const headers = { "Content-Type": "application/json" };
  if (base && base.includes("ngrok")) {
    headers["ngrok-skip-browser-warning"] = "true";
  }
  return headers;
}

export function toPredictPayload(profile = {}, input = {}) {
  const numOr = (v, fallback) => (v === "" || v == null ? fallback : Number(v));
  const strOr = (v, fallback) => (v === "" || v == null ? fallback : String(v).trim() || fallback);
  const dietMap = { poor: "Poor", average: "Average", good: "Good" };
  const activityMap = { sedentary: "Sedentary", moderate: "Moderate", active: "Active" };

  const Height = numOr(profile.height, 170);
  const Weight = numOr(profile.weight, 70);

  const ProfileInfo = {
    Userid: strOr(profile.name, ""),
    Age: numOr(profile.age, 25),
    Gender: strOr(profile.gender, "Male"),
    Height,
    Weight,
    Diet: dietMap[String(profile.diet || "").toLowerCase()] || strOr(profile.diet, "Average"),
    ActivityLevel: activityMap[String(profile.activity || "").toLowerCase()] || strOr(profile.activity, "Moderate"),
  };

  const heightM = Height / 100;
  const Bmi = heightM > 0 ? Math.round((Weight / (heightM * heightM)) * 10) / 10 : null;

  const HealthInfo = {
    Smoking: strOr(input.smoking, "Never"),
    Alcohol: strOr(input.alcohol, "Never"),
    Sleep: numOr(input.sleep, 7),
    Stress: strOr(input.stress, "Low"),
    MedicalConditions: Array.isArray(input.medical_conditions) ? input.medical_conditions.filter(Boolean) : [],
    ...(Bmi != null && { Bmi }),
  };

  return { ProfileInfo, HealthInfo };
}
