#!/usr/bin/env python3
# train_all.py

import os
import sys

print("="*70)
print("🏥 VITALTWIN - TRAINING ALL MODELS")
print("="*70)

# Step 1: Process data
print("\n📊 STEP 1: Processing datasets...")
from utils.data_processor import DataProcessor
processor = DataProcessor()
data = processor.process_all()

# Step 2: Train models
print("\n" + "="*70)
print("🤖 STEP 2: Training ML models...")
from utils.train_models import ModelTrainer
trainer = ModelTrainer()
models = trainer.train_all()

print("\n" + "="*70)
print("✅ ALL DONE! All 8 features are ready!")
print("="*70)
print("\n🎯 Features Included:")
print("  1. ✅ Organ Risk Assessment")
print("  2. ✅ Health Score")
print("  3. ✅ Timeline Projection")
print("  4. ✅ Biological Age Engine ⭐")
print("  5. ✅ Future Self Timeline ⭐⭐⭐")
print("  6. ✅ Body Stress Heatmap ⭐")
print("  7. ✅ What-If Lifestyle Simulator ⭐⭐⭐")
print("  8. ✅ Vital Score Gauge")
print("\n📋 To test:")
print("  python3.12 -c \"from simulation_engine import VitalTwinSimulator; import json; simulator = VitalTwinSimulator(); test_user = {'ProfileInfo': {'Userid': 'TEST123', 'Age': 45, 'Gender': 'Male', 'Height': 175, 'Weight': 85, 'Diet': 'Average', 'ActivityLevel': 'Sedentary'}, 'HealthInfo': {'Smoking': 'Daily', 'Alcohol': 'Weekly', 'Sleep': 5, 'Stress': 'High', 'MedicalConditions': ['Hypertension'], 'Bmi': 27.8}}; result = simulator.run_simulation(test_user); print(json.dumps(result, indent=2))\"")