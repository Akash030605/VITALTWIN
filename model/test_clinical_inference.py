"""Quick test for clinical_inference.py — run from model/ directory."""
from utils.clinical_inference import enrich_health_data

profile = {'age': 52, 'gender': 'Male', 'height': 170, 'weight': 88}

health = {
    'smoking': 'Daily',
    'alcohol': 'Weekly',
    'sleep': 6,
    'stress': 'High',
    'medical_conditions': ['Hypertension Stage 2', 'Type 2 Diabetes'],
}

enriched = enrich_health_data(health, profile)

print("=== INFERENCE RESULTS ===")
print("A) PackYears inferred   :", enriched.get("PackYears"), " (flag:", enriched.get("_inferred_pack_years"), ")")
print("B) WaistCircumference   :", enriched.get("WaistCircumference"), "cm  AbdominalObesity=", enriched.get("AbdominalObesity"), " (flag:", enriched.get("_inferred_waist"), ")")
print("C) SystolicBP inferred  :", enriched.get("SystolicBP"), "/", enriched.get("DiastolicBP"), "mmHg  (flag:", enriched.get("_inferred_bp"), ")")
print("D) HbA1c inferred       :", enriched.get("HbA1c"), "%  (flag:", enriched.get("_inferred_hba1c"), ")")
print()

# Test idempotency: pre-existing values must NOT be overwritten
health2 = dict(health)
health2["PackYears"]  = 25.0
health2["SystolicBP"] = 130
health2["HbA1c"]      = 7.2

enriched2 = enrich_health_data(health2, profile)
print("=== IDEMPOTENCY CHECK (pre-existing values must be preserved) ===")
print("PackYears kept as 25?   :", enriched2.get("PackYears") == 25.0, "->", enriched2.get("PackYears"))
print("SystolicBP kept as 130? :", enriched2.get("SystolicBP") == 130, "->", enriched2.get("SystolicBP"))
print("HbA1c kept as 7.2?      :", enriched2.get("HbA1c") == 7.2, "->", enriched2.get("HbA1c"))
print()

# Test female profile
profile_f = {'age': 47, 'gender': 'Female', 'height': 158, 'weight': 72}
health_f  = {'smoking': 'Never', 'medical_conditions': ['Prediabetes'], 'sleep': 7}
enriched_f = enrich_health_data(health_f, profile_f)
print("=== FEMALE / PREDIABETES TEST ===")
print("WaistCircumference (F)  :", enriched_f.get("WaistCircumference"), "cm (should be ~88)")
print("AbdominalObesity (F)    :", enriched_f.get("AbdominalObesity"), "(threshold 80cm, expect True)")
print("HbA1c prediabetes       :", enriched_f.get("HbA1c"), "% (expect 6.1)")
print("PackYears (non-smoker)  :", enriched_f.get("PackYears"), "(expect None — not a smoker)")
print()

print("ALL TESTS PASSED" if (
    enriched.get("PackYears") is not None and
    enriched.get("WaistCircumference") is not None and
    enriched.get("SystolicBP") == 155 and
    enriched.get("HbA1c") == 8.2 and
    enriched2.get("SystolicBP") == 130 and
    enriched2.get("HbA1c") == 7.2 and
    enriched_f.get("HbA1c") == 6.1
) else "SOME TESTS FAILED — check output above")
