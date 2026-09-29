# train_stroke_model.py
# Train a stroke risk ML model from the 5,110-row Kaggle stroke dataset
# + calibrate against INTERSTROKE India ORs for South Asian correction
#
# Dataset: healthcare-dataset-stroke-data.csv (5,110 rows)
# Features: age, hypertension, heart_disease, avg_glucose_level, bmi,
#           smoking_status, ever_married, work_type, Residence_type
# Target: stroke (binary)
# Stroke prevalence: 4.9% (realistic clinical rate)
#
# Method:
#   1. Train GradientBoostingClassifier (handles imbalanced data well)
#   2. Calibrate probabilities (Platt scaling)
#   3. Apply INTERSTROKE India correction: multiply base risk by India/Global PAR ratio
#   4. Save model to models/stroke_ml.pkl
#
# South Asian calibration:
#   Global 10-factor PAR = 90.7% (O'Donnell 2016)
#   South Asia PAR = 91.5% — very similar, so use same OR values
#   But South Asia baseline stroke incidence is 1.28x higher than global average
#   (GBD 2016 India stroke incidence vs global)
#   So: India_stroke_risk = ML_prob * 1.28
#
# Citation: O'Donnell MJ et al., Lancet 2016;388:761-775 (INTERSTROKE)
#           Feigin VL et al., Lancet Neurol 2019;18(5):459-480 (GBD India)

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
import pickle

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import Pipeline

BASE = Path(__file__).parent

# ── 1. Load data ──────────────────────────────────────────────────────────────
print("[1] Loading stroke dataset...")
df = pd.read_csv(BASE / "data/india/heart/healthcare-dataset-stroke-data.csv")
print(f"    Rows: {len(df)}  Stroke prevalence: {df['stroke'].mean():.3f}")
print(f"    Columns: {list(df.columns)}")

# Drop 'Other' gender (only 1 row)
df = df[df['gender'] != 'Other'].copy()

# ── 2. Feature engineering ────────────────────────────────────────────────────
print("\n[2] Feature engineering...")

# Encode categorical features
df['gender_enc']          = (df['gender'] == 'Male').astype(int)
df['ever_married_enc']    = (df['ever_married'] == 'Yes').astype(int)
df['residence_urban']     = (df['Residence_type'] == 'Urban').astype(int)

# Smoking (4 categories → ordinal risk)
smoke_map = {'never smoked': 0, 'Unknown': 0, 'formerly smoked': 1, 'smokes': 2}
df['smoking_risk'] = df['smoking_status'].map(smoke_map).fillna(0)

# Work type risk (manual labor / stress)
work_map = {'children': 0, 'Never_worked': 0, 'Govt_job': 1,
            'Private': 1, 'Self-employed': 2}
df['work_risk'] = df['work_type'].map(work_map).fillna(1)

# BMI imputation: median by age group
df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')
df['bmi'] = df.groupby(pd.cut(df['age'], bins=[0,40,55,70,120]))['bmi'].transform(
    lambda x: x.fillna(x.median())
)
df['bmi'] = df['bmi'].fillna(df['bmi'].median())

# Age groups for interaction
df['age_over60']   = (df['age'] >= 60).astype(int)
df['glucose_high'] = (df['avg_glucose_level'] >= 126).astype(int)
df['bmi_obese']    = (df['bmi'] >= 30).astype(int)

# Interaction: hypertension + age
df['htn_age']      = df['hypertension'] * df['age']

FEATURES = [
    'age', 'gender_enc', 'hypertension', 'heart_disease',
    'ever_married_enc', 'avg_glucose_level', 'bmi',
    'smoking_risk', 'work_risk', 'residence_urban',
    'age_over60', 'glucose_high', 'bmi_obese', 'htn_age',
]

X = df[FEATURES].values
y = df['stroke'].values

print(f"    Features: {FEATURES}")
print(f"    X shape: {X.shape}  Positive: {y.sum()} ({y.mean():.3f})")

# ── 3. Train GradientBoosting with calibration ────────────────────────────────
print("\n[3] Training GradientBoostingClassifier + Platt calibration...")

base_clf = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,
    min_samples_leaf=20,
    subsample=0.8,
    random_state=42,
)

# CalibratedClassifierCV wraps base model with sigmoid calibration
clf = CalibratedClassifierCV(base_clf, cv=5, method='sigmoid')

# ── 4. Cross-validate ─────────────────────────────────────────────────────────
print("\n[4] Cross-validating (5-fold stratified)...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
auc_scores  = cross_val_score(clf, X, y, cv=cv, scoring='roc_auc')
print(f"    AUC scores: {[round(s,3) for s in auc_scores]}")
print(f"    Mean AUC: {auc_scores.mean():.3f} ± {auc_scores.std():.3f}")

# ── 5. Final fit on all data ──────────────────────────────────────────────────
print("\n[5] Final fit on full dataset...")
clf.fit(X, y)

# Final AUC on training data (upper bound)
y_pred = clf.predict_proba(X)[:, 1]
train_auc = roc_auc_score(y, y_pred)
train_brier = brier_score_loss(y, y_pred)
print(f"    Train AUC: {train_auc:.3f}  Brier score: {train_brier:.4f}")

# ── 6. Save model with metadata ───────────────────────────────────────────────
print("\n[6] Saving model...")
model_dir = BASE / "models"
model_dir.mkdir(exist_ok=True)

model_bundle = {
    'model': clf,
    'features': FEATURES,
    'cv_auc_mean': round(float(auc_scores.mean()), 3),
    'cv_auc_std':  round(float(auc_scores.std()), 3),
    'train_rows': len(df),
    'stroke_prevalence': float(y.mean()),
    'india_calibration_factor': 1.28,   # GBD 2016 India stroke incidence vs global
    'dataset': 'healthcare-dataset-stroke-data.csv (Kaggle, 5110 rows)',
    'notes': (
        "General population stroke ML model. "
        "Calibrated for South Asian baseline via 1.28x India incidence multiplier "
        "(Feigin VL et al., Lancet Neurol 2019 — GBD 2016 India). "
        "Used as ML signal in brain_model alongside INTERSTROKE India formula."
    ),
    'citation': 'Feigin VL et al., Lancet Neurol 2019;18(5):459-480 (GBD India stroke incidence)'
}

with open(model_dir / "stroke_ml.pkl", "wb") as f:
    pickle.dump(model_bundle, f)
print(f"    ✅ Saved: models/stroke_ml.pkl")

# ── 7. Quick sanity checks ────────────────────────────────────────────────────
print("\n[7] Sanity checks on stroke risk predictions...")
test_cases = [
    {'label': 'Low risk (30F, healthy)',
     'vals': [30, 0, 0, 0, 1, 90, 22, 0, 1, 1, 0, 0, 0, 0]},
    {'label': 'High risk (70M, HTN+DM)',
     'vals': [70, 1, 1, 1, 1, 140, 28, 1, 1, 1, 1, 1, 0, 70]},
    {'label': 'Very high (78M, HTN+DM+smoking)',
     'vals': [78, 1, 1, 1, 1, 200, 30, 2, 2, 1, 1, 1, 1, 78]},
    {'label': 'Medium (50M, smoker)',
     'vals': [50, 1, 0, 0, 1, 100, 26, 2, 1, 1, 0, 0, 0, 0]},
]
for tc in test_cases:
    prob = clf.predict_proba([tc['vals']])[0][1]
    india_prob = min(1.0, prob * 1.28)
    print(f"    {tc['label']}: base={prob:.3f}  india_calibrated={india_prob:.3f}")

print("\n✅ Stroke ML model training complete!")
print(f"   CV AUC: {auc_scores.mean():.3f} ± {auc_scores.std():.3f}")
print(f"   Model saved: models/stroke_ml.pkl")
print(f"   India calibration: ×1.28 (GBD 2016 India stroke incidence)")
