import numpy as np

def get_feature_importance(clf, feature_cols):
    """
    Extracts feature importances from a trained RandomForest classifier.
    Returns a sorted list of tuples: (feature_name, importance_score)
    """
    if not hasattr(clf, "feature_importances_"):
        return []
        
    importances = clf.feature_importances_
    
    # Pair with names and sort descending
    feat_imp = list(zip(feature_cols, importances))
    feat_imp.sort(key=lambda x: x[1], reverse=True)
    
    return feat_imp

def generate_local_explanation(feat_imp, row, baselines=None):
    """
    Generates a simple, rule-based plain English explanation based on the top features.
    This acts as a fallback or baseline to the LLM explanation.
    """
    if not feat_imp:
        return "Explanation not available (model lacks feature importances)."
        
    top_feature, top_score = feat_imp[0]
    second_feature, second_score = feat_imp[1]
    
    # Simplify feature names for display
    def clean_name(name):
        name = name.replace("_c", "").replace("_mm_s", "").replace("_bar", "").replace("_a", "")
        name = name.replace("_rolling_5", " (Rolling Avg)").replace("_diff", " (Rate of Change)")
        return name.replace("_", " ").title()
        
    f1_clean = clean_name(top_feature)
    f2_clean = clean_name(second_feature)
    
    explanation = f"The model's decision was primarily driven by {f1_clean} " \
                  f"({top_score:.1%} importance) and {f2_clean} ({second_score:.1%} importance)."
                  
    return explanation
