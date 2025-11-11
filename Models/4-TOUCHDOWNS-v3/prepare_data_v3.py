#!/usr/bin/env python3
"""
Build training features/labels for Anytime TD (WR/RB/TE + QB rushing-only) - v3
Enhanced version combining best of v1 and v2 approaches.
"""

import pandas as pd
import numpy as np
import os


def build_training_dataset() -> pd.DataFrame:
    player_stats = pd.read_csv("data/player_stats_pfr.csv", low_memory=False)
    schedule = pd.read_csv("data/schedule_game_results_pfr.csv")
    team_conv = pd.read_csv("data/team_conversions_pfr.csv")
    game_logs_path = "data/game_logs_pfr.csv"

    df = player_stats.copy()
    df = df.rename(
        columns={
            "player": "full_name",
            "opponent_team": "opp",
            "rush_att": "rush_att",
            "rush_yds": "rush_yds",
            "rush_td": "rush_td",
            "targets": "targets",
            "rec": "rec",
            "rec_yds": "rec_yds",
            "rec_td": "rec_td",
        }
    )

    df["scoring_tds"] = df[["rush_td", "rec_td"]].fillna(0).sum(axis=1)
    df["label_any"] = (df["scoring_tds"] > 0).astype(int)
    df["label_qb_rush"] = (df["rush_td"].fillna(0) > 0).astype(int)

    df["home_flag"] = (df["home"].astype(str).str.lower().eq("y")).astype(int)

    try:
        roster_map = pd.read_csv("data/roster_2025.csv", low_memory=False)
        if "pfr_id" in roster_map.columns:
            roster_map = roster_map[["pfr_id", "position"]].dropna()
            roster_map["player_id"] = roster_map["pfr_id"].astype(str) + ".htm"
            pos_map = roster_map[["player_id", "position"]].drop_duplicates()
            df = df.merge(pos_map, on="player_id", how="left", suffixes=("", "_roster"))
            df["position"] = df["position"].fillna(df["position_roster"])
            df = df.drop(columns=["position_roster"])
    except Exception:
        pass

    ratings = schedule[["Team", "Season", "Offense", "Defense"]].drop_duplicates()
    ratings = ratings.rename(columns={"Team": "team", "Season": "season"})
    df = df.merge(ratings, on=["team", "season"], how="left")
    opp_ratings = ratings.rename(columns={"team": "opp"})
    opp_ratings = opp_ratings.rename(columns={"Offense": "opp_offense", "Defense": "opp_defense"})
    df = df.merge(opp_ratings, on=["opp", "season"], how="left")

    rz = team_conv.rename(columns={"Team": "team", "Year": "season"})
    rz = rz[["team", "season", "RZAtt", "RZTD", "RZPct"]].drop_duplicates()
    df = df.merge(rz, on=["team", "season"], how="left")
    df["rz_td_pct"] = df["RZPct"]
    df["rz_att_pg"] = df["RZAtt"]

    pos_mask = df["position"].isin(["WR", "RB", "TE", "QB"])
    pos_df = df[pos_mask].copy()
    pos_df["td_any_flag"] = (pos_df["scoring_tds"] > 0).astype(int)
    pos_df["td_qb_rush_flag"] = ((pos_df["position"] == "QB") & (pos_df["rush_td"].fillna(0) > 0)).astype(int)

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

    df = df.sort_values(["player_id", "season", "week"]).reset_index(drop=True)

    windows = [2, 3, 5, 8, 12]
    base_feats = ["rush_att", "rush_yds", "targets", "rec", "rec_yds", "scoring_tds"]
    
    for feat in base_feats:
        for w in windows:
            df[f"{feat}_rm{w}"] = (
                df.groupby("player_id")[feat]
                .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
            )

    df["touches"] = df[["rush_att", "targets", "rec"]].fillna(0).sum(axis=1)
    for w in windows:
        df[f"touches_rm{w}"] = (
            df.groupby("player_id")["touches"]
            .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
        )

    df["td_rate"] = np.where(df["touches"] > 0, df["scoring_tds"] / df["touches"], 0)
    for w in windows:
        df[f"td_rate_rm{w}"] = (
            df.groupby("player_id")["td_rate"]
            .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
        )

    df["consecutive_td"] = (
        df.groupby("player_id")["scoring_tds"]
        .transform(lambda s: (s > 0).groupby((s != (s > 0)).cumsum()).cumsum())
    )
    df["consecutive_td_rm3"] = (
        df.groupby("player_id")["consecutive_td"]
        .transform(lambda s: s.shift(1).rolling(3, min_periods=1).max())
    )

    if os.path.exists(game_logs_path):
        game_logs = pd.read_csv(game_logs_path)
        parts = game_logs["game_id"].str.split("_", expand=True)
        game_logs["season"] = parts[0].astype(int)
        game_logs["week"] = parts[1].astype(int)
        game_logs["away_team"] = parts[2]
        game_logs["home_team"] = parts[3]
        game_logs["home_td_scored"] = game_logs["home_pass_td"].fillna(0) + game_logs["home_rush_td"].fillna(0)
        game_logs["away_td_scored"] = game_logs["away_pass_td"].fillna(0) + game_logs["away_rush_td"].fillna(0)
        game_logs["home_td_allowed"] = game_logs["away_td_scored"]
        game_logs["away_td_allowed"] = game_logs["home_td_scored"]

        home_rows = game_logs[["season", "week", "home_team", "home_td_scored", "home_td_allowed"]].rename(
            columns={"home_team": "team", "home_td_scored": "td_scored", "home_td_allowed": "td_allowed"}
        )
        away_rows = game_logs[["season", "week", "away_team", "away_td_scored", "away_td_allowed"]].rename(
            columns={"away_team": "team", "away_td_scored": "td_scored", "away_td_allowed": "td_allowed"}
        )
        team_games = pd.concat([home_rows, away_rows], ignore_index=True)
        team_games = team_games.sort_values(["team", "season", "week"]).reset_index(drop=True)

        grouped = team_games.groupby(["team", "season"], group_keys=False)
        for col in ["td_scored", "td_allowed"]:
            rolling = grouped[col].apply(lambda s: s.shift().rolling(window=3, min_periods=1).mean())
            expanding = grouped[col].apply(lambda s: s.shift().expanding().mean())
            feature = rolling.fillna(expanding)
            feature = feature.fillna(team_games[col].mean())
            team_games[f"{col}_rolling"] = feature

        df = df.merge(
            team_games[["season", "week", "team", "td_scored_rolling", "td_allowed_rolling"]],
            on=["season", "week", "team"],
            how="left",
        )
        opp_team_games = team_games.rename(columns={"team": "opp"})
        df = df.merge(
            opp_team_games[["season", "week", "opp", "td_scored_rolling", "td_allowed_rolling"]],
            on=["season", "week", "opp"],
            how="left",
            suffixes=("", "_opp"),
        )
        df["opp_td_scored_rolling"] = df["td_scored_rolling_opp"]
        df["opp_td_allowed_rolling"] = df["td_allowed_rolling_opp"]
        df = df.drop(columns=["td_scored_rolling_opp", "td_allowed_rolling_opp"])

    keep_cols = [
        "full_name",
        "player_id",
        "team",
        "opp",
        "home_flag",
        "position",
        "season",
        "week",
        "label_any",
        "label_qb_rush",
        "Offense",
        "Defense",
        "opp_offense",
        "opp_defense",
        "rz_td_pct",
        "rz_att_pg",
        "opp_td_rate_pos",
        "opp_td_rate_qb_rush",
    ] + [f"{f}_rm{w}" for f in base_feats for w in windows] + \
        [f"touches_rm{w}" for w in windows] + \
        [f"td_rate_rm{w}" for w in windows] + \
        ["consecutive_td_rm3"]

    if "td_scored_rolling" in df.columns:
        keep_cols.extend(["td_scored_rolling", "td_allowed_rolling", "opp_td_scored_rolling", "opp_td_allowed_rolling"])

    out = df[keep_cols].copy()
    out.to_csv("data/model_train.csv", index=False)
    return out


def build_upcoming_players():
    upcoming = pd.read_csv("data/upcoming_games.csv")
    roster = pd.read_csv("data/roster_2025.csv", low_memory=False)
    starting_qbs = pd.read_csv("data/starting_qbs_2025.csv")

    injured_path = "injured_players.csv"
    questionable_path = "questionable_players.csv"
    if not os.path.exists(injured_path):
        injured_path = "../injured_players.csv"
    if not os.path.exists(questionable_path):
        questionable_path = "../questionable_players.csv"

    injured_df = pd.read_csv(injured_path) if os.path.exists(injured_path) else pd.DataFrame(columns=["player", "status"])
    questionable_df = pd.read_csv(questionable_path) if os.path.exists(questionable_path) else pd.DataFrame(columns=["player", "status"])

    home = upcoming.rename(columns={"home_team": "team", "away_team": "opp"})
    away = upcoming.rename(columns={"away_team": "team", "home_team": "opp"})
    schedule_pairs = pd.concat([home, away], ignore_index=True)

    r = roster[(roster["season"] == 2025)]
    r = r.merge(schedule_pairs, on="team", how="inner")
    r = r[r["position"].isin(["QB", "RB", "WR", "TE"])]

    qb_starters = starting_qbs.rename(columns={"team": "team", "starting_qb": "full_name"})
    qb_starters["position"] = "QB"
    non_qb = r[r["position"] != "QB"]
    qb = r[r["position"] == "QB"][["team", "full_name", "position", "pfr_id"]]
    qb = qb.merge(qb_starters[["team", "full_name"]], on=["team", "full_name"], how="inner")
    r = pd.concat([non_qb, qb], ignore_index=True)

    if not injured_df.empty:
        name_col = "player" if "player" in injured_df.columns else ("full_name" if "full_name" in injured_df.columns else None)
        if name_col:
            out_names = set(injured_df[name_col].astype(str).str.strip().tolist())
            r = r[~r["full_name"].astype(str).isin(out_names)]

    if not questionable_df.empty:
        qcol = "player" if "player" in questionable_df.columns else ("full_name" if "full_name" in questionable_df.columns else None)
        if qcol:
            q_names = set(questionable_df[qcol].astype(str).str.strip().tolist())
            r = r[~r["full_name"].astype(str).isin(q_names)]

    r["injury_status"] = ""

    if "pfr_id" in r.columns:
        r["player_id"] = r["pfr_id"].astype(str) + ".htm"
    else:
        r["player_id"] = ""

    r = r.merge(
        upcoming,
        left_on=["team"],
        right_on=["home_team"],
        how="left",
        suffixes=("", "_home"),
    )
    r["home_flag"] = (r["opp"].eq(r["away_team"])).astype(int)
    r = r.drop(columns=["home_team", "away_team"])

    keep_cols = ["full_name", "player_id", "team", "opp", "position", "home_flag", "injury_status"]
    out = r[keep_cols].drop_duplicates().reset_index(drop=True)
    out.to_csv("data/upcoming_players.csv", index=False)
    return out


def main():
    print("Preparing Anytime TD datasets (4-TOUCHDOWNS-v3)...")
    os.makedirs("data", exist_ok=True)
    train_df = build_training_dataset()
    print(f"Wrote training dataset: data/model_train.csv ({len(train_df)} rows)")
    up_df = build_upcoming_players()
    print(f"Wrote upcoming players: data/upcoming_players.csv ({len(up_df)} rows)")
    print("Done.")


if __name__ == "__main__":
    main()
