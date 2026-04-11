# VitalTwin — Presentation & Demo Guide
*Last updated: April 2026 (post dynamic-recommendations fix)*

---

## 🎯 THE PITCH (30 seconds)

> *"VitalTwin is a digital health twin for Indian users — it predicts organ health risk across 5 organs simultaneously using validated clinical formulas from published medical research, calibrated for the Indian population. Unlike every other health app, it generates personalised recommendations that reference your actual lab values: not 'watch your blood pressure' but 'your BP is 162/98 — Stage 2 hypertension — every 10 mmHg reduction cuts your stroke risk by 27%'. And it runs completely offline."*

---

## 🏆 UNIQUE SELLING POINTS (What no other app does)

| Feature | VitalTwin | Healthify Me / 1mg / Others |
|---------|-----------|---------------------------|
| Validated clinical formulas (PCE, FIB-4, CKD-EPI) | ✅ Yes | ❌ Questionnaire-based |
| All 5 organs simultaneously | ✅ Yes | ❌ Single organ or general |
| India-calibrated (bidi, AQI, TB, cooking fuel) | ✅ Yes | ❌ Generic Western models |
| Real Indian patient data | ✅ Yes (INTERSTROKE India 3K+) | ❌ No |
| Personalised recommendations with actual numbers | ✅ Yes | ❌ Generic pamphlet text |
| Biological age calculation (KDM) | ✅ Yes | ❌ No |
| What-if simulator (RCT-backed effect sizes) | ✅ Yes | ❌ No |
| Confidence score per result | ✅ Yes | ❌ No |
| Works offline | ✅ Yes | ❌ Cloud-only |

---

## 🔬 HOW THE DYNAMICITY WORKS (For Technical Judges)

### The problem with generic health apps
Every health app gives pamphlet text: *"You should exercise more."*
This is ignored. It's not personalised and not actionable.

### What VitalTwin does instead
Every recommendation is generated at runtime from the user's actual values:

**Heart example (52yo, BP 162/98, bidi smoker 15 pack-years, HbA1c 8.2):**
```
1. "Quit smoking — you have 15 pack-years (bidi = 3× more tar than cigarettes).
    Each year of daily smoking raises your heart attack risk by ~3%. Quitting cuts
    CVD risk by 50% within 1 year (Hackshaw BMJ 2018). Your BP 162/98 will also
    drop 5-10 mmHg within 1 year of quitting."

2. "Your BP 162/98 mmHg is Stage 2 hypertension — this alone doubles your heart
    attack risk. Every 10 mmHg reduction cuts CVD risk by 20% (SPRINT 2015).
    Start antihypertensive therapy if not already on it."

3. "Total cholesterol 248 mg/dL (HDL 35 mg/dL — low — raises net risk) — high
    (≥240 = increased CVD risk). Target: <200 mg/dL. Replace saturated fats
    (ghee, butter, red meat) with mustard/olive oil."

4. "HbA1c 8.2% — diabetes raises heart attack risk 2.4× (INTERHEART 2004).
    For every 1% HbA1c reduction, CVD risk drops ~14% (UKPDS 35)."
```

**Brain example (same user, CAIDE 15/30, sleep 5h):**
```
1. "CAIDE score 15/30 — very high 20-year dementia risk. Consult a neurologist for
    cognitive assessment (MoCA or MMSE test). Brain MRI if memory complaints persist
    >3 months. Multidomain lifestyle intervention is the only proven approach
    (FINGER trial 2015)."

2. "BP 162/98 mmHg — Stage 2 hypertension is the #1 modifiable stroke risk factor
    in India (PAR 47.9%, INTERSTROKE Lancet 2016). Every 10 mmHg reduction cuts
    stroke risk by 27% and dementia risk by 20% (SPRINT-MIND 2019)."

3. "Sleep 5 hours/night — severely insufficient. Brain glymphatic clearance of
    amyloid-β requires 7-8h of deep sleep. Chronic <5h sleep triples dementia risk
    (Sabia Nature Commun 2021)."
```

**Liver example (same user, ALT 95, FIB-4 2.74, Albumin 3.2):**
```
1. "ALT 95 U/L — 2.4× the upper limit of normal (ULN=40). This indicates active
    liver cell damage. LFT panel + HBsAg/anti-HCV will pinpoint the cause."

2. "FIB-4 score 2.74 — indeterminate zone. Fibroscan recommended for definitive
    fibrosis staging. Avoid alcohol completely while result is indeterminate."

3. "Albumin 3.2 g/dL — low (normal >3.5). Low albumin means the liver's protein
    manufacturing is impaired — urgent hepatology referral warranted."
```

### Technical implementation
```python
# Before (broken — always defaulted):
recommendations = self._get_recommendations(risk_level, health)  # health had no _age/_fib4

# After (fixed — actual values injected):
health["_age"]      = age                              # heart/brain
health["_activity"] = profile.get("ActivityLevel")    # heart/brain
health["_fib4"]     = fib4_score                       # liver
health["_apri"]     = apri_val                         # liver
recommendations = self._get_recommendations(risk_level, health)
```

Three Python lines. But the result is the difference between a pamphlet and a clinical letter.

---

## 📊 THE NUMBERS (For Data/ML Judges)

| Model | Primary Method | Dataset Size | AUC / Stat | India-specific? |
|-------|---------------|-------------|------------|-----------------|
| Heart | Framingham PCE | 24,626 pts | C-stat 0.72 | SA ×1.26 correction |
| Heart INTERHEART | India ORs | 15,152 pts | Published ORs | ✅ India subset |
| Brain CAIDE | Finnish cohort | 1,449 pts | 20-yr validation | ×0.74 India correction |
| Brain INTERSTROKE | India hospitals | 3,000+ pts | PAR 91.5% | ✅ India-specific |
| Liver FIB-4 | Multi-centre | Published | NPV 90% | Universal |
| Liver ILPD ML | Andhra Pradesh | 583 pts | — | ✅ India patients |
| Liver LPD ML | India dataset | 30,691 rows | AUC 0.998 | ✅ India |
| Kidney CKD-EPI | Multi-centre | Published | Within 10% | Universal |
| Kidney Apollo ML | Tamil Nadu | 400 pts | AUC 0.991 | ✅ India hospital |
| Lungs GOLD | SPIROMICS | Published | FEV1/FVC | Universal |
| Stroke ML | Multi-ethnic | 5,109 rows | AUC 0.828 | ×1.28 India calibration |
| Alzheimer's ML | — | 2,149 rows | AUC 0.949 | — |
| Bio Age KDM | NHANES | 9,473 rows | ±3-5yr | +1.8yr SA offset |

---

## 🇮🇳 INDIA-SPECIFIC FEATURES (For Healthcare Track Judges)

### Why standard health apps fail Indians:
1. **Bidi vs cigarette** — Standard models assume cigarettes. Bidi has 3× more tar and carbon monoxide. We apply a ×1.5 COPD risk correction (Gupta PC, Tobacco Control 1999).
2. **AQI calibration** — Delhi PM2.5 = 99 µg/m³ (CPCB 2023). WHO limit = 10 µg/m³. A model that doesn't use actual city AQI is missing the biggest lung risk factor for most Indians.
3. **Lean NAFLD** — 25% of Indian NAFLD patients have BMI < 23 (Duseja 2015). Standard BMI-based screening misses them. We detect this pattern and flag it.
4. **TB comorbidity** — TB causes 40% post-infection obstructive lung disease (Allwood 2013). We use NTEP state-level TB rates (37 states) to adjust lung risk.
5. **District priors** — NFHS-5 data (706 Indian districts) adjusts the baseline cardiovascular risk by where you actually live.
6. **South Asian CVD** — Indians have 2-4× higher heart attack risk at same cholesterol levels as Europeans. We apply the published South Asian correction (Brindle 2005, Heart journal).
7. **Cooking fuel** — Biomass cooking (chulha) raises indoor PM2.5 to 400+ µg/m³. Affects 50% of rural Indian women. We apply the Balakrishnan 2019 Lancet risk multiplier.

---

## ❓ JUDGE Q&A (Prepared Answers)

**Q: "Is this validated?"**
> "All primary clinical formulas — Framingham PCE, CKD-EPI, FIB-4, CAIDE, GOLD — are validated in peer-reviewed journals (Lancet, NEJM, Circulation, Hepatology) with 400 to 25,000+ patient studies. We use the same formulas a cardiologist or hepatologist would use. We add India-specific corrections where published evidence exists."

**Q: "How is this different from a health questionnaire app?"**
> "Questionnaire apps score you on symptoms. We calculate your 10-year disease risk using the same formulas that clinical guidelines (ACC/AHA, KDIGO, GOLD, EASL) recommend. That's the same methodology used in NHS cardiovascular screening tools and WHO HEARTS programme. The difference is we also calibrate for India."

**Q: "How do you handle missing data?"**
> "Three ways: (1) Confidence score — we tell you exactly how reliable the result is (0–100%). (2) Input completeness score — we flag what's missing and why it matters. (3) Graceful degradation — we fall back to less accurate but still useful methods when labs are missing, rather than refusing to give a result."

**Q: "What about privacy? You're handling health data."**
> "The entire inference stack runs locally — no health data leaves the device. The Python model server runs on the user's machine. The Next.js frontend calls localhost. No cloud database stores health inputs. This is by design — Indian users are understandably cautious about health data privacy."

**Q: "The kidney confidence is only 0.725 — isn't that low?"**
> "Yes — and we display that number to the user. This is honesty as a feature. The kidney model needs serum creatinine for gold-standard CKD-EPI calculation. Without it, we use our Indian ML backup (Apollo Hospital Tamil Nadu data). We tell the user: 'Getting a serum creatinine test (₹100-200 at a government lab) will improve your kidney score accuracy from 72% to 92%.' Transparency beats false confidence."

**Q: "Why not just use a large language model for recommendations?"**
> "LLMs hallucinate. An LLM might confidently say 'your BP is fine' when it's 162/98. Our recommendations are generated by deterministic code that reads the actual numbers and applies published clinical thresholds. Every sentence has a specific evidence citation (paper, year, journal). That's reproducible and auditable — LLM output is neither."

**Q: "What would you improve with more time?"**
> "Priority 1: Creatinine prompt in the UI (1-day fix). Priority 2: Genetic risk layer — ApoE4 for dementia (needs DNA testing partnership). Priority 3: Wearable integration — real-time SpO2 and HR from Apple Health. Priority 4: LASI India Wave 1 biological age recalibration when data is released. Priority 5: Blood test PDF parser so users can just upload their lab report."

---

## 🎬 DEMO SCRIPT (5 minutes)

### Step 1 — The Problem (30 sec)
*"Indians have 2-4× higher heart disease risk than Europeans at the same age. India has the world's highest TB burden. Delhi's AQI is 10× the WHO limit. Yet every health app available today either ignores these factors or gives generic 'eat healthy, exercise more' advice. VitalTwin is different."*

### Step 2 — Enter Data (1 min)
Enter a high-risk profile: 52yo male, Delhi, bidi smoker, BP 162/98, HbA1c 8.2, sedentary, 5h sleep.

### Step 3 — Show Results (2 min)
- **Heart score** — point to "BP 162/98 mmHg — Stage 2 hypertension" in recommendations
- **Brain score** — point to "CAIDE score 15/30 — very high dementia risk"
- **Liver score** — point to "FIB-4 2.74 — indeterminate zone, Fibroscan recommended"
- **Biological age** — "Body aging 19 years faster than chronological age"
- **India-specific** — point to bidi note, Delhi AQI 99 in lungs model

### Step 4 — What-If (1 min)
*"Now watch what happens if we simulate quitting smoking and controlling BP."*
Show risk scores improve with citations: "50% CVD risk reduction within 1 year (Hackshaw BMJ 2018)"

### Step 5 — The Ask (30 sec)
*"We need: (1) access to larger Indian patient datasets, (2) partnership with Apollo/Fortis for EMR integration, and (3) ICMR or AIIMS validation study. This model is ready — it just needs the institutional data to become a class I medical device."*

---

## 🔑 KEY CITATIONS TO REMEMBER

| Claim | Citation |
|-------|---------|
| South Asian 2-4× CVD risk | Brindle P, Heart 2005 |
| INTERHEART India | Yusuf S, Lancet 2004 |
| INTERSTROKE India | O'Donnell MJ, Lancet 2016 |
| FIB-4 NPV 90% | Sterling RK, Hepatology 2006 |
| CKD-EPI gold standard | Inker LA, NEJM 2021 |
| CAIDE dementia | Kivipelto M, Lancet Neurol 2006 |
| Bidi tar correction | Gupta PC, Tobacco Control 1999 |
| Lean NAFLD India 25% | Duseja A, J Clin Exp Hepatol 2015 |
| Delhi PM2.5=99 | CPCB Annual Report 2023 |
| SPRINT trial (BP→CVD) | Wright JT, NEJM 2015 |
| Quit smoking 50% CVD | Hackshaw A, BMJ 2018 |

---

*VitalTwin — Inceptrix Team | April 2026*
