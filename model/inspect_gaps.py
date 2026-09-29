"""Inspect available datasets to fix all trust limitations."""
import pandas as pd, os
from pathlib import Path

# 1. Kidney UCI (Indian patients from various hospitals)
print("=== KIDNEY DISEASE.CSV ===")
ckd = pd.read_csv("data/india/kidney/kidney_disease.csv")
print(f"Shape: {ckd.shape}")
print(f"Cols: {list(ckd.columns)}")
last_col = ckd.columns[-1]
print(f"Target col: {last_col}")
print(f"Target dist: {ckd[last_col].value_counts().to_dict()}")
print()

# 2. Diabetes dataset
print("=== DIABETES PREDICTION DATASET ===")
diab = pd.read_csv("data/india/diabaties/diabetes_prediction_dataset.csv")
print(f"Shape: {diab.shape}")
print(f"Cols: {list(diab.columns)}")
last_col2 = diab.columns[-1]
print(f"Target dist: {diab[last_col2].value_counts().to_dict()}")
print()

# 3. Alzheimer dataset
print("=== ALZHEIMER DATASET ===")
alz = pd.read_csv("data/india/brain/alzheimers_disease_data.csv")
print(f"Shape: {alz.shape}")
print(f"Cols (first 15): {list(alz.columns[:15])}")
print()

# 4. NHANES full labs columns
print("=== NHANES LABS (full) ===")
nhanes_labs = Path("data/india/population/National Health and Nutrition Examination Survey/labs.csv")
labs = pd.read_csv(nhanes_labs, nrows=5)
print(f"Shape (5 rows shown): {labs.shape}")
print(f"Cols (first 30): {list(labs.columns[:30])}")
print()

# 5. NHANES demographic
print("=== NHANES DEMOGRAPHIC ===")
nhanes_demo = Path("data/india/population/National Health and Nutrition Examination Survey/demographic.csv")
demo = pd.read_csv(nhanes_demo, nrows=5)
print(f"Cols: {list(demo.columns[:20])}")
print()

# 6. Kidney models existing
print("=== EXISTING KIDNEY MODELS ===")
import pickle
for pkl in Path("models").glob("kidney*.pkl"):
    with open(pkl, "rb") as f:
        b = pickle.load(f)
    print(f"  {pkl.name}: features={b.get('features', b.get('feature_names', '?'))}")
    print(f"    auc={b.get('auc_cv', b.get('cv_auc', '?'))}  n={b.get('n_rows', '?')}")
