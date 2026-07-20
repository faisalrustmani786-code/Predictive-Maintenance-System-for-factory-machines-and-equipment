import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, mean_absolute_error, mean_squared_error
import time

def evaluate_classifier(y_true, y_pred):
    """Calculates standard classification metrics."""
    # Mapping for multiclass
    # Normal: 0, Warning: 1, Critical: 2
    
    acc = accuracy_score(y_true, y_pred)
    # Use macro avg for multiclass to treat all classes equally
    prec = precision_score(y_true, y_pred, average='macro', zero_division=0)
    rec = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    
    return {
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1 Score": f1,
        "Confusion Matrix": cm
    }

def evaluate_regressor(y_true, y_pred):
    """Calculates standard regression metrics for RUL."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    return {
        "MAE": mae,
        "RMSE": rmse
    }

def compare_approaches(y_true_class, y_pred_ml_class, y_pred_rule_class, 
                       y_true_reg, y_pred_ml_reg, y_pred_rule_reg):
    """
    Compares the ML approach against the Rule-based baseline.
    Returns a dictionary suitable for charting.
    """
    ml_class = evaluate_classifier(y_true_class, y_pred_ml_class)
    rule_class = evaluate_classifier(y_true_class, y_pred_rule_class)
    
    ml_reg = evaluate_regressor(y_true_reg, y_pred_ml_reg)
    rule_reg = evaluate_regressor(y_true_reg, y_pred_rule_reg)
    
    return {
        "Classification": {
            "Accuracy": {"ML": ml_class["Accuracy"], "Rule-Based": rule_class["Accuracy"]},
            "F1 Score": {"ML": ml_class["F1 Score"], "Rule-Based": rule_class["F1 Score"]}
        },
        "Regression": {
            "MAE": {"ML": ml_reg["MAE"], "Rule-Based": rule_reg["MAE"]}
        }
    }

def measure_prediction_latency(predict_func, *args):
    """Measures the time taken for a single prediction in milliseconds."""
    start_time = time.perf_counter()
    result = predict_func(*args)
    end_time = time.perf_counter()
    
    latency_ms = (end_time - start_time) * 1000
    return latency_ms, result
