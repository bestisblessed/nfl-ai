import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie
from PIL import Image

st.set_page_config(page_title="NFL AI", page_icon="🏈", layout="wide")

# Load the background image
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_image

bg_image_base64 = get_base64_image('Streamlit/data/wp11925945-justin-jefferson-2023-wallpapers.jpg')

# Add CSS for the background image behind the title
st.markdown(
    f"""
    <style>
    .title-area {{
        background-image: url("data:image/jpeg;base64,{bg_image_base64}");
        background-size: cover;
        background-position: center;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        padding: 2rem;
        border-radius: 10px;
    }}
    </style>
    <div class="title-area">
        <h1>NFL AI</h1>
        <p>Welcome to NFL AI</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Titles ---- #
st.title('NFL AI')
st.write('Welcome to NFL AI')
# st.write("[My Repo >](https://github.com/bestisblessed)")

# ---- Loading Data ---- #
df_teams = pd.read_csv('Streamlit/data/Teams.csv')
df_games = pd.read_csv('Streamlit/data/Games.csv')
df_playerstats = pd.read_csv('Streamlit/data/PlayerStats.csv')
df_team_game_logs = pd.read_csv('Streamlit/data/all_teams_game_logs_2023.csv')
df_schedule_and_game_results = pd.read_csv('Streamlit/data/all_teams_schedule_and_game_results_merged.csv')
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
# st.header('Galleria')

image1list = Image.open('Streamlit/images/wp12999923-ceedee-lamb-cowboys-wallpapers.jpg')
image2list = Image.open('Streamlit/images/wp1872273-dez-bryant-wallpapers.jpg')
image3list = Image.open('Streamlit/images/wp9604297-michael-irvin-wallpapers.jpg')

col1, col2, col3 = st.columns(3)
with col1:
    st.image(image1list, use_column_width=True, caption="Image 1")
with col2:
    st.image(image2list, use_column_width=True, caption="Image 2")
with col3:
    st.image(image3list, use_column_width=True, caption="Image 3")

### Video
video1 = 'https://www.youtube.com/watch?v=RABQY0t1Bqw&list=PL3HhsOxjnSwI9TDupRLRhPN3TAG4CFGPe&index=40'
st.write('##')
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.video(video1)
    st.caption("Legendary")

# ---- Contact Me ---- #
st.divider()
st.header('Contact Me')
st.write('##')
# st.write('Hover over this text for more information [?](Your help text here)')
st.markdown('By Tyler Durette')
st.markdown("NFL AI © 2023 | [GitHub](https://github.com/bestisblessed) | [Contact Me](tyler.durette@gmail.com)")
