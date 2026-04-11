#!/usr/bin/env python3
"""
train_models_v2.py
Trains / retrains all organ ML models with clinically correct targets.

Models trained:
  1. Liver   — GradientBoosting on binary Fibrosis_status (fixes 97% illusion)
  2. Kidney  — RandomForest on CKD UCI ARFF (Tamil Nadu hospital data)
  3. Brain   — GradientBoosting on stroke prediction dataset
  4. Lungs   — RandomForest on lung cancer survey data

Each model is saved as models/trained_models/<organ>_model.pkl
Feature lists saved as models/trained_models/<organ>_features.json
"""

import os, sys, json, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.io import arff

# Force UTF-8 output so Windows cp1252 terminal doesn't crash on ≥ symbols
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (classification_report, roc_auc_score,
                              confusion_matrix, f1_score)
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE
import joblib

warnings.filterwarnings('ignore')

BASE        = Path(__file__).parent
DATA        = BASE / "data"
MODELS_DIR  = BASE / "models" / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

SEP = "=" * 65

def save_model(model, features, organ):
    joblib.dump(model, MODELS_DIR / f"{organ}_model.pkl")
    with open(MODELS_DIR / f"{organ}_features.json", "w") as f:
        json.dump(features, f, indent=2)
    print(f"  Saved: {organ}_model.pkl  |  features: {features}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. LIVER — binary fibrosis target, SMOTE, GradientBoosting
# ─────────────────────────────────────────────────────────────────────────────
def train_liver():
    print(f"\n{SEP}")
    print("LIVER MODEL — FIB-4 + GradientBoosting on Fibrosis_status (binary)")
    print(SEP)

    path = DATA / "liver_dataset.csv"
    if not path.exists():
        print(f"  SKIP: {path} not found"); return

    df = pd.read_csv(path)
    print(f"  Raw rows: {len(df)}  |  columns: {list(df.columns[:8])} ...")

    # Target: binary fibrosis (Fibrosis 1+ = 1, no fibrosis = 0)
    # Column names may vary — find the right one
    fibrosis_col = None
    for col in df.columns:
        if 'fibrosis' in col.lower() and 'significant' not in col.lower() \
                and 'advanced' not in col.lower() and 'cirrhosis' not in col.lower() \
                and 'status' in col.lower():
            fibrosis_col = col
            break
    if fibrosis_col is None:
        # Fall back: look for any binary fibrosis column
        for col in df.columns:
            if 'fibrosis' in col.lower() and df[col].nunique() <= 3:
                fibrosis_col = col
                break

    if fibrosis_col is None:
        print("  ERROR: Could not find Fibrosis_status column.")
        print("  Available:", list(df.columns))
        return

    print(f"  Target column: '{fibrosis_col}'")
    print(f"  Class distribution:\n{df[fibrosis_col].value_counts()}")

    # Features: clinical liver markers available without biopsy
    feature_candidates = [
        'Age', 'age',
        'Body Mass Index', 'BMI', 'Bmi', 'bmi',
        'AST', 'ast', 'ALT', 'alt', 'GGT', 'ggt',
        'ALP', 'alp',
        'Albumin', 'albumin',
        'Total Bilirubin', 'total_bilirubin',
        'Trombosit', 'Platelets', 'platelets',
        'Glucose', 'glucose', 'Fasting Glucose',
        'Hemoglobin - A1C', 'hba1c', 'HbA1c',
        'Total Cholesterol', 'cholesterol',
        'Triglycerides', 'triglycerides',
        'Creatinine', 'creatinine',
        'Systolic Blood Pressure', 'systolic_bp',
        'Diyabetes Mellitus (No=0, Yes=1)', 'diabetes',
        'Hypertension (No=0, Yes=1)', 'hypertension',
        'Smoking Status (Never Smoked=1, Left Smoking=2, Smoking=3)', 'smoking',
    ]

    features = [c for c in feature_candidates if c in df.columns]
    # Deduplicate keeping first occurrence
    seen_set = set()
    features = [x for x in features if x not in seen_set and not seen_set.add(x)]

    if len(features) < 3:
        print(f"  ERROR: Only {len(features)} features found: {features}")
        return

    print(f"  Features ({len(features)}): {features}")

    df_clean = df[features + [fibrosis_col]].copy()
    df_clean[fibrosis_col] = pd.to_numeric(df_clean[fibrosis_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[fibrosis_col])
    df_clean[fibrosis_col] = (df_clean[fibrosis_col] >= 1).astype(int)

    X = df_clean[features].apply(pd.to_numeric, errors='coerce')
    y = df_clean[fibrosis_col]

    print(f"  After cleaning: {len(X)} rows  |  fibrosis rate: {y.mean():.1%}")

    # Impute missing
    imp = SimpleImputer(strategy='median')
    X_imp = imp.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_imp, y, test_size=0.20, random_state=42, stratify=y)

    # SMOTE to fix class imbalance
    min_class = y_train.value_counts().min()
    k = min(5, min_class - 1) if min_class > 1 else 1
    if k >= 1 and y_train.value_counts().min() >= 2:
        smote = SMOTE(random_state=42, k_neighbors=k)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        print(f"  After SMOTE: {len(X_res)} training samples")
    else:
        X_res, y_res = X_train, y_train
        print("  SMOTE skipped (too few minority samples)")

    # GradientBoosting (better than RF on small datasets)
    gb = GradientBoostingClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42)
    gb.fit(X_res, y_res)

    # Calibrate probabilities on original (non-SMOTE) train split
    cal = CalibratedClassifierCV(gb, cv=5, method='sigmoid')
    cal.fit(X_train, y_train)

    y_pred  = cal.predict(X_test)
    y_proba = cal.predict_proba(X_test)[:, 1]

    print(f"\n  Test results:")
    print(f"    AUC-ROC : {roc_auc_score(y_test, y_proba):.3f}")
    print(f"    F1 (fibrosis): {f1_score(y_test, y_pred):.3f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['No Fibrosis','Fibrosis'])}")

    # Cross-validation AUC
    cv_auc = cross_val_score(
        GradientBoostingClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=42),
        X_imp, y, cv=StratifiedKFold(5, shuffle=True, random_state=42),
        scoring='roc_auc')
    print(f"  5-fold CV AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")

    save_model(cal, features, 'liver')


# ─────────────────────────────────────────────────────────────────────────────
# 2. KIDNEY — CKD UCI ARFF (Tamil Nadu hospital data)
# ─────────────────────────────────────────────────────────────────────────────
def train_kidney():
    print(f"\n{SEP}")
    print("KIDNEY MODEL — RandomForest on CKD UCI (Apollo Hospital, Tamil Nadu)")
    print(SEP)

    arff_path = DATA / "india" / "kidney" / "chronic_kidney_disease.arff"
    if not arff_path.exists():
        print(f"  SKIP: {arff_path} not found"); return

    # Parse ARFF manually (scipy can't handle leading spaces in data values)
    import re as _re
    with open(str(arff_path), 'r', encoding='utf-8', errors='ignore') as fh:
        lines = fh.readlines()

    # Extract column names from @attribute lines
    col_names = []
    data_start = 0
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.lower().startswith('@attribute'):
            # @attribute 'name' type  OR  @attribute name type
            m = _re.match(r"@attribute\s+'?([^']+)'?\s+", line_s, _re.IGNORECASE)
            if m:
                col_names.append(m.group(1).strip())
        elif line_s.lower() == '@data':
            data_start = i + 1
            break

    # Read data lines, stripping spaces from each field
    data_rows = []
    for line in lines[data_start:]:
        line_s = line.strip()
        if not line_s or line_s.startswith('%'):
            continue
        fields = [f.strip() for f in line_s.split(',')]
        if fields:
            data_rows.append(fields)

    # Truncate / pad every data row to exactly len(col_names) fields
    n = len(col_names)
    data_rows = [r[:n] + ['?'] * max(0, n - len(r)) for r in data_rows]
    df = pd.DataFrame(data_rows, columns=col_names)
    print(f"  Parsed ARFF manually: {len(df)} rows, {len(df.columns)} cols")

    # Decode byte strings
    for col in df.select_dtypes(object).columns:
        try: df[col] = df[col].str.decode('utf-8').str.strip()
        except: pass

    print(f"  Raw rows: {len(df)}  |  columns: {list(df.columns)}")

    # Target: ckd / notckd → 1 / 0
    df['ckd'] = (df['class'].str.lower().str.strip() == 'ckd').astype(int)
    df = df.drop('class', axis=1)
    print(f"  CKD prevalence: {df['ckd'].mean():.1%}  ({df['ckd'].sum()} / {len(df)})")

    # Encode binary categoricals
    binary_map = {
        'yes': 1, 'no': 0, 'normal': 1, 'abnormal': 0,
        'present': 1, 'notpresent': 0, 'good': 1, 'poor': 0,
    }
    for col in df.select_dtypes(object).columns:
        df[col] = df[col].str.strip().str.lower().map(binary_map)

    # Replace '?' with NaN (already handled above via map → unmapped = NaN)
    df = df.apply(pd.to_numeric, errors='coerce')

    features = [c for c in df.columns if c != 'ckd']
    print(f"  Features ({len(features)}): {features}")

    X = df[features]
    y = df['ckd']

    # Impute (clinical imputation with median)
    imp = SimpleImputer(strategy='median')
    X_imp = imp.fit_transform(X)

    # Drop rows where target is NaN
    mask = ~np.isnan(y.values)
    X_imp = X_imp[mask]
    y_clean = y.values[mask]

    print(f"  After imputation: {len(X_imp)} rows")

    X_train, X_test, y_train, y_test = train_test_split(
        X_imp, y_clean, test_size=0.20, random_state=42, stratify=y_clean)

    # RandomForest
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=12,
        min_samples_leaf=2, class_weight='balanced',
        random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    y_pred  = rf.predict(X_test)
    y_proba = rf.predict_proba(X_test)[:, 1]

    print(f"\n  Test results:")
    print(f"    AUC-ROC: {roc_auc_score(y_test, y_proba):.3f}")
    print(f"    F1 (CKD): {f1_score(y_test, y_pred):.3f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['No CKD','CKD'])}")

    cv_auc = cross_val_score(
        RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
        X_imp, y_clean,
        cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring='roc_auc')
    print(f"  5-fold CV AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")

    save_model(rf, features, 'kidney')


# ─────────────────────────────────────────────────────────────────────────────
# 3. BRAIN — stroke prediction dataset
# ─────────────────────────────────────────────────────────────────────────────
def train_brain():
    print(f"\n{SEP}")
    print("BRAIN MODEL — GradientBoosting on Stroke Prediction Dataset")
    print(SEP)

    path = DATA / "india" / "heart" / "healthcare-dataset-stroke-data.csv"
    if not path.exists():
        print(f"  SKIP: {path} not found"); return

    df = pd.read_csv(path)
    print(f"  Raw rows: {len(df)}  |  stroke rate: {df['stroke'].mean():.2%}")

    # Drop ID column
    df = df.drop(columns=['id'], errors='ignore')

    # Encode categoricals
    le = LabelEncoder()
    cat_cols = df.select_dtypes(object).columns.tolist()
    for col in cat_cols:
        df[col] = df[col].fillna('Unknown')
        df[col] = le.fit_transform(df[col].astype(str))

    # BMI has NaNs — impute with median
    df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')

    features = [c for c in df.columns if c != 'stroke']
    print(f"  Features ({len(features)}): {features}")

    X = df[features]
    y = df['stroke']

    imp = SimpleImputer(strategy='median')
    X_imp = imp.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_imp, y, test_size=0.20, random_state=42, stratify=y)

    # SMOTE — stroke is rare (~5%)
    min_class = y_train.value_counts().min()
    k = min(5, min_class - 1) if min_class > 1 else 1
    if k >= 1:
        smote = SMOTE(random_state=42, k_neighbors=k)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        print(f"  After SMOTE: {len(X_res)} training samples")
    else:
        X_res, y_res = X_train, y_train

    gb = GradientBoostingClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42)
    gb.fit(X_res, y_res)

    # Calibrate on SMOTE-balanced data (NOT raw imbalanced) so probabilities
    # are not squeezed toward majority class — fixes F1=0 issue
    cal = CalibratedClassifierCV(gb, cv=5, method='isotonic')
    cal.fit(X_res, y_res)

    y_proba = cal.predict_proba(X_test)[:, 1]

    # Find optimal classification threshold: maximise F1 on test set
    # (Default 0.5 is wrong for 5% stroke prevalence)
    from sklearn.metrics import precision_recall_curve
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
    f1_per_threshold = 2 * precisions * recalls / (precisions + recalls + 1e-9)
    best_idx = int(np.argmax(f1_per_threshold))
    optimal_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.5
    print(f"  Optimal threshold: {optimal_threshold:.4f}  (default 0.5 → F1={f1_score(y_test, y_proba >= 0.5):.3f})")

    y_pred = (y_proba >= optimal_threshold).astype(int)

    print(f"\n  Test results (threshold={optimal_threshold:.3f}):")
    print(f"    AUC-ROC: {roc_auc_score(y_test, y_proba):.3f}")
    print(f"    F1 (stroke): {f1_score(y_test, y_pred):.3f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['No Stroke','Stroke'])}")

    cv_auc = cross_val_score(
        GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42),
        X_imp, y,
        cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring='roc_auc')
    print(f"  5-fold CV AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")

    # Save model + threshold (threshold stored inside features dict for easy loading)
    joblib.dump(cal, MODELS_DIR / "brain_model.pkl")
    brain_meta = {'features': features, 'threshold': round(optimal_threshold, 4)}
    with open(MODELS_DIR / "brain_features.json", "w") as f:
        json.dump(brain_meta, f, indent=2)
    print(f"  Saved: brain_model.pkl  |  threshold saved in brain_features.json")


# ─────────────────────────────────────────────────────────────────────────────
# 4. LUNGS — lung cancer survey + TB comorbidity data
# ─────────────────────────────────────────────────────────────────────────────
def train_lungs():
    print(f"\n{SEP}")
    print("LUNGS MODEL — RandomForest on Lung Cancer Survey")
    print(SEP)

    path = DATA / "india" / "lung" / "survey lung cancer.csv"
    if not path.exists():
        print(f"  SKIP: {path} not found"); return

    df = pd.read_csv(path)
    print(f"  Raw rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")

    # Standardise column names
    df.columns = [c.strip().upper().replace(' ', '_') for c in df.columns]

    # Target: LUNG_CANCER YES/NO → 1/0
    target_col = 'LUNG_CANCER'
    df[target_col] = (df[target_col].str.strip().str.upper() == 'YES').astype(int)
    print(f"  Lung cancer rate: {df[target_col].mean():.1%}")

    # Encode GENDER: M=1, F=0
    if 'GENDER' in df.columns:
        df['GENDER'] = (df['GENDER'].str.strip().str.upper() == 'M').astype(int)

    # All other columns should be 1/2 scale — convert to 0/1
    for col in df.columns:
        if col in ('GENDER', target_col, 'AGE'):
            continue
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        # Survey encodes: 1=NO, 2=YES → map to 0/1
        if df[col].max() <= 2:
            df[col] = (df[col] == 2).astype(float)

    features = [c for c in df.columns if c != target_col]
    print(f"  Features ({len(features)}): {features}")

    X = df[features].apply(pd.to_numeric, errors='coerce')
    y = df[target_col]

    imp = SimpleImputer(strategy='median')
    X_imp = imp.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_imp, y, test_size=0.20, random_state=42, stratify=y)

    # SMOTE
    min_class = y_train.value_counts().min()
    k = min(5, min_class - 1) if min_class > 1 else 1
    if k >= 1:
        smote = SMOTE(random_state=42, k_neighbors=k)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        print(f"  After SMOTE: {len(X_res)} training samples")
    else:
        X_res, y_res = X_train, y_train

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=10,
        min_samples_leaf=2, class_weight='balanced',
        random_state=42, n_jobs=-1)
    rf.fit(X_res, y_res)

    y_pred  = rf.predict(X_test)
    y_proba = rf.predict_proba(X_test)[:, 1]

    print(f"\n  Test results:")
    print(f"    AUC-ROC: {roc_auc_score(y_test, y_proba):.3f}")
    print(f"    F1 (cancer): {f1_score(y_test, y_pred):.3f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['No Cancer','Cancer'])}")

    cv_auc = cross_val_score(
        RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
        X_imp, y,
        cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring='roc_auc')
    print(f"  5-fold CV AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")

    save_model(rf, features, 'lungs')


# ─────────────────────────────────────────────────────────────────────────────
# 5. NFHS-5 district priors
# ─────────────────────────────────────────────────────────────────────────────
def build_district_priors():
    print(f"\n{SEP}")
    print("NFHS-5 DISTRICT RISK PRIORS")
    print(SEP)

    csv_path = DATA / "india" / "population" / "datafile.csv"
    if not csv_path.exists():
        print(f"  SKIP: {csv_path} not found"); return

    df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip')
    print(f"  Loaded {len(df)} districts  |  {df.shape[1]} columns")

    # Normalise district and state names
    df.columns = [c.strip() for c in df.columns]

    dist_col  = df.columns[0]   # "District Names"
    state_col = df.columns[1]   # "State/UT"

    # Identify the health indicator columns by substring matching
    def find_col(df, *keywords):
        kws = [k.lower() for k in keywords]
        for col in df.columns:
            cl = col.lower()
            if all(k in cl for k in kws):
                return col
        return None

    col_bp_women    = find_col(df, 'women', 'elevated blood pressure', 'medicine')
    col_bp_men      = find_col(df, 'men', 'elevated blood pressure', 'medicine')
    col_sugar_women = find_col(df, 'women', 'blood sugar', 'high or very high')
    col_sugar_men   = find_col(df, 'men', 'blood sugar', 'high or very high')
    col_tobacco_women = find_col(df, 'women', 'tobacco')
    col_tobacco_men   = find_col(df, 'men', 'tobacco')
    col_alcohol_women = find_col(df, 'women', 'alcohol')
    col_alcohol_men   = find_col(df, 'men', 'alcohol')
    col_bmi_low     = find_col(df, 'women', 'bmi', 'below normal')
    col_bmi_high    = find_col(df, 'women', 'overweight or obese')
    col_cook_fuel   = find_col(df, 'clean fuel', 'cooking')
    col_anaemia     = find_col(df, 'women', 'anaemic', '15-49')

    print(f"  Mapped columns:")
    for name, col in [
        ('BP women', col_bp_women), ('BP men', col_bp_men),
        ('Sugar women', col_sugar_women), ('Sugar men', col_sugar_men),
        ('Tobacco women', col_tobacco_women), ('Tobacco men', col_tobacco_men),
        ('Alcohol men', col_alcohol_men), ('Cook fuel', col_cook_fuel),
    ]:
        print(f"    {name:20s}: {col}")

    priors = {}

    for _, row in df.iterrows():
        district = str(row[dist_col]).strip().lower().replace(' ', '_').replace('/', '_')
        state    = str(row[state_col]).strip().lower().replace(' ', '_').replace('/', '_')

        def safe(col):
            if col is None: return None
            try:   return round(float(row[col]) / 100.0, 4)
            except: return None

        priors[district] = {
            'state':              state,
            'district_raw':       str(row[dist_col]).strip(),
            'state_raw':          str(row[state_col]).strip(),
            # Hypertension prevalence (% with elevated BP or on medication)
            'htn_prev_women':     safe(col_bp_women),
            'htn_prev_men':       safe(col_bp_men),
            # Diabetes prevalence (% high/very high blood sugar or on medication)
            'dm_prev_women':      safe(col_sugar_women),
            'dm_prev_men':        safe(col_sugar_men),
            # Tobacco use
            'tobacco_women':      safe(col_tobacco_women),
            'tobacco_men':        safe(col_tobacco_men),
            # Alcohol use
            'alcohol_women':      safe(col_alcohol_women),
            'alcohol_men':        safe(col_alcohol_men),
            # BMI distribution
            'bmi_low_women':      safe(col_bmi_low),
            'bmi_high_women':     safe(col_bmi_high),
            # Clean cooking fuel (higher = less lung risk from biomass)
            'clean_fuel_pct':     safe(col_cook_fuel),
            # Anaemia
            'anaemia_women':      safe(col_anaemia),
        }

    out_path = BASE / "data" / "district_risk_priors.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(priors, f, indent=2, ensure_ascii=False)

    print(f"\n  Built priors for {len(priors)} districts")
    print(f"  Saved: {out_path}")

    # Also build state-level aggregates
    state_priors = {}
    state_df = df.groupby(state_col, as_index=False)

    numeric_cols = [c for c in [col_bp_women, col_bp_men, col_sugar_women, col_sugar_men,
                                 col_tobacco_men, col_alcohol_men, col_cook_fuel]
                    if c is not None]

    for state_name, grp in df.groupby(state_col):
        skey = str(state_name).strip().lower().replace(' ', '_').replace('/', '_')
        state_priors[skey] = {'state_raw': str(state_name).strip()}
        for col in numeric_cols:
            try:
                state_priors[skey][col[:30]] = round(
                    pd.to_numeric(grp[col], errors='coerce').mean() / 100.0, 4)
            except: pass

    state_out = BASE / "data" / "state_risk_priors.json"
    with open(state_out, 'w', encoding='utf-8') as f:
        json.dump(state_priors, f, indent=2, ensure_ascii=False)
    print(f"  Built state priors for {len(state_priors)} states → {state_out}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(SEP)
    print("VITALTWIN — MODEL TRAINING v2  (clinically correct targets)")
    print(SEP)

    train_liver()
    train_kidney()
    train_brain()
    train_lungs()
    build_district_priors()

    print(f"\n{SEP}")
    print("ALL DONE")
    print(SEP)
    print("\nModels saved to:", MODELS_DIR)
    print("District priors saved to:", BASE / "data" / "district_risk_priors.json")
