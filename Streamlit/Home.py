import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie
from PIL import Image

st.set_page_config(page_title="NFL AI", page_icon="🏈", layout="wide")

# ---- Titles ---- #
st.title('NFL AI')
st.markdown('###### By Tyler Durette')
st.write('Welcome to NFL AI. Time to fucking win')
st.write("[Learn More >](https://github.com/bestisblessed)")
# with st.container():
#     st.title('NFL AI')
#     st.markdown('###### By Tyler Durette')
#     st.write('Welcome to NFL AI. Time to fucking win')
#     st.write("[Learn More >](https://github.com/bestisblessed)")

# ---- Loading Data ---- #
df_teams = pd.read_csv('./data/Teams.csv')
df_games = pd.read_csv('./data/Games.csv')
df_playerstats = pd.read_csv('./data/PlayerStats.csv')
dataframes = [df_teams, df_games, df_playerstats]
st.session_state['df_teams'] = df_teams
st.session_state['df_games'] = df_games
st.session_state['df_playerstats'] = df_playerstats

# # ---- Sidebar ---- #
# with st.sidebar:
#     st.write("Navigation")
#     page = st.radio("Go to", ['Home', 'Introduction', 'Samples', 'Galleria', 'Contact'])
#     st.write("Stuff:")
#     st.write("This app is dedicated to NFL analytics and predictions.")

# ---- Loading Other Files ---- #
### Lottie 1
def load_lottie_pictures(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
lottie_picture1 = load_lottie_pictures("https://lottie.host/9501172e-b94f-441d-a10d-406d7536663c/510yizrK3A.json")

### Picture 1
picture1 = Image.open('./images/pereira-adesanya-faceoff.jpeg')

### Picture 2
picture2 = Image.open('./images/ferg.jpg')

# ---- Introduction and Bio ---- #
# st.write('---')
st.divider()
st.header('Introduction')
left_column, right_column = st.columns(2)
with left_column:
    st.write('##')
    st.write('''
             I predict winners. Simple as that. All I do is win.
             - Predictive modeling
             - Game outcomes
             - Player performances
             - Arbitrage opportunities
             - Random shit

             If this all interests you, this is your lucky day. Nobody is better than us.
             ''')
with right_column:
    st_lottie(lottie_picture1, height=400, width=400, key='lottie1')


# ---- Some Samples ---- #
# st.write('---')
st.divider()
st.header('Some Samples')

### Sample Code
st.write('##')
st.code('''
        import numpy as np
        import streamlit as st
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import requests
        from streamlit_lottie import st_lottie
        from PIL import Image
        ''', language='python'
        )

### Sample 1
st.write('##')
image_column_left, text_column_right = st.columns((1, 2)) ### 2nd column twice as big as 1st
with image_column_left:
    st.image(picture1, use_column_width=True, caption="UFC 287")
with text_column_right:
    st.markdown('#### Sample 1')
    st.write('''
            Here is one of my examples, this is what it does:
            1. Uses my unique and confidential nfl dataset to analyze 
            2. Finds outlying trends
            3. Makes game and player predictions
             ''')

### Sample 2
st.write('##')
text_column_left, image_column_right = st.columns((2, 1)) ### 2nd column twice as big as 1st
with text_column_left:
    st.markdown('#### Sample 2')
    st.write('''
            Here is one of my examples, this is what it does:
            1. Uses my unique and confidential nfl dataset to analyze 
            2. Finds outlying trends
            3. Makes game and player predictions
             ''')
with image_column_right:
    st.image(picture2, use_column_width=True, caption="Before the crash")

### Footers for Samples Section
st.markdown("""
<footer class='font-style'>Your Footer Content</footer>
""", unsafe_allow_html=True)


# ---- Galleria ---- #
# st.write('---')
st.divider()
st.header('Galleria')
image1list = Image.open('./images/friends.jpg')
image2list = Image.open('./images/holloway1.jpeg')
image3list = Image.open('./images/jonesgustaffson.jpg')
### Bad Method
# images = [image1list, image2list, image3list]  # List of images
# st.image(images, width=600, caption=["Image 1", "Image 2", "Image 3"]) # Displaying multiple images side by side

### Correct Method
col1, col2, col3 = st.columns(3)  # Creates three columns
with col1:
    st.image(image1list, use_column_width=True, caption="Image 1")
with col2:
    st.image(image2list, use_column_width=True, caption="Image 2")
with col3:
    st.image(image3list, use_column_width=True, caption="Image 3")

### Video
video1 = 'https://www.youtube.com/watch?v=KxeQHTyfbc0&list=PL3HhsOxjnSwLz4DnP7jQxk8BnvvanToll&index=7&ab_channel=UFC'
st.write('##')
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.video(video1)
    st.caption("To get hyped")



# ---- Contact Me ---- #
# st.write('---')
st.divider()
st.header('Contact Me')
st.write('##')
st.write('Hover over this text for more information [?](Your help text here)')
# st.write('---')
st.divider()
st.markdown("NFL AI © 2023 | [GitHub](https://github.com/bestisblessed) | [Contact](https://example.com/contact)")
