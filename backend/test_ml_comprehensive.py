"""
Comprehensive ML Testing and Analysis
======================================
Tests all components of the BTC direction prediction system
and generates a detailed report on performance and areas for improvement.
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, roc_curve
)

# Import ML components
from app.ml.direction.dataset import load_btc_dataset, build_direction_target
from app.ml.direction.features import build_features, select_feature_columns
from app.ml.direction.backtest import walk_forward_backtest
from app.ml.direction.config import MODEL_CANDIDATES

# Try to import models, handle if XGBoost not available
try:
    from app.ml.direction.models import build_model
    XGBOOST_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: XGBoost not available: {e}")
    print("Models will be tested without XGBoost")
    XGBOOST_AVAILABLE = False
    
    # Define fallback model builder
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    
    def build_model(model_name: str):
        if model_name == "logistic":
            model = Pipeline(steps=[
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=42)),
            ])
            return model
        elif model_name == "random_forest":
            return RandomForestClassifier(
                n_estimators=400, max_depth=5, min_samples_split=8,
                min_samples_leaf=3, max_features="sqrt", random_state=42, n_jobs=-1
            )
        else:
            # Skip XGBoost if not available
            return RandomForestClassifier(
                n_estimators=400, max_depth=5, min_samples_split=8,
                min_samples_leaf=3, max_features="sqrt", random_state=42, n_jobs=-1
            )


class MLTestSuite:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "issues": [],
            "recommendations": [],
            "summary": {}
        }
        
    def add_test(self, name, status, details="", duration=0):
        self.results["tests"].append({
            "name": name,
            "status": status,
            "details": details,
            "duration_ms": duration
        })
        
    def add_issue(self, severity, title, description, impact):
        self.results["issues"].append({
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
            "title": title,
            "description": description,
            "impact": impact
        })
        
    def add_recommendation(self, priority, title, description, effort):
        self.results["recommendations"].append({
            "priority": priority,  # P0, P1, P2, P3
            "title": title,
            "description": description,
            "effort": effort  # Low, Medium, High
        })


def test_dataset_loading(suite):
    """Test 1: Load and inspect BTC dataset"""
    print("\n" + "="*70)
    print("TEST 1: Dataset Loading")
    print("="*70)
    
    import time
    start = time.time()
    
    try:
        df = load_btc_dataset()
        duration = (time.time() - start) * 1000
        
        print(f"✓ Successfully loaded BTC dataset")
        print(f"  - Rows: {len(df)}")
        print(f"  - Columns: {df.columns.tolist()}")
        print(f"  - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  - Missing values: {df.isnull().sum().sum()}")
        print(f"  - Duration: {duration:.2f}ms")
        
        # Checks
        issues = []
        
        if len(df) < 100:
            suite.add_issue(
                "HIGH", "Insufficient data",
                f"Only {len(df)} samples for BTC dataset",
                "Model training will be unreliable with small datasets"
            )
            issues.append(f"Only {len(df)} rows (need ≥365 for reliable training)")
        
        if df.isnull().sum().sum() > 0:
            null_cols = df.columns[df.isnull().any()].tolist()
            suite.add_issue(
                "MEDIUM", "Missing values detected",
                f"Columns with nulls: {null_cols}",
                "May affect feature engineering or model training"
            )
            issues.append(f"Null values in: {null_cols}")
        
        # Check for expected columns
        expected_cols = ['close', 'volume', 'timestamp', 'ma7', 'ma30', 'volatility']
        missing_cols = [c for c in expected_cols if c not in df.columns]
        if missing_cols:
            suite.add_issue(
                "HIGH", "Missing expected columns",
                f"Columns not found: {missing_cols}",
                "Cannot build proper features without these columns"
            )
            issues.append(f"Missing columns: {missing_cols}")
        
        details = f"Loaded {len(df)} rows with {len(df.columns)} columns"
        if issues:
            details += f"\nIssues: {'; '.join(issues)}"
        
        suite.add_test("Dataset Loading", "PASS" if not issues else "WARN", details, duration)
        return df
        
    except Exception as e:
        suite.add_test("Dataset Loading", "FAIL", str(e), (time.time() - start) * 1000)
        suite.add_issue(
            "CRITICAL", "Dataset loading failed",
            f"Error: {str(e)}",
            "Cannot proceed with ML testing"
        )
        print(f"✗ FAILED: {str(e)}")
        traceback.print_exc()
        return None


def test_target_building(suite, df):
    """Test 2: Build target variable"""
    print("\n" + "="*70)
    print("TEST 2: Target Variable Building")
    print("="*70)
    
    import time
    start = time.time()
    
    try:
        df_with_target = build_direction_target(df.copy())
        duration = (time.time() - start) * 1000
        
        print(f"✓ Target variable built successfully")
        print(f"  - Rows after target: {len(df_with_target)}")
        print(f"  - Class distribution:")
        print(f"    - UP (1):   {(df_with_target['target']==1).sum()} ({(df_with_target['target']==1).mean()*100:.1f}%)")
        print(f"    - DOWN (0): {(df_with_target['target']==0).sum()} ({(df_with_target['target']==0).mean()*100:.1f}%)")
        print(f"  - Duration: {duration:.2f}ms")
        
        issues = []
        
        # Check class imbalance
        class_ratio = (df_with_target['target']==1).mean()
        if class_ratio < 0.3 or class_ratio > 0.7:
            suite.add_issue(
                "MEDIUM", "Class imbalance",
                f"UP class: {class_ratio*100:.1f}% (expected ~50%)",
                "May bias model towards majority class, affecting real-world predictions"
            )
            issues.append(f"Class imbalance: {class_ratio*100:.1f}% UP vs {(1-class_ratio)*100:.1f}% DOWN")
            
            if class_ratio < 0.3 or class_ratio > 0.7:
                suite.add_recommendation(
                    "P1", "Address class imbalance",
                    "Use SMOTE, class weights, or stratified sampling",
                    "Medium"
                )
        
        if 'future_return' not in df_with_target.columns:
            suite.add_issue(
                "LOW", "Future return column missing",
                "Required for debugging but not critical",
                "Debugging/analysis may be harder"
            )
            issues.append("future_return column missing")
        
        details = f"Built target from {len(df)} rows, result: {len(df_with_target)} rows"
        if issues:
            details += f"\nIssues: {'; '.join(issues)}"
        
        suite.add_test("Target Building", "PASS" if not issues else "WARN", details, duration)
        return df_with_target
        
    except Exception as e:
        suite.add_test("Target Building", "FAIL", str(e), (time.time() - start) * 1000)
        suite.add_issue(
            "CRITICAL", "Target building failed",
            f"Error: {str(e)}",
            "Cannot create training labels"
        )
        print(f"✗ FAILED: {str(e)}")
        traceback.print_exc()
        return None


def test_feature_engineering(suite, df):
    """Test 3: Feature engineering"""
    print("\n" + "="*70)
    print("TEST 3: Feature Engineering")
    print("="*70)
    
    import time
    start = time.time()
    
    try:
        df_features = build_features(df.copy())
        duration = (time.time() - start) * 1000
        
        print(f"✓ Features built successfully")
        print(f"  - Input rows: {len(df)}")
        print(f"  - Output rows: {len(df_features)}")
        print(f"  - Rows dropped: {len(df) - len(df_features)}")
        print(f"  - Input columns: {len(df.columns)}")
        print(f"  - Output columns: {len(df_features.columns)}")
        print(f"  - New features: {len(df_features.columns) - len(df.columns)}")
        print(f"  - Duration: {duration:.2f}ms")
        
        # Get feature list
        feature_cols = select_feature_columns(df_features)
        print(f"  - Selected features for ML: {len(feature_cols)}")
        print(f"    Features: {feature_cols[:5]}..." if len(feature_cols) > 5 else f"    Features: {feature_cols}")
        
        issues = []
        
        if len(df_features) < 100:
            suite.add_issue(
                "HIGH", "Too many rows dropped",
                f"Only {len(df_features)} rows after feature engineering from {len(df)}",
                "Insufficient data for reliable model training"
            )
            issues.append(f"Too many rows dropped ({len(df)-len(df_features)})")
        
        if len(feature_cols) < 5:
            suite.add_issue(
                "HIGH", "Insufficient features",
                f"Only {len(feature_cols)} features selected",
                "Model has too little information for prediction"
            )
            issues.append(f"Only {len(feature_cols)} features")
            
            suite.add_recommendation(
                "P0", "Engineer more features",
                "Add features: technical indicators (RSI, MACD), cross-asset correlations, sentiment scores, volume patterns",
                "High"
            )
        
        # Check feature statistics
        feature_cols_numeric = df_features[feature_cols].select_dtypes(include=[np.number]).columns
        if len(feature_cols_numeric) < len(feature_cols):
            non_numeric = [c for c in feature_cols if c not in feature_cols_numeric]
            suite.add_issue(
                "MEDIUM", "Non-numeric features detected",
                f"Columns: {non_numeric}",
                "May cause issues with ML models expecting numeric input"
            )
            issues.append(f"Non-numeric features: {non_numeric}")
        
        # Check for infinite values
        inf_count = np.isinf(df_features[feature_cols_numeric].values).sum()
        if inf_count > 0:
            suite.add_issue(
                "MEDIUM", "Infinite values in features",
                f"Found {inf_count} infinite values",
                "Will cause NaN propagation in model training"
            )
            issues.append(f"Infinite values: {inf_count}")
        
        details = f"Engineered {len(feature_cols)} features from {len(df_features)} rows"
        if issues:
            details += f"\nIssues: {'; '.join(issues)}"
        
        suite.add_test("Feature Engineering", "PASS" if not issues else "WARN", details, duration)
        return df_features, feature_cols
        
    except Exception as e:
        suite.add_test("Feature Engineering", "FAIL", str(e), (time.time() - start) * 1000)
        suite.add_issue(
            "CRITICAL", "Feature engineering failed",
            f"Error: {str(e)}",
            "Cannot prepare data for model training"
        )
        print(f"✗ FAILED: {str(e)}")
        traceback.print_exc()
        return None, None


def test_model_training(suite, df, feature_cols):
    """Test 4: Model training and walk-forward backtest"""
    print("\n" + "="*70)
    print("TEST 4: Model Training & Backtesting")
    print("="*70)
    
    import time
    start = time.time()
    
    try:
        # Determine which models to use
        models_to_test = ["logistic", "random_forest"]
        if XGBOOST_AVAILABLE:
            models_to_test.append("xgboost")
        
        results = {}
        best_model_name = None
        best_accuracy = 0
        
        for model_name in models_to_test:
            print(f"\n  Training {model_name}...")
            model_start = time.time()
            
            metrics = walk_forward_backtest(
                df,
                feature_cols,
                lambda: build_model(model_name),
            )
            
            model_duration = (time.time() - model_start) * 1000
            results[model_name] = metrics
            
            print(f"    ✓ {model_name} complete ({model_duration:.2f}ms)")
            print(f"      Accuracy: {metrics['accuracy']:.4f}")
            print(f"      Precision: {metrics['precision_up']:.4f}")
            print(f"      Recall: {metrics['recall_up']:.4f}")
            print(f"      F1-Score: {metrics['f1']:.4f}")
            print(f"      ROC-AUC: {roc_auc_score(metrics['actuals'], metrics['probabilities']):.4f}")
            
            if metrics['accuracy'] > best_accuracy:
                best_accuracy = metrics['accuracy']
                best_model_name = model_name
        
        duration = (time.time() - start) * 1000
        
        print(f"\n✓ Model training complete")
        print(f"  - Best model: {best_model_name} (accuracy: {best_accuracy:.4f})")
        print(f"  - Models tested: {len(models_to_test)}" + (" (XGBoost disabled)" if not XGBOOST_AVAILABLE else ""))
        print(f"  - Duration: {duration:.2f}ms")
        
        issues = []
        
        # Check accuracy
        if best_accuracy < 0.52:
            suite.add_issue(
                "HIGH", "Poor model performance",
                f"Best model accuracy: {best_accuracy:.4f} (only {best_accuracy*100:.1f}% better than random 50%)",
                "Predictions barely better than coin flip, unreliable in production"
            )
            issues.append(f"Low accuracy: {best_accuracy:.4f}")
            
            suite.add_recommendation(
                "P0", "Improve model performance",
                "1. Engineer more features (sentiment, volatility ratios, cross-asset correlations)\n2. Try ensemble methods (stacking, voting)\n3. Optimize hyperparameters (grid search, Bayesian)\n4. Collect more data\n5. Consider different target (e.g., price movement magnitude)",
                "High"
            )
        
        # Check precision/recall balance
        precision = best_model_name and results[best_model_name]['precision_up']
        recall = best_model_name and results[best_model_name]['recall_up']
        
        if precision and abs(precision - recall) > 0.15:
            imbalance_direction = "too many false positives" if precision < recall else "too many false negatives"
            suite.add_issue(
                "MEDIUM", "Precision-Recall imbalance",
                f"Precision: {precision:.4f}, Recall: {recall:.4f} ({imbalance_direction})",
                "May lead to biased trading signals in production"
            )
            issues.append(f"Precision ({precision:.4f}) vs Recall ({recall:.4f}) imbalanced")
            
            suite.add_recommendation(
                "P1", "Rebalance precision-recall",
                f"Adjust decision threshold from 0.5 to ~{0.5 + (recall - precision)/2:.2f} for better balance",
                "Low"
            )
        
        # Check model variance
        all_accuracies = [results[m]['accuracy'] for m in models_to_test]
        accuracy_std = np.std(all_accuracies)
        if accuracy_std > 0.05:
            suite.add_issue(
                "MEDIUM", "High model variance",
                f"Accuracy std dev: {accuracy_std:.4f} (models differ significantly)",
                "May indicate instability or data dependency issues"
            )
            issues.append(f"High model variance (std: {accuracy_std:.4f})")
        
        details = f"Best: {best_model_name} ({best_accuracy:.4f})"
        for m in models_to_test:
            details += f"\n  - {m}: {results[m]['accuracy']:.4f}"
        
        if issues:
            details += f"\nIssues: {'; '.join(issues)}"
        
        suite.add_test("Model Training", "PASS" if best_accuracy > 0.52 else "WARN", details, duration)
        return results, best_model_name, best_accuracy
        
    except Exception as e:
        suite.add_test("Model Training", "FAIL", str(e), (time.time() - start) * 1000)
        suite.add_issue(
            "CRITICAL", "Model training failed",
            f"Error: {str(e)}",
            "Cannot train or evaluate models"
        )
        print(f"✗ FAILED: {str(e)}")
        traceback.print_exc()
        return None, None, 0


def test_prediction(suite, best_model_name, best_results):
    """Test 5: Signal generation"""
    print("\n" + "="*70)
    print("TEST 5: Signal Generation & Confidence")
    print("="*70)
    
    import time
    start = time.time()
    
    try:
        if not best_results:
            raise Exception("No model results available")
        
        # Analyze probability distribution
        probs = best_results['probabilities']
        
        print(f"✓ Probability distribution analyzed")
        print(f"  - Min probability: {min(probs):.4f}")
        print(f"  - Max probability: {max(probs):.4f}")
        print(f"  - Mean probability: {np.mean(probs):.4f}")
        print(f"  - Std dev: {np.std(probs):.4f}")
        
        # Count signals
        buy_signals = sum(1 for p in probs if p >= 0.60)
        sell_signals = sum(1 for p in probs if p <= 0.40)
        hold_signals = len(probs) - buy_signals - sell_signals
        
        print(f"  - Signal distribution:")
        print(f"    - BUY (≥0.60): {buy_signals} ({buy_signals/len(probs)*100:.1f}%)")
        print(f"    - HOLD (0.40-0.60): {hold_signals} ({hold_signals/len(probs)*100:.1f}%)")
        print(f"    - SELL (≤0.40): {sell_signals} ({sell_signals/len(probs)*100:.1f}%)")
        
        duration = (time.time() - start) * 1000
        
        issues = []
        
        # Check signal distribution
        if buy_signals + sell_signals == 0:
            suite.add_issue(
                "HIGH", "No buy/sell signals generated",
                "All predictions are HOLD (probabilities between 0.40-0.60)",
                "API will return no actionable signals to users"
            )
            issues.append("No BUY/SELL signals")
            
            suite.add_recommendation(
                "P1", "Adjust signal thresholds",
                "Lower thresholds (e.g., 0.55/0.45) or add confidence scoring",
                "Low"
            )
        
        if hold_signals / len(probs) > 0.8:
            suite.add_issue(
                "MEDIUM", "Excessive HOLD signals",
                f"{hold_signals/len(probs)*100:.1f}% of predictions are HOLD",
                "Model is too uncertain, limiting trading opportunities"
            )
            issues.append(f"High HOLD ratio: {hold_signals/len(probs)*100:.1f}%")
        
        # Check extreme probabilities
        extreme_probs = sum(1 for p in probs if p < 0.35 or p > 0.65)
        if extreme_probs / len(probs) < 0.2:
            suite.add_issue(
                "MEDIUM", "Insufficient extreme probabilities",
                f"Only {extreme_probs/len(probs)*100:.1f}% of predictions are extreme",
                "Model lacks strong conviction, predictions may be unreliable"
            )
            issues.append(f"Low conviction: only {extreme_probs/len(probs)*100:.1f}% extreme")
        
        details = f"BUY: {buy_signals} ({buy_signals/len(probs)*100:.1f}%), HOLD: {hold_signals} ({hold_signals/len(probs)*100:.1f}%), SELL: {sell_signals} ({sell_signals/len(probs)*100:.1f}%)"
        if issues:
            details += f"\nIssues: {'; '.join(issues)}"
        
        suite.add_test("Signal Generation", "PASS" if len(issues) == 0 else "WARN", details, duration)
        
    except Exception as e:
        suite.add_test("Signal Generation", "FAIL", str(e), (time.time() - start) * 1000)
        suite.add_issue(
            "HIGH", "Signal generation failed",
            f"Error: {str(e)}",
            "Cannot generate trading signals"
        )
        print(f"✗ FAILED: {str(e)}")
        traceback.print_exc()


def analyze_data_quality(suite, df):
    """Additional: Analyze data quality"""
    print("\n" + "="*70)
    print("BONUS: Data Quality Analysis")
    print("="*70)
    
    try:
        # Check timestamp consistency
        df_sorted = df.sort_values('timestamp')
        time_diffs = df_sorted['timestamp'].diff()
        
        print(f"✓ Data quality checks:")
        print(f"  - Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  - Most common time diff: {time_diffs.mode()[0]}")
        print(f"  - Time diff std dev: {time_diffs.std()}")
        
        # Check for price anomalies
        returns = df['close'].pct_change()
        extreme_returns = (returns.abs() > 0.10).sum()  # >10% daily move
        
        print(f"  - Extreme price moves (>10%): {extreme_returns}")
        print(f"  - Max daily return: {returns.max()*100:.2f}%")
        print(f"  - Min daily return: {returns.min()*100:.2f}%")
        
        issues = []
        
        if extreme_returns > len(df) * 0.01:  # More than 1% extreme moves
            suite.add_issue(
                "MEDIUM", "Unusual price volatility",
                f"Found {extreme_returns} moves >10% ({extreme_returns/len(df)*100:.2f}%)",
                "May indicate data quality issues or market stress periods"
            )
            issues.append(f"Extreme returns: {extreme_returns}")
        
        # Check volume patterns
        if 'volume' in df.columns:
            zero_volume = (df['volume'] == 0).sum()
            if zero_volume > 0:
                suite.add_issue(
                    "LOW", "Zero volume records",
                    f"Found {zero_volume} records with zero volume",
                    "May be missing or malformed data"
                )
                issues.append(f"Zero volume: {zero_volume}")
        
        details = "Data spans " + str((df['timestamp'].max() - df['timestamp'].min()).days) + " days"
        if issues:
            details += f"\nIssues: {'; '.join(issues)}"
        
        suite.add_test("Data Quality", "PASS" if len(issues) == 0 else "WARN", details)
        
    except Exception as e:
        print(f"Data quality check error: {e}")


def generate_summary(suite):
    """Generate summary statistics"""
    tests = suite.results["tests"]
    
    test_count = len(tests)
    passed = sum(1 for t in tests if t["status"] == "PASS")
    warned = sum(1 for t in tests if t["status"] == "WARN")
    failed = sum(1 for t in tests if t["status"] == "FAIL")
    
    issue_count = len(suite.results["issues"])
    critical = sum(1 for i in suite.results["issues"] if i["severity"] == "CRITICAL")
    high = sum(1 for i in suite.results["issues"] if i["severity"] == "HIGH")
    medium = sum(1 for i in suite.results["issues"] if i["severity"] == "MEDIUM")
    low = sum(1 for i in suite.results["issues"] if i["severity"] == "LOW")
    
    suite.results["summary"] = {
        "total_tests": test_count,
        "tests_passed": passed,
        "tests_warned": warned,
        "tests_failed": failed,
        "total_issues": issue_count,
        "critical_issues": critical,
        "high_issues": high,
        "medium_issues": medium,
        "low_issues": low,
        "overall_status": "FAIL" if failed > 0 or critical > 0 else ("WARN" if warned > 0 or high > 0 else "PASS")
    }


def print_summary(suite):
    """Print summary report"""
    if not suite.results.get("summary"):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("No summary available - tests did not complete")
        print("="*70)
        return
    
    summary = suite.results["summary"]
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests: {summary['tests_passed']}/{summary['total_tests']} passed")
    print(f"  - Passed:  {summary['tests_passed']}")
    print(f"  - Warned:  {summary['tests_warned']}")
    print(f"  - Failed:  {summary['tests_failed']}")
    print(f"\nIssues: {summary['total_issues']} found")
    print(f"  - Critical: {summary['critical_issues']}")
    print(f"  - High:     {summary['high_issues']}")
    print(f"  - Medium:   {summary['medium_issues']}")
    print(f"  - Low:      {summary['low_issues']}")
    print(f"\nOverall Status: {summary['overall_status']}")
    print("="*70)


def run_all_tests():
    """Execute all tests"""
    suite = MLTestSuite()
    
    print("\n" + "="*70)
    print("CRYPTO-DASHBOARD ML TESTING SUITE")
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Test 1: Load data
    df = test_dataset_loading(suite)
    if df is None:
        print("Cannot continue without data")
        return suite
    
    # Test 2: Build targets
    df_with_target = test_target_building(suite, df)
    if df_with_target is None:
        print("Cannot continue without targets")
        return suite
    
    # Test 3: Engineer features
    df_features, feature_cols = test_feature_engineering(suite, df_with_target)
    if df_features is None or feature_cols is None:
        print("Cannot continue without features")
        return suite
    
    # Test 4: Train models
    results, best_model, best_accuracy = test_model_training(suite, df_features, feature_cols)
    if results is None:
        print("Cannot continue without training results")
        return suite
    
    # Test 5: Generate signals
    if best_model and best_model in results:
        test_prediction(suite, best_model, results[best_model])
    
    # Bonus: Data quality
    analyze_data_quality(suite, df)
    
    # Generate summary
    generate_summary(suite)
    
    return suite


if __name__ == "__main__":
    # Run tests
    suite = run_all_tests()
    
    # Print summary
    print_summary(suite)
    
    # Save report
    report_path = Path(__file__).parent / "ml_test_report.json"
    with open(report_path, "w") as f:
        json.dump(suite.results, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_path}")
