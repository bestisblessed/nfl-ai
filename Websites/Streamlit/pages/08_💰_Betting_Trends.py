import streamlit as st
import pandas as pd
import os
from utils.footer import render_footer

# Page configuration
st.set_page_config(
    page_title="💰 Betting Trends",
    page_icon="🏈",
    layout="wide"
)

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            Betting Trends
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Advanced betting analytics and spread performance tracking
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Season selector
selected_season = st.selectbox("Select Season:", list(range(2010, 2026))[::-1], index=0)  # 2010-2025, most recent first

# Load data files directly if not in session state
if 'df_teams' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
    df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
    # df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))  # COMMENTED OUT - Missing 2025 data, not used in this page
    
    # Store in session state for future use
    st.session_state['df_teams'] = df_teams
    st.session_state['df_games'] = df_games
    # st.session_state['df_playerstats'] = df_playerstats  # COMMENTED OUT
else:
    df_teams = st.session_state['df_teams']
    df_games = st.session_state['df_games'] 
    # df_playerstats = st.session_state['df_playerstats']  # COMMENTED OUT

tab1, tab2 = st.tabs(["ATS", "Over/Under"])


def render_record_table(title: str, records: list[dict], percentage_label: str, outcome_columns: list[str]):
    df = pd.DataFrame(records).fillna(0)
    if df.empty or df['Games'].sum() == 0:
        st.info("No completed games available to display yet.")
        return

    df = df.sort_values(percentage_label, ascending=False).reset_index(drop=True)
    df[percentage_label] = df[percentage_label].round(1)

    display_columns = ['Team', 'Games', percentage_label] + outcome_columns

    st.markdown(f"**{title}**")
    st.dataframe(
        df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            'Games': st.column_config.NumberColumn('Games', format='%d'),
            percentage_label: st.column_config.NumberColumn(percentage_label, format='%.1f%%'),
            **{
                col: st.column_config.NumberColumn(col, format='%d')
                for col in outcome_columns
            },
        },
    )


### --- ATS Record (Overall, Home, Away) --- ###
with tab1:
    st.header("ATS Stats (Reg Reason)")

    teams = df_teams['TeamID'].tolist()

    # Function to determine the ATS result for a game using actual scores and spread
    def ats_result(row, team):
        """Return ATS result (Win, Loss, Push) for the supplied team."""
        if pd.isna(row['home_score']) or pd.isna(row['away_score']) or row['home_score'] == '' or row['away_score'] == '':
            return None  # Game not played yet

        spread = float(row['home_spread']) if row['home_team'] == team else float(row['away_spread'])
        score_diff = row['home_score'] - row['away_score'] if row['home_team'] == team else row['away_score'] - row['home_score']

        if score_diff > spread:
            return 'Win'
        if score_diff < spread:
            return 'Loss'
        return 'Push'

    # Dropdown button for single team stats
    default_index = teams.index('DAL') if 'DAL' in teams else 0
    selected_team = st.selectbox('Team:', teams, key="ATS_selectbox", index=default_index)
    if selected_team:
        # Filter the games for the selected team
        relevant_columns = ['home_team', 'away_team', 'home_score', 'away_score', 'home_spread', 'away_spread']
        team_games = df_games[
            ((df_games['home_team'] == selected_team) | (df_games['away_team'] == selected_team))
            & (df_games['season'] == selected_season)
            & (df_games['week'].between(1, 18))
        ][relevant_columns].copy()

        team_games['ATS_Result'] = team_games.apply(lambda row: ats_result(row, selected_team), axis=1)
        # Filter out unplayed games (None values)
        played_games = team_games.dropna(subset=['ATS_Result'])
        outcome_order = ['Win', 'Loss', 'Push']
        overall_ats_record = played_games['ATS_Result'].value_counts().reindex(outcome_order, fill_value=0)
        home_ats_record = played_games[played_games['home_team'] == selected_team]['ATS_Result'].value_counts().reindex(outcome_order, fill_value=0)
        away_ats_record = played_games[played_games['away_team'] == selected_team]['ATS_Result'].value_counts().reindex(outcome_order, fill_value=0)
        st.write(f"ATS Record for {selected_team} in {selected_season} Season")
        ats_data = pd.DataFrame({
            'Overall': overall_ats_record,
            'Home': home_ats_record,
            'Away': away_ats_record
        })
        st.table(ats_data)

    st.divider()

    outcome_order = ['Win', 'Loss', 'Push']
    percentage_label = 'Cover %'
    overall_records = []
    home_records = []
    away_records = []

    for team in teams:
        relevant_columns = ['home_team', 'away_team', 'home_score', 'away_score', 'home_spread', 'away_spread']
        team_games = df_games[
            ((df_games['home_team'] == team) | (df_games['away_team'] == team))
            & (df_games['season'] == selected_season)
            & (df_games['week'].between(1, 18))
        ][relevant_columns].copy()

        team_games['ATS_Result'] = team_games.apply(lambda row: ats_result(row, team), axis=1)
        played_games = team_games.dropna(subset=['ATS_Result'])

        overall_counts = played_games['ATS_Result'].value_counts().reindex(outcome_order, fill_value=0)
        home_counts = played_games[played_games['home_team'] == team]['ATS_Result'].value_counts().reindex(outcome_order, fill_value=0)
        away_counts = played_games[played_games['away_team'] == team]['ATS_Result'].value_counts().reindex(outcome_order, fill_value=0)

        total_games = int(overall_counts.sum())
        win_pct = (overall_counts['Win'] / total_games * 100) if total_games else 0

        overall_records.append({
            'Team': team,
            'Win': int(overall_counts['Win']),
            'Loss': int(overall_counts['Loss']),
            'Push': int(overall_counts['Push']),
            'Games': total_games,
            percentage_label: win_pct
        })

        home_records.append({
            'Team': team,
            'Win': int(home_counts['Win']),
            'Loss': int(home_counts['Loss']),
            'Push': int(home_counts['Push']),
            'Games': int(home_counts.sum()),
            percentage_label: (home_counts['Win'] / home_counts.sum() * 100) if home_counts.sum() else 0
        })

        away_records.append({
            'Team': team,
            'Win': int(away_counts['Win']),
            'Loss': int(away_counts['Loss']),
            'Push': int(away_counts['Push']),
            'Games': int(away_counts.sum()),
            percentage_label: (away_counts['Win'] / away_counts.sum() * 100) if away_counts.sum() else 0
        })

    st.subheader("Team leaderboards")
    render_record_table(
        title="Overall performance against the spread",
        records=overall_records,
        percentage_label=percentage_label,
        outcome_columns=outcome_order,
    )

    render_record_table(
        title="Home games vs the spread",
        records=home_records,
        percentage_label=percentage_label,
        outcome_columns=outcome_order,
    )

    render_record_table(
        title="Road games vs the spread",
        records=away_records,
        percentage_label=percentage_label,
        outcome_columns=outcome_order,
    )





### --- Over/Under Stats (Reg Reason) --- ###
with tab2:
    st.header("O/U Stats (Reg Reason)")

    teams = df_teams['TeamID'].tolist()
    games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))].copy()
    
    # Filter out unplayed games (games with empty or NaN scores)
    games_selected = games_selected[
        (games_selected['home_score'].notna()) & 
        (games_selected['away_score'].notna()) & 
        (games_selected['home_score'] != '') & 
        (games_selected['away_score'] != '')
    ].copy()
    
    games_selected['total_score'] = games_selected['home_score'] + games_selected['away_score']
    games_selected['over_under_result'] = games_selected.apply(lambda row: 'over' if row['total_score'] > row['total_line'] else 'under' if row['total_score'] < row['total_line'] else 'push', axis=1)

    # Dropdown button for single team stats
    default_index = teams.index('DAL') if 'DAL' in teams else 0
    selected_team = st.selectbox('Team:', teams, key="O/U_selectbox", index=default_index)
    if selected_team:
        selected_team_games = games_selected[(games_selected['home_team'] == selected_team) | (games_selected['away_team'] == selected_team)]
        over_count = selected_team_games['over_under_result'].value_counts().get('over', 0)
        under_count = selected_team_games['over_under_result'].value_counts().get('under', 0)
        push_count = selected_team_games['over_under_result'].value_counts().get('push', 0)
        home_games = games_selected[games_selected['home_team'] == selected_team]
        home_over_count = home_games['over_under_result'].value_counts().get('over', 0)
        home_under_count = home_games['over_under_result'].value_counts().get('under', 0)
        home_push_count = home_games['over_under_result'].value_counts().get('push', 0)
        away_games = games_selected[games_selected['away_team'] == selected_team]
        away_over_count = away_games['over_under_result'].value_counts().get('over', 0)
        away_under_count = away_games['over_under_result'].value_counts().get('under', 0)
        away_push_count = away_games['over_under_result'].value_counts().get('push', 0)
        combined_record = pd.DataFrame({
            'Type': ['Overall', 'Home', 'Away'],
            'Over': [over_count, home_over_count, away_over_count],
            'Under': [under_count, home_under_count, away_under_count],
            'Push': [push_count, home_push_count, away_push_count]
        })
        st.write(f"O/U Record for {selected_team} in {selected_season} Season")
        st.table(combined_record)

    st.divider()

    outcome_order = ['Over', 'Push', 'Under']
    percentage_label = 'Over %'
    overall_ou_records = []
    home_ou_records = []
    away_ou_records = []

    for team in teams:
        team_games = games_selected[(games_selected['home_team'] == team) | (games_selected['away_team'] == team)].copy()
        home_games = games_selected[games_selected['home_team'] == team].copy()
        away_games = games_selected[games_selected['away_team'] == team].copy()

        def build_record(games):
            counts = games['over_under_result'].value_counts().reindex(['over', 'push', 'under'], fill_value=0)
            total = int(counts.sum())
            return {
                'Over': int(counts['over']),
                'Push': int(counts['push']),
                'Under': int(counts['under']),
                'Games': total,
                percentage_label: (counts['over'] / total * 100) if total else 0
            }

        overall_record = build_record(team_games)
        home_record = build_record(home_games)
        away_record = build_record(away_games)

        overall_ou_records.append({'Team': team, **overall_record})
        home_ou_records.append({'Team': team, **home_record})
        away_ou_records.append({'Team': team, **away_record})

    st.subheader("Team leaderboards")
    render_record_table(
        title="Overall totals performance",
        records=overall_ou_records,
        percentage_label=percentage_label,
        outcome_columns=outcome_order,
    )

    render_record_table(
        title="Home totals performance",
        records=home_ou_records,
        percentage_label=percentage_label,
        outcome_columns=outcome_order,
    )

    render_record_table(
        title="Road totals performance",
        records=away_ou_records,
        percentage_label=percentage_label,
        outcome_columns=outcome_order,
    )







# 4. Radar Charts:
# Team Performance Radar Chart:
# A radar chart (spider chart) comparing each team’s ATS performance across multiple dimensions (Overall, Home, Away, Performance as Favorite, Performance as Underdog, etc.). This can give a holistic view of team strengths and weaknesses against the spread.

# 5. Scatter Plots with Regression Lines:
# ATS Win Percentage vs. Point Spread:
# Scatter plots showing the relationship between the average point spread and the ATS win percentage for each team. Adding regression lines can help identify if teams tend to perform better with larger or smaller spreads.
# ATS Win Percentage vs. Team Statistics:
# Scatter plots showing the relationship between ATS win percentage and various team statistics (e.g., offensive or defensive rankings). This can help identify correlations between team performance metrics and success against the spread.

# 7. Correlation Matrix:
# Team Performance Metrics vs. ATS Performance:
# A correlation matrix showing the relationships between various team performance metrics (like offensive/defensive efficiency, turnovers, etc.) and their ATS performance. This can help in identifying which metrics most strongly correlate with ATS success.

# 8. Sankey Diagrams:
# Flow of ATS Outcomes:
# A Sankey diagram to show the flow of ATS outcomes (Win, Loss, Push) based on factors like home/away games, the spread, and other variables. This can visualize how different factors contribute to ATS results.

# 10. 3D Bar Charts:
# 3D Bar Chart for Multi-Dimensional Data:
# A 3D bar chart showing the relationship between three dimensions, such as the ATS record (Win/Loss/Push), the spread size, and the week of the season. This can add depth to understanding how different factors interact.

# Footer
render_footer()
