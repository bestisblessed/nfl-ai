from datetime import date
from pathlib import Path
import pandas as pd
import sys

games_csv = Path("data/games.csv")
output = Path(__file__).parent / "upcoming_games.csv"
bye_output = Path(__file__).parent / "upcoming_bye_week.csv"
reference_date = pd.Timestamp(date.today())
game_type = "REG"
week = sys.argv[1] if len(sys.argv) > 1 else None

games = pd.read_csv(games_csv, parse_dates=["date"], keep_default_na=True)
pending = games[games["home_score"].isna() | games["away_score"].isna()].copy()
pending = pending[pending["game_type"] == game_type]

if week:
    week_key = str(int(week)) if week.isdigit() else week
    pending = pending[pending["week"].astype(str) == week_key]
    if pending.empty:
        raise ValueError(f"No unplayed games for week {week_key}")
    season = pending["season"].max()
    subset = pending[pending["season"] == season]
    resolved_week = week_key
    resolved_game_type = game_type
else:
    future = pending[pending["date"] >= reference_date]
    if future.empty:
        raise ValueError("No upcoming games")
    first = future.sort_values(["date", "gametime", "game_id"]).iloc[0]
    season = int(first["season"])
    resolved_week = str(int(first["week"])) if str(first["week"]).isdigit() else str(first["week"])
    resolved_game_type = str(first["game_type"])
    subset = pending[
        (pending["season"] == season)
        & (pending["week"].astype(str) == resolved_week)
        & (pending["game_type"] == resolved_game_type)
    ]

if subset.empty:
    raise ValueError("No matching games to export")

subset = subset.sort_values(["date", "gametime", "game_id"])
output.parent.mkdir(parents=True, exist_ok=True)
subset[["home_team", "away_team"]].to_csv(output, index=False)

playing_teams = set(subset["home_team"].tolist() + subset["away_team"].tolist())
all_teams = set(games["home_team"].unique().tolist() + games["away_team"].unique().tolist())
bye_teams = sorted(all_teams - playing_teams)

bye_df = pd.DataFrame({"team": bye_teams})
bye_df.to_csv(bye_output, index=False)

print(f"Saved {len(subset)} upcoming {resolved_game_type} games for week {resolved_week} of season {season} to {output}")
print(f"Saved {len(bye_teams)} bye week teams to {bye_output}")

# Automatically update QB files based on playing vs bye week teams
qb_main_file = Path(__file__).parent / "starting_qbs_2025.csv"
qb_bye_file = Path(__file__).parent / "starting_qbs_2025_bye.csv"
bye_teams_set = set(bye_teams)

# Combine all current QB assignments from both files (master list)
all_qbs = []

if qb_main_file.exists():
    main_qbs = pd.read_csv(qb_main_file)
    all_qbs.append(main_qbs)

if qb_bye_file.exists():
    # Read bye file - check if it has header or not
    # Check if file has content first
    with open(qb_bye_file, 'r') as f:
        content = f.read().strip()
    
    if content:  # Only read if file has content
        bye_qbs = pd.read_csv(qb_bye_file, names=['team', 'starting_qb'], header=None)
        # Remove any empty rows
        bye_qbs = bye_qbs.dropna(how='all')
        if len(bye_qbs) > 0:
            all_qbs.append(bye_qbs)

if all_qbs:
    # Combine into master list
    master_qbs = pd.concat(all_qbs, ignore_index=True)
    
    # Remove duplicates (in case a team appears in both files)
    master_qbs = master_qbs.drop_duplicates(subset=['team'], keep='first')
    
    # Separate into playing vs bye week
    playing_qbs = master_qbs[master_qbs['team'].isin(playing_teams)].copy()
    bye_qbs_updated = master_qbs[master_qbs['team'].isin(bye_teams_set)].copy()
    
    # Sort by team for consistency
    playing_qbs = playing_qbs.sort_values('team')
    bye_qbs_updated = bye_qbs_updated.sort_values('team')
    
    # Save updated files
    playing_qbs.to_csv(qb_main_file, index=False)
    bye_qbs_updated.to_csv(qb_bye_file, index=False, header=False)
    
    print(f"\n✅ Automatically updated QB files:")
    print(f"   - {len(playing_qbs)} teams in starting_qbs_2025.csv (playing teams)")
    print(f"   - {len(bye_qbs_updated)} teams in starting_qbs_2025_bye.csv (bye week teams)")
    
    # Show any teams that weren't in either list
    all_known_teams = playing_teams | bye_teams_set
    missing_teams = set(master_qbs['team'].tolist()) - all_known_teams
    if missing_teams:
        print(f"⚠️  Warning: {len(missing_teams)} team(s) not found in upcoming games or bye week:")
        for team in sorted(missing_teams):
            print(f"      - {team}")
else:
    print(f"\n⚠️  Warning: No QB files found. Skipping automatic QB file update.")
    print(f"   Expected files: {qb_main_file}, {qb_bye_file}")
