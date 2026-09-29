# train_all_gaps.py
# Trains ML models for all 4 gaps identified in TRUST_AUDIT.md:
#   1. Kidney  — Apollo CKD India (400 rows) → models/kidney_ml.pkl
#   2. Brain   — Alzheimer's dataset (2149 rows) → models/alzheimer_ml.pkl
#   3. Heart   — Cleveland/UCI heart disease (1025 rows) → models/heart_ml_v2.pkl
#   4. Diabetes — 100K dataset → models/diabetes_ml.pkl (used by all organs)
#
# Run: python train_all_gaps.py

import pickle, warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

warnings.filterwarnings('ignore')

BASE  = Path(__file__).parent
DATA  = BASE / "data"
MDIR  = BASE / "models"
MDIR.mkdir(exist_ok=True)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ══════════════════════════════════════════════════════════════════════════════
# 1. KIDNEY — Apollo CKD India (400 patients, Tamil Nadu)
#    Source: UCI ML Repository via Kaggle mansoordaku/ckdisease
#    Paper:  Soundarapandian P et al., UCI Repository 2015
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("1. KIDNEY — Apollo CKD India (400 rows)")
print("="*70)

df_ckd = pd.read_csv(DATA / "india/kidney/kidney_disease.csv")
print(f"   Loaded: {len(df_ckd)} rows × {len(df_ckd.columns)} cols")

# Clean target: 'ckd' and 'ckd\t' → 1, 'notckd' → 0
df_ckd['target'] = df_ckd['classification'].str.strip().map({'ckd': 1, 'notckd': 0})
df_ckd = df_ckd.dropna(subset=['target'])

# Features: clinical kidney markers
# sc=serum creatinine, bgr=blood glucose, bu=blood urea, sod=sodium,
# pot=potassium, hemo=haemoglobin, pcv=PCV, wc=WBC, rc=RBC,
# age, bp=blood pressure, sg=specific gravity, al=albumin, su=sugar
kidney_features = ['age', 'bp', 'sg', 'al', 'su', 'bgr', 'bu', 'sc',
                   'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc']

# Convert to numeric (some cols have '\t' whitespace issues)
for c in kidney_features + ['target']:
    df_ckd[c] = pd.to_numeric(df_ckd[c].astype(str).str.strip(), errors='coerce')

# Map binary text cols: rbc, pc, pcc, ba, htn, dm, cad, appet, pe, ane
binary_map = {'normal': 0, 'abnormal': 1, 'present': 1, 'notpresent': 0,
              'yes': 1, 'no': 0, 'good': 0, 'poor': 1}
for c in ['rbc', 'pc', 'pcc', 'ba', 'htn', 'dm', 'cad', 'appet', 'pe', 'ane']:
    if c in df_ckd.columns:
        df_ckd[c] = df_ckd[c].astype(str).str.strip().str.lower().map(binary_map)
        kidney_features.append(c)

X_ckd = df_ckd[kidney_features].copy()
y_ckd = df_ckd['target'].copy()
mask  = y_ckd.notna()
X_ckd, y_ckd = X_ckd[mask], y_ckd[mask]

print(f"   After clean: {len(X_ckd)} rows | CKD={int(y_ckd.sum())} NotCKD={int((y_ckd==0).sum())}")

pipe_ckd = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler',  StandardScaler()),
    ('clf',     GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                           learning_rate=0.08, random_state=42))
])
auc_scores = cross_val_score(pipe_ckd, X_ckd, y_ckd, cv=cv, scoring='roc_auc')
print(f"   CV AUC: {auc_scores.mean():.3f} ± {auc_scores.std():.3f}")

pipe_ckd.fit(X_ckd, y_ckd)

bundle_ckd = {
    'model':          pipe_ckd,
    'features':       kidney_features,
    'cv_auc_mean':    round(auc_scores.mean(), 3),
    'cv_auc_std':     round(auc_scores.std(),  3),
    'n_train':        len(X_ckd),
    'source':         'Apollo Hospital Tamil Nadu India — 400 patients (UCI CKD)',
    'target':         'CKD vs not-CKD (binary)',
    'india_specific': True,
    'citation':       'Soundarapandian P et al., UCI ML Repository 2015; '
                      'Ramana BV et al., IJCA 2011;4(2)',
    'notes':          'India-specific: Tamil Nadu Apollo Hospital patients. '
                      'Features: creatinine, urea, haemoglobin, BP, glucose, electrolytes.'
}
with open(MDIR / "kidney_ml.pkl", "wb") as f:
    pickle.dump(bundle_ckd, f)
print(f"   ✅ Saved: models/kidney_ml.pkl  AUC={bundle_ckd['cv_auc_mean']}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. BRAIN — Alzheimer's Disease Dataset (2149 rows)
#    Source: Kaggle rabieelkharoua/alzheimers-disease-dataset
#    Purpose: Calibrate CAIDE dementia output; ML secondary signal
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("2. BRAIN — Alzheimer's (2149 rows)")
print("="*70)

df_alz = pd.read_csv(DATA / "india/brain/alzheimers_disease_data.csv")
print(f"   Loaded: {len(df_alz)} rows × {len(df_alz.columns)} cols")
print(f"   Diagnosis balance: {df_alz['Diagnosis'].value_counts().to_dict()}")

# Features matching what VitalTwin collects
alz_features = [
    'Age', 'Gender', 'BMI', 'Smoking', 'AlcoholConsumption', 'PhysicalActivity',
    'DietQuality', 'SleepQuality', 'FamilyHistoryAlzheimers', 'CardiovascularDisease',
    'Diabetes', 'Depression', 'HeadInjury', 'Hypertension', 'SystolicBP', 'DiastolicBP',
    'CholesterolTotal', 'CholesterolHDL', 'CholesterolLDL', 'MMSE',
    'FunctionalAssessment', 'MemoryComplaints', 'BehavioralProblems', 'ADL',
]
# Keep only columns that exist
alz_features = [c for c in alz_features if c in df_alz.columns]

X_alz = df_alz[alz_features].copy()
y_alz = df_alz['Diagnosis'].copy()

# Convert Gender: Male=1, Female=0
if 'Gender' in X_alz.columns:
    X_alz['Gender'] = pd.to_numeric(X_alz['Gender'], errors='coerce')

for c in X_alz.columns:
    X_alz[c] = pd.to_numeric(X_alz[c], errors='coerce')

mask = y_alz.notna()
X_alz, y_alz = X_alz[mask], y_alz[mask]
print(f"   After clean: {len(X_alz)} rows | Diag=1: {int(y_alz.sum())}  Diag=0: {int((y_alz==0).sum())}")
print(f"   Features used: {alz_features}")

pipe_alz = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler',  StandardScaler()),
    ('clf',     GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                           learning_rate=0.08, random_state=42))
])
auc_scores_alz = cross_val_score(pipe_alz, X_alz, y_alz, cv=cv, scoring='roc_auc')
print(f"   CV AUC: {auc_scores_alz.mean():.3f} ± {auc_scores_alz.std():.3f}")

pipe_alz.fit(X_alz, y_alz)

# Compute calibration: CAIDE score → actual Alzheimer's prevalence in dataset
# Group by FamilyHistory + Age range to get base rates
calib = {}
for age_grp, sub in df_alz.groupby(pd.cut(df_alz['Age'], bins=[0,50,60,70,100])):
    calib[str(age_grp)] = round(sub['Diagnosis'].mean(), 3)
print(f"   Age-group prevalence: {calib}")

bundle_alz = {
    'model':             pipe_alz,
    'features':          alz_features,
    'cv_auc_mean':       round(auc_scores_alz.mean(), 3),
    'cv_auc_std':        round(auc_scores_alz.std(),  3),
    'n_train':           len(X_alz),
    'age_group_prevalence': calib,
    'source':            'Kaggle: rabieelkharoua/alzheimers-disease-dataset (2149 rows)',
    'target':            'Alzheimer\'s Diagnosis (0=No, 1=Yes)',
    'india_specific':    False,
    'citation':          'Dataset: Rabie El Kharoua, Kaggle 2024. '
                         'CAIDE: Kivipelto M et al., Lancet Neurol 2006;5:735-741',
    'notes':             'Used as secondary ML signal for dementia risk. '
                         'Age-group prevalence used to calibrate CAIDE output.'
}
with open(MDIR / "alzheimer_ml.pkl", "wb") as f:
    pickle.dump(bundle_alz, f)
print(f"   ✅ Saved: models/alzheimer_ml.pkl  AUC={bundle_alz['cv_auc_mean']}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. HEART — Better ML (Cleveland UCI 1025 rows)
#    Source: Kaggle fedesoriano/heart-failure-prediction (merged 5 datasets)
#    Replaces: Russian cardio_train.csv (not India-specific)
#    Features: age, sex, chest pain type, BP, cholesterol, ECG, max HR, etc.
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("3. HEART — Cleveland UCI + merged (1025 rows)")
print("="*70)

df_heart = pd.read_csv(DATA / "india/heart/heart.csv")
print(f"   Loaded: {len(df_heart)} rows × {len(df_heart.columns)} cols")
print(f"   Columns: {list(df_heart.columns)}")
print(f"   Target balance: {df_heart['target'].value_counts().to_dict()}")

heart_features = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs',
                  'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']
heart_features = [c for c in heart_features if c in df_heart.columns]

X_hrt = df_heart[heart_features].copy()
y_hrt = df_heart['target'].copy()

for c in X_hrt.columns:
    X_hrt[c] = pd.to_numeric(X_hrt[c], errors='coerce')
y_hrt = pd.to_numeric(y_hrt, errors='coerce')

mask = y_hrt.notna()
X_hrt, y_hrt = X_hrt[mask], y_hrt[mask]
print(f"   After clean: {len(X_hrt)} rows")
print(f"   Features: {heart_features}")

pipe_hrt = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler',  StandardScaler()),
    ('clf',     GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                           learning_rate=0.08, random_state=42))
])
auc_scores_hrt = cross_val_score(pipe_hrt, X_hrt, y_hrt, cv=cv, scoring='roc_auc')
print(f"   CV AUC: {auc_scores_hrt.mean():.3f} ± {auc_scores_hrt.std():.3f}")

pipe_hrt.fit(X_hrt, y_hrt)

# Feature importance
clf_step = pipe_hrt.named_steps['clf']
feat_imp = dict(zip(heart_features, clf_step.feature_importances_.round(3)))
feat_imp_sorted = dict(sorted(feat_imp.items(), key=lambda x: -x[1]))
print(f"   Top features: {dict(list(feat_imp_sorted.items())[:5])}")

bundle_hrt = {
    'model':          pipe_hrt,
    'features':       heart_features,
    'cv_auc_mean':    round(auc_scores_hrt.mean(), 3),
    'cv_auc_std':     round(auc_scores_hrt.std(),  3),
    'n_train':        len(X_hrt),
    'feature_importance': feat_imp_sorted,
    'source':         'Cleveland Heart Disease UCI + merged datasets (Kaggle fedesoriano)',
    'target':         'Heart disease presence (0=No, 1=Yes)',
    'india_specific': False,
    'citation':       'Detrano R et al., Am J Cardiol 1989;64(5):304-310 (Cleveland); '
                      'PCE primary: Goff DC et al., Circulation 2014;129:S49-73',
    'notes':          'Replaces Russian cardio_train.csv. Better clinical features '
                      '(chest pain type, ECG, thalassemia). PCE formula remains primary.'
}
with open(MDIR / "heart_ml_v2.pkl", "wb") as f:
    pickle.dump(bundle_hrt, f)
print(f"   ✅ Saved: models/heart_ml_v2.pkl  AUC={bundle_hrt['cv_auc_mean']}")


# ══════════════════════════════════════════════════════════════════════════════
# 4. DIABETES — 100K dataset (HbA1c + blood glucose)
#    Source: Kaggle iammustafatz/diabetes-prediction-dataset
#    Used by: heart, brain, kidney, liver (diabetes detection from HbA1c)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("4. DIABETES — 100K rows (HbA1c)")
print("="*70)

df_dm = pd.read_csv(DATA / "india/diabaties/diabetes_prediction_dataset.csv")
print(f"   Loaded: {len(df_dm)} rows × {len(df_dm.columns)} cols")
print(f"   Columns: {list(df_dm.columns)}")
print(f"   Diabetes balance: {df_dm['diabetes'].value_counts().to_dict()}")

# Encode gender
df_dm['gender_enc'] = (df_dm['gender'].str.lower() == 'male').astype(int)

# Encode smoking history: never=0, former=1, current=2, ever=1, not current=0
smoke_map = {'never': 0, 'No Info': 0, 'not current': 0, 'ever': 1, 'former': 1, 'current': 2}
df_dm['smoking_enc'] = df_dm['smoking_history'].map(smoke_map).fillna(0)

dm_features = ['age', 'gender_enc', 'hypertension', 'heart_disease',
               'bmi', 'HbA1c_level', 'blood_glucose_level', 'smoking_enc']

X_dm = df_dm[dm_features].copy()
y_dm = df_dm['diabetes'].copy()
for c in X_dm.columns:
    X_dm[c] = pd.to_numeric(X_dm[c], errors='coerce')
mask = y_dm.notna()
X_dm, y_dm = X_dm[mask], y_dm[mask]
print(f"   After clean: {len(X_dm)} rows | Diabetic={int(y_dm.sum())}")

# Subsample to 20K for speed (still >10x bigger than any other dataset)
from sklearn.utils import resample
idx = resample(range(len(X_dm)), n_samples=20000, stratify=y_dm, random_state=42)
X_dm_s, y_dm_s = X_dm.iloc[idx], y_dm.iloc[idx]

pipe_dm = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler',  StandardScaler()),
    ('clf',     GradientBoostingClassifier(n_estimators=150, max_depth=4,
                                           learning_rate=0.1, random_state=42))
])
auc_dm = cross_val_score(pipe_dm, X_dm_s, y_dm_s, cv=cv, scoring='roc_auc')
print(f"   CV AUC (20K subsample): {auc_dm.mean():.3f} ± {auc_dm.std():.3f}")

pipe_dm.fit(X_dm_s, y_dm_s)

# HbA1c reference ranges from dataset
hba1c_stats = df_dm.groupby('diabetes')['HbA1c_level'].describe().round(2)
glucose_stats = df_dm.groupby('diabetes')['blood_glucose_level'].describe().round(2)
print(f"   HbA1c: diabetic mean={hba1c_stats.loc[1,'mean']}, non-diabetic mean={hba1c_stats.loc[0,'mean']}")
print(f"   Glucose: diabetic mean={glucose_stats.loc[1,'mean']}, non-diabetic mean={glucose_stats.loc[0,'mean']}")

bundle_dm = {
    'model':          pipe_dm,
    'features':       dm_features,
    'cv_auc_mean':    round(auc_dm.mean(), 3),
    'cv_auc_std':     round(auc_dm.std(),  3),
    'n_train':        len(X_dm),
    'hba1c_diabetic_mean':     float(hba1c_stats.loc[1,'mean']),
    'hba1c_nondiabetic_mean':  float(hba1c_stats.loc[0,'mean']),
    'glucose_diabetic_mean':   float(glucose_stats.loc[1,'mean']),
    'glucose_nondiabetic_mean':float(glucose_stats.loc[0,'mean']),
    'source':         'Kaggle: iammustafatz/diabetes-prediction-dataset (100K rows)',
    'target':         'Diabetes (0=No, 1=Yes)',
    'india_specific': False,
    'citation':       'Dataset: iammustafatz, Kaggle 2023. '
                      'HbA1c cutoff: ADA Standards of Care 2023 (≥6.5% = diabetes)',
    'notes':          'HbA1c ≥6.5% (ADA 2023) and FPG ≥126 mg/dL used as thresholds. '
                      'Used by heart, brain, kidney, liver models for diabetes detection.'
}
with open(MDIR / "diabetes_ml.pkl", "wb") as f:
    pickle.dump(bundle_dm, f)
print(f"   ✅ Saved: models/diabetes_ml.pkl  AUC={bundle_dm['cv_auc_mean']}")


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("TRAINING COMPLETE — SUMMARY")
print("="*70)
results = [
    ("Kidney ML (India)",   "kidney_ml.pkl",     bundle_ckd['cv_auc_mean'],  bundle_ckd['n_train'],  bundle_ckd['india_specific']),
    ("Alzheimer ML",        "alzheimer_ml.pkl",  bundle_alz['cv_auc_mean'],  bundle_alz['n_train'],  bundle_alz['india_specific']),
    ("Heart ML v2",         "heart_ml_v2.pkl",   bundle_hrt['cv_auc_mean'],  bundle_hrt['n_train'],  bundle_hrt['india_specific']),
    ("Diabetes ML",         "diabetes_ml.pkl",   bundle_dm['cv_auc_mean'],   bundle_dm['n_train'],   bundle_dm['india_specific']),
]
for name, fname, auc, n, india in results:
    flag = "🇮🇳" if india else "🌐"
    print(f"  {flag} {name:25s}  AUC={auc:.3f}  n={n:6d}  → models/{fname}")
print()
print("Next step: Wire these into organ models (kidney_model.py, brain_model.py, heart_model.py)")
