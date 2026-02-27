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
 * Response: JSON report object. Shape should match lib/dummyReport.js for full UI compatibility.
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
      throw new Error(data?.message || res.statusText || `API error: ${res.status}`);
    }
    return { ok: true, data: data?.data ?? data };
  } catch (err) {
    throw new Error(err?.message || "Failed to generate report. Please try again.");
  }
}

