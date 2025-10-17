#!/bin/bash
set -euo pipefail

SCRIPT_DIR="/workspace/nfl-ai/Models/IN-PROGRESS/anytime_touchdown_models"
PYTHON_BIN="python"

$PYTHON_BIN "$SCRIPT_DIR/random_forest.py"
$PYTHON_BIN "$SCRIPT_DIR/xgboost_model.py"
