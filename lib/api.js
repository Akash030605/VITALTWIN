/**
 * API client for VitalTwin report.
 *
 * Submits to same-origin /api/report (avoids CORS). The API route proxies to
 * REPORT_API_URL or NEXT_PUBLIC_REPORT_API_URL when set.
 *
 * Request: POST with body { profile, input }
 * - profile: { name, age, gender, height, weight, diet, activity }
 * - input: { smoking, alcohol, sleep, stress, medical_conditions[] }
 *
 * Response: JSON report object from the report API.
 */
const REPORT_API_PATH = "/api/report";

/**
 * Submit both forms: profile (Step 1) + health input (Step 2). Uses /api/report
 * so the browser never hits an external origin (no CORS). The route proxies to
 * your backend when REPORT_API_URL or NEXT_PUBLIC_REPORT_API_URL is set.
 */
export async function submitReport(profile, input) {
  try {
    const res = await fetch(REPORT_API_PATH, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile, input }),
    });
    const contentType = res.headers.get("content-type");
    const isJson = contentType && contentType.includes("application/json");
    const data = isJson ? await res.json() : {};
    if (!res.ok) {
      const msg = data?.message || (res.status === 404 ? "Report service not found. Check that the report API URL is correct and /predict exists." : res.statusText) || `API error: ${res.status}`;
      throw new Error(msg);
    }
    // Normalize: API may return report in data, prediction, result, or at top level.
    const report = data?.data ?? data?.prediction ?? data?.result ?? data;
    return { ok: true, data: report };
  } catch (err) {
    throw new Error(err?.message || "Failed to generate report. Please try again.");
  }
}

/**
 * Fetch what-if simulation for a given changes object.
 * POST /api/report/what-if with { profile, input, changes }.
 * changes e.g. { HealthInfo: { Smoking: "Never" } } or { ProfileInfo: { Diet: "Good" }, HealthInfo: { Sleep: 8 } }
 */
export async function fetchWhatIfScenario(profile, input, changes) {
  const res = await fetch("/api/report/what-if", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile, input, changes }),
  });
  const contentType = res.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await res.json() : {};
  if (!res.ok) {
    const msg =
      data?.message ||
      (res.status === 404
        ? "What-if endpoint not found. Set REPORT_API_WHATIF_URL to your backend's what-if URL (e.g. https://your-api.com/what-if), or ensure the backend exposes this path."
        : res.statusText) ||
      "What-if request failed.";
    throw new Error(msg);
  }
  return data;
}

