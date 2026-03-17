#!/usr/bin/env python3
# demo.py - Quick demo of VITALTWIN liver model

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.liver_model import LiverModel

def print_patient_result(name, data, result):
    """Pretty print patient results"""
    print(f"\n{'='*60}")
    print(f"🧑 {name}")
    print(f"{'='*60}")
    print(f"Health Data:")
    for key, value in data.items():
        if key != 'name' and value is not None:
            print(f"  {key}: {value}")
    print(f"\n📊 Prediction:")
    print(f"  Risk Score: {result['risk']}")
    print(f"  Risk Level: {result['level']}")
    print(f"  Message: {result['message']}")
    if result['factors']:
        print(f"\n⚠️ Risk Factors:")
        for factor in result['factors']:
            print(f"  • {factor}")

def main():
    print("🚀 VITALTWIN LIVER MODEL DEMO")
    print("="*60)
    
    # Initialize model
    model = LiverModel()
    
    # Test Case 1: Healthy patient
    patient1 = {
        'name': 'Healthy Patient',
        'age': 30,
        'ast': 20,
        'alt': 25,
        'ggt': 18,
        'bmi': 22,
        'glucose': 90
    }
    result1 = model.calculate_risk(patient1)
    print_patient_result(patient1['name'], patient1, result1)
    
    # Test Case 2: Moderate risk (from your data)
    patient2 = {
        'name': 'Moderate Risk Patient',
        'age': 45,
        'ast': 35,
        'alt': 60,
        'ggt': 45,
        'bmi': 28,
        'glucose': 110
    }
    result2 = model.calculate_risk(patient2)
    print_patient_result(patient2['name'], patient2, result2)
    
    # Test Case 3: High risk (from Srishti's data)
    patient3 = {
        'name': 'High Risk Patient (from Srishti)',
        'age': 60,
        'ast': 27,
        'alt': 49,
        'ggt': 19,
        'bmi': 35.56,
        'glucose': 119
    }
    result3 = model.calculate_risk(patient3)
    print_patient_result(patient3['name'], patient3, result3)
    
    # Test Case 4: NHANES patient (High ALT)
    patient4 = {
        'name': 'NHANES Patient (High ALT)',
        'age': 29,
        'ast': 15,
        'alt': 228,  # Very high!
        'ggt': 8,
        'bmi': 25,
        'glucose': 95
    }
    result4 = model.calculate_risk(patient4)
    print_patient_result(patient4['name'], patient4, result4)


if __name__ == "__main__":
    main()