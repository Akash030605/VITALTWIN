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

function getProfileApiPath() {
  const v = process.env.PROFILE_API_PATH?.trim()?.toLowerCase();
  return v === "submissions" ? "submissions" : "profile";
}

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

/**
 * GET /api/profile/[id] — proxy to backend: GET /profile/:id or GET /submissions/:id.
 */
export async function GET(request, context) {
  const p = context.params;
  const params = p && typeof p.then === "function" ? await p : p ?? {};
  const id = params.id;
  if (!id) {
    return NextResponse.json(
      { message: "Missing profile id" },
      { status: 400, headers: CORS_HEADERS }
    );
  }
  const base = getProfileApiUrl();
  const pathKind = getProfileApiPath();
  const byIdUrl = pathKind === "submissions" ? `${base}/submissions/${encodeURIComponent(id)}` : `${base}/profile/${encodeURIComponent(id)}`;
  try {
    const res = await fetch(byIdUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await res.json() : {};
    if (res.status === 404) {
      return NextResponse.json(
        { message: "Not found", data: null },
        { status: 404, headers: CORS_HEADERS }
      );
    }
    if (!res.ok) {
      return NextResponse.json(
        { message: data?.message || res.statusText },
        { status: res.status, headers: CORS_HEADERS }
      );
    }
    return NextResponse.json(data, {
      status: 200,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { message: err?.message || "Failed to reach profile API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
