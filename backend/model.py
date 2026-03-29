import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import sys

CSV_INPUT_PATH = r"C:\Snow_Predictor\backend\stations_with_snow_label.csv"
MODEL_FILE = "snow_model.pkl"
SCALER_FILE = "scaler.pkl"

def load_prepare_data(csv_path):	
    data = pd.read_csv(csv_path)
    
    # Convert labels to 0/1
    data["snow_possible_bin"] = data["snow_possible"].astype(str).str.strip().str.upper().map(
        {"YES":1,"Y":1,"1":1,"TRUE":1,"NO":0,"N":0,"0":0,"FALSE":0}
    )
    
    # Handle any unmapped values
    data["snow_possible_bin"] = data["snow_possible_bin"].fillna(
        data["snow_possible"].map(
            lambda x: 1 if str(x).strip().lower() in ["yes","y","1","true"] else 0
        )
    )
    
    # Use direct features
    feature_cols = ["latitude", "longitude", "elevation_m", "snow_score"]
    
    X = data[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    y = data["snow_possible_bin"].astype(int)
    
    return X, y, feature_cols

def train_and_export(X, y, feature_cols):
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_tr_scaled = scaler.fit_transform(X_tr)
    X_te_scaled = scaler.transform(X_te)
    
    clf = RandomForestClassifier(
        n_estimators=200, 
        max_depth=12, 
        random_state=42,  # ← FIXED: removed the extra 'c'
        class_weight = "balanced"
    )
    clf.fit(X_tr_scaled, y_tr)
    
    y_pred = clf.predict(X_te_scaled)
    
    print("Model Accuracy:", accuracy_score(y_te, y_pred))
    print("\nClassification Report:\n", classification_report(y_te, y_pred))
    
    # Feature importance
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\nFeature Importance:\n", importance_df)
    
    joblib.dump(clf, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    joblib.dump(feature_cols, "feature_cols.pkl")  # Save feature order
    
    print(f"\nModel saved to -> {MODEL_FILE}")
    print(f"Scaler saved to -> {SCALER_FILE}")

def main():
    X_data, y_labels, feature_cols = load_prepare_data(CSV_INPUT_PATH)
    train_and_export(X_data, y_labels, feature_cols)

if __name__ == "__main__":
    main()