import requests

tests = [
  ('PERFECT HEALTH (25yo athlete)', {
    'ProfileInfo': {'Age': 25, 'Gender': 'Male', 'ActivityLevel': 'Active', 'Diet': 'Good'},
    'HealthInfo': {'AST': 20, 'ALT': 18, 'Platelets': 250, 'Albumin': 4.5, 'Alcohol': 'Never',
                   'Bmi': 21, 'TotalCholesterol': 150, 'HDLCholesterol': 65, 'LDLCholesterol': 70,
                   'Triglycerides': 80, 'FastingGlucose': 85, 'HbA1c': 5.0, 'SerumCreatinine': 0.9,
                   'SystolicBP': 110, 'DiastolicBP': 70, 'Hemoglobin': 15.5,
                   'Smoking': 'Never', 'Sleep': 8.0, 'Stress': 'Low'}
  }),
  ('AVERAGE (40yo, BMI26, weekly alcohol)', {
    'ProfileInfo': {'Age': 40, 'Gender': 'Male', 'ActivityLevel': 'Moderate', 'Diet': 'Average'},
    'HealthInfo': {'Bmi': 26, 'TotalCholesterol': 195, 'HDLCholesterol': 42, 'LDLCholesterol': 120,
                   'Triglycerides': 140, 'FastingGlucose': 95, 'SystolicBP': 125, 'DiastolicBP': 82,
                   'SerumCreatinine': 1.0, 'Alcohol': 'Weekly', 'Smoking': 'Never',
                   'Sleep': 7.0, 'Stress': 'Medium'}
  }),
  ('HIGH RISK (55yo, 25pk-yr, DM+HTN)', {
    'ProfileInfo': {'Age': 55, 'Gender': 'Male', 'ActivityLevel': 'Sedentary', 'Diet': 'Poor'},
    'HealthInfo': {'Bmi': 32, 'TotalCholesterol': 245, 'HDLCholesterol': 35, 'LDLCholesterol': 160,
                   'Triglycerides': 230, 'FastingGlucose': 145, 'HbA1c': 8.2, 'SerumCreatinine': 1.6,
                   'SystolicBP': 165, 'DiastolicBP': 100, 'Hemoglobin': 11.5,
                   'Smoking': 'Daily', 'YearsSmoked': 25, 'CigarettesPerDay': 20,
                   'AST': 55, 'ALT': 62, 'Albumin': 3.8, 'GGT': 75,
                   'Alcohol': 'Daily', 'Sleep': 5.5, 'Stress': 'High',
                   'MedicalConditions': ['Type 2 Diabetes', 'Hypertension']}
  }),
]

EXPECTED = {
    'PERFECT HEALTH (25yo athlete)':        {'heart': (85,100), 'liver': (85,100), 'kidney': (88,100), 'brain': (88,100), 'lungs': (88,100), 'bioage_gap': (-15, 0)},
    'AVERAGE (40yo, BMI26, weekly alcohol)': {'heart': (72,90),  'liver': (75,95),  'kidney': (80,95),  'brain': (78,92),  'lungs': (78,95),  'bioage_gap': (-2, 8)},
    'HIGH RISK (55yo, 25pk-yr, DM+HTN)':    {'heart': (15,40),  'liver': (10,40),  'kidney': (20,50),  'brain': (25,55),  'lungs': (35,60),  'bioage_gap': (8, 20)},
}

print('\n' + '='*72)
print('CLINICAL ACCURACY AUDIT')
print('='*72)
all_pass = True
for label, payload in tests:
    r = requests.post('http://localhost:8000/predict', json=payload, timeout=15)
    d = r.json().get('data', {})
    organs = d.get('organs', {})
    bio = d.get('biological_age', {})
    
    print(f'\n--- {label} ---')
    exp = EXPECTED.get(label, {})
    for organ in ['heart', 'liver', 'kidney', 'brain', 'lungs']:
        o = organs.get(organ, {})
        score = o.get('health_score', 0) or 0
        risk = round(float(o.get('current_risk') or 0), 3)
        level = o.get('risk_level', '?')
        lo, hi = exp.get(organ, (0, 100))
        ok = '✓' if lo <= score <= hi else '✗ FAIL'
        if lo > score or score > hi:
            all_pass = False
        print(f'  {organ:8s}: score={score:>3}/100  risk={risk:>6.3f}  level={level:<7}  expected={lo}-{hi}  {ok}')
    
    gap = bio.get('age_gap', 0) or 0
    bio_age = bio.get('biological_age', '?')
    gap_level = bio.get('gap_level', '?')
    lo_g, hi_g = exp.get('bioage_gap', (-15, 20))
    ok_g = '✓' if lo_g <= gap <= hi_g else '✗ FAIL'
    if lo_g > gap or gap > hi_g:
        all_pass = False
    print(f'  bioage  : bio={bio_age}  gap={gap:+.1f}yr  level={gap_level:<6}  expected={lo_g:+d} to {hi_g:+d}  {ok_g}')

print('\n' + '='*72)
print('RESULT:', '✓ ALL PASS' if all_pass else '✗ SOME CHECKS FAILED')
print('='*72)
