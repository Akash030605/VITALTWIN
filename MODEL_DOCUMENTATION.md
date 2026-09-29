# VitalTwin — Complete Model Documentation
> Last updated: April 2026 | Version 3.0.0
> Covers: All 5 organ models, formulas, datasets, ML models, India-specific adjustments, and clinical references.

---

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Heart Model](#2-heart-model)
3. [Liver Model](#3-liver-model)
4. [Kidney Model](#4-kidney-model)
5. [Brain Model](#5-brain-model)
6. [Lungs Model](#6-lungs-model)
7. [Biological Age Engine](#7-biological-age-engine)
8. [Stress Heatmap](#8-stress-heatmap)
9. [Medication Modeler](#9-medication-modeler)
10. [India-Specific Adjustments](#10-india-specific-adjustments)
11. [All Datasets Used](#11-all-datasets-used)
12. [All Formulas Used](#12-all-formulas-used)
13. [Confidence & Trust Framework](#13-confidence--trust-framework)
14. [Known Gaps & Limitations](#14-known-gaps--limitations)

---

## 1. System Architecture

```
User Input (Frontend)
       │
       ▼
POST /api/report (Next.js route)   ← maps snake_case → PascalCase lab fields
       │
       ▼
POST /predict (FastAPI backend)
       │
       ▼
VitalTwinSimulator.run_simulation()
       │
       ├─ Layer 1: Input Validation & Sanity Checks
       ├─ Layer 2: Per-Organ Risk Calculation (5 models in parallel)
       │     ├─ HeartModel.calculate_risk()
       │     ├─ LiverModel.calculate_risk()
       │     ├─ KidneyModel.calculate_risk()
       │     ├─ BrainModel.calculate_risk()
       │     └─ LungsModel.calculate_risk()
       ├─ Layer 3: Medication Effect Modeling
       ├─ Layer 4: Clinical Consistency Cross-checks
       ├─ Layer 5: Biological Age Calculation
       └─ Layer 6: Stress Heatmap Generation
```

**Stack:**
- Backend: Python 3.12, FastAPI, Pydantic v2, scikit-learn 1.8, uvicorn
- Frontend: Next.js 16.1.6 (Turbopack), React 19, Zustand, Tailwind CSS v4
- ML: XGBoost, GradientBoostingClassifier, RandomForestClassifier, LogisticRegression
- Tunnel: ngrok (free tier, India region)

---

## 2. Heart Model

### Primary Method: Framingham Pooled Cohort Equations (PCE)
**Formula:**
```
10-year CVD risk = 1 - S₀^exp(Σβᵢ·Xᵢ - μ)
```
- **Source:** Goff DC Jr et al., *JACC* 2014;63(25):2935-2959
- **Validation:** 24,626 patients from 4 US cohorts (ARIC, CHS, CARDIA, Framingham)
- **Variables:** Age, Total Cholesterol, HDL Cholesterol, Systolic BP, BP treatment status, Diabetes, Smoking, Race
- **Output:** 10-year ASCVD risk (0–1)

**Coefficients used (Women, non-Black):**
```python
ln_age × 17.1141 + ln_total_chol × 0.9396 + ln_hdl × (-18.9196) +
ln_age × ln_hdl × 4.4748 + ln_treated_sbp × 29.7995 +
ln_age × ln_treated_sbp × (-6.4321) + current_smoker × 13.5766 +
ln_age × current_smoker × (-3.7052) + diabetes × 0.8738 - 12.819
```
**Coefficients used (Men, non-Black):**
```python
ln_age × 12.344 + ln_total_chol × 11.853 + ln_age × ln_total_chol × (-2.664) +
ln_hdl × (-7.990) + ln_age × ln_hdl × 1.769 + ln_treated_sbp × 1.797 +
ln_untreated_sbp × 1.764 + current_smoker × 7.837 +
ln_age × current_smoker × (-1.795) + diabetes × 0.658 - 61.18
```

### South Asian Correction Factor
- **Multiplier:** ×1.26 on PCE output
- **Source:** Enas EA et al., *Indian Heart Journal* 2011;63(5):461-464
  - South Asians have 1.4–2× higher CVD mortality vs Western populations at same Framingham score
  - INTERHEART study: South Asians have 60% higher odds of MI vs Europeans
- **Why:** PCE was derived from White/Black US cohorts; South Asians have greater insulin resistance and higher Lp(a) which PCE doesn't capture

### Secondary ML Model: Cleveland Heart Disease UCI
- **Dataset:** 303 patients, Cleveland Clinic (Detrano R et al., 1988)
- **Features:** age, sex, chest_pain_type (4 types), resting_bp, cholesterol, fasting_sugar, ecg, max_hr, exang, oldpeak, slope, num_vessels, thal
- **Algorithm:** GradientBoostingClassifier (AUC ~0.90)
- **Usage:** Secondary signal blended with PCE when detailed clinical data available

### Stroke Sub-model (Framingham Stroke Risk Profile)
- **Source:** Wolf PA et al., *Stroke* 1991;22:312-318
- **Variables:** Age, Systolic BP, antihypertensive therapy, diabetes, current smoking, prior CVD, atrial fibrillation, LVH on ECG
- **Separate ML:** Trained on Kaggle Stroke dataset (5,110 patients, AUC 0.828)

### Heart-Specific Lab Markers Used
| Field | Normal Range | Clinical Use |
|-------|-------------|--------------|
| TotalCholesterol | <200 mg/dL | PCE input |
| LDLCholesterol | <100 mg/dL | Statin threshold |
| HDLCholesterol | >60 mg/dL | PCE input (protective) |
| Triglycerides | <150 mg/dL | Metabolic syndrome |
| FastingGlucose | <100 mg/dL | Diabetes detection |
| HbA1c | <5.7% | Diabetes control |
| SystolicBP | <120 mmHg | PCE input |
| DiastolicBP | <80 mmHg | HTN staging |

---

## 3. Liver Model

### Primary Method A: FIB-4 Index (with lab values)
**Formula:**
```
FIB-4 = (Age × AST) / (Platelets × √ALT)
```
- **Source:** Sterling RK et al., *Hepatology* 2006;43(6):1317-1325
- **Interpretation:**
  - FIB-4 < 1.30 → Low fibrosis risk (NPV 90%)
  - 1.30–2.67 → Indeterminate zone
  - 2.67–3.25 → High risk
  - FIB-4 > 3.25 → Advanced fibrosis / probable cirrhosis (PPV 80%)
- **Validated in:** Hepatitis B, Hepatitis C, NAFLD (NASH), HIV/HCV co-infection

### Primary Method B: APRI Score (companion to FIB-4)
**Formula:**
```
APRI = (AST / AST_ULN) / (Platelets / 100)
```
Where AST_ULN = 40 U/L (standard upper limit of normal)
- **Source:** Wai CT et al., *Hepatology* 2003;38:518-526
- **Interpretation:**
  - APRI < 0.5 → Low fibrosis (NPV 86%)
  - 0.5–1.0 → Indeterminate
  - 1.0–2.0 → Significant fibrosis F2+ (PPV 61%)
  - > 2.0 → Probable cirrhosis (PPV 62–91%)
- **When used:** Averaged equally with FIB-4 when both AST + Platelets available

### Method C: NAFLD Liver Fat Score (without lab values)
**Formula:**
```
LFS = -2.89 + 1.18×MetS + 0.45×DM + (-0.15×AST/ALT) + 0.04×BMI + 0.04×Insulin
```
- **Source:** Bedogni G et al., *Hepatology* 2006;44:1387-1395
- **Cutoff:** LFS > -0.64 = fatty liver present (sensitivity 85%, specificity 71%)
- **India relevance:** Validates in South Asian cohorts with high NAFLD prevalence at lower BMI

### ML Ensemble (4 Models)

#### 1. Turkish NASH Model (25% weight)
- **Dataset:** 604 biopsy-confirmed Turkish NAFLD/NASH patients
- **Source:** Kabbany MN et al., *Dig Dis Sci* 2017
- **Algorithm:** GradientBoostingClassifier (18 features)
- **Features:** Age, BMI, AST, ALT, GGT, ALP, Albumin, Total Bilirubin, Platelets, Glucose, HbA1c, Total Cholesterol, Triglycerides, Creatinine, Systolic BP, Diabetes, Hypertension, Smoking Status
- **Weight reduced from 30%:** Turkish diet (high olive oil, Mediterranean) ≠ Indian diet

#### 2. ILPD Indian Model (20% weight)
- **Dataset:** 583 Indian patients, Andhra Pradesh
- **Source:** Ramana CV et al., *IJCA* 2012; UCI ML Repository
- **Algorithm:** RandomForestClassifier / LogisticRegression
- **Features:** Age, Gender, Total Bilirubin, Direct Bilirubin, ALP, ALT, AST, Total Proteins, Albumin, A/G Ratio
- **Indian population note:** Only liver ML model trained entirely on Indian patients

#### 3. LPD India Model (40% weight — highest weight)
- **Dataset:** 30,691 rows (largest open Indian liver dataset)
- **Source:** Indian Liver Patient Dataset (ILPD extended, UCI 2012)
- **Algorithm:** GradientBoostingClassifier (AUC 0.998)
- **Weight raised from 35%:** Largest Indian dataset; most demographically representative

#### 4. NHANES CDC Model (15% weight)
- **Dataset:** 9,473 American adults (CDC National Health and Nutrition Examination Survey)
- **Algorithm:** GradientBoostingClassifier (AUC 0.900)
- **Features:** Age, Gender, Albumin, AST/ALT ratio
- **Usage:** Demographic calibration; low weight due to non-Indian population

### India-Specific: Lean NAFLD Rule
- **Rule:** BMI < 23 AND ALT > 40 → +12% risk penalty
- **Source:** Duseja A et al., *J Clin Exp Hepatol* 2015;5:S9-S16
- **Prevalence:** ~25% of Indian NAFLD patients have BMI < 23 (lean NAFLD)
- **Why it matters:** Standard BMI-based screening (BMI>30 = NAFLD) misses 1 in 4 Indian NAFLD patients

### New Lab Markers Added (April 2026)
| Marker | Penalty Rule | Source |
|--------|-------------|--------|
| Hemoglobin < 10 g/dL | +10% | García-Tsao G, Hepatology 2017 — portal HTN / cirrhosis anemia |
| Hemoglobin < 12 g/dL | +6% | Moreau R, J Hepatol 2021 — ACLF decompensation predictor |
| Hemoglobin < 13.5/12 M/F | +3% | Mild CLD anemia signal |
| Triglycerides > 500 mg/dL | +12% | Farrell GC, Hepatology 2006 — severe hepatic steatosis |
| Triglycerides > 200 mg/dL | +7% | Hypertriglyceridemia → NAFLD driver |
| Triglycerides > 150 mg/dL | +3% | Borderline high |

---

## 4. Kidney Model

### Primary Method 0: Reported eGFR (Highest Trust)
- When a lab report directly states "eGFR: X mL/min/1.73m²", use it as-is
- More accurate than CKD-EPI calculation when labs used cystatin-C correction
- `method_used = "reported_egfr"`, confidence = 0.97

### Primary Method 1: CKD-EPI 2021 Creatinine Equation
**Formula:**
```
eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(-1.200) × 0.9938^Age × sex_factor
```
Where:
- Female: κ = 0.7, α = -0.241, sex_factor = 1.012
- Male: κ = 0.9, α = -0.302, sex_factor = 1.0

- **Source:** Inker LA et al., *N Engl J Med* 2021;385:1737-1749
- **Standard:** Gold standard for eGFR estimation, validated in >30 countries
- **KDIGO CKD Staging:**
  - G1 ≥90 mL/min/1.73m² → Normal or high
  - G2 60–89 → Mildly decreased
  - G3a 45–59 → Mildly to moderately decreased
  - G3b 30–44 → Moderately to severely decreased
  - G4 15–29 → Severely decreased
  - G5 <15 → Kidney failure

### eGFR → Risk Conversion
```python
eGFR ≥ 90  → base_risk = 0.05
eGFR 60-89 → base_risk = 0.15
eGFR 45-59 → base_risk = 0.40
eGFR 30-44 → base_risk = 0.60
eGFR 15-29 → base_risk = 0.80
eGFR < 15  → base_risk = 0.95
```

### Secondary ML: Apollo CKD India (when no creatinine)
- **Dataset:** Apollo Hospital Tamil Nadu, 400 CKD patients (Soundarapandian P et al., UCI 2015)
- **Algorithm:** GradientBoostingClassifier + SimpleImputer (AUC 0.991)
- **24 features:** age, bp, sg, al, su, rbc, pc, pcc, ba, bgr, bu, sc, sod, pot, hemo, pcv, wbcc, rbcc, htn, dm, cad, appet, pe, ane
- **Bias note:** Hospital dataset biased toward sick patients → only activated when real lab values present; blended 50/50 with rule-based to reduce false positives

### India-Specific: Diabetic Nephropathy Prior (G6)
- **Rule:** Diabetic with no UACR → +5% extra penalty
- **Source:** Ramachandran A et al., *Diabetes Care* 2003;26(9):2756-2760 (Chennai Urban Rural Epidemiology Study)
- **Justification:** 30% of Indian diabetics have microalbuminuria vs 14-15% Western average → 2× higher silent CKD risk
- When UACR ≥ 300 mg/g → +10%; UACR 30-299 → +5%; UACR < 30 → 0%

### New Lab Markers Added (April 2026)
| Marker | Penalty Rule | Source |
|--------|-------------|--------|
| UricAcid > 7.2 M / > 6.0 F | +4% per mg/dL above threshold | Kanbay M, Kidney Int 2013;83(4):587-593 |
| Hemoglobin < 10 g/dL | +10% | KDIGO 2012 Anemia Guidelines |
| Hemoglobin < 12 g/dL | +5% | Toft G, Kidney Int 2018 |
| Hemoglobin < 13.5/12 M/F | +3% | Mild anemia of CKD |
| BUN > 50 mg/dL | +12% | Uremia risk |
| BUN > 30 mg/dL | +6% | Azotemia |
| BUN > 20 mg/dL | +2% | Borderline |
| Albumin < 3.0 g/dL | +12% | Nephrotic syndrome / protein wasting |

### NFHS-5 District Prior Adjustment
- **Data:** National Family Health Survey-5 (2019-21), 636 districts, India
- **Variables used:** Hypertension prevalence, diabetes prevalence by district
- **Formula:** Bayesian prior adjustment — if district has above-average HTN/DM burden, adds 0.01–0.05 to base kidney risk
- **Source:** Ministry of Health and Family Welfare, Government of India, NFHS-5 District Factsheets

---

## 5. Brain Model

### Primary Method A: CAIDE Dementia Risk Score
**Formula:**
```
CAIDE = Age_score + Education_score + Sex_score + 
        SBP_score + BMI_score + Cholesterol_score + 
        Physical_activity_score
```
Score → Risk:
```
0-5  → 1% (20-year risk)
6-7  → 1.9%
8-9  → 4.2%
10-11→ 7.4%
12-13→ 16.4%
≥14  → 26.8%
```
- **Source:** Kivipelto M et al., *Lancet Neurology* 2006;5:735-741
- **Validation:** 1,449 patients, 20-year follow-up in CAIDE study (Finnish population)
- **Variables:** Age (47–70), Education (high/low), Sex, SBP (≥140), BMI (≥30), Cholesterol (≥6.5 mmol/L), Physical inactivity

### Primary Method B: Framingham Stroke Risk Profile
- **Source:** Wolf PA et al., *Stroke* 1991;22:312-318
- **Variables:** Age, SBP, antihypertensives, diabetes, cigarettes, prior CVD, atrial fibrillation, LVH

### Secondary ML: Alzheimer's Prediction Model
- **Dataset:** OASIS Longitudinal MRI dataset (Marcus DS et al., *J Cognitive Neurosci* 2010)
- **Algorithm:** GradientBoostingClassifier (AUC 0.949)
- **Features:** Age, EDUC (years education), SES, MMSE, eTIV (intracranial volume), nWBV (normalized brain volume), CDR
- **Target:** Dementia vs. non-dementia classification

### Stroke ML Model
- **Dataset:** Kaggle Stroke Prediction Dataset (5,110 patients, Fedesoriano 2021)
- **Algorithm:** GradientBoostingClassifier (AUC 0.828)
- **Features:** age, hypertension, heart_disease, ever_married, work_type, Residence_type, avg_glucose_level, bmi, smoking_status

### India-Specific Brain Adjustments
- **Vascular dementia higher in India:** +10% risk for age >60 + HTN + diabetes combined (INCAP study 2019)
- **Lower education protective:** Education < 10 years → +15% dementia risk (Alladi S, Ann Neurol 2016)

---

## 6. Lungs Model

### Primary Method: GOLD 2023 Pack-Years Criteria
**Pack-years formula:**
```
Pack-years = (Cigarettes_per_day / 20) × Years_smoked × Tobacco_multiplier
```
Tobacco multipliers:
- Cigarette: 1.0
- Bidi: 1.5 (1 bidi = 1.5 cigarette-equivalents, 3× tar content)
- Hookah: 0.5
- Mixed: 1.2

**Risk by pack-years (GOLD 2023):**
```
< 10  → +5% (minimal risk)
10-19 → +15% (mild COPD risk — spirometry advised)
20-39 → +28% (significant — pulmonology referral)
≥ 40  → +42% (severe — LDCT screening recommended)
```
- **Source:** GOLD 2023 COPD Guidelines (https://goldcopd.org)
- **Bidi source:** Salvi SS & Barnes PJ, *Lancet* 2009;374:733-743 — COPD in non-smokers

### GOLD Spirometry Staging (when FEV1% available)
**Formula:**
```
FEV1% predicted = (FEV1_measured / FEV1_predicted) × 100
```
Risk by FEV1%:
- ≥ 80% → GOLD 1 Mild (+15%)
- 50–79% → GOLD 2 Moderate (+30%)
- 30–49% → GOLD 3 Severe (+50%)
- < 30% → GOLD 4 Very Severe (+70%)

### Jindal 2012 Indian Spirometry Norms (G5)
**Why:** Western reference values (NHANES/GLI-2012) over-diagnose restriction in Indians. Indian lung volumes are 15-20% smaller at same height/age (Glindmeyer 1999, Cotes 1993).

**Equations (Jindal 2012, Table 2):**
```
Men:   FEV1 = 0.0348 × Height(cm) - 0.0204 × Age - 1.570
Women: FEV1 = 0.0298 × Height(cm) - 0.0180 × Age - 1.145
```
- **Source:** Jindal SK et al., *Indian J Chest Dis Allied Sci* 2012;54(2):93-98
- **Validated on:** 6,994 healthy Indian adults (north + south India)

### AQI Lung Risk (CPCB India 2023)
**Formula:**
```
AQI risk increment = 0 (PM2.5 ≤ 40) | 0.05 (40-60) | 0.12 (60-100) | 0.20 (>100)
```
- **Data:** CPCB Annual AQI Report 2023, 28 Indian cities
- **Source:** Central Pollution Control Board, Ministry of Environment
- **Top 5 high-risk cities:** Delhi (98.6 µg/m³), Gurgaon (91.2), Noida (87.4), Ghaziabad (89.7), Patna (78.9)
- **WHO safe limit:** 5 µg/m³ annual PM2.5 (India exceeds 10-20× in most cities)

### Cooking Fuel Biomass Risk (India-specific)
**Risk increments:**
```python
{
  "wood":      0.20,  # Solid biomass — highest HAP exposure
  "dung":      0.22,  # Cow dung — highest PM2.5 output
  "crop":      0.18,  # Crop residue burning
  "kerosene":  0.15,  # Toxic fumes, carcinogenic
  "coal":      0.18,  # Coal combustion
  "lpg":       0.02,  # Clean fuel — minimal risk
  "electric":  0.01,  # Zero combustion
  "biogas":    0.03,  # Cleaner biomass
}
```
- **Source:** Balakrishnan K et al., *Lancet Planet Health* 2019;3(1):e26-e37
- **Prevalence:** ~60% of Indian rural households use solid biomass fuels (Census 2011)
- **HAP = Household Air Pollution:** 600,000 deaths/year in India (IHME GBD 2019)

### Indoor Radon by Indian State
**Risk formula:** +16% lung cancer risk per 100 Bq/m³ above national average (42 Bq/m³)
```
risk_increment = min(0.12, (Radon_bq - 42) / 100 × 0.16)
```
- **Source:** WHO Indoor Radon Handbook 2009; AMD/BARC India Radiation Survey 2011
- **High-risk states:** Kerala 91 Bq/m³, Rajasthan 79, Jharkhand 68, HP 58

### TB History Lung Risk
- Active TB → +40% lung risk (active disease)
- Past/treated TB → +20% lung risk (post-TB obstructive pattern)
- **Source:** Allwood BW et al., *Int J Tuberc Lung Dis* 2013 — ~40% of TB survivors develop obstructive lung disease

### State-Level TB Comorbidity Risk
- Data: RNTCP/NTEP Annual Report, Ministry of Health, India
- State-level `lung_tb_risk_multiplier`: 1.0–1.25 depending on state TB burden

### Lung Cancer ML Model (Survey-based)
- **AUC:** 0.857
- **Features:** Symptom survey (cough duration, dyspnea, hemoptysis, smoking, exposure)
- **Usage:** Secondary signal alongside clinical formula

---

## 7. Biological Age Engine

### Formula
```
Biological_Age = Chronological_Age + Σ(organ_age_deltas)
```

Where each organ contributes:
```
organ_age_delta = (organ_risk - 0.15) × organ_weight × 20
```
Risk thresholds → age delta:
- Risk > 0.75 → +10 to +20 years
- Risk 0.50–0.75 → +5 to +10 years
- Risk 0.25–0.50 → 0 to +5 years
- Risk < 0.25 → -3 to 0 years (protective)

**Organ weights:**
```python
{
  "heart":  0.35,   # Cardiovascular leads aging
  "brain":  0.25,   # Neurodegeneration second
  "liver":  0.15,
  "kidney": 0.15,
  "lungs":  0.10,
}
```

**Lifestyle modifiers:**
- Sleep 7-9h/night → -1 year
- Exercise Active → -2 years
- Exercise Sedentary → +3 years
- Smoking Daily → +3 years
- Alcohol Daily → +2 years
- Stress High → +2 years

**Source:** Concept inspired by Levine ME et al., *Aging* 2018 (PhenoAge); Belsky DW et al., *PNAS* 2015 (Pace of Aging)

---

## 8. Stress Heatmap

### Algorithm
Multi-dimensional stress score:
1. **Reported stress** (Low=1, Medium=2, High=3) → weight 0.35
2. **Sleep deprivation** (optimal: 7-9h; each hour below 6 adds penalty) → weight 0.20
3. **Physiological markers** (elevated BP, elevated cortisol proxies) → weight 0.25
4. **Lifestyle** (smoking + alcohol combination) → weight 0.20

Output: Per-organ stress contribution displayed as body heatmap.

---

## 9. Medication Modeler

**Purpose:** After organ risk is calculated, apply evidence-based modifiers for medications the user reports taking.

### Drug Classes and Their Organ Effects

| Drug Class | Examples | Heart | Liver | Kidney | Brain | Lungs |
|-----------|----------|-------|-------|--------|-------|-------|
| ACE Inhibitors | ramipril, lisinopril | -20% | 0 | -15% | -5% | 0 |
| ARBs | losartan, valsartan | -18% | 0 | -15% | -5% | 0 |
| Beta-blockers | atenolol, metoprolol | -20% | 0 | 0 | +3% | -5% |
| Statins | atorvastatin, rosuvastatin | -25% | +5% | 0 | -10% | 0 |
| SGLT2i | empagliflozin, dapagliflozin | -15% | -5% | -20% | 0 | 0 |
| GLP-1 RA | semaglutide, liraglutide | -15% | -10% | -10% | -5% | 0 |
| Metformin | metformin | -8% | -5% | 0 | -5% | 0 |
| NSAIDs | ibuprofen, diclofenac, naproxen | +5% | +8% | +12% | 0 | 0 |
| Anticoagulants | warfarin, apixaban, dabigatran | -10% | +5% | 0 | -15% | 0 |
| Antiepileptics | phenytoin, valproate | +3% | +15% | 0 | 0 | 0 |
| Antiretrovirals | tenofovir, efavirenz | 0 | +10% | +8% | 0 | 0 |
| Oral Contraceptives | - | +10% | +5% | 0 | +8% | 0 |
| Corticosteroids | prednisolone, dexamethasone | +10% | +8% | +5% | +5% | -5% |
| Bronchodilators | salbutamol, formoterol | +3% | 0 | 0 | 0 | -25% |
| Inhaled Corticosteroids | budesonide, fluticasone | 0 | 0 | 0 | 0 | -15% |
| Antivirals (HBV/HCV) | tenofovir, sofosbuvir | 0 | -30% | 0 | 0 | 0 |
| Proton Pump Inhibitors | omeprazole, pantoprazole | 0 | +3% | +3% | 0 | 0 |
| Pioglitazone | pioglitazone | +5% | -20% | 0 | 0 | 0 |

**Key clinical references:**
- ACE/ARB renal protection: RENAAL Trial (*NEJM* 2001;345:861-869)
- SGLT2i kidney/heart protection: EMPA-REG (*NEJM* 2015), CREDENCE (*NEJM* 2019)
- Statin pleiotropic effects: JUPITER Trial (*NEJM* 2008;359:2195-2207)
- Pioglitazone liver: PIVENS Trial (*NEJM* 2010;362:1675-1685)

---

## 10. India-Specific Adjustments

### Summary Table

| Adjustment | What it does | Source |
|-----------|-------------|--------|
| South Asian Heart PCE ×1.26 | Corrects PCE for Indian cardiovascular excess risk | Enas EA, Indian Heart Journal 2011 |
| Lean NAFLD (BMI<23 + ALT>40) | +12% liver risk when normal BMI but elevated ALT | Duseja A, JCEH 2015 |
| Indian Spirometry Norms (Jindal) | Uses Indian FEV1 equations instead of Western (15-20% smaller) | Jindal SK, IJCDAS 2012 |
| Diabetic Nephropathy Prior | +5% kidney risk for Indian diabetics without UACR | Ramachandran A, Diabetes Care 2003 |
| City AQI (28 cities) | PM2.5-based lung risk from CPCB 2023 data | CPCB Annual Report 2023 |
| Cooking fuel HAP | Biomass fuel → 15-22% lung risk | Balakrishnan K, Lancet Planet Health 2019 |
| State TB Comorbidity | State-level lung TB risk multiplier (1.0–1.25) | RNTCP/NTEP Annual Report |
| State Radon | Indoor radon lung cancer risk by Indian state | AMD/BARC India 2011; WHO Radon Handbook 2009 |
| NFHS-5 District Prior | Bayesian kidney/diabetes/HTN adjustment by district | NFHS-5 2019-21, 636 districts |
| ILPD Indian Liver ML (20%) | Liver ML model trained on 583 Indian patients, AP | Ramana CV, IJCA 2012 |
| LPD India (40% weight) | Liver ML ensemble — 30,691 Indian rows | UCI ML Repository |

---

## 11. All Datasets Used

| Dataset | Organ | Size | Source | Year |
|---------|-------|------|--------|------|
| Framingham Heart Study cohorts | Heart | ~24,626 | Goff DC, JACC 2014 | 2014 |
| Cleveland Clinic Heart Disease (UCI) | Heart | 303 pts | Detrano R, UCI ML Repository | 1988 |
| Kaggle Stroke Prediction | Brain/Heart | 5,110 pts | Fedesoriano, Kaggle | 2021 |
| OASIS Longitudinal MRI | Brain | ~373 pts | Marcus DS, J Cog Neurosci 2010 | 2010 |
| Turkish NASH Biopsy | Liver | 604 pts | Kabbany MN, Dig Dis Sci 2017 | 2017 |
| ILPD (Indian Liver Patient Dataset) | Liver | 583 pts | Ramana CV, IJCA 2012 | 2012 |
| LPD India (Large) | Liver | 30,691 rows | UCI ML Repository | 2012 |
| NHANES CDC | Liver | 9,473 pts | CDC NHANES | 2021 |
| Apollo Hospital CKD (Tamil Nadu) | Kidney | ~400 pts | Soundarapandian P, UCI 2015 | 2015 |
| NFHS-5 India | Kidney/All | 636 districts | GoI MoHFW | 2021 |
| CPCB AQI Report | Lungs | 28 cities | Central Pollution Control Board | 2023 |
| AMD/BARC Radon Survey | Lungs | All states | Atomic Minerals Directorate | 2011 |
| RNTCP/NTEP TB Report | Lungs | All states | Ministry of Health, India | 2023 |

---

## 12. All Formulas Used

```
# HEART
PCE_risk = 1 - S₀^exp(Σβᵢ·Xᵢ - μ)            # Framingham PCE
Final_heart = PCE_risk × 1.26                  # South Asian correction

# LIVER
FIB-4 = (Age × AST) / (Platelets × √ALT)
APRI = (AST/40) / (Platelets/100)
NAFLD-LFS = -2.89 + 1.18×MetS + 0.45×DM - 0.15×AST/ALT + 0.04×BMI

# KIDNEY
eGFR = 142 × min(Scr/κ,1)^α × max(Scr/κ,1)^(-1.200) × 0.9938^Age × sex
UACR_risk = base + (0.20 if UACR>300 else 0.08 if UACR>30 else 0)

# LUNGS
Pack-years = (CPD/20) × Years × Tobacco_mult
Radon_risk = min(0.12, (Radon_bq - 42) / 100 × 0.16)
FEV1_pct = (FEV1_measured / Jindal_predicted) × 100
Jindal_M: FEV1 = 0.0348×H - 0.0204×A - 1.570
Jindal_F: FEV1 = 0.0298×H - 0.0180×A - 1.145

# BRAIN
CAIDE_score = Σ(age + education + sex + SBP + BMI + cholesterol + activity)

# BIOLOGICAL AGE
Bio_age = Chron_age + Σ(organ_risk - 0.15) × weight × 20

# URIC ACID (KIDNEY)
UricAcid_risk = min(0.15, (UA - threshold) × 0.04)
# threshold: 7.2 mg/dL men, 6.0 mg/dL women
```

---

## 13. Confidence & Trust Framework

### Confidence Levels per Method

| Method | Confidence | Why |
|--------|-----------|-----|
| Reported eGFR | 0.97 | Lab-reported value, highest trust |
| CKD-EPI eGFR | 0.95 | Gold standard validated formula |
| GOLD Spirometry (FEV1) | 0.95 | Direct spirometry data |
| FIB-4 + APRI + ML ensemble | 0.92 | Multiple corroborating signals |
| FIB-4 alone | 0.85 | Formula + good evidence base |
| Apollo CKD India ML | 0.88 | AUC 0.991 but hospital dataset bias |
| Framingham PCE | 0.87 | Population-level formula, South Asian caveat |
| ILPD Indian ML | 0.82 | Indian data, smaller dataset |
| NAFLD-LFS (no labs) | 0.65 | Formula without labs |
| Rule-based | 0.52–0.55 | Heuristics only |
| Smoking category heuristic | 0.45 | No clinical measurements |

### What each confidence score affects
- Displayed on results screen as "Model Confidence: X%"
- Used by clinical inference layer to flag low-confidence outputs
- Determines whether to show "Upload lab report for better accuracy" prompts

---

## 14. Known Gaps & Limitations

### 🔴 Critical
1. **`YearsSmokedmoked` typo** in `app.py` — pack-years calculation always uses fallback; fix needed
2. **`user_data.dict()`** deprecated in Pydantic V2 — use `model_dump()` instead
3. **sklearn feature_names warning** — models trained on DataFrames, called with plain lists; cosmetic but risks numeric drift
4. **Heart model** doesn't use `LDLCholesterol`, `HDLCholesterol` from new PascalCase mapping (only uses `TotalCholesterol`)
5. **Brain model** uses `systolic_bp` (old snake_case) but not `SystolicBP` (new PascalCase)

### 🟡 Moderate
6. **PDF parser** doesn't extract: `bun`, `uric_acid`, `egfr`, `triglycerides`, `albumin`, `hemoglobin`, `fev1_percent`
7. **UACR** now in HealthInfo model but nothing sends it (no form field, no PDF parsing)
8. **Biological age** doesn't use direct lab inputs (HbA1c, creatinine)
9. **Liver metrics dict** doesn't include `hemoglobin_flag` or `trig_flag` for frontend display
10. **ngrok URL** changes every session (free plan limitation)

### 🟢 Minor / Future
11. No ophthalmology model (diabetic retinopathy — high prevalence in India)
12. No bone health / osteoporosis model
13. No thyroid model (hypothyroidism very common in Indian women)
14. No PCOS model
15. Waist circumference not collected (better metabolic syndrome marker than BMI for Indians)
16. No pancreas / diabetes progression model
17. No genetic risk factors (APOE ε4 for Alzheimer's, BRCA for cancer)
18. Simulation "future self" projections are rule-based, not trained on longitudinal data

---

## Appendix A: File Map

```
model/
├── app.py                          # FastAPI endpoint, HealthInfo Pydantic model
├── simulation_engine.py            # VitalTwinSimulator orchestrator
├── models/
│   ├── base_model.py               # BaseOrganModel (shared utilities)
│   ├── heart_model.py              # PCE + Cleveland ML + South Asian correction
│   ├── liver_model.py              # FIB-4 + APRI + 4-model ensemble
│   ├── kidney_model.py             # CKD-EPI + Apollo India ML
│   ├── brain_model.py              # CAIDE + OASIS ML + Stroke ML
│   └── lungs_model.py              # GOLD + Pack-years + AQI + Jindal
├── features/
│   ├── biological_age.py           # Biological age calculation
│   └── stress_heatmap.py           # Multi-dimensional stress scoring
├── utils/
│   ├── clinical_inference.py       # Cross-organ consistency checks
│   ├── district_priors.py          # NFHS-5 district-level Bayesian priors
│   └── input_completeness.py       # Field completeness checker
├── data/india/
│   └── tb/tb_lung_risk_by_state.json  # State-level TB lung risk
└── models/ (trained .pkl files)
    ├── heart_model.pkl             # Cleveland UCI trained
    ├── heart_model_v2.pkl          # Extended features
    ├── liver_model.pkl             # Turkish NASH (60% weight)
    ├── liver_ilpd_model.pkl        # Indian ILPD (40% weight)
    ├── liver_lpd_ml.pkl            # LPD India (30,691 rows)
    ├── nhanes_liver_ml.pkl         # NHANES CDC (9,473 rows)
    ├── kidney_ml.pkl               # Apollo Tamil Nadu (AUC 0.991)
    ├── brain_model.pkl             # OASIS Alzheimer's
    ├── stroke_model.pkl            # Kaggle stroke (AUC 0.828)
    ├── lung_cancer_ml.pkl          # Symptom survey (AUC 0.857)
    └── lungs_model.pkl             # Primary lungs model
```

---

*This document is auto-generated from source code inspection and maintained by the VitalTwin team.*
*For clinical use queries, see TRUST_FRAMEWORK.md and CITATIONS.json.*
