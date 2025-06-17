import streamlit as st
from main import scrape_round, process_data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============== CONFIGURATION ==============
st.set_page_config(
    page_title="FaB Tournament Analyzer Pro",
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
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'tournament_name' not in st.session_state:
    st.session_state.tournament_name = ""

# ============== STYLING ==============
def apply_style(dark):
    if dark:
        plt.style.use('dark_background')
        sns.set_palette('dark')
        st.markdown("""
        <style>
            :root {--primary-color: #ff4b4b;}
            .main {background-color: #0e1117;}
            .sidebar .sidebar-content {background-color: #1a1d24;}
            .stDataFrame {background-color: #1a1d24;}
            .stProgress > div > div {background-color: #ff4b4b;}
        </style>
        """, unsafe_allow_html=True)
    else:
        plt.style.use('default')
        sns.set_palette('bright')
        st.markdown("""
        <style>
            :root {--primary-color: #ff4b4b;}
            .main {background-color: #f8f9fa;}
            .stProgress > div > div {background-color: #ff4b4b;}
        </style>
        """, unsafe_allow_html=True)

# ============== ENHANCED VISUALIZATIONS ==============
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

def plot_matchup_heatmap(df):
    min_matches = st.slider(
        "Minimum matches to display", 
        min_value=1, 
        max_value=20, 
        value=5,
        key="heatmap_slider"
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
        st.session_state.tournament_name = tournament_name
        
        with st.spinner("Analyzing matches..."):
            return cached_process(all_rounds)

# ============== MAIN APP ==============
def main():
    st.title("🏆 Flesh and Blood Tournament Analyzer Pro")
    
    # ===== SIDEBAR CONTROLS =====
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Dark Mode Toggle
        st.session_state.dark_mode = st.toggle(
            "Dark Mode",
            value=st.session_state.dark_mode,
            key="dark_mode_toggle"
        )
        apply_style(st.session_state.dark_mode)
        
        # Tournament Analysis
        st.subheader("Tournament Analysis")
        url = st.text_input(
            "Enter URL:",
            "https://fabtcg.com/en/coverage/calling-bologna-2025/results/",
            key="tournament_url"
        )
        
        if st.button("Analyze Tournament", key="analyze_tournament"):
            result = analyze_tournament(url)
            if result is not None:
                st.session_state.df = result
                st.session_state.match_count = len(result['1_match_results'])
                st.success("Analysis complete!")
        
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
    if st.session_state.df:
        st.header(f"📊 {st.session_state.tournament_name} Analysis")
        st.metric("Total Matches Analyzed", st.session_state.match_count)
        
        tab1, tab2, tab3 = st.tabs(["Hero Performance", "Matchups", "Player Stats"])
        
        with tab1:
            plot_hero_performance(st.session_state.df)
            
            with st.expander("Detailed Hero Stats"):
                st.dataframe(
                    st.session_state.df['3_hero_stats'].sort_values('Win Rate (%)', ascending=False),
                    use_container_width=True,
                    height=400
                )
        
        with tab2:
            plot_matchup_heatmap(st.session_state.df)
            
            with st.expander("Matchup Details"):
                st.dataframe(
                    st.session_state.df['4_hero_matchups'],
                    use_container_width=True,
                    height=400
                )
        
        with tab3:
            plot_player_performance(st.session_state.df)
            
            with st.expander("All Player Stats"):
                st.dataframe(
                    st.session_state.df['2_player_stats'].sort_values('Win Rate (%)', ascending=False),
                    use_container_width=True,
                    height=400
                )
    
    # Debug footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"v{datetime.now().strftime('%Y.%m.%d')} | Python {sys.version.split()[0]}")

if __name__ == "__main__":
    main()