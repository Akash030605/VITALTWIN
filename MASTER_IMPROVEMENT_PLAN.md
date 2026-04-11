# VitalTwin — Master Improvement Plan
*Last updated: April 2026 (post dynamic-recommendations fix)*

---

## 🏁 CURRENT STATE SUMMARY (April 2026)

| Component | Status | Notes |
|-----------|--------|-------|
| Heart model (PCE + INTERHEART India) | ✅ Complete | Dynamic recs verified |
| Brain model (CAIDE + INTERSTROKE India) | ✅ Complete | Dynamic recs verified |
| Liver model (FIB-4 + 4-model ensemble) | ✅ Complete | Dynamic recs verified |
| Kidney model (CKD-EPI + Apollo ML) | ✅ Complete | Confidence gap without creatinine |
| Lungs model (GOLD + India AQI + TB) | ✅ Complete | Dynamic recs verified |
| Biological Age (KDM + NHANES) | ✅ Complete | ±3-5yr uncertainty for Indians |
| Dynamic personalised recommendations | ✅ Fixed April 2026 | All 5 organs fully dynamic |
| Input completeness scoring | ✅ Complete | Flags CRIT MISSING fields |
| What-if simulator | ✅ Complete | RCT-backed effect sizes |
| Smoke test | ✅ Passing | All phases complete |
| Frontend (Next.js) | ✅ Running | Client app active |

---

## ✅ COMPLETED IMPROVEMENTS (April 2026 Session)

### Phase 1: Model Accuracy Fixes
| # | Fix | Impact |
|---|-----|--------|
| 1 | Heart score = 0 for worst-case inputs | Fixed — capped `final_risk` at 0.80 |
| 2 | Lungs score too high for elderly smokers | Fixed — age-scaled floor |
| 3 | Kidney showing 100 despite diabetes+HTN | Fixed — ML skips without kidney labs |
| 4 | INTERHEART India pkl reading wrong key | Fixed — `interheart_south_asia_ors` |
| 5 | Turkish liver model at 60% weight | Fixed — reduced to 30%, added NHANES 15% |

### Phase 2: Dynamic Recommendations (Major Feature)
| # | Fix | Before | After |
|---|-----|--------|-------|
| 1 | Heart `_age`/`_activity` injection | Defaults (age=45, "Moderate") | Real values from profile |
| 2 | Brain `_activity` injection | Sedentary branch never fired | Real ActivityLevel |
| 3 | Liver `_fib4`/`_apri` injection | Dead code | FIB-4 score in recommendations |
| 4 | Heart recommendations | "Maintain a healthy BP" | "BP 162/98 mmHg — Stage 2 hypertension..." |
| 5 | Brain recommendations | "Consider cognitive exercises" | "CAIDE score 15/30 — very high dementia risk..." |
| 6 | Liver recommendations | "Reduce alcohol intake" | "FIB-4 2.74 — indeterminate zone, Fibroscan recommended" |
| 7 | Lungs recommendations | "Quit smoking" | "18.4 pack-years (bidi = 3× more tar)..." |
| 8 | Kidney recommendations | "Check eGFR" | "eGFR 42 mL/min — moderate CKD (G3b)..." |
| 9 | India-specific notes | Missing | Bidi tar note, NTEP state TB, UJJWALA scheme, NPHCE HCV |

### Phase 3: Indian Data Integration
| # | Dataset | Rows | Organ | Weight |
|---|---------|------|-------|--------|
| 1 | INTERHEART India (Yusuf 2004, Lancet) | 15,152 | Heart | 20% blend |
| 2 | INTERSTROKE India (O'Donnell 2016, Lancet) | 3,000+ | Brain | 32% weight |
| 3 | ILPD (Ramana 2012, Andhra Pradesh) | 583 | Liver | 20% weight |
| 4 | LPD India | 30,691 | Liver | 35% weight |
| 5 | Apollo CKD Tamil Nadu | 400 | Kidney | ML fallback |
| 6 | CPCB AQI 2023 (60+ cities) | Real PM2.5 | Lungs | Primary |
| 7 | NTEP State TB 2021-22 (37 states) | State rates | Lungs | State multiplier |
| 8 | NFHS-5 District Priors (706 districts) | — | Heart | Bayesian prior |

---

## 🔴 REMAINING OPEN ITEMS (Priority Order)

### Priority 1 — Kidney Creatinine Prompt (HIGH IMPACT, LOW EFFORT)
**Problem:** Without serum creatinine, kidney confidence = 0.55 (rule-based guess).
**Solution:** Add a UI prompt: *"Add your serum creatinine from your last blood test — test costs ₹100–200 at a government lab and will increase your kidney score accuracy from 55% to 92%."*
**Effort:** Frontend UI change only — backend already handles creatinine correctly.
**Impact:** Lifts kidney confidence from C → A for most users with lab reports.

### Priority 2 — sklearn Feature Name Warning (LOW EFFORT, COSMETIC)
**Problem:** `SimpleImputer` fitted with named features warns when receiving unnamed arrays.
**Solution:** Pass feature names consistently or suppress with `warnings.filterwarnings`.
**Effort:** 2-line fix in liver/kidney model's `_extract_features()`.
**Impact:** Cleaner logs — no effect on predictions.

### Priority 3 — Lung Cancer ML Dataset Size (MEDIUM EFFORT)
**Problem:** 309 patients — too small for reliable ML. AUC 0.857 on small data is fragile.
**Solution:** Find larger lung cancer dataset; currently used at 15% weight to limit impact.
**Effort:** Data sourcing + retraining.

### Priority 4 — CAIDE India Recalibration (LOW EFFORT NOW, FUTURE DATA)
**Problem:** CAIDE validated on Finnish population.
**Solution:** When LASI Wave 1 cognitive data becomes publicly available, recalibrate the CAIDE → India risk table.
**Effort:** Data availability gating — algorithm is ready.

---

## 🔮 V2 ROADMAP (Post-Hackathon)

### V2.1 — Data Completeness UX
- [ ] Creatinine prompt on kidney results page
- [ ] FEV1% prompt on lungs results page ("Have a spirometry result? Enter it for better accuracy")
- [ ] Blood test upload parser (extract values from PDF lab report)

### V2.2 — Wearable Integration
- [ ] Apple HealthKit / Google Fit API
- [ ] Real-time resting heart rate → biological age input
- [ ] SpO2 → lungs oxygen saturation signal
- [ ] Step count → activity level override

### V2.3 — Genetic Risk Layer
- [ ] ApoE4 genotype → CAIDE +4 points (dementia)
- [ ] APOL1 G1/G2 variants → kidney risk ×7 (South Indian subpopulations)
- [ ] MTHFR C677T → homocysteine → cardiovascular risk
- [ ] Requires DNA testing lab partnership

### V2.4 — India Population Recalibration
- [ ] LASI Wave 1 biomarker data → KDM biological age recalibration
- [ ] India-specific Framingham equivalent (when available — being collected by IIARI)
- [ ] Regional diet patterns (South Indian rice diet vs North Indian wheat diet)

### V2.5 — Advanced Features
- [ ] Retinal scan AI for CVD risk (proven by Google DeepMind, available via API)
- [ ] AIIMS / Fortis / Apollo EMR integration
- [ ] Longitudinal tracking (annual comparison, trend analysis)
- [ ] Family risk tree (first-degree relative history structured input)

---

## 📐 ARCHITECTURE DECISIONS (Rationale)

### Why ensemble instead of single model?
- No single Indian dataset has enough patients for all 5 organs
- Ensemble averaging reduces individual dataset bias
- Each dataset brings different clinical signal (formula vs ML vs rules)
- Confidence score reflects ensemble quality

### Why clinical formulas first, ML second?
- Clinical formulas (PCE, FIB-4, CKD-EPI) are validated in peer-reviewed journals
- ML models trained on small Indian datasets (400–600 patients) are secondary signals
- Formula-first = interpretable, citable, defensible to doctors and judges

### Why dynamic recommendations matter?
- A recommendation that says "BP 162/98 — Stage 2 hypertension" is actionable
- A recommendation that says "Monitor your blood pressure" is ignored
- Personalised text = higher user engagement + clinical credibility
- Clinical letters from doctors always reference actual numbers — so should ours

### Why India-specific corrections instead of global models?
- South Asians have 2–4× higher CVD risk at same Framingham score (well-documented)
- Indian AQI (PM2.5 Delhi = 99 µg/m³) is 10× WHO limit — must be modelled
- Bidi smoke has 3× more tar than cigarettes — a global model would miss this
- TB comorbidity with COPD is India-specific (NTEP data)

---

*VitalTwin — Inceptrix Team | April 2026*
