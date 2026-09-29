# VitalTwin — Integration Roadmap
*Created: April 2026 | Focus: Open APIs, Real Data Pipelines, No-Partner Integrations*

---

## 🎯 North Star Goal

Transform VitalTwin from a **form-based health calculator** into a **living digital twin** — one that reads your real medical documents, pulls live environment data, checks your medications, and continuously updates your risk profile. All using free/open APIs that can be integrated today.

---

## 💡 THE BIG IDEA: Medical Document Intelligence

> *"User uploads their prescription and blood test report → AI reads and extracts all clinical values → organ risk scores automatically update with real lab data"*

This is the highest-impact feature gap in the current platform. Here's the full architecture for how to build it right:

---

### 📄 Feature: Smart Medical Document Upload

#### **The Problem Today**
- Kidney confidence = 55% because we don't have creatinine
- Liver FIB-4 needs AST, ALT, platelets — user has to type them manually
- Brain CAIDE needs cholesterol — user has to know their number
- Users have this data on paper/PDF lab reports but can't easily use it

#### **The Solution: AI-Powered Lab Report Parser**

```
User uploads PDF/image of lab report
        ↓
[Step 1] Extract text (PDF.js for PDF, Tesseract.js for images)
        ↓
[Step 2] Send text to Groq LLaMA-3 with structured extraction prompt
        ↓
[Step 3] Groq returns JSON: { creatinine: 1.2, ast: 34, alt: 28, hba1c: 6.8, ... }
        ↓
[Step 4] Values auto-populate the health form fields
        ↓
[Step 5] Re-run prediction with enriched data → organ scores update
        ↓
Result: Kidney goes from 55% confidence → 92% confidence
```

#### **What Values Can Be Extracted**

| Lab Value | Used By | Confidence Impact |
|---|---|---|
| Serum Creatinine | Kidney (CKD-EPI) | 55% → 92% |
| AST, ALT | Liver (FIB-4, APRI) | Improves FIB-4 accuracy |
| Platelet Count | Liver (FIB-4) | Required for FIB-4 |
| Total Cholesterol / LDL | Heart (PCE), Brain (CAIDE) | Improves both |
| HbA1c / Fasting Glucose | Heart, Kidney, Brain | All 3 organs benefit |
| Systolic / Diastolic BP | Heart (PCE), Brain | Enables Stage 2 HTN detection |
| FEV1% | Lungs (GOLD staging) | GOLD A/B/C/D classification |
| eGFR (if reported) | Kidney | Direct CKD stage input |
| Hemoglobin | Biological Age | KDM calibration |
| Uric Acid | Kidney, Biological Age | Gout risk + bio age signal |

#### **Prescription Parser (separate flow)**

```
User uploads prescription image/PDF
        ↓
Groq extracts: { medications: ["Metformin 500mg", "Atorvastatin 10mg"], 
                 conditions: ["Type 2 Diabetes", "Dyslipidemia"],
                 doctor_notes: "Follow up in 3 months" }
        ↓
Medications → auto-populate MedicationsField
Conditions → auto-add to MedicalConditions checklist
        ↓
OpenFDA API checks interactions between all medications
        ↓
Results panel shows: "⚠️ Metformin + Ibuprofen: increased kidney stress risk"
```

#### **How to Make It Even Better**

1. **Camera capture on mobile** — "Take photo of your report" button using `<input type="file" capture="environment">` — works on all Android/iOS phones without any app
2. **Multi-language support** — Many Indian lab reports are in Hindi/regional languages. Groq LLaMA-3 handles multilingual extraction natively
3. **Report history** — Store extracted values timestamped so user can see trends over time ("Your creatinine was 1.1 in Jan, 1.3 in April — kidney function declining")
4. **Lab reference range validation** — Cross-check extracted value against lab's own reference range printed on the report to flag if it was already flagged by the lab
5. **Confidence badge update** — After upload, show animated badge change: "Kidney accuracy: 55% → 92%" to reward the user for uploading

#### **Tech Stack Required**
| Component | Library | Cost |
|---|---|---|
| PDF text extraction | `pdf.js` (Mozilla, free) or `pdfjs-dist` | Free |
| Image OCR | `Tesseract.js` (free) | Free |
| AI extraction | Groq LLaMA-3 (already integrated) | Free tier |
| Drug interactions | OpenFDA + NIH RxNav APIs | Free, no key |

---

## 🌬️ Integration 1: Live Air Quality (OpenAQ API)

### Why
- Lungs model currently uses **static 2023 CPCB AQI averages** per city
- Real AQI fluctuates massively (Delhi: 48 µg/m³ in summer → 350+ in November)
- A user checking their lungs risk in November gets a completely different (accurate) picture than March

### How It Works
```
User enters city in profile form (or auto-detected via GPS)
        ↓
Frontend calls: GET /api/aqi?city=Delhi
        ↓
Next.js API route calls OpenAQ: 
  https://api.openaq.org/v3/locations?city=Delhi&parameter=pm25&limit=5
        ↓
Returns current PM2.5 (µg/m³)
        ↓
PM2.5 sent to backend as extra field: { air_quality_pm25: 187 }
        ↓
Lungs model uses real-time PM2.5 instead of annual average
        ↓
Results page shows: "Current AQI in Delhi: 187 µg/m³ (Very Unhealthy)"
```

### OpenAQ API Details
- **URL:** `https://api.openaq.org/v3/locations`
- **No API key required** for public access (100 req/hour free)
- **Coverage:** 200+ Indian cities including Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Pune, Kolkata
- **Parameters:** `pm25`, `pm10`, `no2`, `o3`
- **Fallback:** Use existing CPCB static data if city not found

### Files to Create/Modify
- `client/app/api/aqi/route.js` — new Next.js API route (proxy to OpenAQ)
- `client/components/landing/ProfileForm.jsx` — add AQI badge next to city field
- `model/models/lungs_model.py` — accept `air_quality_pm25` override field

### Impact on Lungs Score
| Scenario | Old (static) | New (live) |
|---|---|---|
| Delhi, November | PM2.5: 99 µg/m³ (annual avg) | PM2.5: 280 µg/m³ (actual) |
| Delhi, July | PM2.5: 99 µg/m³ (annual avg) | PM2.5: 48 µg/m³ (actual) |
| Chennai, any month | PM2.5: 38 µg/m³ | PM2.5: 31 µg/m³ (actual) |

---

## 📍 Integration 2: Auto Location → District Health Priors

### Why
- `district_priors.py` has NFHS-5 data for **706 districts** (636,699 households surveyed)
- Currently: user must manually know their district — many users skip this
- Priors affect Heart (HTN prevalence), Brain (stroke), Lungs (TB state multiplier)

### How It Works
```
Profile form loads → "Use my location for accurate district health data?" [Allow]
        ↓
Browser: navigator.geolocation.getCurrentPosition()
        ↓
Coordinates sent to: 
  https://nominatim.openstreetmap.org/reverse?lat=28.6&lon=77.2&format=json
        ↓
Returns: { address: { state: "Delhi", county: "Central Delhi", city: "New Delhi" } }
        ↓
District name sent to backend → district_priors.py loads matching prior
        ↓
Results show: "📍 Central Delhi — High HTN prevalence district (NFHS-5: 34.2%)"
```

### API Details
- **Nominatim:** `https://nominatim.openstreetmap.org/reverse` — Free, no key, OpenStreetMap
- **Rate limit:** 1 req/sec (more than enough for single user calls)
- **Privacy:** Coordinates are reverse-geocoded to district name only — raw GPS never stored

### Files to Create/Modify
- `client/components/landing/ProfileForm.jsx` — add location permission button
- `client/app/api/geocode/route.js` — proxy to Nominatim (avoids CORS)
- `model/utils/district_priors.py` — already ready, just needs district string input

---

## 💊 Integration 3: Drug Interaction Checker (OpenFDA + NIH RxNav)

### Why
- `MedicationsField.jsx` already collects user medications
- Currently: medications list is stored but **not used in any risk calculation**
- Many Indian patients on polypharmacy (multiple medications) have undetected interaction risks

### How It Works
```
User enters medications: ["Metformin", "Atorvastatin", "Amlodipine"]
        ↓
On results page: POST /api/drug-interactions { medications: [...] }
        ↓
Next.js route:
  Step 1 — NIH RxNorm: resolve drug names to RxCUI codes
    GET https://rxnav.nlm.nih.gov/REST/rxcui.json?name=Metformin
  Step 2 — NIH Drug Interactions:
    GET https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=6809+83367+17767
        ↓
Returns: [
  { pair: ["Metformin", "Ibuprofen"], severity: "moderate", description: "NSAIDs may reduce Metformin efficacy and increase kidney stress" },
  { pair: ["Atorvastatin", "Amlodipine"], severity: "minor", description: "May slightly increase statin levels" }
]
        ↓
Display in results: ⚠️ Drug Interactions panel in MedicalConditionsSummary
        ↓
Also feed back to organ models:
  - NSAIDs + Metformin → kidney risk +0.05
  - Warfarin → hemorrhagic stroke risk flag in brain model
```

### API Details
- **NIH RxNav:** `https://rxnav.nlm.nih.gov/REST/` — Free, no key, US National Library of Medicine
- **OpenFDA:** `https://api.fda.gov/drug/label.json` — Free, no key, FDA
- **Coverage:** 10,000+ drugs including all common Indian generics (Metformin, Atorvastatin, Amlodipine, Losartan, Aspirin, etc.)
- **Fallback:** OpenFDA adverse events API as secondary source

### Files to Create/Modify
- `client/app/api/drug-interactions/route.js` — new Next.js route
- `client/components/results/MedicalConditionsSummary.jsx` — add interactions panel
- `model/models/kidney_model.py` — NSAID flag input
- `model/models/brain_model.py` — anticoagulant flag input

---

## 🧾 Integration 4: Groq Lab Report Text Parser

### Why
This is the **highest confidence multiplier** available — creatinine alone takes kidney from 55% → 92%.

### How It Works
```
User pastes raw lab report text (or uploads — see Big Idea above)
        ↓
POST /api/parse-lab { text: "...raw lab text..." }
        ↓
Groq LLaMA-3 system prompt:
  "You are a medical data extractor. Extract ALL numeric lab values from this text.
   Return ONLY valid JSON: { creatinine: null, ast: null, alt: null, platelets: null,
   cholesterol: null, ldl: null, hdl: null, hba1c: null, glucose: null,
   systolic_bp: null, diastolic_bp: null, fev1_percent: null, hemoglobin: null }
   Fill null for any value not found. Use SI units."
        ↓
Returns: { creatinine: 1.2, ast: 34, alt: 28, cholesterol: 218, hba1c: 7.1 }
        ↓
Auto-fills form fields + re-runs prediction with enriched data
        ↓
Confidence badges update: 
  Kidney: 55% → 92% ✅
  Liver FIB-4: "estimated" → "calculated" ✅
  Heart: standard → high accuracy ✅
```

### Groq API Details
- **Already integrated** — `GROQ_API_KEY` in `.env.local`
- **Model:** `llama-3.3-70b-versatile` (already configured)
- **Cost:** Free tier covers 14,400 requests/day
- **Latency:** ~500ms for extraction

### Files to Create/Modify
- `client/app/api/parse-lab/route.js` — new Next.js API route
- `client/components/results/OrganSection.jsx` — "Upload Lab Report" button
- `client/components/results/YourInputsSummary.jsx` — show extracted values + source badge

---

## 📊 Integration 5: Longitudinal Health Tracking

### Why
- Profile API (`/api/profile`) already exists and saves data
- No "compare with last time" feature exists yet
- This is what makes VitalTwin a **living twin** instead of a one-time calculator

### How It Works
```
User completes assessment → results saved with timestamp to profile DB
        ↓
Next time user opens app → previous report loaded from profile API
        ↓
Results page shows dual view:
  "January 2026: Heart 72, Liver 68, Brain 81"
  "April 2026:   Heart 74↑, Liver 71↑, Brain 78↓"
        ↓
Trend arrows: ↑ improving, ↓ declining, → stable
        ↓
Smart alerts: "Your brain score declined 3 points since January — 
               your stress level increased from Low to High. 
               Consider stress management."
        ↓
Annual "Health Report Card" PDF exportable
```

### Files to Create/Modify
- Profile DB (Render backend) — add `timestamp` field to saved results
- `client/app/results/page.js` — load previous result from profile API
- `client/components/results/` — new `TrendComparisonCard.jsx`
- `client/lib/generatePdf.js` — add trend charts to PDF export

---

## 🏥 Integration 6: ABDM (Ayushman Bharat Digital Mission) — India's Official Health Network

### Why
- Government of India's ABHA (Ayushman Bharat Health Account) links all hospital visits, lab reports, prescriptions
- If user has ABHA ID → can pull real creatinine, HbA1c, lipid panel from any ABDM-linked hospital
- Covers: Apollo, Fortis, government hospitals, diagnostic chains (Dr. Lal PathLabs, SRL, Metropolis)

### How It Works
```
User enters ABHA ID: "91-1234-5678-9012"
        ↓
Redirect to ABDM consent gateway → user approves sharing
        ↓
ABDM returns FHIR bundle: structured health records
        ↓
VitalTwin parses FHIR → extracts same fields as lab parser
        ↓
All organ scores update with real clinical data
```

### API Details
- **Sandbox:** `https://sandbox.abdm.gov.in/` — free registration
- **Protocol:** FHIR R4 compliant
- **Effort:** 1-2 days (OAuth + FHIR parsing)
- **Impact:** Highest possible — real hospital data, zero manual entry

### Files to Create/Modify
- `client/app/api/abdm/route.js` — OAuth + FHIR fetch
- `client/components/landing/ProfileForm.jsx` — ABHA ID field + "Connect" button

---

## 📐 Implementation Priority Matrix

| # | Feature | Effort | Impact | API Cost | Recommended Sprint |
|---|---|---|---|---|---|
| 1 | **Lab Report Text Parser** (paste text → Groq extract) | 4 hrs | ⭐⭐⭐⭐⭐ | Free (have key) | Sprint 1 |
| 2 | **PDF/Image Lab Upload** (PDF.js + Tesseract) | 6 hrs | ⭐⭐⭐⭐⭐ | Free | Sprint 1 |
| 3 | **OpenAQ Live AQI** → lungs model | 2 hrs | ⭐⭐⭐⭐ | Free, no key | Sprint 1 |
| 4 | **Geolocation → District Priors** | 2 hrs | ⭐⭐⭐⭐ | Free, no key | Sprint 1 |
| 5 | **Drug Interaction Checker** (NIH RxNav) | 4 hrs | ⭐⭐⭐⭐⭐ | Free, no key | Sprint 2 |
| 6 | **Prescription Parser** (image → Groq → medications) | 4 hrs | ⭐⭐⭐⭐ | Free (have key) | Sprint 2 |
| 7 | **Longitudinal Tracking** (trend comparison) | 6 hrs | ⭐⭐⭐⭐ | None | Sprint 2 |
| 8 | **Google Fit REST API** (live wearable data) | 8 hrs | ⭐⭐⭐ | Free (OAuth) | Sprint 3 |
| 9 | **ABDM Integration** (ABHA health records) | 2 days | ⭐⭐⭐⭐⭐ | Free sandbox | Sprint 3 |
| 10 | **Retinal AI** (DeepMind) | Not possible | — | Private API | Future |

---

## 🏗️ Full System Architecture After Integration

```
┌─────────────────────────────────────────────────────────┐
│                    DATA INPUTS                          │
│                                                         │
│  Manual Form  ←→  Lab Report Upload  ←→  Wearable File b│
│       ↓                  ↓                    ↓         │
│  GPS Location  ←→  ABDM Records  ←→  Google Fit REST    │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                  AI PROCESSING LAYER                    │
│                                                         │
│  Groq LLaMA-3    OpenFDA Drug   OpenAQ Live AQI         │
│  Lab Extractor   Interactions   PM2.5 Lookup            │
│       ↓               ↓              ↓                  │
│         Nominatim District Geocoding                    │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              VITALTWIN PREDICTION ENGINE                │
│                                                         │
│  Heart (PCE + INTERHEART)   Brain (CAIDE + INTERSTROKE) │
│  Liver (FIB-4 + ensemble)   Kidney (CKD-EPI + Apollo)   │
│  Lungs (GOLD + CPCB + NTEP) Bio Age (KDM + NHANES)      │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                 RESULTS + INSIGHTS                      │
│                                                         │
│  3D Organ Models   Drug Interactions   Trend History    │
│  Dynamic Recs      What-If Scenarios   PDF Report       │
│  AI Chat (Groq)    District Priors     Confidence Badges│
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Sprint 1 — Build Now (All Free, No New Sign-ups)

### Sprint 1 Scope (Est. 14 hours total)

#### Task 1.1: Lab Report Text Parser UI (4 hrs)
- Add "Paste Lab Report" text area on health questions page
- Add `/api/parse-lab` Next.js route using existing Groq key
- Groq structured extraction prompt for 12 lab values
- Auto-fill form fields + show confidence badges
- Files: `client/app/api/parse-lab/route.js` (new), `client/app/health-questions/page.js` (modify)

#### Task 1.2: PDF Lab Upload (4 hrs)
- Install `pdfjs-dist` for PDF text extraction
- Camera capture button for mobile (no app needed)
- Connect extracted text to Task 1.1 parser
- Files: `client/components/landing/LabReportUpload.jsx` (new)

#### Task 1.3: OpenAQ Live AQI (2 hrs)
- New `/api/aqi` route proxying OpenAQ
- City field in profile form triggers AQI fetch
- Send `air_quality_pm25` to backend
- Files: `client/app/api/aqi/route.js` (new), `client/components/landing/ProfileForm.jsx` (modify)

#### Task 1.4: Geolocation → District (2 hrs)
- "Use my location" button on profile form
- Nominatim reverse geocode → district name
- District sent to backend → NFHS-5 prior applied
- Files: `client/app/api/geocode/route.js` (new), `client/components/landing/ProfileForm.jsx` (modify)

---

## 📋 Confidence Score Impact Summary

After Sprint 1 implementation, expected confidence score improvements:

| Organ | Before (form only) | After (with lab upload) |
|---|---|---|
| Kidney | 55% (no creatinine) | 92% (CKD-EPI exact) |
| Liver | 72% (no AST/ALT direct) | 88% (FIB-4 exact) |
| Heart | 78% (no cholesterol direct) | 91% (PCE exact) |
| Brain | 74% (no cholesterol direct) | 85% (CAIDE exact) |
| Lungs | 80% (static AQI) | 87% (live PM2.5) |

---

## 🔐 Privacy & Security Notes

1. **Lab reports never stored** — extracted values stored, raw text/images discarded immediately
2. **Groq data:** API calls are stateless; Groq does not train on API calls (per their policy)
3. **GPS data:** Coordinates converted to district name in the API route; raw coordinates never stored
4. **ABDM:** All data sharing requires explicit user consent per ABDM protocol
5. **OpenFDA/NIH:** Drug names sent to public APIs — no PII transmitted

---

## 💬 Questions for Judges / Reviewers

When presenting these integrations:

> *"We identified that the single biggest gap between our model's estimated health scores and clinical reality is missing lab values — most users have a blood test report on their phone but can't manually find 'serum creatinine' in a dense lab report. Our lab report AI parser solves this with zero friction — upload a photo, AI extracts the values, kidney confidence goes from 55% to 92% in 3 seconds."*

> *"We use three completely free, no-sign-up APIs: OpenAQ for real-time air quality (lungs), NIH RxNav for drug interactions (medications), and OpenStreetMap Nominatim for district-level health priors (NFHS-5). None of these require API keys or partnerships — they're public health infrastructure."*

---

*VitalTwin — Inceptrix Team | April 2026*
*See also: MASTER_IMPROVEMENT_PLAN.md, TRUST_AUDIT.md, GAPS_AND_LIMITATIONS.md*
