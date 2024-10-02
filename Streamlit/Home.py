import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie
from PIL import Image
import os

st.set_page_config(page_title="NFL AI", page_icon="🏈", layout="wide")

# ---- Titles ---- #
st.title('NFL AI')
st.write('Welcome to NFL AI')
# st.write("[My Repo >](https://github.com/bestisblessed)")
# current_dir = os.path.dirname(os.path.abspath(__file__))
# justin_jefferson_path = os.path.join(current_dir, 'Streamlit/images/jettas.jpg')
# st.image(justin_jefferson_path, use_column_width=True)
# st.image(justin_jefferson_path, width=300)

# Get the current directory of the script (Home.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load the CSV data into a DataFrame
csv_file_path = os.path.join(current_dir, 'data/all_team_game_logs.csv')
df_team_game_logs = pd.read_csv(csv_file_path)
csv_file_path_2 = os.path.join(current_dir, 'data/all_teams_schedule_and_game_results_merged.csv')
df_schedule_and_game_results = pd.read_csv(csv_file_path_2)

# ---- Loading Data ---- #
df_teams = pd.read_csv('Streamlit/data/Teams.csv')
df_games = pd.read_csv('Streamlit/data/Games.csv')
df_playerstats = pd.read_csv('Streamlit/data/PlayerStats.csv')
# df_team_game_logs = pd.read_csv('Streamlit/data/all_teams_game_logs.csv')
# df_schedule_and_game_results = pd.read_csv('Streamlit/data/all_teams_schedule_and_game_results_merged.csv')
st.session_state['df_teams'] = df_teams
st.session_state['df_games'] = df_games
st.session_state['df_playerstats'] = df_playerstats
st.session_state['df_team_game_logs'] = df_team_game_logs
st.session_state['df_schedule_and_game_results'] = df_schedule_and_game_results

# ---- Loading Other Files ---- #
def load_lottie_pictures(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_picture1 = load_lottie_pictures("https://lottie.host/9501172e-b94f-441d-a10d-406d7536663c/510yizrK3A.json")

# picture1 = Image.open('Streamlit/images/pereira-adesanya-faceoff.jpeg')
# picture2 = Image.open('Streamlit/images/ferg.jpg')

# ---- Introduction and Bio ---- #
st.divider()
st.header('Introduction')
left_column, right_column = st.columns(2)
with left_column:
    st.write('##')
    st.write('''
        - Historical AI chatbot since 2000 season
        - Predictive modeling
        - Game outcomes
        - Player performances
        - Standings & league leaders
        - Arbitrage opportunities
        - Random analysis

        If this all interests you, this is the spot.
    ''')
with right_column:
    st_lottie(lottie_picture1, height=400, width=400, key='lottie1')

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

# image1list = Image.open('Streamlit/images/ceedee.jpg')
# image2list = Image.open('Streamlit/images/dez.jpg')
# image3list = Image.open('Streamlit/images/irvin.jpg')

# Get the current directory of the script (Home.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full absolute paths for each image
image1_path = os.path.join(current_dir, 'Streamlit/images/ceedee.jpg')
image2_path = os.path.join(current_dir, 'Streamlit/images/dez2.jpg')
image3_path = os.path.join(current_dir, 'Streamlit/images/irvin.jpg')
image4_path = os.path.join(current_dir, 'Streamlit/images/jettas.jpg')

# Load the images using their absolute paths
image1list = Image.open(image1_path)
image2list = Image.open(image2_path)
image3list = Image.open(image3_path)
image4list = Image.open(image4_path)

# col1, col2, col3 = st.columns(3)
col1, col2, col3 = st.columns([1, 1.25, 1])  # Proportions for the columns
with col1:
    st.image(image1list, use_column_width=True, caption="Ceedee 88")
with col2:
    st.image(image2list, use_column_width=True, caption="Bryant 88")
    # st.image(image2list, height=400, caption="Bryant 88")  # Specify height for this image
with col3:
    st.image(image3list, use_column_width=True, caption="Irvin 88")

### JJettas
st.write('##')
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.image(image4list, use_column_width=True, caption="JJettas")
# st.image(image4list, use_column_width=True, caption="JJettas")
# st.image(image4list, width=200, caption="JJettas")

### Video
video1 = 'https://www.youtube.com/watch?v=K8RQkt3Ee0Y'
st.write('##')
# col1, col2, col3 = st.columns([1, 4, 1])
# with col2:
#     st.video(video1)
#     st.caption("Legendary")
st.video(video1)

# ---- Contact Me ---- #
st.divider()
st.header('Contact Me')
st.write('##')
# st.write('Hover over this text for more information [?](Your help text here)')
st.markdown('By Tyler Durette')
st.markdown("NFL AI © 2023 | [GitHub](https://github.com/bestisblessed) | [Contact Me](tyler.durette@gmail.com)")
