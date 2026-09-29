import warnings
warnings.filterwarnings("ignore")

from simulation_engine import VitalTwinSimulator
sim = VitalTwinSimulator()

test = {
  "ProfileInfo": {"Age": 45, "Gender": "Male", "Diet": "Average", "ActivityLevel": "Moderate"},
  "HealthInfo": {
    "Bmi": 26.5, "Smoking": "Daily", "Alcohol": "Occasional",
    "SystolicBP": 145, "DiastolicBP": 92,
    "TotalCholesterol": 220, "HDLCholesterol": 42,
    "AST": 45, "ALT": 52, "Platelets": 200,
    "FastingGlucose": 110, "Stress": "High", "Sleep": 6,
    "MedicalConditions": ["Hypertension"],
    "City": "delhi", "CookingFuel": "lpg",
    "WaistCircumference": 95, "RestingHeartRate": 82,
  }
}
result = sim.run_simulation(test)
organs = result.get("organs", {})
bio    = result.get("biological_age", {})
compl  = result.get("input_completeness", {})

print("=" * 55)
print("ORGAN RESULTS")
print("=" * 55)
for organ in ["heart","brain","liver","kidney","lungs"]:
    r = organs.get(organ, {})
    print(f"  {organ:8s}: risk={r.get('current_risk')}  conf={r.get('model_confidence')}  method={r.get('method_used','')[:40]}")

print()
print("=" * 55)
print("BIOLOGICAL AGE")
print("=" * 55)
print(f"  Real={bio.get('real_age')} | Bio={bio.get('biological_age')} | Gap={bio.get('age_gap')}yrs")
print(f"  Method: {bio.get('method')} | KDM biomarkers: {bio.get('kdm_biomarkers_used')}")
print(f"  {bio.get('message')}")

print()
print("=" * 55)
print("INPUT COMPLETENESS")
print("=" * 55)
ov = compl.get("_overall", {})
print(f"  Overall: {ov.get('overall_completeness_pct')}% [{ov.get('tier')}]")
print(f"  Tip: {ov.get('recommendation')}")
for organ in ["heart","brain","liver","kidney","lungs"]:
    c = compl.get(organ, {})
    missing_crit = [m['input'] for m in c.get('critical_missing', [])]
    missing_imp  = [m['input'] for m in c.get('important_missing', [])]
    print(f"  {organ:8s}: {c.get('completeness_pct')}% [{c.get('completeness_tier')}]  "
          f"{'[OK]' if c.get('critical_complete') else '[WARN] CRIT MISSING: ' + str(missing_crit)}"
          f"  imp_missing={missing_imp[:2]}")

print()
print("=" * 55)
print("CLINICAL METHODS (all organs)")
print("=" * 55)
for organ, method in result.get("clinical_methods", {}).items():
    print(f"  {organ:8s}: {method}")

print()
print("[OK] ALL PHASES COMPLETE")
