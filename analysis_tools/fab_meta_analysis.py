"""
Flesh and Blood Meta Analysis Tool
Analyzes hero win rates and matchups from tournament data.
Input: CSV with columns [Hero, Wins, Losses, Total Matches, Win Rate (%)]
Output: Visualizations and exported CSV with insights.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. Load and Prepare Data ---
def load_data(filename):
    """Load and clean the dataset."""
    df = pd.read_csv(filename)
    
    # Ensure Win Rate is numeric (if it has '%' signs)
    if isinstance(df['Win Rate (%)'].iloc[0], str):
        df['Win Rate (%)'] = df['Win Rate (%)'].str.replace('%', '').astype(float)
    
    return df

# --- 2. Analysis Functions ---
def analyze_overall_performance(df):
    """Calculate and print top/bottom heroes by win rate."""
    df_sorted = df.sort_values('Win Rate (%)', ascending=False)
    
    print("\n--- Top 10 Heroes by Win Rate ---")
    print(df_sorted[['Hero', 'Win Rate (%)', 'Total Matches']].head(10))
    
    print("\n--- Bottom 10 Heroes by Win Rate ---")
    print(df_sorted[['Hero', 'Win Rate (%)', 'Total Matches']].tail(10))
    
    return df_sorted

def plot_win_rate_distribution(df):
    """Visualize the distribution of win rates."""
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='Win Rate (%)', bins=20, kde=True)
    plt.title('Distribution of Hero Win Rates')
    plt.savefig('win_rate_distribution.png', bbox_inches='tight')
    plt.close()

def plot_performance_scatter(df):
    """Bubble plot: Win Rate vs. Popularity."""
    plt.figure(figsize=(12, 8))
    scatter = sns.scatterplot(
        data=df, 
        x='Total Matches', 
        y='Win Rate (%)', 
        size='Wins', 
        hue='Hero', 
        alpha=0.7,
        sizes=(20, 200)  # Adjust bubble sizes
    )
    plt.title('Hero Performance: Win Rate vs. Popularity')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('performance_scatter.png', bbox_inches='tight')
    plt.close()

# --- 3. Advanced Analysis (If Matchup Data Exists) ---
def analyze_matchups(df):
    """Optional: Generate matchup heatmap if data is structured for it."""
    try:
        # Pivot table (adjust columns if needed)
        matchup_df = df.pivot_table(values='Win Rate (%)', index='Hero', columns='Opponent')
        plt.figure(figsize=(12, 10))
        sns.heatmap(matchup_df, annot=True, cmap='coolwarm', center=50, fmt='.1f')
        plt.title('Hero Matchup Win Rates (%)')
        plt.savefig('matchup_heatmap.png', bbox_inches='tight')
        plt.close()
        print("\nMatchup heatmap saved as 'matchup_heatmap.png'")
    except KeyError:  
        print("\nNo matchup data found. Skipping heatmap.")

# --- 4. Main Execution ---
def main():
    # Load data
    df = load_data('fab_tournament_data\\3_hero_stats.csv')
    
    # Basic analysis
    df_sorted = analyze_overall_performance(df)
    
    # Visualizations
    plot_win_rate_distribution(df_sorted)
    plot_performance_scatter(df_sorted)
    
    # Advanced (if applicable)
    analyze_matchups(df)
    
    # Export results
    df_sorted.to_csv('hero_analysis_results.csv', index=False)
    print("\nAnalysis complete! Results saved to:")
    print("- hero_analysis_results.csv")
    print("- win_rate_distribution.png")
    print("- performance_scatter.png")

if __name__ == '__main__':
    main()