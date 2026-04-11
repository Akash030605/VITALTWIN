import { NextResponse } from "next/server";
import {
  getWhatIfTargetUrl,
  llmHeaders,
  mergeWhatIfIntoPredictPayload,
  toPredictPayload,
} from "../../../../lib/reportApiServer";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS, POST",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Max-Age": "86400",
};

const SCENARIO_NAMES = {
  current: "Current",
  quit_smoking: "Quit Smoking",
  sleep_8: "Sleep 8 Hours",
  reduce_stress: "Reduce Stress",
  stop_alcohol: "Stop Alcohol",
  active_lifestyle: "Active Lifestyle",
  healthy_diet: "Healthy Diet",
  complete_transformation: "Complete Transformation",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

/** Call Groq (or OpenRouter fallback) to generate what-if scenario results. */
async function whatIfWithOpenRouter(profile, input, currentReport, scenarioId, changes) {
  // Prefer Groq; fall back to OpenRouter if only that key is set
  const groqKey = process.env.GROQ_API_KEY?.trim();
  const orKey = process.env.OPENROUTER_API_KEY?.trim();
  const apiKey = groqKey || orKey;
  if (!apiKey) return null;

  const useGroq = !!groqKey;
  const apiUrl = useGroq
    ? "https://api.groq.com/openai/v1/chat/completions"
    : "https://openrouter.ai/api/v1/chat/completions";
  const model = useGroq
    ? (process.env.GROQ_WHATIF_MODEL?.trim() || "llama-3.3-70b-versatile")
    : (process.env.OPENROUTER_WHATIF_MODEL?.trim() || "google/gemini-2.0-flash-exp");

  const scenarioName = SCENARIO_NAMES[scenarioId] || scenarioId;
  const currentBio = typeof currentReport?.biological_age === "object"
    ? currentReport.biological_age?.biological_age
    : currentReport?.biological_age;
  const currentScore = currentReport?.overall_health_score ?? currentReport?.vital_score?.current ?? null;
  const currentMessage = currentReport?.vital_score?.message ?? currentReport?.vital_score?.interpretation ?? "";

  const systemPrompt = `You are a health coach. Given the user's profile, health inputs, and their current health report from an LLM, you answer "what-if" scenarios.
Respond with a JSON object only, no markdown, with these exact keys:
- "message": string. One short sentence for the scenario outcome. If they make the change, say how much they gain. Example: "If you quit smoking, you could gain about 2 years in biological age and 8 points in health score."
- "years_gained": number or null. Estimated biological years they could gain (e.g. 1, 2). Use null if not applicable.
- "points_gained": number or null. Estimated health score points they could gain (e.g. 5, 10). Use null if not applicable.
- "recommendations": array of strings. 2–4 short, actionable recommendations for this scenario.`;

  const userContent = `Scenario: "${scenarioName}". The user is considering this change.

## Profile (inputs)
${JSON.stringify(profile, null, 2)}

## Health inputs (smoking, alcohol, sleep, stress, etc.)
${JSON.stringify(input, null, 2)}

## Current health report (from LLM)
- Biological age: ${currentBio ?? "unknown"}
- Health score: ${currentScore ?? "unknown"}
- Summary: ${currentMessage || "—"}
${currentReport?.organ_scores ? `- Organ scores: ${JSON.stringify(currentReport.organ_scores)}` : ""}

## What changes in this scenario
${JSON.stringify(changes, null, 2)}

Return only the JSON object with keys: message, years_gained, points_gained, recommendations.`;

  try {
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` };
    if (!useGroq) headers["HTTP-Referer"] = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

    const res = await fetch(apiUrl, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userContent },
        ],
        temperature: 0.3,
        max_tokens: 512,
      }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `AI API ${res.status}`);
    }
    const data = await res.json();
    const raw = data?.choices?.[0]?.message?.content?.trim();
    if (!raw) throw new Error("Empty AI response");
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      const jsonMatch = raw.match(/\{[\s\S]*\}/);
      parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : {};
    }
    const message = parsed.message ?? "";
    const yearsGained = parsed.years_gained != null ? Number(parsed.years_gained) : null;
    const pointsGained = parsed.points_gained != null ? Number(parsed.points_gained) : null;
    const recommendations = Array.isArray(parsed.recommendations) ? parsed.recommendations.filter(Boolean).map(String) : [];

    const bioNum = typeof currentBio === "number" && yearsGained != null ? Math.max(0, currentBio - yearsGained) : currentBio;
    const scoreNum = typeof currentScore === "number" && pointsGained != null ? Math.min(100, currentScore + pointsGained) : currentScore;

    return {
      ...(typeof currentReport === "object" && currentReport !== null ? currentReport : {}),
      biological_age: bioNum,
      overall_health_score: scoreNum,
      vital_score: {
        ...(currentReport?.vital_score && typeof currentReport.vital_score === "object" ? currentReport.vital_score : {}),
        message,
        current: scoreNum,
      },
      improvements: {
        years_gained: yearsGained,
        health_score_increase: pointsGained,
      },
      scenario_recommendations: recommendations,
    };
  } catch (e) {
    console.error("What-if AI error:", e?.message || e);
    return null;
  }
}

/**
 * POST /api/report/what-if — OpenRouter (if key set) or backend what-if or /predict with merged changes.
 * Body: { profile, input, changes, current_report?, scenario_id? }
 * Sends all inputs and full LLM report to OpenRouter when OPENROUTER_API_KEY is set.
 */
export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: "Invalid JSON body" }, { status: 400, headers: CORS_HEADERS });
  }

  const { profile = {}, input = {}, changes = {}, current_report: currentReport, scenario_id: scenarioId } = body;
  const payload = toPredictPayload(profile, input);
  const changesObj = typeof changes === "object" && changes !== null ? changes : {};

  // "Current" scenario: return report as-is (no AI call).
  if (scenarioId === "current" && currentReport != null && typeof currentReport === "object") {
    return NextResponse.json(currentReport, {
      status: 200,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  // OpenRouter: full context (inputs + report) → message, years_gained, points_gained, recommendations.
  if (scenarioId && scenarioId !== "current" && currentReport != null && typeof currentReport === "object") {
    const openRouterResult = await whatIfWithOpenRouter(profile, input, currentReport, scenarioId, changesObj);
    if (openRouterResult) {
      return NextResponse.json(openRouterResult, {
        status: 200,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }
    // If OpenRouter failed and we have no external URL, return 503 below.
  }

  const target = getWhatIfTargetUrl();
  if (!target) {
    return NextResponse.json(
      {
        message: (process.env.GROQ_API_KEY || process.env.OPENROUTER_API_KEY)
          ? "What-if failed (AI error or missing current_report). Ensure you have a report and GROQ_API_KEY set."
          : "Report API not configured. Set REPORT_API_URL or GROQ_API_KEY (with current_report) for what-if.",
      },
      { status: 503, headers: CORS_HEADERS }
    );
  }

  const requestBody = target.usePredict
    ? mergeWhatIfIntoPredictPayload(payload, changesObj)
    : {
        user_data: { ProfileInfo: payload.ProfileInfo, HealthInfo: payload.HealthInfo },
        changes: changesObj,
        ...(currentReport != null && typeof currentReport === "object" && { current_report: currentReport }),
        ...(scenarioId != null && scenarioId !== "" && { scenario_id: scenarioId }),
      };

  const headers = llmHeaders();
  if (target.usePredict) {
    headers["X-What-If"] = "true";
  }

  try {
    const res = await fetch(target.url, {
      method: "POST",
      headers,
      body: JSON.stringify(requestBody),
    });
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await res.json() : {};

    if (!res.ok) {
      const fallback =
        res.status === 404
          ? "What-if endpoint not found (404). Set REPORT_API_WHATIF_URL or use OPENROUTER_API_KEY with current_report."
          : `What-if API error: ${res.status}`;
      const message = data?.message || data?.detail || (res.status === 404 ? fallback : res.statusText) || fallback;
      return NextResponse.json(
        { message },
        { status: res.status, headers: CORS_HEADERS }
      );
    }

    const result = data?.data ?? data?.prediction ?? data?.result ?? data;
    return NextResponse.json(result != null ? result : data, {
      status: 200,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { message: err?.message || "Failed to reach what-if API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
