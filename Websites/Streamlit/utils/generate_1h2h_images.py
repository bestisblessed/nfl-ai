import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Load data
teams = pd.read_csv('/workspace/Websites/Streamlit/data/Teams.csv')
games = pd.read_csv('/workspace/Websites/Streamlit/data/Games.csv')
box = pd.read_csv('/workspace/Websites/Streamlit/data/all_box_scores.csv')

# Prep boxscores
box['pfr'] = box['URL'].str.extract(r'/boxscores/([0-9a-z]+)\.htm')
for c in ['1','2','3','4']:
    box[c] = pd.to_numeric(box[c], errors='coerce').fillna(0)
box['first_half'] = box['1'] + box['2']
box['second_half'] = box['3'] + box['4']

images_dir = '/workspace/Websites/Streamlit/images'
os.makedirs(images_dir, exist_ok=True)

for season in [2024, 2025]:
    sel = games[(games['season'] == season) & (games['game_type'] == 'REG') & (games['week'].between(1, 18))]
    joined = box.merge(sel[['pfr','season']], on='pfr', how='inner')
    joined = joined.merge(teams[['TeamID','Team']], on='Team', how='left')

    team_halves = joined.groupby('TeamID')[['first_half','second_half']].mean().round(2).reset_index()
    team_halves['diff_2H_minus_1H'] = (team_halves['second_half'] - team_halves['first_half']).round(2)

    # Figure 1: diff barh
    fig1, ax1 = plt.subplots(figsize=(10, 12))
    ordered = team_halves.sort_values('diff_2H_minus_1H', ascending=True)
    ax1.barh(ordered['TeamID'], ordered['diff_2H_minus_1H'], color=['#2ecc71' if v > 0 else '#e74c3c' for v in ordered['diff_2H_minus_1H']])
    ax1.axvline(0, color='#7f8c8d', linewidth=1)
    ax1.set_xlabel('2H - 1H (points)')
    ax1.set_ylabel('Team')
    ax1.set_title(f'Average 2H minus 1H Points by Team ({season})')
    fig1.tight_layout()
    fig1.savefig(os.path.join(images_dir, f'1h_vs_2h_diff_{season}.png'), dpi=150, bbox_inches='tight')
    plt.close(fig1)

    # Figure 2: scatter
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    ax2.scatter(team_halves['first_half'], team_halves['second_half'], color='#3498db')
    mn = float(min(team_halves['first_half'].min(), team_halves['second_half'].min()))
    mx = float(max(team_halves['first_half'].max(), team_halves['second_half'].max()))
    ax2.plot([mn, mx], [mn, mx], linestyle='--', color='#e74c3c', linewidth=1)
    ax2.set_xlabel('Avg 1H Points')
    ax2.set_ylabel('Avg 2H Points')
    ax2.set_title(f'Avg 1H vs 2H Points by Team ({season})')
    ax2.grid(True, axis='both', linestyle='--', alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(os.path.join(images_dir, f'1h_vs_2h_scatter_{season}.png'), dpi=150, bbox_inches='tight')
    plt.close(fig2)

print('Generated 1H vs 2H images for 2024 and 2025.')
