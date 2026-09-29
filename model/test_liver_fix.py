import requests, json

# Test 1: Normal lab values — should give HIGH score (not 0)
normal = {
    "ProfileInfo": {"Age": 30, "Gender": "Male"},
    "HealthInfo": {
        "AST": 25, "ALT": 28, "Platelets": 220,
        "Albumin": 4.2, "Alcohol": "Never", "Bmi": 22
    }
}

# Test 2: Slightly elevated but still normal range
slightly_elevated = {
    "ProfileInfo": {"Age": 45, "Gender": "Male"},
    "HealthInfo": {
        "AST": 35, "ALT": 40, "Platelets": 180,
        "Albumin": 4.0, "Alcohol": "Occasional", "Bmi": 26,
        "Triglycerides": 160, "GGT": 52
    }
}

# Test 3: Worst case — daily alcohol + high GGT + low albumin
worst = {
    "ProfileInfo": {"Age": 55, "Gender": "Male"},
    "HealthInfo": {
        "AST": 80, "ALT": 45, "Platelets": 120,
        "Albumin": 3.2, "Alcohol": "Daily", "Bmi": 32,
        "Triglycerides": 250, "GGT": 120
    }
}

for label, payload in [("Normal labs", normal), ("Slightly elevated", slightly_elevated), ("Worst case", worst)]:
    try:
        r = requests.post("http://localhost:8000/analyze", json=payload, timeout=10)
        liver = r.json().get("organs", {}).get("liver", {})
        score = liver.get("health_score")
        risk  = liver.get("current_risk")
        method = liver.get("method_used")
        print(f"{label}: score={score}/100  risk={round(risk,3) if risk else risk}  method={method}")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"{label}: ERROR — {e}")
