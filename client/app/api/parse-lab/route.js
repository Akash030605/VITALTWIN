import { NextResponse } from "next/server";

/**
 * POST /api/parse-lab
 * Body: { text: string }  — raw text extracted from a blood test PDF
 *
 * Sends the text to Groq LLaMA-3 with a structured extraction prompt.
 * Returns JSON with extracted lab values (null for any not found).
 */

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

const LAB_EXTRACTION_PROMPT = `You are a medical data extractor. Extract specific numeric lab values AND patient demographics from a raw blood test report.

RULES:
1. Return ONLY valid JSON — no explanation, no markdown, no extra text.
2. Units: creatinine mg/dL, cholesterol mg/dL, triglycerides mg/dL, glucose mg/dL, hemoglobin g/dL, albumin g/dL, total_protein g/dL, platelets 10^3/µL, AST/ALT/GGT/ALP in U/L, FEV1 as %, uric_acid mg/dL, BUN mg/dL, eGFR mL/min/1.73m², bilirubin mg/dL.
3. If a value is not found, use null.
4. For gender: extract "Male" or "Female" from patient info (look for M/F, Male/Female, or name context like "19Y/F").
5. For age: extract the numeric age from patient info (e.g. "19Y/F" → 19, "45 Years" → 45).
6. For patient_name: extract the full patient name if present.
7. SGOT = AST, SGPT = ALT — they are the same tests with different names.
8. Look through the ENTIRE report for LFT (Liver Function Tests): AST/SGOT, ALT/SGPT, GGT, Albumin, Total Protein, ALP, Bilirubin.
9. total_protein: extract "Total Protein" or "Serum Total Protein" value (normal range 6.0–8.3 g/dL).

Return EXACTLY this JSON structure:
{
  "patient_name": null,
  "age": null,
  "gender": null,
  "creatinine": null,
  "ast": null,
  "alt": null,
  "ggt": null,
  "alp": null,
  "bilirubin_total": null,
  "platelets": null,
  "cholesterol": null,
  "ldl": null,
  "hdl": null,
  "hba1c": null,
  "glucose": null,
  "systolic_bp": null,
  "diastolic_bp": null,
  "fev1_percent": null,
  "hemoglobin": null,
  "uric_acid": null,
  "egfr": null,
  "bun": null,
  "triglycerides": null,
  "albumin": null,
  "total_protein": null,
  "vitamin_b12": null,
  "vitamin_d": null,
  "tsh": null,
  "iron": null,
  "transferrin_saturation": null
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
  if (!text || typeof text !== "string" || text.trim().length < 20) {
    return NextResponse.json(
      { error: "No usable text provided. Make sure the PDF contains readable text." },
      { status: 400, headers: CORS_HEADERS }
    );
  }

  // Use up to 14000 chars — long lab reports (13+ pages) have LFT data near the end
  // 6000 char limit was cutting off page 10+ data (LFT, kidney, lipid sections)
  const truncatedText = text.slice(0, 14000);

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
          { role: "system", content: LAB_EXTRACTION_PROMPT },
          { role: "user", content: `Extract lab values and patient demographics from this report:\n\n${truncatedText}` },
        ],
        temperature: 0.0,
        max_tokens: 800,
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

    // Numeric lab keys
    const numericKeys = [
      "creatinine", "ast", "alt", "ggt", "alp", "bilirubin_total",
      "platelets", "cholesterol", "ldl", "hdl", "hba1c", "glucose",
      "systolic_bp", "diastolic_bp", "fev1_percent", "hemoglobin",
      "uric_acid", "egfr", "bun", "triglycerides", "albumin", "total_protein",
      "vitamin_b12", "vitamin_d", "tsh", "iron", "transferrin_saturation"
    ];

    const sanitized = {};

    // Handle numeric fields
    for (const key of numericKeys) {
      const val = extracted[key];
      sanitized[key] = (val !== null && val !== undefined && !isNaN(Number(val)))
        ? Number(val)
        : null;
    }

    // Handle demographic fields — keep as string/number
    sanitized.patient_name = (typeof extracted.patient_name === "string" && extracted.patient_name.trim())
      ? extracted.patient_name.trim()
      : null;

    // Gender: normalize to "Male" or "Female"
    if (typeof extracted.gender === "string") {
      const g = extracted.gender.trim().toLowerCase();
      if (g === "male" || g === "m") sanitized.gender = "Male";
      else if (g === "female" || g === "f") sanitized.gender = "Female";
      else sanitized.gender = null;
    } else {
      sanitized.gender = null;
    }

    // Age: numeric
    const ageVal = extracted.age;
    sanitized.age = (ageVal !== null && ageVal !== undefined && !isNaN(Number(ageVal)))
      ? Number(ageVal)
      : null;

    const foundCount = Object.values(sanitized).filter((v) => v !== null).length;

    return NextResponse.json(
      { values: sanitized, found_count: foundCount },
      { status: 200, headers: CORS_HEADERS }
    );
  } catch (err) {
    return NextResponse.json(
      { error: err?.message || "Failed to reach Groq API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
