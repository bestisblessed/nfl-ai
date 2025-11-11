#!/usr/bin/env python3
"""
v3 Data Preparation: Combines best of v1 and v2
- Multi-window rolling features (3, 5, 8 games)
- Team-level offensive/defensive metrics
- Enhanced player features (target share, td trends)
- Better opponent matchup analysis
"""

import pandas as pd
import numpy as np
import os


def build_training_dataset():
    player_stats = pd.read_csv("../../Scrapers/final_data_pfr/player_stats_pfr.csv", low_memory=False)
    game_logs = pd.read_csv("../../Scrapers/final_data_pfr/game_logs_pfr.csv", low_memory=False)
    schedule = pd.read_csv("data/schedule_game_results_pfr.csv")
    team_conv = pd.read_csv("data/team_conversions_pfr.csv")
    
    df = player_stats.copy()
    df = df.rename(columns={
        "player": "full_name",
        "opponent_team": "opp",
    })
    
    # Core TD labels
    df["rush_td"] = df["rush_td"].fillna(0)
    df["rec_td"] = df["rec_td"].fillna(0)
    df["scoring_tds"] = df["rush_td"] + df["rec_td"]
    df["label_any"] = (df["scoring_tds"] > 0).astype(int)
    df["label_qb_rush"] = (df["rush_td"] > 0).astype(int)
    
    df["home_flag"] = (df["home"].astype(str).str.lower().eq("y")).astype(int)
    
    # Fill positions from roster
    try:
        roster_map = pd.read_csv("../data/rosters.csv", low_memory=False)
        if "pfr_id" in roster_map.columns:
            roster_map = roster_map[["pfr_id", "position", "season"]].dropna()
            roster_map["player_id"] = roster_map["pfr_id"].astype(str) + ".htm"
            pos_map = roster_map[["player_id", "position", "season"]].drop_duplicates()
            df = df.merge(pos_map, on=["player_id", "season"], how="left", suffixes=("", "_roster"))
            df["position"] = df["position"].fillna(df["position_roster"])
            df = df.drop(columns=["position_roster"], errors="ignore")
    except Exception as e:
        print(f"Warning: Could not load roster data: {e}")
    
    # Team offensive/defensive ratings from schedule
    ratings = schedule[["Team", "Season", "Offense", "Defense"]].drop_duplicates()
    ratings = ratings.rename(columns={"Team": "team", "Season": "season"})
    df = df.merge(ratings, on=["team", "season"], how="left")
    
    opp_ratings = ratings.rename(columns={"team": "opp"})
    opp_ratings = opp_ratings.rename(columns={"Offense": "opp_offense", "Defense": "opp_defense"})
    df = df.merge(opp_ratings, on=["opp", "season"], how="left")
    
    # Red zone stats
    rz = team_conv.rename(columns={"Team": "team", "Year": "season"})
    rz = rz[["team", "season", "RZAtt", "RZTD", "RZPct"]].drop_duplicates()
    df = df.merge(rz, on=["team", "season"], how="left")
    df["rz_td_pct"] = df["RZPct"]
    df["rz_att_pg"] = df["RZAtt"]
    
    # Enhanced opponent TD rates by position
    pos_mask = df["position"].isin(["WR", "RB", "TE", "QB"])
    pos_df = df[pos_mask].copy()
    pos_df["td_any_flag"] = (pos_df["scoring_tds"] > 0).astype(int)
    pos_df["td_qb_rush_flag"] = ((pos_df["position"] == "QB") & (pos_df["rush_td"] > 0)).astype(int)
    
    allowed_any = (
        pos_df[pos_df["position"].isin(["WR", "RB", "TE"])]
        .groupby(["season", "opp", "position"])["td_any_flag"]
        .mean()
        .reset_index()
        .rename(columns={"td_any_flag": "opp_td_rate_pos"})
    )
    allowed_qb = (
        pos_df[pos_df["position"] == "QB"]
        .groupby(["season", "opp"])["td_qb_rush_flag"]
        .mean()
        .reset_index()
        .rename(columns={"td_qb_rush_flag": "opp_td_rate_qb_rush"})
    )
    df = df.merge(allowed_any, on=["season", "opp", "position"], how="left")
    df = df.merge(allowed_qb, on=["season", "opp"], how="left")
    
    # Calculate team-level passing/rushing volume per game for target share
    team_game_stats = df.groupby(["team", "season", "week"]).agg({
        "targets": "sum",
        "rec": "sum",
        "rush_att": "sum"
    }).reset_index()
    team_game_stats = team_game_stats.rename(columns={
        "targets": "team_total_targets",
        "rec": "team_total_rec",
        "rush_att": "team_total_rush_att"
    })
    df = df.merge(team_game_stats, on=["team", "season", "week"], how="left")
    
    # Player share metrics
    df["target_share"] = df["targets"] / df["team_total_targets"].replace(0, np.nan)
    df["rush_share"] = df["rush_att"] / df["team_total_rush_att"].replace(0, np.nan)
    df["target_share"] = df["target_share"].fillna(0).clip(0, 1)
    df["rush_share"] = df["rush_share"].fillna(0).clip(0, 1)
    
    df = df.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
    
    # Multi-window rolling features (3, 5, 8 games)
    windows = [3, 5, 8]
    base_feats = [
        "rush_att", "rush_yds", "targets", "rec", "rec_yds", 
        "scoring_tds", "target_share", "rush_share"
    ]
    
    for feat in base_feats:
        for w in windows:
            df[f"{feat}_rm{w}"] = (
                df.groupby("player_id")[feat]
                .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
            )
    
    # TD trend: recent 3 games vs previous 3 games
    df["tds_last3"] = df.groupby("player_id")["scoring_tds"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).sum()
    )
    df["tds_prev3"] = df.groupby("player_id")["scoring_tds"].transform(
        lambda s: s.shift(4).rolling(3, min_periods=1).sum()
    )
    df["td_trend"] = (df["tds_last3"] - df["tds_prev3"]).fillna(0)
    
    # Season expanding averages for key stats
    df["scoring_tds_season_avg"] = df.groupby(["player_id", "season"])["scoring_tds"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    df["targets_season_avg"] = df.groupby(["player_id", "season"])["targets"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    
    # Games played counter
    df["games_played_season"] = df.groupby(["player_id", "season"]).cumcount()
    
    keep_cols = [
        "full_name", "player_id", "team", "opp", "home_flag", "position",
        "season", "week", "label_any", "label_qb_rush",
        "Offense", "Defense", "opp_offense", "opp_defense",
        "rz_td_pct", "rz_att_pg",
        "opp_td_rate_pos", "opp_td_rate_qb_rush",
        "td_trend", "scoring_tds_season_avg", "targets_season_avg",
        "games_played_season"
    ]
    
    # Add all rolling features
    for feat in base_feats:
        for w in windows:
            keep_cols.append(f"{feat}_rm{w}")
    
    out = df[keep_cols].copy()
    out.to_csv("data/model_train.csv", index=False)
    print(f"Training data saved: {len(out)} rows")
    return out


def build_upcoming_players():
    upcoming = pd.read_csv("../upcoming_games.csv")
    roster = pd.read_csv("../data/rosters.csv", low_memory=False)
    starting_qbs = pd.read_csv("../starting_qbs_2025.csv")
    
    injured_path = "../injured_players.csv"
    questionable_path = "../questionable_players.csv"
    
    injured_df = pd.read_csv(injured_path) if os.path.exists(injured_path) else pd.DataFrame(columns=["player"])
    questionable_df = pd.read_csv(questionable_path) if os.path.exists(questionable_path) else pd.DataFrame(columns=["player"])
    
    home = upcoming.rename(columns={"home_team": "team", "away_team": "opp"})
    away = upcoming.rename(columns={"away_team": "team", "home_team": "opp"})
    schedule_pairs = pd.concat([home, away], ignore_index=True)
    
    r = roster[(roster["season"] == 2025)]
    r = r.merge(schedule_pairs, on="team", how="inner")
    r = r[r["position"].isin(["QB", "RB", "WR", "TE"])]
    
    # QB filtering: only starters
    qb_starters = starting_qbs.rename(columns={"team": "team", "starting_qb": "full_name"})
    qb_starters["position"] = "QB"
    non_qb = r[r["position"] != "QB"]
    qb = r[r["position"] == "QB"][["team", "full_name", "position", "pfr_id"]]
    qb = qb.merge(qb_starters[["team", "full_name"]], on=["team", "full_name"], how="inner")
    r = pd.concat([non_qb, qb], ignore_index=True)
    
    # Remove injured players
    if not injured_df.empty:
        name_col = "player" if "player" in injured_df.columns else "full_name"
        if name_col:
            out_names = set(injured_df[name_col].astype(str).str.strip().tolist())
            r = r[~r["full_name"].astype(str).isin(out_names)]
    
    # Remove questionable players
    if not questionable_df.empty:
        qcol = "player" if "player" in questionable_df.columns else "full_name"
        if qcol:
            q_names = set(questionable_df[qcol].astype(str).str.strip().tolist())
            r = r[~r["full_name"].astype(str).isin(q_names)]
    
    if "pfr_id" in r.columns:
        r["player_id"] = r["pfr_id"].astype(str) + ".htm"
    else:
        r["player_id"] = ""
    
    r = r.merge(upcoming, left_on=["team"], right_on=["home_team"], how="left", suffixes=("", "_home"))
    r["home_flag"] = (r["opp"].eq(r["away_team"])).astype(int)
    r = r.drop(columns=["home_team", "away_team"], errors="ignore")
    
    keep_cols = ["full_name", "player_id", "team", "opp", "position", "home_flag"]
    out = r[keep_cols].drop_duplicates().reset_index(drop=True)
    out.to_csv("data/upcoming_players.csv", index=False)
    print(f"Upcoming players saved: {len(out)} rows")
    return out


def main():
    print("Preparing v3 Touchdown datasets...")
    os.makedirs("data", exist_ok=True)
    train_df = build_training_dataset()
    up_df = build_upcoming_players()
    print("v3 data preparation complete.")


if __name__ == "__main__":
    main()
