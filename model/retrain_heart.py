"""Retrain heart model with current sklearn version to fix version mismatch warning."""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, f1_score, classification_report
from sklearn.calibration import CalibratedClassifierCV
from imblearn.over_sampling import SMOTE
import joblib, json
from pathlib import Path

BASE       = Path(__file__).parent
DATA       = BASE / "data" / "processed" / "heart_training_data.csv"
MODELS_DIR = BASE / "models" / "trained_models"

print("=" * 60)
print("HEART MODEL — Retrain with sklearn 1.8.0")
print("=" * 60)

if not DATA.exists():
    print(f"ERROR: {DATA} not found")
    exit(1)

df = pd.read_csv(DATA)
print(f"Loaded {len(df)} rows")

feature_cols = ['age', 'bmi', 'systolic_bp', 'diastolic_bp',
                'cholesterol_mgdl', 'glucose_mgdl', 'smoke', 'alco', 'active']

# Use whichever columns exist
available = [c for c in feature_cols if c in df.columns]
# Fallback to original column names if mapped ones not present
if 'cholesterol_mgdl' not in df.columns and 'cholesterol' in df.columns:
    df['cholesterol_mgdl'] = df['cholesterol'].map({1: 185, 2: 215, 3: 265}).fillna(200)
    available = [c for c in feature_cols if c in df.columns]
if 'glucose_mgdl' not in df.columns and 'gluc' in df.columns:
    df['glucose_mgdl'] = df['gluc'].map({1: 90, 2: 115, 3: 160}).fillna(100)
    available = [c for c in feature_cols if c in df.columns]

print(f"Features: {available}")
target = 'cardio' if 'cardio' in df.columns else df.columns[-1]
print(f"Target: {target}, positive rate: {df[target].mean():.1%}")

X = df[available].apply(pd.to_numeric, errors='coerce').fillna(df[available].median())
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# SMOTE
smote = SMOTE(random_state=42)
X_res, y_res = smote.fit_resample(X_train, y_train)
print(f"After SMOTE: {len(X_res)} training samples")

# RandomForest with calibration
rf = RandomForestClassifier(
    n_estimators=300, max_depth=12,
    min_samples_leaf=2, class_weight='balanced',
    random_state=42, n_jobs=-1)
rf.fit(X_res, y_res)

# Calibrate
cal = CalibratedClassifierCV(rf, cv=5, method='isotonic')
cal.fit(X_train, y_train)

y_proba = cal.predict_proba(X_test)[:, 1]
y_pred  = (y_proba > 0.5).astype(int)

print(f"\nTest results:")
print(f"  AUC-ROC: {roc_auc_score(y_test, y_proba):.3f}")
print(f"  F1:      {f1_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred, target_names=['No CVD', 'CVD']))

cv_auc = cross_val_score(
    RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
    X, y, cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring='roc_auc')
print(f"5-fold CV AUC: {cv_auc.mean():.3f} +/- {cv_auc.std():.3f}")

joblib.dump(cal, MODELS_DIR / "heart_model.pkl")
json.dump(available, open(MODELS_DIR / "heart_features.json", "w"))
print(f"\nSaved: heart_model.pkl | features: {available}")
print("Done!")
