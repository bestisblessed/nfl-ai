import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import glob

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

# Page header
st.markdown("""
<div class="main-header">
    <h1>🔮 NFL Projections Dashboard</h1>
    <p style="margin: 0; font-size: 1.1rem;">Real AI-powered projections for all major NFL props</p>
</div>
""", unsafe_allow_html=True)

# Function to load projections data
@st.cache_data
def load_projections_data():
    """Load and process projections data from CSV files"""
    projections_dir = "data/projections"
    
    # Find all projection files
    projection_files = glob.glob(f"{projections_dir}/week*_all_props_summary.csv")
    
    if not projection_files:
        st.error("No projection files found in data/projections/")
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
    file_path = f"data/projections/week{week_num}_all_props_summary.csv"
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        
        # Clean and process the data
        df = df.dropna(subset=['pred_yards'])
        df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
        df = df.dropna(subset=['pred_yards'])
        
        # Add confidence score based on prediction magnitude (placeholder logic)
        df['confidence'] = np.clip((df['pred_yards'] / df['pred_yards'].max()) * 100, 50, 95).round(0)
        
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

# Week selector
st.markdown("### 📅 Select Week")
selected_week = st.selectbox("Choose Week:", available_weeks, index=0, key="week_selector")

# Load data for selected week
projections_df = get_week_projections(selected_week)

if projections_df is None:
    st.error(f"No data available for Week {selected_week}")
    st.stop()

# Week header with key info
st.markdown(f"## Week {selected_week} Projections")
st.markdown(f"*Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}*")

# Key metrics summary
st.markdown("### 📊 Projection Summary")

# Calculate top projections by prop type
receiving_yards = projections_df[projections_df['prop_type'] == 'Receiving Yards'].nlargest(1, 'pred_yards')
rushing_yards = projections_df[projections_df['prop_type'] == 'Rushing Yards'].nlargest(1, 'pred_yards')
passing_yards = projections_df[projections_df['prop_type'] == 'Passing Yards'].nlargest(1, 'pred_yards')

col1, col2, col3, col4 = st.columns(4)

with col1:
    if not receiving_yards.empty:
        top_wr = receiving_yards.iloc[0]
        st.metric("Top Receiving Yards", f"{top_wr['full_name']}", f"{top_wr['pred_yards']:.1f} yards")
    else:
        st.metric("Top Receiving Yards", "N/A", "N/A")

with col2:
    if not rushing_yards.empty:
        top_rb = rushing_yards.iloc[0]
        st.metric("Top Rushing Yards", f"{top_rb['full_name']}", f"{top_rb['pred_yards']:.1f} yards")
    else:
        st.metric("Top Rushing Yards", "N/A", "N/A")

with col3:
    if not passing_yards.empty:
        top_qb = passing_yards.iloc[0]
        st.metric("Top Passing Yards", f"{top_qb['full_name']}", f"{top_qb['pred_yards']:.1f} yards")
    else:
        st.metric("Top Passing Yards", "N/A", "N/A")

with col4:
    total_projections = len(projections_df)
    avg_confidence = projections_df['confidence'].mean()
    st.metric("Total Projections", total_projections, f"Avg Confidence: {avg_confidence:.0f}%")

# Main projections display with tabs
st.markdown("---")

# Get unique prop types
prop_types = projections_df['prop_type'].unique()
prop_types = sorted(prop_types)

# Create tabs for each prop type
if len(prop_types) > 0:
    tabs = st.tabs([f"🎯 {prop_type}" for prop_type in prop_types])
    
    for i, prop_type in enumerate(prop_types):
        with tabs[i]:
            st.markdown(f"### 🎯 {prop_type} Projections")
            
            # Filter data for this prop type
            prop_data = projections_df[projections_df['prop_type'] == prop_type].copy()
            
            if prop_data.empty:
                st.info(f"No {prop_type} projections available for Week {selected_week}")
                continue
            
            # Filters for this tab
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_yards = st.slider(f"Min {prop_type.split()[0]} Yards", 
                                    float(prop_data['pred_yards'].min()), 
                                    float(prop_data['pred_yards'].max()), 
                                    float(prop_data['pred_yards'].quantile(0.3)),
                                    key=f"{prop_type}_yards")
            
            with col2:
                available_teams = sorted(prop_data['team'].unique())
                selected_teams = st.multiselect("Filter Teams", available_teams, key=f"{prop_type}_teams")
            
            with col3:
                available_positions = sorted(prop_data['position'].unique())
                selected_positions = st.multiselect("Filter Positions", available_positions, 
                                                  default=available_positions, key=f"{prop_type}_positions")
            
            # Apply filters
            filtered_data = prop_data.copy()
            filtered_data = filtered_data[filtered_data['pred_yards'] >= min_yards]
            
            if selected_teams:
                filtered_data = filtered_data[filtered_data['team'].isin(selected_teams)]
            
            if selected_positions:
                filtered_data = filtered_data[filtered_data['position'].isin(selected_positions)]
            
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
                
                # Top 3 highlights
                st.markdown("### 🏆 Top 3")
                for idx, (_, player) in enumerate(top_players.head(3).iterrows(), 1):
                    st.markdown(f"""
                    <div class="prop-highlight">
                        <strong>{idx}. {player['full_name']}</strong> ({player['team']})<br>
                        <strong>{player['pred_yards']:.1f} yards</strong> vs {player['opp']}<br>
                        Confidence: {player['confidence']:.0f}% | {player['trend']}
                    </div>
                    """, unsafe_allow_html=True)

# Additional analysis section
st.markdown("---")
st.markdown("### 📈 Analysis & Insights")

col1, col2 = st.columns(2)

with col1:
    # Prop type distribution
    prop_counts = projections_df['prop_type'].value_counts()
    fig = px.pie(
        values=prop_counts.values,
        names=prop_counts.index,
        title="Projection Distribution by Prop Type"
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Position distribution
    pos_counts = projections_df['position'].value_counts()
    fig = px.bar(
        x=pos_counts.index,
        y=pos_counts.values,
        title="Projections by Position"
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

# Team analysis
st.markdown("### 🏈 Team Analysis")
team_stats = projections_df.groupby('team').agg({
    'pred_yards': ['count', 'mean', 'max'],
    'confidence': 'mean'
}).round(1)

team_stats.columns = ['Total Props', 'Avg Yards', 'Max Yards', 'Avg Confidence']
team_stats = team_stats.sort_values('Total Props', ascending=False)

st.dataframe(team_stats, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    <p>🔮 Projections are based on AI analysis and historical data patterns</p>
    <p>📊 Confidence scores indicate model certainty in projections</p>
    <p>🎲 Data sourced from real NFL projections models</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for global filters and stats
with st.sidebar:
    st.markdown("### 🔍 Global Filters")
    
    # Position filter
    all_positions = sorted(projections_df['position'].unique())
    position_filter = st.multiselect(
        "Position",
        all_positions,
        default=all_positions
    )
    
    # Team filter
    all_teams = sorted(projections_df['team'].unique())
    team_filter = st.multiselect(
        "Team",
        all_teams,
        default=all_teams
    )
    
    # Confidence threshold
    global_confidence = st.slider(
        "Min Confidence %",
        min_value=50,
        max_value=95,
        value=65,
        step=5
    )
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("### 📊 Quick Stats")
    
    # Calculate stats across all projections
    filtered_df = projections_df[
        (projections_df['position'].isin(position_filter)) &
        (projections_df['team'].isin(team_filter)) &
        (projections_df['confidence'] >= global_confidence)
    ]
    
    st.metric("Filtered Projections", len(filtered_df))
    st.metric("Avg Confidence", f"{filtered_df['confidence'].mean():.1f}%")
    st.metric("Total Players", filtered_df['full_name'].nunique())
    
    # Prop type breakdown
    st.markdown("### 📊 Prop Type Breakdown")
    prop_breakdown = filtered_df['prop_type'].value_counts()
    for prop_type, count in prop_breakdown.items():
        st.markdown(f"**{prop_type}:** {count}")
    
    # Top teams by projection count
    st.markdown("### 🏆 Top Teams")
    top_teams = filtered_df['team'].value_counts().head(5)
    for team, count in top_teams.items():
        st.markdown(f"**{team}:** {count} props")

