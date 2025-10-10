# # <iframe src="https://claude.site/public/artifacts/1ca9aa13-a81f-491a-a1b3-459e08bc9948/embed" title="Claude Artifact" width="100%" height="600" frameborder="0" allow="clipboard-write" allowfullscreen></iframe>
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NFL 2025: TDs Allowed by Defense", page_icon="🛡️", layout="wide")
st.title("NFL 2025: TDs Allowed by Defense")

# Add CSS to control width and centering
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 80%;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            max-width: 95%;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_csv(path_local: str) -> pd.DataFrame:
    if os.path.exists(path_local):
        return pd.read_csv(path_local)
    raise FileNotFoundError(f"Local file not found: {path_local}")

@st.cache_data(show_spinner=False)
def build_table(season:int=2025) -> tuple[pd.DataFrame, dict, dict]:
    # Use relative paths like other pages
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_stats_path = os.path.join(current_dir, '../data', 'player_stats_pfr.csv')
    local_roster_path = os.path.join(current_dir, '../data', 'rosters', 'roster_2025.csv')
    
    stats  = load_csv(local_stats_path)
    roster = load_csv(local_roster_path)
    # minimal column checks
    need_stats = {"season","player_id","opponent_team","game_id","rush_td","rec_td"}
    need_roster = {"pfr_id","position"}
    missing = (need_stats - set(stats.columns)) | (need_roster - set(roster.columns))
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    # map player_id -> position (support with and without .htm)
    roster = roster.dropna(subset=["pfr_id","position"]).copy()
    roster["pfr_id_clean"] = roster["pfr_id"].str.replace(".htm","", regex=False)
    pos_map = dict(zip(roster["pfr_id"], roster["position"])) | dict(zip(roster["pfr_id_clean"], roster["position"]))
    df = stats[stats["season"] == season].copy()
    df["player_id_clean"] = df["player_id"].astype(str).str.replace(".htm","", regex=False)
    df["position"] = df["player_id"].map(pos_map).fillna(df["player_id_clean"].map(pos_map))
    # total TD logic (QB = rushing only; others = rushing + receiving)
    df["rush_td"] = pd.to_numeric(df["rush_td"], errors="coerce").fillna(0)
    df["rec_td"]  = pd.to_numeric(df["rec_td"],  errors="coerce").fillna(0)
    df["total_td"] = df.apply(
        lambda r: r["rush_td"] if r["position"] == "QB" else r["rush_td"] + r["rec_td"], axis=1
    )
    # keep valid rows
    df = df[(df["total_td"] > 0) & df["position"].notna() & df["opponent_team"].notna()].copy()
    pos_group = {"QB":"QB","RB":"RB","FB":"RB","WR":"WR","TE":"TE"}
    df["pos_group"] = df["position"].map(lambda p: pos_group.get(p, "OTHER"))
    df = df[df["pos_group"] != "OTHER"]
    # de-dup by game + player
    df = df.drop_duplicates(subset=["game_id","player_id"])
    # group to defense table
    tbl = (
        df.groupby(["opponent_team","pos_group"])["total_td"]
          .sum()
          .unstack(fill_value=0)
          .reindex(columns=["QB","RB","WR","TE"], fill_value=0)
          .reset_index()
          .rename(columns={"opponent_team":"Defense"})
    )
    for c in ["QB","RB","WR","TE"]:
        tbl[c] = tbl[c].astype(int)
    tbl["Total"] = tbl[["QB","RB","WR","TE"]].sum(axis=1).astype(int)
    tbl = tbl.sort_values("Total", ascending=False).reset_index(drop=True)
    tbl.insert(0, "Rank", range(1, len(tbl)+1))
    # KPIs
    col_max = {c: int(tbl[c].max()) for c in ["QB","RB","WR","TE","Total"]}
    totals  = {c: int(tbl[c].sum()) for c in ["QB","RB","WR","TE"]}
    worst   = {c: (tbl.loc[tbl[c].idxmax(), "Defense"], int(tbl[c].max())) for c in ["QB","RB","WR","TE"]}
    return tbl, totals, worst
try:
    season = 2025
    tbl, totals, worst = build_table(season)
except Exception as e:
    st.error(str(e))
    st.stop()

# ---------- KPI cards ----------
k1, k2, k3, k4 = st.columns(4)
for k, col in zip(["QB","RB","WR","TE"], [k1,k2,k3,k4]):
    team, val = worst[k]
    with col:
        label = f"**{k} (rushing)**" if k == "QB" else f"**{k}**"
        st.markdown(label)
        st.metric("Total TDs", totals[k])
        st.caption(f"Worst: {team} ({val})")
st.divider()

# ---------- Heatmapped table (HTML to match artifact style) ----------
def render_table_html(df: pd.DataFrame) -> str:
    def cell_bg(val, vmax):
        if vmax <= 0: return "background-color:rgba(0,0,0,0);"
        alpha = 0.7 * (val / vmax)
        color = f"rgba(239,68,68,{alpha:.3f})"  # Tailwind red-500
        txt = "color:white;" if alpha > 0.4 else "color:black;"
        return f"background-color:{color};{txt}"
    vmax = {c: df[c].max() for c in ["QB","RB","WR","TE"]}
    rows = []
    for _, r in df.iterrows():
        cells = [
            f"<td class='rank'>#{int(r['Rank'])}</td>",
            f"<td class='def'>{r['Defense']}</td>",
            f"<td class='pos' style='{cell_bg(r['QB'], vmax['QB'])}'>{int(r['QB'])}</td>",
            f"<td class='pos' style='{cell_bg(r['RB'], vmax['RB'])}'>{int(r['RB'])}</td>",
            f"<td class='pos' style='{cell_bg(r['WR'], vmax['WR'])}'>{int(r['WR'])}</td>",
            f"<td class='pos' style='{cell_bg(r['TE'], vmax['TE'])}'>{int(r['TE'])}</td>",
            f"<td class='total'>{int(r['Total'])}</td>",
        ]
        rows.append("<tr>" + "".join(cells) + "</tr>")
    style = """
    <style>
      .tbl { border-collapse: collapse; width:100%; font-size:14px; }
      .tbl th, .tbl td { padding:8px 10px; border-bottom:1px solid #e5e7eb; text-align:center; }
      .tbl th { text-align:left; background:#f3f4f6; font-weight:700; }
      .tbl td.rank, .tbl th.rank { text-align:left; width:50px; }
      .tbl td.def  { text-align:left; font-weight:700; }
      .tbl td.total{ background:#fee2e2; color:#b91c1c; font-weight:700; }
      .card { background:white; border:1px solid #e5e7eb; border-radius:12px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
    </style>
    """
    header = """
    <table class="tbl">
      <thead>
        <tr>
          <th class="rank">Rank</th>
          <th>Defense</th>
          <th>QB (rushing)</th><th>RB</th><th>WR</th><th>TE</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
    """
    return f"""
    {style}
    <div class="card">
      <h3 style="margin:0 0 12px 0;">Defense Rankings</h3>
      {header}
        {''.join(rows)}
      </tbody>
    </table>
    </div>
    """

st.components.v1.html(render_table_html(tbl), height=400, scrolling=True)

st.subheader("Position Insights: Most Vulnerable (Top 5)")
left, right = st.columns(2)

def top5_html(name:str):
    sub = tbl[["Defense", name]].sort_values(name, ascending=False).head(5)
    items = "".join(
        f"<div style='display:flex;justify-content:space-between;padding:8px 10px;background:#f9fafb;border-radius:8px;margin-bottom:6px;'>"
        f"<span style='font-weight:600;color:#374151'>{i+1}. {row.Defense}</span>"
        f"<span style='font-weight:700;color:#dc2626'>{int(row[name])} TDs</span>"
        f"</div>"
        for i, row in sub.reset_index(drop=True).iterrows()
    )
    return f"""
    <div class="card">
      <h4 style="margin:0 0 10px 0;color:#dc2626">{name} Most Vulnerable</h4>
      {items}
    </div>
    """

with left:
    st.components.v1.html(top5_html("QB"), height=200)
    st.components.v1.html(top5_html("RB"), height=200)
with right:
    st.components.v1.html(top5_html("WR"), height=200)
    st.components.v1.html(top5_html("TE"), height=200)

st.caption("QB TDs = rushing only. RB/WR/TE = receiving + rushing. Source: PFR-derived CSVs.")

# import streamlit as st
# st.title("NFL 2025 Defense TD Analysis")
# # Direct iframe embed
# st.components.v1.iframe(
#     "https://claude.site/public/artifacts/1ca9aa13-a81f-491a-a1b3-459e08bc9948/embed",
#     width=1000,   # adjust as needed
#     height=600,
#     scrolling=True
# )
# # Or if you need more control over styles
# st.components.v1.html(
#     """
#     <div style="position:relative;padding-top:56.25%;">
#       <iframe src="https://claude.site/public/artifacts/XXXX/embed"
#               title="Claude Artifact"
#               style="position:absolute;inset:0;width:100%;height:100%;border:0;"
#               allow="clipboard-write; fullscreen"></iframe>
#     </div>
#     """,
#     height=600
# )
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


