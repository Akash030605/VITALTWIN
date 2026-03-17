#!/usr/bin/env python3
# run_tests.py - Run all tests

import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("="*70)
print("🚀 VITALTWIN AI MODEL - TEST SUITE")
print("="*70)

# Test 1: Check if data files exist
print("\n📁 CHECKING DATA FILES:")
print("-"*50)

data_dir = os.path.join(os.path.dirname(__file__), 'data')
files = {
    'NHANES': 'nhanes_liver_data.csv',
    'Srishti': 'liver_dataset.csv',
    'Cardio': 'cardio_dataset.csv'
}

for name, filename in files.items():
    path = os.path.join(data_dir, filename)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✅ {name}: {filename} ({size:,} bytes)")
    else:
        print(f"❌ {name}: {filename} NOT FOUND")

# Test 2: Import models
print("\n🔧 TESTING IMPORTS:")
print("-"*50)

try:
    from models.liver_model import LiverModel
    print("✅ LiverModel imported successfully")
    
    # Initialize model
    model = LiverModel()
    print("✅ LiverModel initialized")
    
except Exception as e:
    print(f"❌ Error importing LiverModel: {e}")

# Test 3: Run simple prediction
print("\n🤖 TESTING PREDICTION:")
print("-"*50)

try:
    # Test with a sample patient
    test_patient = {
        'age': 45,
        'ast': 50,
        'alt': 80,
        'ggt': 70,
        'bmi': 32,
        'glucose': 115
    }
    
    result = model.calculate_risk(test_patient)
    print(f"✅ Prediction successful!")
    print(f"   Risk: {result['risk']} - {result['level']}")
    print(f"   Message: {result['message']}")
    if result['factors']:
        print(f"   Factors: {', '.join(result['factors'])}")
        
except Exception as e:
    print(f"❌ Error in prediction: {e}")

# Test 4: Check thresholds
print("\n📊 CURRENT THRESHOLDS:")
print("-"*50)

try:
    thresholds_path = os.path.join(os.path.dirname(__file__), 'utils', 'thresholds.json')
    with open(thresholds_path, 'r') as f:
        thresholds = json.load(f)
    
    print("Liver Thresholds:")
    for key, value in thresholds['liver']['thresholds'].items():
        print(f"  {key}: >{value}")
        
except Exception as e:
    print(f"❌ Error loading thresholds: {e}")

print("\n" + "="*70)
print("✅ Test suite complete! Run specific tests with:")
print("   python3.12 tests/test_nhanes_data.py")
print("="*70)