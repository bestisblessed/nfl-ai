import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

# ---- Load ----
hist = pd.read_csv("historical_player_games.csv")
upcoming = pd.read_csv("upcoming_player_games.csv")

# ---- Training frame ----
required_train_cols = {"rec_yards", "targets", "receptions"}
required_pred_cols = {"targets", "receptions"}
df = hist.dropna(subset=["rec_yards"]).copy()
for c in ["targets", "receptions", "rec_yards"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
upcoming["targets"] = pd.to_numeric(upcoming["targets"], errors="coerce")
upcoming["receptions"] = pd.to_numeric(upcoming["receptions"], errors="coerce")

# Simple split (time-aware if season present & populated, else random)
if "season" in df.columns and (df["season"] == df["season"].max()).sum() > 50:
    max_season = int(df["season"].max())
    train_df = df[df["season"] < max_season]
    valid_df = df[df["season"] == max_season]
else:
    train_df, valid_df = train_test_split(df, test_size=0.2, random_state=42)

# ---- Features & label (ONLY these two features) ----
X_train = train_df[["targets", "receptions"]]
y_train = train_df["rec_yards"].astype(float)
X_valid = valid_df[["targets", "receptions"]]
y_valid = valid_df["rec_yards"].astype(float)

# ---- Model ----
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
model.fit(X_train, y_train)

# Predict upcoming
pred = model.predict(upcoming[["targets", "receptions"]])
upcoming["pred_rec_yards"] = pred

# Save
upcoming.to_csv("prop_projections_receiving.csv", index=False)
print("Saved: prop_projections_receiving.csv")
print(upcoming[["targets", "receptions", "pred_rec_yards"]].head(10))

