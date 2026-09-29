# utils/data_processor.py

import pandas as pd
import numpy as np
from pathlib import Path
import os

class DataProcessor:
    """Process all datasets for training"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
    
    def process_cardio_data(self):
        """Process cardio dataset for heart model"""
        print("\n🔍 Processing Cardio Dataset...")
        
        cardio_path = self.data_dir / "cardio_dataset.csv"
        if not cardio_path.exists():
            print(f"❌ Cardio data not found at {cardio_path}")
            return None
        
        df = pd.read_csv(cardio_path)
        print(f"📊 Loaded {len(df)} cardio records")
        
        # Parse age from "50 years 143 days" format
        def parse_age(age_str):
            try:
                parts = str(age_str).split()
                return int(parts[0])
            except:
                return 50
        
        df['age'] = df['age'].apply(parse_age)
        
        # Select features for heart model
        feature_cols = ['age', 'bmi', 'systolic_bp', 'diastolic_bp', 
                       'cholesterol', 'gluc', 'smoke', 'alco', 'active']
        
        # Create processed dataset
        processed_df = df[feature_cols + ['cardio']].copy()
        
        # Handle missing values
        processed_df = processed_df.dropna()
        
        # Save
        output_path = self.processed_dir / "heart_training_data.csv"
        processed_df.to_csv(output_path, index=False)
        print(f"✅ Saved {len(processed_df)} processed heart records to {output_path}")
        
        return processed_df
    
    def process_liver_data(self):
        """Process liver datasets for liver model"""
        print("\n🔍 Processing Liver Datasets...")
        
        # Load Srishti's data
        liver_path = self.data_dir / "liver_dataset.csv"
        nhanes_path = self.data_dir / "nhanes_liver_data.csv"
        
        datasets = []
        
        # Process Srishti's data
        if liver_path.exists():
            df1 = pd.read_csv(liver_path)
            print(f"📊 Loaded {len(df1)} Srishti liver records")
            
            # Map columns
            df1_processed = pd.DataFrame()
            df1_processed['age'] = df1['Age']
            df1_processed['bmi'] = df1['Body Mass Index']
            df1_processed['ast'] = df1['AST']
            df1_processed['alt'] = df1['ALT']
            df1_processed['ggt'] = df1['GGT']
            df1_processed['glucose'] = df1['Glucose']
            
            # Target: fibrosis (0 = healthy, 1+ = diseased)
            fibrosis_col = None
            for col in df1.columns:
                if 'Fibrosis' in str(col) and 'status' not in str(col).lower():
                    fibrosis_col = col
                    break
            
            if fibrosis_col:
                df1_processed['target'] = (df1[fibrosis_col] >= 1).astype(int)
                datasets.append(df1_processed)
                print(f"  Added {len(df1_processed)} Srishti samples")
        
        # Process NHANES data
        if nhanes_path.exists():
            df2 = pd.read_csv(nhanes_path)
            print(f"📊 Loaded {len(df2)} NHANES liver records")
            
            df2_processed = pd.DataFrame()
            df2_processed['age'] = df2['RIDAGEYR']
            df2_processed['ast'] = df2['LBXSATSI']
            df2_processed['alt'] = df2['ALT_UL']
            df2_processed['ggt'] = df2['LBXSGTSI']
            df2_processed['target'] = df2['Liver_Risk_Score']
            
            # NHANES doesn't have BMI/glucose, use median from Srishti's data
            if datasets:
                df2_processed['bmi'] = datasets[0]['bmi'].median()
                df2_processed['glucose'] = datasets[0]['glucose'].median()
            else:
                df2_processed['bmi'] = 28
                df2_processed['glucose'] = 100
            
            datasets.append(df2_processed)
            print(f"  Added {len(df2_processed)} NHANES samples")
        
        if not datasets:
            print("❌ No liver data found")
            return None
        
        # Combine all datasets
        combined = pd.concat(datasets, ignore_index=True)
        combined = combined.dropna()
        
        print(f"\n✅ Combined dataset: {len(combined)} total samples")
        print(f"   Healthy (target=0): {sum(combined['target']==0)}")
        print(f"   Diseased (target=1): {sum(combined['target']==1)}")
        
        # Save
        output_path = self.processed_dir / "liver_training_data.csv"
        combined.to_csv(output_path, index=False)
        print(f"✅ Saved to {output_path}")
        
        return combined
    
    def process_all(self):
        """Process all datasets"""
        print("="*60)
        print("🔄 PROCESSING ALL DATASETS")
        print("="*60)
        
        heart_data = self.process_cardio_data()
        liver_data = self.process_liver_data()
        
        return {
            'heart': heart_data,
            'liver': liver_data
        }


if __name__ == "__main__":
    processor = DataProcessor()
    processor.process_all()