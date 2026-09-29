"""
Deep accuracy diagnostic — find remaining gaps across all 5 models.
Tests 4 representative patient profiles to surface any remaining issues.
"""
import sys, warnings
sys.path.insert(0, ".")
warnings.filterwarnings("ignore")

from models.heart_model import HeartModel
from models.brain_model import BrainModel
from models.liver_model import LiverModel
from models.lungs_model import LungsModel
from models.kidney_model import KidneyModel

hm = HeartModel()
bm = BrainModel()
lm = LiverModel()
lu = LungsModel()
km = KidneyModel()

ISSUES = []

def show(label, results):
    print(f"\n{'─'*55}")
    print(f"  {label}")
    print(f"{'─'*55}")
    for name, r in results:
        flag = ""
        score = r["health_score"]
        level = r["risk_level"]
        # Automatic issue detection
        if label.startswith("PERFECT") and level != "GREEN":
            flag = "  ⚠️  EXPECTED GREEN"
            ISSUES.append(f"{label} | {name}: level={level} score={score} — expected GREEN")
        if label.startswith("PERFECT") and score < 78:
            flag = f"  ⚠️  SCORE TOO LOW"
            ISSUES.append(f"{label} | {name}: score={score} — expected >=78 for perfect health")
        if label.startswith("HIGH RISK") and level == "GREEN":
            flag = "  ⚠️  EXPECTED YELLOW/RED"
            ISSUES.append(f"{label} | {name}: level=GREEN score={score} — expected YELLOW or RED")
        if label.startswith("HIGH RISK") and score > 65:
            flag = f"  ⚠️  SCORE TOO HIGH"
            ISSUES.append(f"{label} | {name}: score={score} — expected <65 for high-risk profile")
        if label.startswith("19YO") and level == "RED":
            flag = "  ⚠️  TOO HIGH FOR TEEN"
            ISSUES.append(f"{label} | {name}: level=RED score={score} — too aggressive for healthy 19yo")
        if label.startswith("19YO") and score < 72:
            flag = f"  ⚠️  SCORE TOO LOW"
            ISSUES.append(f"{label} | {name}: score={score} — expected >=72 for healthy 19yo")
        print(f"  {name:8s}  score={score:3d}  level={level:6s}  risk={r['current_risk']:.3f}  method={r['method_used'][:35]}{flag}")

# ── PROFILE 1: Perfect health 25yo male ────────────────────────────────────
p1 = {
    "ProfileInfo": {"Age": 25, "Gender": "Male", "ActivityLevel": "Active", "Diet": "Good"},
    "HealthInfo":  {
        "Smoking": "Never", "Alcohol": "Never", "Bmi": 21, "Sleep": 8, "Stress": "Low",
        "TotalCholesterol": 165, "HDLCholesterol": 62, "SystolicBP": 110, "DiastolicBP": 70,
        "FastingGlucose": 85, "AST": 22, "ALT": 18, "Albumin": 4.5,
        "SerumCreatinine": 0.85, "eGFR": 102, "City": "pune"
    }
}
show("PERFECT HEALTH 25yo MALE (full labs)", [
    ("Heart", hm.calculate_risk(p1)),
    ("Brain", bm.calculate_risk(p1)),
    ("Liver", lm.calculate_risk(p1)),
    ("Lungs", lu.calculate_risk(p1)),
    ("Kidney", km.calculate_risk(p1)),
])

# ── PROFILE 2: 40yo moderate risk ──────────────────────────────────────────
p2 = {
    "ProfileInfo": {"Age": 40, "Gender": "Male", "ActivityLevel": "Sedentary", "Diet": "Poor"},
    "HealthInfo":  {
        "Smoking": "Occasional", "Alcohol": "Weekly", "Bmi": 27, "Sleep": 6, "Stress": "High",
        "TotalCholesterol": 220, "HDLCholesterol": 38, "SystolicBP": 135, "DiastolicBP": 86,
        "FastingGlucose": 105, "City": "delhi"
    }
}
show("MODERATE RISK 40yo MALE (no labs, Delhi)", [
    ("Heart", hm.calculate_risk(p2)),
    ("Brain", bm.calculate_risk(p2)),
    ("Liver", lm.calculate_risk(p2)),
    ("Lungs", lu.calculate_risk(p2)),
    ("Kidney", km.calculate_risk(p2)),
])

# ── PROFILE 3: 60yo HIGH risk ──────────────────────────────────────────────
p3 = {
    "ProfileInfo": {"Age": 60, "Gender": "Male", "ActivityLevel": "Sedentary", "Diet": "Poor"},
    "HealthInfo":  {
        "Smoking": "Daily", "Alcohol": "Daily", "Bmi": 31, "Sleep": 5, "Stress": "High",
        "SystolicBP": 162, "DiastolicBP": 100, "HbA1c": 9.2,
        "AST": 65, "ALT": 72, "Albumin": 3.1,
        "TotalCholesterol": 270, "HDLCholesterol": 28,
        "SerumCreatinine": 1.8, "eGFR": 42,
        "Triglycerides": 310, "City": "delhi"
    }
}
show("HIGH RISK 60yo MALE (full labs)", [
    ("Heart", hm.calculate_risk(p3)),
    ("Brain", bm.calculate_risk(p3)),
    ("Liver", lm.calculate_risk(p3)),
    ("Lungs", lu.calculate_risk(p3)),
    ("Kidney", km.calculate_risk(p3)),
])

# ── PROFILE 4: 19yo healthy female (no labs) ───────────────────────────────
p4 = {
    "ProfileInfo": {"Age": 19, "Gender": "Female", "ActivityLevel": "Active", "Diet": "Good"},
    "HealthInfo":  {
        "Smoking": "Never", "Alcohol": "Never", "Bmi": 20, "Sleep": 8, "Stress": "Low"
    }
}
show("19YO HEALTHY FEMALE (no labs)", [
    ("Heart", hm.calculate_risk(p4)),
    ("Brain", bm.calculate_risk(p4)),
    ("Liver", lm.calculate_risk(p4)),
    ("Lungs", lu.calculate_risk(p4)),
    ("Kidney", km.calculate_risk(p4)),
])

# ── PROFILE 5: 35yo female, pregnancy-age, normal everything ───────────────
p5 = {
    "ProfileInfo": {"Age": 35, "Gender": "Female", "ActivityLevel": "Moderate", "Diet": "Average"},
    "HealthInfo":  {
        "Smoking": "Never", "Alcohol": "Never", "Bmi": 23, "Sleep": 7, "Stress": "Medium",
        "TotalCholesterol": 185, "HDLCholesterol": 58, "SystolicBP": 118,
        "AST": 25, "ALT": 22, "Albumin": 4.1, "SerumCreatinine": 0.75
    }
}
show("NORMAL HEALTH 35yo FEMALE (partial labs)", [
    ("Heart", hm.calculate_risk(p5)),
    ("Brain", bm.calculate_risk(p5)),
    ("Liver", lm.calculate_risk(p5)),
    ("Lungs", lu.calculate_risk(p5)),
    ("Kidney", km.calculate_risk(p5)),
])

# ── SUMMARY ────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
if ISSUES:
    print(f"⚠️  {len(ISSUES)} accuracy issue(s) found:")
    for i in ISSUES:
        print(f"  • {i}")
else:
    print("✅  No accuracy issues detected across all profiles.")
