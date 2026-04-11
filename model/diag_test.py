import sys
sys.path.insert(0, '.')
from simulation_engine import VitalTwinSimulator

sim = VitalTwinSimulator()

# Test 1: Perfectly healthy 25yo male
healthy_25 = {
    'ProfileInfo': {'Age': 25, 'Gender': 'Male', 'ActivityLevel': 'Active', 'Diet': 'Good'},
    'HealthInfo': {
        'Bmi': 22.0,
        'SystolicBP': 110, 'DiastolicBP': 70,
        'TotalCholesterol': 170, 'HDLCholesterol': 60,
        'FastingGlucose': 85,
        'Smoking': 'Never', 'Alcohol': 'Never',
        'Sleep': 8, 'Stress': 'Low',
        'MedicalConditions': []
    }
}

result = sim.run_simulation(healthy_25, include_what_if=False)
vs = result.get('vital_score', {})
print('=== HEALTHY 25YO MALE (expect: Excellent 85+) ===')
print('Vital Score:', vs.get('current'), '(', vs.get('category'), ')')
organs = result.get('organ_scores', {})
for organ, data in organs.items():
    print('  ', organ, ': score=', data.get('health_score'), ', risk=', data.get('current_risk'), ', level=', data.get('risk_level'), ', method=', data.get('method_used','?'))

# Test 2: Average 40yo
avg_40 = {
    'ProfileInfo': {'Age': 40, 'Gender': 'Male', 'ActivityLevel': 'Moderate', 'Diet': 'Average'},
    'HealthInfo': {
        'Bmi': 26.0,
        'SystolicBP': 125, 'DiastolicBP': 82,
        'TotalCholesterol': 210, 'HDLCholesterol': 48,
        'FastingGlucose': 95,
        'Smoking': 'Never', 'Alcohol': 'Occasional',
        'Sleep': 7, 'Stress': 'Medium',
        'MedicalConditions': []
    }
}
result_avg = sim.run_simulation(avg_40, include_what_if=False)
vs_avg = result_avg.get('vital_score', {})
print()
print('=== AVERAGE 40YO MALE (expect: Good 65-75) ===')
print('Vital Score:', vs_avg.get('current'), '(', vs_avg.get('category'), ')')
for organ, data in result_avg.get('organ_scores', {}).items():
    print('  ', organ, ': score=', data.get('health_score'), ', risk=', data.get('current_risk'), ', level=', data.get('risk_level'))

# Test 3: Unhealthy 55yo
unhealthy_55 = {
    'ProfileInfo': {'Age': 55, 'Gender': 'Male', 'ActivityLevel': 'Sedentary', 'Diet': 'Poor'},
    'HealthInfo': {
        'Bmi': 32.0,
        'SystolicBP': 160, 'DiastolicBP': 100,
        'TotalCholesterol': 260, 'HDLCholesterol': 35,
        'FastingGlucose': 140,
        'Smoking': 'Daily', 'Alcohol': 'Daily',
        'Sleep': 5, 'Stress': 'High',
        'MedicalConditions': ['Hypertension', 'Diabetes']
    }
}
result2 = sim.run_simulation(unhealthy_55, include_what_if=False)
vs2 = result2.get('vital_score', {})
print()
print('=== UNHEALTHY 55YO MALE (expect: Poor/Critical <40) ===')
print('Vital Score:', vs2.get('current'), '(', vs2.get('category'), ')')
for organ, data in result2.get('organ_scores', {}).items():
    print('  ', organ, ': score=', data.get('health_score'), ', risk=', data.get('current_risk'), ', level=', data.get('risk_level'))

# Test 4: No labs at all - 35yo
no_labs_35 = {
    'ProfileInfo': {'Age': 35, 'Gender': 'Male', 'ActivityLevel': 'Moderate', 'Diet': 'Average'},
    'HealthInfo': {
        'Bmi': 24.0,
        'Smoking': 'Never', 'Alcohol': 'Never',
        'Sleep': 7, 'Stress': 'Medium',
        'MedicalConditions': []
    }
}
result3 = sim.run_simulation(no_labs_35, include_what_if=False)
vs3 = result3.get('vital_score', {})
print()
print('=== NO LABS 35YO MALE (expect: Good ~70) ===')
print('Vital Score:', vs3.get('current'), '(', vs3.get('category'), ')')
for organ, data in result3.get('organ_scores', {}).items():
    print('  ', organ, ': score=', data.get('health_score'), ', risk=', data.get('current_risk'), ', level=', data.get('risk_level'))
