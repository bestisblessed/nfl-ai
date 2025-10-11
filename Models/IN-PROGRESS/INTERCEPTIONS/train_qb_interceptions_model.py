"""
QB Interception Prediction Model

This script trains and evaluates machine learning models to predict
the probability that a quarterback will throw an interception in their next game.
"""

import warnings
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from xgboost import XGBClassifier
import config
import pickle

# Suppress sklearn RuntimeWarnings about overflow and divide by zero in matmul
warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")


def load_and_preprocess_data(filepath=config.DATA_PATH, seasons=config.TRAINING_SEASONS):
    """
    Load and preprocess the player stats data for QB interception prediction.

    Args:
        filepath (str): Path to the PlayerStats.csv file
        seasons (list): List of seasons to include in the analysis

    Returns:
        pd.DataFrame: Preprocessed dataframe ready for modeling
    """
    # Load data
    player_stats = pd.read_csv(filepath, low_memory=False)

    # Ensure numeric dtypes for features and target
    for col in list(config.FEATURES) + ['pass_int']:
        if col in player_stats.columns:
            player_stats[col] = pd.to_numeric(player_stats[col], errors='coerce')

    # Step 1: Remove rows where all relevant stats are zeros (use configured features)
    stats_columns = list(config.FEATURES)
    non_all_zero_mask = ~((player_stats[stats_columns].fillna(0) == 0).all(axis=1))
    player_stats_cleaned = player_stats[non_all_zero_mask]

    # Step 2: Filter data to only include specified seasons
    player_stats_cleaned = player_stats_cleaned[
        player_stats_cleaned['season'].isin(seasons)
    ]

    # Step 3: Identify passing rows (QB-like) using at least 2 pass attempts
    passing_mask = player_stats_cleaned['pass_att'].fillna(0) >= 2
    player_stats_cleaned = player_stats_cleaned[passing_mask]

    return player_stats_cleaned


def prepare_features_and_target(df):
    """
    Prepare features and target variable for modeling.

    Args:
        df (pd.DataFrame): Preprocessed dataframe

    Returns:
        tuple: (X, y, features) where X is features, y is target, features is feature list
    """
    # Feature selection - using only available columns
    features = list(config.FEATURES)

    # Target variable: whether the QB threw an interception
    df = df.copy()
    # New schema target column: 'pass_int'
    df['threw_interception'] = df['pass_int'].apply(lambda x: 1 if x > 0 else 0)

    # Drop rows with missing values
    df = df.dropna(subset=features + ['threw_interception'])

    # Split into features and target
    X = df[features]
    y = df['threw_interception']

    return X, y, features


def train_models(X_train, y_train, X_test, y_test):
    """
    Train and evaluate multiple machine learning models.

    Args:
        X_train, y_train: Training data
        X_test, y_test: Test data

    Returns:
        dict: Dictionary containing trained models and their performance metrics
    """
    models = {}
    results = {}

    # Logistic Regression
    print("Training Logistic Regression...")
    lr_model = LogisticRegression(**config.LOGISTIC_REGRESSION_PARAMS)
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)

    models['logistic_regression'] = lr_model
    results['logistic_regression'] = {
        'accuracy': accuracy_score(y_test, y_pred_lr),
        'classification_report': classification_report(y_test, y_pred_lr),
        'confusion_matrix': confusion_matrix(y_test, y_pred_lr)
    }

    # Random Forest
    print("Training Random Forest...")
    rf_model = RandomForestClassifier(**config.RANDOM_FOREST_PARAMS)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)

    models['random_forest'] = rf_model
    results['random_forest'] = {
        'accuracy': accuracy_score(y_test, y_pred_rf),
        'classification_report': classification_report(y_test, y_pred_rf),
        'confusion_matrix': confusion_matrix(y_test, y_pred_rf)
    }

    # XGBoost
    print("Training XGBoost...")
    xgb_model = XGBClassifier(**config.XGBOOST_PARAMS)
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)

    models['xgboost'] = xgb_model
    results['xgboost'] = {
        'accuracy': accuracy_score(y_test, y_pred_xgb),
        'classification_report': classification_report(y_test, y_pred_xgb),
        'confusion_matrix': confusion_matrix(y_test, y_pred_xgb)
    }

    return models, results


def print_model_results(results):
    """
    Print formatted results for all models.

    Args:
        results (dict): Results dictionary from train_models
    """
    model_names = {
        'logistic_regression': 'Logistic Regression',
        'random_forest': 'Random Forest',
        'xgboost': 'XGBoost'
    }

    for model_key, model_results in results.items():
        print(f"\n{'='*50}")
        print(f"{model_names[model_key]} Results")
        print(f"{'='*50}")
        print(".4f")
        print(f"\nClassification Report:\n{model_results['classification_report']}")
        print(f"\nConfusion Matrix:\n{model_results['confusion_matrix']}")


def predict_interceptions_for_players(model, df, features):
    """
    Generate interception probability predictions for all players and preserve QB identifiers.

    Args:
        model: Trained ML model
        df (pd.DataFrame): Preprocessed dataframe with player stats
        features (list): List of feature column names

    Returns:
        DataFrame: QB names, no_interception_prob, interception_prob
    """
    # Compute average stats for each player
    average_stats = df.groupby('player')[features].mean().reset_index()

    # Step 2: Shift data by one game to predict the next game based on the previous one
    shifted_stats = df.groupby('player')[features].shift(1)
    shifted_stats = shifted_stats.reset_index()
    shifted_stats['player'] = df['player'].values

    # Combine shifted stats with historical averages
    merged = pd.merge(shifted_stats, average_stats, on='player', how='left', suffixes=('_shift', '_avg'))

    # For each feature, use the shifted value if available, else fallback to average
    for feat in features:
        merged[feat] = merged[f"{feat}_shift"].combine_first(merged[f"{feat}_avg"])

    pred_input = merged[features]
    pred_input = pred_input.fillna(pred_input.mean())

    probs = model.predict_proba(pred_input)
    result = pd.DataFrame({
        'player': merged['player'],
        'no_interception_prob': probs[:, 0],
        'interception_prob': probs[:, 1]
    })
    return result


def main():
    """
    Main function to run the complete QB interception prediction pipeline.
    """
    print("QB Interception Prediction Model")
    print("="*50)

    # Load and preprocess data
    print("Loading and preprocessing data...")
    df = load_and_preprocess_data()

    # Prepare features and target
    X, y, features = prepare_features_and_target(df)
    print(f"Dataset shape: {X.shape}")
    print(f"Features: {features}")

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE)
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")

    # Train and evaluate models
    models, results = train_models(X_train, y_train, X_test, y_test)

    # Print results
    print_model_results(results)

    # Generate predictions for all models and save results
    print(f"\n{'='*50}")
    print("Generating Interception Probability Predictions for All Models")
    print(f"{'='*50}")

    model_names = {
        'logistic_regression': 'Logistic Regression',
        'random_forest': 'Random Forest',
        'xgboost': 'XGBoost'
    }

    for model_key, model in models.items():
        # Save the trained model
        model_save_path = f"{model_key}_model.pkl"
        with open(model_save_path, "wb") as f:
            pickle.dump(model, f)
        print(f"Saved {model_names[model_key]} model to {model_save_path}")

    print(f"\nSaved all trained models")

    return models, results


if __name__ == "__main__":
    main()
