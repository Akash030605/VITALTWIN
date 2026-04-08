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

/**
 * Map frontend store fields → Python backend ProfileInfo + HealthInfo schema.
 *
 * profile fields: name, age, gender, height, weight, diet, activity,
 *                 city (new)
 * input fields:   smoking, alcohol, sleep, stress, medical_conditions[],
 *                 medications[],
 *                 -- Clinical labs (all optional, improve accuracy significantly) --
 *                 tobaccoType, yearsSmoking, cigarettesPerDay, cookingFuel,
 *                 systolicBp, diastolicBp, bpOnMedication, familyHistoryHeart,
 *                 familyHistoryDiabetes, familyHistoryKidney,
 *                 totalCholesterol, hdlCholesterol, ldlCholesterol, triglycerides,
 *                 fastingGlucose, hbA1c,
 *                 serumCreatinine, ast, alt, ggt, albumin, platelets,
 *                 fev1Percent
 */
export function toPredictPayload(profile = {}, input = {}) {
  const numOr = (v, fallback) => (v === "" || v == null ? fallback : Number(v));
  const strOr = (v, fallback) => (v === "" || v == null ? fallback : String(v).trim() || fallback);
  const boolOr = (v, fallback) => (v == null ? fallback : Boolean(v));
  const optNum = (v) => (v === "" || v == null ? undefined : Number(v));
  const optStr = (v) => (v === "" || v == null ? undefined : String(v).trim() || undefined);

  const dietMap     = { poor: "Poor", average: "Average", good: "Good", excellent: "Excellent" };
  const activityMap = { sedentary: "Sedentary", light: "Light", moderate: "Moderate", active: "Active", "very active": "Very Active" };

  const Height = numOr(profile.height, 170);
  const Weight = numOr(profile.weight, 70);

  const ProfileInfo = {
    Userid:        strOr(profile.name, ""),
    Age:           numOr(profile.age, 25),
    Gender:        strOr(profile.gender, "Male"),
    Height,
    Weight,
    Diet:          dietMap[String(profile.diet || "").toLowerCase()] || strOr(profile.diet, "Average"),
    ActivityLevel: activityMap[String(profile.activity || "").toLowerCase()] || strOr(profile.activity, "Moderate"),
    ...(profile.city ? { City: profile.city } : {}),
  };

  const heightM = Height / 100;
  const Bmi = heightM > 0 ? Math.round((Weight / (heightM * heightM)) * 10) / 10 : null;

  // ── Core lifestyle (always present) ────────────────────────────────────────
  const HealthInfo = {
    Smoking:           strOr(input.smoking, "Never"),
    Alcohol:           strOr(input.alcohol, "Never"),
    Sleep:             numOr(input.sleep, 7),
    Stress:            strOr(input.stress, "Low"),
    MedicalConditions: Array.isArray(input.medical_conditions) ? input.medical_conditions.filter(Boolean) : [],
    Medications:       Array.isArray(input.medications)         ? input.medications.filter(Boolean)         : [],
    ...(Bmi != null ? { Bmi } : {}),
  };

  // ── Tobacco detail ──────────────────────────────────────────────────────────
  const tobaccoType    = optStr(input.tobaccoType);
  const yearsSmoking   = optNum(input.yearsSmoking);
  const cigarettesPerDay = optNum(input.cigarettesPerDay);
  if (tobaccoType)      HealthInfo.TobaccoType      = tobaccoType;
  if (yearsSmoking != null)    HealthInfo.YearsSmoking    = yearsSmoking;
  if (cigarettesPerDay != null) HealthInfo.CigarettesPerDay = cigarettesPerDay;

  // Bidi-corrected pack-years (frontend pre-computes for display; backend also recomputes)
  if (yearsSmoking != null && cigarettesPerDay != null) {
    const bidiMult = tobaccoType === "bidi" ? 1.5 : 1.0;
    HealthInfo.PackYears = Math.round((cigarettesPerDay / 20) * yearsSmoking * bidiMult * 10) / 10;
  }

  // ── Environment ─────────────────────────────────────────────────────────────
  const cookingFuel = optStr(input.cookingFuel);
  if (cookingFuel) HealthInfo.CookingFuel = cookingFuel;

  // ── Blood pressure ───────────────────────────────────────────────────────────
  const systolicBp  = optNum(input.systolicBp);
  const diastolicBp = optNum(input.diastolicBp);
  if (systolicBp  != null) HealthInfo.SystolicBP  = systolicBp;
  if (diastolicBp != null) HealthInfo.DiastolicBP = diastolicBp;
  if (input.bpOnMedication != null) HealthInfo.BPOnMedication = boolOr(input.bpOnMedication, false);

  // ── Family history ───────────────────────────────────────────────────────────
  if (input.familyHistoryHeart    != null) HealthInfo.FamilyHistoryHeart    = boolOr(input.familyHistoryHeart, false);
  if (input.familyHistoryDiabetes != null) HealthInfo.FamilyHistoryDiabetes = boolOr(input.familyHistoryDiabetes, false);
  if (input.familyHistoryKidney   != null) HealthInfo.FamilyHistoryKidney   = boolOr(input.familyHistoryKidney, false);

  // ── Lipid panel ─────────────────────────────────────────────────────────────
  const totalCholesterol = optNum(input.totalCholesterol);
  const hdlCholesterol   = optNum(input.hdlCholesterol);
  const ldlCholesterol   = optNum(input.ldlCholesterol);
  const triglycerides    = optNum(input.triglycerides);
  if (totalCholesterol != null) HealthInfo.TotalCholesterol = totalCholesterol;
  if (hdlCholesterol   != null) HealthInfo.HDLCholesterol   = hdlCholesterol;
  if (ldlCholesterol   != null) HealthInfo.LDLCholesterol   = ldlCholesterol;
  if (triglycerides    != null) HealthInfo.Triglycerides    = triglycerides;

  // ── Glucose / HbA1c ─────────────────────────────────────────────────────────
  const fastingGlucose = optNum(input.fastingGlucose);
  const hbA1c          = optNum(input.hbA1c);
  if (fastingGlucose != null) HealthInfo.FastingGlucose = fastingGlucose;
  if (hbA1c          != null) HealthInfo.HbA1c          = hbA1c;

  // ── Renal ────────────────────────────────────────────────────────────────────
  const serumCreatinine = optNum(input.serumCreatinine);
  if (serumCreatinine != null) HealthInfo.SerumCreatinine = serumCreatinine;

  // ── Liver enzymes ────────────────────────────────────────────────────────────
  const ast      = optNum(input.ast);
  const alt      = optNum(input.alt);
  const ggt      = optNum(input.ggt);
  const albumin  = optNum(input.albumin);
  const platelets = optNum(input.platelets);
  if (ast      != null) HealthInfo.AST      = ast;
  if (alt      != null) HealthInfo.ALT      = alt;
  if (ggt      != null) HealthInfo.GGT      = ggt;
  if (albumin  != null) HealthInfo.Albumin  = albumin;
  if (platelets != null) HealthInfo.Platelets = platelets;

  // ── Spirometry ───────────────────────────────────────────────────────────────
  const fev1Percent = optNum(input.fev1Percent);
  if (fev1Percent != null) HealthInfo.FEV1Percent = fev1Percent;

  return { ProfileInfo, HealthInfo };
}
