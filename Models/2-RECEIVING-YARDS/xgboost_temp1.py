# xgb_receiving_yards_hardcoded.py
# Simplest possible: train ONLY on 'targets' and 'receptions' to predict 'rec_yards'.
# No checks, no validation split, no extra casting.

import pandas as pd
from xgboost import XGBRegressor

# Load
hist = pd.read_csv("historical_player_games.csv")
upcoming = pd.read_csv("upcoming_player_games.csv")

# Train on just these columns
df = hist[["targets", "receptions", "rec_yards"]].dropna()
X = df[["targets", "receptions"]]
y = df["rec_yards"]

model = XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="reg:squarederror",
    random_state=42,
    tree_method="hist",
)
model.fit(X, y)

# Predict upcoming
pred = model.predict(upcoming[["targets", "receptions"]])
upcoming["pred_rec_yards"] = pred

# Save
upcoming.to_csv("prop_projections_receiving.csv", index=False)
print("Saved: prop_projections_receiving.csv")
print(upcoming[["targets", "receptions", "pred_rec_yards"]].head(10))

