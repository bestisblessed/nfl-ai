import streamlit as st

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie
from PIL import Image
import os

# Configure page
st.set_page_config(page_title="NFL AI", page_icon="🏈")

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
csv_file_path_all_passing_rushing_receiving = os.path.join(BASE_DIR, 'data/all_passing_rushing_receiving.csv')

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
st.title('NFL AI')
st.write('Welcome to NFL AI')
# st.write("[My Repo >](https://github.com/bestisblessed)")
# current_dir = os.path.dirname(os.path.abspath(__file__))
# justin_jefferson_path = os.path.join(current_dir, 'images/jettas.jpg')
# st.image(justin_jefferson_path, use_column_width=True)
# st.image(justin_jefferson_path, width=300)

# # Get the current directory of the script (Home.py)
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # Load the CSV data into a DataFrame

# csv_file_path = os.path.join(current_dir, 'data/all_team_game_logs.csv')
# df_team_game_logs = pd.read_csv(csv_file_path)
# csv_file_path_4 = os.path.join(current_dir, 'data/SR-game-logs/all_teams_game_logs_2024.csv')
# df_team_game_logs_2024 = pd.read_csv(csv_file_path_4)
# csv_file_path_2 = os.path.join(current_dir, 'data/all_teams_schedule_and_game_results_merged.csv')
# df_schedule_and_game_results = pd.read_csv(csv_file_path_2)
# csv_file_path_3 = os.path.join(current_dir, 'data/all_passing_rushing_receiving.csv')
# df_all_passing_rushing_receiving = pd.read_csv(csv_file_path_3)
# # csv_file_path_5 = os.path.join(current_dir, 'data/odds/nfl_odds_movements.csv')
# # df_nfl_odds_movements = pd.read_csv(csv_file_path_5)

# # Add these lines where you load other CSV files
# csv_file_path_odds = os.path.join(current_dir, 'data/odds/nfl_odds_movements.csv')
# csv_file_path_circa = os.path.join(current_dir, 'data/odds/nfl_odds_movements_circa.csv')

# try:
#     df_nfl_odds_movements = pd.read_csv(csv_file_path_odds)
#     df_nfl_odds_movements_circa = pd.read_csv(csv_file_path_circa)
# except FileNotFoundError:
#     st.warning("Odds data files not found. Some features may be unavailable.")
#     df_nfl_odds_movements = pd.DataFrame()
#     df_nfl_odds_movements_circa = pd.DataFrame()

# # ---- Loading Data ---- #
# csv_file_path_teams = os.path.join(current_dir, 'data/Teams.csv')
# csv_file_path_games = os.path.join(current_dir, 'data/Games.csv')
# csv_file_path_playerstats = os.path.join(current_dir, 'data/PlayerStats.csv')
# df_teams = pd.read_csv(csv_file_path_teams)
# df_games = pd.read_csv(csv_file_path_games)
# df_playerstats = pd.read_csv(csv_file_path_playerstats)
# st.session_state['df_teams'] = df_teams
# st.session_state['df_games'] = df_games
# st.session_state['df_playerstats'] = df_playerstats
# st.session_state['df_team_game_logs'] = df_team_game_logs
# st.session_state['df_schedule_and_game_results'] = df_schedule_and_game_results
# st.session_state['df_all_passing_rushing_receiving'] = df_all_passing_rushing_receiving
# st.session_state['df_team_game_logs_2024'] = df_team_game_logs_2024
# st.session_state['df_nfl_odds_movements'] = df_nfl_odds_movements
# st.session_state['df_nfl_odds_movements_circa'] = df_nfl_odds_movements_circa

# ---- Loading Other Files ---- #
# def load_lottie_pictures(url):
#     r = requests.get(url)
#     if r.status_code != 200:
#         return None
#     return r.json()
# lottie_picture1 = load_lottie_pictures("https://lottie.host/9501172e-b94f-441d-a10d-406d7536663c/510yizrK3A.json")

# picture1 = Image.open('images/pereira-adesanya-faceoff.jpeg')
# picture2 = Image.open('images/ferg.jpg')

# ---- Introduction and Bio ---- #
st.divider()
st.header('Introduction')
left_column, right_column = st.columns([1, 2])  # Right column gets twice the width
with left_column:
    st.write('##')
    st.write('''
        - Historical AI chatbot since 2000 season
        - Predictive modeling
        - Odds movement dashboard
        - Game outcomes
        - Player performances
        - Standings & league leaders 
        - Arbitrage opportunities
        - Random analysis
    ''')
with right_column:
    # st_lottie(lottie_picture1, height=400, width=400, key='lottie1')
    image_path = os.path.join(BASE_DIR, 'images/justin-jefferson-2.jpg')
    right_column_image = Image.open(image_path)
    st.image(right_column_image, use_container_width=True)  # Increased width significantly

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
st.header('Galleria')
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

### JJettas
# st.write('##')
# col1, col2, col3 = st.columns([1, 4, 1])
# with col2:
#     st.image(image4list, use_container_width=True, caption="JJettas")

### Video
video1 = 'https://www.youtube.com/watch?v=K8RQkt3Ee0Y'
st.write('##')
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.video(video1)
    st.markdown("<p style='text-align: center; color: white;'>Legendary</p>", unsafe_allow_html=True)
    # st.caption("Legendary")
# st.video(video1)

# ---- Contact Me ---- #
st.divider()
st.header('Contact Me')
# st.write('##')
# st.write('Hover over this text for more information [?](Your help text here)')
st.markdown('By Tyler Durette')
st.markdown("NFL AI © 2023 | [GitHub](https://github.com/bestisblessed) | [Contact Me](tyler.durette@gmail.com)")
