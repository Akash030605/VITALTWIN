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

/** What-if path (default /what-if). */
function getWhatIfPath() {
  const p = process.env.REPORT_API_WHATIF_PATH?.trim();
  return p ? (p.startsWith("/") ? p : `/${p}`) : "/what-if";
}

/** Full what-if URL. If REPORT_API_WHATIF_URL is set, use it; otherwise {base}{path}. */
function getWhatIfUrl() {
  const full = process.env.REPORT_API_WHATIF_URL?.trim();
  if (full) return full.replace(/\/$/, "");
  const base = getLlmBaseUrl();
  if (!base) return null;
  return `${base}${getWhatIfPath()}`;
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
  };

  // BMI = weight (kg) / height (m)² — calculated on frontend and sent so backend doesn't divide by None.
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
 * POST /api/report — sends { profile, input } to LLM:
 * 1) POST {base}/predict → report output
 * 2) POST {base}/what-if → what-if data for frontend
 * Merges what_if response into report as what_if_simulations.
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

    const whatIfUrl = getWhatIfUrl();
    const whatIfPayload = {
      user_data: { ProfileInfo: payload.ProfileInfo, HealthInfo: payload.HealthInfo },
      changes: { additionalProp1: {} },
    };
    try {
      if (!whatIfUrl) {
        console.warn("[report] What-if skipped: no base URL (set REPORT_API_WHATIF_URL or use REPORT_API_URL with base)");
      } else {
        const whatIfRes = await fetch(whatIfUrl, {
          method: "POST",
          headers: llmHeaders(),
          body: JSON.stringify(whatIfPayload),
        });
        const whatIfContentType = whatIfRes.headers.get("content-type") || "";
        const whatIfIsJson = whatIfContentType.includes("application/json");
        const whatIfData = whatIfIsJson ? await whatIfRes.json() : null;
        if (whatIfRes.ok && whatIfData != null) {
          const simData = whatIfData?.data ?? whatIfData?.scenarios ?? whatIfData;
          const hasReportShape = simData && typeof simData === "object" && (simData.vital_score != null || simData.overall_health_score != null);
          if (hasReportShape) {
            const bio = simData.biological_age;
            const score = simData.overall_health_score ?? simData.vital_score?.current ?? 0;
            report.what_if_simulations = {
              current: {
                id: "current",
                name: "Current lifestyle",
                description: "Your current assessment based on the report.",
                biological_age: report.biological_age?.biological_age ?? 0,
                health_score: report.overall_health_score ?? report.vital_score?.current ?? 0,
              },
              scenarios: [
                {
                  id: "what-if",
                  name: "What-if simulation",
                  description: simData.vital_score?.message ?? "Simulated outcome from what-if analysis.",
                  biological_age: typeof bio === "object" ? bio?.biological_age ?? 0 : (bio ?? 0),
                  health_score: score,
                },
              ],
              quick_wins: [],
            };
          } else {
            report.what_if_simulations = simData;
          }
        } else {
          console.warn("[report] What-if failed:", whatIfRes.status, whatIfUrl, whatIfData?.message || whatIfData?.detail || "");
        }
      }
    } catch (err) {
      console.warn("[report] What-if request error:", err?.message);
    }

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
