"""
Configuration settings for QB Interception Prediction Model
"""

# Data settings
DATA_PATH = '/Users/td/Code/nfl-ai/Models/IN-PROGRESS/final_data_pfr/player_stats_pfr.csv'
TRAINING_SEASONS = [2020, 2021, 2022, 2023, 2024, 2025]
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Model features (columns in player_stats_pfr.csv)
FEATURES = [
    'pass_att',      # Number of pass attempts
    'pass_cmp',      # Number of completed passes
    'pass_yds',      # Total passing yards
    'pass_td',       # Passing touchdowns
    'pass_sacked'    # Number of times sacked
]

# Model hyperparameters
LOGISTIC_REGRESSION_PARAMS = {
    'max_iter': 1000,
    'random_state': RANDOM_STATE
}

RANDOM_FOREST_PARAMS = {
    'n_estimators': 100,
    'random_state': RANDOM_STATE
}

XGBOOST_PARAMS = {
    'eval_metric': 'logloss',
    'random_state': RANDOM_STATE
}

# Output settings
SAVE_PREDICTIONS = False
PREDICTIONS_OUTPUT_PATH = 'interception_predictions.csv'
SAVE_MODEL = False
MODEL_OUTPUT_PATH = 'trained_model.pkl'
