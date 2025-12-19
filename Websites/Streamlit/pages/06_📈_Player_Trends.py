import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import altair as alt
import os
# from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

# Page configuration
st.set_page_config(
    page_title="📈 Player Trends",
    page_icon="🏈",
    layout="wide"
)

# # Define the base directory
# base_dir = os.path.abspath('../data')

# # Use absolute paths
# df_teams = pd.read_csv(os.path.join(base_dir, 'Teams.csv'))
# df_games = pd.read_csv(os.path.join(base_dir, 'Games.csv'))
# df_playerstats = pd.read_csv(os.path.join(base_dir, 'PlayerStats.csv'))

PAGE_KEY_PREFIX = "player_trends"

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            Player Trends
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Advanced analytics and statistical trends across player positions
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load data using cached function
@st.cache_data(show_spinner=False)
def load_data():
    """Load all required CSV files for Player Trends"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
        df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
        # df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))  # COMMENTED OUT - Missing 2025 data, not used in this page
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
        df_schedule_and_game_results = pd.read_csv(os.path.join(current_dir, '../data', 'all_teams_schedule_and_game_results_merged.csv'))
        # Add the detailed passing/rushing/receiving data for 2025 trends
        df_all_passing_rushing_receiving = pd.read_csv(os.path.join(current_dir, '../data', 'all_passing_rushing_receiving.csv'))
        
        return df_teams, df_games, None, df_team_game_logs, df_schedule_and_game_results, df_all_passing_rushing_receiving  # df_playerstats replaced with None
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        st.stop()

# Load all data
df_teams, df_games, _, df_team_game_logs, df_schedule_and_game_results, df_all_passing_rushing_receiving = load_data()  # df_playerstats not used

# Function to get the standardized dataset for any season
def get_player_data_for_season(season):
    """Return the standardized player dataset for any season"""
    # Use the detailed passing/rushing/receiving data for all seasons
    df_standard = df_all_passing_rushing_receiving.copy()
    # Extract season from game_id (format: YYYY_XX_TEAM1_TEAM2)
    df_standard['season'] = df_standard['game_id'].str[:4].astype(int)
    
    # Map column names to match the standard format used in the page
    column_mapping = {
        'player': 'player_display_name',
        'pass_sacked': 'sacks',
        'pass_int': 'interceptions', 
        'pass_yds': 'passing_yards',
        'pass_td': 'passing_tds',
        'pass_att': 'passing_attempts',
        'rush_yds': 'rushing_yards',
        'rush_td': 'rushing_tds',
        'rec_yds': 'receiving_yards',
        'rec_td': 'receiving_tds'
    }
    
    # Rename columns to match the expected format
    df_standard = df_standard.rename(columns=column_mapping)
    
    return df_standard

# Season selector - now includes all available years from the standardized dataset (2010-2025)
available_seasons = list(range(2010, 2026))
selected_season = persistent_selectbox(
    "Select Season:",
    options=available_seasons,
    page=PAGE_KEY_PREFIX,
    widget="season",
    default=2025,
)

# st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["QBs", "RBs", "WRs", "TEs"])

with tab1:
    st.header('Quarterback Stats')
    st.write("")
    # Get the appropriate dataset for the selected season (once for all charts)
    current_player_data = get_player_data_for_season(selected_season)
    qb_selected_stats = current_player_data[(current_player_data['position'] == 'QB') & (current_player_data['season'] == selected_season)]

    # Pre-calculate all QB data
    qb_interceptions_data = None
    qb_sacks_data = None
    qb_passing_data = None
    qb_rushing_data = None

    if not qb_selected_stats.empty:
        # Calculate Interceptions data
        qb_interceptions_selected = qb_selected_stats.groupby('player_display_name').agg({
            'interceptions': 'sum',
            'passing_attempts': 'sum'
        }).reset_index()
        qb_interceptions_selected = qb_interceptions_selected[qb_interceptions_selected['passing_attempts'] >= 10]
        qb_interceptions_data = qb_interceptions_selected.sort_values(by='interceptions', ascending=False)

        # Calculate Sacks data
        qb_sacked_selected = qb_selected_stats.groupby('player_display_name').agg({
            'sacks': 'sum',
            'game_id': 'nunique'
        }).reset_index()
        qb_sacked_selected = qb_sacked_selected[qb_sacked_selected['sacks'] > 0]
        qb_sacked_selected = qb_sacked_selected[qb_sacked_selected['game_id'] >= 2]
        qb_sacks_data = qb_sacked_selected.sort_values(by='sacks', ascending=False)

        # Calculate Passing Yards per Game data
        qb_passing_stats = qb_selected_stats.groupby('player_display_name').agg({
            'passing_yards': 'sum',
            'game_id': 'nunique'
        }).reset_index()
        qb_passing_stats['yards_per_game'] = qb_passing_stats['passing_yards'] / qb_passing_stats['game_id']
        qb_passing_stats = qb_passing_stats[qb_passing_stats['game_id'] >= 2]
        qb_passing_stats = qb_passing_stats[qb_passing_stats['yards_per_game'] >= 30]
        qb_passing_data = qb_passing_stats.sort_values(by='yards_per_game', ascending=False)

        # Calculate Rushing Yards per Game data
        qb_rushing_selected = qb_selected_stats.groupby('player_display_name').agg({
            'rushing_yards': 'sum',
            'game_id': 'nunique'
        }).reset_index()
        qb_rushing_selected['yards_per_game'] = qb_rushing_selected['rushing_yards'] / qb_rushing_selected['game_id']
        qb_rushing_selected = qb_rushing_selected[qb_rushing_selected['rushing_yards'] > 0]
        qb_rushing_selected = qb_rushing_selected[qb_rushing_selected['game_id'] >= 2]
        qb_rushing_data = qb_rushing_selected.sort_values(by='yards_per_game', ascending=False)

    # Row 1: Passing Yards per Game | Rushing Yards (side by side)
    col1, col2 = st.columns(2)

    with col1:
        # st.header('Quarterback Passing Yards per Game')
        if qb_passing_data is not None and len(qb_passing_data) > 0:
            st.markdown("<h5 style='text-align: center;'>Passing Yards per Game (Min. 2 Games)</h5>", unsafe_allow_html=True)
            # Create bar chart with text labels
            bars = alt.Chart(qb_passing_data).mark_bar(
                color='forestgreen',
                size=20
            ).encode(
                x=alt.X('yards_per_game:Q', title='Passing Yards per Game'),
                y=alt.Y('player_display_name:N', title='Quarterbacks', sort='-x'),
                tooltip=['player_display_name', 'yards_per_game', 'passing_yards', 'game_id']
            )

            # Add text labels on the bars
            text = bars.mark_text(
                align='left',
                baseline='middle',
                dx=3,  # Offset from end of bar
                color='gray',
            ).encode(
                x=alt.X('yards_per_game:Q'),
                y=alt.Y('player_display_name:N', sort='-x'),
                text=alt.Text('yards_per_game:Q', format='.1f')
            )

            chart = (bars + text).properties(
                width=400,
                height=max(300, len(qb_passing_data) * 25)
            ).configure_axisX(
                grid=False,
                labelColor='#333333'
            ).configure_axisY(
                grid=False,
                labelColor='#333333'
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No QB passing data available.")

    with col2:
        # st.header('Quarterback Rushing Yards per Game')
        if qb_rushing_data is not None and len(qb_rushing_data) > 0:
            st.markdown("<h5 style='text-align: center;'>Rushing Yards per Game (Min. 2 Games)</h5>", unsafe_allow_html=True)
            # Create bar chart with text labels
            bars = alt.Chart(qb_rushing_data).mark_bar(
                color='darkgreen',
                size=20
            ).encode(
                x=alt.X('yards_per_game:Q', title='Rushing Yards per Game'),
                y=alt.Y('player_display_name:N', title='Quarterbacks', sort='-x'),
                tooltip=['player_display_name', 'yards_per_game', 'rushing_yards', 'game_id']
            )

            # Add text labels on the bars
            text = bars.mark_text(
                align='left',
                baseline='middle',
                dx=3,  # Offset from end of bar
                color='gray',
            ).encode(
                x=alt.X('yards_per_game:Q'),
                y=alt.Y('player_display_name:N', sort='-x'),
                text=alt.Text('yards_per_game:Q', format='.1f')
            )

            chart = (bars + text).properties(
                width=400,
                height=max(300, len(qb_rushing_data) * 25)
            ).configure_axisX(
                grid=False,
                labelColor='#333333'
            ).configure_axisY(
                grid=False,
                labelColor='#333333'
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No QB rushing data available.")

    # Row 2: Sacks | Interceptions (side by side)
    col3, col4 = st.columns(2)

    with col3:
        # st.header('Quarterback Sack Rankings')
        if qb_sacks_data is not None and len(qb_sacks_data) > 0:
            st.markdown("<h5 style='text-align: center;'>Sacks (Min. 2 Games)</h5>", unsafe_allow_html=True) 
            # Create bar chart with text labels
            bars = alt.Chart(qb_sacks_data).mark_bar(
                color='blueviolet',
                size=20
            ).encode(
                x=alt.X('sacks:Q', title='Number of Sacks'),
                y=alt.Y('player_display_name:N', title='Quarterbacks', sort='-x'),
                tooltip=['player_display_name', 'sacks', 'game_id']
            )

            # Add text labels on the bars
            text = bars.mark_text(
                align='left',
                baseline='middle',
                dx=3,  # Offset from end of bar
                color='gray',
            ).encode(
                x=alt.X('sacks:Q'),
                y=alt.Y('player_display_name:N', sort='-x'),
                text=alt.Text('sacks:Q', format='.0f')
            )

            chart = (bars + text).properties(
                width=400,
                height=max(300, len(qb_sacks_data) * 25)
            ).configure_axisX(
                grid=False,
                labelColor='#333333'
            ).configure_axisY(
                grid=False,
                labelColor='#333333'
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No QB sack data available.")

    with col4:
        # st.header('Quarterback Interception Rankings')
        if qb_interceptions_data is not None and len(qb_interceptions_data) > 0:
            st.markdown("<h5 style='text-align: center;'>Interceptions (Min. 10 Attempts)</h5>", unsafe_allow_html=True)
            # Create bar chart with text labels
            bars = alt.Chart(qb_interceptions_data).mark_bar(
                color='salmon',
                size=20
            ).encode(
                x=alt.X('interceptions:Q', title='Number of Interceptions', scale=alt.Scale(domain=[0, qb_interceptions_data['interceptions'].max()])),
                y=alt.Y('player_display_name:N', title='Quarterbacks', sort='-x'),
                tooltip=['player_display_name', 'interceptions', 'passing_attempts']
            )

            # Add text labels on the bars
            text = bars.mark_text(
                align='left',
                baseline='middle',
                dx=3,  # Offset from end of bar
                color='gray',
            ).encode(
                x=alt.X('interceptions:Q'),
                y=alt.Y('player_display_name:N', sort='-x'),
                text=alt.Text('interceptions:Q', format='.0f')
            )

            chart = (bars + text).properties(
                width=400,
                height=max(300, len(qb_interceptions_data) * 25)
            ).configure_axisX(
                labelExpr="datum.value % 1 == 0 ? datum.value : ''",
                grid=False,
                labelColor='#333333'
            ).configure_axisY(
                grid=False,
                labelColor='#333333'
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No QB interception data available.")

with tab2:
    st.header('Running Back Stats')
    st.write("")
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    rb_selected_stats = current_player_data[(current_player_data['position'] == 'RB') & (current_player_data['season'] == selected_season)]

    # Create side-by-side layout: Yards (3/4) | Touchdowns (1/4)
    rb_col1, rb_col2 = st.columns([3, 1])

    with rb_col1:
        if not rb_selected_stats.empty:
            # Rushing Yards
            rb_rushing_selected = rb_selected_stats.groupby('player_display_name')['rushing_yards'].sum().reset_index()
            rb_rushing_ranked = rb_rushing_selected.sort_values(by='rushing_yards', ascending=False).head(30)

            if len(rb_rushing_ranked) > 0:
                st.markdown("**Top 30 Rushing Yards**")
                # st.markdown("<h5 style='text-align: center;'>Top 30 Rushing Yards</h5>", unsafe_allow_html=True)
                # Create Plotly Express chart
                fig = px.bar(
                    rb_rushing_ranked,
                    x='player_display_name',
                    y='rushing_yards',
                    color='rushing_yards',
                    color_continuous_scale='greens',
                    height=max(400, len(rb_rushing_ranked) * 25)
                )
                fig.update_layout(
                    xaxis_title='Running Backs',
                    yaxis_title='Rushing Yards',
                    showlegend=False,
                    coloraxis=dict(showscale=False),
                    font=dict(size=12),
                    xaxis=dict(tickangle=45)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No data.")
        else:
            st.write("No RB data.")

    with rb_col2:
        st.markdown('**Total Touchdowns**')
        if not rb_selected_stats.empty:
            rb_td_selected = rb_selected_stats.groupby('player_display_name').agg({
            'rushing_tds': 'sum',
            'receiving_tds': 'sum'
        }).reset_index()

        # Calculate total touchdowns
        rb_td_selected['total_tds'] = rb_td_selected['rushing_tds'] + rb_td_selected['receiving_tds']

        # Filter for players with at least 1 total TD
        rb_td_selected = rb_td_selected[rb_td_selected['total_tds'] > 0]

        rb_td_ranked = rb_td_selected.sort_values(by='total_tds', ascending=False)

        if len(rb_td_ranked) > 0:
            # Create a styled dataframe for display
            rb_td_display = rb_td_ranked[['player_display_name', 'total_tds']].copy()
            rb_td_display.columns = ['Player', 'Total TDs']

            # Style the dataframe for compact column display
            st.dataframe(
                rb_td_display,
                column_config={
                    "Player": st.column_config.TextColumn("Player", width="small"),
                    "Total TDs": st.column_config.NumberColumn("Total TDs", format="%d")
                },
                hide_index=True,
                use_container_width=True,
                height=750  # Fixed reasonable height
            )
        else:
            st.write("No data.")

with tab3:
    st.header('Wide Receiver Stats')
    st.write("")
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    wr_selected_stats = current_player_data[(current_player_data['position'] == 'WR') & (current_player_data['season'] == selected_season)]

    # Create side-by-side layout: Yards (3/4) | Touchdowns (1/4)
    wr_col1, wr_col2 = st.columns([3, 1])

    with wr_col1:
        if not wr_selected_stats.empty:
            # Receiving Yards
            wr_receiving_selected = wr_selected_stats.groupby('player_display_name')['receiving_yards'].sum().reset_index()
            wr_receiving_ranked = wr_receiving_selected.sort_values(by='receiving_yards', ascending=False).head(30)

            if len(wr_receiving_ranked) > 0:
                st.markdown('**Top 30 Receiving Yards**')
                # Create Plotly Express chart
                fig = px.bar(
                    wr_receiving_ranked,
                    x='player_display_name',
                    y='receiving_yards',
                    color='receiving_yards',
                    color_continuous_scale='purples',
                    height=max(400, len(wr_receiving_ranked) * 25)
                )
                fig.update_layout(
                    xaxis_title='Wide Receivers',
                    yaxis_title='Receiving Yards',
                    showlegend=False,
                    coloraxis=dict(showscale=False),
                    font=dict(size=12),
                    xaxis=dict(tickangle=45)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No data.")
        else:
            st.write("No WR data.")

    with wr_col2:
        st.markdown('**Total Touchdowns**')
        if not wr_selected_stats.empty:
            wr_td_selected = wr_selected_stats.groupby('player_display_name').agg({
            'rushing_tds': 'sum',
            'receiving_tds': 'sum'
        }).reset_index()

        # Calculate total touchdowns
        wr_td_selected['total_tds'] = wr_td_selected['rushing_tds'] + wr_td_selected['receiving_tds']

        # Filter for players with at least 1 total TD
        wr_td_selected = wr_td_selected[wr_td_selected['total_tds'] > 0]

        wr_td_ranked = wr_td_selected.sort_values(by='total_tds', ascending=False)

        if len(wr_td_ranked) > 0:
            # Create a styled dataframe for display
            wr_td_display = wr_td_ranked[['player_display_name', 'total_tds']].copy()
            wr_td_display.columns = ['Player', 'Total TDs']

            # Style the dataframe for compact column display
            st.dataframe(
                wr_td_display,
                column_config={
                    "Player": st.column_config.TextColumn("Player", width="small"),
                    "Total TDs": st.column_config.NumberColumn("Total TDs", format="%d")
                },
                hide_index=True,
                use_container_width=True,
                height=750  # Fixed reasonable height
            )
        else:
            st.write("No data.")

with tab4:
    st.header('Tight End Stats')
    st.write("")
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    te_selected_stats = current_player_data[(current_player_data['position'] == 'TE') & (current_player_data['season'] == selected_season)]

    # Create side-by-side layout: Yards (3/4) | Touchdowns (1/4)
    te_col1, te_col2 = st.columns([3, 1])

    with te_col1:
        if not te_selected_stats.empty:
            
            # Receiving Yards
            te_receiving_selected = te_selected_stats.groupby('player_display_name')['receiving_yards'].sum().reset_index()
            te_receiving_ranked = te_receiving_selected.sort_values(by='receiving_yards', ascending=False).head(30)

            if len(te_receiving_ranked) > 0:
                st.markdown('**Top 30 Receiving Yards**')
                # Create Plotly Express chart
                fig = px.bar(
                    te_receiving_ranked,
                    x='player_display_name',
                    y='receiving_yards',
                    color='receiving_yards',
                    color_continuous_scale='oranges',
                    height=max(400, len(te_receiving_ranked) * 25)
                )
                fig.update_layout(
                    xaxis_title='Tight Ends',
                    yaxis_title='Receiving Yards',
                    showlegend=False,
                    coloraxis=dict(showscale=False),
                    font=dict(size=12),
                    xaxis=dict(tickangle=45)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No data.")
        else:
            st.write("No TE data.")

    with te_col2:
        st.markdown('**Total Touchdowns**')
        if not te_selected_stats.empty:
            te_td_selected = te_selected_stats.groupby('player_display_name').agg({
            'rushing_tds': 'sum',
            'receiving_tds': 'sum'
        }).reset_index()

        # Calculate total touchdowns
        te_td_selected['total_tds'] = te_td_selected['rushing_tds'] + te_td_selected['receiving_tds']

        # Filter for players with at least 1 total TD
        te_td_selected = te_td_selected[te_td_selected['total_tds'] > 0]

        te_td_ranked = te_td_selected.sort_values(by='total_tds', ascending=False)

        if len(te_td_ranked) > 0:
            # Create a styled dataframe for display
            te_td_display = te_td_ranked[['player_display_name', 'total_tds']].copy()
            te_td_display.columns = ['Player', 'Total TDs']

            # Style the dataframe for compact column display
            st.dataframe(
                te_td_display,
                column_config={
                    "Player": st.column_config.TextColumn("Player", width="small"),
                    "Total TDs": st.column_config.NumberColumn("Total TDs", format="%d")
                },
                hide_index=True,
                use_container_width=True,
                height=750  # Fixed reasonable height
            )
        else:
            st.write("No data.")

# Footer
render_footer()
