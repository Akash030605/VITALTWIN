import { NextResponse } from "next/server";
import { buildSystemPrompt } from "../../../lib/buildChatContext";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS_HEADERS });
}

/**
 * POST /api/chat
 * Body: { messages: [{role, content}], profile, input, result }
 * Streams response from Groq (OpenAI-compatible endpoint).
 */
export async function POST(request) {
  const apiKey = process.env.GROQ_API_KEY?.trim();
  if (!apiKey) {
    return NextResponse.json(
      { error: "Chat not configured. Set GROQ_API_KEY in .env.local." },
      { status: 503, headers: CORS_HEADERS }
    );
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400, headers: CORS_HEADERS });
  }

  const { messages = [], profile = {}, input = {}, result = null } = body;
  const model = process.env.GROQ_CHAT_MODEL?.trim() || "llama-3.3-70b-versatile";
  const systemPrompt = buildSystemPrompt(profile, input, result);

  const groqMessages = [
    { role: "system", content: systemPrompt },
    ...messages.filter((m) => m?.role && m?.content),
  ];

  try {
    const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: groqMessages,
        temperature: 0.5,
        max_tokens: 512,
        stream: true,
      }),
    });

    if (!groqRes.ok) {
      const errText = await groqRes.text();
      return NextResponse.json(
        { error: `Groq API error ${groqRes.status}: ${errText}` },
        { status: groqRes.status, headers: CORS_HEADERS }
      );
    }

    // Stream the response back as Server-Sent Events
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const reader = groqRes.body.getReader();
        const decoder = new TextDecoder();
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            // Forward raw SSE lines from Groq to client
            controller.enqueue(encoder.encode(chunk));
          }
        } catch (err) {
          controller.error(err);
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        ...CORS_HEADERS,
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err?.message || "Failed to reach Groq API" },
      { status: 502, headers: CORS_HEADERS }
    );
  }
}
