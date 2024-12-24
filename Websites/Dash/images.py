import os
import requests

# Create a directory to store images
os.makedirs('images', exist_ok=True)

# List of URLs for team logos and their corresponding abbreviations
team_logos = {
    "https://cdn.fastassets.io/images/team-logos/New-Orleans-Saints.png": "NO",
    "https://cdn.fastassets.io/images/team-logos/Atlanta-Falcons.png": "ATL",
    "https://cdn.fastassets.io/images/team-logos/Pittsburgh-Steelers.png": "PIT",
    "https://cdn.fastassets.io/images/team-logos/Indianapolis-Colts.png": "IND",
    "https://cdn.fastassets.io/images/team-logos/Jacksonville-Jaguars.png": "JAX",
    "https://cdn.fastassets.io/images/team-logos/Houston-Texans.png": "HOU",
    "https://cdn.fastassets.io/images/team-logos/Minnesota-Vikings.png": "MIN",
    "https://cdn.fastassets.io/images/team-logos/Green-Bay-Packers.png": "GB",
    "https://cdn.fastassets.io/images/team-logos/Cincinnati-Bengals.png": "CIN",
    "https://cdn.fastassets.io/images/team-logos/Carolina-Panthers.png": "CAR",
    "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lar.png": "LAR",  # Corrected
    "https://cdn.fastassets.io/images/team-logos/Chicago-Bears.png": "CHI",
    "https://cdn.fastassets.io/images/team-logos/Denver-Broncos.png": "DEN",
    "https://cdn.fastassets.io/images/team-logos/Tampa-Bay-Buccaneers.png": "TB",
    "https://cdn.fastassets.io/images/team-logos/Seattle-Seahawks.png": "SEA",
    "https://cdn.fastassets.io/images/team-logos/San-Francisco-49ers.png": "SF",
    "https://cdn.fastassets.io/images/team-logos/Arizona-Cardinals.png": "ARI",
    "https://cdn.fastassets.io/images/team-logos/Dallas-Cowboys.png": "DAL",
    "https://cdn.fastassets.io/images/team-logos/Philadelphia-Eagles.png": "PHI",
    "https://cdn.fastassets.io/images/team-logos/Washington-Redskins.png": "WAS",  # Corrected
    "https://cdn.fastassets.io/images/team-logos/New-York-Giants.png": "NYG",
    "https://cdn.fastassets.io/images/team-logos/Kansas-City-Chiefs.png": "KC",
    "https://s.yimg.com/cv/apiv2/default/nfl/20200908/500x500/raiders_wbg.png": "LVR",  # Corrected
    "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lac.png": "LAC",  # Corrected
    "https://cdn.fastassets.io/images/team-logos/Buffalo-Bills.png": "BUF",
    "https://cdn.fastassets.io/images/team-logos/Miami-Dolphins.png": "MIA",
    "https://cdn.fastassets.io/images/team-logos/New-York-Jets.png": "NYJ",
    "https://cdn.fastassets.io/images/team-logos/New-England-Patriots.png": "NE",
    "https://cdn.fastassets.io/images/team-logos/Cleveland-Browns.png": "CLE",
    "https://cdn.fastassets.io/images/team-logos/Baltimore-Ravens.png": "BAL",
    "https://cdn.fastassets.io/images/team-logos/Detroit-Lions.png": "DET",
    "https://cdn.fastassets.io/images/team-logos/Tennessee-Titans.png": "TEN"
}

# Download each logo and save it with the abbreviation as the file name
for url, abbreviation in team_logos.items():
    try:
        img_data = requests.get(url).content  # Download the image content
        with open(f'images/{abbreviation}.png', 'wb') as handler:
            handler.write(img_data)  # Save the image to the file
        print(f"Downloaded {abbreviation}.png")
    except Exception as e:
        print(f"Failed to download {abbreviation}: {e}")

print("All images have been downloaded.")
