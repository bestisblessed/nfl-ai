import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games'] 
df_playerstats = st.session_state['df_playerstats']

st.write('Coming soon..')
st.title('League Leaders')


### SACKS ###
st.header('Quarterback Sack Rankings')
#st.table(qb_sacked_ranked_2023)
#st.dataframe(qb_sacked_ranked_2023)

player_stats_df = pd.read_csv('./data/PlayerStats.csv')
qb_2023_stats = player_stats_df[(player_stats_df['position'] == 'QB') & (player_stats_df['season'] == 2023)]
qb_sacked_2023 = qb_2023_stats.groupby('player_display_name')['sacks'].sum().reset_index()
qb_sacked_ranked_2023 = qb_sacked_2023.sort_values(by='sacks')
#qb_sacked_ranked_2023 = qb_sacked_2023.sort_values(by='sacks', ascending=False)
#print(qb_sacked_ranked_2023)

plt.figure(figsize=(12, len(qb_sacked_ranked_2023) / 2))  # Adjust the divisor to scale for the number of QBs
bars = plt.barh(qb_sacked_ranked_2023['player_display_name'], qb_sacked_ranked_2023['sacks'], color='skyblue')
plt.xlabel('Number of Sacks', fontsize=32)
plt.ylabel('Quarterbacks', fontsize=32)
plt.title('Number of Sacks for NFL Quarterbacks in 2023', fontsize=16)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

# Add numbers to end of bars
# for index, value in enumerate(qb_sacked_ranked_2023['sacks']):
#     plt.text(value, index, str(value))
plt.bar_label(bars)

# Display the plot within Streamlit
st.pyplot(plt)
#st.bar_chart(plt)



### INTERCEPTIONS ###
st.header('Quarterback Interception Rankings')

qb_interceptions_stats = player_stats_df[(player_stats_df['position'] == 'QB') & (player_stats_df['season'] == 2023)]
qb_interceptions_2023 = qb_interceptions_stats.groupby('player_display_name')['interceptions'].sum().reset_index()
qb_interceptions_ranked_2023 = qb_interceptions_2023.sort_values(by='interceptions')
plt.figure(figsize=(12, len(qb_interceptions_ranked_2023) / 2))
bars = plt.barh(qb_interceptions_ranked_2023['player_display_name'], qb_interceptions_ranked_2023['interceptions'], color='salmon')
plt.xlabel('Number of Interceptions', fontsize=32)
plt.ylabel('Quarterbacks', fontsize=32)
plt.title('Number of Interceptions for NFL Quarterbacks in 2023', fontsize=16)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

# Add numbers to end of bars
# for index, value in enumerate(qb_interceptions_ranked_2023['interceptions']):
#     plt.text(value, index, str(value))
plt.bar_label(bars)

# Display the plot within Streamlit
st.pyplot(plt)







