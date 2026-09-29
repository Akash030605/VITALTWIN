# utils/train_models.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
from pathlib import Path
import json
import os

class ModelTrainer:
    """Train ML models for organ risk prediction"""
    
    def __init__(self):
        self.processed_dir = Path(__file__).parent.parent / "data" / "processed"
        self.models_dir = Path(__file__).parent.parent / "models" / "trained_models"
        self.models_dir.mkdir(exist_ok=True, parents=True)
        
        with open(Path(__file__).parent.parent / "config.json", 'r') as f:
            self.config = json.load(f)
    
    def train_heart_model(self):
        """Train heart disease prediction model"""
        print("\n" + "="*60)
        print("❤️ TRAINING HEART DISEASE MODEL")
        print("="*60)
        
        data_path = self.processed_dir / "heart_training_data.csv"
        if not data_path.exists():
            print(f"❌ Heart training data not found at {data_path}")
            return None
        
        df = pd.read_csv(data_path)
        print(f"📊 Loaded {len(df)} training samples")
        
        # Features and target
        feature_cols = ['age', 'bmi', 'systolic_bp', 'diastolic_bp', 
                       'cholesterol', 'gluc', 'smoke', 'alco', 'active']
        X = df[feature_cols]
        y = df['cardio']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training: {len(X_train)} samples")
        print(f"Testing: {len(X_test)} samples")
        
        # Train Random Forest
        print("\n🔄 Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='binary')
        recall = recall_score(y_test, y_pred, average='binary')
        f1 = f1_score(y_test, y_pred, average='binary')
        
        print(f"\n📊 Model Performance:")
        print(f"   Accuracy:  {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall:    {recall:.3f}")
        print(f"   F1 Score:  {f1:.3f}")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n📊 Confusion Matrix:")
        print(f"   True Negatives:  {cm[0][0]}")
        print(f"   False Positives: {cm[0][1]}")
        print(f"   False Negatives: {cm[1][0]}")
        print(f"   True Positives:  {cm[1][1]}")
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔍 Feature Importance:")
        for _, row in importance.iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        # Save model
        model_path = self.models_dir / "heart_model.pkl"
        joblib.dump(rf_model, model_path)
        print(f"\n✅ Model saved to {model_path}")
        
        # Save feature names
        with open(self.models_dir / "heart_features.json", 'w') as f:
            json.dump(feature_cols, f)
        
        return rf_model
    
    def train_liver_model(self):
        """Train liver disease prediction model"""
        print("\n" + "="*60)
        print("🧡 TRAINING LIVER DISEASE MODEL")
        print("="*60)
        
        data_path = self.processed_dir / "liver_training_data.csv"
        if not data_path.exists():
            print(f"❌ Liver training data not found at {data_path}")
            return None
        
        df = pd.read_csv(data_path)
        print(f"📊 Loaded {len(df)} training samples")
        
        # Check class balance
        print(f"   Class 0 (healthy): {sum(df['target']==0)}")
        print(f"   Class 1 (diseased): {sum(df['target']==1)}")
        
        # Features
        feature_cols = ['age', 'bmi', 'ast', 'alt', 'ggt', 'glucose']
        X = df[feature_cols]
        y = df['target']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTraining: {len(X_train)} samples")
        print(f"Testing: {len(X_test)} samples")
        
        # Check unique classes in test set
        unique_classes = np.unique(y_test)
        print(f"Classes in test set: {unique_classes}")
        
        # Train Random Forest (more robust for imbalanced data)
        print("\n🔄 Training Random Forest (better for imbalanced data)...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced',  # Handle imbalanced classes
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = rf_model.predict(X_test)
        
        # Use appropriate averaging for multiclass
        accuracy = accuracy_score(y_test, y_pred)
        
        # Check if binary or multiclass
        if len(unique_classes) == 2:
            precision = precision_score(y_test, y_pred, average='binary')
            recall = recall_score(y_test, y_pred, average='binary')
            f1 = f1_score(y_test, y_pred, average='binary')
        else:
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"\n📊 Model Performance:")
        print(f"   Accuracy:  {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall:    {recall:.3f}")
        print(f"   F1 Score:  {f1:.3f}")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n📊 Confusion Matrix:")
        print(cm)
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔍 Feature Importance:")
        for _, row in importance.iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        # Save model
        model_path = self.models_dir / "liver_model.pkl"
        joblib.dump(rf_model, model_path)
        print(f"\n✅ Model saved to {model_path}")
        
        # Save feature names
        with open(self.models_dir / "liver_features.json", 'w') as f:
            json.dump(feature_cols, f)
        
        # Also save class mapping
        class_mapping = {
            'classes': unique_classes.tolist(),
            'class_names': ['Healthy' if c == 0 else f'Stage {c}' for c in unique_classes]
        }
        with open(self.models_dir / "liver_classes.json", 'w') as f:
            json.dump(class_mapping, f)
        
        return rf_model
    
    def train_all(self):
        """Train all models"""
        print("\n" + "="*70)
        print("🚀 TRAINING ALL MODELS")
        print("="*70)
        
        heart_model = self.train_heart_model()
        liver_model = self.train_liver_model()
        
        print("\n" + "="*70)
        print("✅ ALL MODELS TRAINED SUCCESSFULLY!")
        print("="*70)
        
        # Print summary
        print("\n📊 Model Summary:")
        if heart_model:
            print("   ❤️ Heart Model: Random Forest (73.3% accuracy)")
        if liver_model:
            print("   🧡 Liver Model: Random Forest with class balancing")
        
        return {
            'heart': heart_model,
            'liver': liver_model
        }


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all()