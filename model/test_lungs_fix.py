"""Quick test: Delhi + daily smoking should NOT show healthy lungs."""
import sys
sys.path.insert(0, ".")
from models.lungs_model import LungsModel

m = LungsModel()

# Test 1: Young daily smoker in Delhi — must be at least YELLOW
r = m.calculate_risk({
    "ProfileInfo": {"Age": 25, "Gender": "Male", "ActivityLevel": "Moderate"},
    "HealthInfo": {"Smoking": "Daily", "City": "delhi"}
})
print(f"Test1 — 25yo Delhi daily smoker: risk={r['current_risk']}, score={r['health_score']}, level={r['risk_level']}")
assert r['risk_level'] == 'YELLOW', f"FAIL: level={r['risk_level']}, score={r['health_score']} — daily Delhi smoker must be YELLOW, not GREEN"
assert r['health_score'] < 76, f"FAIL: score {r['health_score']} too high for daily Delhi smoker"

# Test 2: Older daily smoker in Delhi — should be RED
r2 = m.calculate_risk({
    "ProfileInfo": {"Age": 50, "Gender": "Male", "ActivityLevel": "Sedentary"},
    "HealthInfo": {"Smoking": "Daily", "City": "delhi"}
})
print(f"Test2 — 50yo Delhi daily smoker sedentary: risk={r2['current_risk']}, score={r2['health_score']}, level={r2['risk_level']}")
assert r2['risk_level'] in ('YELLOW', 'RED'), f"FAIL: 50yo Delhi daily smoker must not be GREEN, got {r2['risk_level']}"
assert r2['health_score'] < 75, f"FAIL: score {r2['health_score']} still too high for 50yo heavy smoker in Delhi"

# Test 3: Non-smoker in Delhi — should stay GREEN/YELLOW but not RED
r3 = m.calculate_risk({
    "ProfileInfo": {"Age": 30, "Gender": "Female", "ActivityLevel": "Active"},
    "HealthInfo": {"Smoking": "Never", "City": "delhi"}
})
print(f"Test3 — 30yo Delhi never-smoker active: risk={r3['current_risk']}, score={r3['health_score']}, level={r3['risk_level']}")
assert r3['health_score'] >= 65, f"FAIL: non-smoker score {r3['health_score']} too low — non-smoker in Delhi should not be RED"

# Test 4: Clean city non-smoker — should be GREEN
r4 = m.calculate_risk({
    "ProfileInfo": {"Age": 28, "Gender": "Male", "ActivityLevel": "Active"},
    "HealthInfo": {"Smoking": "Never", "City": "mysore"}
})
print(f"Test4 — 28yo Mysore never-smoker: risk={r4['current_risk']}, score={r4['health_score']}, level={r4['risk_level']}")
assert r4['health_score'] >= 75, f"FAIL: healthy person score {r4['health_score']} should be GREEN"

print("\nAll tests PASSED!")
