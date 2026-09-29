"""inspect_datasets.py — audit all data files vs what models currently use."""
import pandas as pd

print("=" * 60)
print("CURRENTLY USED BY MODELS (pkl files exist)")
print("=" * 60)
used = [
    ("heart_ml_v2.pkl",      "heart model — cardio_train.csv (70K) via processed/heart_training_data.csv"),
    ("interheart_india.pkl",  "heart model — InterHEART India-specific"),
    ("stroke_ml.pkl",         "brain model — healthcare-dataset-stroke-data.csv (5110)"),
    ("alzheimer_ml.pkl",      "brain model — alzheimers_disease_data.csv (2149)"),
    ("liver_lpd_ml.pkl",      "liver model — LPD_train.csv (30K)"),
    ("diabetes_ml.pkl",       "kidney/shared — diabetes dataset"),
    ("kidney_ml.pkl",         "kidney model — kidney_disease.csv (400)"),
    ("kidney_full_ml.pkl",    "kidney model — full feature set"),
    ("lung_cancer_ml.pkl",    "lungs model — survey lung cancer.csv (309)"),
    ("nhanes_bioage_params.pkl", "biological age — NHANES"),
]
for pkl, desc in used:
    print(f"  ✅ {pkl}: {desc}")

print()
print("=" * 60)
print("DATA FILES — ROW COUNTS & STATUS")
print("=" * 60)

datasets = [
    ("data/india/brain/alzheimers_disease_data.csv",     None,  "✅ USED (alzheimer_ml.pkl)"),
    ("data/india/heart/cardio_train.csv",                 ";",   "✅ USED (heart_ml_v2.pkl via processed)"),
    ("data/india/heart/healthcare-dataset-stroke-data.csv", None,"✅ USED (stroke_ml.pkl)"),
    ("data/india/heart/heart.csv",                        None,  "⚠️ NOT USED — Cleveland UCI 1025 rows"),
    ("data/india/heart/heartdata.csv",                    None,  "⚠️ NOT USED — 918 rows, 12 features"),
    ("data/india/kidney/kidney_disease.csv",              None,  "✅ USED (kidney_ml.pkl)"),
    ("data/india/liver/Indian Liver Patient Dataset (ILPD).csv", None, "✅ USED (liver_ilpd_model.pkl)"),
    ("data/india/lung/survey lung cancer.csv",            None,  "✅ USED (lung_cancer_ml.pkl)"),
    ("data/india/diabaties/diabetes_prediction_dataset.csv", None,"✅ USED (diabetes_ml.pkl)"),
    ("data/liver_dataset.csv",                            None,  "✅ USED (liver Turkish NASH model)"),
    ("data/nhanes_liver_data.csv",                        None,  "⚠️ NOT USED — NHANES 9473 rows (ALT/AST/albumin)"),
    ("data/india/population/datafile.csv",                None,  "⚠️ NOT USED — NFHS-5 district 706 rows"),
    ("data/india/tb/2.10_TB_Diabetes.csv",                None,  "⚠️ NOT USED — TB-Diabetes state data"),
    ("data/india/tb/2.11_TB_Tobacco.csv",                 None,  "⚠️ NOT USED — TB-Tobacco state data"),
    ("data/india/tb/2.12_TB_Alcohol.csv",                 None,  "⚠️ NOT USED — TB-Alcohol state data"),
    ("data/processed/heart_training_data.csv",            None,  "✅ USED — processed cardio_train"),
    ("data/processed/liver_training_data.csv",            None,  "✅ USED — processed liver"),
]

for path, sep, status in datasets:
    try:
        kw = {"sep": sep} if sep else {}
        df = pd.read_csv(path, **kw)
        print(f"  {status}")
        print(f"    {path}")
        print(f"    rows={len(df)} cols={len(df.columns)}: {list(df.columns[:6])}...")
    except Exception as e:
        print(f"  ERROR reading {path}: {e}")
    print()

print("=" * 60)
print("NOT-YET-USED DATASETS — POTENTIAL INTEGRATIONS")
print("=" * 60)
print("""
1. data/india/heart/heart.csv         (1025 rows, Cleveland UCI)
   data/india/heart/heartdata.csv     (918 rows, 12 features)
   → Merge with existing heart training to boost ensemble.
   → Features: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal/target
   → ACTION: retrain heart_ml_v2 with merged Cleveland+cardio_train+heartdata

2. data/nhanes_liver_data.csv         (9473 rows, NHANES)
   → Has ALT, AST, albumin, GGT, Liver_Risk_Score, AST_ALT_Ratio
   → ACTION: train nhanes_liver_ml.pkl → add as 4th liver ensemble signal

3. data/india/population/datafile.csv (706 rows, NFHS-5 districts)
   → Has: clean_fuel_pct, BMI_below_normal, overweight, high_BP, high_blood_sugar by district
   → ACTION: use as district-level priors for heart/kidney/diabetes risk lookup

4. data/india/tb/2.10_TB_Diabetes.csv  (37 states)
   data/india/tb/2.11_TB_Tobacco.csv   (37 states)
   data/india/tb/2.12_TB_Alcohol.csv   (37 states)
   → State-level TB comorbidity rates — diabetes%, tobacco%, alcohol% of TB patients
   → ACTION: extend tb_lung_risk_by_state.json with these co-morbidity rates
             use in lungs model for better TB-related risk adjustment

5. data/india/heart/heart.csv + heartdata.csv
   → Can augment stroke model (shared features: age, BP, cholesterol, BMI)
""")
