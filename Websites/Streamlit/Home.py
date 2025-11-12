import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie
from PIL import Image
import os

# Configure page
st.set_page_config(page_title="NFL AI", page_icon="🏈", layout="wide")

# Clear all Streamlit cache
st.cache_data.clear()
st.cache_resource.clear()

# Clear session state if needed
if 'first_time' not in st.session_state:
    st.session_state.clear()
    st.session_state['first_time'] = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_file_path_all_team_game_logs = os.path.join(BASE_DIR, 'data/all_team_game_logs.csv')
csv_file_path_all_team_game_logs_2024 = os.path.join(BASE_DIR, 'data/SR-game-logs/all_teams_game_logs_2024.csv')
csv_file_path_all_team_game_logs_2025 = os.path.join(BASE_DIR, 'data/SR-game-logs/all_teams_game_logs_2025.csv')
csv_file_path_odds = os.path.join(BASE_DIR, 'data/odds/nfl_odds_movements.csv')
csv_file_path_circa = os.path.join(BASE_DIR, 'data/odds/nfl_odds_movements_circa.csv')
csv_file_path_teams = os.path.join(BASE_DIR, 'data/Teams.csv')
csv_file_path_games = os.path.join(BASE_DIR, 'data/Games.csv')
csv_file_path_playerstats = os.path.join(BASE_DIR, 'data/PlayerStats.csv')
csv_file_path_schedule_and_game_results = os.path.join(BASE_DIR, 'data/all_teams_schedule_and_game_results_merged.csv')
csv_file_path_all_passing_rushing_receiving = os.path.join(BASE_DIR, 'data/player_stats_pfr.csv')

try:
    df_all_team_game_logs = pd.read_csv(csv_file_path_all_team_game_logs)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_all_team_game_logs}. Please ensure the file exists.")
    df_all_team_game_logs = pd.DataFrame()

try:
    df_all_team_game_logs_2024 = pd.read_csv(csv_file_path_all_team_game_logs_2024)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_all_team_game_logs_2024}. Please ensure the file exists.")
    df_all_team_game_logs_2024 = pd.DataFrame()

try:
    df_all_team_game_logs_2025 = pd.read_csv(csv_file_path_all_team_game_logs_2025)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_all_team_game_logs_2025}. Please ensure the file exists.")
    df_all_team_game_logs_2025 = pd.DataFrame()

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

try:
    df_teams = pd.read_csv(csv_file_path_teams)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_teams}. Please ensure the file exists.")
    df_teams = pd.DataFrame()

try:
    df_games = pd.read_csv(csv_file_path_games)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_games}. Please ensure the file exists.")
    df_games = pd.DataFrame()

try:
    df_playerstats = pd.read_csv(csv_file_path_playerstats)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_playerstats}. Please ensure the file exists.")
    df_playerstats = pd.DataFrame()

try:
    df_schedule_and_game_results = pd.read_csv(csv_file_path_schedule_and_game_results)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_schedule_and_game_results}. Please ensure the file exists.")
    df_schedule_and_game_results = pd.DataFrame()

try:
    df_all_passing_rushing_receiving = pd.read_csv(csv_file_path_all_passing_rushing_receiving)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_all_passing_rushing_receiving}. Please ensure the file exists.")
    df_all_passing_rushing_receiving = pd.DataFrame()

st.session_state['df_all_team_game_logs'] = df_all_team_game_logs
st.session_state['df_all_team_game_logs_2024'] = df_all_team_game_logs_2024
st.session_state['df_all_team_game_logs_2025'] = df_all_team_game_logs_2025
st.session_state['df_nfl_odds_movements'] = df_nfl_odds_movements
st.session_state['df_nfl_odds_movements_circa'] = df_nfl_odds_movements_circa
st.session_state['df_teams'] = df_teams
st.session_state['df_games'] = df_games
st.session_state['df_playerstats'] = df_playerstats
st.session_state['df_schedule_and_game_results'] = df_schedule_and_game_results
st.session_state['df_all_passing_rushing_receiving'] = df_all_passing_rushing_receiving

# ---- Titles ---- #
st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            NFL AI
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Welcome to NFL AI
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
# st.title('NFL AI')
# st.write('Welcome to NFL AI')
# st.write("[My Repo >](https://github.com/bestisblessed)")
# current_dir = os.path.dirname(os.path.abspath(__file__))
# justin_jefferson_path = os.path.join(current_dir, 'images/jettas.jpg')
# st.image(justin_jefferson_path, use_column_width=True)
# st.image(justin_jefferson_path, width=300)

# ---- Overview Section ---- #
st.divider()
# st.write('######')
# st.markdown("""
#     <div style='text-align: center; margin-bottom: 2rem;'>
#         <h2 style='color: #1a202c; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;'>Overview</h2>
#     </div>
#     """, unsafe_allow_html=True)
        # <p style='color: #6c757d; font-size: 1rem;'>Comprehensive NFL analytics platform powered by machine learning</p>

left_column, right_column = st.columns([1, 2])
with left_column:
    # st.write('######')
    st.write('######')
    st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;">Overview</h1></div>', unsafe_allow_html=True)
    st.markdown('''
- Predictive player performance models
- Machine-learning projections w/ calculated value opportunities every week
- Comprehensive historical analysis
- Player and team trend dashboards for rapid analysis 
- Live odds movement and historical line analytics
    ''')
with right_column:
    # st.write('######')
    st.write('')
    # st_lottie(lottie_picture1, height=400, width=400, key='lottie1')
    image_path = os.path.join(BASE_DIR, 'images/justin-jefferson-2.jpg')
    if os.path.exists(image_path):
        right_column_image = Image.open(image_path)
        st.image(right_column_image, use_container_width=True)

# ---- Pages & Tools ---- #
st.divider()
st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h2 style='color: #1a202c; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;'>Features</h2>
        <p style='color: #6c757d; font-size: 1rem;'>Explore our comprehensive suite of NFL analytics, predictions, and betting tools</p>
    </div>
    """, unsafe_allow_html=True)

# Enhanced CSS for polished tool cards
st.markdown("""
<style>
.tool-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid #e9ecef;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 0.5rem 0;
    box-shadow: 0 3px 14px rgba(0,0,0,0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.tool-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    transform: scaleX(0);
    transition: transform 0.3s ease;
}
.tool-card:hover::before {
    transform: scaleX(1);
}
.tool-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    border-color: #dee2e6;
}
.tool-emoji {
    font-size: 1.9rem;
    margin-bottom: 0.75rem;
    display: block;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.tool-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: #1a202c;
    margin-bottom: 0.6rem;
    letter-spacing: -0.02em;
}
.tool-description {
    color: #4a5568;
    font-size: 0.95rem;
    line-height: 1.55;
    margin: 0;
    font-weight: 400;
}
.tools-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
}
.tools-last-row {
    grid-column: 1 / -1;
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
}
.tools-last-row .tool-card {
    flex: 0 1 calc(33.333% - 0.67rem);
    max-width: calc(33.333% - 0.67rem);
}
@media (max-width: 1024px) {
    .tools-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .tools-last-row .tool-card {
        flex: 0 1 calc(50% - 0.5rem);
        max-width: calc(50% - 0.5rem);
    }
}
@media (max-width: 768px) {
    .tools-grid {
        grid-template-columns: 1fr;
        gap: 0.75rem;
    }
    .tools-last-row .tool-card {
        flex: 0 1 100%;
        max-width: 100%;
    }
    .tool-card {
        padding: 1.25rem;
    }
    .tool-emoji {
        font-size: 1.8rem;
    }
    .tool-title {
        font-size: 1.1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Streamlined tool data without categories
tools = [
    {"emoji": "⚔️", "title": "Matchup Generator", "description": "Head-to-head team analysis with comprehensive trends, defensive metrics, and player performance comparisons for strategic game planning."},
    {"emoji": "🔮", "title": "Weekly Projections", "description": "ML-generated player projections for upcoming games with fantasy points, yards, and touchdown predictions organized by kickoff time."},
    {"emoji": "📋", "title": "Weekly Leaders", "description": "Top projected performers by position with detailed statistical breakdowns and performance rankings for fantasy and betting insights."},
    {"emoji": "💎", "title": "Value Play Finder", "description": "High-value betting opportunities identified through edge analysis, EV calculations, and matchup-specific recommendations."},
    {"emoji": "📈", "title": "Odds Dashboard", "description": "Live odds movement tracking across major sportsbooks with interactive charts and historical movement analysis."},
    {"emoji": "🥇", "title": "Player Dashboard", "description": "Comprehensive player analytics with career statistics, performance trends, and headshot integration for detailed player evaluation."},
    {"emoji": "📈", "title": "Player Trends", "description": "Advanced position-specific analytics with statistical trends, distributions, and historical performance patterns across seasons."},
    {"emoji": "📉", "title": "Team Trends", "description": "Team performance analysis including home/away splits, offensive/defensive metrics, and comprehensive statistical rankings."},
    {"emoji": "💰", "title": "Betting Trends", "description": "ATS and Over/Under performance tracking with detailed record analysis, push tracking, and betting strategy insights."},
    {"emoji": "📊", "title": "Scoring Trends", "description": "Touchdown and scoring metrics by position with offensive production and defensive vulnerability analysis across the league."},
    {"emoji": "💍", "title": "NFL Standings", "description": "Current standings by division with win-loss-tie records, team performance statistics, and playoff positioning indicators."}
]

# Generate HTML for all tool cards in a single grid
tool_cards_parts = ['<div class="tools-grid">']

# First 9 tools (3 rows of 3)
for tool in tools[:9]:
    tool_cards_parts.append(
        f'<div class="tool-card">'
        f'<div class="tool-emoji">{tool["emoji"]}</div>'
        f'<div class="tool-title">{tool["title"]}</div>'
        f'<div class="tool-description">{tool["description"]}</div>'
        f'</div>'
    )

# Last 2 tools wrapped in a centered container
if len(tools) > 9:
    tool_cards_parts.append('<div class="tools-last-row">')
    for tool in tools[9:]:
        tool_cards_parts.append(
            f'<div class="tool-card">'
            f'<div class="tool-emoji">{tool["emoji"]}</div>'
            f'<div class="tool-title">{tool["title"]}</div>'
            f'<div class="tool-description">{tool["description"]}</div>'
            f'</div>'
        )
    tool_cards_parts.append('</div>')

tool_cards_parts.append('</div>')
st.markdown(''.join(tool_cards_parts), unsafe_allow_html=True)

# ---- Platform Stats ---- #
st.markdown("""
<style>
.platform-stats-container {
    text-align: center;
    margin: 3rem 0 2rem 0;
    padding: 2rem;
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border-radius: 16px;
    border: 1px solid rgba(52, 152, 219, 0.2);
}
.platform-stats-title {
    color: #7f8c8d;
    font-size: 1rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.platform-stats-values {
    color: #2c3e50;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.platform-stats-subtitle {
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

season_sources = [
    st.session_state.get('df_all_team_game_logs'),
    st.session_state.get('df_all_team_game_logs_2024'),
    st.session_state.get('df_all_team_game_logs_2025'),
    st.session_state.get('df_games'),
    st.session_state.get('df_schedule_and_game_results'),
    st.session_state.get('df_all_passing_rushing_receiving')
]

game_sources = [
    st.session_state.get('df_all_team_game_logs'),
    st.session_state.get('df_all_team_game_logs_2024'),
    st.session_state.get('df_all_team_game_logs_2025'),
    st.session_state.get('df_games'),
    st.session_state.get('df_schedule_and_game_results')
]

# Primary source: player_stats_pfr.csv has the most comprehensive player list
player_stats_pfr_path = os.path.join(BASE_DIR, 'data/player_stats_pfr.csv')
player_sources = []

if os.path.exists(player_stats_pfr_path):
    try:
        df_player_stats_pfr = pd.read_csv(player_stats_pfr_path)
        player_sources.append(df_player_stats_pfr)
    except:
        pass

# Also include other sources as fallback
player_sources.extend([
    st.session_state.get('df_all_passing_rushing_receiving'),
    st.session_state.get('df_playerstats'),
])

# Also check roster files directly for comprehensive player lists
roster_dir = os.path.join(BASE_DIR, 'data/rosters')
if os.path.exists(roster_dir):
    for roster_file in os.listdir(roster_dir):
        if roster_file.endswith('.csv'):
            try:
                roster_df = pd.read_csv(os.path.join(roster_dir, roster_file))
                player_sources.append(roster_df)
            except:
                pass

def collect_seasons(dfs):
    seasons: set[int] = set()
    for df in dfs:
        if df is None or df.empty:
            continue
        for col in ['season', 'Season', 'SEASON']:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce').dropna().astype(int)
                seasons.update(values.tolist())
        for col in ['game_id', 'GameID', 'game_id_simple']:
            if col in df.columns:
                season_guess = df[col].astype(str).str.slice(0, 4)
                values = pd.to_numeric(season_guess, errors='coerce').dropna().astype(int)
                seasons.update(values.tolist())
    return seasons

def collect_games(dfs):
    games: set[str] = set()
    for df in dfs:
        if df is None or df.empty:
            continue
        for col in ['game_id', 'GameID', 'game_id_simple', 'schedule_id']:
            if col in df.columns:
                ids = df[col].astype(str).dropna()
                games.update(ids.tolist())
                break
    return games

def collect_players(dfs):
    players: set[str] = set()
    player_cols = ['player_id', 'player', 'player_display_name', 'full_name', 'name', 'player_name', 'player_name_with_position']
    
    for df in dfs:
        if df is None or df.empty:
            continue
        # Check ALL possible player columns, not just the first match
        for col in player_cols:
            if col in df.columns:
                names = df[col].astype(str).dropna()
                # Filter out empty strings and common non-player values
                valid_names = names[~names.isin(['', 'nan', 'None', 'NaN'])]
                players.update(valid_names.tolist())
    return players

seasons = collect_seasons(season_sources)
games = collect_games(game_sources)
players = collect_players(player_sources)

# Format stats inline with dots (matching PDF style)
seasons_text = f"{len(seasons)} Seasons"
games_text = f"{len(games):,} Games"
players_text = f"{len(players):,} Players"

stats_html = f'''
<div class="platform-stats-container">
    <div class="platform-stats-title">Dataset Metrics</div>
    <div class="platform-stats-values">{seasons_text} · {games_text} · {players_text}</div>
    <div class="platform-stats-subtitle">Updated Weekly After All Games Have Concluded</div>
</div>
'''
st.markdown(stats_html, unsafe_allow_html=True)

# # Enhanced call-to-action with better styling
# st.markdown("""
# <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); color: white; padding: 2.5rem 2rem; border-radius: 20px; text-align: center; margin: 3rem 0; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);'>
#     <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🚀</div>
#     <h3 style='margin: 0 0 1rem 0; color: white; font-size: 1.5rem; font-weight: 700;'>Ready to Explore NFL AI?</h3>
#     <p style='margin: 0; font-size: 1.1rem; opacity: 0.95; line-height: 1.6;'>Navigate to any page using the sidebar menu to dive deep into advanced NFL analytics, predictions, and betting insights!</p>
# </div>
# """, unsafe_allow_html=True)

# # ---- Some Samples ---- #
# st.divider()
# st.header('Some Samples')
# st.write('##')

# ### Sample Code
# st.code('''
# import numpy as np
# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# import requests
# from streamlit_lottie import st_lottie
# from PIL import Image
# ''', language='python')

# ### Sample 1
# image_column_left, text_column_right = st.columns((1, 2))
# with image_column_left:
#     st.image(picture1, use_column_width=True, caption="UFC 287")
# with text_column_right:
#     st.markdown('#### Sample 1')
#     st.write('''
#         Here is one of my examples, this is what it does:
#         1. Uses my unique and confidential nfl dataset to analyze
#         2. Finds outlying trends
#         3. Makes game and player predictions
#     ''')

# ### Sample 2
# text_column_left, image_column_right = st.columns((2, 1))
# with text_column_left:
#     st.markdown('#### Sample 2')
#     st.write('''
#         Here is another example, this is what it does:
#         1. Uses my unique and confidential nfl dataset to analyze
#         2. Finds outlying trends
#         3. Makes game and player predictions
#     ''')
# with image_column_right:
#     st.image(picture2, use_column_width=True, caption="Before the crash")

# ---- Galleria ---- #
st.divider()
# st.header('Galleria')
st.write()

# image1list = Image.open('images/ceedee.jpg')
# image2list = Image.open('images/dez.jpg')
# image3list = Image.open('images/irvin.jpg')

# Get the current directory of the script (Home.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full absolute paths for each image
image1_path = os.path.join(current_dir, 'images/ceedee.jpg')
image2_path = os.path.join(current_dir, 'images/dez2.jpg')
image3_path = os.path.join(current_dir, 'images/irvin.jpg')
# image4_path = os.path.join(current_dir, 'images/jettas.jpg')

# Load the images using their absolute paths
image1list = Image.open(image1_path)
image2list = Image.open(image2_path)
image3list = Image.open(image3_path)
# image4list = Image.open(image4_path)

# col1, col2, col3 = st.columns(3)
col1, col2, col3 = st.columns([1, 1.25, 1])  # Proportions for the columns
with col1:
    st.image(image1list, use_container_width=True, caption="Ceedee 88")
with col2:
    st.image(image2list, use_container_width=True, caption="Bryant 88")
    # st.image(image2list, height=400, caption="Bryant 88")  # Specify height for this image
with col3:
    st.image(image3list, use_container_width=True, caption="Irvin 88")

# JD image full size
st.write('##')
jd_image_path = os.path.join(current_dir, 'images/jd.png')
if os.path.exists(jd_image_path):
    st.image(Image.open(jd_image_path), use_container_width=True, caption="JD5")
else:
    st.warning(f"JD image not found. Tried: {jd_image_path}")

### JJettas
# st.write('##')
# col1, col2, col3 = st.columns([1, 4, 1])
# with col2:
#     st.image(image4list, use_container_width=True, caption="JJettas")

# ### Video
# video1 = 'https://www.youtube.com/watch?v=K8RQkt3Ee0Y'
# st.write('##')
# col1, col2, col3 = st.columns([1, 4, 1])
# with col2:
#     st.video(video1)
#     st.markdown("<p style='text-align: center; color: white;'>Legendary</p>", unsafe_allow_html=True)
#     # st.caption("Legendary")
# # st.video(video1)

# ---- Contact Me ---- #
st.divider()
st.header('Contact Me')
# st.write('##')
# st.write('Hover over this text for more information [?](Your help text here)')
st.markdown('By Tyler Durette')
st.markdown("NFL AI © 2023 | [GitHub](https://github.com/bestisblessed) | [Contact Me](tyler.durette@gmail.com)")
