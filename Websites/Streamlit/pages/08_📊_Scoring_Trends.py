# <iframe src="https://claude.site/public/artifacts/1ca9aa13-a81f-491a-a1b3-459e08bc9948/embed" title="Claude Artifact" width="100%" height="600" frameborder="0" allow="clipboard-write" allowfullscreen></iframe>

import streamlit as st

st.title("NFL 2025 Defense TD Analysis")

# Direct iframe embed
st.components.v1.iframe(
    "https://claude.site/public/artifacts/1ca9aa13-a81f-491a-a1b3-459e08bc9948/embed",
    width=1000,   # adjust as needed
    height=600,
    scrolling=True
)

# Or if you need more control over styles
st.components.v1.html(
    """
    <div style="position:relative;padding-top:56.25%;">
      <iframe src="https://claude.site/public/artifacts/XXXX/embed"
              title="Claude Artifact"
              style="position:absolute;inset:0;width:100%;height:100%;border:0;"
              allow="clipboard-write; fullscreen"></iframe>
    </div>
    """,
    height=600
)


# import os
# import numpy as np
# import pandas as pd
# import streamlit as st
# import altair as alt

# # ------------------------- Page setup -------------------------
# st.set_page_config(page_title="Scoring Trends", page_icon="📊", layout="wide")
# st.title("📊 Scoring Trends")

# # ------------------------- Data loading -------------------------
# def load_data():
#     # 1) If the app already has a DataFrame in session_state, use it.
#     for k in ("games_df", "df_games", "nfl_games"):
#         if k in st.session_state and isinstance(st.session_state[k], pd.DataFrame):
#             return st.session_state[k].copy()

#     # 2) Optional: load from a default CSV path if your project has one.
#     default_csv = "data/games.csv"  # change if you already have a canonical path
#     if os.path.exists(default_csv):
#         return pd.read_csv(default_csv)

#     # 3) Fallback sample so the page renders without your data.
#     rng = np.random.default_rng(7)
#     weeks = np.arange(1, 19)
#     teams = ["BUF", "KC", "PHI", "DAL", "MIA", "SF", "NYJ", "CHI"]
#     rows = []
#     for season in [2023, 2024, 2025]:
#         for t in teams:
#             base = rng.integers(18, 29)  # base team strength
#             for w in weeks:
#                 pf = int(np.clip(base + rng.normal(0, 6), 6, 48))
#                 pa = int(np.clip(24 + rng.normal(0, 7), 6, 48))
#                 rows.append(
#                     dict(season=season, week=w, team=t, opponent=rng.choice(teams),
#                          points_for=pf, points_against=pa,
#                          total_points=pf+pa, home=bool(rng.integers(0,2)))
#                 )
#     return pd.DataFrame(rows)

# df = load_data()

# # Standardize expected columns
# expected = {
#     "season","week","team","opponent","points_for","points_against","total_points","home"
# }
# missing = expected.difference(df.columns)
# if missing:
#     st.error(f"Missing columns: {sorted(missing)}")
#     st.stop()

# # Coerce types
# df["season"] = df["season"].astype(int)
# df["week"] = df["week"].astype(int)
# df["points_for"] = df["points_for"].astype(float)
# df["points_against"] = df["points_against"].astype(float)
# df["total_points"] = df["total_points"].astype(float)
# df["home"] = df["home"].astype(bool)

# # ------------------------- Sidebar filters -------------------------
# with st.sidebar:
#     st.header("Filters")
#     seasons = sorted(df["season"].unique())
#     season = st.selectbox("Season", seasons, index=len(seasons)-1)

#     teams = sorted(df["team"].unique())
#     team = st.multiselect("Teams", teams, default=teams[:3])

#     min_w, max_w = int(df["week"].min()), int(df["week"].max())
#     week_range = st.slider("Weeks", min_value=min_w, max_value=max_w, value=(min_w, max_w))
#     home_away = st.selectbox("Venue", ["All", "Home", "Away"])

# # Apply filters
# mask = (df["season"] == season) & (df["week"].between(week_range[0], week_range[1]))
# if team:
#     mask &= df["team"].isin(team)
# if home_away != "All":
#     mask &= (df["home"] if home_away == "Home" else ~df["home"])

# f = df.loc[mask].copy()
# if f.empty:
#     st.warning("No rows match the filters.")
#     st.stop()

# # ------------------------- Derived metrics -------------------------
# f.sort_values(["team", "week"], inplace=True)
# f["pf_rolling_3"] = f.groupby("team")["points_for"].transform(lambda s: s.rolling(3, min_periods=1).mean())
# f["tp_rolling_3"] = f.groupby("team")["total_points"].transform(lambda s: s.rolling(3, min_periods=1).mean())

# league_week = (
#     f.groupby("week", as_index=False)[["points_for","total_points"]]
#      .mean()
#      .rename(columns={"points_for":"lg_pf_avg", "total_points":"lg_tp_avg"})
# )

# f = f.merge(league_week, on="week", how="left")

# # ------------------------- KPI tiles -------------------------
# left, mid, right = st.columns(3)
# with left:
#     st.metric("Avg Points For", f["points_for"].mean().round(1))
# with mid:
#     st.metric("Avg Total Points", f["total_points"].mean().round(1))
# with right:
#     st.metric("3W Rolling PF (mean)", f["pf_rolling_3"].mean().round(1))

# # ------------------------- Charts -------------------------
# # 1) Team scoring trend with rolling mean
# line_base = alt.Chart(f).encode(x=alt.X("week:Q", title="Week"))

# team_pf = line_base.mark_line(point=True).encode(
#     y=alt.Y("points_for:Q", title="Points For"),
#     color=alt.Color("team:N", title="Team"),
#     tooltip=["team","week","points_for","pf_rolling_3"]
# ).properties(height=320)

# team_pf_roll = line_base.mark_line(strokeDash=[4,3]).encode(
#     y="pf_rolling_3:Q",
#     color="team:N"
# )

# st.subheader("Team Points For per Week")
# st.altair_chart((team_pf + team_pf_roll).interactive(), use_container_width=True)

# # 2) League total-points trend vs team rolling
# lg = alt.Chart(league_week).mark_line(point=True).encode(
#     x="week:Q", y=alt.Y("lg_tp_avg:Q", title="League Avg Total Points"), tooltip=["week","lg_tp_avg"]
# )

# team_tp_roll = alt.Chart(f).mark_line().encode(
#     x="week:Q", y="tp_rolling_3:Q", color="team:N", tooltip=["team","week","tp_rolling_3"]
# )

# st.subheader("Total Points Trend: Teams vs League")
# st.altair_chart((lg + team_tp_roll).interactive(), use_container_width=True)

# # 3) Distribution by team
# st.subheader("Points For Distribution")
# box = alt.Chart(f).mark_boxplot().encode(x="team:N", y=alt.Y("points_for:Q", title="Points For"))
# st.altair_chart(box.properties(height=300), use_container_width=True)

# # 4) Heatmap: average points by team and week
# st.subheader("Heatmap: Avg Points For by Week")
# heat = alt.Chart(f).mark_rect().encode(
#     x=alt.X("week:O", title="Week"),
#     y=alt.Y("team:N", title="Team"),
#     color=alt.Color("mean(points_for):Q", title="Avg PF"),
#     tooltip=["team","week",alt.Tooltip("mean(points_for):Q", title="Avg PF")]
# ).properties(height=320)
# st.altair_chart(heat, use_container_width=True)

# # ------------------------- Download -------------------------
# st.download_button(
#     "Download filtered data as CSV",
#     data=f.to_csv(index=False).encode("utf-8"),
#     file_name=f"scoring_trends_{season}_{week_range[0]}-{week_range[1]}.csv",
#     mime="text/csv",
# )
