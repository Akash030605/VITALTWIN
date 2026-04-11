import sys
sys.path.insert(0, '.')
from simulation_engine import VitalTwinSimulator

sim = VitalTwinSimulator()

def test_case(label, data):
    result = sim.run_simulation(data, include_what_if=False)
    vs = result.get('vital_score', {})
    print()
    print('=== ' + label + ' ===')
    print('Vital Score:', vs.get('current'), '(' + str(vs.get('category')) + ')')
    organs = result.get('organ_scores', {})
    for organ, d in organs.items():
        print('  ' + organ + ': score=' + str(d.get('health_score')) +
              ' risk=' + str(d.get('current_risk')) +
              ' level=' + str(d.get('risk_level')) +
              ' method=' + str(d.get('method_used','?')))

# Avg 40yo with full labs
test_case('AVG 40YO FULL LABS (expect Good ~68)', {
    'ProfileInfo': {'Age': 40, 'Gender': 'Male', 'ActivityLevel': 'Moderate', 'Diet': 'Average'},
    'HealthInfo': {
        'Bmi': 26.0, 'SystolicBP': 125, 'DiastolicBP': 82,
        'TotalCholesterol': 210, 'HDLCholesterol': 48, 'FastingGlucose': 95,
        'Smoking': 'Never', 'Alcohol': 'Occasional',
        'Sleep': 7, 'Stress': 'Medium', 'MedicalConditions': []
    }
})

# No labs 35yo
test_case('NO LABS 35YO (expect Good ~65-72)', {
    'ProfileInfo': {'Age': 35, 'Gender': 'Male', 'ActivityLevel': 'Moderate', 'Diet': 'Average'},
    'HealthInfo': {
        'Bmi': 24.0, 'Smoking': 'Never', 'Alcohol': 'Never',
        'Sleep': 7, 'Stress': 'Medium', 'MedicalConditions': []
    }
})

# No labs at all - no input
test_case('EMPTY PROFILE 30YO (expect ~60-65)', {
    'ProfileInfo': {'Age': 30, 'Gender': 'Male'},
    'HealthInfo': {}
})

# Slightly overweight smoker 45yo no labs
test_case('SMOKER 45YO NO LABS (expect Fair/Yellow ~55)', {
    'ProfileInfo': {'Age': 45, 'Gender': 'Male', 'ActivityLevel': 'Sedentary', 'Diet': 'Poor'},
    'HealthInfo': {
        'Bmi': 28.0, 'Smoking': 'Daily', 'Alcohol': 'Occasional',
        'Sleep': 6, 'Stress': 'High', 'MedicalConditions': []
    }
})
