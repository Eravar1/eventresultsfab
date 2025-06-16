import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import os
import re

def get_tournament_url():
    """Prompt user for tournament URL and validate format."""
    print("\nPlease enter the tournament results page URL (e.g., https://fabtcg.com/en/coverage/calling-bologna-2025/results/)")
    while True:
        url = input("Tournament URL: ").strip()
        
        # Basic validation
        if not url.startswith('https://fabtcg.com/en/coverage/'):
            print("URL must start with: https://fabtcg.com/en/coverage/")
            continue
            
        if not url.endswith('/results/'):
            if url.endswith('/results'):
                url += '/'
            else:
                print("URL must end with: /results/")
                continue
                
        # Test the base URL
        test_url = f"{url}1/"  # Test with round 1
        try:
            response = requests.head(test_url, timeout=5)
            if response.status_code == 200:
                return url
            print(f"Couldn't access tournament data (HTTP {response.status_code}). Please check the URL.")
        except requests.RequestException:
            print("Invalid URL or couldn't connect. Please try again.")

def scrape_round(base_url, round_num):
    """Scrape match data for a specific round."""
    url = f"{base_url}{round_num}/"
    soup = fetch_page(url)
    if not soup:
        return None
    
    matches = []
    match_rows = soup.find_all('div', class_='tournament-coverage__row--results')
    
    for row in match_rows:
        players = row.find_all('div', class_='tournament-coverage__player')
        if len(players) >= 2:
            p1_name = players[0].find('span').get_text(strip=True)
            p1_hero = players[0].find('div', class_='tournament-coverage__player-hero-and-deck').get_text(strip=True)
            p2_name = players[1].find('span').get_text(strip=True)
            p2_hero = players[1].find('div', class_='tournament-coverage__player-hero-and-deck').get_text(strip=True)
            
            winner = None
            if 'tournament-coverage__player--winner' in players[0]['class']:
                winner = p1_name
            elif 'tournament-coverage__player--winner' in players[1]['class']:
                winner = p2_name
            
            matches.append({
                'Round': f"Round {round_num}",
                'Player 1 Name': p1_name, 'Player 1 Hero': p1_hero,
                'Player 2 Name': p2_name, 'Player 2 Hero': p2_hero,
                'Winner': winner,
                'Winning Hero': p1_hero if winner == p1_name else p2_hero if winner == p2_name else None
            })
    return matches


def fetch_page(url):
    """Fetch webpage and return BeautifulSoup object."""
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser') if response.status_code == 200 else None

# def scrape_round(round_num):
#     """Scrape match data for a specific round."""
#     soup = fetch_page(BASE_URL.format(round_num))
#     if not soup:
#         return []
    
#     matches = []
#     for row in soup.find_all('div', class_='tournament-coverage__row--results'):
#         players = row.find_all('div', class_='tournament-coverage__player')
#         if len(players) >= 2:
#             p1_name = players[0].find('span').get_text(strip=True)
#             p1_hero = players[0].find('div', class_='tournament-coverage__player-hero-and-deck').get_text(strip=True)
#             p2_name = players[1].find('span').get_text(strip=True)
#             p2_hero = players[1].find('div', class_='tournament-coverage__player-hero-and-deck').get_text(strip=True)
            
#             winner = None
#             if 'tournament-coverage__player--winner' in players[0]['class']:
#                 winner = p1_name
#             elif 'tournament-coverage__player--winner' in players[1]['class']:
#                 winner = p2_name
            
#             matches.append({
#                 'Round': f"Round {round_num}",
#                 'Player 1 Name': p1_name, 'Player 1 Hero': p1_hero,
#                 'Player 2 Name': p2_name, 'Player 2 Hero': p2_hero,
#                 'Winner': winner,
#                 'Winning Hero': p1_hero if winner == p1_name else p2_hero if winner == p2_name else None
#             })
#     return matches

def process_data(matches):
    """Process all tournament data and return organized DataFrames."""
    # Initialize data structures
    player_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'heroes_used': set()})
    hero_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'matchups': defaultdict(lambda: {'wins': 0, 'losses': 0})})
    all_player_details = []
    all_matches = []
    
    for match in matches:
        p1, p2 = match['Player 1 Name'], match['Player 2 Name']
        h1, h2 = match['Player 1 Hero'], match['Player 2 Hero']
        winner = match['Winner']
        
        # Track match results
        all_matches.append(match)
        
        # Track player stats
        player_stats[p1]['heroes_used'].add(h1)
        player_stats[p2]['heroes_used'].add(h2)
        
        # Track hero stats
        if winner == p1:
            player_stats[p1]['wins'] += 1
            player_stats[p2]['losses'] += 1
            hero_stats[h1]['wins'] += 1
            hero_stats[h2]['losses'] += 1
            hero_stats[h1]['matchups'][h2]['wins'] += 1
            hero_stats[h2]['matchups'][h1]['losses'] += 1
        elif winner == p2:
            player_stats[p2]['wins'] += 1
            player_stats[p1]['losses'] += 1
            hero_stats[h2]['wins'] += 1
            hero_stats[h1]['losses'] += 1
            hero_stats[h2]['matchups'][h1]['wins'] += 1
            hero_stats[h1]['matchups'][h2]['losses'] += 1
        
        # Combine player details
        all_player_details.append({
            'Player': p1, 'Hero': h1,
            'Round': match['Round'],
            'Opponent': p2, 'Opponent Hero': h2,
            'Result': 'Win' if winner == p1 else 'Loss'
        })
        all_player_details.append({
            'Player': p2, 'Hero': h2,
            'Round': match['Round'],
            'Opponent': p1, 'Opponent Hero': h1,
            'Result': 'Win' if winner == p2 else 'Loss'
        })
    
    # Create DataFrames
    match_results_df = pd.DataFrame(all_matches)
    
    player_stats_df = pd.DataFrame([{
        'Player': player,
        'Wins': stats['wins'],
        'Losses': stats['losses'],
        'Win Rate (%)': round(stats['wins'] / (stats['wins'] + stats['losses']) * 100, 2) if (stats['wins'] + stats['losses']) > 0 else 0,
        'Heroes Used': ', '.join(stats['heroes_used'])
    } for player, stats in player_stats.items()])
    
    hero_stats_df = pd.DataFrame([{
        'Hero': hero,
        'Wins': stats['wins'],
        'Losses': stats['losses'],
        'Total Matches': stats['wins'] + stats['losses'],
        'Win Rate (%)': round(stats['wins'] / (stats['wins'] + stats['losses']) * 100, 2) if (stats['wins'] + stats['losses']) > 0 else 0
    } for hero, stats in hero_stats.items()])
    
    # Prepare hero matchup data
    matchup_data = []
    for hero, stats in hero_stats.items():
        for opponent, matchup in stats['matchups'].items():
            total = matchup['wins'] + matchup['losses']
            if total > 0:
                matchup_data.append({
                    'Hero': hero,
                    'Opponent Hero': opponent,
                    'Wins': matchup['wins'],
                    'Losses': matchup['losses'],
                    'Total Matches': total,
                    'Win Rate (%)': round(matchup['wins'] / total * 100, 2)
                })
    hero_matchups_df = pd.DataFrame(matchup_data)
    
    player_details_df = pd.DataFrame(all_player_details)
    
    return {
        '1_match_results': match_results_df,
        '2_player_stats': player_stats_df,
        '3_hero_stats': hero_stats_df,
        '4_hero_matchups': hero_matchups_df,
        '5_player_details': player_details_df
    }

def save_to_csv(data_frames, output_dir):
    """Save all DataFrames to CSV files."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for name, df in data_frames.items():
        filename = f"{name}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Saved {filename}")

def main():
    # Get tournament URL from user
    BASE_URL = get_tournament_url()
    OUTPUT_DIR = "fab_tournament_data"
    
    # Scrape all rounds
    all_rounds = []
    print("\nScraping tournament data...")
    
    max_attempts = 3
    found_rounds = 0
    
    for round_num in range(1, 21):  # Check up to 20 rounds
        if max_attempts == 0:
            break
            
        print(f"  Round {round_num}...", end=' ', flush=True)
        round_matches = scrape_round(BASE_URL, round_num)
        
        if not round_matches:
            print("no data")
            max_attempts -= 1
            continue
            
        all_rounds.extend(round_matches)
        found_rounds += 1
        max_attempts = 3  # Reset attempts if we found data
        print(f"{len(round_matches)} matches")
    
    if not all_rounds:
        print("\nNo tournament data found. Please check the URL and try again.")
        return
    
    print(f"\nFound {found_rounds} rounds with {len(all_rounds)} total matches")
    
    # Process and save data
    data_frames = process_data(all_rounds)
    save_to_csv(data_frames, OUTPUT_DIR)
    
    print(f"\nAll files saved to '{OUTPUT_DIR}' directory.")
    print("\nHow to import to Google Sheets:")
    print("1. Go to sheets.google.com")
    print("2. Create new spreadsheet")
    print("3. For each CSV:")
    print("   - File > Import > Upload")
    print("   - Select CSV file")
    print("   - Choose 'Replace spreadsheet'")
if __name__ == "__main__":
    main()