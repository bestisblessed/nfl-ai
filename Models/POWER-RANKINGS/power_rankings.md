# Current Model

1. Based on all regular season games from last 3 seasons
    ```python
    # Filter for last 3 seasons
    last_3_seasons = sorted(nfl_data['season'].unique())[-3:]
    nfl_data = nfl_data[nfl_data['season'].isin(last_3_seasons)]
    print(f"Data shape after filtering for last 3 seasons ({last_3_seasons}): {nfl_data.shape}")
    ```

2. No playoff games included
