"""
integrate_datasets.py
=====================
Integrates all 4 currently-unused datasets into the VitalTwin model pipeline.

TASK 1: Retrain heart ML with Cleveland UCI (heart.csv) + heartdata.csv merged
TASK 2: Train NHANES liver ML (nhanes_liver_data.csv, 9473 rows)
TASK 3: Parse TB comorbidity CSVs → extend tb_lung_risk_by_state.json
TASK 4: Parse NFHS-5 district data → build district_health_priors.json

Run: python integrate_datasets.py
"""

import json
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

MODELS_DIR = Path("models")
DATA_DIR   = Path("data")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 1: Upgrade heart ML — merge Cleveland UCI + heartdata into existing model
# ══════════════════════════════════════════════════════════════════════════════
def task1_upgrade_heart_ml():
    print("\n" + "="*60)
    print("TASK 1: Upgrading heart_ml_v2 with Cleveland + heartdata")
    print("="*60)

    # --- Load Cleveland UCI (heart.csv) ---
    # Cols: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target
    cld = pd.read_csv("data/india/heart/heart.csv")
    cld = cld.rename(columns={
        "age": "age", "sex": "gender", "trestbps": "systolic_bp",
        "chol": "cholesterol", "fbs": "gluc", "target": "cardio"
    })
    cld["bmi"] = 26.0  # Cleveland has no BMI — use Indian adult mean (NFHS-5)
    cld["diastolic_bp"] = 80.0
    cld["smoke"] = 0
    cld["alco"] = 0
    cld["active"] = 1
    cld = cld[["age", "bmi", "systolic_bp", "diastolic_bp", "cholesterol", "gluc",
                "smoke", "alco", "active", "cardio"]]
    print(f"  Cleveland UCI: {len(cld)} rows, target={cld['cardio'].value_counts().to_dict()}")

    # --- Load heartdata.csv ---
    # Cols: Age,Sex,ChestPainType,RestingBP,Cholesterol,FastingBS,RestingECG,
    #       MaxHR,ExerciseAngina,Oldpeak,ST_Slope,HeartDisease
    hd = pd.read_csv("data/india/heart/heartdata.csv")
    hd = hd.rename(columns={
        "Age": "age",
        "Sex": "gender",
        "RestingBP": "systolic_bp",
        "Cholesterol": "cholesterol",
        "FastingBS": "gluc",
        "HeartDisease": "cardio"
    })
    # Sex: M=1, F=0
    hd["gender"] = (hd["gender"] == "M").astype(int)
    hd["bmi"] = 26.0
    hd["diastolic_bp"] = 80.0
    hd["smoke"] = 0
    hd["alco"] = 0
    hd["active"] = 1
    hd = hd[["age", "bmi", "systolic_bp", "diastolic_bp", "cholesterol", "gluc",
              "smoke", "alco", "active", "cardio"]]
    print(f"  heartdata.csv:  {len(hd)} rows, target={hd['cardio'].value_counts().to_dict()}")

    # --- Load existing processed cardio_train ---
    existing = pd.read_csv("data/processed/heart_training_data.csv")
    # cardio_train age is in days → convert to years
    if existing["age"].mean() > 1000:
        existing["age"] = (existing["age"] / 365.25).round(0).astype(int)
    print(f"  cardio_train:   {len(existing)} rows, target={existing['cardio'].value_counts().to_dict()}")

    # --- Merge all three ---
    combined = pd.concat([existing, cld, hd], ignore_index=True)
    combined = combined.dropna(subset=["cardio"])

    # Cap outliers
    combined["systolic_bp"] = combined["systolic_bp"].clip(80, 220)
    combined["diastolic_bp"] = combined["diastolic_bp"].clip(50, 130)
    combined["cholesterol"] = combined["cholesterol"].clip(100, 400)
    combined["age"] = combined["age"].clip(18, 90)

    print(f"  Combined total: {len(combined)} rows, target={combined['cardio'].value_counts().to_dict()}")

    features = ["age", "bmi", "systolic_bp", "diastolic_bp", "cholesterol",
                "gluc", "smoke", "alco", "active"]
    X = combined[features].fillna(combined[features].median())
    y = combined["cardio"]

    # CV score
    gb = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.08,
                                     subsample=0.8, random_state=42)
    cv_scores = cross_val_score(gb, X, y, cv=5, scoring="roc_auc")
    print(f"  CV AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Full fit
    gb.fit(X, y)

    bundle = {
        "model": gb,
        "features": features,
        "auc_cv": round(float(cv_scores.mean()), 3),
        "n_rows": len(combined),
        "sources": ["cardio_train_70K", "cleveland_uci_1025", "heartdata_918"],
        "note": "Merged 3-dataset heart ML: cardio_train (Russian), Cleveland UCI, heartdata (Fedesoriano)",
    }
    out_path = MODELS_DIR / "heart_ml_v2.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"  ✅ Saved upgraded heart_ml_v2.pkl (AUC={cv_scores.mean():.3f}, N={len(combined)})")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# TASK 2: Train NHANES liver ML (9473 rows) → nhanes_liver_ml.pkl
# ══════════════════════════════════════════════════════════════════════════════
def task2_nhanes_liver():
    print("\n" + "="*60)
    print("TASK 2: Training NHANES liver ML (9473 rows)")
    print("="*60)

    # Cols: SEQN, RIDAGEYR (age), RIAGENDR (1=M,2=F),
    #       LBXSAL (albumin g/dL), LBXSATSI (AST U/L), LBXSGTSI (GGT U/L),
    #       ALT_UL (ALT), Liver_Risk_Score, AST_ALT_Ratio
    df = pd.read_csv("data/nhanes_liver_data.csv")
    print(f"  Loaded: {len(df)} rows, cols={list(df.columns)}")
    print(f"  Liver_Risk_Score stats: {df['Liver_Risk_Score'].describe().to_dict()}")
    print(f"  Liver_Risk_Score value_counts: {df['Liver_Risk_Score'].value_counts().to_dict()}")

    # Liver_Risk_Score is ordinal 1/2/3 (not 0-1):
    #   1 = low risk, 2 = moderate, 3 = high risk
    # Target: score>=2 OR any enzyme elevated
    # ALT>56 (AASLD female ULN) OR AST>40 OR GGT>60 → "liver at risk"
    df["target"] = (
        (df["LBXSATSI"] > 40) |   # AST elevated
        (df["ALT_UL"] > 56)    |   # ALT elevated
        (df["LBXSGTSI"] > 60)  |   # GGT elevated
        (df["Liver_Risk_Score"] >= 2)  # ordinal 2=moderate, 3=high
    ).astype(int)

    print(f"  Target distribution: {df['target'].value_counts().to_dict()}")

    # Features
    df["gender_enc"] = (df["RIAGENDR"] == 1).astype(float)  # 1=Male
    features = ["RIDAGEYR", "gender_enc", "LBXSAL", "LBXSATSI", "LBXSGTSI",
                "ALT_UL", "AST_ALT_Ratio", "Liver_Risk_Score"]
    feature_names = ["age", "gender", "albumin", "ast", "ggt", "alt", "ast_alt_ratio", "nhanes_score"]

    df_clean = df[features + ["target"]].dropna()
    X = df_clean[features].values
    y = df_clean["target"].values
    print(f"  Clean rows: {len(df_clean)}, features={feature_names}")

    # Train with pipeline (impute + scale + GBM)
    pipe = Pipeline([
        ("imp",   SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf",   GradientBoostingClassifier(n_estimators=150, max_depth=4,
                                              learning_rate=0.1, subsample=0.8,
                                              random_state=42))
    ])
    cv_scores = cross_val_score(pipe, X, y, cv=5, scoring="roc_auc")
    print(f"  CV AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    pipe.fit(X, y)

    bundle = {
        "model": pipe,
        "features": feature_names,
        "feature_cols": features,
        "auc_cv": round(float(cv_scores.mean()), 3),
        "n_rows": len(df_clean),
        "source": "NHANES (National Health and Nutrition Examination Survey)",
        "note": (
            "NHANES liver risk model: Age, gender, ALT, AST, GGT, albumin, AST/ALT ratio. "
            "Target: elevated enzymes (ALT>56 OR AST>40 OR GGT>60) or Liver_Risk_Score>=0.5. "
            "Used as 4th liver ensemble signal (Indian-adjacent general population)."
        ),
    }
    out_path = MODELS_DIR / "nhanes_liver_ml.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"  ✅ Saved nhanes_liver_ml.pkl (AUC={cv_scores.mean():.3f}, N={len(df_clean)})")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# TASK 3: Parse TB comorbidity CSVs → extend tb_lung_risk_by_state.json
# ══════════════════════════════════════════════════════════════════════════════
STATE_NAME_MAP = {
    "a & n islands": "andaman_and_nicobar_islands",
    "andaman & nicobar": "andaman_and_nicobar_islands",
    "andaman and nicobar islands": "andaman_and_nicobar_islands",
    "andhra pradesh": "andhra_pradesh",
    "arunachal pradesh": "arunachal_pradesh",
    "assam": "assam",
    "bihar": "bihar",
    "chandigarh": "chandigarh",
    "chhattisgarh": "chhattisgarh",
    "dadra & nagar": "dadra_and_nagar_haveli",
    "dadra and nagar haveli": "dadra_and_nagar_haveli",
    "daman & diu": "daman_and_diu",
    "delhi": "delhi",
    "goa": "goa",
    "gujarat": "gujarat",
    "haryana": "haryana",
    "himachal pradesh": "himachal_pradesh",
    "jammu & kashmir": "jammu_and_kashmir",
    "jammu and kashmir": "jammu_and_kashmir",
    "jharkhand": "jharkhand",
    "karnataka": "karnataka",
    "kerala": "kerala",
    "lakshadweep": "lakshadweep",
    "madhya pradesh": "madhya_pradesh",
    "maharashtra": "maharashtra",
    "manipur": "manipur",
    "meghalaya": "meghalaya",
    "mizoram": "mizoram",
    "nagaland": "nagaland",
    "odisha": "odisha",
    "orissa": "odisha",
    "puducherry": "puducherry",
    "pondicherry": "puducherry",
    "punjab": "punjab",
    "rajasthan": "rajasthan",
    "sikkim": "sikkim",
    "tamil nadu": "tamil_nadu",
    "telangana": "telangana",
    "tripura": "tripura",
    "uttar pradesh": "uttar_pradesh",
    "uttarakhand": "uttarakhand",
    "uttaranchal": "uttarakhand",
    "west bengal": "west_bengal",
    "india": "india_national",
    "total": "india_national",
}

def _norm_state(s):
    if not isinstance(s, str):
        return None
    s = s.strip().lower().split("(")[0].strip()
    for k, v in STATE_NAME_MAP.items():
        if k in s or s in k:
            return v
    return s.replace(" ", "_").replace("&", "and").replace("-", "_")

def task3_tb_comorbidity():
    print("\n" + "="*60)
    print("TASK 3: Parsing TB comorbidity CSVs → tb_lung_risk_by_state.json")
    print("="*60)

    # Load existing JSON
    tb_json_path = Path("data/india/tb/tb_lung_risk_by_state.json")
    with open(tb_json_path) as f:
        tb_data = json.load(f)

    states_data = tb_data.get("states", {})

    # --- 2.10 TB-Diabetes ---
    dm_df = pd.read_csv("data/india/tb/2.10_TB_Diabetes.csv")
    # Col: "Percentage  of TB - Diabetes-TB patients with known DM status,of notified)-Total"
    dm_pct_col = [c for c in dm_df.columns if "percentage" in c.lower() and "total" in c.lower()
                   and "notified" in c.lower()][0]
    print(f"  TB-DM pct col: {dm_pct_col}")
    dm_dict = {}
    for _, row in dm_df.iterrows():
        key = _norm_state(str(row["State/Uts"]))
        if key:
            try:
                dm_dict[key] = float(str(row[dm_pct_col]).replace("%","").strip())
            except Exception:
                pass

    # --- 2.11 TB-Tobacco ---
    tob_df = pd.read_csv("data/india/tb/2.11_TB_Tobacco.csv")
    tob_pct_col = [c for c in tob_df.columns if "%" in c and "total" in c.lower()
                    and "notified" in c.lower()][0]
    print(f"  TB-Tobacco pct col: {tob_pct_col}")
    tob_dict = {}
    for _, row in tob_df.iterrows():
        key = _norm_state(str(row["State/Uts"]))
        if key:
            try:
                tob_dict[key] = float(str(row[tob_pct_col]).replace("%","").strip())
            except Exception:
                pass

    # --- 2.12 TB-Alcohol ---
    alc_df = pd.read_csv("data/india/tb/2.12_TB_Alcohol.csv")
    alc_pct_col = [c for c in alc_df.columns if "%" in c and "total" in c.lower()
                    and "notified" in c.lower()][0]
    print(f"  TB-Alcohol pct col: {alc_pct_col}")
    alc_dict = {}
    for _, row in alc_df.iterrows():
        key = _norm_state(str(row["State/Uts"]))
        if key:
            try:
                alc_dict[key] = float(str(row[alc_pct_col]).replace("%","").strip())
            except Exception:
                pass

    print(f"  DM entries:      {len(dm_dict)}")
    print(f"  Tobacco entries: {len(tob_dict)}")
    print(f"  Alcohol entries: {len(alc_dict)}")

    # Merge into existing state entries + create new ones for all states found
    all_keys = set(dm_dict) | set(tob_dict) | set(alc_dict)
    for key in all_keys:
        if key not in states_data:
            states_data[key] = {}
        if key in dm_dict and dm_dict[key] > 0:
            states_data[key]["tb_diabetes_pct"]  = round(dm_dict[key], 1)
        if key in tob_dict and tob_dict[key] > 0:
            states_data[key]["tb_tobacco_pct"]   = round(tob_dict[key], 1)
        if key in alc_dict and alc_dict[key] > 0:
            states_data[key]["tb_alcohol_pct"]   = round(alc_dict[key], 1)
        # Augment lung risk multiplier: states with high TB-DM (>30%) get extra 0.05 multiplier bump
        dm_pct = dm_dict.get(key, 0)
        if dm_pct > 30:
            existing_mult = states_data[key].get("lung_tb_risk_multiplier", 1.0)
            states_data[key]["lung_tb_risk_multiplier"] = round(
                min(1.30, existing_mult + 0.03), 3
            )

    tb_data["states"] = states_data
    tb_data["tb_comorbidity_sources"] = {
        "tb_diabetes":  "NTEP Annual Report 2021-22 — Table 2.10: TB-DM % of notified patients by state",
        "tb_tobacco":   "NTEP Annual Report 2021-22 — Table 2.11: TB-Tobacco % by state",
        "tb_alcohol":   "NTEP Annual Report 2021-22 — Table 2.12: TB-Alcohol % by state",
        "note": (
            "TB-DM comorbidity: 25–35% of TB patients in India have DM (ICMR/WHO). "
            "High TB-DM states get +0.03 lung_tb_risk_multiplier adjustment. "
            "Useful for diabetes model: DM worsens TB outcome and vice versa."
        )
    }

    with open(tb_json_path, "w") as f:
        json.dump(tb_data, f, indent=2)
    print(f"  ✅ Updated tb_lung_risk_by_state.json with {len(all_keys)} state TB-comorbidity records")

    # Show sample
    sample_states = ["kerala", "delhi", "maharashtra", "uttar_pradesh"]
    for s in sample_states:
        d = states_data.get(s, {})
        print(f"    {s}: DM={d.get('tb_diabetes_pct','?')}%  Tob={d.get('tb_tobacco_pct','?')}%  "
              f"Alc={d.get('tb_alcohol_pct','?')}%  mult={d.get('lung_tb_risk_multiplier','?')}")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# TASK 4: NFHS-5 district data → district_health_priors.json
# ══════════════════════════════════════════════════════════════════════════════
def task4_nfhs5_district_priors():
    print("\n" + "="*60)
    print("TASK 4: Building district_health_priors.json from NFHS-5")
    print("="*60)

    df = pd.read_csv("data/india/population/datafile.csv")
    print(f"  Loaded: {len(df)} rows, {len(df.columns)} cols")

    # Extract relevant columns (with partial matching for robustness)
    def find_col(df, keywords, require_all=False):
        kw_lower = [k.lower() for k in keywords]
        for col in df.columns:
            col_l = col.lower()
            if require_all:
                if all(k in col_l for k in kw_lower):
                    return col
            else:
                if any(k in col_l for k in kw_lower):
                    return col
        return None

    col_district  = "District Names"
    col_state     = "State/UT"
    col_fuel      = find_col(df, ["clean fuel", "cooking"], require_all=True)
    col_bmi_low   = find_col(df, ["bmi", "below normal"], require_all=True)
    col_overweight= find_col(df, ["overweight", "obese"], require_all=True)
    col_bp_women  = find_col(df, ["elevated blood pressure", "women"], require_all=True)
    col_sugar_women= find_col(df, ["high or very high", "blood sugar", "women"], require_all=True)
    col_anaemia   = find_col(df, ["all women", "anaemic"], require_all=True)
    col_tobacco_women = find_col(df, ["tobacco", "women"], require_all=True)
    col_alcohol_men   = find_col(df, ["alcohol", "men"], require_all=True)

    print(f"  Columns mapped:")
    for name, col in [("clean_fuel", col_fuel), ("bmi_low", col_bmi_low),
                       ("overweight", col_overweight), ("bp_women", col_bp_women),
                       ("blood_sugar_women", col_sugar_women), ("anaemia", col_anaemia),
                       ("tobacco_women", col_tobacco_women), ("alcohol_men", col_alcohol_men)]:
        print(f"    {name}: {col}")

    out = {}
    n_districts = 0
    for _, row in df.iterrows():
        district = str(row.get(col_district, "")).strip()
        state    = str(row.get(col_state,    "")).strip()
        if not district or district == "nan":
            continue

        def safe_pct(col):
            if col is None:
                return None
            try:
                v = float(str(row[col]).replace("%","").replace(",","").strip())
                return round(v, 1) if 0 <= v <= 100 else None
            except Exception:
                return None

        entry = {
            "state":              state,
            "clean_fuel_pct":     safe_pct(col_fuel),
            "bmi_below_normal_pct": safe_pct(col_bmi_low),
            "overweight_pct":     safe_pct(col_overweight),
            "high_bp_women_pct":  safe_pct(col_bp_women),
            "high_sugar_women_pct": safe_pct(col_sugar_women),
            "anaemia_all_women_pct": safe_pct(col_anaemia),
            "tobacco_women_pct":  safe_pct(col_tobacco_women),
            "alcohol_men_pct":    safe_pct(col_alcohol_men),
        }
        # Compute composite risk scores for quick lookup
        # Heart/BP risk: high_bp_pct / 100 * 0.6 + high_sugar_pct / 100 * 0.4
        bp_v   = (entry["high_bp_women_pct"] or 20) / 100
        sug_v  = (entry["high_sugar_women_pct"] or 15) / 100
        fuel_v = 1.0 - ((entry["clean_fuel_pct"] or 50) / 100)
        entry["composite_cardio_risk"]    = round(bp_v * 0.60 + sug_v * 0.40, 3)
        entry["indoor_air_pollution_risk"] = round(fuel_v * 0.25, 3)  # max 0.25

        district_key = district.lower().replace(" ", "_")
        out[district_key] = entry
        n_districts += 1

    priors = {
        "source": "NFHS-5 (National Family Health Survey 5, 2019-21), MoHFW India",
        "coverage": f"{n_districts} districts",
        "note": (
            "District-level health priors for heart, kidney, lungs risk adjustment. "
            "composite_cardio_risk: weighted BP (60%) + blood sugar (40%). "
            "indoor_air_pollution_risk: cooking fuel risk proxy (1-clean_fuel_pct)*0.25. "
            "Use for district-level baseline adjustment when user provides district."
        ),
        "districts": out,
    }

    out_path = Path("data/india/population/district_health_priors.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(priors, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Saved district_health_priors.json — {n_districts} districts")

    # Show 3 sample districts
    sample = list(out.items())[:3]
    for dname, ddata in sample:
        print(f"    {dname} ({ddata['state']}): "
              f"fuel={ddata['clean_fuel_pct']}%  BP={ddata['high_bp_women_pct']}%  "
              f"sugar={ddata['high_sugar_women_pct']}%  cardio_risk={ddata['composite_cardio_risk']}")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    results = {}

    try:
        results["heart_upgrade"] = task1_upgrade_heart_ml()
    except Exception as e:
        print(f"  ❌ TASK 1 FAILED: {e}")
        results["heart_upgrade"] = False

    try:
        results["nhanes_liver"] = task2_nhanes_liver()
    except Exception as e:
        print(f"  ❌ TASK 2 FAILED: {e}")
        results["nhanes_liver"] = False

    try:
        results["tb_comorbidity"] = task3_tb_comorbidity()
    except Exception as e:
        print(f"  ❌ TASK 3 FAILED: {e}")
        import traceback; traceback.print_exc()
        results["tb_comorbidity"] = False

    try:
        results["nfhs5_district"] = task4_nfhs5_district_priors()
    except Exception as e:
        print(f"  ❌ TASK 4 FAILED: {e}")
        import traceback; traceback.print_exc()
        results["nfhs5_district"] = False

    print("\n" + "="*60)
    print("INTEGRATION SUMMARY")
    print("="*60)
    for task, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {task}: {'OK' if ok else 'FAILED'}")

    print("\nNext steps:")
    print("  1. Wire nhanes_liver_ml.pkl into liver_model.py as 4th ensemble signal")
    print("  2. Wire district_health_priors.json into heart_model.py/kidney_model.py")
    print("  3. Wire TB comorbidity fields (tb_diabetes_pct etc.) into lungs_model.py")
    print("  4. Run: python smoke_test.py")
