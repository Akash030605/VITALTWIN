"""Quick test of the full simulation pipeline."""
from simulation_engine import VitalTwinSimulator
import json

simulator = VitalTwinSimulator()

test_user = {
    'ProfileInfo': {
        'Userid': 'TEST123', 'Age': 45, 'Gender': 'Male',
        'Height': 175, 'Weight': 85, 'Diet': 'Average',
        'ActivityLevel': 'Sedentary', 'City': 'Delhi'
    },
    'HealthInfo': {
        'Smoking': 'Daily', 'Alcohol': 'Weekly', 'Sleep': 5,
        'Stress': 'High', 'MedicalConditions': ['Hypertension'],
        'Medications': ['Lisinopril'], 'Bmi': 27.8,
        'SystolicBP': 145, 'DiastolicBP': 92
    }
}

result = simulator.run_simulation(test_user)

print('SUCCESS - Full pipeline working!')
print(f"Vital Score: {result['vital_score']['current']} - {result['vital_score']['category']}")
print(f"Bio Age: {result['biological_age']}")
print(f"System Confidence: {result['system_confidence']}")
print("\nOrgans:")
for organ, data in result['organs'].items():
    print(f"  {organ}: risk={data['current_risk']}, level={data['risk_level']}, method={data['method_used']}, conf={data['model_confidence']}")

print("\nMedication effects:", result['verification']['medication_effects'])
print("Consistency flags:", result['verification']['consistency_adjustments'])
print("\nFuture self (10yr):", result['future_self']['timeline'][-1])
print("\nWhat-if count:", len(result.get('what_if_simulations', {})))
print("\nInput validation:", result['verification']['input_validation'])
