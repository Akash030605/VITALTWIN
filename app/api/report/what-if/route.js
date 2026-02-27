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

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

/**
 * POST /api/report/what-if — call backend what-if or, if no what-if URL, /predict with merged changes.
 * Body: { profile, input, changes }
 * changes: e.g. { HealthInfo: { Smoking: "Never" } } or { ProfileInfo: { Diet: "Good" }, HealthInfo: { Sleep: 8 } }
 * When REPORT_API_WHATIF_URL is not set, we call the same /predict URL with ProfileInfo/HealthInfo merged with changes.
 */
export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: "Invalid JSON body" }, { status: 400, headers: CORS_HEADERS });
  }

  const { profile = {}, input = {}, changes = {} } = body;
  const payload = toPredictPayload(profile, input);
  const target = getWhatIfTargetUrl();

  if (!target) {
    return NextResponse.json(
      { message: "Report API not configured. Set REPORT_API_URL or NEXT_PUBLIC_REPORT_API_URL." },
      { status: 503, headers: CORS_HEADERS }
    );
  }

  const requestBody = target.usePredict
    ? mergeWhatIfIntoPredictPayload(payload, changes)
    : {
        user_data: { ProfileInfo: payload.ProfileInfo, HealthInfo: payload.HealthInfo },
        changes: typeof changes === "object" && changes !== null ? changes : { additionalProp1: {} },
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
          ? "What-if endpoint not found (404). Set REPORT_API_WHATIF_URL to your backend's what-if URL (e.g. https://your-api.com/what-if), or ensure the backend exposes this path."
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
