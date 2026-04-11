# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start development server on :3000
npm run build    # Build for production
npm start        # Run production build
npm run lint     # Run ESLint
```

No test framework is configured.

---

## What This App Does

**VitalTwin** is a health digital twin platform. Users fill a 2-step form (profile + lifestyle), which gets sent to a Python ML backend that returns a health report containing biological age, vital score, organ health, stress heatmap, and future predictions. The frontend renders an interactive 3D dashboard with what-if scenario simulation, AI chat, PDF export, and wellness scoring.

**User Journey:** ProfileForm (Step 1) → HealthQuestionsPage (Step 2) → DigitalTwinLoadingScene overlay → Report dashboard.

---

## Architecture

### State & Data Flow

Zustand store at [store/useStore.js](store/useStore.js):

```
profile  { name, age, gender, height, weight, diet, activity }
input    { smoking, alcohol, sleep, stress, medical_conditions[], medications[] }
result   { vital_score, biological_age, organs, body_stress, recommendations, future_self, priority_recommendations }
isSubmitting
```

`result` persists to `localStorage` under key `vitaltwin_report` and is rehydrated on init.

**Report Generation Flow:**
```
HealthQuestionsPage.handleGenerateReport()
  → clearResult() + setShowLoadingScene(true)
  → Promise.allSettled([
      saveSubmission(profile, input),   ← /api/profile (persistence)
      submitReport(profile, input)      ← /api/report  (ML prediction)
    ])
  → setResult(report) → router.push('/')
```

**What-If Flow:**
```
User selects scenario in WhatIfPanel
  → fetchWhatIfScenario(profile, input, changes, { currentReport, scenarioId })
  → POST /api/report/what-if
  → If GROQ_API_KEY: calls Groq llama-3.3-70b-versatile with full context
  → Else if OPENROUTER_API_KEY: calls OpenRouter Gemini
  → Else: calls REPORT_API_WHATIF_URL or falls back to /predict
  → Returns projected organ scores, vital score, recommendations
```

**Twin Chat Flow:**
```
User opens chat panel → buildSystemPrompt(profile, input, result)
  → POST /api/chat with messages[]
  → Groq streaming (llama-3.3-70b-versatile) via SSE
  → ReadableStream piped to client → TwinChatPanel renders tokens
```

### API Routes (All Server-Side Proxies)

| Route | Purpose |
|-------|---------|
| `POST /api/report` | Profile+input → `toPredictPayload()` → backend `/predict` |
| `POST /api/report/what-if` | Scenario analysis via Groq → OpenRouter → backend fallback |
| `POST /api/chat` | Twin AI chat — Groq streaming SSE |
| `GET/POST /api/profile` | Profile CRUD proxy to PROFILE_API_URL |
| `GET /api/profile/[id]` | Load saved profile by ID |

The `toPredictPayload()` in [lib/reportApiServer.js](lib/reportApiServer.js) maps frontend fields to `ProfileInfo` / `HealthInfo` shapes expected by the Python backend. BMI is calculated frontend-side to avoid backend division errors.

### 3D Models (Three.js / React Three Fiber)

All 3D components must use `dynamic(() => import(...), { ssr: false })` — Three.js requires browser APIs unavailable during SSR. GLTF/GLB model files live in [public/models/](public/models/) organized by `brain/`, `heart/`, `femalebody/`, `malebody/`, `liver/`, `lungs/`, `kidneys/`.

**Animated Aging** ([components/three/BodyModelScene.jsx](components/three/BodyModelScene.jsx)): `applyAgeingTint()` applies material-level aging via emissive glow (`#22100a`), roughness increase (+0.35), metalness decrease. A reactive `pointLight` pulses amber in `useFrame` — intensity proportional to `ageingLevel`.

### What-If Scenario System

[components/results/WhatIfPanel.jsx](components/results/WhatIfPanel.jsx) — real API-backed scenarios. Each scenario has `id`, `name`, `showWhen(input, profile)`, and `changes` (partial `ProfileInfo`/`HealthInfo` payload sent to Groq). Results are cached per `scenarioId` to avoid repeated API calls. The special `"current"` scenario returns the current report unchanged.

### Organ Status Mapping

Backend returns `organs: { heart: { risk_level: "RED" | "YELLOW" | ... } }`.

`getOrganStatus(organId)` in the store maps: `RED` → `"critical"`, `YELLOW` → `"at-risk"`, else → `"healthy"`. This drives 3D model coloring, badge styles, and sort order in [components/results/ReportOrgansSection.jsx](components/results/ReportOrgansSection.jsx) (sorted RED > YELLOW > GREEN).

---

## Design System & Theme

### Color Palette (CSS variables in [app/globals.css](app/globals.css))

```css
--background / --color-bg:    #080a0d      /* Dark navy — base bg */
--foreground:                 #e8ecf1      /* Light gray — body text */
--color-primary:              #14b8a6      /* Teal — main accent, borders, buttons */
--color-scan:                 #2dd4bf      /* Brighter teal — scan/glow effects */
--color-accent:               #fbbf24      /* Amber — secondary highlight */
--color-surface:              #0f1216      /* Card background */
--color-surface-border:       rgba(20,184,166,0.2)  /* Teal border default */
--color-muted:                #64748b      /* Secondary text */
--color-muted-dim:            #475569      /* Subtle/disabled text */
```

**Risk/Status Colors** (applied dynamically throughout dashboard):
- `RED` → `text-red-400`, `border-red-500/30`, `bg-red-950/60`
- `YELLOW` → `text-amber-400`, `border-amber-500/30`, `bg-amber-950/50`
- `GREEN` → `text-emerald-400`, `border-emerald-500/30`, `bg-emerald-950/50`

### Tailwind v4 Class Syntax

**Critical:** Use canonical Tailwind v4 syntax for CSS variables — `(--x)` not `[var(--x)]`:

```
// Correct
className="text-(--color-primary) bg-(--color-surface)"
// Wrong — IDE will warn
className="text-[var(--color-primary)] bg-[var(--color-surface)]"
```

Standard token names (`text-foreground`, `bg-background`) do NOT need the `(--x)` wrapper.

### Fonts

- **Poppins** (Google Fonts, weights 400/500/600/700) — body and headings, letter-spacing: -0.05em
- **Geist Mono** (Google Fonts) — technical labels, data displays, tactical UI

### Typography Hierarchy

```
Page heading:    text-xl md:text-2xl font-semibold text-glow-primary
Section label:   text-xs font-medium uppercase tracking-wider text-primary
Card title:      text-sm font-semibold
Data label:      text-xs font-medium uppercase tracking-[0.1em]
Body:            text-sm text-muted
```

### Card / Panel Styles

Three main card variants used throughout:

1. **`.glass-card`** (glassmorphism) — `bg-[rgba(15,22,28,0.6)]`, `backdrop-blur-[16px]`, teal border at 15% opacity, inner highlight shadow
2. **Lab Panel** (clinical) — solid `bg-[rgba(15,18,22,0.95)]`, teal border at 20% opacity
3. **`.game-hud-frame`** (tactical HUD) — corner bracket decorations via `::before`/`::after` pseudo-elements, `.game-panel` top border gradient

### CSS Utility Classes (defined in globals.css)

| Class | Effect |
|-------|--------|
| `.bg-dot-grid` | 20×20px teal dot grid background pattern |
| `.text-glow` | Teal text-shadow glow (0 0 24px, 0 0 48px) |
| `.game-hud-frame` | Corner bracket decorations |
| `.letterbox` | Cinematic vignette (inset top/bottom 8vh shadows) |
| `.float-subtle` | translateY(-3px) 4s infinite float |
| `.gauge-pulse` | Opacity 0.85→1 2s infinite (health metrics) |
| `.scan-ring` | Pulsing circle border around 3D models (scale 0.3→1.4, 2.5s) |

### Animations

- **Scan line**: Linear gradient sweeping down, 8s infinite — loading/cinematic effect
- **Pulse wave bg**: Radial gradient breathing, two waves offset by 4s — `DashboardBackground`
- **Scan ring**: `scale(0.3)` → `scale(1.4)` ease-out-expo 2.5s — around 3D body model
- **AnimatedCounter**: Numbers ease from 0 to target via `easeOutQuad`, default 1200ms
- **GSAP staggered entrance**: `fromTo` with `power3.out` easing, 0.08s stagger per field — profile form
- **`prefers-reduced-motion`**: All animations set to `0.01ms` duration

### Background Layers

- **[components/ui/PageBackground.jsx](components/ui/PageBackground.jsx)** (all pages): dot grid + linear gradient (teal→black) + vignette + SVG film grain
- **[components/ui/DashboardBackground.jsx](components/ui/DashboardBackground.jsx)** (dashboard only): adds pulsing wave overlay

### Smooth Scroll

[components/ui/LenisProvider.jsx](components/ui/LenisProvider.jsx) wraps the app. Config: duration 1.2s, custom exponential decay easing, wheel×1 touch×2. Auto-disabled if `prefers-reduced-motion`.

---

## Pages & Layout

### [app/page.js](app/page.js) — Home / Dashboard

**Two states based on whether `result` exists in store:**

1. **Landing** (no result): 2-column grid — `HeroWithModel` (3D left) + `ProfileForm` (right, Step 1) + `HealthDataImport` drag-drop zone
2. **Dashboard** (has result):
   - Sticky `AppHeader` with nav + profile popup
   - 3-column main section: 3D body model (left) + VitalScoreCard (top-right) + StressHeatmap (bottom-right)
   - Report sections below: `ReportBodyAgeingSection`, `ReportOrgansSection`, `ReportRecommendationsSection` (contains `WhatIfPanel`, `WellnessScoreCard`)
   - Floating `PdfExportButton` + `ShareCardButton` + "Ask your Twin" chat button
   - `TwinChatPanel` slides in from right when chat is open

### [app/health-questions/page.js](app/health-questions/page.js) — Step 2

- Left: 3D HeartModelView with scan line + spotlight cinematic effect
- Right: Form with 4 required selects + custom searchable multi-select for 95+ medical conditions + `MedicationsField` tag-input for current medications
- `DigitalTwinLoadingScene` full-screen overlay on submit (4-phase animation with progress bar)
- Error: red alert box listing missing required fields

### Dashboard Navigation ([components/results/DashboardNav.jsx](components/results/DashboardNav.jsx))

4 sections using pathname-based active state: Dashboard → Body Ageing → Organs → Recommendations.

---

## Feature Components

### Twin AI Chat ([components/results/TwinChatPanel.jsx](components/results/TwinChatPanel.jsx))

Floating panel (right side). Opens with auto-generated greeting via `buildInitialGreeting()`. Streams tokens from `POST /api/chat` using SSE `ReadableStream`. Renders `**bold**` markdown inline. AbortController cleans up on panel close. System prompt from [lib/buildChatContext.js](lib/buildChatContext.js) includes full report data (organ scores, vital score, bio age, top recommendations, medications).

### PDF Export ([components/results/PdfExportButton.jsx](components/results/PdfExportButton.jsx))

Dynamically imports [lib/generatePdf.js](lib/generatePdf.js) (jsPDF + jspdf-autotable). Generates a dark-themed clinical PDF: patient info bar, vital score/bio age boxes, organ health table, body stress table, future trajectory table, recommendations table, health inputs + medications. File: `VitalTwin-{name}-{date}.pdf`.

### Shareable Report Card ([components/results/ShareCardButton.jsx](components/results/ShareCardButton.jsx))

Opens modal with [components/results/ShareableCard.jsx](components/results/ShareableCard.jsx) preview. Uses `html2canvas` at `scale: 2` to capture as PNG. **Important:** `ShareableCard` uses hardcoded hex colors (e.g. `#14b8a6`, `#080a0d`) — html2canvas cannot resolve CSS custom properties.

### Wearable Data Import ([components/landing/HealthDataImport.jsx](components/landing/HealthDataImport.jsx))

Drag-drop zone accepting `.xml` (Apple Health) and `.json` (Google Fit). Parsers in [lib/parseHealthData.js](lib/parseHealthData.js):
- Apple Health: extracts HKQuantityTypeIdentifierHeight, BodyMass, SleepAnalysis (30-day average), HeartRate, StepCount
- Google Fit: extracts height, weight, sleep sessions (30-day average), steps
- `normalizeImportedData()` maps parsed values to store field names (`profileFields.height`, `profileFields.weight`, `inputFields.sleep`)

### Risk Trajectory Alerts ([components/results/FutureSelfTimeline.jsx](components/results/FutureSelfTimeline.jsx))

`RISK_THRESHOLDS` defines Critical (<40 vitality) and Elevated (<60) bands. `findThresholdCrossing()` linearly interpolates between consecutive timeline pairs to find the fractional year when a threshold is crossed. Alert banners show above the timeline and marker dots are positioned at `(crossYear / maxYear) * 100%`.

### Wellness / Insurance Score ([components/results/WellnessScoreCard.jsx](components/results/WellnessScoreCard.jsx))

Derives actuarial-style scores from report data:
- `riskMultiplier` from vital score, age gap, RED/YELLOW organ count
- **Wellness Tier**: Excellent / Good / Moderate / High-Risk
- **Health Cost Index**: multiplier vs average (e.g. ×1.3)
- **Insurance Risk Band**: Low / Standard / Elevated / High
- Displayed in [components/results/ReportRecommendationsSection.jsx](components/results/ReportRecommendationsSection.jsx)

### Medications Input ([components/results/MedicationsField.jsx](components/results/MedicationsField.jsx))

Tag-input component: type + Enter to add, click × or Backspace to remove, teal-styled pills. Values stored in `input.medications[]` in Zustand. Flow: HealthQuestionsPage → Zustand → `toPredictPayload()` (as `Medications[]` in `HealthInfo`) → PDF export → Twin chat context → `MedicalConditionsSummary` display.

---

## Component Library Patterns

### Recurring Interactive Elements

- **Buttons**: `border border-primary/50 bg-primary/10` + hover `scale-105` + `translateY(-2px)` lift
- **Inputs/Selects**: `bg-white/5 border border-white/10` + teal focus ring `ring-2 ring-primary/50`
- **Range sliders**: Teal thumb, white/10 track
- **Hover tooltips**: Absolute-positioned panels with `z-50`, appear on `:hover`/`:focus-within`

### AnimatedCounter ([components/ui/AnimatedCounter.jsx](components/ui/AnimatedCounter.jsx))

```jsx
<AnimatedCounter value={85} duration={1200} suffix="%" />
```

Uses `easeOutQuad` easing. Supports decimals. Falls back to static value if non-numeric.

### Error & Loading Patterns

- **Form errors**: Field-level red text + `aria-invalid` / `aria-describedby`
- **Page errors**: `role="alert"` red banner (`bg-red-950/40 border-red-500/30`)
- **API errors**: Friendly messages for 404, 502, 503 with cause explanation
- **Loading**: `DigitalTwinLoadingScene` overlay (full-screen, 4 phases: Initialize→Calibrate→Project→Build)

---

## Environment Variables

```env
# Required — Python ML backend base URL
REPORT_API_URL=https://your-backend.com
# or: NEXT_PUBLIC_REPORT_API_URL=https://your-backend.com

# Groq AI (twin chat + what-if) — preferred over OpenRouter
GROQ_API_KEY=gsk_...
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
GROQ_WHATIF_MODEL=llama-3.3-70b-versatile

# What-if fallback: OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_WHATIF_MODEL=google/gemini-2.0-flash-exp

# Dedicated what-if backend endpoint (optional — falls back to /predict)
REPORT_API_WHATIF_URL=https://your-backend.com/what-if

# Profile persistence backend
PROFILE_API_URL=https://vitaltwin-backend.onrender.com
PROFILE_API_PATH=profile   # or: submissions

# Optional path overrides
REPORT_API_PREDICT_PATH=predict
REPORT_API_WHATIF_PATH=what-if
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

The what-if route priority: `GROQ_API_KEY` → `OPENROUTER_API_KEY` → `REPORT_API_WHATIF_URL` → `/predict` fallback.

---

## Python Backend

Separate ML service in [VITALTWIN-AI-MODEL/](VITALTWIN-AI-MODEL/) with its own `requirements.txt` and `Dockerfile`. Exposes `/predict` and optionally `/what-if`. The Next.js app proxies to it — they are entirely decoupled.

## Path Aliases

`@/*` → `./` (project root), configured in [jsconfig.json](jsconfig.json). All imports use `@/components/...`, `@/lib/...`, `@/store/...`.

## Key npm Packages Added

- `jspdf` + `jspdf-autotable` — clinical PDF generation (dynamic import, client-only)
- `html2canvas` — report card PNG capture (client-only, no CSS variable support)
