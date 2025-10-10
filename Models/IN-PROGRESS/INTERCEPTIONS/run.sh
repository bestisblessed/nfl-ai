#!/bin/bash

cd /Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS

# Train model
python train_interception_model.py
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..100})"

# Predict upcoming games
python predict_upcoming_starting_qbs.py

rm -rf __pycache*
rm logreg_model.pkl