"""Configuration settings for QB Interception Analysis"""
import os

# Base directory - adjust to your project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../../"))

# Data paths (relative to project root or absolute)
DATA_PATH = os.path.join(PROJECT_ROOT, "Scrapers/final_data_pfr/player_stats_pfr.csv")

# Or use environment variable for flexibility
DATA_PATH = os.getenv("NFL_DATA_PATH", DATA_PATH)

# Output directories (relative to this module)
DATA_DIR = os.path.join(BASE_DIR, "data")
PREDICTIONS_DIR = os.path.join(BASE_DIR, "predictions")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Output file paths
ODDS_LATEST = os.path.join(DATA_DIR, "odds_interceptions_dk_latest.csv")
ODDS_SNAPSHOT_DIR = DATA_DIR

# Model settings
TRAINING_SEASONS = [2020, 2021, 2022, 2023, 2024, 2025]
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Model features
FEATURES = [
    'pass_att',
    'pass_cmp',
    'pass_yds',
    'pass_td',
    'pass_sacked'
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

# Scraping settings
SCRAPE_CACHE_MINUTES = 5  # Skip re-scraping if file is newer than this

# Edge analysis settings
MIN_EDGE_THRESHOLD = 0.02  # Minimum 2% edge to highlight
VIG_METHOD = "actual"  # "actual" or "fixed"
FIXED_VIG_PERCENT = 0.05  # Used if VIG_METHOD is "fixed"
