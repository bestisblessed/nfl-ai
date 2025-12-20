import os
import sys

import pandas as pd
import plotly.express as px


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Websites", "Streamlit"))

from utils.matchup_report import (  # noqa: E402
    NFL_BLUE,
    NFL_RED,
    PUSH_GRAY,
    calculate_defense_summary,
    compute_head_to_head_bets,
    compute_top_skill_performers,
    generate_html_report,
    get_redzone_targets,
    get_team_color,
)


def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def _extract_body(html: str) -> str:
    body_start = html.find("<body>")
    body_end = html.rfind("</body>")
    return html[body_start + len("<body>") : body_end]


def _extract_style(html: str) -> str:
    s = html.find("<style>")
    e = html.find("</style>")
    return html[s + len("<style>") : e]


def _write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _render_pdf_and_png(html_path: str, pdf_path: str, png_path: str) -> None:
    from playwright.sync_api import sync_playwright

    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    os.makedirs(os.path.dirname(png_path), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(f"file://{os.path.abspath(html_path)}", wait_until="networkidle")
        page.emulate_media(media="screen")
        page.pdf(path=pdf_path, format="Letter", print_background=True, margin={"top": "0.4in", "bottom": "0.4in"})
        page.screenshot(path=png_path, full_page=True)
        browser.close()


def _build_matchup_report_data(
    df_games: pd.DataFrame,
    df_playerstats: pd.DataFrame,
    df_roster2025: pd.DataFrame,
    df_team_game_logs: pd.DataFrame,
    df_defense_logs: pd.DataFrame,
    df_redzone: pd.DataFrame,
    team1: str,
    team2: str,
) -> dict:
    team_matchups = df_games[
        ((df_games["home_team"] == team1) & (df_games["away_team"] == team2))
        | ((df_games["home_team"] == team2) & (df_games["away_team"] == team1))
    ]
    completed_matchups = team_matchups.dropna(subset=["home_score", "away_score"])
    last_10_games = completed_matchups.sort_values(by="date", ascending=False).head(10)

    if last_10_games.empty:
        h2h = compute_head_to_head_bets(df_games, team1, team2, limit=10)
        return {
            "summary_stats": {
                "games_analyzed": 0,
                "team1_wins": 0,
                "team2_wins": 0,
                "winning_streak": 0,
                "winner_team": "N/A",
                "team1_ppg": 0.0,
                "team2_ppg": 0.0,
                "avg_total_points": 0.0,
                "over_50_games": 0,
            },
            "h2h_betting": {
                "team1_ats": h2h["team1_ats"],
                "team2_ats": h2h["team2_ats"],
                "ou": h2h["ou"],
                "fav_dog": h2h["fav_dog"],
            },
            "defense_data": {
                "team1": calculate_defense_summary(df_defense_logs, df_team_game_logs, team1, last_n_games=10, df_games_ctx=df_games),
                "team2": calculate_defense_summary(df_defense_logs, df_team_game_logs, team2, last_n_games=10, df_games_ctx=df_games),
            },
            "top_performers": {"team1": pd.DataFrame(), "team2": pd.DataFrame()},
            "redzone_targets": {"team1": pd.DataFrame(), "team2": pd.DataFrame()},
            "pie_charts": {"ats_chart": None, "ou_chart": None},
            "historical_stats": {"team1": pd.DataFrame(), "team2": pd.DataFrame()},
        }

    total_points = last_10_games["home_score"] + last_10_games["away_score"]
    average_total_points = total_points.mean()
    team1_wins = int(
        (((last_10_games["home_team"] == team1) & (last_10_games["home_score"] > last_10_games["away_score"])).sum())
        + (((last_10_games["away_team"] == team1) & (last_10_games["away_score"] > last_10_games["home_score"])).sum())
    )
    team2_wins = int(
        (((last_10_games["home_team"] == team2) & (last_10_games["home_score"] > last_10_games["away_score"])).sum())
        + (((last_10_games["away_team"] == team2) & (last_10_games["away_score"] > last_10_games["home_score"])).sum())
    )

    team1_scores = last_10_games.loc[last_10_games["home_team"] == team1, "home_score"].sum() + last_10_games.loc[
        last_10_games["away_team"] == team1, "away_score"
    ].sum()
    team2_scores = last_10_games.loc[last_10_games["home_team"] == team2, "home_score"].sum() + last_10_games.loc[
        last_10_games["away_team"] == team2, "away_score"
    ].sum()

    num_h2h_games = len(last_10_games)
    team1_ppg = float(team1_scores) / num_h2h_games if num_h2h_games > 0 else 0.0
    team2_ppg = float(team2_scores) / num_h2h_games if num_h2h_games > 0 else 0.0
    over_50_points_games = int((total_points > 50).sum())

    recent_games_for_streak = last_10_games.sort_values(by="date", ascending=False)
    most_recent = recent_games_for_streak.iloc[0]
    winner_team = most_recent["home_team"] if most_recent["home_score"] > most_recent["away_score"] else most_recent["away_team"]

    streak = 0
    for _, g in recent_games_for_streak.iterrows():
        home_win = g["home_score"] > g["away_score"]
        away_win = g["away_score"] > g["home_score"]
        team_won = (home_win and g["home_team"] == winner_team) or (away_win and g["away_team"] == winner_team)
        if team_won:
            streak += 1
        else:
            break

    h2h = compute_head_to_head_bets(df_games, team1, team2, limit=10)
    ats_t1_w, _, ats_push = h2h["team1_ats"]
    ou_over, ou_under, ou_push = h2h["ou"]

    pie_ats = (
        px.pie(
            values=[ats_t1_w, h2h["team2_ats"][0], ats_push],
            names=[f"{team1} cover", f"{team2} cover", "Push"],
            hole=0.45,
            color_discrete_sequence=[get_team_color(team1), get_team_color(team2), PUSH_GRAY],
        )
        if (ats_t1_w + h2h["team2_ats"][0] + ats_push) > 0
        else None
    )
    pie_ou = (
        px.pie(
            values=[ou_over, ou_under, ou_push],
            names=["Over", "Under", "Push"],
            hole=0.45,
            color_discrete_sequence=[NFL_BLUE, NFL_RED, PUSH_GRAY],
        )
        if (ou_over + ou_under + ou_push) > 0
        else None
    )

    t1_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team1, last_n_games=10, df_games_ctx=df_games)
    t2_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team2, last_n_games=10, df_games_ctx=df_games)

    roster = df_roster2025
    roster_team1 = roster[(roster["season"] == 2025) & (roster["team"] == team1) & (~roster["status"].isin(["CUT", "RET"]))]
    roster_team2 = roster[(roster["season"] == 2025) & (roster["team"] == team2) & (~roster["status"].isin(["CUT", "RET"]))]
    players_team1_names = roster_team1["full_name"].dropna().unique()
    players_team2_names = roster_team2["full_name"].dropna().unique()

    historical_stats_team1 = pd.DataFrame(columns=df_playerstats.columns)
    historical_stats_team2 = pd.DataFrame(columns=df_playerstats.columns)

    if players_team1_names.size > 0:
        mask_names_t1 = df_playerstats["player_display_name"].isin(players_team1_names)
        mask_game_has_team2 = (df_playerstats["home_team"] == team2) | (df_playerstats["away_team"] == team2)
        mask_player_not_team2 = df_playerstats["player_current_team"] != team2
        historical_stats_team1 = df_playerstats[mask_names_t1 & mask_game_has_team2 & mask_player_not_team2]

    if players_team2_names.size > 0:
        mask_names_t2 = df_playerstats["player_display_name"].isin(players_team2_names)
        mask_game_has_team1 = (df_playerstats["home_team"] == team1) | (df_playerstats["away_team"] == team1)
        mask_player_not_team1 = df_playerstats["player_current_team"] != team1
        historical_stats_team2 = df_playerstats[mask_names_t2 & mask_game_has_team1 & mask_player_not_team1]

    if not historical_stats_team1.empty and "date" not in historical_stats_team1.columns:
        historical_stats_team1 = historical_stats_team1.merge(df_games[["game_id", "date"]], on="game_id", how="left")
    if not historical_stats_team2.empty and "date" not in historical_stats_team2.columns:
        historical_stats_team2 = historical_stats_team2.merge(df_games[["game_id", "date"]], on="game_id", how="left")

    if not historical_stats_team1.empty:
        historical_stats_team1 = historical_stats_team1.copy()
        historical_stats_team1.loc[:, "date"] = pd.to_datetime(historical_stats_team1["date"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        historical_stats_team1.loc[:, "player_name_with_position"] = historical_stats_team1["player_display_name"] + " (" + historical_stats_team1["position"] + ")"
    if not historical_stats_team2.empty:
        historical_stats_team2 = historical_stats_team2.copy()
        historical_stats_team2.loc[:, "date"] = pd.to_datetime(historical_stats_team2["date"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        historical_stats_team2.loc[:, "player_name_with_position"] = historical_stats_team2["player_display_name"] + " (" + historical_stats_team2["position"] + ")"

    t1_top = compute_top_skill_performers(historical_stats_team1, top_n=4)
    t2_top = compute_top_skill_performers(historical_stats_team2, top_n=4)
    rz_t1 = get_redzone_targets(df_redzone, team1, year=2025)
    rz_t2 = get_redzone_targets(df_redzone, team2, year=2025)

    return {
        "summary_stats": {
            "games_analyzed": len(last_10_games),
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "winning_streak": streak,
            "winner_team": winner_team,
            "team1_ppg": team1_ppg,
            "team2_ppg": team2_ppg,
            "avg_total_points": average_total_points,
            "over_50_games": over_50_points_games,
        },
        "h2h_betting": {"team1_ats": h2h["team1_ats"], "team2_ats": h2h["team2_ats"], "ou": h2h["ou"], "fav_dog": h2h["fav_dog"]},
        "defense_data": {"team1": t1_def_early, "team2": t2_def_early},
        "top_performers": {"team1": t1_top, "team2": t2_top},
        "redzone_targets": {"team1": rz_t1, "team2": rz_t2},
        "pie_charts": {"ats_chart": pie_ats, "ou_chart": pie_ou},
        "historical_stats": {"team1": historical_stats_team1, "team2": historical_stats_team2},
    }


def main() -> None:
    week = int(sys.argv[1])

    data_dir = os.path.join(os.path.dirname(__file__), "Websites", "Streamlit", "data")
    df_games = _read_csv(os.path.join(data_dir, "Games.csv"))
    df_playerstats = _read_csv(os.path.join(data_dir, "all_passing_rushing_receiving.csv"))

    df_playerstats["player_display_name"] = df_playerstats["player"]
    df_playerstats["player_current_team"] = df_playerstats["team"]
    df_playerstats["passing_yards"] = df_playerstats["pass_yds"]
    df_playerstats["rushing_yards"] = df_playerstats["rush_yds"]
    df_playerstats["receiving_yards"] = df_playerstats["rec_yds"]
    df_playerstats["passing_tds"] = df_playerstats["pass_td"]
    df_playerstats["rushing_tds"] = df_playerstats["rush_td"]
    df_playerstats["receiving_tds"] = df_playerstats["rec_td"]
    df_playerstats["completions"] = df_playerstats["pass_cmp"]
    df_playerstats["attempts"] = df_playerstats["pass_att"]
    df_playerstats["interceptions"] = df_playerstats["pass_int"]
    df_playerstats["sacks"] = df_playerstats["pass_sacked"]
    df_playerstats["carries"] = df_playerstats["rush_att"]
    df_playerstats["receptions"] = df_playerstats["rec"]

    game_id_parts = df_playerstats["game_id"].astype(str).str.split("_", expand=True)
    df_playerstats["week"] = pd.to_numeric(game_id_parts[1], errors="coerce")
    df_playerstats["away_team"] = game_id_parts[2]
    df_playerstats["home_team"] = game_id_parts[3]

    df_roster2025 = _read_csv(os.path.join(data_dir, "rosters", "roster_2025.csv"))
    df_roster2025["team"] = df_roster2025["team"].map(lambda x: {"LV": "LVR", "LA": "LAR"}.get(x, x))

    df_team_game_logs = _read_csv(os.path.join(data_dir, "all_team_game_logs.csv"))
    df_defense_logs = _read_csv(os.path.join(data_dir, "all_defense-game-logs.csv"))
    df_defense_logs["team"] = df_defense_logs["team"].map(
        lambda x: {"GNB": "GB", "KAN": "KC", "NOR": "NO", "NWE": "NE", "OAK": "LVR", "SFO": "SF", "TAM": "TB"}.get(x, x)
    )
    df_redzone = _read_csv(os.path.join(data_dir, "all_redzone.csv"))

    df_games = df_games.copy()
    df_games["season_num"] = pd.to_numeric(df_games["season"], errors="coerce")
    df_games["week_num"] = pd.to_numeric(df_games["week"], errors="coerce")
    df_games["date"] = pd.to_datetime(df_games["date"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    season = int(df_games["season_num"].max())
    week_games = df_games[(df_games["season_num"] == season) & (df_games["week_num"] == week) & (df_games["game_type"] == "REG")].copy()
    week_games = week_games.sort_values(["date", "gametime"])

    out_dir = os.path.join(os.path.dirname(__file__), "reports", f"week{week}")
    os.makedirs(out_dir, exist_ok=True)

    per_game_html_paths = []
    for _, g in week_games.iterrows():
        away = str(g["away_team"])
        home = str(g["home_team"])
        report_data = _build_matchup_report_data(
            df_games=df_games,
            df_playerstats=df_playerstats,
            df_roster2025=df_roster2025,
            df_team_game_logs=df_team_game_logs,
            df_defense_logs=df_defense_logs,
            df_redzone=df_redzone,
            team1=away,
            team2=home,
        )
        html = generate_html_report(away, home, report_data)
        html_path = os.path.join(out_dir, f"{away}_vs_{home}_matchup_report.html")
        _write_text(html_path, html)
        per_game_html_paths.append(html_path)

    index_body = []
    first_style = ""
    for i, p in enumerate(per_game_html_paths):
        html = open(p, "r", encoding="utf-8").read()
        if i == 0:
            first_style = _extract_style(html)
        body = _extract_body(html)
        index_body.append(f'<div class="week-break">{body}</div><div class="pagebreak"></div>')

    weekly_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Week {week} Matchup Reports</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
  {first_style}
  .pagebreak {{ page-break-after: always; break-after: page; }}
  .week-break {{ margin-bottom: 30px; }}
  </style>
</head>
<body>
  {''.join(index_body)}
</body>
</html>
"""
    weekly_html_path = os.path.join(out_dir, f"week{week}_weekly_matchup_report.html")
    _write_text(weekly_html_path, weekly_html)

    weekly_pdf_path = os.path.join(out_dir, f"week{week}_weekly_matchup_report.pdf")
    weekly_png_path = os.path.join(out_dir, f"week{week}_weekly_matchup_report.png")
    _render_pdf_and_png(weekly_html_path, weekly_pdf_path, weekly_png_path)


if __name__ == "__main__":
    main()

