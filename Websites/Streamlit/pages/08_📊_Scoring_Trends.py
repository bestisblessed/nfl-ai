import os
import pandas as pd
import streamlit as st

# <iframe src="https://claude.site/public/artifacts/1ca9aa13-a81f-491a-a1b3-459e08bc9948/embed" title="Claude Artifact" width="100%" height="600" frameborder="0" allow="clipboard-write" allowfullscreen></iframe>
    
    # /* Hide Streamlit default elements */
    # #MainMenu {visibility: hidden;}
    # footer {visibility: hidden;}
    # # header {visibility: hidden;}

    # /* Center Streamlit title */
    # h1 {
    #     text-align: center !important;
    # }

st.set_page_config(page_title="Touchdowns Allowed Per Position", layout="wide")
# st.set_page_config(page_title="NFL 2025 TDs Allowed")

# Create columns to control width (left margin, content, right margin)
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    st.title("Touchdowns Allowed Per Position")
    st.divider()
    st.write(' ')

st.markdown("""
<style>
    
    /* Title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    
    .subtitle {
        font-size: 1rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card styling for metrics */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e1e8ed;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-position {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #e74c3c;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .metric-worst {
        font-size: 0.8rem;
        color: #95a5a6;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 2rem 0 1rem 0;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e1e8ed;
    }
    
    /* Vulnerable teams styling */
    .vulnerable-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
        height: 200px;
        width: 100%;
        overflow: hidden;
    }
    
    .vulnerable-width {
        font-size: 1rem;
        font-weight: 700;
        color: #dc2626;
        text-align: center;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #f3f4f6;
    }
    
    .vulnerable-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0;
        border-bottom: 1px solid #f3f4f6;
        font-size: 0.9rem;
    }
    
    .vulnerable-item:last-child {
        border-bottom: none;
    }
    
    .vulnerable-team {
        font-weight: 600;
        color: #374151;
    }
    
    .vulnerable-tds {
        font-weight: 700;
        color: #dc2626;
    }
    
    /* Center the title */
    h1 {
        text-align: center !important;
    }
    
    /* Ensure proper centering and responsive behavior - only for main content */
    .main .block-container {
        text-align: center;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            max-width: 95%;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_csv(path_local: str) -> pd.DataFrame:
    if os.path.exists(path_local):
        return pd.read_csv(path_local)
    raise FileNotFoundError(f"Local file not found: {path_local}")

@st.cache_data(show_spinner=False)
def load():
    # Use relative paths like other pages
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_stats_path = os.path.join(current_dir, '../data', 'player_stats_pfr.csv')
    local_roster_path = os.path.join(current_dir, '../data', 'rosters', 'roster_2025.csv')
    
    stats = load_csv(local_stats_path)
    roster = load_csv(local_roster_path)
    return roster, stats

def build_position_lookup(roster: pd.DataFrame) -> dict:
    lut = {}
    for _, r in roster.iterrows():
        pid = str(r.get("pfr_id", "") or "")
        pos = r.get("position", None)
        if not pid or not pos:
            continue
        clean = pid.replace(".htm", "")
        lut[pid] = pos
        lut[clean] = pos
    return lut

def infer_pos(pid: str, lut: dict) -> str | None:
    if not pid:
        return None
    pid = str(pid)
    clean = pid.replace(".htm", "")
    pos = lut.get(pid) or lut.get(clean)
    if pos:
        return pos
    for k, v in lut.items():
        if clean in k or k in clean:
            return v
    return None

def compute(def_stats: pd.DataFrame, roster: pd.DataFrame, season_filter: str) -> pd.DataFrame:
    # Parse season filter
    if '-' in season_filter:
        # Range of seasons (e.g., "2023-2025")
        start_year, end_year = map(int, season_filter.split('-'))
        df = def_stats.loc[def_stats["season"].astype("Int64").between(start_year, end_year)].copy()
    else:
        # Single season
        year = int(season_filter)
        df = def_stats.loc[def_stats["season"].astype("Int64") == year].copy()
    
    lut = build_position_lookup(roster)
    df["position"] = df["player_id"].apply(lambda x: infer_pos(x, lut))
    df["rush_td"] = pd.to_numeric(df.get("rush_td", 0), errors="coerce").fillna(0)
    df["rec_td"]  = pd.to_numeric(df.get("rec_td", 0),  errors="coerce").fillna(0)
    df["total_td"] = df.apply(lambda r: r.rush_td if r.position=="QB" else r.rush_td + r.rec_td, axis=1)
    pos_map = {"QB":"QB", "RB":"RB", "FB":"RB", "WR":"WR", "TE":"TE"}
    df = df[(df["total_td"] > 0) & df["position"].notna() & df["opponent_team"].notna()].copy()
    df["pos_group"] = df["position"].map(pos_map)
    df = df[df["pos_group"].notna()].copy()
    df = df.sort_values(["game_id", "player_id"]).drop_duplicates(["game_id", "player_id"])
    pivot = (
        df.pivot_table(index="opponent_team",
                       columns="pos_group",
                       values="total_td",
                       aggfunc="sum",
                       fill_value=0)
          .reindex(columns=["QB","RB","WR","TE"], fill_value=0)
          .reset_index()
          .rename(columns={"opponent_team":"team"})
    )
    pivot["total"] = pivot[["QB","RB","WR","TE"]].sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False, kind="mergesort").reset_index(drop=True)
    pivot.index = pivot.index + 1  
    return pivot

# # Main title and subtitle
# st.markdown('<h1 class="main-title">NFL 2025: TDs Allowed by Defense</h1>', unsafe_allow_html=True)
# st.markdown('<p class="subtitle">Analyzing touchdowns allowed by position group • QB = rushing TDs only</p>', unsafe_allow_html=True)

# Load data and season selection in sidebar
with st.sidebar:
    with st.spinner("Loading data..."):
        roster, stats = load()
    
    st.markdown("### 📅 Season Selection")
    
    # Get available seasons from the data
    available_seasons = sorted(stats["season"].dropna().unique().astype(int))
    
    # Quick selection buttons
    st.markdown("**Quick Select:**")
    
    if st.button("2025", use_container_width=True):
        st.session_state.selected_season = "2025"
    if st.button("2024", use_container_width=True):
        st.session_state.selected_season = "2024"
    if st.button("2023", use_container_width=True):
        st.session_state.selected_season = "2023"
    if st.button("2022", use_container_width=True):
        st.session_state.selected_season = "2022"
    
    # if st.button("2023-2025", use_container_width=True):
    #     st.session_state.selected_season = "2023-2025"
    
    st.markdown("**Custom Range:**")
    
    # Custom range selection - default to 2025
    start_season = st.selectbox(
        "From:",
        options=available_seasons,
        index=available_seasons.index(2025) if 2025 in available_seasons else len(available_seasons)-1,
        key="start_season"
    )
    
    end_season = st.selectbox(
        "To:",
        options=available_seasons,
        index=available_seasons.index(2025) if 2025 in available_seasons else len(available_seasons)-1,
        key="end_season"
    )
    
    # Create season filter string from custom range
    if start_season == end_season:
        custom_season = str(start_season)
    else:
        custom_season = f"{start_season}-{end_season}"
    
    # Initialize session state for custom range
    if 'custom_range' not in st.session_state:
        st.session_state.custom_range = custom_season
    
    # Update custom range when dropdowns change
    if st.session_state.custom_range != custom_season:
        st.session_state.custom_range = custom_season
        # Clear quick select when custom range changes
        if 'selected_season' in st.session_state:
            del st.session_state.selected_season
    
    # Determine final selection
    if 'selected_season' in st.session_state:
        selected_season = st.session_state.selected_season
    else:
        selected_season = st.session_state.custom_range
    
    # Display selected range
    if '-' in selected_season:
        start, end = map(int, selected_season.split('-'))
        st.success(f"📊 **{start}-{end}** ({end - start + 1} seasons)")
    else:
        st.success(f"📊 **{selected_season}** season")
    
    st.markdown("---")

with col2:
    
    # Display dynamic title based on selected season
    if '-' in selected_season:
        st.markdown(f"### NFL {selected_season}: Touchdowns Allowed by Defense")
    else:
        st.markdown(f"### NFL {selected_season}: Touchdowns Allowed by Defense")
    
    table = compute(stats, roster, selected_season)

    # Summary cards section
    positions = ["QB","WR","TE","RB"]
    cols = st.columns(4)

    for i, pos in enumerate(positions):
        total_pos = int(table[pos].sum())
        worst_row = table.loc[table[pos].idxmax()]
        worst_team = worst_row['team']
        worst_value = int(worst_row[pos])
        
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-position">{pos}</div>
                <div class="metric-value">{total_pos}</div>
                <div class="metric-label">Total TDs</div>
                <div class="metric-worst">Worst: {worst_team} ({worst_value})</div>
            </div>
            """, unsafe_allow_html=True)

    # Defense rankings section
    # st.markdown('<h2 class="section-header">Defense Rankings</h2>', unsafe_allow_html=True)
    st.write('####')

    # Create styled table with rank column and format numbers as integers
    display_table = table[["team","QB","WR","TE","RB","total"]].copy()
    display_table = display_table.rename(columns={"QB": "QB (rushing)"})
    display_table.index = [f"#{i}" for i in display_table.index]
    
    # Convert all numeric columns to integers to remove decimals
    numeric_cols = ["QB (rushing)", "WR", "TE", "RB", "total"]
    for col in numeric_cols:
        display_table[col] = display_table[col].astype(int)

    # Style the dataframe with heatmap colors
    def style_heatmap(val):
        if isinstance(val, (int, float)) and val > 0:
            # Create pink/red gradient heatmap like the reference image
            intensity = min(val / 5, 1)  # Normalize to 0-1 scale
            # Use pink to red gradient
            red = 255  # Keep red at max
            green = int(245 - (195 * intensity))  # Start at light pink (245), go to red (50)
            blue = int(245 - (195 * intensity))   # Start at light pink (245), go to red (50)
            color = f"rgb({red}, {green}, {blue})"
            # Use white text for darker backgrounds, dark text for lighter backgrounds
            text_color = "white" if intensity > 0.4 else "#2c3e50"
            return f"background-color: {color}; color: {text_color}; font-weight: bold; text-align: center;"
        elif isinstance(val, (int, float)) and val == 0:
            return "background-color: #f8f9fa; color: #2c3e50; text-align: center;"
        else:
            return "text-align: center;"

    # Apply styling to numeric columns (excluding total)
    styled_table = display_table.style.map(style_heatmap, subset=["QB (rushing)", "WR", "TE", "RB"])
    styled_table = styled_table.map(lambda x: "font-weight: bold; color: #2c3e50;" if isinstance(x, (int, float)) else "", subset=["total"])

    st.dataframe(styled_table, use_container_width=True, height=600)

    # Most vulnerable by position section - 2x2 layout without nested columns
    st.write('####')
    
    # Create 2x2 layout directly at the main level
    positions = ["QB", "WR", "TE", "RB"]
    
    # Create two rows for 2x2 layout with minimal gaps
    row1_col1, row1_col2 = st.columns([1, 1], gap="small")
    row2_col1, row2_col2 = st.columns([1, 1], gap="small")

    # Define which column each position goes to
    position_columns = [
        (row1_col1, "QB"),  # Top-left
        (row1_col2, "WR"),  # Top-right
        (row2_col1, "TE"),  # Bottom-left
        (row2_col2, "RB")   # Bottom-right
    ]
    
    for col, pos in position_columns:
        with col:
            top5 = table.sort_values(pos, ascending=False).head(5)[["team",pos]]
            title = f"{pos} Most Vulnerable" if pos != "QB" else "QB Most Vulnerable"
        
            # Build the complete HTML for each card
            items_html = ""
            for idx, (_, row) in enumerate(top5.iterrows(), 1):
                team = row['team']
                tds = int(row[pos])
                items_html += f"""
                <div class="vulnerable-item">
                    <span class="vulnerable-team">{idx}. {team}</span>
                    <span class="vulnerable-tds">{tds} TDs</span>
                </div>
                """
            
            # Use st.components.v1.html for proper HTML rendering
            card_html = f"""
            <style>
                .vulnerable-card {{
                    background: white;
                    border-radius: 12px;
                    padding: 1.5rem;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    border: 1px solid #e5e7eb;
                    margin: 0.25rem;
                    min-height: 320px;
                    width: 100%;
                    box-sizing: border-box;
                }}
                .vulnerable-title {{
                    font-size: 1.2rem;
                    font-weight: 700;
                    color: #dc2626;
                    text-align: center;
                    margin-bottom: 1rem;
                    padding-bottom: 0.75rem;
                    border-bottom: 1px solid #f3f4f6;
                }}
                .vulnerable-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.6rem 0;
                    border-bottom: 1px solid #f3f4f6;
                    font-size: 1rem;
                }}
                .vulnerable-item:last-child {{
                    border-bottom: none;
                }}
                .vulnerable-team {{
                    font-weight: 600;
                    color: #374151;
                }}
                .vulnerable-tds {{
                    font-weight: 700;
                    color: #dc2626;
                }}
            </style>
            <div class="vulnerable-card">
                <div class="vulnerable-title">{title}</div>
                {items_html}
            </div>
            """
            
            st.components.v1.html(card_html, height=380)
