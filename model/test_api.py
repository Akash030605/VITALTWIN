"""End-to-end API test — run from model/ directory."""
import urllib.request, json, sys

payload = {
    "ProfileInfo": {
        "Age": 45, "Gender": "Male", "Height": 170, "Weight": 80,
        "Diet": "Average", "ActivityLevel": "Moderate"
    },
    "HealthInfo": {
        "Smoking": "Daily", "Alcohol": "Weekly", "Sleep": 6, "Stress": "High",
        "MedicalConditions": ["Hypertension Stage 2", "Type 2 Diabetes"]
    }
}

data = json.dumps(payload).encode()
req  = urllib.request.Request(
    "http://localhost:8000/predict",
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    resp   = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    d      = result["data"]

    print("STATUS   :", result["status"])
    print("VITAL    :", d["vital_score"]["current"], "/ 100 (", d["vital_score"]["category"], ")")
    bio = d["biological_age"]
    print("BIO AGE  : Real", bio["real_age"], "| Bio", bio["biological_age"], "| Gap", bio["age_gap"])
    print()

    for organ, res in d["organs"].items():
        score = res["health_score"]
        level = res["risk_level"]
        conf  = res["model_confidence"]
        print("  " + organ.ljust(8) + ": score=" + str(score).rjust(3) + "  risk=" + level.ljust(6) + "  conf=" + str(round(conf, 2)))

    print()
    if d["priority_recommendations"]:
        print("TOP REC  :", d["priority_recommendations"][0]["action"][:90])

    print()
    print("CLINICAL INFERENCE CHECK:")
    heart_metrics = d["organs"]["heart"].get("metrics", {})
    kidney_metrics = d["organs"]["kidney"].get("metrics", {})
    print("  Heart SBP used  :", heart_metrics.get("systolic_bp", "not in metrics"))
    print("  Kidney SBP used :", kidney_metrics.get("systolic_bp", "not in metrics"))

    print()
    print("SCORE REASONS (first 2 organs):")
    for organ, res in list(d["organs"].items())[:2]:
        print("  " + organ + ":", str(res.get("score_reason", "N/A"))[:100])

except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.reason)
    body = e.read().decode()
    print("DETAIL:", body[:2000])
    sys.exit(1)
