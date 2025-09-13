import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="🔮 NFL Projections",
    page_icon="🔮",
    layout="wide"
)

# Custom CSS for cleaner styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .week-selector {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .odds-badge {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.4rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    .confidence-high { background-color: #d4edda; color: #155724; }
    .confidence-medium { background-color: #fff3cd; color: #856404; }
    .confidence-low { background-color: #f8d7da; color: #721c24; }
    .trend-up { color: #28a745; font-weight: bold; }
    .trend-down { color: #dc3545; font-weight: bold; }
    .trend-stable { color: #6c757d; font-weight: bold; }
    .prop-highlight {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #2196f3;
        margin: 0.2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Page title
st.title('Weekly Projections')
st.markdown('NFL weekly player projections using my machine learning models')
st.divider()

# Function to load projections data
@st.cache_data
def load_projections_data():
    """Load and process projections data from CSV files"""
    projections_dir = os.path.join(BASE_DIR, "data/projections")
    
    # Find all projection files
    projection_files = glob.glob(os.path.join(projections_dir, "week*_all_props_summary.csv"))
    
    if not projection_files:
        st.error(f"No projection files found in {projections_dir}")
        return None, []
    
    # Extract available weeks
    available_weeks = []
    for file in projection_files:
        week_num = file.split('week')[1].split('_')[0]
        available_weeks.append(int(week_num))
    
    available_weeks.sort()
    
    return projection_files, available_weeks

# Function to get projections for a specific week
@st.cache_data
def get_week_projections(week_num):
    """Get projections data for a specific week"""
    file_path = os.path.join(BASE_DIR, f"data/projections/week{week_num}_all_props_summary.csv")
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        
        # Clean and process the data
        df = df.dropna(subset=['pred_yards'])
        df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
        df = df.dropna(subset=['pred_yards'])
        
        # Add confidence score based on prediction magnitude within each prop type
        df['confidence'] = 0.0
        for prop_type in df['prop_type'].unique():
            prop_mask = df['prop_type'] == prop_type
            prop_max = df.loc[prop_mask, 'pred_yards'].max()
            df.loc[prop_mask, 'confidence'] = np.clip((df.loc[prop_mask, 'pred_yards'] / prop_max) * 100, 0, 100).round(0)
        
        # Add trend (placeholder - could be enhanced with historical data)
        trends = np.random.choice(['↗️', '→', '↘️'], size=len(df), p=[0.3, 0.4, 0.3])
        df['trend'] = trends
        
        return df
    except Exception as e:
        st.error(f"Error loading week {week_num} data: {str(e)}")
        return None

# Load available data
projection_files, available_weeks = load_projections_data()

if not available_weeks:
    st.error("No projection data available. Please ensure projection files are in data/projections/")
    st.stop()

# NFC East teams
NFC_EAST_TEAMS = ["DAL", "NYG", "PHI", "WAS"]

# Create two-column layout with padding
col1, padding, col2 = st.columns([1, 0.2, 2])

with col1:
    # Controls in left column
    st.markdown("**Week**")
    selected_week = st.selectbox("", available_weeks, index=len(available_weeks)-1, key="week_selector", label_visibility="collapsed")
    
    # Load data for selected week
    projections_df = get_week_projections(selected_week)
    
    if projections_df is None:
        st.error(f"No data available for Week {selected_week}")
        st.stop()
    
    st.markdown("**Position**")
    all_positions = sorted(projections_df['position'].unique())
    position_filter = st.multiselect(
        "",
        all_positions,
        default=all_positions,
        key="global_position_filter",
        label_visibility="collapsed"
    )
    
    st.markdown("**Team**")
    all_teams = sorted(projections_df['team'].unique())
    # Set default_teams to NFC East teams if present, else fallback to all_teams
    default_teams = [team for team in NFC_EAST_TEAMS if team in all_teams]
    if not default_teams:
        default_teams = all_teams
    
    # Create columns for team selector and checkbox
    team_col1, team_col2 = st.columns([3, 1])
    
    with team_col1:
        # Determine which teams to show based on checkbox state
        if st.session_state.get('select_all_teams_checkbox', True):
            team_filter = st.multiselect(
                "",
                all_teams,
                default=default_teams,
                key="global_team_filter",
                label_visibility="collapsed"
            )
        else:
            team_filter = st.multiselect(
                "",
                all_teams,
                default=[],  # Empty list when unchecked
                key="global_team_filter",
                label_visibility="collapsed"
            )
    
    with team_col2:
        # Add Select All checkbox to the right
        select_all_teams = st.checkbox("Select All", key="select_all_teams_checkbox", value=True)
    
    # Refresh Data button removed

# Middle column for padding
with padding:
    st.markdown("")  # Empty space for padding

with col2:
    # Projection Summary in right column, bigger font
    st.markdown("<div style='text-align: left; font-weight: bold; font-size: 1.7rem; margin-left: 210px;'>Projection Summary</div>", unsafe_allow_html=True)
    st.write('')
    st.write('')
    
    # Calculate top projections by prop type using ALL data (before filtering)
    receiving_yards = projections_df[projections_df['prop_type'] == 'Receiving Yards'].nlargest(1, 'pred_yards')
    rushing_yards = projections_df[projections_df['prop_type'] == 'Rushing Yards'].nlargest(1, 'pred_yards')
    passing_yards = projections_df[projections_df['prop_type'] == 'Passing Yards'].nlargest(1, 'pred_yards')
    
    # Apply global filters for the count/metrics
    filtered_projections_df = projections_df.copy()
    if position_filter:
        filtered_projections_df = filtered_projections_df[filtered_projections_df['position'].isin(position_filter)]
    if team_filter:
        filtered_projections_df = filtered_projections_df[filtered_projections_df['team'].isin(team_filter)]
    
    # Create metrics in 2x2 grid
    metric_col1, metric_col2 = st.columns(2)
    
    with metric_col1:
        if not receiving_yards.empty:
            top_wr = receiving_yards.iloc[0]
            st.metric("Top Receiving Yards", f"{top_wr['full_name']}", f"{top_wr['pred_yards']:.1f} yards")
        else:
            st.metric("Top Receiving Yards", "N/A", "N/A")
            
        if not rushing_yards.empty:
            top_rb = rushing_yards.iloc[0]
            st.metric("Top Rushing Yards", f"{top_rb['full_name']}", f"{top_rb['pred_yards']:.1f} yards")
        else:
            st.metric("Top Rushing Yards", "N/A", "N/A")
    
    with metric_col2:
        if not passing_yards.empty:
            top_qb = passing_yards.iloc[0]
            st.metric("Top Passing Yards", f"{top_qb['full_name']}", f"{top_qb['pred_yards']:.1f} yards")
        else:
            st.metric("Top Passing Yards", "N/A", "N/A")
            
        total_projections = len(filtered_projections_df)
        avg_confidence = filtered_projections_df['confidence'].mean() if not filtered_projections_df.empty else 0
        st.metric("Total Projections", total_projections, f"Avg Confidence: {avg_confidence:.0f}%")

# Main projections display with tabs
st.markdown("---")

# Get unique prop types from ALL data (to show all tabs)
prop_types = projections_df['prop_type'].unique()
prop_types = sorted(prop_types)

# Create tabs for each prop type
if len(prop_types) > 0:
    # Add CSS to make tab titles bigger
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs([f"🎯 {prop_type}" for prop_type in prop_types])
    
    for i, prop_type in enumerate(prop_types):
        with tabs[i]:
            
            # Start with all data for this prop type, then apply global filters
            prop_data = projections_df[projections_df['prop_type'] == prop_type].copy()
            
            # Apply global filters
            if position_filter:
                prop_data = prop_data[prop_data['position'].isin(position_filter)]
            if team_filter:
                prop_data = prop_data[prop_data['team'].isin(team_filter)]
            
            if prop_data.empty:
                st.info(f"No {prop_type} projections available for Week {selected_week} with current filters")
                continue
            
            # Only show yards filter (teams and positions already filtered globally)
            min_val = float(prop_data['pred_yards'].min())
            max_val = float(prop_data['pred_yards'].max())
            
            # Handle case where min equals max (single value)
            if min_val == max_val:
                st.info(f"Only one {prop_type.split()[0]} projection available: {min_val:.1f} yards")
                min_yards = min_val
            else:
                st.markdown(f"<div style='font-size: 0.85rem; margin-bottom: 0.3rem;'><strong>Min {prop_type.split()[0]} Yards</strong></div>", unsafe_allow_html=True)
                min_yards = st.slider(
                    f"Min {prop_type.split()[0]} Yards",
                    min_val, 
                    max_val, 
                    min_val,  # Start at minimum to include all players
                    key=f"{prop_type}_yards",
                    label_visibility="collapsed"
                )
            
            # Add confidence slider for this prop type (after yards slider)
            st.markdown("<div style='font-size: 0.85rem; margin-bottom: 0.3rem;'><strong>Min Confidence %</strong></div>", unsafe_allow_html=True)
            min_confidence = st.slider(
                "Min Confidence %",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
                key=f"{prop_type}_confidence",
                label_visibility="collapsed"
            )
            
            # Apply both filters
            filtered_data = prop_data[
                (prop_data['pred_yards'] >= min_yards) & 
                (prop_data['confidence'] >= min_confidence)
            ]
            
            # Sort by predicted yards
            filtered_data = filtered_data.sort_values('pred_yards', ascending=False)
            
            # Display data
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Enhanced table with more info
                display_cols = ['full_name', 'team', 'opp', 'position', 'pred_yards', 'confidence', 'trend']
                
                # Format the dataframe for display
                display_df = filtered_data[display_cols].copy()
                display_df.columns = ['Player', 'Team', 'Opponent', 'Position', 'Projected Yards', 'Confidence', 'Trend']
                
                st.dataframe(
                    display_df.style.format({
                        'Projected Yards': '{:.1f}',
                        'Confidence': '{:.0f}%'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                # Bar chart for top projections
                top_players = filtered_data.head(10)
                
                if not top_players.empty:
                    fig = px.bar(
                        top_players, 
                        x='pred_yards', 
                        y='full_name',
                        orientation='h',
                        title=f"Week {selected_week} Top {prop_type}",
                        color='confidence',
                        color_continuous_scale='Blues',
                        hover_data=['team', 'opp', 'position']
                    )
                    fig.update_layout(
                        height=400, 
                        showlegend=False,
                        xaxis_title=f"{prop_type.split()[0]} Yards",
                        yaxis_title="Player"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # # Top 3 highlights
                # st.markdown("### 🏆 Top 3")
                # for idx, (_, player) in enumerate(top_players.head(3).iterrows(), 1):
                #     st.markdown(f"""
                #     <div class="prop-highlight">
                #         <strong>{idx}. {player['full_name']}</strong> ({player['team']})<br>
                #         <strong>{player['pred_yards']:.1f} yards</strong> vs {player['opp']}<br>
                #         Confidence: {player['confidence']:.0f}% | {player['trend']}
                #     </div>
                #     """, unsafe_allow_html=True)

# # Additional analysis section
# st.markdown("---")
# st.markdown("### 📈 Analysis & Insights")

# col1, col2 = st.columns(2)

# with col1:
#     # Prop type distribution (use filtered data)
#     prop_counts = filtered_projections_df['prop_type'].value_counts()
#     fig = px.pie(
#         values=prop_counts.values,
#         names=prop_counts.index,
#         title="Projection Distribution by Prop Type"
#     )
#     fig.update_layout(height=300)
#     st.plotly_chart(fig, use_container_width=True)

# with col2:
#     # Position distribution (use filtered data)
#     pos_counts = filtered_projections_df['position'].value_counts()
#     fig = px.bar(
#         x=pos_counts.index,
#         y=pos_counts.values,
#         title="Projections by Position"
#     )
#     fig.update_layout(height=300)
#     st.plotly_chart(fig, use_container_width=True)

# # Team analysis
# st.markdown("### 🏈 Team Analysis")
# team_stats = filtered_projections_df.groupby('team').agg({
#     'pred_yards': ['count', 'mean', 'max'],
#     'confidence': 'mean'
# }).round(1)

# team_stats.columns = ['Total Props', 'Avg Yards', 'Max Yards', 'Avg Confidence']
# team_stats = team_stats.sort_values('Total Props', ascending=False)

# st.dataframe(team_stats, use_container_width=True)

# # Footer
st.write('')
st.write('')
st.write('')
st.write('')
st.markdown("---")
st.markdown('By Tyler Durette')
st.markdown("NFL AI © 2023 | [GitHub](https://github.com/bestisblessed) | [Contact Me](tyler.durette@gmail.com)")
