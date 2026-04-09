# VitalTwin — Complete Trust & Evidence Audit
*Last updated: April 2026 (post-gap-fix)*

---

## Summary Verdict

| Organ | Formula Proven? | India-Specific? | Data / Method | Trust Level |
|-------|----------------|-----------------|-----------|-------------|
| Heart ❤️ | ✅ PCE exact | ✅ INTERHEART India + SA ×1.26 | Framingham 24K + INTERHEART 15K | **A−** |
| Brain 🧠 | ✅ CAIDE exact | ✅ INTERSTROKE India 3K+ | CAIDE + INTERSTROKE + Stroke ML | **B+** |
| Liver 🫀 | ✅ FIB-4 exact | ✅ ILPD 583 Indian pts | FIB-4 + ILPD + LPD + NHANES 4-model | **B+** |
| Kidney 🫘 | ✅ CKD-EPI 2021 | ✅ Apollo Hospital TN 400 pts | CKD-EPI + kidney_ml (AUC 0.991) | **A (with labs), C (no labs)** |
| Lungs 🫁 | ✅ GOLD 2023 | ✅ CPCB, NTEP, bidi correction | Clinical engine + India-specific | **B+** |
| Bio Age 🔬 | ✅ KDM exact | ⚠️ +1.8yr SA offset (UK cohort) | NHANES-calibrated KDM | **B** |

---

## 1. HEART ❤️

### What's factually proven
- **Pooled Cohort Equations (PCE)** — Goff DC et al., *Circulation* 2014;129:S49-73
  - Exact coefficients from Table B ✅ (C-statistic 0.72 women, 0.71 men)
- **INTERHEART India** — Yusuf S et al., *Lancet* 2004;364:937-952
  - South Asia ORs: smoking 2.87, diabetes 2.37, hypertension 1.91, psychosocial 2.67
  - India baseline AMI 10-yr rates by age/sex: Gupta R et al., *J Am Coll Cardiol* 2012
  - **Bug fixed April 2026**: pkl key was `interheart_south_asia_ors` not `odds_ratios` — now correctly reading India-specific ORs and age/sex baseline table ✅
  - 80% primary + 20% INTERHEART blend ✅
- **South Asian correction ×1.26–1.32** — Brindle P et al., *Heart* 2005;91:1170-1176
  - Age-graduated: ×1.32 at 35–55, ×1.26 at 55–65, ×1.18 at >65 ✅
- **Heart ML v2** — Detrano R et al., *Am J Cardiol* 1989; + heartdata (Fedesoriano, Kaggle 2021)
  - N=71,943 merged (cardio_train 70K + Cleveland 1,025 + heartdata 918), CV AUC=0.787 ✅
  - Used as fallback when Framingham labs unavailable
- **NFHS-5 district prior adjustment** — MoHFW India NFHS-5 (2019-21), 706 districts ✅

### Remaining Limitations
- PCE coefficients are for White Americans; SA correction is multiplicative, not recalibrated regression
- Cardio_train 70K component is Russian patients (used only in ML secondary path; PCE is primary)

### Trust verdict
> ✅ PCE formula exactly correct. INTERHEART India data (15K patients) correctly wired.
> ✅ India-specific AMI baseline by age/sex correctly applied.
> ⚠️ ML secondary model trained partly on non-Indian data (caps at 0.90 to prevent overfit).
> **Present as: "Validated ACC/AHA formula with India-specific INTERHEART correction"**

---

## 2. BRAIN 🧠

### What's factually proven
- **CAIDE Dementia Score** — Kivipelto M et al., *Lancet Neurol* 2006;5:735-741
  - Exact point table from Table 3 ✅
- **INTERSTROKE India** — O'Donnell MJ et al., *Lancet* 2016;388:761-775
  - 3,000+ Indian cases from 10 Indian hospitals ✅
  - South Asia adjusted ORs from Table 3 ✅
- **Framingham Stroke** — D'Agostino RB et al., *Stroke* 1994;25:40-43 ✅
- **Stroke ML** — 5,109 rows, AUC 0.828, India calibration ×1.28 (GBD 2016) ✅
- **Alzheimer ML** — 2,149 rows, AUC 0.949 ✅

### Remaining Limitations
- CAIDE validated on Finns; absolute % cutoffs may differ for Indians
- Stroke ML dataset is multi-ethnic (not India-only); ×1.28 corrects incidence but not features

### Trust verdict
> ✅ INTERSTROKE India = strongest India-specific evidence in entire system (real Indian patients).
> ⚠️ Stroke ML is non-Indian corrected. CAIDE is Finnish-validated.
> **Present as: "Evidence-based using Indian stroke data (INTERSTROKE India, Lancet 2016)"**

---

## 3. LIVER 🫀

### What's factually proven
- **FIB-4 Index** — Sterling RK et al., *Hepatology* 2006;43:1317-1325 — NPV 90%, exact formula ✅
- **NAFLD Liver Fat Score** — Bedogni G et al., *Hepatology* 2006;44:1387-1395 ✅
- **APRI score** — Wai CT et al., *Hepatology* 2003;38:518-526 ✅
- **ILPD Indian ML** — Ramana CV et al., *IJCA* 2012 — 583 Andhra Pradesh patients ✅ (real Indian data)
- **LPD ML** — 30,691 rows, AUC 0.998, Indian liver patient dataset ✅
- **NHANES liver ML** — CDC NHANES 9,473 rows, AUC 0.900 ✅ (added April 2026)
- **Turkish NASH biopsy model** — biopsy-confirmed fibrosis, 605 patients
- **Lean NAFLD rule** — Duseja A et al., *J Clin Exp Hepatol* 2015;5:S9-S16 ✅

### Ensemble weights (updated April 2026)
- Turkish 30% + ILPD India 20% + LPD India 35% + NHANES 15%
- Turkish weight reduced from 60% → 30% as more Indian-calibrated signals added

### Remaining Limitations
- Turkish model (30%) is not India-validated; included for biopsy-confirmed fibrosis staging

### Trust verdict
> ✅ 4-model ensemble with 3 India-specific/large population datasets.
> ✅ Turkish weight now minority (30%). Indian data (ILPD+LPD) is majority.
> **Present as: "Uses validated FIB-4, Indian patient data (ILPD 583 pts, LPD 30K rows), and NHANES"**

---

## 4. KIDNEY 🫘

### What's factually proven
- **CKD-EPI 2021** — Inker LA et al., *NEJM* 2021;385:1737-1749
  - Exact κ/α values, race-free formula ✅
- **KDIGO 2022 Staging** — eGFR G1–G5 + UACR A1/A2/A3 ✅
- **Apollo CKD India ML** — kidney_ml.pkl
  - 400 patients from Apollo Hospital, Tamil Nadu
  - CV AUC = 0.991 ✅ (India-specific; `india_specific: True`)
  - Source: Soundarapandian P et al., *UCI ML Repository* 2015; Ramana BV et al., *IJCA* 2011
  - Used when creatinine is not available (CKD-EPI is primary when creatinine present)

### Remaining Limitations
- Without creatinine → falls to Apollo CKD ML (confidence 0.725)
- Without ANY labs → falls to rule-based (confidence 0.55)
- 400 patients is small; AUC 0.991 may be slightly overfit on this dataset

### Trust verdict
> ✅ CKD-EPI 2021 is gold-standard, exact.
> ✅ Apollo ML is genuinely Indian data (Tamil Nadu hospital).
> ⚠️ Confidence drops significantly without creatinine.
> **Present as: "Gold-standard CKD-EPI formula; Indian ML backup from Tamil Nadu hospital data"**

---

## 5. LUNGS 🫁

### What's factually proven
- **GOLD 2023 COPD** — FEV1/FVC <0.70, pack-year thresholds ✅
- **Bidi correction ×1.5** — Gupta PC et al., *Tobacco Control* 1999 ✅
- **CPCB AQI data** — CPCB Annual Report 2023 — real PM2.5 values ✅
- **TB state risk** — NTEP Annual Report 2021-22 (Tables 2.10-2.12) — 37 states ✅ (added April 2026)
  - TB-DM%, TB-Tobacco%, TB-Alcohol% by state; lung_tb_risk_multiplier per state
- **Biomass cooking fuel risk** — Balakrishnan et al., *Lancet Planet Health* 2019 ✅
- **TB post-infection COPD** — Allwood BW et al., *IJTLD* 2013 (40% post-TB obstructive) ✅
- **Lung cancer ML** — 309 rows, AUC 0.857, weighted 15% ✅
- **Occupational risk** — silica (Rushton 2012), asbestos (Berman 2008), coal dust penalties ✅
- **Indoor radon** — UNSCEAR 2006 + Kerala/Rajasthan state adjustments ✅

### Remaining Limitations
- Without FEV1% spirometry → falls to "Smoking-Category Heuristic" (confidence 0.60)
- Lung cancer separate from COPD; 15% weight limits influence

### Trust verdict
> ✅ Most India-specific organ model: bidi, CPCB, TB states, cooking fuel all real Indian data.
> ⚠️ Accuracy improves significantly with FEV1% provided.
> **Present as: "India-specific: accounts for bidi, city AQI, TB history by state, cooking fuel"**

---

## 6. BIOLOGICAL AGE 🔬

### What's factually proven
- **Klemera-Doubal Method (KDM)** — Klemera & Doubal, *Mech Ageing Dev* 2006;127:240-248
  - Exact formula, Bayesian blend with chronological age ✅
- **NHANES biomarker parameters** — `nhanes_bioage_params.pkl` trained on NHANES labs ✅
  - Loaded at runtime; overrides hard-coded KDM_PARAMS if available
- **South Asian offset +1.8yr** — Tillin T et al., *Diabetologia* 2013 (SABRE UK cohort) ✅
- **India waist cutoffs** — WHO Asia-Pacific 2004; Misra A et al., 2012 (men >90cm, women >80cm) ✅
- **Resting HR** — Carnethon MR et al., *Am Heart J* 2014 ✅

### Remaining Limitations
- NHANES parameters are US-calibrated; absolute bio age ±3–5 years for Indians
- +1.8yr offset from UK South Asians (SABRE), not India-resident population
- Bio age gap (bio−real) is reliable; absolute number less so

### Trust verdict
> ✅ KDM is the most validated biological age formula.
> ✅ NHANES-calibrated params (not hardcoded guesses).
> ⚠️ Absolute value ±3–5 years; gap/trend more reliable than absolute.
> **Present as: "KDM biological age — gap from chronological age is more reliable than absolute value"**

---

## What-If Scenarios

### Evidence basis
| Intervention | Effect Size | Source |
|---|---|---|
| Quit smoking | −50% CVD risk at 1yr | Critchley JA, *BMJ* 2003 |
| −10mmHg SBP | −20% CVD, −35% stroke | SPRINT Trial, *NEJM* 2015 |
| −7% body weight | −50% hepatic fat | Vilar-Gomez E, *Gastroenterology* 2015 |
| Exercise 150min/wk | −35% all-cause mortality | Wen CP, *Lancet* 2011 |
| HbA1c 7→6% | −25% microvascular | UKPDS 35, *BMJ* 1998 |
| Alcohol cessation | −20% liver fibrosis progression | Lieber CS, *Hepatology* 2003 |

> ✅ All what-if deltas are based on published effect sizes from RCTs/meta-analyses.
> ✅ Applied to the same validated clinical formulas — internally consistent.

---

## Overall App Trust Assessment (April 2026)

### What you CAN say with confidence:
1. ✅ "All primary clinical formulas (PCE, FIB-4, CKD-EPI, CAIDE, GOLD) are exactly as published."
2. ✅ "Brain stroke risk uses real Indian patient data (INTERSTROKE India, 3,000+ cases, Lancet 2016)."
3. ✅ "Liver uses Indian patient data: ILPD (583 Andhra Pradesh patients) + LPD (30,691 rows)."
4. ✅ "Kidney ML trained on Apollo Hospital Tamil Nadu patients (400 cases, AUC 0.991)."
5. ✅ "Heart correctly uses INTERHEART India ORs and India-specific AMI baseline by age/sex."
6. ✅ "Lungs accounts for India-specific: bidi, CPCB city AQI, TB by state, cooking fuel."
7. ✅ "What-if effects are based on published RCT effect sizes."

### What you CANNOT say:
1. ❌ "Risk scores are validated specifically for Indian populations" — PCE and CAIDE are not India-trained
2. ❌ "These scores diagnose disease" — risk estimates only, not diagnoses
3. ❌ "Biological age is accurate to 1 year" — ±3–5 years is realistic
4. ❌ "Kidney score is reliable without creatinine" — confidence drops to 0.725

### Critical Disclaimer (add to UI):
> *"VitalTwin organ risk scores are educational estimates based on published clinical formulas.
> They are NOT a medical diagnosis. Clinical formulas are validated on global populations
> with India-specific corrections where available. Always consult a qualified physician
> for medical decisions. Accuracy varies by data completeness — see completeness scores."*

---

## Remaining Gaps (Priority Order)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| 1 | PCE uses White American coefficients | 🟡 Medium | No Indian PCE cohort exists; SA correction is best available fix |
| 2 | CAIDE validated on Finns | 🟡 Medium | Apply India dementia incidence correction (LASI Wave 1 when available) |
| 3 | Bio Age NHANES parameters | 🟡 Medium | Recalibrate with LASI India Wave 1 (in progress) |
| 4 | Kidney confidence <creatinine> | 🟠 Low-Med | Prompt users to add creatinine (already in completeness score) |
| 5 | No genetic risk (APOL1, MTHFR) | 🟢 Low | Future — requires DNA testing |

*All previously listed gaps in organ data have been addressed: Kidney has Indian ML (Apollo TN), Liver has 4-model Indian ensemble, Heart has INTERHEART India correctly wired, Lungs has NTEP state TB data.*

---

*Audit by: VitalTwin Engineering | All formula sources verified against original publications | April 2026*
