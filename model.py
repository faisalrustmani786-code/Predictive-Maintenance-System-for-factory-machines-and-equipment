import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

MODEL_DIR = "models"
CLF_PATH = f"{MODEL_DIR}/health_classifier.joblib"
REG_PATH = f"{MODEL_DIR}/rul_regressor.joblib"
SCALER_PATH = f"{MODEL_DIR}/scaler.joblib"
FEATURES_PATH = f"{MODEL_DIR}/feature_names.joblib"

SENSOR_COLS = ["temperature_c", "vibration_mm_s", "pressure_bar", "current_a", "rpm"]
LABEL_MAPPING = {"Normal": 0, "Warning": 1, "Critical": 2}
REVERSE_MAPPING = {0: "Normal", 1: "Warning", 2: "Critical"}

def load_data(path="data/machine_sensor_log.csv"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found at {path}. Please generate it first.")
    
    df = pd.read_csv(path)
    required_cols = ["timestamp", "machine_id"] + SENSOR_COLS + ["health_label", "rul_hours"]
    missing = [c for c in required_cols if c not in df.columns]
    
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
        
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def preprocess_data(df):
    """
    Engineers features for each machine:
    - Rolling averages (window = 5)
    - Rate of change (diff)
    """
    df = df.sort_values(by=["machine_id", "timestamp"]).copy()
    
    engineered_df = []
    
    for machine_id, group in df.groupby("machine_id"):
        group = group.copy()
        
        # Calculate rolling means
        for col in SENSOR_COLS:
            group[f"{col}_rolling_5"] = group[col].rolling(window=5, min_periods=1).mean()
            group[f"{col}_diff"] = group[col].diff().fillna(0)
            
        engineered_df.append(group)
        
    final_df = pd.concat(engineered_df)
    
    # Define features
    feature_cols = SENSOR_COLS + [f"{c}_rolling_5" for c in SENSOR_COLS] + [f"{c}_diff" for c in SENSOR_COLS]
    
    return final_df, feature_cols

def train_models(df, feature_cols):
    """Trains both classifier and regressor and saves to disk."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Prepare data
    X = df[feature_cols].values
    y_class = df["health_label"].map(LABEL_MAPPING).values
    y_reg = df["rul_hours"].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_scaled, y_class)
    
    # Train Regressor
    reg = GradientBoostingRegressor(n_estimators=100, random_state=42)
    reg.fit(X_scaled, y_reg)
    
    # Save models
    joblib.dump(clf, CLF_PATH)
    joblib.dump(reg, REG_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(feature_cols, FEATURES_PATH)
    
    return clf, reg, scaler, feature_cols

def load_models():
    """Loads trained models from disk if available."""
    if not all(os.path.exists(p) for p in [CLF_PATH, REG_PATH, SCALER_PATH, FEATURES_PATH]):
        return None, None, None, None
        
    clf = joblib.load(CLF_PATH)
    reg = joblib.load(REG_PATH)
    scaler = joblib.load(SCALER_PATH)
    feature_cols = joblib.load(FEATURES_PATH)
    return clf, reg, scaler, feature_cols

def predict(row_features_df, clf, reg, scaler, feature_cols):
    """Make prediction for a single processed row (DataFrame format)."""
    X = row_features_df[feature_cols].values
    X_scaled = scaler.transform(X)
    
    # Classification
    probs = clf.predict_proba(X_scaled)[0]
    pred_class = np.argmax(probs)
    label = REVERSE_MAPPING[pred_class]
    
    # Failure prob = P(Warning) + P(Critical)
    # or just P(Critical) depending on business logic. We'll use Critical + Warning/2
    fail_prob = (probs[2] + probs[1]*0.5) * 100 
    
    # Regression
    rul = max(0, reg.predict(X_scaled)[0])
    
    return label, fail_prob, rul, probs

def rule_based_predict(row):
    """
    Baseline threshold-based rule system.
    Values approximate to the data generator baselines.
    """
    vibration = row.get('vibration_mm_s', 0)
    temp = row.get('temperature_c', 0)
    current = row.get('current_a', 0)
    
    vibration_warn, vibration_crit = 3.5, 4.5
    temp_warn, temp_crit = 50.0, 55.0
    current_warn, current_crit = 18.0, 20.0
    
    if vibration >= vibration_crit or temp >= temp_crit or current >= current_crit:
        label = "Critical"
    elif vibration >= vibration_warn or temp >= temp_warn or current >= current_warn:
        label = "Warning"
    else:
        label = "Normal"
        
    # Dummy RUL for baseline (Rule-based engines usually can't predict precise RUL)
    if label == "Normal":
        rul = 1000.0
    elif label == "Warning":
        rul = 200.0
    else:
        rul = 10.0
        
    return label, rul

def get_intermediate_steps(row_raw, row_processed, clf, scaler, feature_cols):
    """
    Returns a dictionary of the intermediate transformation steps to show in UI.
    """
    X = row_processed[feature_cols].values
    X_scaled = scaler.transform(X)
    probs = clf.predict_proba(X_scaled)[0]
    
    return {
        "1. Raw Sensors": {col: round(row_raw.get(col, 0), 2) for col in SENSOR_COLS},
        "2. Engineered Features": {
            "vibration_rolling_5": round(row_processed.get("vibration_mm_s_rolling_5", 0).iloc[0] if isinstance(row_processed.get("vibration_mm_s_rolling_5", 0), pd.Series) else row_processed.get("vibration_mm_s_rolling_5", 0), 3),
            "temp_diff": round(row_processed.get("temperature_c_diff", 0).iloc[0] if isinstance(row_processed.get("temperature_c_diff", 0), pd.Series) else row_processed.get("temperature_c_diff", 0), 2)
        },
        "3. Model Probabilities": {
            "Normal": f"{probs[0]*100:.1f}%",
            "Warning": f"{probs[1]*100:.1f}%",
            "Critical": f"{probs[2]*100:.1f}%"
        },
        "4. Final Output": REVERSE_MAPPING[np.argmax(probs)]
    }
