import { NextResponse } from "next/server";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS, POST, PUT, PATCH, DELETE",
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

/** "profile" => POST/GET /profile; "submissions" => POST /submissions, GET /submissions/latest */
function getProfileApiPath() {
  const v = process.env.PROFILE_API_PATH?.trim()?.toLowerCase();
  return v === "submissions" ? "submissions" : "profile";
}

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

/**
 * GET /api/profile — proxy to backend: GET /profile or GET /submissions/latest.
 */
export async function GET() {
  const base = getProfileApiUrl();
  const pathKind = getProfileApiPath();
  const latestUrl = pathKind === "submissions" ? `${base}/submissions/latest` : `${base}/profile`;
  try {
    const res = await fetch(latestUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await res.json() : {};
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

/**
 * POST /api/profile — proxy to backend: POST /profile or POST /submissions (save; use returned id if needed).
 */
export async function POST(request) {
  const base = getProfileApiUrl();
  const pathKind = getProfileApiPath();
  const saveUrl = pathKind === "submissions" ? `${base}/submissions` : `${base}/profile`;
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
  try {
    const res = await fetch(saveUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile, input }),
    });
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await res.json() : {};
    if (!res.ok) {
      return NextResponse.json(
        { message: data?.message || res.statusText },
        { status: res.status, headers: CORS_HEADERS }
      );
    }
    return NextResponse.json(data, {
      status: res.status,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { message: err?.message || "Failed to reach profile API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
