import pandas as pd
import json
from pathlib import Path

BASE = Path(__file__).parent

print("=" * 65)
print("1. cardio_train.csv  (cardiovascular disease — likely Kaggle/Russia)")
print("=" * 65)
try:
    df = pd.read_csv(BASE / "data/india/heart/cardio_train.csv", sep=None, engine='python', nrows=5)
    print(f"   Rows (full): {sum(1 for _ in open(BASE / 'data/india/heart/cardio_train.csv'))-1}")
    print(f"   Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"   Sample row:\n{df.iloc[0].to_dict()}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 65)
print("2. healthcare-dataset-stroke-data.csv  (Kaggle stroke dataset)")
print("=" * 65)
try:
    df2 = pd.read_csv(BASE / "data/india/heart/healthcare-dataset-stroke-data.csv", nrows=5)
    total = sum(1 for _ in open(BASE / "data/india/heart/healthcare-dataset-stroke-data.csv"))-1
    print(f"   Rows: {total}")
    print(f"   Columns ({len(df2.columns)}): {list(df2.columns)}")
    print(f"   Gender counts: {pd.read_csv(BASE / 'data/india/heart/healthcare-dataset-stroke-data.csv')['gender'].value_counts().to_dict()}")
    print(f"   Stroke rate: {pd.read_csv(BASE / 'data/india/heart/healthcare-dataset-stroke-data.csv')['stroke'].mean():.3f}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 65)
print("3. survey lung cancer.csv")
print("=" * 65)
try:
    df3 = pd.read_csv(BASE / "data/india/lung/survey lung cancer.csv", nrows=5)
    total = sum(1 for _ in open(BASE / "data/india/lung/survey lung cancer.csv"))-1
    print(f"   Rows: {total}")
    print(f"   Columns ({len(df3.columns)}): {list(df3.columns)}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 65)
print("4. TB datasets")
print("=" * 65)
for tb_file in ["2.10_TB_Diabetes.csv", "2.11_TB_Tobacco.csv", "2.12_TB_Alcohol.csv"]:
    try:
        df4 = pd.read_csv(BASE / f"data/india/tb/{tb_file}")
        print(f"   {tb_file}: {len(df4)} rows x {len(df4.columns)} cols")
        print(f"   Columns: {list(df4.columns)[:8]}")
    except Exception as e:
        print(f"   {tb_file}: ERROR {e}")

print()
print("=" * 65)
print("5. NFHS_5_India_Districts_Factsheet_Data.xls")
print("=" * 65)
try:
    xl = pd.ExcelFile(BASE / "data/india/lung/NFHS_5_India_Districts_Factsheet_Data.xls")
    print(f"   Sheets ({len(xl.sheet_names)}): {xl.sheet_names[:5]}")
    df5 = xl.parse(xl.sheet_names[0], nrows=5)
    print(f"   First sheet shape: {df5.shape}")
    print(f"   First 8 cols: {list(df5.columns[:8])}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 65)
print("6. data/processed/heart_training_data.csv (1.9MB)")
print("=" * 65)
try:
    df6 = pd.read_csv(BASE / "data/processed/heart_training_data.csv", nrows=5)
    total = sum(1 for _ in open(BASE / "data/processed/heart_training_data.csv"))-1
    print(f"   Rows: {total}")
    print(f"   Columns ({len(df6.columns)}): {list(df6.columns)[:10]}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 65)
print("7. data/liver_dataset.csv (111KB)")
print("=" * 65)
try:
    df7 = pd.read_csv(BASE / "data/liver_dataset.csv", nrows=5)
    total = sum(1 for _ in open(BASE / "data/liver_dataset.csv"))-1
    print(f"   Rows: {total}")
    print(f"   Columns ({len(df7.columns)}): {list(df7.columns)}")
except Exception as e:
    print(f"   ERROR: {e}")
