import { NextResponse } from "next/server";
import { DUMMY_REPORT } from "@/lib/dummyReport";

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

/**
 * GET /api/report — proxy to report API (if URL set) or return dummy.
 */
export async function GET() {
  const reportApiUrl =
    process.env.REPORT_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_REPORT_API_URL?.trim() ||
    null;

  if (reportApiUrl) {
    try {
      const res = await fetch(reportApiUrl, { method: "GET" });
      const contentType = res.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");
      const data = isJson ? await res.json() : {};
      if (!res.ok) {
        return NextResponse.json(
          { message: data?.message || res.statusText || `API error: ${res.status}` },
          { status: res.status, headers: CORS_HEADERS }
        );
      }
      return NextResponse.json(data?.data ?? data, {
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

  await new Promise((r) => setTimeout(r, 200));
  return NextResponse.json(DUMMY_REPORT, {
    status: 200,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

/**
 * POST /api/report — proxy to report API or return dummy data.
 * Body: { profile, input }
 */
export async function POST(request) {
  const reportApiUrl =
    process.env.REPORT_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_REPORT_API_URL?.trim() ||
    null;

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

  if (reportApiUrl) {
    try {
      const res = await fetch(reportApiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, input }),
      });
      const contentType = res.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");
      const data = isJson ? await res.json() : {};

      if (!res.ok) {
        return NextResponse.json(
          { message: data?.message || res.statusText || `API error: ${res.status}` },
          { status: res.status, headers: CORS_HEADERS }
        );
      }

      return NextResponse.json(data?.data ?? data, {
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

  // No API URL: return dummy report after a short delay
  await new Promise((r) => setTimeout(r, 800));
  return NextResponse.json(DUMMY_REPORT, {
    status: 200,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}
