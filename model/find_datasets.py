import urllib.request, json, io, csv, os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "india"

# ── Check what's already in our data folder ──────────────────────────────────
print("=" * 60)
print("EXISTING DATA FILES IN PROJECT")
print("=" * 60)
for root, dirs, files in os.walk(Path(__file__).parent / "data"):
    for f in files:
        fp = Path(root) / f
        size = fp.stat().st_size // 1024
        print(f"  {size:5d}KB  {fp.relative_to(Path(__file__).parent)}")

# ── Try OpenML API ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("OPENML API - FINDING DATASETS")
print("=" * 60)

openml_ids = {
    "Heart Disease": 53,
    "Diabetes PIMA": 37,
    "CKD Apollo":    1453,
    "Liver Bupa":    8,
    "Stroke":        43208,
}

for name, did in openml_ids.items():
    try:
        url = f"https://api.openml.org/api/v1/json/data/{did}"
        r = urllib.request.urlopen(url, timeout=8)
        d = json.loads(r.read())
        ds = d.get("data_set_description", {})
        rows = ds.get("number_instances", "?")
        cols = ds.get("number_features", "?")
        fid  = ds.get("file_id", "?")
        dname = ds.get("name", "?")
        print(f"  OK  {name}: name={dname} rows={rows} cols={cols} file_id={fid}")
    except Exception as e:
        print(f"  FAIL {name}: {str(e)[:60]}")

# ── Try direct downloads of confirmed working URLs ────────────────────────────
print("\n" + "=" * 60)
print("DIRECT DOWNLOAD TESTS")
print("=" * 60)

direct_urls = {
    "PIMA Diabetes (768 South Asian women)":
        "https://raw.githubusercontent.com/npradaschnor/Pima-Indians-Diabetes-Dataset/master/diabetes.csv",
    "Cleveland Heart Disease (303 pts)":
        "https://raw.githubusercontent.com/kb22/Heart-Disease-Prediction/master/dataset.csv",
    "Cleveland Heart v2":
        "https://raw.githubusercontent.com/dsrscientist/dataset1/master/heart_disease.csv",
    "Framingham Heart Study (4238 pts)":
        "https://raw.githubusercontent.com/ManishJoc14/framingham-heart-disease/master/framingham.csv",
    "Stroke prediction (5110 pts)":
        "https://raw.githubusercontent.com/dsrscientist/dataset1/master/stroke.csv",
    "Indian Heart Disease Kaggle":
        "https://raw.githubusercontent.com/Arjun-Narula/Cardiovascular-Disease-Detection/main/heart.csv",
    "Hypertension risk dataset":
        "https://raw.githubusercontent.com/Naivedya-Rai/Hypertension-Dataset/main/hypertension_data.csv",
    "Diabetes 130 hospitals India-like":
        "https://raw.githubusercontent.com/dsrscientist/dataset1/master/diabetes_data_upload.csv",
}

working = {}
for name, url in direct_urls.items():
    try:
        r = urllib.request.urlopen(url, timeout=7)
        content = r.read()
        size = len(content)
        first_line = content.decode("utf-8", errors="ignore").split("\n")[0]
        print(f"  OK  [{size//1024}KB] {name}")
        print(f"       cols: {first_line[:80]}")
        working[name] = (url, size, first_line)
    except Exception as e:
        print(f"  FAIL {name}: {str(e)[:55]}")

print(f"\n  Working downloads: {len(working)}/{len(direct_urls)}")
