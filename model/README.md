# 🏥 VITALTWIN - Digital Twin of Human Body

## 🎯 8 Winning Features

### Core Features
1. **Organ Risk Assessment** - Risk scores for Heart, Brain, Liver, Kidney, Lungs
2. **Health Score** - Unified 0-100 score
3. **Timeline Projection** - 1,3,5,10 year risk progression

### ⭐ Differentiator Features
4. **Biological Age Engine** - Compare real age vs biological age
5. **Future Self Timeline** - Visual evolution over 10 years
6. **Body Stress Heatmap** - Color-coded stress overlay
7. **What-If Lifestyle Simulator** - See impact of changes instantly
8. **Vital Score Gauge** - Quick health snapshot

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Place datasets in data/ folder
# - cardio_dataset.csv
# - liver_dataset.csv  
# - nhanes_liver_data.csv

# Train models
python train_all.py

# Test
python -c "from simulation_engine import VitalTwinSimulator; simulator = VitalTwinSimulator(); test_user = {'ProfileInfo': {'Userid': 'TEST123', 'Age': 45}, 'HealthInfo': {'Smoking': 'Daily', 'Sleep': 5}}; print(simulator.run_simulation(test_user))"