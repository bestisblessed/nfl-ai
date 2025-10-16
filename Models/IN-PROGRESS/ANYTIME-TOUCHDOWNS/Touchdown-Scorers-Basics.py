#!/usr/bin/env python3
"""
NFL Touchdown Prediction Script
Converted from Touchdown-Scorers-Basics.ipynb
"""

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import warnings
from datetime import datetime
import os
import webbrowser
import glob

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

def find_latest_date_files():
    """Find the latest date files in the data directory"""
    data_dir = "./data"  # Use local data directory

    # File patterns to look for
    file_patterns = {
        'teams': 'Teams_*.csv',
        'games': 'Games_*.csv',
        'rosters': 'Rosters_*.csv'
    }

    latest_files = {}

    for file_type, pattern in file_patterns.items():
        # Find all matching files
        files = glob.glob(os.path.join(data_dir, pattern))

        if not files:
            raise FileNotFoundError(f"No {file_type} files found in {data_dir}")

        # Extract dates and find the latest
        dates = []
        for file in files:
            filename = os.path.basename(file)
            # Extract date part (e.g., OCT_15_2025 from Teams_OCT_15_2025.csv)
            date_str = filename.replace(f'{file_type.capitalize()}_', '').replace('.csv', '')
            try:
                # Parse date (assuming format like OCT_15_2025)
                date_obj = datetime.strptime(date_str, '%b_%d_%Y')
                dates.append((date_obj, file))
            except ValueError:
                continue

        if not dates:
            raise ValueError(f"No valid date files found for {file_type}")

        # Sort by date and get the latest
        dates.sort(key=lambda x: x[0], reverse=True)
        latest_files[file_type] = dates[0][1]

    return latest_files

def probability_to_american_odds(probability):
    """Convert probability to American betting odds"""
    if probability <= 0:
        return "+99999"  # Very high positive odds for near-zero probability
    elif probability >= 1:
        return "-99999"  # Very high negative odds for certainty
    elif probability >= 0.5:
        # Favorite (negative odds)
        odds = -(probability / (1 - probability)) * 100
        return f"{odds:.0f}"
    else:
        # Underdog (positive odds)
        odds = ((1 - probability) / probability) * 100
        return f"+{odds:.0f}"

def export_predictions_to_csv(predictions, filename):
    """Export predictions to CSV file"""
    # Create DataFrame from predictions
    data = []
    for pred in predictions:
        # Get all model probabilities and odds
        model_probs = [
            ('XGB', pred['xgb_prob']),
            ('RF', pred['rf_prob']),
            ('LR', pred['lr_prob'])
        ]
        
        # Sort by probability to find highest and lowest
        model_probs.sort(key=lambda x: x[1], reverse=True)
        highest_prob_model = model_probs[0]  # Highest probability = lowest odds (biggest favorite)
        lowest_prob_model = model_probs[-1]  # Lowest probability = highest odds (biggest underdog)

        data.append({
            'Player': pred['player'],
            'Team': pred['team'],
            'Position': pred['position'],
            'Opponent': pred['opponent'],
            'Lowest_Probability': f"{highest_prob_model[1]:.1%}",
            'Lowest_Odds': probability_to_american_odds(highest_prob_model[1]),
            'Lowest_Model': highest_prob_model[0],
            'Highest_Probability': f"{lowest_prob_model[1]:.1%}",
            'Highest_Odds': probability_to_american_odds(lowest_prob_model[1]),
            'Highest_Model': lowest_prob_model[0],
            'XGB_Probability': f"{pred['xgb_prob']:.1%}",
            'XGB_Odds': probability_to_american_odds(pred['xgb_prob']),
            'RF_Probability': f"{pred['rf_prob']:.1%}",
            'RF_Odds': probability_to_american_odds(pred['rf_prob']),
            'LR_Probability': f"{pred['lr_prob']:.1%}",
            'LR_Odds': probability_to_american_odds(pred['lr_prob'])
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Highest_Probability', ascending=False, key=lambda x: x.str.rstrip('%').astype(float))
    df.to_csv(filename, index=False)
    return df

def export_predictions_to_html(predictions, filename, title="NFL Touchdown Predictions"):
    """Export predictions to HTML file with nice formatting"""
    
    # Track game order from original predictions (before probability sorting)
    game_order = []
    seen_games = set()
    for pred in predictions:  # Use original order, not sorted
        teams = sorted([pred['team'], pred['opponent']])
        game_key = f"{teams[0]} vs {teams[1]}"
        if game_key not in seen_games:
            game_order.append(game_key)
            seen_games.add(game_key)

    # Sort predictions by highest probability from any model
    sorted_predictions = sorted(predictions, key=lambda x: max(x['xgb_prob'], x['rf_prob'], x['lr_prob']), reverse=True)

    # Group by game (sort teams alphabetically to ensure consistent game keys)
    games = {}
    for pred in sorted_predictions:
        teams = sorted([pred['team'], pred['opponent']])
        game_key = f"{teams[0]} vs {teams[1]}"
        if game_key not in games:
            games[game_key] = []
        games[game_key].append(pred)
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .header {{ text-align: center; color: black; margin-bottom: 30px; }}
            .game-section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .game-title {{ color: black; font-size: 28px; font-weight: bold; margin-bottom: 15px; border-bottom: 2px solid black; padding-bottom: 10px; }}
            .teams-container {{ display: flex; gap: 20px; justify-content: space-between; }}
            .team-table {{ flex: 1; min-width: 0; }}
            .team-title {{ color: #3498db; font-size: 18px; font-weight: bold; margin: 10px 0; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th {{ background-color: #34495e; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .prob-high {{ color: #27ae60; font-weight: bold; }}
            .prob-medium {{ color: #f39c12; font-weight: bold; }}
            .prob-low {{ color: #7f8c8d; }}
            .summary {{ background: #ecf0f1; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .top-picks {{ background: #d5f4e6; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            @media (max-width: 768px) {{
                .teams-container {{ flex-direction: column; gap: 10px; }}
                .team-table {{ margin-bottom: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
    """
    
    # Add game sections (in order they appear in upcoming games)
    for game_name in game_order:
        game_predictions = games[game_name]
        # Split into teams
        teams = {}
        for pred in game_predictions:
            if pred['team'] not in teams:
                teams[pred['team']] = []
            teams[pred['team']].append(pred)
        
        html_content += f"""
        <div class="game-section">
            <div class="game-title">{game_name}</div>
            <div class="teams-container">
        """

        # Add each team's predictions as side-by-side tables
        for team_name, team_preds in teams.items():
            opponent = team_preds[0]['opponent']
            html_content += f"""
            <div class="team-table">
                <div class="team-title">{team_name}</div>
                <table>
                    <tr>
                        <th>Player</th>
                        <th>Position</th>
                        <th>Lowest Odds</th>
                        <th>Highest Odds</th>
                        <th>XGBoost</th>
                        <th>Random Forest</th>
                        <th>Logistic Regression</th>
                    </tr>
            """

            # Sort team predictions by highest probability from any model
            team_preds.sort(key=lambda x: max(x['xgb_prob'], x['rf_prob'], x['lr_prob']), reverse=True)

            for pred in team_preds:
                # Get highest and lowest probabilities
                model_probs = [pred['xgb_prob'], pred['rf_prob'], pred['lr_prob']]
                highest_prob = max(model_probs)  # Highest prob = lowest odds (biggest favorite)
                lowest_prob = min(model_probs)   # Lowest prob = highest odds (biggest underdog)

                prob_class = "prob-high" if highest_prob >= 0.25 else "prob-medium" if highest_prob >= 0.15 else "prob-low"

                html_content += f"""
                    <tr>
                        <td><strong>{pred['player']}</strong></td>
                        <td>{pred['position']}</td>
                        <td class="{prob_class}">{probability_to_american_odds(highest_prob)}</td>
                        <td class="{prob_class}">{probability_to_american_odds(lowest_prob)}</td>
                        <td>{probability_to_american_odds(pred['xgb_prob'])}</td>
                        <td>{probability_to_american_odds(pred['rf_prob'])}</td>
                        <td>{probability_to_american_odds(pred['lr_prob'])}</td>
                    </tr>
                """

            html_content += """
                </table>
            </div>
            """
        
        html_content += "</div>"
    
    # Add summary section
    html_content += f"""
        <div class="summary">
            <h2>Top Touchdown Candidates (All Games)</h2>
            <div class="top-picks">
                <h3>🏆 Best Bets (Highest Probability)</h3>
    """
    
    for i, pred in enumerate(sorted_predictions[:10]):
        html_content += f"""
                <p><strong>{i+1}. {pred['player']}</strong> ({pred['team']} {pred['position']}) vs {pred['opponent']}: 
                <span class="prob-high">{pred['avg_prob']:.1%} ({probability_to_american_odds(pred['avg_prob'])})</span></p>
        """
    
    # html_content += """
    #         </div>
            
    #         <div style="margin-top: 20px;">
    #             <h3>📊 Position Breakdown</h3>
    # """
    
    # # Position breakdown
    # positions = ['RB', 'WR', 'TE']
    # for pos in positions:
    #     pos_predictions = [p for p in sorted_predictions if p['position'] == pos]
    #     if pos_predictions:
    #         html_content += f"<p><strong>Top {pos}:</strong> "
    #         top_pos = pos_predictions[:3]
    #         pos_names = [f"{p['player']} ({p['avg_prob']:.1%})" for p in top_pos]
    #         html_content += ", ".join(pos_names) + "</p>"
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_content

def load_data():
    """Load data from CSV files in data/ directory"""
    print("Finding latest date files...")

    # Find latest date files
    latest_files = find_latest_date_files()

    print("Loading data from latest date files...")
    print(f"Teams file: {os.path.basename(latest_files['teams'])}")
    print(f"Games file: {os.path.basename(latest_files['games'])}")
    print(f"Rosters file: {os.path.basename(latest_files['rosters'])}")

    teams_df = pd.read_csv(latest_files['teams'])
    games_df = pd.read_csv(latest_files['games'])
    player_stats_df = pd.read_csv('data/all_passing_rushing_receiving.csv')
    rosters_df = pd.read_csv(latest_files['rosters'])

    # Save to data/ directory for compatibility
    teams_df.to_csv('data/Teams.csv', index=False)
    games_df.to_csv('data/Games.csv', index=False)
    player_stats_df.to_csv('data/PlayerStats.csv', index=False)
    rosters_df.to_csv('data/Rosters.csv', index=False)

    print("Data loaded successfully!")
    print(f"Player stats shape: {player_stats_df.shape}")
    print(f"Available columns: {list(player_stats_df.columns)}")

    return player_stats_df

def calculate_defense_strength(player_stats_df):
    """Calculate opponent defense strength"""
    print("\nCalculating defense strength...")
    
    # Calculate team defense stats using actual column names
    team_defense_stats = player_stats_df.groupby('opponent_team').agg({
        'rush_td': 'sum',
        'pass_td': 'sum', 
        'rec_td': 'sum',
        'rush_yds': 'sum',
        'rec_yds': 'sum'
    }).reset_index()
    
    # Calculate total touchdowns and yards allowed
    team_defense_stats['total_touchdowns_allowed'] = team_defense_stats['rush_td'] + team_defense_stats['pass_td'] + team_defense_stats['rec_td']
    team_defense_stats['total_yards_allowed'] = team_defense_stats['rush_yds'] + team_defense_stats['rec_yds']
    
    # Keep only needed columns and rename for consistency
    team_defense_stats = team_defense_stats[['opponent_team', 'total_touchdowns_allowed', 'total_yards_allowed']].rename(columns={'opponent_team': 'team_name'})
    
    # Assign weights to touchdowns and yards allowed
    weights = {
        'total_touchdowns_allowed': 0.5,
        'total_yards_allowed': 0.5
    }
    
    # Calculate a composite defensive strength index
    team_defense_stats['composite_defense_strength'] = (
        weights['total_touchdowns_allowed'] * team_defense_stats['total_touchdowns_allowed'] +
        weights['total_yards_allowed'] * team_defense_stats['total_yards_allowed']
    )
    
    # Normalize the composite score (min-max normalization)
    team_defense_stats['defense_strength'] = (
        (team_defense_stats['composite_defense_strength'] - team_defense_stats['composite_defense_strength'].min()) /
        (team_defense_stats['composite_defense_strength'].max() - team_defense_stats['composite_defense_strength'].min())
    )
    
    # Invert so that lower scores indicate stronger defenses
    team_defense_stats['defense_strength'] = 1 - team_defense_stats['defense_strength']
    
    # Save to CSV
    output_df = team_defense_stats[['team_name', 'defense_strength']]
    output_df.to_csv('data/defense_strength.csv', index=False)
    
    print(f"Defense strength calculated for {len(output_df)} teams")
    return output_df

def merge_defense_strength():
    """Merge opponent defense strength to PlayerStats"""
    print("\nMerging defense strength...")
    
    # Load the CSV files
    player_stats_df = pd.read_csv('data/PlayerStats.csv')
    defense_strength_df = pd.read_csv('data/defense_strength.csv')
    
    # Merge the player_stats_df with the defense strengths based on the opponent_team
    player_stats_df = player_stats_df.merge(
        defense_strength_df,
        how='left',
        left_on='opponent_team',
        right_on='team_name'
    )
    
    # Rename the defense strength column for clarity
    player_stats_df.rename(columns={'defense_strength': 'opponent_defense_strength'}, inplace=True)
    
    # Drop the extra column after merging
    player_stats_df.drop(columns=['team_name'], inplace=True)
    
    # Save the updated DataFrame back to a CSV file
    player_stats_df.to_csv('data/PlayerStats.csv', index=False)
    
    print("Defense strength merged successfully")
    return player_stats_df

def prepare_model_data():
    """Prepare data for model training"""
    print("\nPreparing model data...")
    
    # Load data and filter for skill positions
    df = pd.read_csv('data/PlayerStats.csv')
    df = df[df['position'].isin(['RB', 'WR', 'TE'])].copy()
    print(f"Loaded {len(df)} records for RB, WR, TE players")
    
    # Create target variable using actual column names
    df['scored_touchdown'] = ((df['rush_td'] > 0) | (df['rec_td'] > 0)).astype(int)
    
    # Select features using actual column names
    features = ['rush_att', 'rush_yds', 'rec', 'targets', 'rec_yds', 'opponent_defense_strength']
    X = df[features].fillna(0)  # Fill NaN values with 0
    
    # Replace infinite values and handle numerical issues
    X = X.replace([np.inf, -np.inf], 0)
    
    # Cap extreme values for each column individually
    for col in X.columns:
        upper_bound = X[col].quantile(0.99)
        X[col] = X[col].clip(lower=0, upper=upper_bound)
    
    y = df['scored_touchdown']

    print(f"Features: {features}")
    # print(f"Target distribution: {y.value_counts()}")
    # print(f"Touchdown rate: {y.mean():.3f}")

    return X, y, features

def train_xgboost_model(X, y):
    """Train XGBoost model"""
    print("\nTraining XGBoost model...")
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
    
    # Initialize and train the model
    xgb_model = xgb.XGBClassifier(
        eval_metric='logloss',
        max_depth=4,
        random_state=42
    )
    
    xgb_model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = xgb_model.predict(X_test)
    
    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    print(f"XGBoost Accuracy: {accuracy:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False)
    # print("\nFeature Importance:")
    # print(feature_importance)

    # Confusion Matrix
    # print("\nConfusion Matrix:")
    # print(confusion_matrix(y_test, y_pred))

    # Classification Report
    # print("\nClassification Report:")
    # print(classification_report(y_test, y_pred))
    
    return xgb_model

def train_random_forest_model(X, y):
    """Train Random Forest model"""
    print("\nTraining Random Forest model...")
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train the model
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = rf_model.predict(X_test)
    
    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Random Forest Accuracy: {accuracy:.4f}")
    
    return rf_model

def train_logistic_regression_model(X, y):
    """Train Logistic Regression model"""
    print("\nTraining Logistic Regression model...")
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale the features to prevent numerical issues
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Initialize and train the model with regularization
    logreg_model = LogisticRegression(random_state=42, C=1.0, max_iter=1000, solver='liblinear')
    logreg_model.fit(X_train_scaled, y_train)
    
    # Make predictions
    y_pred = logreg_model.predict(X_test_scaled)
    
    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Logistic Regression Accuracy: {accuracy:.4f}")
    
    # Store scaler for later use
    logreg_model.scaler = scaler
    
    return logreg_model

def get_player_recent_stats(player_name, team, position):
    """Get recent stats for a player to estimate upcoming performance"""
    df = pd.read_csv('data/PlayerStats.csv')
    
    # Find player stats (using fuzzy matching)
    player_stats = df[
        (df['team'] == team) & 
        (df['position'] == position) &
        (df['player'].str.contains(player_name.split()[-1], case=False, na=False))  # Match by last name
    ]
    
    if player_stats.empty:
        # Return default stats based on position
        if position == 'RB':
            return {'rush_att': 12, 'rush_yds': 60, 'rec': 2, 'targets': 3, 'rec_yds': 15}
        elif position == 'WR':
            return {'rush_att': 0, 'rush_yds': 0, 'rec': 4, 'targets': 7, 'rec_yds': 50}
        elif position == 'TE':
            return {'rush_att': 0, 'rush_yds': 0, 'rec': 3, 'targets': 5, 'rec_yds': 35}
    
    # Calculate recent averages (last 10 games or all available)
    recent_stats = player_stats.tail(10)
    
    return {
        'rush_att': recent_stats['rush_att'].mean(),
        'rush_yds': recent_stats['rush_yds'].mean(),
        'rec': recent_stats['rec'].mean(),
        'targets': recent_stats['targets'].mean(),
        'rec_yds': recent_stats['rec_yds'].mean()
    }

def predict_player_touchdown(models, player_name, team, position, opponent_team, defense_strength_df):
    """Predict touchdown probability for a specific player"""
    xgb_model, rf_model, logreg_model = models
    
    # Get opponent defense strength
    opponent_defense = defense_strength_df[defense_strength_df['team_name'] == opponent_team]
    if opponent_defense.empty:
        opponent_defense_strength = 0.5  # Default middle value
    else:
        opponent_defense_strength = opponent_defense.iloc[0]['defense_strength']
    
    # Get player's estimated stats
    player_stats = get_player_recent_stats(player_name, team, position)
    
    # Create prediction data
    player_data = {
        'rush_att': player_stats['rush_att'],
        'rush_yds': player_stats['rush_yds'],
        'rec': player_stats['rec'],
        'targets': player_stats['targets'],
        'rec_yds': player_stats['rec_yds'],
        'opponent_defense_strength': opponent_defense_strength
    }
    
    player_df = pd.DataFrame([player_data])
    
    # Clean the prediction data
    player_df = player_df.fillna(0)
    player_df = player_df.replace([np.inf, -np.inf], 0)
    player_df = player_df.clip(lower=0, upper=1000)  # Reasonable upper bounds
    
    # Get predictions from all models
    xgb_prob = xgb_model.predict_proba(player_df)[:, 1][0]
    rf_prob = rf_model.predict_proba(player_df)[:, 1][0]
    
    # Scale data for logistic regression
    player_df_scaled = logreg_model.scaler.transform(player_df)
    lr_prob = logreg_model.predict_proba(player_df_scaled)[:, 1][0]
    
    avg_prob = (xgb_prob + rf_prob + lr_prob) / 3
    
    return {
        'player': player_name,
        'team': team,
        'position': position,
        'opponent': opponent_team,
        'xgb_prob': xgb_prob,
        'rf_prob': rf_prob,
        'lr_prob': lr_prob,
        'avg_prob': avg_prob,
        'estimated_stats': player_stats,
        'opponent_defense_strength': opponent_defense_strength
    }

def predict_upcoming_games(models, num_games=2):
    """Predict touchdown probabilities for upcoming games"""
    print(f"\n=== Predicting First {num_games} Upcoming Games ===")
    
    # Load upcoming games
    upcoming_games = pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv')

    # Use latest rosters file
    latest_files = find_latest_date_files()
    rosters_df = pd.read_csv(latest_files['rosters'])
    print(f"Using rosters file: {os.path.basename(latest_files['rosters'])}")

    defense_strength_df = pd.read_csv('data/defense_strength.csv')
    
    games_to_predict = upcoming_games.head(num_games)
    
    all_predictions = []
    
    for idx, game in games_to_predict.iterrows():
        away_team = game['away_team']
        home_team = game['home_team']
        
        print(f"\n--- Game {idx+1}: {away_team} @ {home_team} ---")
        
        # Get only active roster skill position players for both teams
        for team in [away_team, home_team]:
            team_players = rosters_df[
                (rosters_df['team'] == team) & 
                (rosters_df['position'].isin(['RB', 'WR', 'TE'])) &
                (rosters_df['status'] == 'ACT')  # Only active players
            ]
            
            opponent = home_team if team == away_team else away_team
            
            print(f"\n{team} players vs {opponent}:")
            
            team_predictions = []
            for _, player in team_players.iterrows():
                prediction = predict_player_touchdown(
                    models, 
                    player['full_name'], 
                    team, 
                    player['position'], 
                    opponent, 
                    defense_strength_df
                )
                
                all_predictions.append(prediction)
                team_predictions.append(prediction)
            
            # Sort team predictions by probability and display all
            team_predictions.sort(key=lambda x: x['avg_prob'], reverse=True)
            for prediction in team_predictions:
                avg_odds = probability_to_american_odds(prediction['avg_prob'])
                xgb_odds = probability_to_american_odds(prediction['xgb_prob'])
                rf_odds = probability_to_american_odds(prediction['rf_prob'])
                lr_odds = probability_to_american_odds(prediction['lr_prob'])
                
                print(f"  {prediction['player']} ({prediction['position']}): {prediction['avg_prob']:.1%} ({avg_odds}) "
                      f"[XGB: {prediction['xgb_prob']:.1%} ({xgb_odds}), RF: {prediction['rf_prob']:.1%} ({rf_odds}), LR: {prediction['lr_prob']:.1%} ({lr_odds})]")
    
    return all_predictions

def main():
    """Main function to run the complete pipeline"""
    print("=== NFL Touchdown Prediction Script ===")
    
    # Step 1: Load data
    player_stats_df = load_data()
    
    # Step 2: Calculate defense strength
    defense_strength_df = calculate_defense_strength(player_stats_df)
    
    # Step 3: Merge defense strength
    merged_df = merge_defense_strength()
    
    # Step 4: Prepare model data
    X, y, features = prepare_model_data()
    
    # Step 5: Train models
    xgb_model = train_xgboost_model(X, y)
    rf_model = train_random_forest_model(X, y)
    logreg_model = train_logistic_regression_model(X, y)
    
    # Step 6: Predict upcoming games
    models = (xgb_model, rf_model, logreg_model)
    predictions = predict_upcoming_games(models, num_games=2)
    
    # Step 7: Summary
    print(f"\n=== Summary ===")
    print(f"Predicted touchdown probabilities for {len(predictions)} players across 2 games")
    
    # Show all predictions sorted by probability
    sorted_predictions = sorted(predictions, key=lambda x: x['avg_prob'], reverse=True)
    print(f"\nAll touchdown candidates (sorted by probability):")
    for i, pred in enumerate(sorted_predictions):
        odds = probability_to_american_odds(pred['avg_prob'])
        print(f"{i+1:2d}. {pred['player']} ({pred['team']} {pred['position']}): {pred['avg_prob']:.1%} ({odds})")
    
    # Show breakdown by position
    print(f"\n=== Breakdown by Position ===")
    positions = ['RB', 'WR', 'TE']
    for pos in positions:
        pos_predictions = [p for p in sorted_predictions if p['position'] == pos]
        if pos_predictions:
            print(f"\nTop {pos}s:")
            for i, pred in enumerate(pos_predictions[:5]):  # Top 5 per position
                odds = probability_to_american_odds(pred['avg_prob'])
                print(f"  {i+1}. {pred['player']} ({pred['team']}): {pred['avg_prob']:.1%} ({odds})")
    
    # Step 8: Export reports
    print(f"\n=== Exporting Reports ===")
    
    # Create reports directory if it doesn't exist
    reports_dir = "data/projections"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export to CSV
    csv_filename = f"{reports_dir}/touchdown_predictions_{timestamp}.csv"
    csv_df = export_predictions_to_csv(predictions, csv_filename)
    print(f"✅ CSV report exported: {csv_filename}")
    
    # Export to HTML
    html_filename = f"{reports_dir}/touchdown_predictions_{timestamp}.html"
    export_predictions_to_html(predictions, html_filename, "NFL Touchdown Predictions Report")
    print(f"✅ HTML report exported: {html_filename}")

    # Open HTML file in browser
    try:
        webbrowser.open(f"file://{os.path.abspath(html_filename)}")
        print(f"🌐 Opened {html_filename} in your default browser")
    except Exception as e:
        print(f"⚠️  Could not open HTML file automatically: {e}")
        print(f"📊 Open {html_filename} in your browser for a formatted view")

    # Export summary CSV with just top candidates
    top_predictions = sorted_predictions[:20]  # Top 20 players
    summary_csv_filename = f"{reports_dir}/top_touchdown_candidates_{timestamp}.csv"
    export_predictions_to_csv(top_predictions, summary_csv_filename)
    print(f"✅ Top 20 summary CSV exported: {summary_csv_filename}")

    print(f"\n📁 All reports saved in '{reports_dir}/' directory")

    print("\n=== Script completed successfully! ===")

if __name__ == "__main__":
    main()
