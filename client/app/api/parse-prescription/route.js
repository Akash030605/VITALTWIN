import { NextResponse } from "next/server";

/**
 * POST /api/parse-prescription
 * Body: { text: string }  — raw text extracted from a prescription PDF
 *
 * Sends the text to Groq LLaMA-3 to extract:
 *   - medications: list of drug names (with dosage if available)
 *   - conditions: list of diagnosed conditions
 *
 * Returns: { medications: string[], conditions: string[] }
 */

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

const PRESCRIPTION_EXTRACTION_PROMPT = `You are a medical data extractor specializing in prescriptions.

Your job is to extract two things from a prescription or medical document:
1. All medications prescribed (include dosage and frequency if mentioned)
2. Any diagnosed medical conditions, diseases, or diagnoses mentioned

RULES:
1. Return ONLY valid JSON — no explanation, no markdown, no extra text.
2. medications: array of strings — each string is ONE medication with dosage (e.g. "Metformin 500mg twice daily", "Atorvastatin 10mg")
3. conditions: array of strings — each string is ONE condition (e.g. "Type 2 Diabetes", "Hypertension", "Dyslipidemia")
4. If no medications found, return empty array [].
5. If no conditions found, return empty array [].
6. Normalize condition names to standard medical English (e.g. "Sugar" → "Type 2 Diabetes", "BP" → "Hypertension").
7. Do NOT include vitamins, supplements, or non-prescription items in medications unless clearly prescribed.

Return EXACTLY this JSON structure:
{
  "medications": [],
  "conditions": []
}`;

export async function POST(request) {
  const apiKey = process.env.GROQ_API_KEY?.trim();
  if (!apiKey) {
    return NextResponse.json(
      { error: "Groq API key not configured. Set GROQ_API_KEY in .env.local." },
      { status: 503, headers: CORS_HEADERS }
    );
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400, headers: CORS_HEADERS }
    );
  }

  const { text } = body;
  if (!text || typeof text !== "string" || text.trim().length < 10) {
    return NextResponse.json(
      { error: "No usable text provided. Make sure the PDF contains readable text." },
      { status: 400, headers: CORS_HEADERS }
    );
  }

  // Truncate to ~4000 chars (prescriptions are shorter than lab reports)
  const truncatedText = text.slice(0, 4000);

  const model = process.env.GROQ_CHAT_MODEL?.trim() || "llama-3.3-70b-versatile";

  try {
    const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: PRESCRIPTION_EXTRACTION_PROMPT },
          { role: "user", content: `Extract medications and conditions from this prescription:\n\n${truncatedText}` },
        ],
        temperature: 0.0,   // deterministic extraction
        max_tokens: 512,
        stream: false,
      }),
    });

    if (!groqRes.ok) {
      const errText = await groqRes.text();
      return NextResponse.json(
        { error: `Groq API error ${groqRes.status}: ${errText}` },
        { status: groqRes.status, headers: CORS_HEADERS }
      );
    }

    const groqData = await groqRes.json();
    const rawContent = groqData?.choices?.[0]?.message?.content?.trim() ?? "";

    // Strip any accidental markdown code fences
    const jsonString = rawContent
      .replace(/^```json\s*/i, "")
      .replace(/^```\s*/i, "")
      .replace(/```\s*$/i, "")
      .trim();

    let extracted;
    try {
      extracted = JSON.parse(jsonString);
    } catch {
      return NextResponse.json(
        { error: "AI returned unparseable response. Try again.", raw: rawContent },
        { status: 422, headers: CORS_HEADERS }
      );
    }

    // Sanitize: ensure arrays
    const medications = Array.isArray(extracted.medications)
      ? extracted.medications.filter((m) => typeof m === "string" && m.trim().length > 0)
      : [];

    const conditions = Array.isArray(extracted.conditions)
      ? extracted.conditions.filter((c) => typeof c === "string" && c.trim().length > 0)
      : [];

    return NextResponse.json(
      {
        medications,
        conditions,
        found_count: medications.length + conditions.length,
      },
      { status: 200, headers: CORS_HEADERS }
    );
  } catch (err) {
    return NextResponse.json(
      { error: err?.message || "Failed to reach Groq API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
