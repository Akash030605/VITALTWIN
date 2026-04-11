"""
Comprehensive test suite for all 5 organ models.
Verifies all clinical fixes applied 2026-04-11:
  Fix 1: Heart  — INTERHEART abdominal obesity BMI >25 → >=27.5 (WHO Asia-Pacific 2004)
  Fix 2: Brain  — Stroke ML India factor not double-applied with INTERSTROKE
  Fix 3: Liver  — GGT penalty fires only at >60 U/L in isolation (Kwo 2017 AASLD)
  Fix 4: Lungs  — Delhi daily smoker now YELLOW not GREEN (Salvi Lancet 2009)
"""
import sys
sys.path.insert(0, ".")

PASS = 0
FAIL = 0

def check(name, condition, got, expected_desc):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name} — got {got}, expected {expected_desc}")
        FAIL += 1

# ─────────────────────────────────────────────────────────────
print("\n=== HEART MODEL ===")
from models.heart_model import HeartModel
hm = HeartModel()

# H1: Healthy young person — no risk factors, BMI 26 (overweight but <27.5)
# Before fix: BMI>25 triggered INTERHEART abdominal obesity OR 1.62 → inflated score
# After fix:  BMI 26 < 27.5 → no abdominal obesity penalty → GREEN
r = hm.calculate_risk({"ProfileInfo": {"Age": 32, "Gender": "Male", "ActivityLevel": "Active"},
                        "HealthInfo":  {"Smoking": "Never", "Alcohol": "Never", "Bmi": 26,
                                        "TotalCholesterol": 180, "HDLCholesterol": 55,
                                        "SystolicBP": 118, "DiastolicBP": 76}})
check("H1: 32yo healthy male BMI=26 — should be GREEN",
      r["risk_level"] == "GREEN", r["risk_level"], "GREEN")
check("H1: score ≥ 75",
      r["health_score"] >= 75, r["health_score"], ">= 75")

# H2: BMI 28 (≥27.5) — now triggers abdominal obesity penalty correctly
r2 = hm.calculate_risk({"ProfileInfo": {"Age": 45, "Gender": "Male", "ActivityLevel": "Moderate"},
                         "HealthInfo":  {"Smoking": "Never", "Bmi": 28,
                                         "TotalCholesterol": 200, "HDLCholesterol": 45,
                                         "SystolicBP": 130, "DiastolicBP": 84}})
check("H2: 45yo male BMI=28 should score lower than H1",
      r2["health_score"] < r["health_score"], r2["health_score"], f"< {r['health_score']}")

# H3: High-risk — diabetes + smoking + hypertension → RED or deep YELLOW
r3 = hm.calculate_risk({"ProfileInfo": {"Age": 55, "Gender": "Male", "ActivityLevel": "Sedentary"},
                         "HealthInfo":  {"Smoking": "Daily", "Alcohol": "Daily",
                                         "Bmi": 30, "HbA1c": 8.5,
                                         "TotalCholesterol": 260, "HDLCholesterol": 32,
                                         "SystolicBP": 155, "DiastolicBP": 96}})
check("H3: 55yo diabetic smoker HTN — must be YELLOW or RED",
      r3["risk_level"] in ("YELLOW", "RED"), r3["risk_level"], "YELLOW or RED")
check("H3: score < 65",
      r3["health_score"] < 65, r3["health_score"], "< 65")

# ─────────────────────────────────────────────────────────────
print("\n=== BRAIN MODEL ===")
from models.brain_model import BrainModel
bm = BrainModel()

# B1: Young healthy person — before fix stroke ML was ×1.28 extra on top of INTERSTROKE
# After fix: stroke_ml_risk = raw_prob (no double India factor) → lower risk for healthy person
r = bm.calculate_risk({"ProfileInfo": {"Age": 28, "Gender": "Male", "ActivityLevel": "Active"},
                        "HealthInfo":  {"Smoking": "Never", "Stress": "Low",
                                        "SystolicBP": 115, "DiastolicBP": 72,
                                        "Sleep": 8}})
check("B1: 28yo healthy male — should be GREEN",
      r["risk_level"] == "GREEN", r["risk_level"], "GREEN")
check("B1: score ≥ 78",
      r["health_score"] >= 78, r["health_score"], ">= 78")

# B2: Multiple risk factors — should be YELLOW or RED
r2 = bm.calculate_risk({"ProfileInfo": {"Age": 62, "Gender": "Male", "ActivityLevel": "Sedentary"},
                         "HealthInfo":  {"Smoking": "Daily", "Stress": "High",
                                         "SystolicBP": 158, "DiastolicBP": 98,
                                         "Sleep": 5, "HbA1c": 8.0,
                                         "BPOnMedication": True}})
check("B2: 62yo HTN diabetic smoker — must be YELLOW or RED",
      r2["risk_level"] in ("YELLOW", "RED"), r2["risk_level"], "YELLOW or RED")
check("B2: score < 60",
      r2["health_score"] < 60, r2["health_score"], "< 60")

# B3: Young person without clinical inputs — should not get artificially high brain risk
r3 = bm.calculate_risk({"ProfileInfo": {"Age": 22, "Gender": "Female", "ActivityLevel": "Active"},
                         "HealthInfo":  {"Smoking": "Never", "Stress": "Medium", "Sleep": 8}})
check("B3: 22yo healthy female — must be GREEN",
      r3["risk_level"] == "GREEN", r3["risk_level"], "GREEN")
check("B3: score ≥ 80",
      r3["health_score"] >= 80, r3["health_score"], ">= 80")

# ─────────────────────────────────────────────────────────────
print("\n=== LIVER MODEL ===")
from models.liver_model import LiverModel
lm = LiverModel()

# L1: Isolated GGT=52 (48-60 range), no AST/ALT — before fix would get ggt_penalty=0.01
# After fix: isolated mild GGT without transaminases = no penalty
r = lm.calculate_risk({"ProfileInfo": {"Age": 35, "Gender": "Male"},
                        "HealthInfo":  {"GGT": 52, "Alcohol": "Never", "Bmi": 22}})
print(f"  INFO  L1 GGT=52 isolated: score={r['health_score']}, risk={r['current_risk']:.3f}")
check("L1: GGT=52 isolated (no AST/ALT) — should be GREEN or high YELLOW",
      r["health_score"] >= 70, r["health_score"], ">= 70")

# L2: GGT=52 WITH elevated AST=55 — should still get penalty (concurrent transaminase)
r2 = lm.calculate_risk({"ProfileInfo": {"Age": 42, "Gender": "Male"},
                         "HealthInfo":  {"GGT": 52, "AST": 55, "ALT": 45, "Alcohol": "Weekly"}})
print(f"  INFO  L2 GGT=52 + AST=55: score={r2['health_score']}, level={r2['risk_level']}")
check("L2: GGT=52 + AST elevated — should score lower than L1 (penalty applies)",
      r2["health_score"] < r["health_score"], r2["health_score"], f"< {r['health_score']}")

# L3: GGT=120 (>100) — should still get full penalty regardless
r3 = lm.calculate_risk({"ProfileInfo": {"Age": 50, "Gender": "Male"},
                         "HealthInfo":  {"GGT": 120, "AST": 80, "ALT": 75, "Alcohol": "Daily"}})
check("L3: GGT=120 + daily alcohol + elevated enzymes — must be YELLOW or RED",
      r3["risk_level"] in ("YELLOW", "RED"), r3["risk_level"], "YELLOW or RED")

# L4: Healthy labs — should remain GREEN regardless of other factors
r4 = lm.calculate_risk({"ProfileInfo": {"Age": 30, "Gender": "Female"},
                         "HealthInfo":  {"AST": 22, "ALT": 18, "Albumin": 4.2,
                                         "GGT": 25, "Alcohol": "Never"}})
check("L4: Normal AST/ALT/Albumin — must be GREEN",
      r4["risk_level"] == "GREEN", r4["risk_level"], "GREEN")
check("L4: score ≥ 80",
      r4["health_score"] >= 80, r4["health_score"], ">= 80")

# ─────────────────────────────────────────────────────────────
print("\n=== LUNGS MODEL ===")
from models.lungs_model import LungsModel
lm_lungs = LungsModel()

# LU1: Delhi daily smoker — previously GREEN (bug), now must be YELLOW
r = lm_lungs.calculate_risk({"ProfileInfo": {"Age": 25, "Gender": "Male", "ActivityLevel": "Moderate"},
                               "HealthInfo":  {"Smoking": "Daily", "City": "delhi"}})
check("LU1: 25yo Delhi daily smoker — must be YELLOW (not GREEN)",
      r["risk_level"] == "YELLOW", r["risk_level"], "YELLOW")
check("LU1: score < 76 (not in healthy green range)",
      r["health_score"] < 76, r["health_score"], "< 76")

# LU2: Non-smoker clean city — must stay GREEN
r2 = lm_lungs.calculate_risk({"ProfileInfo": {"Age": 28, "Gender": "Male", "ActivityLevel": "Active"},
                                "HealthInfo":  {"Smoking": "Never", "City": "mysore"}})
check("LU2: 28yo Mysore never-smoker — must be GREEN",
      r2["risk_level"] == "GREEN", r2["risk_level"], "GREEN")
check("LU2: score ≥ 75",
      r2["health_score"] >= 75, r2["health_score"], ">= 75")

# LU3: Non-smoker Delhi — pollution alone without smoking should not push to RED
r3 = lm_lungs.calculate_risk({"ProfileInfo": {"Age": 30, "Gender": "Female", "ActivityLevel": "Active"},
                                "HealthInfo":  {"Smoking": "Never", "City": "delhi"}})
check("LU3: Delhi never-smoker — must not be RED",
      r3["risk_level"] != "RED", r3["risk_level"], "not RED")
check("LU3: score ≥ 65",
      r3["health_score"] >= 65, r3["health_score"], ">= 65")

# ─────────────────────────────────────────────────────────────
print("\n=== KIDNEY MODEL ===")
from models.kidney_model import KidneyModel
km = KidneyModel()

# K1: Normal labs — should be GREEN
r = km.calculate_risk({"ProfileInfo": {"Age": 30, "Gender": "Male"},
                        "HealthInfo":  {"SerumCreatinine": 0.9, "eGFR": 95,
                                        "Smoking": "Never", "Alcohol": "Never"}})
check("K1: Normal creatinine/eGFR — should be GREEN",
      r["risk_level"] == "GREEN", r["risk_level"], "GREEN")

# K2: CKD indicators — elevated creatinine, low eGFR
r2 = km.calculate_risk({"ProfileInfo": {"Age": 58, "Gender": "Male"},
                         "HealthInfo":  {"SerumCreatinine": 2.8, "eGFR": 28,
                                         "HbA1c": 9.0, "MedicalConditions": ["diabetes"]}})
check("K2: Creatinine 2.8 + eGFR 28 + DM — must be YELLOW or RED",
      r2["risk_level"] in ("YELLOW", "RED"), r2["risk_level"], "YELLOW or RED")

# ─────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
if FAIL == 0:
    print("ALL TESTS PASSED ✅")
else:
    print(f"⚠️  {FAIL} test(s) failed — review above")
