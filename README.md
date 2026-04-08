# VitalTwin — AI Health Digital Twin Platform

VitalTwin creates a personalised digital twin of your body. Users complete a two-step health assessment (profile + lifestyle), which feeds a Python ML backend that returns a clinically-grounded health report: biological age, vital score, organ-by-organ health, body stress heatmap, 10-year future projections, and priority recommendations. The frontend renders an interactive 3D dashboard with what-if scenario simulation, AI twin chat, PDF export, and wellness scoring.

---

## Table of Contents

- [Live Architecture](#live-architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [User Journey](#user-journey)
- [Frontend — Next.js App](#frontend--nextjs-app)
  - [Pages](#pages)
  - [State Management](#state-management)
  - [API Routes](#api-routes)
  - [3D Models](#3d-models)
  - [Key Features](#key-features)
  - [Design System](#design-system)
- [Backend — Python ML Service](#backend--python-ml-service)
  - [Organ Models](#organ-models)
  - [Feature Engines](#feature-engines)
  - [Verification Layers](#verification-layers)
  - [API Endpoints](#api-endpoints)
  - [Input / Output Schema](#input--output-schema)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Deployment](#deployment)

---

## Live Architecture

```
Browser
  │
  ├── Next.js 16 (App Router)
  │     ├── app/page.js              ← Landing + Dashboard
  │     ├── app/health-questions/    ← Step 2 form
  │     ├── app/body-ageing/         ← Body ageing view
  │     ├── app/organs/              ← Organ health view
  │     ├── app/recommendations/     ← Recommendations + What-If
  │     └── app/api/                 ← Server-side proxy routes
  │           ├── report/route.js    → Python /predict
  │           ├── report/what-if/    → Groq / OpenRouter / Python
  │           ├── chat/              → Groq streaming SSE
  │           └── profile/           → Profile persistence backend
  │
  └── Python FastAPI Service (VITALTWIN-AI-MODEL/)
        ├── /predict                 ← Full health report
        └── /what-if                 ← Scenario delta analysis
```

---

## Tech Stack

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| Next.js | 16.1.6 | React framework, App Router, SSR |
| React | 19.2.3 | UI rendering |
| Tailwind CSS | v4 | Utility-first styling |
| Three.js | 0.183 | 3D rendering engine |
| @react-three/fiber | 9.5 | React renderer for Three.js |
| @react-three/drei | 10.7 | Three.js helpers (OrbitControls, useGLTF, etc.) |
| Zustand | 5.0 | Global state management |
| GSAP | 3.14 | Animations (staggered form entrance, counters) |
| Lenis | 1.3 | Smooth scroll |
| jsPDF + jspdf-autotable | 4.2 / 5.0 | Client-side PDF generation |
| html2canvas | 1.4 | Report card PNG capture |

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime |
| FastAPI | 0.104 | REST API framework |
| Uvicorn + Gunicorn | 0.24 / 21.2 | ASGI server |
| scikit-learn | 1.2.2 | ML models (RandomForest, LogisticRegression, etc.) |
| NumPy | 1.23.5 | Numerical computation |
| pandas | 1.5.3 | Data manipulation |
| SciPy | 1.10.1 | Statistical functions |
| joblib | 1.2.0 | Model serialisation / persistence |
| Pydantic | 2.4.2 | Request/response validation |

### AI / LLM Services

| Service | Purpose |
|---|---|
| Groq (llama-3.3-70b-versatile) | Twin AI chat (SSE streaming) + What-If scenarios (primary) |
| OpenRouter (Gemini 2.0 Flash) | What-If fallback when Groq is unavailable |

---

## Repository Structure

```
VitalTwin/
├── app/                          # Next.js App Router pages
│   ├── page.js                   # Landing (no report) + Dashboard (has report)
│   ├── health-questions/page.js  # Step 2: lifestyle + medical history form
│   ├── body-ageing/page.js       # Biological age + future timeline
│   ├── organs/page.js            # Per-organ health detail
│   ├── recommendations/page.js   # Priority actions + what-if + wellness score
│   ├── layout.js                 # Root layout (fonts, LenisProvider)
│   ├── globals.css               # CSS variables, utility classes, animations
│   └── api/
│       ├── report/route.js       # POST /api/report → Python /predict
│       ├── report/what-if/       # POST /api/report/what-if → Groq/OpenRouter
│       ├── chat/                 # POST /api/chat → Groq streaming
│       └── profile/              # GET/POST /api/profile
│
├── components/
│   ├── landing/
│   │   ├── HeroWithModel.jsx     # 3D hero section on landing
│   │   ├── ProfileForm.jsx       # Step 1: name/age/gender/height/weight/diet/activity
│   │   └── HealthDataImport.jsx  # Apple Health XML / Google Fit JSON drag-drop import
│   ├── layout/
│   │   └── AppHeader.jsx         # Sticky nav with avatar dropdown
│   ├── results/
│   │   ├── DashboardLayout.jsx   # Guard: redirects if no report
│   │   ├── DashboardNav.jsx      # Section tabs: Overview / Body Ageing / Organs / Recs
│   │   ├── BiologicalAgeCard.jsx # Chrono vs biological age comparison + gap banner
│   │   ├── StressHeatmap.jsx     # Body system stress levels grid
│   │   ├── OrgansOverview.jsx    # Organ cards with score, risk bar, tooltip
│   │   ├── OrganSection.jsx      # Full organ detail with 3D model
│   │   ├── PriorityRecommendations.jsx  # Action cards by priority
│   │   ├── WhatIfPanel.jsx       # Scenario selector + API-backed projections
│   │   ├── FutureSelfTimeline.jsx # 10-year trajectory chart + threshold alerts
│   │   ├── WellnessScoreCard.jsx # Actuarial wellness tier + insurance risk band
│   │   ├── ProfileSummary.jsx    # Patient avatar, name, BMI, lifestyle chips
│   │   ├── TwinChatPanel.jsx     # Floating AI chat panel with SSE streaming
│   │   ├── PdfExportButton.jsx   # Clinical PDF download
│   │   ├── ShareCardButton.jsx   # PNG share card via html2canvas
│   │   ├── MedicalConditionsSummary.jsx
│   │   ├── YourInputsSummary.jsx
│   │   ├── ReportBodyAgeingSection.jsx
│   │   ├── ReportOrgansSection.jsx
│   │   └── ReportRecommendationsSection.jsx
│   ├── three/
│   │   ├── BodyModelScene.jsx    # Full-body model with ageing tint animation
│   │   ├── BrainModelScene.jsx
│   │   ├── HeartModelScene.jsx
│   │   ├── KidneyModelScene.jsx
│   │   ├── LiverModelScene.jsx
│   │   ├── LungsModelScene.jsx
│   │   ├── HumanModelScene.jsx
│   │   └── DashboardMaleBodyScene.jsx
│   ├── ui/
│   │   ├── AnimatedCounter.jsx   # Eased numeric counter
│   │   ├── DashboardBackground.jsx
│   │   ├── PageBackground.jsx
│   │   └── LenisProvider.jsx
│   └── DigitalTwinLoadingScene.jsx  # Full-screen 4-phase loading overlay
│
├── lib/
│   ├── reportApiServer.js        # toPredictPayload() mapper + API call logic
│   ├── buildChatContext.js       # Assembles system prompt from full report data
│   ├── generatePdf.js            # jsPDF dark-clinical PDF generator
│   ├── parseHealthData.js        # Apple Health XML + Google Fit JSON parsers
│   ├── profileApi.js             # Profile persistence helpers
│   ├── whatIfSimulation.js       # Client-side scenario helpers
│   └── api.js                   # Shared fetch wrappers
│
├── store/
│   └── useStore.js               # Zustand store (profile, input, result, UI state)
│
├── public/
│   └── models/                   # GLTF/GLB 3D model assets
│       ├── brain/
│       ├── heart/
│       ├── liver/
│       ├── lungs/
│       ├── kidney/
│       ├── malebody/
│       ├── femalebody/
│       └── human/
│
├── VITALTWIN-AI-MODEL/           # Python ML service (independent deployment)
│   ├── app.py                    # FastAPI application entry point
│   ├── simulation_engine.py      # Orchestration: 4 verification layers
│   ├── models/
│   │   ├── heart_model.py        # Cardiovascular risk model
│   │   ├── brain_model.py        # Neurological / cognitive model
│   │   ├── liver_model.py        # Hepatic function model
│   │   ├── kidney_model.py       # Renal function model
│   │   ├── lungs_model.py        # Pulmonary model (pack-years, AQI)
│   │   └── base_model.py         # Shared base class
│   ├── features/
│   │   ├── biological_age.py     # Bio-age vs chronological age engine
│   │   ├── vital_score.py        # 0–100 overall health gauge
│   │   ├── stress_heatmap.py     # Per-system stress scoring
│   │   ├── future_self.py        # 10-year projection simulator
│   │   └── what_if_simulator.py  # Scenario delta modelling
│   ├── utils/
│   │   ├── input_validator.py    # Layer 1: input validation
│   │   ├── confidence_scorer.py  # Layer 2: confidence scoring per organ
│   │   ├── consistency_checker.py # Layer 3: cross-organ consistency
│   │   └── medication_modeler.py # Layer 4: drug class effect modelling
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml               # Render.com deploy config
│
├── next.config.mjs
├── jsconfig.json                 # Path alias: @/* → ./
├── package.json
├── postcss.config.mjs
└── CLAUDE.md                     # AI assistant instructions
```

---

## User Journey

```
Step 1 — ProfileForm
  name, age, gender, height, weight, diet, activity level
         ↓
Step 2 — HealthQuestionsPage
  smoking, alcohol, sleep, stress level
  medical conditions (95+ searchable options)
  current medications (tag input)
         ↓
DigitalTwinLoadingScene overlay (4 phases)
  Initialize → Calibrate → Project → Build
         ↓
Promise.allSettled([
  POST /api/profile    (persistence)
  POST /api/report     (ML prediction)
])
         ↓
Dashboard — interactive report
  • Vital Score gauge
  • Biological age vs chronological age
  • Organ health cards (Heart / Brain / Liver / Kidney / Lungs)
  • Body stress heatmap
  • 10-year future self timeline
  • Priority recommendations
  • What-If scenario simulator
  • Wellness & insurance risk score
  • AI Twin chat (streaming)
  • PDF export
  • Share card PNG
```

---

## Frontend — Next.js App

### Pages

| Route | File | Description |
|---|---|---|
| `/` | `app/page.js` | Landing (no report) or full dashboard (has report) |
| `/health-questions` | `app/health-questions/page.js` | Step 2 form + loading overlay |
| `/body-ageing` | `app/body-ageing/page.js` | 3D body ageing slider + timeline |
| `/organs` | `app/organs/page.js` | All 5 organ detail cards |
| `/recommendations` | `app/recommendations/page.js` | Actions + what-if + wellness score |

### State Management

Zustand store at [store/useStore.js](store/useStore.js):

```js
{
  profile: { name, age, gender, height, weight, diet, activity },
  input:   { smoking, alcohol, sleep, stress, medical_conditions[], medications[] },
  result:  {
    vital_score, biological_age, organs,
    body_stress, recommendations,
    future_self, priority_recommendations
  },
  isSubmitting,
  showLoadingScene
}
```

`result` is persisted to `localStorage` under key `vitaltwin_report` and rehydrated on init, so the dashboard survives page refresh.

### API Routes

All routes are **server-side proxies** — API keys never reach the browser.

| Route | Method | Purpose |
|---|---|---|
| `/api/report` | POST | Maps frontend payload → `toPredictPayload()` → Python `/predict` |
| `/api/report/what-if` | POST | Groq → OpenRouter → Python fallback scenario analysis |
| `/api/chat` | POST | Groq SSE streaming for Twin AI chat |
| `/api/profile` | GET/POST | Profile CRUD proxy to `PROFILE_API_URL` |
| `/api/profile/[id]` | GET | Load saved profile by ID |

**What-if priority chain:** `GROQ_API_KEY` → `OPENROUTER_API_KEY` → `REPORT_API_WHATIF_URL` → `/predict` fallback

### 3D Models

All Three.js components use `dynamic(() => import(...), { ssr: false })` because Three.js requires browser APIs unavailable during server-side rendering.

GLTF/GLB assets live in `public/models/` and are loaded via `useGLTF` from `@react-three/drei`.

**Animated body ageing** (`BodyModelScene.jsx`): `applyAgeingTint()` applies material-level ageing — emissive glow (`#22100a`), +0.35 roughness, decreased metalness. A reactive `pointLight` pulses amber in `useFrame` proportional to `ageingLevel`.

**Zoom disabled** on all models: all `OrbitControls` use `enableZoom={false}`.

### Key Features

#### Twin AI Chat
- Floating panel (right side) with streaming SSE tokens from Groq
- System prompt built by `buildChatContext.js` from full report: organ scores, vital score, bio age, medications, top recommendations
- Streams `llama-3.3-70b-versatile` via `ReadableStream`; `AbortController` cleans up on close
- Renders `**bold**` inline markdown

#### What-If Scenarios
- Each scenario has `id`, `name`, `showWhen(input, profile)`, `changes` (partial payload sent to Groq/OpenRouter)
- Results cached per `scenarioId` to avoid repeated API calls
- Special `"current"` scenario returns existing report unchanged
- Returns projected organ scores, vital score, delta recommendations

#### PDF Export
- Dynamic import of `lib/generatePdf.js` (jsPDF + jspdf-autotable)
- Dark-themed clinical PDF: patient info bar, vital score, organ health table, stress table, future trajectory, recommendations, medications
- File: `VitalTwin-{name}-{date}.pdf`

#### Wearable Data Import
- Drag-drop zone: `.xml` (Apple Health) and `.json` (Google Fit)
- Apple Health: extracts Height, BodyMass, SleepAnalysis (30-day avg), HeartRate, StepCount
- Google Fit: extracts height, weight, sleep sessions (30-day avg), steps
- `normalizeImportedData()` maps parsed values to Zustand store fields

#### Wellness & Insurance Score
- Derived actuarially from vital score, age gap, RED/YELLOW organ count
- Outputs: **Wellness Tier** (Excellent/Good/Moderate/High-Risk), **Health Cost Index** (multiplier vs average), **Insurance Risk Band** (Low/Standard/Elevated/High)

#### Risk Trajectory Alerts
- `RISK_THRESHOLDS`: Critical (<40 vitality), Elevated (<60)
- `findThresholdCrossing()` linearly interpolates between timeline pairs to find the exact fractional year of crossing
- Alert banners above timeline; marker dots at `(crossYear / maxYear) × 100%`

### Design System

**Color palette** (CSS variables in `app/globals.css`):

```css
--background:          #F8FAFB    /* Warm neutral white */
--color-primary:       #059669    /* Emerald — main accent */
--color-primary-deep:  #047857    /* Emerald dark — hover states */
--color-scan:          #34D399    /* Bright emerald — glow effects */
--color-accent:        #fbbf24    /* Amber — secondary highlight */
--color-surface:       #FFFFFF    /* Card background */
--color-muted:         #64748b    /* Secondary text */
```

**Risk status colors:**
- `RED` → `text-red-600`, `border-red-200`, `bg-red-50`
- `YELLOW` → `text-amber-600`, `border-amber-200`, `bg-amber-50`
- `GREEN` → `text-emerald-600`, `border-emerald-200`, `bg-emerald-50`

**Tailwind v4 syntax** — CSS variable references use `(--x)` not `[var(--x)]`:
```jsx
// Correct
className="text-(--color-primary) bg-(--color-surface)"
// Wrong
className="text-[var(--color-primary)]"
```

**Fonts:**
- **Poppins** (400/500/600/700) — body and headings
- **Geist Mono** — technical labels, data readouts

**Utility classes** (defined in `globals.css`):

| Class | Effect |
|---|---|
| `.glass-card` | Frosted glass card (backdrop-blur, teal border) |
| `.bg-dot-grid` | 20×20px dot grid background pattern |
| `.text-glow` | Emerald text-shadow glow |
| `.hover-lift` | translateY(-2px) + box-shadow on hover |
| `.scan-ring` | Pulsing border ring around 3D models |
| `.float-subtle` | translateY(-3px) 4s infinite float |
| `.gauge-pulse` | Opacity 0.85→1 2s infinite |
| `.pulse-wave-bg` | Radial gradient breathing animation |

---

## Backend — Python ML Service

Located in `VITALTWIN-AI-MODEL/`. Entirely decoupled from the Next.js app — communicates only via HTTP.

### Organ Models

Each model in `models/` inherits from `BaseModel` and produces a `risk_level` (`RED` / `YELLOW` / `GREEN`), a `health_score` (0–100), and a list of `possible_issues`.

| Model | File | Key Inputs |
|---|---|---|
| Heart | `heart_model.py` | BP, cholesterol, family history, smoking, BMI, stress |
| Brain | `brain_model.py` | Sleep, stress, alcohol, age, BP |
| Liver | `liver_model.py` | Alcohol, BMI, AST/ALT/GGT, medications |
| Kidney | `kidney_model.py` | BP, creatinine, diabetes status, NSAIDs |
| Lungs | `lungs_model.py` | Smoking (pack-years), AQI (city lookup), cooking fuel |

### Feature Engines

| Engine | File | Output |
|---|---|---|
| BiologicalAgeEngine | `biological_age.py` | Biological age, age gap, contributing factors |
| VitalScoreGauge | `vital_score.py` | 0–100 overall health score |
| BodyStressHeatmap | `stress_heatmap.py` | Per-system stress levels (cardiovascular, neurological, etc.) |
| FutureSelfSimulator | `future_self.py` | 10-year vitality trajectory (yearly snapshots) |
| WhatIfSimulator | `what_if_simulator.py` | Delta analysis for lifestyle changes |

### Verification Layers

The `VitalTwinSimulator` runs 4 layers on every prediction:

1. **Input Validation** (`input_validator.py`) — range checks, required fields, outlier flags
2. **Confidence Scoring** (`confidence_scorer.py`) — per-organ confidence based on available lab values
3. **Cross-Organ Consistency** (`consistency_checker.py`) — flags contradictory risk signals between organs
4. **Medication Effect Modelling** (`medication_modeler.py`) — adjusts organ scores for known drug classes (antihypertensives, statins, metformin, etc.)

### API Endpoints

```
POST /predict
  Body: { profile: ProfileInfo, health: HealthInfo }
  Returns: full health report (organs, vital_score, biological_age, ...)

POST /what-if  (optional dedicated endpoint)
  Body: { profile, health, changes }
  Returns: delta report for scenario changes
```

### Input / Output Schema

**ProfileInfo** (key fields):
```python
Age, Gender, Height (cm), Weight (kg)
Diet: "Poor" | "Average" | "Good"
ActivityLevel: "Sedentary" | "Moderate" | "Active"
City, State  # for Indian AQI / disease prevalence priors
```

**HealthInfo** (key fields):
```python
Smoking: "Never" | "Occasional" | "Daily"
Alcohol: "Never" | "Occasional" | "Weekly" | "Daily"
Sleep: float  # hours/night
Stress: "Low" | "Medium" | "High"
MedicalConditions: List[str]
Medications: List[str]
Bmi: float  # calculated frontend-side

# Optional lab values
SystolicBP, DiastolicBP
TotalCholesterol, HDL, LDL, Triglycerides
FastingGlucose, HbA1c
SerumCreatinine, AST, ALT, GGT, Albumin, Platelets
```

**Report response shape** (consumed by frontend store):
```json
{
  "vital_score": 72,
  "biological_age": 38,
  "organs": {
    "heart":  { "risk_level": "YELLOW", "health_score": 65, "possible_issues": [...] },
    "brain":  { "risk_level": "GREEN",  "health_score": 81, "possible_issues": [] },
    "liver":  { ... },
    "kidney": { ... },
    "lungs":  { ... }
  },
  "body_stress": { "cardiovascular": 0.6, "neurological": 0.3, ... },
  "recommendations": [...],
  "priority_recommendations": [...],
  "future_self": [
    { "year": 1, "vital_score": 71, ... },
    ...
    { "year": 10, "vital_score": 58, ... }
  ],
  "biological_age_details": { "gap": 5, "factors": [...] }
}
```

The `getOrganStatus()` helper in the Zustand store maps: `RED` → `"critical"`, `YELLOW` → `"at-risk"`, else → `"healthy"`. This drives 3D model coloring, badge styles, and sort order (RED first).

---

## Environment Variables

Create `.env.local` in the project root:

```env
# ── Python ML backend ──────────────────────────────────────────────
REPORT_API_URL=https://your-backend.com
# or (public, exposed to browser):
NEXT_PUBLIC_REPORT_API_URL=https://your-backend.com

# ── Groq AI — twin chat + what-if (primary) ───────────────────────
GROQ_API_KEY=gsk_...
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
GROQ_WHATIF_MODEL=llama-3.3-70b-versatile

# ── OpenRouter — what-if fallback ─────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_WHATIF_MODEL=google/gemini-2.0-flash-exp

# ── Dedicated what-if endpoint (optional) ─────────────────────────
REPORT_API_WHATIF_URL=https://your-backend.com/what-if

# ── Profile persistence backend ───────────────────────────────────
PROFILE_API_URL=https://vitaltwin-backend.onrender.com
PROFILE_API_PATH=profile

# ── Optional path overrides ───────────────────────────────────────
REPORT_API_PREDICT_PATH=predict
REPORT_API_WHATIF_PATH=what-if
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

What-if AI priority: `GROQ_API_KEY` → `OPENROUTER_API_KEY` → `REPORT_API_WHATIF_URL` → `/predict` fallback.

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- npm or yarn

### Frontend

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

### Python Backend

```bash
cd VITALTWIN-AI-MODEL

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at `http://localhost:8000`. Set `REPORT_API_URL=http://localhost:8000` in your `.env.local`.

---

## Deployment

### Frontend — Vercel (recommended)

1. Push to GitHub
2. Import repo in [vercel.com](https://vercel.com)
3. Set all environment variables in the Vercel dashboard
4. Deploy — Vercel handles the Next.js build automatically

### Backend — Render

A `render.yaml` is included in `VITALTWIN-AI-MODEL/` with pre-configured Render.com deployment settings. The `Dockerfile` can also be used for any container platform (Railway, Fly.io, GCP Cloud Run, etc.).

```dockerfile
# Build and run locally with Docker
cd VITALTWIN-AI-MODEL
docker build -t vitaltwin-api .
docker run -p 8000:8000 vitaltwin-api
```

### Path Aliases

`@/*` maps to the project root, configured in `jsconfig.json`:

```json
{
  "compilerOptions": {
    "paths": { "@/*": ["./*"] }
  }
}
```

All imports use `@/components/...`, `@/lib/...`, `@/store/...`.
