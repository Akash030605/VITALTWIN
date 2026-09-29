# Exact Datasets Needed to Fix All Gaps
*Download these from Kaggle and place in the specified folders*

---

## GAP 1 — KIDNEY (🔴 HIGHEST PRIORITY)
**Problem:** No Indian kidney data. Falls back to rule-based (confidence 0.55) without creatinine.

### Download this:
**Kaggle Dataset:** `mansoordaku/ckdisease`
**URL:** https://www.kaggle.com/datasets/mansoordaku/ckdisease
**File name:** `kidney_disease.csv`
**Size:** ~27KB, 400 rows
**What it is:** 400 patients from Apollo Hospital, Tamil Nadu, India — chronic kidney disease dataset
**Columns:** age, bp, sg, al, su, rbc, pc, pcc, ba, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm, cad, appet, pe, ane, classification
**Place at:** `model/data/india/kidney/apollo_ckd_india.csv`

---

## GAP 2 — HEART (🟡 Replace Russian ML with Indian data)
**Problem:** Heart ML trained on Russian Kaggle data (cardio_train.csv). Formula (PCE) is fine but secondary ML is not Indian.

### Download these 2 datasets:

**Dataset A:** `johnsmith88/heart-disease-dataset`
**URL:** https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset
**File name:** `heart.csv`
**Size:** ~11KB, 303 rows — Cleveland Heart Disease (UCI)
**Place at:** `model/data/india/heart/cleveland_heart.csv`

**Dataset B:** `fedesoriano/heart-failure-prediction`
**URL:** https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction
**File name:** `heart.csv`
**Size:** ~40KB, 918 rows — combined 5 heart disease datasets
**Place at:** `model/data/india/heart/heart_failure_918.csv`

> NOTE: These are not India-specific, but they have better clinical features than the Russian dataset.
> If you can find: `rishidamarla/heart-disease-prediction-dataset` (Indian patients) even better.

---

## GAP 3 — BRAIN (🟡 Better dementia/Alzheimer India data)
**Problem:** CAIDE validated on Finns. No Indian dementia dataset.

### Download this:
**Kaggle Dataset:** `rabieelkharoua/alzheimers-disease-dataset`
**URL:** https://www.kaggle.com/datasets/rabieelkharoua/alzheimers-disease-dataset
**File name:** `alzheimers_disease_data.csv`
**Size:** ~2MB, 2,149 rows
**Columns:** Age, Gender, Ethnicity, BMI, Smoking, PhysicalActivity, DietQuality, SleepQuality, FamilyHistoryAlzheimers, CardiovascularDisease, Diabetes, Depression, Diagnosis (0/1)
**Place at:** `model/data/brain/alzheimers_2149.csv`

---

## GAP 4 — DIABETES (needed by multiple organs)
**Problem:** Diabetes is a key input for heart, brain, kidney, liver but no Indian diabetes dataset is integrated.

### Download this:
**Kaggle Dataset:** `vikasukani/diabetes-disease-dataset`  (Indian patients)
**URL:** https://www.kaggle.com/datasets/vikasukani/diabetes-disease-dataset
**File name:** `diabetes.csv`
**Size:** ~23KB, 768 rows — PIMA Indians (South Asian women)
**Place at:** `model/data/india/diabetes/pima_indians_768.csv`

**ALSO download:** `iammustafatz/diabetes-prediction-dataset`
**URL:** https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset
**File name:** `diabetes_prediction_dataset.csv`
**Size:** ~1.5MB, 100,000 rows — includes HbA1c, blood glucose, BMI
**Place at:** `model/data/india/diabetes/diabetes_100k.csv`

---

## GAP 5 — LIVER (🟡 Reduce Turkish model weight)
**Problem:** Turkish biopsy model gets 60% weight. Need more Indian liver data.

### Download this:
**Kaggle Dataset:** Already have ILPD (583 Indian patients). But also:
**Kaggle Dataset:** `abhi8923shriv/liver-disease-patient-dataset`
**URL:** https://www.kaggle.com/datasets/abhi8923shriv/liver-disease-patient-dataset
**File name:** `Indian Liver Patient Dataset (ILPD).csv`  
**Size:** ~24KB, 583 rows — same ILPD dataset (confirm you have it)
**Check:** Already at `model/data/india/liver/Indian Liver Patient Dataset (ILPD).csv` ✅

**Additional:** `aaronhd/liverdisease`
**URL:** https://www.kaggle.com/datasets/aaronhd/liverdisease
**File name:** `liver.csv`
**Size:** ~8KB — BUPA liver disorders
**Place at:** `model/data/liver/bupa_liver.csv`

---

## GAP 6 — BIOLOGICAL AGE (🟡 Better calibration data)
**Problem:** NHANES-calibrated. Need better reference ranges.

### Download this:
**Kaggle Dataset:** `cdc/national-health-and-nutrition-examination-survey`
**URL:** https://www.kaggle.com/datasets/cdc/national-health-and-nutrition-examination-survey
**File name:** various `.XPT` files
**Size:** ~500MB total (large — only if you have bandwidth)
**Place at:** `model/data/nhanes/`

**Simpler alternative:** `mihirdave/nhanes-2013-14-demographics-and-lab-data`
**URL:** https://www.kaggle.com/datasets/mihirdave/nhanes-2013-14-demographics-and-lab-data
**Size:** ~5MB
**Place at:** `model/data/nhanes/nhanes_2013_14.csv`

---

## SUMMARY — What to Download (Priority Order)

| Priority | Dataset | Kaggle URL | Save as |
|----------|---------|-----------|---------|
| 🔴 1 | Apollo CKD (400 Indian pts) | `mansoordaku/ckdisease` | `data/india/kidney/apollo_ckd_india.csv` |
| 🟡 2 | Alzheimer's (2149 pts) | `rabieelkharoua/alzheimers-disease-dataset` | `data/brain/alzheimers_2149.csv` |
| 🟡 3 | Diabetes 100K (HbA1c) | `iammustafatz/diabetes-prediction-dataset` | `data/india/diabetes/diabetes_100k.csv` |
| 🟡 4 | Heart failure 918 rows | `fedesoriano/heart-failure-prediction` | `data/india/heart/heart_failure_918.csv` |
| 🟢 5 | NHANES 2013-14 | `mihirdave/nhanes-2013-14-demographics-and-lab-data` | `data/nhanes/nhanes_2013_14.csv` |

---

## How to Download from Kaggle

**Option A — Kaggle website:**
1. Go to the URL
2. Click "Download" button
3. Unzip and place the CSV in the folder shown above

**Option B — Kaggle CLI (if installed):**
```bash
pip install kaggle
# Set up API key from kaggle.com/settings
kaggle datasets download mansoordaku/ckdisease -p model/data/india/kidney/ --unzip
kaggle datasets download rabieelkharoua/alzheimers-disease-dataset -p model/data/brain/ --unzip
kaggle datasets download iammustafatz/diabetes-prediction-dataset -p model/data/india/diabetes/ --unzip
kaggle datasets download fedesoriano/heart-failure-prediction -p model/data/india/heart/ --unzip
```

---

## What I'll do once you provide them:
1. **Apollo CKD** → Train a CKD ML model, wire into kidney_model.py (confidence 0.55 → 0.85)
2. **Alzheimer's** → Use to calibrate CAIDE output for non-Finnish populations
3. **Diabetes 100K** → Extract HbA1c/glucose reference ranges, improve diabetes detection across all organs
4. **Heart failure 918** → Retrain heart secondary ML on better clinical data
5. **NHANES** → Recalibrate bio age KDM parameters more accurately
