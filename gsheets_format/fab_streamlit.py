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

def plot_matchup_heatmap(df, key_suffix=""):
    min_matches = st.slider(
        "Minimum matches to display", 
        min_value=1, 
        max_value=20, 
        value=5,
        key=f"heatmap_slider_{key_suffix}"
    )
    
    filtered = df['4_hero_matchups'][
        df['4_hero_matchups']['Total Matches'] >= min_matches
    ]
    
    heatmap_data = filtered.pivot_table(
        values='Win Rate (%)',
        index='Hero',
        columns='Opponent Hero',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdBu',
        zmid=50,
        text=heatmap_data.values.round(1),
        hoverinfo="x+y+z"
    ))
    
    fig.update_layout(
        height=800,
        title="Hero Matchup Win Rates (%)",
        xaxis_title="Opponent Hero",
        yaxis_title="Hero",
        margin=dict(l=100, r=50, b=150, t=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

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
    tab1, tab2, tab3 = st.tabs(["Hero Performance", "Matchups", "Player Stats"])
    
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
        st.subheader("Multi-Tournament")
        multi_urls = st.text_area(
            "Enter URLs (one per line):",
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
            
            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                tournament_filter = st.multiselect(
                    "Filter by tournament",
                    options=decklist_df['Tournament'].unique(),
                    default=decklist_df['Tournament'].unique()
                )
            with col2:
                hero_filter = st.multiselect(
                    "Filter by hero",
                    options=decklist_df['Hero'].unique(),
                    default=decklist_df['Hero'].unique()
                )
            
            # Apply filters
            filtered = decklist_df[
                (decklist_df['Tournament'].isin(tournament_filter)) &
                (decklist_df['Hero'].isin(hero_filter))
            ]
            
            # Display decklist selector
            selected_player = st.selectbox(
                "Select player to view decklist",
                filtered['Player'].unique()
            )
            
            selected_deck = filtered[filtered['Player'] == selected_player].iloc[0]
            st.write(f"**Hero:** {selected_deck['Hero']}")
            st.write(f"**Tournament:** {selected_deck['Tournament']}")
            
            # Fetch and display decklist
            if st.button("View Decklist"):
                with st.spinner("Loading decklist..."):
                    deck = fetch_decklist(selected_deck['Decklist URL'])
                    display_decklist(deck)
            
            # Show all available decklists
            with st.expander("View All Decklists"):
                st.dataframe(
                    filtered[['Player', 'Hero', 'Tournament']],
                    use_container_width=True,
                    height=400
                )

    # Debug footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"v{datetime.now().strftime('%Y.%m.%d')} | Python {sys.version.split()[0]}")

if __name__ == "__main__":
    main()