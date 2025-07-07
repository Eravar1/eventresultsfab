import streamlit as st
from main import scrape_round, process_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import sys 
from bs4 import BeautifulSoup
import requests
import streamlit.components.v1 as components

# ============== CONFIGURATION ==============
st.set_page_config(
    page_title="FaB Tournament Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== CACHING ==============
@st.cache_data(ttl=3600, show_spinner=False)
def cached_scrape(url, round_num):
    try:
        return scrape_round(url, round_num)
    except Exception as e:
        st.warning(f"Error in Round {round_num}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def cached_process(data):
    return process_data(data)

# ============== SESSION STATE ==============
if 'df' not in st.session_state:
    st.session_state.df = None
if 'multi_df' not in st.session_state:
    st.session_state.multi_df = []
if 'tournament_names' not in st.session_state:
    st.session_state.tournament_names = []

# ============== VISUALIZATIONS ==============
def plot_hero_performance(df):
    hero_stats = df['3_hero_stats'].sort_values('Win Rate (%)', ascending=False)
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Win Rate", "Play Rate"))
    
    fig.add_trace(
        go.Bar(
            x=hero_stats['Hero'],
            y=hero_stats['Win Rate (%)'],
            name="Win Rate",
            marker_color='#1f77b4'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=hero_stats['Hero'],
            y=hero_stats['Total Matches'],
            name="Play Rate",
            marker_color='#ff7f0e'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        margin=dict(l=50, r=50, b=100, t=50, pad=4)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# def plot_matchup_heatmap(df, key_suffix=""):
#     min_matches = st.slider(
#         "Minimum matches to display", 
#         min_value=1, 
#         max_value=20, 
#         value=5,
#         key=f"heatmap_slider_{key_suffix}"
#     )
    
#     filtered = df['4_hero_matchups'][
#         df['4_hero_matchups']['Total Matches'] >= min_matches
#     ]
    
#     heatmap_data = filtered.pivot_table(
#         values='Win Rate (%)',
#         index='Hero',
#         columns='Opponent Hero',
#         aggfunc='mean'
#     )
    
#     fig = go.Figure(data=go.Heatmap(
#         z=heatmap_data.values,
#         x=heatmap_data.columns,
#         y=heatmap_data.index,
#         colorscale='RdBu',
#         zmid=50,
#         text=heatmap_data.values.round(1),
#         hoverinfo="x+y+z"
#     ))
    
#     fig.update_layout(
#         height=800,
#         title="Hero Matchup Win Rates (%)",
#         xaxis_title="Opponent Hero",
#         yaxis_title="Hero",
#         margin=dict(l=100, r=50, b=150, t=50)
#     )
    
#     st.plotly_chart(fig, use_container_width=True)

# def plot_matchup_heatmap(df, key_suffix=""):
#     min_matches = st.slider(
#         "Minimum matches to display", 
#         min_value=1, 
#         max_value=20, 
#         value=5,
#         key=f"heatmap_slider_{key_suffix}"
#     )
    
#     filtered = df['4_hero_matchups'][
#         df['4_hero_matchups']['Total Matches'] >= min_matches
#     ]
    
#     heatmap_data = filtered.pivot_table(
#         values='Win Rate (%)',
#         index='Hero',
#         columns='Opponent Hero',
#         aggfunc='mean'
#     )
    
#     # Create a container that will allow horizontal scrolling
#     heatmap_container = st.container()
    
#     with heatmap_container:
#         # Calculate optimal figure size based on number of heroes
#         num_heroes = max(len(heatmap_data.index), len(heatmap_data.columns))
#         cell_size = 80  # pixels per cell
#         fig_width = max(800, num_heroes * cell_size)  # Minimum 800px width
#         fig_height = max(600, num_heroes * cell_size)  # Minimum 600px height
        
#         # Create the figure with dynamic sizing
#         fig = go.Figure(data=go.Heatmap(
#             z=heatmap_data.values,
#             x=heatmap_data.columns,
#             y=heatmap_data.index,
#             colorscale='RdBu',
#             zmid=50,
#             text=heatmap_data.values.round(1),
#             texttemplate="%{text}%",  # Show percentage sign
#             hoverinfo="x+y+z+text",
#             hoverongaps=False,
#             textfont={"size": 12, "color": "black"},
#             showscale=True
#         ))
        
#         # Update layout for better readability
#         fig.update_layout(
#             height=fig_height,
#             width=fig_width,
#             title="Hero Matchup Win Rates (%)",
#             xaxis_title="Opponent Hero",
#             yaxis_title="Hero",
#             margin=dict(l=100, r=50, b=150, t=50, pad=4),
#             xaxis=dict(
#                 tickangle=45,
#                 side="top",
#                 tickfont=dict(size=12)
#             ),
#             yaxis=dict(
#                 tickfont=dict(size=12)
#             )
#         )
        
#         # Configure the color scale
#         fig.update_traces(
#             colorbar=dict(
#                 title=dict(text="Win Rate %", side="right"),
#                 ticks="outside"
#             )
#         )
        
#         # Display the figure in a horizontally scrollable container
#         components.html(
#             f"""
#             <div style="width: 100%; overflow-x: auto;">
#                 {fig.to_html(full_html=False, include_plotlyjs='cdn')}
#             </div>
#             """,
#             height=fig_height + 100  # Add extra space for title/axes
#         )
    
#     # Show raw data in expander
#     with st.expander("View Matchup Data"):
#         st.dataframe(
#             filtered.sort_values('Win Rate (%)', ascending=False),
#             use_container_width=True,
#             height=400
#         )
def plot_matchup_heatmap(df, key_suffix=""):
    min_matches = st.slider(
        "Minimum matches to display", 
        min_value=1, 
        max_value=20, 
        value=5,
        key=f"heatmap_slider_{key_suffix}"
    )
    
    # Filter out blank/empty opponent heroes and matches below threshold
    filtered = df['4_hero_matchups'][
        (df['4_hero_matchups']['Total Matches'] >= min_matches) &
        (df['4_hero_matchups']['Opponent Hero'].notna()) &
        (df['4_hero_matchups']['Opponent Hero'] != '')
    ].copy()
    
    # Create pivot table
    heatmap_data = filtered.pivot_table(
        values='Win Rate (%)',
        index='Hero',
        columns='Opponent Hero',
        aggfunc='mean'
    )
    
    # Replace NaN with None (which will display as blank)
    heatmap_data = heatmap_data.where(pd.notna(heatmap_data))
    
    # Create a container that will allow horizontal scrolling
    heatmap_container = st.container()
    
    with heatmap_container:
        # Calculate optimal figure size based on number of heroes
        num_heroes = max(len(heatmap_data.index), len(heatmap_data.columns))
        cell_size = 80  # pixels per cell
        fig_width = max(800, num_heroes * cell_size)  # Minimum 800px width
        fig_height = max(600, num_heroes * cell_size)  # Minimum 600px height
        
        # Create the figure with dynamic sizing
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdBu',
            zmid=50,
            text=heatmap_data.values.round(1),
            texttemplate="%{text}%",
            textfont={"size": 12, "color": "black"},
            hoverinfo="x+y+z+text",
            hoverongaps=False,
            showscale=True,
            hovertext=[
                [f"{y} vs {x}: {z}%" if pd.notna(z) else f"{y} vs {x}: No data" 
                 for x, z in zip(heatmap_data.columns, row)]
                for y, row in zip(heatmap_data.index, heatmap_data.values)
            ]
        ))
        
        # Update layout for better readability
        fig.update_layout(
            height=fig_height,
            width=fig_width,
            title="Hero Matchup Win Rates (%)",
            xaxis_title="Opponent Hero",
            yaxis_title="Hero",
            margin=dict(l=100, r=50, b=150, t=50, pad=4),
            xaxis=dict(
                tickangle=45,
                side="top",
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                tickfont=dict(size=12)
            )
        )
        
        # Configure the color scale
        fig.update_traces(
            colorbar=dict(
                title=dict(text="Win Rate %", side="right"),
                ticks="outside"
            )
        )
        
        # Display the figure in a horizontally scrollable container
        components.html(
            f"""
            <div style="width: 100%; overflow-x: auto;">
                {fig.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>
            """,
            height=fig_height + 100  # Add extra space for title/axes
        )
    
    # Show raw data in expander
    with st.expander("View Matchup Data"):
        st.dataframe(
            filtered.sort_values('Win Rate (%)', ascending=False),
            use_container_width=True,
            height=400
        )


def plot_top8_conversion(data):
    """Handle both dictionary of DataFrames (aggregated) and single DataFrame (tournament)"""
    if isinstance(data, dict):
        # For aggregated data, we need to combine all tournament DataFrames
        if '6_top8_conversion' not in data:
            st.warning("No conversion rate data available")
            return
            
        df = data['6_top8_conversion']
    else:
        # For single tournament data
        df = data
    
    # Get the actual conversion rate column name
    conv_cols = [c for c in df.columns if 'Conversion Rate' in c]
    if not conv_cols:
        st.warning("No conversion rate data found in DataFrame")
        return
        
    conv_col = conv_cols[0]
    round_num = conv_col.split()[1]
    appear_col = f'Round {round_num} Appearances'
    
    st.subheader(f"Round {round_num} Conversion Rates")
    st.write(f"Percentage of each hero's total registrations that made it to Round {round_num}")
    
    top8_df = df.sort_values(conv_col, ascending=False)
    
    fig = px.bar(
        top8_df,
        x='Hero',
        y=conv_col,
        color='Total Registrations',
        hover_data=['Total Registrations', appear_col],
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="Hero",
        yaxis_title=f"Conversion Rate (%) - Round {round_num}",
        margin=dict(l=50, r=50, b=150, t=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("View Raw Data"):
        st.dataframe(top8_df, use_container_width=True)
                    
def plot_tournament_top8_comparison():
    """Plot comparison of conversion rates across tournaments, using each tournament's own round structure."""
    if len(st.session_state.multi_df) < 1:
        st.warning("Add at least 1 tournament to enable comparison")
        return
    
    # Combine top8 data from all tournaments
    all_top8 = []
    for df, name in zip(st.session_state.multi_df, st.session_state.tournament_names):
        if '6_top8_conversion' in df and not df['6_top8_conversion'].empty:
            tournament_df = df['6_top8_conversion'].copy()
            
            # Find the conversion rate column for this tournament
            conv_cols = [c for c in tournament_df.columns if 'Conversion Rate' in c]
            if not conv_cols:
                continue
            conv_col = conv_cols[0]
            
            # Standardize the column names for comparison
            tournament_df['Conversion Rate'] = tournament_df[conv_col]
            tournament_df['Tournament'] = name
            tournament_df['Target Round'] = tournament_df.get('Target Round', '?')
            
            all_top8.append(tournament_df)
    
    if not all_top8:
        st.warning("No conversion rate data available")
        return
    
    combined = pd.concat(all_top8)
    
    # Show which rounds were used for each tournament
    st.write("**Rounds used for conversion calculation:**")
    round_info = combined[['Tournament', 'Target Round']].drop_duplicates()
    st.dataframe(round_info, hide_index=True, use_container_width=True)
    
    # Filter heroes with minimum registrations across tournaments
    min_registrations = st.slider(
        "Minimum total registrations (across all tournaments) to include", 
        min_value=1, 
        max_value=50, 
        value=10
    )
    
    hero_totals = combined.groupby('Hero')['Total Registrations'].sum()
    valid_heroes = hero_totals[hero_totals >= min_registrations].index
    filtered = combined[combined['Hero'].isin(valid_heroes)]
    
    # Plot comparison
    st.subheader("Tournament-by-Tournament Conversion Rates")
    st.caption("Note: Each tournament uses its own 3rd-to-last round for conversion calculation")
    
    # Option 1: Faceted bar chart
    tab1, tab2, tab3 = st.tabs(["Faceted View", "Box Plot", "Line Chart"])
    
    with tab1:
        fig = px.bar(
            filtered.sort_values('Conversion Rate', ascending=False),
            x='Hero',
            y='Conversion Rate',
            color='Tournament',
            barmode='group',
            facet_col='Tournament',
            facet_col_wrap=3,
            height=800,
            title="Conversion Rates by Tournament"
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.box(
            filtered,
            x='Hero',
            y='Conversion Rate',
            color='Hero',
            points="all",
            hover_data=['Tournament', 'Total Registrations', 'Target Round'],
            title="Distribution of Conversion Rates by Hero"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.line(
            filtered,
            x='Tournament',
            y='Conversion Rate',
            color='Hero',
            markers=True,
            hover_data=['Total Registrations', 'Target Round'],
            title="Conversion Rate Trends Across Tournaments"
        )
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Show raw data
    with st.expander("View Raw Tournament-by-Tournament Data"):
        st.dataframe(
            filtered.sort_values(['Tournament', 'Conversion Rate'], ascending=[True, False]),
            use_container_width=True,
            height=400
        )
    
    return filtered

def plot_player_performance(df):
    player_stats = df['2_player_stats'].sort_values('Win Rate (%)', ascending=False).head(20)
    
    fig = px.bar(
        player_stats,
        x='Player',
        y='Win Rate (%)',
        color='Wins',
        hover_data=['Wins', 'Losses', 'Heroes Used'],
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        height=600,
        title="Top Players by Win Rate",
        xaxis_title="Player",
        yaxis_title="Win Rate (%)",
        margin=dict(l=50, r=50, b=150, t=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_multi_tournament_comparison():
    st.header("🏆 Multi-Tournament Comparison")
    
    if len(st.session_state.multi_df) < 2:
        st.warning("Add at least 2 tournaments to enable comparison")
        return
    
    # Combine hero stats from all tournaments
    combined = pd.concat([
        df['3_hero_stats'].assign(Tournament=name)
        for df, name in zip(st.session_state.multi_df, st.session_state.tournament_names)
    ])
    
    # Comparison metrics
    metric = st.selectbox(
        "Comparison Metric",
        ['Win Rate (%)', 'Total Matches', 'Wins'],
        key="multi_metric"
    )
    
    # Top heroes comparison
    top_n = st.slider("Number of top heroes to show", 5, 20, 10, key="top_n")
    
    fig = px.bar(
        combined.groupby(['Hero', 'Tournament'])[metric].mean().reset_index(),
        x='Hero',
        y=metric,
        color='Tournament',
        barmode='group',
        title=f"Top {top_n} Heroes by {metric} Across Tournaments"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap of hero appearances
    heatmap_data = combined.pivot_table(
        index='Hero',
        columns='Tournament',
        values=metric,
        aggfunc='mean'
    ).fillna(0)
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Tournament", y="Hero", color=metric),
        aspect="auto",
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_aggregated_analysis():
    st.header("📊 Aggregated Tournament Data")
    
    if len(st.session_state.multi_df) < 1:
        st.warning("Add at least 1 tournament to enable aggregation")
        return
    
    # Combine all match results
    all_matches = pd.concat([
        df['1_match_results'].assign(Tournament=name)
        for df, name in zip(st.session_state.multi_df, st.session_state.tournament_names)
    ])

        # Process the aggregated data
    with st.spinner("Processing aggregated data..."):
        aggregated_data = process_data(all_matches.to_dict('records'))
    
    # Combine all hero stats
    all_hero_stats = pd.concat([
        df['3_hero_stats'].assign(Tournament=name)
        for df, name in zip(st.session_state.multi_df, st.session_state.tournament_names)
    ])
    
    # Combine all player stats
    all_player_stats = pd.concat([
        df['2_player_stats'].assign(Tournament=name)
        for df, name in zip(st.session_state.multi_df, st.session_state.tournament_names)
    ])
    
    # Process the aggregated data
    with st.spinner("Processing aggregated data..."):
        aggregated_data = process_data(all_matches.to_dict('records'))
    
    # Show summary metrics
    total_matches = len(all_matches)
    unique_players = all_player_stats['Player'].nunique()
    unique_heroes = all_hero_stats['Hero'].nunique()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Matches", total_matches)
    with col2:
        st.metric("Unique Players", unique_players)
    with col3:
        st.metric("Unique Heroes", unique_heroes)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Hero Performance", "Matchups", "Player Stats", "Top 8 Conversion", "Tournament Comparison"])
    
    with tab1:
        plot_hero_performance(aggregated_data)
        with st.expander("View All Hero Stats"):
            st.dataframe(
                aggregated_data['3_hero_stats'].sort_values('Win Rate (%)', ascending=False),
                use_container_width=True,
                height=400
            )
    
    with tab2:
        plot_matchup_heatmap(aggregated_data, "aggregated")
        with st.expander("View All Matchups"):
            st.dataframe(
                aggregated_data['4_hero_matchups'],
                use_container_width=True,
                height=400
            )
    
    with tab3:
        plot_player_performance(aggregated_data)
        with st.expander("View All Player Stats"):
            st.dataframe(
                aggregated_data['2_player_stats'].sort_values('Win Rate (%)', ascending=False),
                use_container_width=True,
                height=400
            )
    with tab4:
        plot_top8_conversion(aggregated_data)

    with tab5:
        plot_tournament_top8_comparison()

# ============== CORE FUNCTIONS ==============
def analyze_tournament(url):
    with st.spinner(f"Scraping {url.split('/')[-3].replace('-',' ').title()}..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_rounds = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for round_num in range(1, 21):
                futures.append(executor.submit(cached_scrape, url, round_num))
            
            for i, future in enumerate(futures):
                progress_bar.progress((i + 1) / 20)
                status_text.text(f"Processing Round {i+1}/20")
                result = future.result()
                if result:
                    all_rounds.extend(result)
        
        progress_bar.empty()
        status_text.empty()
        
        if not all_rounds:
            st.error(f"No data found for {url}")
            return None
        
        tournament_name = url.split('/')[-3].replace('-', ' ').title()
        
        with st.spinner("Analyzing matches..."):
            return cached_process(all_rounds), tournament_name


@st.cache_data(ttl=3600)
def fetch_decklist(url):
    """Fetch and parse a decklist page with image URLs."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        def extract_cards(table_soup):
            cards = []
            for row in table_soup.find_all('tr')[1:]:
                link = row.find('a')
                if link:
                    card_text = link.get_text(strip=True)
                    normal_img = link['href']
                    large_img = link.find('span').find('img')['src'] if link.find('span') else normal_img
                    quantity = row.get_text(strip=True).split('x')[0].strip()
                    cards.append({
                        'text': card_text,
                        'quantity': quantity,
                        'normal_img': normal_img,
                        'large_img': large_img
                    })
            return cards
        
        # Extract hero/equipment
        hero_equip = []
        hero_table = soup.find('th', string='Hero / Weapon / Equipment')
        if hero_table:
            hero_equip = extract_cards(hero_table.find_parent('table'))
        
        # Extract cards by pitch value
        deck = {'Hero/Equipment': hero_equip}
        for pitch in ['0', '1', '2', '3']:
            pitch_table = soup.find('th', string=f'Pitch {pitch}')
            if pitch_table:
                deck[f'Pitch {pitch}'] = extract_cards(pitch_table.find_parent('table'))
        
        return deck
    except Exception as e:
        st.error(f"Error fetching decklist: {str(e)}")
        return None

def create_hoverable_card(card):
    """Generate HTML for a hoverable card with proper escaping."""
    img_id = card['large_img'].split('/')[-1].replace("'", "")
    return f"""
    <div style="position:relative; display:inline-block; margin:5px;">
        <a href="#" style="text-decoration:none; color:inherit;"
           onmouseover="document.getElementById('img-{img_id}').style.display='block'"
           onmouseout="document.getElementById('img-{img_id}').style.display='none'">
            {card['quantity']} x {card['text']}
        </a>
        <img id="img-{img_id}" 
             src="{card['large_img']}" 
             style="position:absolute; display:none; z-index:1000; 
                    width:250px; left:50%; transform:translateX(-50%);
                    border:2px solid #ddd; border-radius:5px; box-shadow:0 0 10px rgba(0,0,0,0.3);"/>
    </div>
    """

def display_decklist(deck):
    """Display a decklist with hoverable card images."""
    if not deck:
        st.warning("No decklist data available")
        return
    
    # Display Hero & Equipment
    st.subheader("Hero & Equipment")
    if deck.get('Hero/Equipment'):
        hero_html = "<div style='line-height:2.0;'>"
        for card in deck['Hero/Equipment']:
            hero_html += create_hoverable_card(card)
        hero_html += "</div>"
        components.html(hero_html, height=50*len(deck['Hero/Equipment']))
    else:
        st.write("No hero/equipment data")
    
    # Display cards by pitch value
    for pitch in ['0', '1', '2', '3']:
        pitch_key = f'Pitch {pitch}'
        if pitch_key in deck:
            st.subheader(f"Pitch {pitch} Cards")
            cards_html = "<div style='line-height:2.0;'>"
            for card in deck[pitch_key]:
                cards_html += create_hoverable_card(card)
            cards_html += "</div>"
            components.html(cards_html, height=50*len(deck[pitch_key]))


# ============== MAIN APP ==============
def main():

    st.markdown("""
    <script>
        function showCard(imgId) {
            document.getElementById(imgId).style.display = 'block';
        }
        function hideCard(imgId) {
            document.getElementById(imgId).style.display = 'none';
        }
    </script>
    <style>
        .hover-card { transition: all 0.3s ease; }
        .hover-card:hover { color: #4a8bfc; }
    </style>
    """, unsafe_allow_html=True)
        
    st.title("Flesh and Blood GG Tournament Analyzer")
    
    # ===== SIDEBAR CONTROLS =====
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Single Tournament Analysis
        st.subheader("Single Tournament")
        url = st.text_input(
            "Enter URL:",
            "https://fabtcg.com/en/coverage/calling-bologna-2025/results/",
            key="single_url"
        )
        
        if st.button("Analyze Tournament", key="analyze_single"):
            result = analyze_tournament(url)
            if result is not None:
                st.session_state.df = result[0]
                st.session_state.tournament_name = result[1]
                st.session_state.match_count = len(result[0]['1_match_results'])
                st.success("Analysis complete!")
        
        # Multi-Tournament Comparison
        default_values = """https://fabtcg.com/en/coverage/national-championship-2025-brunei/results/
https://fabtcg.com/en/coverage/national-championship-2025-canada/results/
https://fabtcg.com/en/coverage/national-championship-2025-denmark/results/
https://fabtcg.com/en/coverage/national-championship-2025-czechia/results/
https://fabtcg.com/en/coverage/national-championship-2025-germany-main-event/results/
https://fabtcg.com/en/coverage/national-championship-2025-iceland/results/
https://fabtcg.com/en/coverage/national-championship-2025-romania/results/
https://fabtcg.com/en/coverage/national-championship-2025-slovenia/results/
https://fabtcg.com/en/coverage/national-championship-2025-switzerland/results/
https://fabtcg.com/en/coverage/national-championship-2025-thailand/results/
https://fabtcg.com/en/coverage/national-championship-2025-taiwan/results/
https://fabtcg.com/en/coverage/national-championship-2025-australia/results/
https://fabtcg.com/en/coverage/national-championship-2025-austria/results/
https://fabtcg.com/en/coverage/national-championship-2025-estonia/results/
https://fabtcg.com/en/coverage/national-championship-2025-finland/results/
https://fabtcg.com/en/coverage/national-championship-2025-greece/results/
https://fabtcg.com/en/coverage/national-championship-2025-hungary/results/
https://fabtcg.com/en/coverage/national-championship-2025-hong-kong-region/results/
https://fabtcg.com/en/coverage/national-championship-2025-ireland/results/
https://fabtcg.com/en/coverage/national-championship-2025-italy/results/
https://fabtcg.com/en/coverage/national-championship-2025-japan/results/
https://fabtcg.com/en/coverage/national-championship-2025-latvia/results/
https://fabtcg.com/en/coverage/national-championship-2025-malaysia/results/
https://fabtcg.com/en/coverage/national-championship-2025-mexico/results/
https://fabtcg.com/en/coverage/national-championship-2025-norway/results/
https://fabtcg.com/en/coverage/national-championship-2025-philippines/results/
https://fabtcg.com/en/coverage/national-championship-2025-poland/results/
https://fabtcg.com/en/coverage/national-championship-2025-portugal/results/
https://fabtcg.com/en/coverage/national-championship-2025-south-korea/results/
https://fabtcg.com/en/coverage/national-championship-2025-spain/results/
https://fabtcg.com/en/coverage/national-championship-2025-sweden/results/"""
        st.subheader("Multi-Tournament")
        multi_urls = st.text_area(
            "Enter URLs (one per line):",
            value=default_values,
            height=100,
            key="multi_urls"
        )
        
        if st.button("Compare Tournaments", key="analyze_multi"):
            urls = [u.strip() for u in multi_urls.split('\n') if u.strip()]
            st.session_state.multi_df = []
            st.session_state.tournament_names = []
            
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            for i, url in enumerate(urls):
                progress_text.text(f"Processing {i+1}/{len(urls)}")
                progress_bar.progress((i + 1) / len(urls))
                
                result = analyze_tournament(url)
                if result:
                    st.session_state.multi_df.append(result[0])
                    st.session_state.tournament_names.append(result[1])
            
            progress_bar.empty()
            progress_text.empty()
            
            if len(st.session_state.multi_df) > 1:
                st.success(f"Loaded {len(st.session_state.multi_df)} tournaments!")
            else:
                st.warning("Need at least 2 tournaments for comparison")
        
        # Data Export
        st.subheader("💾 Data Export")
        if st.session_state.df:
            json_data = json.dumps(
                {k: v.to_dict(orient='records') for k, v in st.session_state.df.items()},
                indent=2
            )
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"fab_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                key="json_download"
            )

    # ===== MAIN CONTENT =====
    tab1, tab2, tab3, tab4 = st.tabs([
        "Single Tournament", 
        "Multi-Tournament Comparison",
        "Aggregated Analysis",
        "Decklists"
    ])

    with tab1:
        if st.session_state.df:
            st.header(f"📊 {st.session_state.tournament_name} Analysis")
            st.metric("Total Matches Analyzed", st.session_state.match_count)
            
            plot_hero_performance(st.session_state.df)
            
            with st.expander("Detailed Hero Stats"):
                st.dataframe(
                    st.session_state.df['3_hero_stats'].sort_values('Win Rate (%)', ascending=False),
                    use_container_width=True,
                    height=400
                )
            
            plot_matchup_heatmap(st.session_state.df, "single")
            
            plot_player_performance(st.session_state.df)
    
    with tab2:
        plot_multi_tournament_comparison()
        
        if len(st.session_state.multi_df) > 1:
            with st.expander("Raw Comparison Data"):
                combined = pd.concat([
                    df['3_hero_stats'].assign(Tournament=name)
                    for df, name in zip(st.session_state.multi_df, st.session_state.tournament_names)
                ])
                st.dataframe(combined, use_container_width=True, height=400)

    with tab3:
        plot_aggregated_analysis()

    with tab4:
        st.header("📚 Tournament Decklists")
        
        if not st.session_state.df and not st.session_state.multi_df:
            st.warning("Please analyze a tournament first")
        else:
            # Get all decklist data
            decklist_data = []
            
            # Single tournament data
            if st.session_state.df:
                df = st.session_state.df['1_match_results']
                tournament = st.session_state.tournament_name
                for _, row in df.iterrows():
                    if row['Player 1 Decklist']:
                        decklist_data.append({
                            'Player': row['Player 1 Name'],
                            'Hero': row['Player 1 Hero'],
                            'Decklist URL': row['Player 1 Decklist'],
                            'Tournament': tournament
                        })
                    if row['Player 2 Decklist']:
                        decklist_data.append({
                            'Player': row['Player 2 Name'],
                            'Hero': row['Player 2 Hero'],
                            'Decklist URL': row['Player 2 Decklist'],
                            'Tournament': tournament
                        })
            
            # Multi-tournament data
            for df, tournament in zip(st.session_state.multi_df, st.session_state.tournament_names):
                for _, row in df['1_match_results'].iterrows():
                    if row['Player 1 Decklist']:
                        decklist_data.append({
                            'Player': row['Player 1 Name'],
                            'Hero': row['Player 1 Hero'],
                            'Decklist URL': row['Player 1 Decklist'],
                            'Tournament': tournament
                        })
                    if row['Player 2 Decklist']:
                        decklist_data.append({
                            'Player': row['Player 2 Name'],
                            'Hero': row['Player 2 Hero'],
                            'Decklist URL': row['Player 2 Decklist'],
                            'Tournament': tournament
                        })
            
            if not decklist_data:
                st.warning("No decklist data available")
                return
            
            # Remove duplicates
            unique_decklists = {}
            for entry in decklist_data:
                key = (entry['Player'], entry['Hero'], entry['Decklist URL'])
                unique_decklists[key] = entry
            decklist_df = pd.DataFrame(unique_decklists.values())
            
            # Improved tournament filtering with search
            st.write("**Filter tournaments:**")
            
            # Create a searchable multiselect
            all_tournaments = sorted(decklist_df['Tournament'].unique())
            selected_tournaments = st.multiselect(
                "Select tournaments (searchable)",
                options=all_tournaments,
                default=all_tournaments[:10],  # Show first 10 by default
                key="tournament_filter",
                help="Start typing to search through all available tournaments"
            )
            
            # Hero filter remains the same
            st.write("**Filter heroes:**")
            all_heroes = sorted(decklist_df['Hero'].unique())
            selected_heroes = st.multiselect(
                "Select heroes",
                options=all_heroes,
                default=all_heroes,
                key="hero_filter"
            )
            
            # Apply filters
            filtered = decklist_df[
                (decklist_df['Tournament'].isin(selected_tournaments)) &
                (decklist_df['Hero'].isin(selected_heroes))
            ]
            
            # Display player selector with search
            st.write("**Select player to view decklist:**")
            selected_player = st.selectbox(
                "Player",
                options=sorted(filtered['Player'].unique()),
                index=0,
                key="player_selector"
            )
            
            # Display selected deck info
            selected_deck = filtered[filtered['Player'] == selected_player].iloc[0]
            st.write(f"**Hero:** {selected_deck['Hero']}")
            st.write(f"**Tournament:** {selected_deck['Tournament']}")
            
            # Fetch and display decklist
            if st.button("View Decklist"):
                with st.spinner("Loading decklist..."):
                    deck = fetch_decklist(selected_deck['Decklist URL'])
                    display_decklist(deck)
            
            # Show all available decklists with pagination
            st.write(f"**Available decklists ({len(filtered)} total):**")
            
            # Add pagination
            page_size = 20
            page_number = st.number_input(
                "Page number", 
                min_value=1, 
                max_value=len(filtered)//page_size + 1, 
                value=1
            )
            
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            
            st.dataframe(
                filtered[['Player', 'Hero', 'Tournament']].iloc[start_idx:end_idx],
                use_container_width=True,
                height=min(400, page_size * 35)  # Adjust height based on page size
            )
            
        # Debug footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"v{datetime.now().strftime('%Y.%m.%d')} | Python {sys.version.split()[0]}")

if __name__ == "__main__":
    main()