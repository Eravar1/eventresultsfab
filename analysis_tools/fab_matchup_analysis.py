"""
Flesh and Blood Matchup Analysis Tool
Analyzes hero-vs-hero win rates from tournament data.
Input: 4_hero_matchups.csv with columns [Hero, Opponent Hero, Wins, Losses, Total Matches, Win Rate (%)]
Output: Matchup heatmap and top polarized matchups.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. Load Matchup Data ---
def load_matchup_data(filename):
    """Load and clean matchup data."""
    df = pd.read_csv(filename)
    
    # Clean column names (remove spaces)
    df.columns = df.columns.str.replace(' ', '_')
    
    # Ensure Win Rate is numeric (if it has '%' signs)
    if isinstance(df['Win_Rate_(%)'].iloc[0], str):
        df['Win_Rate_(%)'] = df['Win_Rate_(%)'].str.replace('%', '').astype(float)
    
    return df

# --- 2. Generate Matchup Heatmap ---
# def plot_matchup_heatmap(df):
#     """Create a win rate heatmap for hero matchups."""
#     # Pivot table: Heroes vs. Opponents with Win Rate as values
#     matchup_df = df.pivot_table(
#         values='Win_Rate_(%)', 
#         index='Hero', 
#         columns='Opponent_Hero',
#         aggfunc='mean'  # In case of duplicate entries
#     )
    
#     # Plot
#     plt.figure(figsize=(15, 12))
#     sns.heatmap(
#         matchup_df, 
#         annot=True, 
#         cmap='coolwarm', 
#         center=50, 
#         fmt='.1f',
#         linewidths=0.5
#     )
#     plt.title('Hero Matchup Win Rates (%)', fontsize=16)
#     plt.xticks(rotation=45, ha='right')
#     plt.yticks(rotation=0)
#     plt.tight_layout()
#     plt.savefig('matchup_heatmap.png', dpi=300, bbox_inches='tight')
#     plt.close()
#     print("Matchup heatmap saved as 'matchup_heatmap.png'")
    
#     return matchup_df


def plot_matchup_heatmap(df):
    """Create a cleaner, more readable win rate heatmap."""
    # Pivot and filter matchups with sufficient data (e.g., >= 10 matches)
    matchup_df = df[df['Total_Matches'] >= 10].pivot_table(
        values='Win_Rate_(%)', 
        index='Hero', 
        columns='Opponent_Hero',
        aggfunc='mean'
    )
    
    # Set up the figure
    plt.figure(figsize=(18, 16))  # Larger size for clarity
    ax = sns.heatmap(
        matchup_df,
        annot=True,
        annot_kws={'fontsize': 9},  # Smaller annotation font
        cmap='coolwarm',
        center=50,
        fmt='.0f',  # Round to whole numbers
        linewidths=0.3,
        linecolor='grey',
        cbar_kws={'label': 'Win Rate (%)'}
    )
    
    # Improve labels and title
    plt.title(
        'Flesh and Blood Hero Matchups (Win Rates %)\nMinimum 10 Matches', 
        fontsize=14,
        pad=20
    )
    plt.xlabel('Opponent Hero', fontsize=12)
    plt.ylabel('Hero', fontsize=12)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    
    # Save high-resolution image
    plt.tight_layout()
    plt.savefig('matchup_heatmap_enhanced.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Enhanced heatmap saved as 'matchup_heatmap_enhanced.png'")


    
# --- 3. Identify Polarized Matchups ---
def find_polarized_matchups(df, threshold=60):
    """
    Find matchups where win rate >= threshold (strong favor).
    Returns a DataFrame sorted by most polarized.
    """
    polarized = df[
        (df['Win_Rate_(%)'] >= threshold) | 
        (df['Win_Rate_(%)'] <= 100 - threshold)
    ].sort_values('Win_Rate_(%)', ascending=False)
    
    # Calculate absolute deviation from 50%
    polarized['Deviation'] = abs(polarized['Win_Rate_(%)'] - 50)
    polarized = polarized.sort_values('Deviation', ascending=False)
    
    return polarized

# --- 4. Main Execution ---
def main():
    # Load matchup data
    df = load_matchup_data('fab_tournament_data\\4_hero_matchups.csv')
    print("\n--- Loaded Data Sample ---")
    print(df.head())
    
    # Generate heatmap
    matchup_df = plot_matchup_heatmap(df)
    
    # Find top polarized matchups (e.g., win rate >= 60% or <= 40%)
    polarized = find_polarized_matchups(df, threshold=60)
    print("\n--- Top Polarized Matchups ---")
    print(polarized[['Hero', 'Opponent_Hero', 'Win_Rate_(%)', 'Total_Matches']])
    
    # Save polarized matchups to CSV
    polarized.to_csv('polarized_matchups.csv', index=False)
    print("\nPolarized matchups saved to 'polarized_matchups.csv'")

if __name__ == '__main__':
    main()