import streamlit as st
import pandas as pd
import os
import json
import re
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import dates as mdates
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.footer import render_footer

# Page configuration
st.set_page_config(
    page_title="Odds Dashboard",
    page_icon="🏈",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load data files directly
csv_file_path_odds = os.path.join(BASE_DIR, 'data/odds/nfl_odds_movements.csv')
csv_file_path_circa = os.path.join(BASE_DIR, 'data/odds/nfl_odds_movements_circa.csv')

try:
    df_nfl_odds_movements = pd.read_csv(csv_file_path_odds)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_odds}. Please ensure the file exists.")
    df_nfl_odds_movements = pd.DataFrame()

try:
    df_nfl_odds_movements_circa = pd.read_csv(csv_file_path_circa)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_circa}. Please ensure the file exists.")
    df_nfl_odds_movements_circa = pd.DataFrame()

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            NFL Odds Dashboard
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Live Odds Movement Tracking Across All Major Sportsbooks
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()

# Create main container with wider layout
col1, col2, col3 = st.columns([0.5, 5, 0.5])

with col2:
    
    # BLACKLIST_TEAMS = ["Minnesota Vikings", "Los Angeles Rams"]
    # st.write(f"*Blacklisted Teams:* {', '.join(BLACKLIST_TEAMS)}")
    def load_odds_movements():
        if df_nfl_odds_movements.empty:
            st.error("Data not loaded. Please ensure the data is loaded in Home.py.")
            return pd.DataFrame()  
        df_nfl_odds_movements['game_date'] = df_nfl_odds_movements['game_date'].str.replace(' ', '').str.strip().str.lower()
        df_nfl_odds_movements['game_time'] = df_nfl_odds_movements['game_time'].str.replace('\n', ' ').str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
        df_nfl_odds_movements['matchup'] = df_nfl_odds_movements['matchup'].str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
        sportsbooks_to_include = [
            'Circa', 'Westgate', 'South Point', 'Wynn', 'Caesars', 'BetMGM', 'DK'
        ]
        filtered_odds = df_nfl_odds_movements[df_nfl_odds_movements['sportsbook'].isin(sportsbooks_to_include)].copy()
        return filtered_odds
    
    def load_games_data():
        games_data = []
        data_dir = os.path.join(os.path.dirname(__file__), '../data/odds/')
        json_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".json") and f.startswith('nfl')], reverse=True)
        most_recent_file = json_files[0] if json_files else None
        if most_recent_file:
            filepath = os.path.join(data_dir, most_recent_file)
            with open(filepath) as f:
                data = json.load(f)
                for game in data:
                    game_time = game['Time']
                    day_and_matchup_key = list(game.keys())[1]
                    day_and_matchup_value = game[day_and_matchup_key]
                    day_and_matchup_column_name = list(game.keys())[1].replace(',', ', ')
                    game_date = day_and_matchup_key.strip()
                    teams = day_and_matchup_value.replace('\n', ' ').strip()
                    if '  ' in teams:
                        teams_list = [team.strip() for team in teams.split('  ') if team.strip()]
                    else:
                        teams_list = [team.strip() for team in re.split(r'\s+|,', teams) if team.strip()]
                    # if len(teams_list) != 2 or any(team in teams_list for team in BLACKLIST_TEAMS):
                    if len(teams_list) != 2:  # or any(team in teams_list for team in BLACKLIST_TEAMS):
                        continue  
                    game_date = game_date.replace(' ', '').strip().lower()
                    game_time = re.sub(r'\s+', ' ', game_time.replace('\n', ' ')).strip().lower()
                    matchup = re.sub(r'\s+', ' ', ' vs '.join(teams_list)).strip().lower()
                    circa_spread = game.get("Circa", "").replace('\n', ' ').strip().split(' ')
                    spread_favorite, spread_underdog = ("N/A", "N/A") if len(circa_spread) != 4 else (f"{circa_spread[0]} {circa_spread[1]}", f"{circa_spread[2]} {circa_spread[3]}")
                    games_data.append({
                        'time': game_time,
                        'day_and_matchup_column_name': day_and_matchup_column_name,
                        'game_date': game_date,
                        'matchup': matchup,
                        'teams': teams_list,
                        'spread': [spread_favorite, spread_underdog],
                        'moneyline': ['N/A', 'N/A'],
                        'total': ['N/A', 'N/A']
                    })
        else:
            st.warning("No JSON files found in the data directory.")
        return games_data
    
    df_nfl_odds_movements = load_odds_movements()
    games_data = load_games_data()
    games_df = pd.DataFrame(games_data)

    # Load upcoming games and filter to only show those matchups
    upcoming_matchups = []  # Initialize empty list
    try:
        df_upcoming_games = pd.read_csv(os.path.join(BASE_DIR, 'upcoming_games.csv'))
        
        # Team abbreviation to full name mapping
        team_mapping = {
            'GB': 'Green Bay Packers', 'WAS': 'Wash Commanders',
            'DAL': 'Dallas Cowboys', 'NYG': 'New York Giants',
            'PIT': 'Pittsburgh Steelers', 'SEA': 'Seattle Seahawks',
            'TEN': 'Tennessee Titans', 'LAR': 'Los Angeles Rams',
            'NYJ': 'New York Jets', 'BUF': 'Buffalo Bills',
            'MIA': 'Miami Dolphins', 'NE': 'New England Patriots',
            'CIN': 'Cincinnati Bengals', 'JAX': 'Jacksonville Jaguars',
            'NO': 'New Orleans Saints', 'SF': 'San Francisco 49ers',
            'BAL': 'Baltimore Ravens', 'CLE': 'Cleveland Browns',
            'DET': 'Detroit Lions', 'CHI': 'Chicago Bears',
            'IND': 'Indianapolis Colts', 'DEN': 'Denver Broncos',
            'ARI': 'Arizona Cardinals', 'CAR': 'Carolina Panthers',
            'KC': 'Kansas City Chiefs', 'PHI': 'Philadelphia Eagles',
            'MIN': 'Minnesota Vikings', 'ATL': 'Atlanta Falcons',
            'HOU': 'Houston Texans', 'TB': 'Tampa Bay Buccaneers',
            'LVR': 'Las Vegas Raiders', 'LAC': 'Los Angeles Chargers'
        }
        
        # Create matchup strings from upcoming games (format: "Away vs Home" to match JSON data)
        # Store the order from CSV for later sorting
        upcoming_matchups_ordered = []
        for _, row in df_upcoming_games.iterrows():
            away_team = team_mapping.get(row['away_team'], row['away_team'])
            home_team = team_mapping.get(row['home_team'], row['home_team'])
            matchup = f"{away_team} vs {home_team}".lower()
            upcoming_matchups_ordered.append(matchup)
        
        # Filter games_df to only include upcoming games
        if not games_df.empty:
            games_df = games_df[games_df['matchup'].isin(upcoming_matchups_ordered)]
            # Sort games_df to match the order from upcoming_games.csv
            games_df['matchup_order'] = games_df['matchup'].map({matchup: i for i, matchup in enumerate(upcoming_matchups_ordered)})
            games_df = games_df.sort_values('matchup_order').drop('matchup_order', axis=1)
        
    except FileNotFoundError:
        st.error("upcoming_games.csv not found. Showing all games.")
    except Exception as e:
        st.error(f"Error loading upcoming games: {str(e)}")

    if not games_df.empty:
        # Show all upcoming games - historical data is a bonus but not required for current odds display
        games_with_sufficient_data = games_df
    else:
        games_with_sufficient_data = pd.DataFrame()  # Empty DataFrame instead of list

    # Normalize matchup and compute Circa upcoming-week subset once for reuse in the loop below
    def normalize_matchup(matchup):
        return str(matchup).lower().replace('  ', ' ').strip()

    def format_month_day_with_ordinal(dt):
        day = dt.day
        if 11 <= day % 100 <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return dt.strftime('%b ') + f"{day}{suffix}"

    def format_month_day_hour_with_ordinal(dt):
        day = dt.day
        if 11 <= day % 100 <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        month_day = dt.strftime('%b ') + f"{day}{suffix}"
        hour12 = dt.strftime('%I').lstrip('0')
        if hour12 == '':
            hour12 = '12'
        am_pm = dt.strftime('%p').lower()
        return f"{month_day} {hour12}{am_pm}"

    def format_month_day_hour_compact(dt):
        month_day = dt.strftime('%b ') + str(dt.day)
        hour12 = dt.strftime('%I').lstrip('0') or '12'
        am_pm_short = 'a' if dt.strftime('%p') == 'AM' else 'p'
        return f"{month_day}, {hour12}{am_pm_short}"

    def format_month_day_hour_simple(dt):
        month_day = dt.strftime('%b ') + str(dt.day)
        hour12 = dt.strftime('%I').lstrip('0') or '12'
        am_pm = dt.strftime('%p')
        return f"{month_day}, {hour12} {am_pm}"

    def format_numeric_md_hour(dt):
        month = dt.month
        day = dt.day
        hour12 = dt.strftime('%I').lstrip('0') or '12'
        am_pm_lower = dt.strftime('%p').lower()
        # Use Matplotlib mathtext superscript (ASCII-only, no Unicode)
        ampm_small = f"$^{{\\mathrm{{{am_pm_lower}}}}}$"
        return f"{month}/{day} {hour12}{ampm_small}"

    def parse_and_format_game_date(date_string):
        """Parse a date string like 'sun, october19th' and format it nicely"""
        try:
            # Clean up the input string
            clean_date = date_string.replace(',', '').strip().lower()

            # Extract day of week and date
            parts = clean_date.split()
            if len(parts) >= 2:
                day_of_week = parts[0].capitalize()
                date_part = parts[1]

                # Parse the date part - handle formats like 'october19th', 'oct19', etc.
                import re
                month_match = re.match(r'([a-z]+)(\d+)', date_part)
                if month_match:
                    month_name = month_match.group(1).capitalize()
                    day_num = int(month_match.group(2))

                    # Create a datetime for this year (we'll assume current year)
                    from datetime import datetime
                    current_year = datetime.now().year
                    try:
                        dt = datetime(current_year, {
                            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
                        }.get(month_name.lower(), 1), day_num)

                        # Format using the ordinal function
                        formatted_date = format_month_day_with_ordinal(dt)
                        return f"{day_of_week}, {formatted_date}"
                    except ValueError:
                        pass

            # Fallback: try to format the original string better
            formatted = date_string.replace(',', ', ')
            # Add space between month and day (e.g., "October16th" -> "October 16th")
            import re
            formatted = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', formatted)
            # Capitalize first letter of each word
            formatted = ' '.join(word.capitalize() for word in formatted.split())
            return formatted

        except Exception:
            # Ultimate fallback
            formatted = date_string.replace(',', ', ')
            # Add space between month and day
            import re
            formatted = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', formatted)
            return formatted

    def format_game_time(time_string):
        """Format game time strings nicely"""
        try:
            # Clean up the input
            clean_time = time_string.replace('splits', '').strip()

            # Handle various time formats
            import re

            # Look for time patterns like "1pm", "12:30pm", "1 pm", etc.
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', clean_time.lower())
            if time_match:
                hour = int(time_match.group(1))
                minute = time_match.group(2) or '00'
                am_pm = time_match.group(3).upper()

                # Format nicely
                if minute == '00':
                    return f"{hour} {am_pm}"
                else:
                    return f"{hour}:{minute} {am_pm}"

            # If no match found, just clean up capitalization
            formatted = clean_time.replace('pm', 'PM').replace('am', 'AM')
            return formatted

        except Exception:
            # Fallback
            return time_string.replace('splits', '').strip()

    if upcoming_matchups and (not df_nfl_odds_movements_circa.empty) and ('matchup' in df_nfl_odds_movements_circa.columns):
        upcoming_matchups_normalized = [normalize_matchup(m) for m in upcoming_matchups]
        circa_matchups_normalized = df_nfl_odds_movements_circa['matchup'].apply(normalize_matchup)
        upcoming_week_games = df_nfl_odds_movements_circa[
            circa_matchups_normalized.isin(upcoming_matchups_normalized)
        ]
    else:
        upcoming_week_games = df_nfl_odds_movements_circa

    if not games_with_sufficient_data.empty:
        for _, game in games_with_sufficient_data.iterrows():
            # Format date properly - "Sun, Oct 19th"
            formatted_date = parse_and_format_game_date(game['game_date'])

            # Format time properly
            formatted_time = format_game_time(game['time'])

            # Game title with date and time in styled box
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                padding: 10px;
                                border-radius: 15px;
                                margin: 10px 0 25px 0;
                                text-align: center;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                    <h2 style='color: white; margin: 0 0 5px 0; font-size: 1.8em; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                        {game['teams'][0]} vs {game['teams'][1]}
                    </h2>
                    <p style='color: white; margin: 0; font-size: 1.1em; font-weight: 600; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>
                        {formatted_date} • {formatted_time}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            df = pd.DataFrame({
                "Team": [game['teams'][0], game['teams'][1]],
                "Spread": [game['spread'][0], game['spread'][1]],
                "Moneyline": [game['moneyline'][0], game['moneyline'][1]],
                "Total": [game['total'][0], game['total'][1]]
            })
            st.table(df.set_index('Team'))

            # Create two columns for parallel expanders (like the old modal buttons)
            col1, col2 = st.columns(2)

            for i, team in enumerate(game['teams']):
                # Use the appropriate column for each team (parallel layout)
                with col1 if i == 0 else col2:
                    # Remove emoji from expander title
                    with st.expander(f"Odds Movement for {team}", expanded=False):
                        game_date_clean = game['game_date'].replace(' ', '').strip().lower()
                        game_time_clean = game['time'].strip().lower()
                        matchup_clean = game['matchup'].strip().lower()
                        relevant_odds_movements = df_nfl_odds_movements.loc[
                            (df_nfl_odds_movements['game_date'] == game_date_clean) &
                            (df_nfl_odds_movements['game_time'] == game_time_clean) &
                            (df_nfl_odds_movements['matchup'] == matchup_clean)
                        ].copy()
                        if not relevant_odds_movements.empty:
                            if 'file2' in relevant_odds_movements.columns:
                                relevant_odds_movements['timestamp'] = relevant_odds_movements['file2'].apply(
                                    lambda x: '_'.join(x.split('_')[3:5]).replace('.json', '')
                                )
                                relevant_odds_movements['timestamp'] = pd.to_datetime(
                                    relevant_odds_movements['timestamp'], format='%Y%m%d_%H%M'
                                ).dt.strftime('%-m/%d %-I:%M%p').str.lower()
                            sportsbooks = relevant_odds_movements['sportsbook'].unique().tolist()
                            default_index = sportsbooks.index('Circa') if 'Circa' in sportsbooks else 0
                            selected_sportsbook = st.selectbox("Select Sportsbook", sportsbooks, index=default_index, key=f"sb_{team}_{game['game_date']}_{game['time']}")
                            filtered_data = relevant_odds_movements[relevant_odds_movements['sportsbook'] == selected_sportsbook]
                            st.dataframe(filtered_data[['timestamp', 'sportsbook', 'odds_before', 'odds_after']], use_container_width=True)
                        else:
                            st.write("No odds movement data available for this game.")

            # st.write(' ')
            # st.write(' ')

            # Always show the main Plotly graph first
            selected_matchup = game['matchup']
            if not df_nfl_odds_movements.empty:
                try:
                    # Filter data for this specific matchup using the same cleaning logic
                    clean_game_date = game['game_date'].replace(' ', '').strip().lower()
                    clean_game_time = re.sub(r'\s+', ' ', game['time'].replace('\n', ' ')).strip().lower()
                    clean_matchup = re.sub(r'\s+', ' ', selected_matchup).strip().lower()

                    matchup_mask = (df_nfl_odds_movements['game_date'] == clean_game_date) & \
                                   (df_nfl_odds_movements['game_time'] == clean_game_time) & \
                                   (df_nfl_odds_movements['matchup'] == clean_matchup)
                    selected_data = df_nfl_odds_movements[matchup_mask].copy()

                    if len(selected_data) > 0:
                        # Clean and prepare data
                        selected_data.loc[:, 'team1_odds_before'] = selected_data['team1_odds_before'].replace('PK', 0)
                        selected_data.loc[:, 'team2_odds_before'] = selected_data['team2_odds_before'].replace('PK', 0)
                        selected_data.loc[:, 'team1_odds_before'] = pd.to_numeric(selected_data['team1_odds_before'], errors='coerce')
                        selected_data.loc[:, 'team2_odds_before'] = pd.to_numeric(selected_data['team2_odds_before'], errors='coerce')
                        selected_data = selected_data.dropna(subset=['team1_odds_before', 'team2_odds_before'])

                        # Convert timestamps
                        if 'file2' in selected_data.columns:
                            selected_data['timestamp'] = selected_data['file2'].apply(
                                lambda x: '_'.join(x.split('_')[3:5]).replace('.json', '')
                            )
                            selected_data['timestamp'] = pd.to_datetime(
                                selected_data['timestamp'], format='%Y%m%d_%H%M'
                            )
                        else:
                            selected_data['timestamp'] = pd.to_datetime(selected_data['time_before'], errors='coerce')

                        # Main Plotly graph (always shown)
                        try:
                            # Define colors for different sportsbooks (more visible on grey background)
                            sportsbook_colors = {
                                'Circa': '#FF4500',      # Brighter OrangeRed
                                'Westgate': '#FFD700',   # Gold
                                'South Point': '#32CD32',# LimeGreen
                                'Wynn': '#1E90FF',       # DodgerBlue
                                'Caesars': '#FF1493',    # DeepPink
                                'BetMGM': '#8A2BE2',     # BlueViolet
                                'DK': '#00CED1',         # DarkTurquoise
                                'GLD Nugget': '#FF8C00', # DarkOrange
                                'Stations': '#BA55D3'    # MediumOrchid
                            }

                            sportsbooks = selected_data['sportsbook'].unique()
                            plotted_any = False

                            # Create plotly figure
                            fig = go.Figure()

                            # Plot each sportsbook's odds movement
                            for sportsbook in sportsbooks:
                                sb_data = selected_data[selected_data['sportsbook'] == sportsbook].sort_values('timestamp')
                                if len(sb_data) > 1:  # Only plot if we have multiple data points
                                    color = sportsbook_colors.get(sportsbook, '#95A5A6')

                                    # Add team 1 line with thicker, more visible styling
                                    fig.add_trace(go.Scatter(
                                        x=sb_data['timestamp'],
                                        y=sb_data['team1_odds_before'],
                                        mode='lines+markers',
                                        name=f'{game["teams"][0]} ({sportsbook})',
                                        line=dict(color=color, width=2),
                                        marker=dict(symbol='circle', size=8, color=color, line=dict(width=2, color='white')),
                                        hovertemplate=f'{game["teams"][0]} ({sportsbook})<br>Spread: %{{y}}<br>Time: %{{x}}<extra></extra>'
                                    ))

                                    # Add team 2 line with thicker, more visible styling
                                    fig.add_trace(go.Scatter(
                                        x=sb_data['timestamp'],
                                        y=sb_data['team2_odds_before'],
                                        mode='lines+markers',
                                        name=f'{game["teams"][1]} ({sportsbook})',
                                        line=dict(color=color, width=2),
                                        marker=dict(symbol='square', size=8, color=color, line=dict(width=2, color='white')),
                                        hovertemplate=f'{game["teams"][1]} ({sportsbook})<br>Spread: %{{y}}<br>Time: %{{x}}<extra></extra>'
                                    ))

                                    plotted_any = True

                            if plotted_any:
                                # Update layout with larger size
                                fig.update_layout(
                                    title=f"Odds Movement - {game['teams'][0]} vs {game['teams'][1]}",
                                    title_x=0.29,  # Center the title
                                    # title_xref='container',  # Position relative to entire container
                                    xaxis_title=dict(
                                        text="Time",
                                        font=dict(size=16, color='black')
                                    ),
                                    yaxis_title=dict(
                                        text="Spread",
                                        font=dict(size=16, color='black')
                                    ),
                                    yaxis=dict(
                                        tickformat='+.1f',
                                        tickmode='linear'
                                    ),
                                    hovermode='x unified',
                                    legend=dict(
                                        orientation="v",
                                        yanchor="top",
                                        y=1,
                                        xanchor="left",
                                        x=1.02
                                    ),
                                    margin=dict(l=50, r=150, t=80, b=50),
                                    width=1200,
                                    height=600
                                )

                                # Add gunmetal gridlines
                                fig.update_xaxes(
                                    showgrid=True,
                                    gridwidth=2,
                                    gridcolor='rgba(160, 160, 160, 0.35)',
                                    showline=True,
                                    linewidth=2,
                                    # linecolor='rgba(150, 150, 150, 0.5)'
                                    linecolor='black',
                                    tickfont=dict(color='black'),
                                    tickcolor='black',
                                    ticklen=5,
                                    tickwidth=2
                                )
                                fig.update_yaxes(
                                    showgrid=True,
                                    gridwidth=2,
                                    gridcolor='rgba(160, 160, 160, 0.35)',
                                    showline=True,
                                    linewidth=2,
                                    # linecolor='rgba(150, 150, 150, 0.5)'
                                    linecolor='black',
                                    tickfont=dict(color='black'),
                                    tickcolor='black',
                                    ticklen=5,
                                    tickwidth=2
                                )

                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No valid odds movement data available for plotting this matchup.")
                        except Exception as e:
                            st.error(f"Error creating main plot: {str(e)}")
                            st.write("Raw data for debugging:")
                            st.dataframe(selected_data)

                        # Circa graph in an expandable section below
                        with st.expander("📊 Show Simplified Circa Graph", expanded=False):
                            try:
                                # Filter for Circa sportsbook only
                                circa_data = selected_data[selected_data['sportsbook'] == 'Circa'].copy()

                                if not circa_data.empty and len(circa_data) > 1:
                                    # Sort by timestamp
                                    circa_data = circa_data.sort_values('timestamp')

                                    # Create matplotlib figure
                                    fig, ax = plt.subplots(figsize=(12, 6))

                                    # Plot both teams' odds
                                    ax.plot(circa_data['timestamp'], circa_data['team1_odds_before'],
                                           'o-', color='#FF4500', linewidth=2, markersize=6, label=game['teams'][0])
                                    ax.plot(circa_data['timestamp'], circa_data['team2_odds_before'],
                                           's-', color='#1E90FF', linewidth=2, markersize=6, label=game['teams'][1])

                                    # Formatting
                                    ax.set_title(f'Circa Odds Movement: {game["teams"][0]} vs {game["teams"][1]}',
                                                fontsize=16, fontweight='bold', loc='center')
                                    ax.set_xlabel('Time', fontsize=14)
                                    ax.set_ylabel('Spread', fontsize=14)
                                    ax.legend(fontsize=12)
                                    ax.grid(True, alpha=0.3)

                                    # Format y-axis to show decimal places
                                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.1f}'))

                                    # Format x-axis dates
                                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %I:%M%p'))
                                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

                                    plt.tight_layout()
                                    st.pyplot(fig)
                                    plt.close(fig)
                                else:
                                    st.info("Insufficient Circa odds movement data available for this matchup.")
                            except Exception as e:
                                st.error(f"Error creating Circa plot: {str(e)}")
                                if 'Circa' in selected_data['sportsbook'].values:
                                    st.write("Circa data for debugging:")
                                    st.dataframe(selected_data[selected_data['sportsbook'] == 'Circa'])
                    else:
                        st.warning("No odds movement data found for this matchup.")
                except Exception as e:
                    st.error(f"Error preparing odds data: {str(e)}")
            else:
                st.warning("No odds data available to plot for this matchup.")

            st.write(' ')
            st.divider()
            st.write(' ')
    else:
        st.warning("No upcoming games found in the odds data.")


# Footer
render_footer()