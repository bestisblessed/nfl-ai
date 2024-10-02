import os
import requests

# Create a directory to store images
os.makedirs('images', exist_ok=True)

# teams = {
#     'crd': 'ARI',
#     'atl': 'ATL',
#     'rav': 'BAL',
#     'buf': 'BUF',
#     'car': 'CAR',
#     'chi': 'CHI',
#     'cin': 'CIN',
#     'cle': 'CLE',
#     'dal': 'DAL',
#     'den': 'DEN',
#     'det': 'DET',
#     'gnb': 'GB',
#     'htx': 'HOU',
#     'clt': 'IND',
#     'jax': 'JAX',
#     'kan': 'KC',
#     'sdg': 'LAC',
#     'ram': 'LAR',
#     'rai': 'LV',
#     'mia': 'MIA',
#     'min': 'MIN',
#     'nwe': 'NE',
#     'nor': 'NO',
#     'nyg': 'NYG',
#     'nyj': 'NYJ',
#     'phi': 'PHI',
#     'pit': 'PIT',
#     'sea': 'SEA',
#     'sfo': 'SF',
#     'tam': 'TB',
#     'oti': 'TEN',
#     'was': 'WAS'
# }


# # List of URLs for team logos and their corresponding abbreviations
# team_logos = {
#     "https://cdn.fastassets.io/images/team-logos/New-Orleans-Saints.png": "NO",
#     "https://cdn.fastassets.io/images/team-logos/Atlanta-Falcons.png": "ATL",
#     "https://cdn.fastassets.io/images/team-logos/Pittsburgh-Steelers.png": "PIT",
#     "https://cdn.fastassets.io/images/team-logos/Indianapolis-Colts.png": "IND",
#     "https://cdn.fastassets.io/images/team-logos/Jacksonville-Jaguars.png": "JAX",
#     "https://cdn.fastassets.io/images/team-logos/Houston-Texans.png": "HOU",
#     "https://cdn.fastassets.io/images/team-logos/Minnesota-Vikings.png": "MIN",
#     "https://cdn.fastassets.io/images/team-logos/Green-Bay-Packers.png": "GB",
#     "https://cdn.fastassets.io/images/team-logos/Cincinnati-Bengals.png": "CIN",
#     "https://cdn.fastassets.io/images/team-logos/Carolina-Panthers.png": "CAR",
#     "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lar.png": "LAR",  # Corrected
#     "https://cdn.fastassets.io/images/team-logos/Chicago-Bears.png": "CHI",
#     "https://cdn.fastassets.io/images/team-logos/Denver-Broncos.png": "DEN",
#     "https://cdn.fastassets.io/images/team-logos/Tampa-Bay-Buccaneers.png": "TB",
#     "https://cdn.fastassets.io/images/team-logos/Seattle-Seahawks.png": "SEA",
#     "https://cdn.fastassets.io/images/team-logos/San-Francisco-49ers.png": "SF",
#     "https://cdn.fastassets.io/images/team-logos/Arizona-Cardinals.png": "ARI",
#     "https://cdn.fastassets.io/images/team-logos/Dallas-Cowboys.png": "DAL",
#     "https://cdn.fastassets.io/images/team-logos/Philadelphia-Eagles.png": "PHI",
#     "https://cdn.fastassets.io/images/team-logos/Washington-Redskins.png": "WAS",  # Corrected
#     "https://cdn.fastassets.io/images/team-logos/New-York-Giants.png": "NYG",
#     "https://cdn.fastassets.io/images/team-logos/Kansas-City-Chiefs.png": "KC",
#     "https://s.yimg.com/cv/apiv2/default/nfl/20200908/500x500/raiders_wbg.png": "LVR",  # Corrected
#     "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lac.png": "LAC",  # Corrected
#     "https://cdn.fastassets.io/images/team-logos/Buffalo-Bills.png": "BUF",
#     "https://cdn.fastassets.io/images/team-logos/Miami-Dolphins.png": "MIA",
#     "https://cdn.fastassets.io/images/team-logos/New-York-Jets.png": "NYJ",
#     "https://cdn.fastassets.io/images/team-logos/New-England-Patriots.png": "NE",
#     "https://cdn.fastassets.io/images/team-logos/Cleveland-Browns.png": "CLE",
#     "https://cdn.fastassets.io/images/team-logos/Baltimore-Ravens.png": "BAL",
#     "https://cdn.fastassets.io/images/team-logos/Detroit-Lions.png": "DET",
#     "https://cdn.fastassets.io/images/team-logos/Tennessee-Titans.png": "TEN"
# }

# # Download each logo and save it with the abbreviation as the file name
# for url, abbreviation in team_logos.items():
#     try:
#         img_data = requests.get(url).content  # Download the image content
#         with open(f'images/{abbreviation}.png', 'wb') as handler:
#             handler.write(img_data)  # Save the image to the file
#         print(f"Downloaded {abbreviation}.png")
#     except Exception as e:
#         print(f"Failed to download {abbreviation}: {e}")

# print("All images have been downloaded.")
import os
import requests

# List of team abbreviations
teams = [
    'crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den',
    'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia',
    'min', 'nwe', 'nor', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam',
    'oti', 'was'
]

# Base URL for the team logos
base_url = "https://cdn.ssref.net/req/202409272/tlogo/pfr/"

# Directory to save the images
save_dir = "images/team-logos"
os.makedirs(save_dir, exist_ok=True)  # Create the directory if it doesn't exist

# Function to download an image
def download_image(team):
    url = f"{base_url}{team}.png"
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(save_dir, f"{team}.png"), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {team}.png")
    else:
        print(f"Failed to download: {team}.png")

# Download all team logos
for team in teams:
    download_image(team)

print("All team logos downloaded successfully.")




# Downloading player headshots

import os
import pandas as pd
import requests

# Load the player_stats data from your file in the 'data/' directory
df_player_stats = pd.read_csv('data/player_stats.csv')

# Filter out QBs with valid headshot URLs and remove duplicates based on player_display_name
# unique_qbs_with_urls = df_player_stats[(df_player_stats['position'] == 'QB') & df_player_stats['headshot_url'].notna()] \
unique_qbs_with_urls = df_player_stats[df_player_stats['headshot_url'].notna()] \
                        .drop_duplicates(subset=['player_display_name'])

# Set up the directory to save images
image_folder = 'images'
os.makedirs(image_folder, exist_ok=True)

# Initialize a counter for downloaded images
downloaded_count = 0
total_qbs = len(unique_qbs_with_urls)

# Iterate through the unique QBs and download their headshots
for index, row in unique_qbs_with_urls.iterrows():
    player_name = row['player_display_name'].lower().replace(' ', '_')
    headshot_url = row['headshot_url']
    image_path = os.path.join(image_folder, f"{player_name}.png")
    
    # Download the image and save it
    try:
        response = requests.get(headshot_url)
        if response.status_code == 200:
            with open(image_path, 'wb') as file:
                file.write(response.content)
            downloaded_count += 1
            print(f"Downloaded {player_name}'s headshot ({downloaded_count}/{total_qbs}).")
        else:
            print(f"Failed to download {player_name}'s headshot (Status code: {response.status_code}).")
    except Exception as e:
        print(f"Error downloading {player_name}'s headshot: {e}")

# Print final result
print(f"Download complete: {downloaded_count}/{total_qbs} images successfully downloaded.")
