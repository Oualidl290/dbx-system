#!/usr/bin/env python3
"""
Model Evaluation Script with Proper Metrics
Addresses reviewer concerns about evaluation methodology
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate_with_proper_cv():
    """Proper cross-validation with stratified splits"""
    
    # Load data (synthetic + real holdout)
    X_synthetic, y_synthetic = load_synthetic_data()
    X_real, y_real = load_real_holdout_data()
    
    # Stratified K-Fold Cross Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X_synthetic, y_synthetic)):
        print(f"Fold {fold + 1}/5")
        
        X_train, X_val = X_synthetic[train_idx], X_synthetic[val_idx]
        y_train, y_val = y_synthetic[train_idx], y_synthetic[val_idx]
        
        # Train model
        model = train_aircraft_classifier(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)
        
        # Calculate metrics
        fold_metrics = {
            'accuracy': accuracy_score(y_val, y_pred),
            'f1_macro': f1_score(y_val, y_pred, average='macro'),
            'roc_auc': roc_auc_score(y_val, y_proba, multi_class='ovr')
        }
        cv_scores.append(fold_metrics)
    
    # Report CV results with confidence intervals
    print("\n=== Cross-Validation Results ===")
    for metric in ['accuracy', 'f1_macro', 'roc_auc']:
        scores = [fold[metric] for fold in cv_scores]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        print(f"{metric}: {mean_score:.3f} ± {std_score:.3f}")
    
    # Real data validation
    print("\n=== Real Data Holdout Results ===")
    final_model = train_aircraft_classifier(X_synthetic, y_synthetic)
    y_real_pred = final_model.predict(X_real)
    
    print(classification_report(y_real, y_real_pred))
    
    # Plot confusion matrix
    plot_confusion_matrix(y_real, y_real_pred)
    
    # ROC curves
    plot_roc_curves(final_model, X_real, y_real)

def evaluate_anomaly_detection():
    """Proper anomaly detection evaluation with ROC/PR curves"""
    
    # Load normal and anomalous flight data
    normal_flights = load_normal_flights()
    anomalous_flights = load_anomalous_flights()
    
    # Combine and label
    X = np.vstack([normal_flights, anomalous_flights])
    y = np.hstack([np.zeros(len(normal_flights)), np.ones(len(anomalous_flights))])
    
    # Train anomaly detector
    detector = IsolationForest(contamination=0.1, random_state=42)
    anomaly_scores = detector.decision_function(X)
    
    # Convert scores to probabilities
    anomaly_probs = (anomaly_scores.max() - anomaly_scores) / (anomaly_scores.max() - anomaly_scores.min())
    
    # ROC Curve
    fpr, tpr, thresholds = roc_curve(y, anomaly_probs)
    roc_auc = auc(fpr, tpr)
    
    # Precision-Recall Curve
    precision, recall, pr_thresholds = precision_recall_curve(y, anomaly_probs)
    pr_auc = auc(recall, precision)
    
    print(f"Anomaly Detection Performance:")
    print(f"ROC AUC: {roc_auc:.3f}")
    print(f"PR AUC: {pr_auc:.3f}")
    
    # Plot curves
    plot_roc_pr_curves(fpr, tpr, precision, recall, roc_auc, pr_auc)
    
    # Find optimal threshold
    optimal_threshold = find_optimal_threshold(precision, recall, pr_thresholds)
    print(f"Optimal Threshold: {optimal_threshold:.3f}")

def plot_confusion_matrix(y_true, y_pred):
    """Plot confusion matrix with proper labels"""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix - Real Data Holdout')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_roc_pr_curves(fpr, tpr, precision, recall, roc_auc, pr_auc):
    """Plot ROC and PR curves"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # ROC Curve
    ax1.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.3f})')
    ax1.plot([0, 1], [0, 1], 'k--', label='Random')
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('ROC Curve - Anomaly Detection')
    ax1.legend()
    ax1.grid(True)
    
    # PR Curve
    ax2.plot(recall, precision, label=f'PR Curve (AUC = {pr_auc:.3f})')
    ax2.set_xlabel('Recall')
    ax2.set_ylabel('Precision')
    ax2.set_title('Precision-Recall Curve')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('roc_pr_curves.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    print("🔍 Running Comprehensive Model Evaluation...")
    evaluate_with_proper_cv()
    evaluate_anomaly_detection()
    print("✅ Evaluation complete. Check generated plots.")