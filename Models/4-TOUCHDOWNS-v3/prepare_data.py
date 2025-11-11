#!/usr/bin/env python3

import os
import pandas as pd


def build_training_dataset() -> pd.DataFrame:
    player_stats = pd.read_csv("data/player_stats_pfr.csv", low_memory=False)
    schedule = pd.read_csv("data/schedule_game_results_pfr.csv")
    team_conv = pd.read_csv("data/team_conversions_pfr.csv")
    roster = pd.read_csv("data/roster_2025.csv", low_memory=False)

    df = player_stats.rename(
        columns={
            "player": "full_name",
            "opponent_team": "opp",
        }
    )

    df["rush_att"] = df["rush_att"].fillna(0.0)
    df["rush_yds"] = df["rush_yds"].fillna(0.0)
    df["rush_td"] = df["rush_td"].fillna(0.0)
    df["targets"] = df["targets"].fillna(0.0)
    df["rec"] = df["rec"].fillna(0.0)
    df["rec_yds"] = df["rec_yds"].fillna(0.0)
    df["rec_td"] = df["rec_td"].fillna(0.0)
    df["fantasy_points_ppr"] = df["fantasy_points_ppr"].fillna(0.0)

    df["scoring_tds"] = df[["rush_td", "rec_td"]].sum(axis=1)
    df["label_any"] = (df["scoring_tds"] > 0).astype(int)
    df["label_qb_rush"] = ((df["position"] == "QB") & (df["rush_td"] > 0)).astype(int)
    df["home_flag"] = df["home"].astype(str).str.lower().eq("y").astype(int)
    df["touches"] = df[["rush_att", "targets", "rec"]].sum(axis=1)
    df["yards_from_scrimmage"] = df["rush_yds"] + df["rec_yds"]
    df["games_played"] = df.groupby("player_id").cumcount()

    roster_map = roster[["pfr_id", "position"]].dropna()
    roster_map["player_id"] = roster_map["pfr_id"].astype(str) + ".htm"
    df = df.merge(
        roster_map[["player_id", "position"]],
        on="player_id",
        how="left",
        suffixes=("", "_roster"),
    )
    df["position"] = df["position"].fillna(df["position_roster"])
    df = df.drop(columns=["position_roster"])

    ratings = schedule[["Team", "Season", "Offense", "Defense"]].drop_duplicates()
    ratings = ratings.rename(columns={"Team": "team", "Season": "season"})
    df = df.merge(ratings, on=["team", "season"], how="left")
    opp_ratings = ratings.rename(columns={"team": "opp"})
    opp_ratings = opp_ratings.rename(
        columns={"Offense": "opp_offense", "Defense": "opp_defense"}
    )
    df = df.merge(opp_ratings, on=["opp", "season"], how="left")

    rz = team_conv.rename(columns={"Team": "team", "Year": "season"})
    rz = rz[["team", "season", "RZAtt", "RZTD", "RZPct"]].drop_duplicates()
    df = df.merge(rz, on=["team", "season"], how="left")
    df["rz_td_pct"] = df["RZPct"]
    df["rz_att_pg"] = df["RZAtt"]

    pos_mask = df["position"].isin(["WR", "RB", "TE", "QB"])
    pos_df = df[pos_mask].copy()
    pos_df["td_any_flag"] = (pos_df["scoring_tds"] > 0).astype(int)
    pos_df["td_qb_rush_flag"] = (
        (pos_df["position"] == "QB") & (pos_df["rush_td"] > 0)
    ).astype(int)

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
    windows = [3, 5, 8, 12]
    base_feats = [
        "rush_att",
        "rush_yds",
        "targets",
        "rec",
        "rec_yds",
        "scoring_tds",
        "touches",
        "fantasy_points_ppr",
        "yards_from_scrimmage",
    ]
    for feat in base_feats:
        for w in windows:
            df[f"{feat}_rm{w}"] = (
                df.groupby("player_id")[feat]
                .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
            )

    df["season_tds_to_date"] = (
        df.groupby(["player_id", "season"])["scoring_tds"]
        .transform(lambda s: s.shift(1).cumsum())
        .fillna(0.0)
    )
    df["season_touches_to_date"] = (
        df.groupby(["player_id", "season"])["touches"]
        .transform(lambda s: s.shift(1).cumsum())
        .fillna(0.0)
    )

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
        "touches",
        "fantasy_points_ppr",
        "yards_from_scrimmage",
        "games_played",
        "season_tds_to_date",
        "season_touches_to_date",
    ] + [f"{f}_rm{w}" for f in base_feats for w in windows]

    out = df[keep_cols].copy()
    out.to_csv("data/model_train_v3.csv", index=False)
    return out


def build_upcoming_players() -> pd.DataFrame:
    upcoming = pd.read_csv("data/upcoming_games.csv")
    roster = pd.read_csv("data/roster_2025.csv", low_memory=False)
    starting_qbs = pd.read_csv("data/starting_qbs_2025.csv")

    injured_path = "data/injured_players.csv"
    questionable_path = "data/questionable_players.csv"

    injured_df = (
        pd.read_csv(injured_path)
        if os.path.exists(injured_path)
        else pd.DataFrame(columns=["player", "status"])
    )
    questionable_df = (
        pd.read_csv(questionable_path)
        if os.path.exists(questionable_path)
        else pd.DataFrame(columns=["player", "status"])
    )

    home = upcoming.rename(columns={"home_team": "team", "away_team": "opp"})
    away = upcoming.rename(columns={"away_team": "team", "home_team": "opp"})
    schedule_pairs = pd.concat([home, away], ignore_index=True)

    roster_year = roster[roster["season"] == 2025]
    roster_year = roster_year.merge(schedule_pairs, on="team", how="inner")
    roster_year = roster_year[roster_year["position"].isin(["QB", "RB", "WR", "TE"])]

    qb_map = starting_qbs.rename(columns={"team": "team", "starting_qb": "full_name"})
    qb_map["position"] = "QB"
    qb = roster_year[roster_year["position"] == "QB"][["team", "full_name", "position", "pfr_id"]]
    qb = qb.merge(qb_map[["team", "full_name"]], on=["team", "full_name"], how="inner")
    non_qb = roster_year[roster_year["position"] != "QB"]
    roster_year = pd.concat([non_qb, qb], ignore_index=True)

    if not injured_df.empty:
        injured_names = set(injured_df.iloc[:, 0].astype(str).str.strip())
        roster_year = roster_year[~roster_year["full_name"].astype(str).isin(injured_names)]

    if not questionable_df.empty:
        questionable_names = set(questionable_df.iloc[:, 0].astype(str).str.strip())
        roster_year = roster_year[~roster_year["full_name"].astype(str).isin(questionable_names)]

    if "pfr_id" in roster_year.columns:
        roster_year["player_id"] = roster_year["pfr_id"].astype(str) + ".htm"
    else:
        roster_year["player_id"] = ""

    roster_year = roster_year.merge(
        upcoming,
        left_on="team",
        right_on="home_team",
        how="left",
        suffixes=("", "_home"),
    )
    roster_year["home_flag"] = roster_year["opp"].eq(roster_year["away_team"]).astype(int)
    roster_year = roster_year.drop(columns=["home_team", "away_team"])

    out = roster_year[
        ["full_name", "player_id", "team", "opp", "position", "home_flag"]
    ].drop_duplicates()
    out.to_csv("data/upcoming_players_v3.csv", index=False)
    return out


def main():
    os.makedirs("data", exist_ok=True)
    train_df = build_training_dataset()
    print(f"Saved data/model_train_v3.csv ({len(train_df)} rows)")
    upcoming_df = build_upcoming_players()
    print(f"Saved data/upcoming_players_v3.csv ({len(upcoming_df)} rows)")


if __name__ == "__main__":
    main()

