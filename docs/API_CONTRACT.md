# API contract: What-if and organ score reasons

This document describes the request/response shape for the what-if endpoint and for organ score reasons so the backend and frontend stay in sync.

---

## What-if (POST /api/report/what-if)

The Next.js route forwards the following to `REPORT_API_WHATIF_URL` (or to `/predict` with merged payload when that URL is not set).

### Request (body)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile` | object | Yes | App profile: name, age, gender, height, weight, diet, activity |
| `input` | object | Yes | Health input: smoking, alcohol, sleep, stress, medical_conditions[] |
| `changes` | object | Yes | Scenario changes, e.g. `{ HealthInfo: { Smoking: "Never" } }` or `{}` for Current |
| `current_report` | object | No | Full result from predict (vital_score, biological_age, body_stress, future_self, organs, overall_health_score, etc.). Sent when available so backend can base what-if on full context. |
| `scenario_id` | string | No | Scenario identifier, e.g. `"current"`, `"quit_smoking"`, `"reduce_stress"`, `"stop_alcohol"`, `"sleep_8"`, `"active_lifestyle"`, `"healthy_diet"`, `"complete_transformation"`. Backend can use this to tailor the message. |

When the dedicated what-if URL is used, the body sent to the backend is:

- `user_data`: `{ ProfileInfo, HealthInfo }` (from profile + input, same shape as predict).
- `changes`: as above.
- `current_report`: (optional) full report object.
- `scenario_id`: (optional) string.

If the backend does not yet accept `current_report` or `scenario_id`, the Next.js route still sends only `user_data` and `changes` so existing behavior is unchanged.

### Response (what-if)

Same report-like shape the frontend already uses:

- `vital_score.message` or `vital_score.interpretation`: narrative for the scenario (e.g. "If you quit smoking, you could gain about 2 years and 8 points").
- `overall_health_score` or `vital_score.current`: score 0–100.
- `biological_age` or `biological_age.biological_age`: biological age.
- Optional: `improvements.years_gained`, `improvements.health_score_increase` (or `points_gained`) for "gain X years, +Y points".
- Optional: `scenario_recommendations` or `recommendations`: array of strings for follow-up recommendations.
- Optional: full report shape (organs, body_stress, future_self, etc.) if the backend returns it.

When `OPENROUTER_API_KEY` is set, the Next.js route uses OpenRouter AI to generate the what-if response from full context (profile, input, current report). It sends all inputs and the full LLM report to OpenRouter and returns the above shape including `improvements` and `scenario_recommendations`.

---

## Organ score reasons (report / predict response)

The frontend expects each organ in `result.organs` to optionally include reasons that link the score to the user’s data (diseases, habits, lifestyle).

### Per-organ fields (optional)

Existing fields (unchanged): `health_score`, `current_risk`, `risk_level`, `metrics`, `risk_progression`, `recommendations`.

New optional fields (backend may add one or both):

| Field | Type | Description |
|-------|------|-------------|
| `score_reason` | string | One short paragraph (1–3 sentences) explaining why this organ has this score, referencing the user’s smoking, alcohol, medical conditions, diet, activity, sleep, stress where relevant. |
| `factors` | array | List of `{ factor: string, impact: "positive" \| "negative" \| "neutral", detail?: string }`. Example: `{ factor: "Smoking: Never", impact: "positive" }`, `{ factor: "Hypertension in conditions", impact: "negative", detail: "Increases cardiovascular risk" }`. |

If neither `score_reason` nor `factors` is present, the frontend shows no “Why this score” block (no errors).

---

## Summary

- **What-if**: Send `user_data`, `changes`, and optionally `current_report` + `scenario_id`. Response: same report shape (at least vital_score, overall_health_score, biological_age).
- **Organs**: Response may include per-organ `score_reason` and/or `factors` so the frontend can show personalized reasons next to each organ score.
