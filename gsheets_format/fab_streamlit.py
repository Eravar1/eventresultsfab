import streamlit as st
from main import scrape_round, process_data
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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
    except:
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

# ============== VISUALIZATION FUNCTIONS ==============
def show_matchup_analysis(data):
    st.header("⚔️ Matchup Analysis")
    
    min_matches = st.slider(
        "Minimum matches to display", 
        min_value=1, 
        max_value=20, 
        value=5,
        key="matchup_slider"
    )
    
    filtered = data['4_hero_matchups'][
        data['4_hero_matchups']['Total Matches'] >= min_matches
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Most Polarized Matchups")
        polarized = filtered[
            (filtered['Win Rate (%)'] >= 60) | 
            (filtered['Win Rate (%)'] <= 40)
        ].sort_values('Win Rate (%)', ascending=False)
        
        st.dataframe(
            polarized[['Hero', 'Opponent Hero', 'Win Rate (%)', 'Total Matches']],
            use_container_width=True
        )
    
    with col2:
        st.subheader("Matchup Heatmap")
        try:
            heatmap_data = filtered.pivot_table(
                values='Win Rate (%)',
                index='Hero',
                columns='Opponent Hero',
                aggfunc='mean'
            )
            
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(
                heatmap_data,
                annot=True,
                cmap='coolwarm',
                center=50,
                fmt='.1f',
                linewidths=0.5,
                ax=ax
            )
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Couldn't generate heatmap: {str(e)}")

def plot_comparison_chart(metric):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, df in enumerate(st.session_state.multi_df):
        hero_stats = df['3_hero_stats']
        tournament_name = st.session_state.tournament_names[i]
        
        top_hero = hero_stats.nlargest(5, metric)
        sns.barplot(
            x='Hero',
            y=metric,
            data=top_hero,
            label=tournament_name,
            alpha=0.7,
            ax=ax
        )
    
    ax.set_title(f"Top Heroes by {metric} Across Tournaments")
    ax.legend()
    st.pyplot(fig)

def render_hero_analysis():
    st.header("📊 Hero Performance")
    
    tab1, tab2 = st.tabs(["Single Tournament", "Multi-Tournament"])
    
    with tab1:
        if st.session_state.df:
            hero_stats = st.session_state.df['3_hero_stats']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Matches", st.session_state.match_count)
            
            with col2:
                top_hero = hero_stats.nlargest(1, 'Win Rate (%)')
                st.metric("Top Win Rate", 
                         f"{top_hero['Win Rate (%)'].values[0]}%",
                         top_hero['Hero'].values[0])
            
            st.dataframe(
                hero_stats.sort_values('Win Rate (%)', ascending=False),
                use_container_width=True,
                height=400
            )
    
    with tab2:
        if len(st.session_state.multi_df) > 1:
            metric = st.selectbox(
                "Comparison Metric",
                ['Win Rate (%)', 'Total Matches', 'Wins'],
                key="metric_selector"
            )
            plot_comparison_chart(metric)
            
            st.dataframe(
                pd.concat([
                    df['3_hero_stats'].assign(Tournament=name)
                    for df, name in zip(
                        st.session_state.multi_df,
                        st.session_state.tournament_names
                    )
                ]),
                use_container_width=True
            )
        else:
            st.info("Add more tournaments to enable comparison")

# ============== CORE FUNCTIONS ==============
def analyze_tournament(url):
    with st.spinner(f"Scraping {url.split('/')[-3].replace('-',' ').title()}..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_rounds = []
        
        with ThreadPoolExecutor() as executor:
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
        
        # Single Tournament Analysis
        st.subheader("Single Tournament")
        url = st.text_input(
            "Enter URL:",
            "https://fabtcg.com/en/coverage/calling-bologna-2025/results/",
            key="single_url"
        )
        
        if st.button("Analyze", key="analyze_single"):
            result = analyze_tournament(url)
            if result is not None:
                st.session_state.df = result
                st.session_state.match_count = len(result['1_match_results'])
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
                    st.session_state.multi_df.append(result)
                    st.session_state.tournament_names.append(
                        url.split('/')[-3].replace('-', ' ').title()
                    )
            
            progress_bar.empty()
            progress_text.empty()
            
            if st.session_state.multi_df:
                st.success(f"Loaded {len(st.session_state.multi_df)} tournaments!")
        
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
    if st.session_state.df or st.session_state.multi_df:
        render_hero_analysis()
        
        if st.session_state.df:
            with st.expander("🔍 Detailed Matchup Analysis"):
                show_matchup_analysis(st.session_state.df)
    
    # Debug footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"v{datetime.now().strftime('%Y.%m.%d')}")

if __name__ == "__main__":
    main()