/**
 * Profile / submissions API client. Uses same-origin /api/profile (Next.js proxies to backend).
 *
 * Backend contract (proxy supports both styles via PROFILE_API_PATH):
 * - Save:  POST /profile or POST /submissions with { profile, input } → use returned id if needed.
 * - Latest: GET /profile or GET /submissions/latest → { profile, input, createdAt, id }.
 * - By id: GET /profile/:id or GET /submissions/:id with stored id.
 * - Health: GET /health (optional).
 *
 * Env: PROFILE_API_URL (or NEXT_PUBLIC_*); PROFILE_API_PATH=profile|submissions (default profile).
 */

const API_BASE = "/api/profile";
const headers = { "Content-Type": "application/json" };

async function parseError(res) {
  let message = res.statusText;
  try {
    const data = await res.json();
    if (data?.message) message = data.message;
  } catch {}
  return message;
}

/**
 * Save form (one request). POST with { profile, input } → returns { ok, id } (use id for load by id).
 */
export async function saveSubmission(profile, input) {
  const res = await fetch(API_BASE, {
    method: "POST",
    headers,
    body: JSON.stringify({ profile: profile ?? {}, input: input ?? {} }),
  });
  const data = res.ok ? await res.json().catch(() => ({})) : null;
  if (!res.ok) {
    const message = await parseError(res);
    throw new Error(message || "Failed to save.");
  }
  return { ok: true, id: data?.id ?? null };
}

/**
 * Load profile / last submission. GET latest → { ok, data: { profile, input, createdAt, id } }.
 */
export async function getLatestSubmission() {
  const res = await fetch(API_BASE, { method: "GET", headers });
  if (res.status === 404) return { ok: false, data: null };
  if (!res.ok) {
    const message = await parseError(res);
    throw new Error(message || "Failed to load profile.");
  }
  const data = await res.json().catch(() => null);
  return { ok: true, data };
}

/**
 * Load a specific submission. GET /profile/:id (or /submissions/:id) with stored id.
 */
export async function getSubmissionById(id) {
  if (!id) return { ok: false, data: null };
  const res = await fetch(`${API_BASE}/${encodeURIComponent(id)}`, { method: "GET", headers });
  if (res.status === 404) return { ok: false, data: null };
  if (!res.ok) {
    const message = await parseError(res);
    throw new Error(message || "Failed to load submission.");
  }
  const data = await res.json().catch(() => null);
  return { ok: true, data };
}

/**
 * Optional: GET /health to verify backend is reachable. Returns { ok: true } when healthy.
 */
export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`, { method: "GET", headers });
  if (!res.ok) return { ok: false };
  const data = await res.json().catch(() => ({}));
  return { ok: data?.ok === true };
}
