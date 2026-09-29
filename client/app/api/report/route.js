import { NextResponse } from "next/server";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS, POST, PUT, PATCH, DELETE",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin",
  "Access-Control-Max-Age": "86400",
};

/**
 * CORS preflight
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: CORS_HEADERS,
  });
}

const REPORT_API_ENV =
  process.env.REPORT_API_URL?.trim() ||
  process.env.NEXT_PUBLIC_REPORT_API_URL?.trim() ||
  null;

/** Base URL with no trailing slash. If env is full predict URL (ends with /predict), strip it for base. */
function getLlmBaseUrl() {
  if (!REPORT_API_ENV) return null;
  const url = REPORT_API_ENV.replace(/\/$/, "");
  if (/\/predict\/?$/i.test(url)) return url.replace(/\/predict\/?$/i, "");
  return url;
}

/** Predict URL. If REPORT_API_URL is the full predict URL (e.g. .../predict), use it as-is. */
function getPredictUrl() {
  if (!REPORT_API_ENV) return null;
  const url = REPORT_API_ENV.replace(/\/$/, "");
  if (/\/predict\/?$/i.test(url)) return url.replace(/predict\/?$/i, "predict");
  const base = getLlmBaseUrl();
  const path = process.env.REPORT_API_PREDICT_PATH?.trim();
  const predictPath = path ? (path.startsWith("/") ? path : `/${path}`) : "/predict";
  return `${base}${predictPath}`;
}

/** Headers for LLM requests (ngrok may require ngrok-skip-browser-warning). */
function llmHeaders() {
  const base = getLlmBaseUrl();
  const headers = { "Content-Type": "application/json" };
  if (base && base.includes("ngrok")) {
    headers["ngrok-skip-browser-warning"] = "true";
  }
  return headers;
}

/**
 * Map app payload { profile, input } to the predict API contract.
 * Full API also allows HealthInfo: Bmi, ast, alt, ggt, glucose, systolic_bp, diastolic_bp, cholesterol, gluc
 * — we only send the fields we collect (no optional lab/vitals we don't have).
 */
function toPredictPayload(profile = {}, input = {}) {
  const numOr = (v, fallback) => (v === "" || v == null ? fallback : Number(v));
  const strOr = (v, fallback) => (v === "" || v == null ? fallback : String(v).trim() || fallback);
  const dietMap = { poor: "Poor", average: "Average", good: "Good" };
  const activityMap = { sedentary: "Sedentary", moderate: "Moderate", active: "Active" };

  // Send every field with a value (no missing keys) so backend never sees None in division/calculations.
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
    ...(profile.city ? { City: String(profile.city).trim().toLowerCase() } : {}),
  };

  // BMI = weight (kg) / height (m)² — calculated on frontend and sent so backend doesn't divide by None.
  const heightM = Height / 100;
  const Bmi = heightM > 0 ? Math.round((Weight / (heightM * heightM)) * 10) / 10 : null;

  // ── Lab values from uploaded PDF or manual entry ─────────────────────────
  // Frontend stores as lowercase snake_case; backend HealthInfo uses PascalCase.
  // We map both so legacy lowercase fields AND new PascalCase fields are always set.
  // Only include a field if it has a real numeric value (not null/undefined/NaN).
  const n = (v) => (v !== null && v !== undefined && !isNaN(Number(v)) ? Number(v) : null);

  const labFields = {};

  // Serum Creatinine → SerumCreatinine (used by CKD-EPI eGFR equation)
  if (n(input.creatinine) != null) labFields.SerumCreatinine = n(input.creatinine);

  // Liver enzymes → AST, ALT, GGT (used by FIB-4 index, NAFLD-LFS)
  if (n(input.ast)  != null) { labFields.AST = n(input.ast);  labFields.ast = n(input.ast); }
  if (n(input.alt)  != null) { labFields.ALT = n(input.alt);  labFields.alt = n(input.alt); }
  if (n(input.ggt)  != null) { labFields.GGT = n(input.ggt);  labFields.ggt = n(input.ggt); }

  // Platelets → Platelets (used by FIB-4 index)
  if (n(input.platelets) != null) labFields.Platelets = n(input.platelets);

  // Lipids → TotalCholesterol, LDLCholesterol, HDLCholesterol, Triglycerides
  if (n(input.cholesterol) != null) labFields.TotalCholesterol = n(input.cholesterol);
  if (n(input.ldl)         != null) labFields.LDLCholesterol   = n(input.ldl);
  if (n(input.hdl)         != null) labFields.HDLCholesterol   = n(input.hdl);
  if (n(input.triglycerides) != null) labFields.Triglycerides  = n(input.triglycerides);

  // Glucose / HbA1c → FastingGlucose, HbA1c (used by kidney, heart, brain models)
  if (n(input.hba1c)   != null) labFields.HbA1c          = n(input.hba1c);
  if (n(input.glucose) != null) { labFields.FastingGlucose = n(input.glucose); labFields.glucose = n(input.glucose); }

  // Blood pressure (systolic + diastolic) — both PascalCase and legacy snake_case
  if (n(input.systolic_bp)  != null) { labFields.SystolicBP  = n(input.systolic_bp);  labFields.systolic_bp  = n(input.systolic_bp); }
  if (n(input.diastolic_bp) != null) { labFields.DiastolicBP = n(input.diastolic_bp); labFields.diastolic_bp = n(input.diastolic_bp); }

  // FEV1% predicted — used directly by GOLD spirometry stage in lungs model
  if (n(input.fev1_percent) != null) labFields.FEV1Percent = n(input.fev1_percent);

  // Smoking detail — CigarettesPerDay + YearsSmoked for pack-years calculation
  if (n(input.cigarettes_per_day) != null) labFields.CigarettesPerDay = n(input.cigarettes_per_day);
  if (n(input.years_smoked)       != null) labFields.YearsSmoked       = n(input.years_smoked);

  // Hemoglobin — used by kidney model (anemia of CKD) and liver model (portal HTN)
  if (n(input.hemoglobin) != null) labFields.Hemoglobin = n(input.hemoglobin);

  // Uric acid — used by kidney model (hyperuricemia → CKD risk, Kanbay 2013)
  if (n(input.uric_acid) != null) labFields.UricAcid = n(input.uric_acid);

  // eGFR (if directly reported on lab report — overrides CKD-EPI calculation)
  if (n(input.egfr) != null) labFields.ReportedEGFR = n(input.egfr);

  // Albumin (used by liver Child-Pugh, kidney UACR context)
  if (n(input.albumin) != null) labFields.Albumin = n(input.albumin);
  // Total Protein — required for ILPD A/G ratio calculation (Ramana CV et al., IJCA 2012)
  if (n(input.total_protein) != null) labFields.TotalProteins = n(input.total_protein);

  // BUN (Blood Urea Nitrogen) — kidney marker
  if (n(input.bun) != null) labFields.BUN = n(input.bun);

  // ALP + Bilirubin — used by ILPD, LPD liver models and Child-Pugh
  if (n(input.alp)            != null) { labFields.ALP = n(input.alp); labFields.alp = n(input.alp); }
  if (n(input.bilirubin_total) != null) { labFields.TotalBilirubin = n(input.bilirubin_total); labFields.bilirubin_total = n(input.bilirubin_total); }

  // Vitamins, thyroid, iron — passed through for future model use
  if (n(input.vitamin_b12)          != null) labFields.VitaminB12         = n(input.vitamin_b12);
  if (n(input.vitamin_d)            != null) labFields.VitaminD            = n(input.vitamin_d);
  if (n(input.tsh)                  != null) labFields.TSH                 = n(input.tsh);
  if (n(input.iron)                 != null) labFields.Iron                = n(input.iron);
  if (n(input.transferrin_saturation) != null) labFields.TransferrinSaturation = n(input.transferrin_saturation);

  const HealthInfo = {
    Smoking: strOr(input.smoking, "Never"),
    Alcohol: strOr(input.alcohol, "Never"),
    Sleep: numOr(input.sleep, 7),
    Stress: strOr(input.stress, "Low"),
    MedicalConditions: Array.isArray(input.medical_conditions) ? input.medical_conditions.filter(Boolean) : [],
    Medications: Array.isArray(input.medications) ? input.medications.filter(Boolean) : [],
    ...(Bmi != null && { Bmi }),
    // All mapped lab fields (PascalCase + legacy lowercase aliases)
    ...labFields,
    // Audit flag: tells backend real lab values were uploaded vs estimated
    ...(Object.keys(labFields).length > 0 && { lab_source: input.lab_source ?? "uploaded" }),
  };

  return { ProfileInfo, HealthInfo };
}

/**
 * GET /api/report — not used by app; LLM report comes from POST /predict.
 */
export async function GET() {
  const base = getLlmBaseUrl();
  if (!base) {
    return NextResponse.json(
      { message: "Report API not configured. Set REPORT_API_URL or NEXT_PUBLIC_REPORT_API_URL." },
      { status: 503, headers: CORS_HEADERS }
    );
  }
  return NextResponse.json(
    { message: "Use POST /api/report with { profile, input }. Sent to LLM as ProfileInfo + HealthInfo." },
    { status: 405, headers: CORS_HEADERS }
  );
}

/**
 * POST /api/report — sends { profile, input } to LLM backend /predict.
 * Returns the normalized report object.
 */
export async function POST(request) {
  const base = getLlmBaseUrl();

  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { message: "Invalid JSON body" },
      { status: 400, headers: CORS_HEADERS }
    );
  }

  const { profile = {}, input = {} } = body;
  const payload = toPredictPayload(profile, input);

  if (!base) {
    return NextResponse.json(
      { message: "Report API not configured. Set REPORT_API_URL or NEXT_PUBLIC_REPORT_API_URL." },
      { status: 503, headers: CORS_HEADERS }
    );
  }

  try {
    const predictUrl = getPredictUrl();
    const res = await fetch(predictUrl, {
      method: "POST",
      headers: llmHeaders(),
      body: JSON.stringify(payload),
    });
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await res.json() : {};

    if (!res.ok) {
      let message = data?.message || data?.detail || res.statusText || `API error: ${res.status}`;
      if (res.status === 404) {
        message = `Report service not found (404). Tried ${predictUrl}. Check REPORT_API_URL in .env.`;
      }
      return NextResponse.json(
        { message },
        { status: res.status, headers: CORS_HEADERS }
      );
    }

    // Backend returns { status: "success", data: { vital_score, biological_age, body_stress, future_self, organs, ... } }.
    // Normalize: also support { prediction }, { result }, or report at top level.
    let report = data?.data ?? data?.prediction ?? data?.result ?? data;
    if (typeof report !== "object" || report === null) report = {};

    return NextResponse.json(report, {
      status: 200,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { message: err?.message || "Failed to reach report API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
