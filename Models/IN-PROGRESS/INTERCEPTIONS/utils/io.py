"""File I/O utilities"""
import csv
import os


def write_odds_csv(rows: list, output_path: str):
    """Write odds data to CSV file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        "player",
        "team",
        "opponent",
        "home_away",
        "line",
        "over_american_odds",
        "under_american_odds",
        "event_id",
        "start_time",
        "source",
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    
    print(f"Saved {len(rows)} rows to {output_path}")
