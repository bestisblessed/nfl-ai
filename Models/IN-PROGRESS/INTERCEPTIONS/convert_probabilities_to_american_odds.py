import os
import re
import argparse
import pandas as pd


p = argparse.ArgumentParser(description="Convert QB interception probabilities to American betting odds.")
p.add_argument("--week", type=int, default=None)
p.add_argument("--model", type=str, default="logistic_regression", choices=["logistic_regression", "random_forest", "xgboost"])
p.add_argument("--path", type=str, default=None)
a = p.parse_args()

d = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/predictions"
f = a.path if a.path else (os.path.join(d, f"upcoming_qb_interception_probs_{a.model}_week_{a.week}.csv") if a.week is not None else None)
if not f:
    w0, f0 = None, None
    for n in os.listdir(d):
        m = re.match(r"upcoming_qb_interception_probs_(\w+)_week_(\d+)\.csv$", n)
        if m and m.group(1) == a.model and (w0 is None or int(m.group(2)) > w0): w0, f0 = int(m.group(2)), os.path.join(d, n)
    if not f0: raise FileNotFoundError(f"No predictions files found for model {a.model} in {d}")
    f, a.week = f0, w0
elif not os.path.exists(f):
    raise FileNotFoundError(f"Predictions file not found: {f}")
elif a.week is None or a.model == "logistic_regression":
    m = re.search(r"upcoming_qb_interception_probs_(\w+)_week_(\d+)\.csv$", os.path.basename(f))
    if m:
        a.model, a.week = m.group(1), int(m.group(2))
    else:
        m = re.search(r"week_(\d+)", os.path.basename(f)); a.week = int(m.group(1)) if m else 0

df = pd.read_csv(f)
if 'interception_prob' not in df.columns or 'no_interception_prob' not in df.columns:
    raise ValueError("Missing columns: interception_prob, no_interception_prob")

pi = df['interception_prob'].clip(1e-9, 1-1e-9)
pno = df['no_interception_prob'].clip(1e-9, 1-1e-9)
df['interception_american_odds'] = (-((pi/(1-pi))*100).round().astype(int)).where(pi>=0.5, (((1-pi)/pi)*100).round().astype(int))
df['no_interception_american_odds'] = (-((pno/(1-pno))*100).round().astype(int)).where(pno>=0.5, (((1-pno)/pno)*100).round().astype(int))

# Overwrite original file with American odds instead of probabilities
# df.drop(columns=['interception_prob', 'no_interception_prob'], inplace=True)
df.to_csv(f, index=False)

try:
    from tabulate import tabulate
    df_display = df.copy()
    df_display['interception_american_odds'] = df_display['interception_american_odds'].apply(lambda v: f"+{v}" if v>0 else str(v))
    df_display['no_interception_american_odds'] = df_display['no_interception_american_odds'].apply(lambda v: f"+{v}" if v>0 else str(v))
    print(tabulate(df_display, headers='keys', tablefmt='github', showindex=False))
except Exception:
    print(f"Updated {f} with American odds")