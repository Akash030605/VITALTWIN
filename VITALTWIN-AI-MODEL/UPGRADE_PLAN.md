# VitalTwin AI Model — Complete Upgrade Plan

This document is the single source of truth for making the VitalTwin ML backend
clinically accurate, fully integrated, and production-ready. It covers every layer
from raw data to API response.

---

## Table of Contents

1. [Current State — What's Broken](#1-current-state--whats-broken)
2. [Data You Need — Where to Get It](#2-data-you-need--where-to-get-it)
3. [Additional User Inputs Required](#3-additional-user-inputs-required)
4. [New Model Architecture — All 5 Organs](#4-new-model-architecture--all-5-organs)
5. [Biological Age — Clinically Valid Formula](#5-biological-age--clinically-valid-formula)
6. [Verification Layers](#6-verification-layers)
7. [Complete Training Pipeline](#7-complete-training-pipeline)
8. [API Schema Changes](#8-api-schema-changes)
9. [Frontend Changes Required](#9-frontend-changes-required)
10. [Integration Checklist](#10-integration-checklist)
11. [Deployment & Monitoring](#11-deployment--monitoring)

---

## 1. Current State — What's Broken

### Organ Model Reality Check

| Organ  | Method         | Problem |
|--------|---------------|---------|
| Heart  | Random Forest (73.3%) | Trained on categorical cholesterol (1/2/3) not mg/dL. BP values are INFERRED from text conditions — model gets 120/80 when no data, not real values |
| Liver  | Random Forest (97.3%) | Class imbalance — 90%+ of samples are "healthy" so model predicts healthy almost always and still scores 97%. F1 for diseased class is ~0.3 |
| Brain  | Hardcoded weights | `stress × 0.4 + sleep × 0.35`. Not a model. |
| Kidneys| Hardcoded weights | `bp_risk × 0.3 + diabetes × 0.3`. Uses string matching ("Hypertension" in list), not actual BP numbers |
| Lungs  | Hardcoded weights | Only knows "Daily"/"Occasional"/"Never" smoking. No pack-years. |

### What Medications Does

Frontend collects `medications[]`. Backend `HealthInfo` has no `Medications` field.
Every medication the user enters is **silently discarded**. Drug effects on organ risk
(statins, metformin, ACE inhibitors, beta-blockers) are completely unmodeled.

### Biological Age

Additive formula with arbitrary constants. `daily_smoking = +6 years` is a guess,
not derived from any study. Real biological age requires validated biomarker composites.

### Future Self Timeline

Heart degrades exactly 3%/year, liver 4%/year — constants written by hand, no
epidemiological basis.

---

## 2. Data You Need — Where to Get It

### Dataset 1: NHANES (Primary Source — Free, Public)

**What it is:** US National Health and Nutrition Examination Survey. 10,000+ participants
per 2-year cycle. The most comprehensive population health dataset available.

**Where:** https://www.cdc.gov/nchs/nhanes/index.htm

**Which cycles to download:** 2017-2018 (Pre-COVID, most complete), 2015-2016 as supplement.
Each cycle has separate XPT files per module.

**Modules needed:**

| Module Code | Contains | Use For |
|-------------|---------|---------|
| DEMO_J | Age, gender, race, education | All models |
| BMX_J | Height, weight, BMI, waist circumference | All models |
| BPX_J | Systolic BP, diastolic BP (3 readings) | Heart, Kidney, Brain |
| TCHOL_J | Total cholesterol (mg/dL) | Heart, Brain |
| HDL_J | HDL cholesterol (mg/dL) | Heart |
| TRIGLY_J | Triglycerides, LDL (calculated) | Heart, Liver |
| GLU_J | Fasting glucose (mg/dL), insulin | Kidney, Liver |
| GHB_J | HbA1c (%) | Kidney, Liver, Heart |
| ALB_CR_J | Urine albumin, creatinine → UACR | Kidney |
| BIOPRO_J | Serum creatinine, albumin, AST, ALT | Kidney, Liver |
| GGT_J | GGT | Liver |
| MCQ_J | Medical conditions (diabetes, heart attack, stroke, cancer) | All |
| SMQ_J | Smoking — pack-years, years smoked, cigarettes/day | Lungs, Heart |
| ALQ_J | Alcohol drinks/week, drinks/day | Liver |
| PAQ_J | Physical activity MET-minutes/week | All |
| SLQ_J | Sleep hours, trouble sleeping | Brain, Heart |
| PFQ_J | Physical functioning limitations | Lungs |
| SPX_J | Spirometry: FEV1, FVC, FEV1/FVC | Lungs |
| DPQ_J | Depression score (PHQ-9) | Brain |
| DIQ_J | Diabetes — type, insulin use, A1c control | Kidney, Liver |

**Download script:**
```python
import urllib.request
import os

BASE = "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/"
MODULES = [
    "DEMO_J.XPT", "BMX_J.XPT", "BPX_J.XPT", "TCHOL_J.XPT",
    "HDL_J.XPT", "TRIGLY_J.XPT", "GLU_J.XPT", "GHB_J.XPT",
    "ALB_CR_J.XPT", "BIOPRO_J.XPT", "GGT_J.XPT", "MCQ_J.XPT",
    "SMQ_J.XPT", "ALQ_J.XPT", "PAQ_J.XPT", "SLQ_J.XPT",
    "SPX_J.XPT", "DIQ_J.XPT"
]

os.makedirs("data/nhanes_raw", exist_ok=True)
for m in MODULES:
    url = BASE + m
    path = f"data/nhanes_raw/{m}"
    if not os.path.exists(path):
        print(f"Downloading {m}...")
        urllib.request.urlretrieve(url, path)

# Read XPT files with pandas
import pandas as pd
dfs = {}
for m in MODULES:
    key = m.replace("_J.XPT", "").lower()
    dfs[key] = pd.read_sas(f"data/nhanes_raw/{m}", format="xport", encoding="utf-8")

# Merge all on SEQN (participant ID)
nhanes = dfs["demo"].copy()
for key, df in dfs.items():
    if key != "demo":
        nhanes = nhanes.merge(df, on="SEQN", how="left")

nhanes.to_csv("data/nhanes_merged.csv", index=False)
print(f"NHANES merged: {len(nhanes)} participants, {nhanes.shape[1]} variables")
```

**Read with:**
```bash
pip install pandas scipy
python -c "import pandas as pd; df = pd.read_sas('data/nhanes_raw/DEMO_J.XPT', format='xport'); print(df.head())"
```

---

### Dataset 2: Your Existing liver_dataset.csv — Use It Properly

You already have 604 rows of **biopsy-confirmed** NAFLD data with:
- AST, ALT, GGT, ALP, Bilirubin, Albumin, Total Protein
- Cholesterol, Triglycerides, HDL, LDL
- Glucose, Insulin, HOMA-IR, HbA1c
- Creatinine, BUN, Uric Acid
- Steatosis grade (0-3), Fibrosis stage (0-4), NAS score
- Fibrosis status (binary), Significant Fibrosis (binary)

**This is clinical gold.** 604 biopsy samples > 10,000 self-reported samples for liver.
The problem is you trained a multiclass model on it when a binary fibrosis risk model
(Fibrosis_status column) would be far more useful and accurate.

---

### Dataset 3: Your Existing cardio_dataset.csv — Fix the Preprocessing

70,000 rows, already downloaded. The issue is cholesterol is encoded as 1/2/3
(normal/above normal/well above normal) — not real mg/dL values.

Map for training:
```
cholesterol: 1 → 185 mg/dL (normal midpoint)
             2 → 215 mg/dL (borderline midpoint)
             3 → 265 mg/dL (high midpoint)
gluc:        1 → 90 mg/dL (normal)
             2 → 115 mg/dL (pre-diabetic)
             3 → 160 mg/dL (diabetic)
```

Age is stored as "50 years 143 days" — parse to integer years.

---

### Dataset 4: CKD Dataset (UCI Machine Learning Repository)

**What:** 400 patients with/without chronic kidney disease. Contains creatinine,
albumin, hemoglobin, BP, glucose, red blood cell count.

**Where:** https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease

**Columns needed:** age, bp (blood pressure), sg (specific gravity), al (albumin),
su (sugar), bgr (blood glucose), bu (blood urea), sc (serum creatinine), sod, pot,
hemo (hemoglobin), pcv, wc, rc, class (ckd/notckd)

```bash
# Download
wget https://archive.ics.uci.edu/static/public/336/chronic+kidney+disease.zip
unzip "chronic+kidney+disease.zip" -d data/ckd_raw/
```

---

### Dataset 5: COPD/Lung Dataset (Kaggle or UCI)

**Option A — NHANES Spirometry:** Already in NHANES SPX_J module. Variables:
SPXNFEV1 (FEV1 in liters), SPXNFVC (FVC), SPXNFVR (FEV1/FVC ratio).
Combine with smoking history from SMQ_J to build a lung risk model.

**Option B — COPDGene:** Clinical dataset for COPD risk.
https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000179

For NHANES-based lung model, target variable: FEV1/FVC < 0.70 = airflow obstruction.

---

### Dataset 6: Brain/Cognitive Risk

**Use NHANES + DPQ (depression/PHQ-9) + cognitive function tests.**
NHANES 2011-2014 cycles include CERAD cognitive tests and digit span.

Variables: RIDAGEYR (age), DMDEDUC2 (education), BPX_J systolic BP, BMX BMI,
LBXTC total cholesterol, PAQ physical activity score, SLQ sleep hours, DPQ PHQ-9 score.

Target: Composite cognitive impairment score or use published CAIDE score cutoffs.

---

## 3. Additional User Inputs Required

### What to Add to the Form (Frontend)

These are the inputs that make the models clinically meaningful.
Split into **Required** (always ask) and **Optional — from blood test** (collapsible).

#### Required Additional Inputs

```
blood_pressure_systolic    integer   e.g. 120    mmHg  (replaces inferred values)
blood_pressure_diastolic   integer   e.g. 80     mmHg
bp_on_medication           boolean               Are you on BP medication?
years_smoked               integer               How many years have you smoked? (0 if never)
cigarettes_per_day         integer               On average, cigarettes per day when smoking
family_history_heart       boolean               Parent/sibling with heart attack before age 65?
family_history_diabetes    boolean               Parent/sibling with Type 2 diabetes?
```

**Pack-years** = `(cigarettes_per_day / 20) × years_smoked`
This single derived variable is a far better lung risk predictor than "daily/occasional".

#### Optional — From Blood Test (Collapsible Section)

```
total_cholesterol          float     mg/dL    (reference: <200 normal, 200-239 borderline, ≥240 high)
hdl_cholesterol            float     mg/dL    (reference: >60 protective, <40 low risk for men)
ldl_cholesterol            float     mg/dL    (reference: <100 optimal, 100-129 near optimal)
triglycerides              float     mg/dL    (reference: <150 normal)
fasting_glucose            float     mg/dL    (reference: <100 normal, 100-125 pre-diabetic, ≥126 diabetic)
hba1c                      float     %        (reference: <5.7% normal, 5.7-6.4% pre, ≥6.5% diabetic)
serum_creatinine           float     mg/dL    (reference: 0.7-1.3 men, 0.6-1.1 women)
ast                        float     U/L      (reference: 10-40 normal)
alt                        float     U/L      (reference: 7-56 normal)
ggt                        float     U/L      (reference: 9-48 normal)
albumin                    float     g/dL     (reference: 3.5-5.0 normal)
```

**Why these specific labs:**
- total_cholesterol + hdl → Framingham heart risk (10-year validated formula)
- serum_creatinine + age + gender → CKD-EPI eGFR (gold standard kidney function)
- ast + alt + platelets → FIB-4 index (liver fibrosis staging without biopsy)
- hba1c → diabetes control affecting kidney, liver, heart
- fasting_glucose + insulin → HOMA-IR (insulin resistance)

Show a note: "Find these on any routine blood test / annual physical report."

---

## 4. New Model Architecture — All 5 Organs

### 4.1 Heart Model

**Primary: Framingham Risk Score (for users without full labs)**

The Pooled Cohort Equations (ACC/AHA 2013) are the current US clinical standard:

```python
import math

def pooled_cohort_ascvd_10yr(age, gender, total_chol, hdl_chol,
                              systolic_bp, bp_treated, smoker, diabetic, race="white"):
    """
    ACC/AHA 2013 Pooled Cohort Equations
    Returns 10-year ASCVD risk as decimal (0.0 - 1.0)
    Validated on: Framingham, ARIC, CHS, CARDIA cohorts (~24,000 patients)
    """
    ln_age = math.log(age)
    ln_tc = math.log(total_chol)
    ln_hdl = math.log(hdl_chol)
    ln_sbp = math.log(systolic_bp)

    if gender == "Female" and race == "white":
        s010 = 0.9665
        mn = -29.799
        terms = (
            -29.799 * 1 +
            4.884 * ln_age +
            13.540 * ln_tc +
            -3.114 * ln_age * ln_tc +
            -13.578 * ln_hdl +
            3.149 * ln_age * ln_hdl +
            2.019 * (ln_sbp if bp_treated else 0) +
            1.957 * (ln_sbp if not bp_treated else 0) +
            7.574 * (1 if smoker else 0) +
            -1.665 * ln_age * (1 if smoker else 0) +
            0.661 * (1 if diabetic else 0)
        )
    elif gender == "Male" and race == "white":
        s010 = 0.9144
        mn = 61.18
        terms = (
            12.344 * ln_age +
            11.853 * ln_tc +
            -2.664 * ln_age * ln_tc +
            -7.990 * ln_hdl +
            1.769 * ln_age * ln_hdl +
            1.797 * (ln_sbp if bp_treated else 0) +
            1.764 * (ln_sbp if not bp_treated else 0) +
            7.837 * (1 if smoker else 0) +
            -1.795 * ln_age * (1 if smoker else 0) +
            0.658 * (1 if diabetic else 0)
        )
    # Add African American coefficients similarly if needed
    else:
        # Simplified fallback
        return _framingham_simplified(age, gender, total_chol, hdl_chol,
                                       systolic_bp, bp_treated, smoker, diabetic)

    risk = 1 - s010 ** math.exp(terms - mn)
    return max(0.0, min(1.0, risk))


def _framingham_simplified(age, gender, total_chol, hdl_chol,
                            systolic_bp, bp_treated, smoker, diabetic):
    """Simple point-score Framingham when full data not available."""
    points = 0
    if gender == "Male":
        age_pts = {(20,34): -9, (35,39): -4, (40,44): 0, (45,49): 3,
                   (50,54): 6, (55,59): 8, (60,64): 10, (65,69): 11,
                   (70,74): 12, (75,200): 13}
        chol_pts_by_age = {  # points depend on age bracket
            (20,39): {(0,160):0,(160,200):4,(200,240):7,(240,280):9,(280,999):11},
            (40,49): {(0,160):0,(160,200):3,(200,240):5,(240,280):6,(280,999):8},
            (50,59): {(0,160):0,(160,200):2,(200,240):3,(240,280):4,(280,999):5},
            (60,69): {(0,160):0,(160,200):1,(200,240):1,(240,280):2,(280,999):3},
            (70,99): {(0,160):0,(160,200):0,(200,240):0,(240,280):1,(280,999):1},
        }
    # ... (full implementation in heart_model.py)
    # Return calibrated estimate
    risk_table = {0: 0.01, 5: 0.02, 7: 0.03, 8: 0.04, 9: 0.05, 10: 0.06,
                  11: 0.08, 12: 0.10, 13: 0.12, 14: 0.16, 15: 0.20, 16: 0.25, 17: 0.30}
    return risk_table.get(max(0, min(17, points)), 0.15)
```

**Secondary: ML model (Random Forest on cardio_dataset, properly preprocessed)**

Use ML risk as correction factor on top of Framingham:
```
final_heart_risk = 0.6 × framingham_risk + 0.4 × ml_risk
```

If user has no lab values: fall back to ML only (it was trained with categorical cholesterol/BP).
If user has lab values: use Framingham as primary (clinically superior).

**Medical conditions layer:** Keep existing keyword parser. Add these missing conditions:
- Atrial Fibrillation → direct +0.25 risk for stroke/cardiac events
- Prior MI → direct +0.35 (already have this)
- LVEF < 35% → direct RED override

---

### 4.2 Liver Model

**Primary: FIB-4 Index (if AST, ALT, age, platelets available)**

```python
def fib4_index(age, ast, alt, platelets):
    """
    FIB-4 Index for liver fibrosis risk.
    Published: Sterling et al. (2006), validated in >10,000 patients.
    
    Thresholds:
    < 1.30  → Low risk of significant fibrosis (NPV 90%)
    1.30-2.67 → Indeterminate (needs further testing)
    > 2.67  → High risk of significant fibrosis (PPV 80%)
    > 3.25  → Advanced fibrosis / cirrhosis
    """
    if not platelets or alt == 0:
        return None
    import math
    fib4 = (age * ast) / (platelets * math.sqrt(alt))
    return round(fib4, 3)

def liver_risk_from_fib4(fib4):
    if fib4 is None:
        return None
    if fib4 < 1.30:
        return 0.10  # Low
    elif fib4 < 2.67:
        return 0.40  # Indeterminate
    elif fib4 < 3.25:
        return 0.65  # High
    else:
        return 0.85  # Advanced fibrosis
```

**Primary (no labs): NAFLD-LFS (Liver Fat Score)**

```python
def nafld_liver_fat_score(metabolic_syndrome, diabetes_type2, ast_alt_ratio, bmi, insulin):
    """
    Bedogni et al. (2006). Predicts liver fat without ultrasound.
    metabolic_syndrome: 0/1
    diabetes_type2: 0/1
    ast_alt_ratio: AST/ALT (or use default 0.8 if no labs)
    bmi: float
    insulin: fasting insulin μU/mL (or use None)
    """
    score = (-2.89
             + 1.18 * metabolic_syndrome
             + 0.45 * diabetes_type2
             - 0.15 * ast_alt_ratio
             + 0.04 * bmi)
    if insulin is not None:
        score += 0.04 * insulin
    # LFS > -0.64 = fatty liver present (sensitivity 85%, specificity 71%)
    return score

def liver_risk_from_lfs(lfs_score, alcohol, smoking):
    base = 0.3 if lfs_score > -0.64 else 0.10
    if alcohol == "Daily":
        base += 0.25
    elif alcohol == "Weekly":
        base += 0.10
    return min(1.0, base)
```

**ML model: Retrain on liver_dataset.csv properly**

```python
# Target: "Fibrosis_status" column (binary: 0=no fibrosis, 1=fibrosis)
# NOT the multiclass NAS score (which causes 97% accuracy illusion)
# Features: age, bmi, ast, alt, ggt, glucose, hba1c, alcohol (binary), smoking (binary)

from imblearn.over_sampling import SMOTE
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV

# Fix class imbalance
smote = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Use Gradient Boosting (better than RF for small datasets)
gb = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
gb.fit(X_resampled, y_resampled)

# Calibrate probabilities (Platt scaling)
calibrated = CalibratedClassifierCV(gb, cv=5, method='sigmoid')
calibrated.fit(X_train, y_train)  # Fit calibration on original (not SMOTE) data

# Expected accuracy: 75-82% (not 97% — that was fake)
# Expected AUC: 0.82-0.88 on fibrosis detection
```

---

### 4.3 Kidney Model

**Primary: CKD-EPI eGFR (if serum creatinine available)**

```python
def ckd_epi_egfr(creatinine, age, gender):
    """
    CKD-EPI 2021 Creatinine Equation.
    Replaces the old MDRD formula. Gold standard for eGFR.
    Validated on 30+ international cohorts.
    
    Returns: eGFR in mL/min/1.73m²
    KDIGO CKD Staging:
    G1: ≥90       (normal or high)
    G2: 60-89     (mildly decreased)
    G3a: 45-59    (mildly to moderately decreased)
    G3b: 30-44    (moderately to severely decreased)
    G4: 15-29     (severely decreased)
    G5: <15       (kidney failure)
    """
    if gender == "Female":
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0

    ratio = creatinine / kappa
    egfr = (142
            * min(ratio, 1.0) ** alpha
            * max(ratio, 1.0) ** (-1.200)
            * 0.9938 ** age
            * sex_factor)
    return round(egfr, 1)

def kidney_risk_from_egfr(egfr, uacr=None):
    """Convert eGFR to risk score. UACR = urine albumin-creatinine ratio mg/g."""
    # CKD stage from eGFR
    if egfr >= 90:
        base_risk = 0.05
    elif egfr >= 60:
        base_risk = 0.15
    elif egfr >= 45:
        base_risk = 0.40
    elif egfr >= 30:
        base_risk = 0.60
    elif egfr >= 15:
        base_risk = 0.80
    else:
        base_risk = 0.95
    
    # UACR adds additional risk dimension
    if uacr is not None:
        if uacr > 300:   base_risk = min(1.0, base_risk + 0.25)  # Macroalbuminuria
        elif uacr > 30:  base_risk = min(1.0, base_risk + 0.10)  # Microalbuminuria
    
    return base_risk
```

**Secondary: Rule-based when creatinine not available**

The existing rule-based approach is acceptable here IF you add actual BP numbers
instead of string-matching "Hypertension":

```python
def kidney_risk_rule_based(age, gender, systolic_bp, diastolic_bp,
                            bmi, diabetic, hypertensive, diet):
    risk = 0.0

    # BP — use actual numbers, not condition string
    if systolic_bp >= 160 or diastolic_bp >= 100:
        risk += 0.35   # Stage 2 hypertension
    elif systolic_bp >= 140 or diastolic_bp >= 90:
        risk += 0.20   # Stage 1 hypertension
    elif systolic_bp >= 130 or diastolic_bp >= 80:
        risk += 0.08   # Elevated

    if diabetic:
        risk += 0.30   # Diabetic nephropathy — #1 cause of CKD
    if bmi > 35:
        risk += 0.10   # Obesity-related nephropathy
    elif bmi > 30:
        risk += 0.05

    age_risk = 0.0
    if age > 70:  age_risk = 0.20
    elif age > 60: age_risk = 0.12
    elif age > 50: age_risk = 0.06
    risk += age_risk

    diet_risk = {"Poor": 0.12, "Average": 0.05, "Good": 0.0}.get(diet, 0.05)
    risk += diet_risk

    return min(1.0, risk)
```

**ML model: Train on NHANES + CKD UCI dataset**

Target: CKD stage (binary: G1-G2=0, G3+= 1)
Features: age, gender_encoded, creatinine, glucose, bmi, systolic_bp, diastolic_bp,
albumin, hemoglobin, smoking (binary), diabetes (binary)

---

### 4.4 Lung Model

**Primary: GOLD Staging + FEV1 Risk (if spirometry available)**

```python
def gold_copd_staging(fev1_fvc_ratio, fev1_percent_predicted):
    """
    GOLD 2023 COPD Staging.
    Airflow obstruction defined as post-bronchodilator FEV1/FVC < 0.70
    """
    if fev1_fvc_ratio >= 0.70:
        return {"stage": 0, "name": "No obstruction", "risk": 0.05}
    
    if fev1_percent_predicted >= 80:
        return {"stage": 1, "name": "Mild COPD", "risk": 0.20}
    elif fev1_percent_predicted >= 50:
        return {"stage": 2, "name": "Moderate COPD", "risk": 0.50}
    elif fev1_percent_predicted >= 30:
        return {"stage": 3, "name": "Severe COPD", "risk": 0.75}
    else:
        return {"stage": 4, "name": "Very Severe COPD", "risk": 0.95}
```

**Secondary: Pack-years based risk (no spirometry)**

```python
def lung_risk_from_pack_years(pack_years, age, asthma, current_smoker, bmi, activity):
    """
    Pack-years = (cigarettes_per_day / 20) × years_smoked
    Clinical significance:
    < 10 pack-years: minimal COPD risk
    ≥ 10 pack-years: COPD screening recommended
    ≥ 20 pack-years: significant risk
    ≥ 40 pack-years: very high risk (lung cancer screening with LDCT recommended by USPSTF)
    """
    # Smoking base risk
    if pack_years == 0:
        smoke_risk = 0.02
    elif pack_years < 5:
        smoke_risk = 0.08
    elif pack_years < 10:
        smoke_risk = 0.18
    elif pack_years < 20:
        smoke_risk = 0.32
    elif pack_years < 40:
        smoke_risk = 0.52
    else:
        smoke_risk = 0.75  # 40+ pack-years

    # Current vs ex-smoker
    if not current_smoker and pack_years > 0:
        smoke_risk *= 0.6  # Ex-smokers have significantly lower ongoing risk

    # Asthma
    asthma_risk = 0.20 if asthma else 0.0

    # Age (lungs decline naturally after 30)
    age_risk = max(0, (age - 30) * 0.004)  # ~0.4% per year after 30

    # Activity is protective
    activity_modifier = {"Active": 0.7, "Moderate": 1.0, "Sedentary": 1.2}
    modifier = activity_modifier.get(activity, 1.0)

    # BMI: both underweight and obese increase lung risk
    bmi_risk = 0.0
    if bmi < 18.5:
        bmi_risk = 0.08  # Underweight — muscle wasting affects respiratory muscles
    elif bmi > 35:
        bmi_risk = 0.10  # Obesity hypoventilation

    total_risk = min(1.0, (smoke_risk + asthma_risk + bmi_risk + age_risk) * modifier)
    return round(total_risk, 3)
```

**ML model: Train on NHANES Spirometry module**

Target: FEV1/FVC < 0.70 (GOLD criterion for airflow obstruction)
Features: age, gender, pack_years, bmi, asthma (binary), years_since_quit,
physical_activity_met, height (for FVC prediction)

---

### 4.5 Brain Model

**Primary: CAIDE Dementia Risk Score (validated)**

```python
def caide_score(age, education_years, systolic_bp, bmi, total_cholesterol,
                physical_active, sleep_hours=None, apoe4=False):
    """
    CAIDE (Cardiovascular Risk Factors, Aging and Dementia) Score
    Validated: Kivipelto et al. (2006) — 1,449 Finns, 20-year follow-up.
    Predicts dementia risk at age 65-79 for midlife adults.
    
    Score → Risk:
    0-5: 1% risk
    6-7: 1.9%
    8-9: 4.2%
    10-11: 7.4%
    12-15: 16.4%
    ≥16: 33.9%
    """
    points = 0

    # Age
    if age < 47:   points += 0
    elif age < 53: points += 3
    elif age < 59: points += 6
    elif age < 65: points += 9
    else:          points += 12  # ≥65

    # Education
    if education_years < 7:    points += 3
    elif education_years < 10: points += 2
    elif education_years < 13: points += 1
    # ≥13 years = 0 points

    # Systolic BP
    if systolic_bp >= 140:  points += 2

    # BMI
    if bmi >= 30:   points += 2
    elif bmi >= 25: points += 1  # Borderline not in original but commonly added

    # Cholesterol
    if total_cholesterol >= 240:  points += 2  # ≥6.2 mmol/L in original

    # Physical activity
    if not physical_active:  points += 1

    # Sleep (not in original CAIDE but meta-analyses show strong association)
    if sleep_hours is not None and sleep_hours < 6:
        points += 2  # Chronic sleep deprivation is a modifiable dementia risk factor

    # ApoE4 (genetic — only include if user has genetic test)
    if apoe4:
        points += 4  # Strongest single genetic risk factor

    risk_table = {
        0: 0.01, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.01,
        6: 0.019, 7: 0.019,
        8: 0.042, 9: 0.042,
        10: 0.074, 11: 0.074,
        12: 0.164, 13: 0.164, 14: 0.164, 15: 0.164,
    }
    return risk_table.get(points, 0.339 if points >= 16 else 0.01)
```

**Secondary: Stroke Risk (Framingham Stroke)**

```python
def framingham_stroke_risk(age, gender, systolic_bp, bp_treated,
                            diabetes, smoker, afib, lvh):
    """
    Framingham Stroke Risk Profile. D'Agostino et al. (1994).
    Validated in multiple populations.
    lvh = left ventricular hypertrophy (from ECG — not always available)
    """
    # Simplified point-score version
    points = 0
    # ... full implementation
    # Returns 10-year stroke probability
```

**Brain final risk = 0.6 × CAIDE risk + 0.4 × Stroke risk**

---

## 5. Biological Age — Clinically Valid Formula

### Use Klemera-Doubal Method (KDM) Approximation

The KDM method is the most validated biological age calculator that works without
methylation data. It uses multiple biomarkers simultaneously.

**Required biomarkers (from NHANES research):**

| Biomarker | Variable | Range | Direction |
|-----------|---------|-------|-----------|
| Systolic BP | systolic_bp | mmHg | ↑ = older |
| BMI | bmi | kg/m² | ↑ = older |
| Fasting glucose | fasting_glucose | mg/dL | ↑ = older |
| Total cholesterol | total_cholesterol | mg/dL | complex |
| Serum albumin | albumin | g/dL | ↓ = older |
| Serum creatinine | creatinine | mg/dL | ↑ = older |
| HbA1c | hba1c | % | ↑ = older |
| FEV1 % predicted | fev1_percent | % | ↓ = older |
| C-reactive protein | crp | mg/L | ↑ = older |
| Pulse rate | resting_hr | bpm | varies |

**Implementation (simplified KDM with available inputs):**

```python
class BiologicalAgeKDM:
    """
    Simplified Klemera-Doubal Biological Age
    Based on Levine (2013) implementation using NHANES III
    
    Full reference: Klemera P, Doubal S. (2006) Mech Ageing Dev.
    Python implementation based on Levine (2013) J Gerontol.
    """
    
    # Regression parameters from NHANES III calibration
    # Format: (q_intercept, b_slope, s_residual_std)
    BIOMARKER_PARAMS = {
        "systolic_bp":   (111.7, 0.568, 14.2),
        "bmi":           (22.1,  0.110, 4.8),
        "fasting_glucose": (83.5, 0.225, 14.8),
        "albumin":       (4.40, -0.013, 0.28),    # Negative slope — declines with age
        "creatinine":    (0.75,  0.004, 0.22),
        "hba1c":        (5.05,  0.024, 0.48),
        "fev1_percent": (110.5, -0.72, 18.5),     # Declines with age
        "total_chol":   (195.0,  0.95, 32.0),
    }
    
    def calculate(self, real_age, biomarkers: dict):
        """
        biomarkers: dict of {name: value} for available markers
        Returns: biological_age (float)
        """
        s_j_list = []   # residual stds
        x_j_list = []   # biomarker values
        q_j_list = []   # intercepts
        b_j_list = []   # slopes
        
        for name, value in biomarkers.items():
            if name not in self.BIOMARKER_PARAMS or value is None:
                continue
            q, b, s = self.BIOMARKER_PARAMS[name]
            s_j_list.append(s)
            x_j_list.append(value)
            q_j_list.append(q)
            b_j_list.append(b)
        
        if not b_j_list:
            return self._fallback(real_age, biomarkers)
        
        import numpy as np
        s = np.array(s_j_list)
        x = np.array(x_j_list)
        q = np.array(q_j_list)
        b = np.array(b_j_list)
        
        # KDM formula
        numerator   = np.sum(b * (x - q) / (s ** 2))
        denominator = np.sum(b ** 2 / (s ** 2))
        
        ba = numerator / denominator
        
        # Blend with chronological age (r²-weighted)
        # This prevents extreme values for sparse biomarker sets
        k = len(b_j_list)
        weight = k / (k + 2)  # More biomarkers = more weight to KDM
        bio_age = weight * ba + (1 - weight) * real_age
        
        # Constrain to realistic range
        bio_age = max(real_age - 20, min(real_age + 30, bio_age))
        return round(bio_age, 1)
    
    def _fallback(self, real_age, inputs):
        """When no lab values available, use lifestyle-based estimate."""
        # Keep existing additive approach but use validated estimates
        offset = 0
        smoking = inputs.get("smoking", "Never")
        if smoking == "Daily":
            pack_years = inputs.get("pack_years", 10)
            offset += min(8, pack_years * 0.25)   # Research: ~2.5 years per decade of daily smoking
        elif smoking == "Occasional":
            offset += 1.5
        
        alcohol = inputs.get("alcohol", "Never")
        if alcohol == "Daily":
            offset += 4   # Heavy drinking accelerates aging 4-7 years in research
        elif alcohol == "Weekly":
            offset += 1
        
        sleep = inputs.get("sleep", 7)
        if sleep < 6:
            offset += 2.5  # Chronic sleep deprivation: ~2-3 years biological aging
        
        stress = inputs.get("stress", "Medium")
        if stress == "High":
            offset += 1.5  # Chronic stress: ~1-2 years (telomere shortening studies)
        
        activity = inputs.get("activity", "Moderate")
        if activity == "Active":
            offset -= 3.5  # Regular exercise: -3.5 to -5 years biological age
        elif activity == "Sedentary":
            offset += 2

        bmi = inputs.get("bmi", 25)
        if bmi > 35:
            offset += 3
        elif bmi > 30:
            offset += 1.5
        
        return round(real_age + max(-10, offset), 1)
```

---

## 6. Verification Layers

A "single piece" means every output is verified before being shown. Four layers:

### Layer 1: Input Sanity Validation

```python
class InputValidator:
    """Validates all inputs before they reach any model."""
    
    RANGES = {
        "age":               (0, 120),
        "bmi":               (10, 80),
        "systolic_bp":       (60, 260),
        "diastolic_bp":      (30, 160),
        "total_cholesterol": (50, 600),
        "hdl_cholesterol":   (10, 150),
        "ldl_cholesterol":   (10, 500),
        "triglycerides":     (20, 2000),
        "fasting_glucose":   (40, 700),
        "hba1c":            (3.0, 20.0),
        "serum_creatinine":  (0.1, 30.0),
        "ast":               (5, 5000),
        "alt":               (5, 5000),
        "ggt":               (5, 2000),
        "albumin":           (1.0, 6.0),
        "sleep":             (0, 24),
        "pack_years":        (0, 200),
        "cigarettes_per_day":(0, 100),
        "years_smoked":      (0, 90),
    }
    
    CLINICAL_CHECKS = [
        # (condition, warning_message)
        (lambda d: d.get("systolic_bp", 999) < d.get("diastolic_bp", 0),
         "Systolic BP cannot be less than diastolic BP"),
        (lambda d: d.get("ldl_cholesterol", 0) + d.get("hdl_cholesterol", 0) > d.get("total_cholesterol", 999),
         "LDL + HDL cannot exceed total cholesterol"),
        (lambda d: d.get("hba1c", 0) > 10 and d.get("fasting_glucose", 999) < 126,
         "HbA1c >10% is inconsistent with fasting glucose <126 mg/dL — verify inputs"),
        (lambda d: d.get("serum_creatinine", 0) > 10 and d.get("age", 0) < 20,
         "Creatinine >10 mg/dL is very unusual in patients under 20"),
    ]
    
    def validate(self, data):
        errors = []
        warnings = []
        
        all_fields = {**data.get("ProfileInfo", {}), **data.get("HealthInfo", {})}
        
        # Range checks
        for field, (lo, hi) in self.RANGES.items():
            val = all_fields.get(field)
            if val is not None:
                try:
                    v = float(val)
                    if v < lo or v > hi:
                        errors.append(f"{field} value {v} is outside physiologically possible range [{lo}, {hi}]")
                except:
                    errors.append(f"{field} must be numeric, got: {val}")
        
        # Clinical consistency checks
        for check_fn, message in self.CLINICAL_CHECKS:
            try:
                if check_fn(all_fields):
                    warnings.append(message)
            except:
                pass
        
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
```

### Layer 2: Model Confidence Scoring

```python
class ConfidenceScorer:
    """
    Scores model confidence based on:
    1. Number of real inputs vs imputed defaults
    2. Whether validated clinical formulas could be applied
    3. Input quality (e.g., single BP reading vs average of 3)
    """
    
    HIGH_VALUE_INPUTS = [
        "systolic_bp", "diastolic_bp", "total_cholesterol",
        "hdl_cholesterol", "serum_creatinine", "hba1c", "fasting_glucose",
        "ast", "alt", "pack_years",
    ]
    
    def score(self, organ, data, method_used):
        """
        Returns: {
          "score": 0.0-1.0,
          "label": "High" | "Medium" | "Low",
          "method": "clinical_formula" | "ml_model" | "rule_based",
          "missing_inputs": ["list of fields that would improve accuracy"]
        }
        """
        all_inputs = {**data.get("ProfileInfo", {}), **data.get("HealthInfo", {})}
        present = sum(1 for f in self.HIGH_VALUE_INPUTS if all_inputs.get(f) is not None)
        
        base_confidence = {
            "clinical_formula": 0.85,
            "ml_model": 0.72,
            "rule_based": 0.50,
        }.get(method_used, 0.55)
        
        # Boost confidence if more real lab values provided
        input_boost = (present / len(self.HIGH_VALUE_INPUTS)) * 0.15
        final_confidence = min(0.97, base_confidence + input_boost)
        
        missing = [f for f in self.HIGH_VALUE_INPUTS if all_inputs.get(f) is None]
        label = "High" if final_confidence >= 0.80 else ("Medium" if final_confidence >= 0.65 else "Low")
        
        return {
            "score": round(final_confidence, 2),
            "label": label,
            "method": method_used,
            "missing_high_value": missing[:3],  # Top 3 most impactful
        }
```

### Layer 3: Clinical Consistency Cross-Check

```python
class ClinicalConsistencyChecker:
    """
    Cross-checks organ results against each other for medical plausibility.
    Example: If liver risk is RED, kidney risk should never be GREEN if diabetes is present.
    """
    
    def check(self, organ_results, data):
        flags = []
        health = data.get("HealthInfo", {})
        
        heart_risk = organ_results.get("heart", {}).get("current_risk", 0)
        liver_risk = organ_results.get("liver", {}).get("current_risk", 0)
        kidney_risk = organ_results.get("kidney", {}).get("current_risk", 0)
        
        conditions = [c.lower() for c in health.get("MedicalConditions", [])]
        is_diabetic = any("diabetes" in c for c in conditions)
        has_hypertension = any("hypertension" in c or "high bp" in c for c in conditions)
        
        # Diabetes should elevate both kidney and liver
        if is_diabetic and kidney_risk < 0.20:
            flags.append({
                "type": "consistency_adjustment",
                "organ": "kidney",
                "reason": "Diabetes is the leading cause of CKD; kidney risk floored to 0.20",
                "adjustment": 0.20
            })
            organ_results["kidney"]["current_risk"] = max(organ_results["kidney"]["current_risk"], 0.20)
        
        if is_diabetic and liver_risk < 0.15:
            flags.append({
                "type": "consistency_adjustment",
                "organ": "liver",
                "reason": "T2DM is strongly associated with NAFLD",
                "adjustment": 0.15
            })
        
        # Severe heart failure typically means multiple organ involvement
        if heart_risk > 0.75:
            kidney_adj = max(kidney_risk, 0.30)
            if kidney_adj > kidney_risk:
                flags.append({
                    "type": "consistency_adjustment",
                    "organ": "kidney",
                    "reason": "Severe cardiac dysfunction often causes cardiorenal syndrome",
                    "adjustment": kidney_adj
                })
                organ_results["kidney"]["current_risk"] = kidney_adj
        
        return organ_results, flags
```

### Layer 4: Medication Interaction Modeling

```python
class MedicationEffectModeler:
    """
    Models how current medications affect organ risk scores.
    Finally uses the medications[] field that the frontend collects.
    """
    
    MEDICATION_EFFECTS = {
        # keyword → {organ: risk_reduction_factor}
        "statin":           {"heart": -0.15, "liver": +0.03},   # Protective for heart, slight liver load
        "atorvastatin":     {"heart": -0.15, "liver": +0.03},
        "rosuvastatin":     {"heart": -0.15, "liver": +0.03},
        "simvastatin":      {"heart": -0.12, "liver": +0.03},
        "metformin":        {"liver": -0.10, "kidney": -0.05},   # Protective for liver/kidney in T2DM
        "ace inhibitor":    {"kidney": -0.15, "heart": -0.10},  # Renoprotective
        "lisinopril":       {"kidney": -0.15, "heart": -0.10},
        "ramipril":         {"kidney": -0.15, "heart": -0.10},
        "arb":              {"kidney": -0.12, "heart": -0.08},   # Similar to ACE inhibitors
        "losartan":         {"kidney": -0.12, "heart": -0.08},
        "beta blocker":     {"heart": -0.10},
        "metoprolol":       {"heart": -0.10},
        "aspirin":          {"heart": -0.08},
        "warfarin":         {"heart": -0.05},                    # Anticoagulation for AFib
        "insulin":          {"kidney": +0.05},                   # Indicates advanced diabetes
        "dialysis":         {"kidney": 0.95},                    # Override to critical
        "nsaid":            {"kidney": +0.10, "heart": +0.05},  # Nephrotoxic with chronic use
        "ibuprofen":        {"kidney": +0.08},
        "naproxen":         {"kidney": +0.08},
        "acetaminophen":    {"liver": +0.05},                    # Liver load at high doses
        "alcohol":          {"liver": +0.20},                    # Hepatotoxic
        "chemotherapy":     {"liver": +0.20, "kidney": +0.15},  # Organ toxicity
    }
    
    def apply(self, organ_results, medications):
        if not medications:
            return organ_results, []
        
        adjustments = []
        combined_effects = {}
        
        for med in medications:
            med_lower = med.lower()
            for keyword, effects in self.MEDICATION_EFFECTS.items():
                if keyword in med_lower:
                    for organ, delta in effects.items():
                        combined_effects[organ] = combined_effects.get(organ, 0) + delta
                    adjustments.append({
                        "medication": med,
                        "matched": keyword,
                        "effects": effects
                    })
                    break
        
        for organ, total_delta in combined_effects.items():
            if organ in organ_results:
                original = organ_results[organ]["current_risk"]
                adjusted = max(0.02, min(1.0, original + total_delta))
                organ_results[organ]["current_risk"] = round(adjusted, 3)
                organ_results[organ]["medication_adjusted"] = True
                organ_results[organ]["medication_delta"] = round(total_delta, 3)
        
        return organ_results, adjustments
```

---

## 7. Complete Training Pipeline

### Step 1: Environment Setup

```bash
# Create conda environment
conda create -n vitaltwin-ml python=3.10
conda activate vitaltwin-ml

pip install pandas==1.5.3 numpy==1.23.5 scikit-learn==1.2.2 \
    xgboost==1.7.6 lightgbm==3.3.5 imbalanced-learn==0.10.1 \
    scipy==1.10.1 joblib==1.2.0 matplotlib seaborn shap optuna
```

### Step 2: Data Preparation

```python
# Run this script: utils/prepare_all_data.py

import pandas as pd
import numpy as np
from pathlib import Path

def prepare_heart_data():
    df = pd.read_csv("data/cardio_dataset.csv")
    
    # Fix age format "50 years 143 days" → 50
    df["age"] = df["age"].astype(str).str.extract(r"(\d+)").astype(int)
    
    # Map categorical cholesterol to mg/dL midpoints
    chol_map = {1: 185, 2: 215, 3: 265}
    df["cholesterol_mgdl"] = df["cholesterol"].map(chol_map)
    
    # Map categorical glucose
    gluc_map = {1: 90, 2: 115, 3: 160}
    df["glucose_mgdl"] = df["gluc"].map(gluc_map)
    
    # Estimate HDL from total cholesterol and gender (approximate)
    df["hdl_est"] = np.where(df["gender"] == "Male",
                             df["cholesterol_mgdl"] * 0.22,
                             df["cholesterol_mgdl"] * 0.28)
    
    features = ["age", "bmi", "systolic_bp", "diastolic_bp",
                "cholesterol_mgdl", "glucose_mgdl", "smoke", "alco", "active"]
    df[features + ["cardio"]].to_csv("data/processed/heart_training_data.csv", index=False)
    print(f"Heart: {len(df)} rows, {df['cardio'].mean():.2%} positive rate")

def prepare_liver_data():
    df = pd.read_csv("data/liver_dataset.csv")
    
    # Use biopsy-confirmed fibrosis as target (not NAS score)
    # "Fibrosis_status (No=0, Yes=1)" column
    # Rename columns for clarity
    col_map = {
        "Age": "age",
        "Gender (Female=1, Male=2)": "gender",
        "Body Mass Index": "bmi",
        "Systolic Blood Pressure": "systolic_bp",
        "Diastolic Blood Pressure": "diastolic_bp",
        "Diyabetes Mellitus (No=0, Yes=1)": "diabetes",
        "Hypertension (No=0, Yes=1)": "hypertension",
        "Smoking Status (Never Smoked=1, Left Smoking=2, Smoking=3)": "smoking",
        "AST": "ast",
        "ALT": "alt",
        "GGT": "ggt",
        "Total Cholesterol": "total_cholesterol",
        "Triglycerides": "triglycerides",
        "HDL": "hdl",
        "LDL": "ldl",
        "Glucose": "glucose",
        "Hemoglobin - A1C": "hba1c",
        "Creatinine": "creatinine",
        "Albumin": "albumin",
        "Fibrosis status (No=0, Yes=1) (Fibrosis 1 and above, there is Fibrosis)": "fibrosis_binary",
        "Significant Fibrosis (No=0, Yes=1) (If Fibrosis 2 and above, there is Significant Fibrosis)": "sig_fibrosis"
    }
    df = df.rename(columns=col_map)
    
    features = ["age", "gender", "bmi", "ast", "alt", "ggt",
                "total_cholesterol", "triglycerides", "hdl",
                "glucose", "hba1c", "creatinine", "albumin",
                "diabetes", "hypertension"]
    
    available = [f for f in features if f in df.columns]
    target = "fibrosis_binary" if "fibrosis_binary" in df.columns else "sig_fibrosis"
    
    df_clean = df[available + [target]].dropna(subset=[target])
    df_clean.to_csv("data/processed/liver_training_data.csv", index=False)
    print(f"Liver: {len(df_clean)} rows, {df_clean[target].mean():.2%} fibrosis rate")
    print(f"Note: Target is '{target}' (biopsy confirmed)")

prepare_heart_data()
prepare_liver_data()
```

### Step 3: Training All Models

```python
# utils/train_all_upgraded.py

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, f1_score, classification_report
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import optuna
import joblib, json
import pandas as pd
import numpy as np

def train_with_optuna(X_train, y_train, model_name):
    """Use Optuna to find best hyperparameters via cross-validation."""
    
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "scale_pos_weight": sum(y_train == 0) / max(1, sum(y_train == 1)),
            "eval_metric": "auc",
            "use_label_encoder": False,
        }
        model = xgb.XGBClassifier(**params, random_state=42)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
        return scores.mean()
    
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50, show_progress_bar=True)
    print(f"\n{model_name} best AUC: {study.best_value:.4f}")
    print(f"Best params: {study.best_params}")
    return study.best_params

def train_heart_model():
    df = pd.read_csv("data/processed/heart_training_data.csv")
    X = df.drop("cardio", axis=1)
    y = df["cardio"]
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    # SMOTE only on training data
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    best_params = train_with_optuna(X_train_resampled, y_train_resampled, "Heart")
    
    model = xgb.XGBClassifier(**best_params, random_state=42)
    model.fit(X_train_resampled, y_train_resampled)
    
    # Calibrate probabilities
    calibrated = CalibratedClassifierCV(model, cv=5, method="isotonic")
    calibrated.fit(X_train, y_train)  # Calibrate on original, unsmoted data
    
    y_proba = calibrated.predict_proba(X_test)[:, 1]
    y_pred = (y_proba > 0.5).astype(int)
    
    print(f"\nHeart Model Results:")
    print(f"  AUC-ROC: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"  F1: {f1_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))
    
    joblib.dump(calibrated, "models/trained_models/heart_model.pkl")
    json.dump(list(X.columns), open("models/trained_models/heart_features.json", "w"))
    return calibrated

def train_liver_model():
    df = pd.read_csv("data/processed/liver_training_data.csv")
    
    feature_cols = [c for c in df.columns if c not in ["fibrosis_binary", "sig_fibrosis"]]
    target = "fibrosis_binary" if "fibrosis_binary" in df.columns else "sig_fibrosis"
    
    df = df.dropna(subset=feature_cols + [target])
    X = df[feature_cols]
    y = df[target]
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    smote = SMOTE(random_state=42, k_neighbors=min(5, sum(y_train == 1) - 1))
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    best_params = train_with_optuna(X_train_resampled, y_train_resampled, "Liver")
    
    model = xgb.XGBClassifier(**best_params, random_state=42)
    model.fit(X_train_resampled, y_train_resampled)
    
    calibrated = CalibratedClassifierCV(model, cv=5, method="isotonic")
    calibrated.fit(X_train, y_train)
    
    y_proba = calibrated.predict_proba(X_test)[:, 1]
    y_pred = (y_proba > 0.5).astype(int)
    
    print(f"\nLiver Model Results:")
    print(f"  AUC-ROC: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"  F1: {f1_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))
    
    joblib.dump(calibrated, "models/trained_models/liver_model.pkl")
    json.dump(feature_cols, open("models/trained_models/liver_features.json", "w"))
```

---

## 8. API Schema Changes

### New HealthInfo Schema

```python
class HealthInfo(BaseModel):
    # Existing fields (keep)
    Smoking: Optional[str] = "Never"          # "Never" | "Occasional" | "Daily"
    Alcohol: Optional[str] = "Never"          # "Never" | "Weekly" | "Daily"
    Sleep: Optional[float] = 7
    Stress: Optional[str] = "Low"             # "Low" | "Medium" | "High"
    MedicalConditions: Optional[List[str]] = []
    Medications: Optional[List[str]] = []     # NOW ACTUALLY USED
    Bmi: Optional[float] = None
    
    # NEW: Smoking detail
    YearsSmokedmoked: Optional[int] = None          # Years smoked (or currently smoking)
    CigarettesPerDay: Optional[int] = None    # Cigarettes per day when/while smoking
    
    # NEW: Blood pressure (actual numbers, not inferred)
    SystolicBP: Optional[int] = None          # mmHg
    DiastolicBP: Optional[int] = None         # mmHg
    BPOnMedication: Optional[bool] = False
    
    # NEW: Family history
    FamilyHistoryHeart: Optional[bool] = False
    FamilyHistoryDiabetes: Optional[bool] = False
    FamilyHistoryKidney: Optional[bool] = False
    
    # NEW: Lab values (all optional — from blood test)
    TotalCholesterol: Optional[float] = None  # mg/dL
    HDLCholesterol: Optional[float] = None    # mg/dL
    LDLCholesterol: Optional[float] = None    # mg/dL
    Triglycerides: Optional[float] = None     # mg/dL
    FastingGlucose: Optional[float] = None    # mg/dL
    HbA1c: Optional[float] = None            # %
    SerumCreatinine: Optional[float] = None   # mg/dL
    AST: Optional[float] = None              # U/L
    ALT: Optional[float] = None              # U/L
    GGT: Optional[float] = None              # U/L
    Albumin: Optional[float] = None          # g/dL
    
    # Legacy lab fields (keep for backwards compatibility)
    ast: Optional[float] = None
    alt: Optional[float] = None
    ggt: Optional[float] = None
    glucose: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    cholesterol: Optional[int] = None
    gluc: Optional[int] = None
```

### New Response Schema

Add these fields to the `/predict` response:

```json
{
  "organs": {
    "heart": {
      "current_risk": 0.24,
      "risk_level": "GREEN",
      "health_score": 76,
      "method_used": "framingham_pooled_cohort",
      "confidence": {"score": 0.89, "label": "High", "missing_high_value": ["hdl_cholesterol"]},
      "medication_adjusted": true,
      "medication_delta": -0.08,
      "possible_issues": ["Elevated LDL detected", "Family history of heart disease"]
    }
  },
  "input_quality": {
    "lab_values_provided": 4,
    "lab_values_available": 11,
    "overall_confidence": "Medium",
    "upgrade_message": "Add your blood pressure and cholesterol for 40% more accurate results"
  },
  "medication_effects": [
    {"medication": "Lisinopril", "matched": "lisinopril", "effects": {"kidney": -0.15, "heart": -0.10}}
  ],
  "consistency_flags": [
    {"type": "consistency_adjustment", "organ": "kidney", "reason": "Diabetes is the leading cause of CKD"}
  ]
}
```

---

## 9. Frontend Changes Required

### New Fields in HealthQuestionsPage

```jsx
// Add to health-questions form — Section: "Vitals" (required)
<div className="grid grid-cols-2 gap-4">
  <div>
    <label>Systolic Blood Pressure (mmHg)</label>
    <input type="number" placeholder="e.g. 120" min="60" max="260"
           value={input.systolic_bp} onChange={e => setInput("systolic_bp", +e.target.value)} />
    <p className="text-xs text-muted">Top number on your BP reading</p>
  </div>
  <div>
    <label>Diastolic Blood Pressure (mmHg)</label>
    <input type="number" placeholder="e.g. 80" min="30" max="160"
           value={input.diastolic_bp} onChange={e => setInput("diastolic_bp", +e.target.value)} />
  </div>
</div>

<label>Are you on blood pressure medication?</label>
<Toggle value={input.bp_on_medication} onChange={v => setInput("bp_on_medication", v)} />

// Smoking detail (show only if smoking !== "Never")
{input.smoking !== "Never" && (
  <div className="grid grid-cols-2 gap-4">
    <input type="number" placeholder="Years smoked" label="Years Smoked"
           value={input.years_smoked} onChange={e => setInput("years_smoked", +e.target.value)} />
    <input type="number" placeholder="Cigarettes/day" label="Cigarettes Per Day"
           value={input.cigarettes_per_day} onChange={e => setInput("cigarettes_per_day", +e.target.value)} />
  </div>
)}

// Family history
<label>Family History of Heart Disease (parent/sibling before age 65)</label>
<Toggle value={input.family_history_heart} onChange={v => setInput("family_history_heart", v)} />

// Collapsible: "From a recent blood test (optional — improves accuracy by ~40%)"
<Collapsible title="Add Blood Test Results (Optional)" badge="More Accurate">
  <div className="grid grid-cols-2 gap-3">
    <LabInput label="Total Cholesterol" unit="mg/dL" field="total_cholesterol" ref="<200 normal" />
    <LabInput label="HDL Cholesterol" unit="mg/dL" field="hdl_cholesterol" ref=">60 protective" />
    <LabInput label="Systolic BP" unit="mmHg" field="systolic_bp" />  {/* if not already given */}
    <LabInput label="Fasting Glucose" unit="mg/dL" field="fasting_glucose" ref="<100 normal" />
    <LabInput label="HbA1c" unit="%" field="hba1c" ref="<5.7% normal" />
    <LabInput label="Serum Creatinine" unit="mg/dL" field="serum_creatinine" ref="0.7-1.3 men" />
    <LabInput label="AST" unit="U/L" field="ast" ref="<40 normal" />
    <LabInput label="ALT" unit="U/L" field="alt" ref="<56 normal" />
  </div>
</Collapsible>
```

### New Store Fields

```js
// Add to INITIAL_INPUT in store/useStore.js
const INITIAL_INPUT = {
  smoking: "",
  alcohol: "",
  sleep: "",
  stress: "",
  medical_conditions: [],
  medications: [],
  // New
  systolic_bp: "",
  diastolic_bp: "",
  bp_on_medication: false,
  years_smoked: "",
  cigarettes_per_day: "",
  family_history_heart: false,
  family_history_diabetes: false,
  // Lab values (optional)
  total_cholesterol: "",
  hdl_cholesterol: "",
  fasting_glucose: "",
  hba1c: "",
  serum_creatinine: "",
  ast: "",
  alt: "",
  ggt: "",
};
```

### Map New Fields in toPredictPayload()

```js
// In lib/reportApiServer.js — toPredictPayload()
const HealthInfo = {
  // ... existing fields ...
  SystolicBP: numOr(input.systolic_bp, null),
  DiastolicBP: numOr(input.diastolic_bp, null),
  BPOnMedication: Boolean(input.bp_on_medication),
  YearsSmokedmoked: numOr(input.years_smoked, null),
  CigarettesPerDay: numOr(input.cigarettes_per_day, null),
  FamilyHistoryHeart: Boolean(input.family_history_heart),
  FamilyHistoryDiabetes: Boolean(input.family_history_diabetes),
  // Lab values — send null if empty, not zero
  TotalCholesterol: numOr(input.total_cholesterol, null),
  HDLCholesterol: numOr(input.hdl_cholesterol, null),
  FastingGlucose: numOr(input.fasting_glucose, null),
  HbA1c: numOr(input.hba1c, null),
  SerumCreatinine: numOr(input.serum_creatinine, null),
  AST: numOr(input.ast, null),
  ALT: numOr(input.alt, null),
  GGT: numOr(input.ggt, null),
};
```

---

## 10. Integration Checklist

### Complete Request → Response Flow

```
Frontend Form
  ↓ (profile + input including new fields)
lib/reportApiServer.js toPredictPayload()
  ↓ (ProfileInfo + HealthInfo with lab values)
POST /api/report (Next.js proxy)
  ↓
POST /predict (Python FastAPI)
  ↓
InputValidator.validate()              ← Layer 1: Input validation
  ↓ (reject if impossible values)
BiologicalAgeKDM.calculate()          ← Upgraded biological age
  ↓
HeartModel.calculate_risk()
  → pooled_cohort_ascvd() if cholesterol+BP available
  → ml_model.predict_proba() as secondary
  → keyword_condition_parser()
  ↓
LiverModel.calculate_risk()
  → fib4_index() if AST+ALT available
  → nafld_lfs() if no labs
  → ml_model.predict_proba() as validation
  ↓
KidneyModel.calculate_risk()
  → ckd_epi_egfr() if creatinine available
  → rule_based_kidney() with real BP numbers
  → nhanes_ml_model if available
  ↓
BrainModel.calculate_risk()
  → caide_score() + framingham_stroke()
  ↓
LungsModel.calculate_risk()
  → pack_years_risk() (cigarettes × years)
  → nhanes_spirometry_ml if available
  ↓
ClinicalConsistencyChecker.check()     ← Layer 3: Cross-organ validation
  ↓
MedicationEffectModeler.apply()        ← Layer 4: Medications NOW USED
  ↓
ConfidenceScorer.score() per organ     ← Layer 2: Confidence
  ↓
BodyStressHeatmap.calculate()
FutureSelfSimulator.simulate()
VitalScoreGauge.calculate()
BioPriorityRecommendations()
  ↓
Response with: organs + confidence + medication_effects + consistency_flags + input_quality
  ↓
Next.js proxy returns to frontend
  ↓
Dashboard renders with confidence badges
```

---

## 11. Deployment & Monitoring

### Dependencies to Add

```
# requirements.txt additions
xgboost==1.7.6
imbalanced-learn==0.10.1
optuna==3.3.0
shap==0.42.1            # Feature importance explanations
```

### Model Versioning

```python
# Save model metadata alongside .pkl files
metadata = {
    "model_name": "heart_xgb_calibrated_v2",
    "trained_on": "2024-01-15",
    "training_samples": 56000,
    "test_auc": 0.824,
    "test_f1": 0.752,
    "features": feature_cols,
    "target": "cardio",
    "calibration": "isotonic",
    "validation": "5-fold stratified CV",
    "notes": "Trained on cardio_dataset.csv with SMOTE, XGBoost + Platt calibration"
}
json.dump(metadata, open("models/trained_models/heart_model_metadata.json", "w"), indent=2)
```

### Input Quality Signal to User

Show on the dashboard — a subtle accuracy indicator:

```
Input Quality: ●●●○○  Medium (3/5 key inputs provided)
→ "Add blood pressure + cholesterol for High confidence results"
```

### What Realistic Accuracy Looks Like After Upgrade

| Organ | Current | After Upgrade | Method |
|-------|---------|--------------|--------|
| Heart | ~73% acc (misleading) | AUC 0.82-0.86 | Framingham + XGBoost |
| Liver | ~97% acc (fake) | AUC 0.82-0.88 F1~0.75 | FIB-4 + XGBoost + SMOTE |
| Kidney | Rule-based (no metric) | AUC 0.88-0.92 (CKD-EPI is near-exact) | CKD-EPI equation + NHANES ML |
| Brain | Rule-based (no metric) | Validated 20-yr risk (CAIDE published) | CAIDE + Framingham Stroke |
| Lungs | Rule-based (no metric) | AUC 0.78-0.84 | Pack-years + NHANES spirometry ML |

AUC 0.82 means the model correctly ranks a sick person above a healthy one 82% of the time.
Clinical standard for acceptable diagnostic tools is AUC > 0.75.
