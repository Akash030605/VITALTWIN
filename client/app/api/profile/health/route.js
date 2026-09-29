import { NextResponse } from "next/server";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin",
  "Access-Control-Max-Age": "86400",
};

function getProfileApiUrl() {
  return (
    process.env.PROFILE_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_PROFILE_API_URL?.trim() ||
    "https://vitaltwin-backend.onrender.com"
  ).replace(/\/$/, "");
}

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

/**
 * GET /api/profile/health — proxy to profile API health check.
 */
export async function GET() {
  const base = getProfileApiUrl();
  try {
    const res = await fetch(`${base}/health`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    const data = res.ok ? await res.json().catch(() => ({})) : {};
    return NextResponse.json(
      { ok: data?.ok === true },
      { status: res.ok ? 200 : res.status, headers: CORS_HEADERS }
    );
  } catch (err) {
    return NextResponse.json(
      { ok: false, message: err?.message || "Failed to reach profile API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
