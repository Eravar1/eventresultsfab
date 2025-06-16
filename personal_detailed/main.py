import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import os

BASE_URL = "https://fabtcg.com/en/coverage/calling-bologna-2025/results/{}/"
OUTPUT_DIR = "tournament_results"
MATCH_RESULTS_FILE = "match_results.csv"
PLAYER_STATS_FILE = "player_stats.csv"
HERO_STATS_FILE = "hero_stats.csv"
PLAYER_DETAILS_DIR = "player_details"
HERO_MATCHUPS_DIR = "hero_matchups"

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

def fetch_page(url):
    """Fetch a webpage and return its BeautifulSoup object."""
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Failed to fetch {url}. Status: {response.status_code}")
        return None

def scrape_round(base_url, round_num):
    """Scrape match data for a specific round."""
    url = f"{base_url}{round_num}/"
    soup = fetch_page(url)
    if not soup:
        return []
    
    matches = []
    match_rows = soup.find_all('div', class_='tournament-coverage__row--results')
    
    for row in match_rows:
        players = row.find_all('div', class_='tournament-coverage__player')
        
        if len(players) >= 2:
            # Player 1 data
            player1_name = players[0].find('span').get_text(strip=True)
            player1_hero = players[0].find('div', class_='tournament-coverage__player-hero-and-deck').get_text(strip=True)
            
            # Player 2 data
            player2_name = players[1].find('span').get_text(strip=True)
            player2_hero = players[1].find('div', class_='tournament-coverage__player-hero-and-deck').get_text(strip=True)
            
            # Determine winner
            winner = None
            if 'tournament-coverage__player--winner' in players[0]['class']:
                winner = player1_name
            elif 'tournament-coverage__player--winner' in players[1]['class']:
                winner = player2_name
            
            matches.append({
                'Round': f"Round {round_num}",
                'Player 1 Name': player1_name,
                'Player 1 Hero': player1_hero,
                'Player 2 Name': player2_name,
                'Player 2 Hero': player2_hero,
                'Winner': winner,
                'Winning Hero': player1_hero if winner == player1_name else player2_hero if winner == player2_name else None
            })
    
    return matches

def calculate_stats(matches):
    """Calculate player and hero statistics."""
    player_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'heroes_used': set()})
    hero_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'matchups': defaultdict(lambda: {'wins': 0, 'losses': 0})})
    player_details = defaultdict(list)
    
    for match in matches:
        player1 = match['Player 1 Name']
        player2 = match['Player 2 Name']
        hero1 = match['Player 1 Hero']
        hero2 = match['Player 2 Hero']
        winner = match['Winner']
        
        # Track player stats
        player_stats[player1]['heroes_used'].add(hero1)
        player_stats[player2]['heroes_used'].add(hero2)
        
        # Track hero stats
        if winner == player1:
            player_stats[player1]['wins'] += 1
            player_stats[player2]['losses'] += 1
            hero_stats[hero1]['wins'] += 1
            hero_stats[hero2]['losses'] += 1
            hero_stats[hero1]['matchups'][hero2]['wins'] += 1
            hero_stats[hero2]['matchups'][hero1]['losses'] += 1
        elif winner == player2:
            player_stats[player2]['wins'] += 1
            player_stats[player1]['losses'] += 1
            hero_stats[hero2]['wins'] += 1
            hero_stats[hero1]['losses'] += 1
            hero_stats[hero2]['matchups'][hero1]['wins'] += 1
            hero_stats[hero1]['matchups'][hero2]['losses'] += 1
        
        # Record player details
        player_details[player1].append({
            'Round': match['Round'],
            'Opponent': player2,
            'Opponent Hero': hero2,
            'Result': 'Win' if winner == player1 else 'Loss',
            'Player Hero': hero1
        })
        
        player_details[player2].append({
            'Round': match['Round'],
            'Opponent': player1,
            'Opponent Hero': hero1,
            'Result': 'Win' if winner == player2 else 'Loss',
            'Player Hero': hero2
        })
    
    return player_stats, hero_stats, player_details

def prepare_hero_stats(hero_stats):
    """Prepare hero statistics for CSV output."""
    # Overall hero stats
    overall_stats = []
    for hero, stats in hero_stats.items():
        total = stats['wins'] + stats['losses']
        overall_stats.append({
            'Hero': hero,
            'Wins': stats['wins'],
            'Losses': stats['losses'],
            'Total Matches': total,
            'Win Rate': round(stats['wins'] / total * 100, 2) if total > 0 else 0
        })
    
    # Hero matchup stats
    matchup_stats = []
    for hero, stats in hero_stats.items():
        for opponent, matchup in stats['matchups'].items():
            total = matchup['wins'] + matchup['losses']
            if total > 0:
                matchup_stats.append({
                    'Hero': hero,
                    'Opponent Hero': opponent,
                    'Wins': matchup['wins'],
                    'Losses': matchup['losses'],
                    'Total Matches': total,
                    'Win Rate': round(matchup['wins'] / total * 100, 2)
                })
    
    return overall_stats, matchup_stats

def save_player_details(player_details):
    """Save individual player details to separate CSV files."""
    if not os.path.exists(os.path.join(OUTPUT_DIR, PLAYER_DETAILS_DIR)):
        os.makedirs(os.path.join(OUTPUT_DIR, PLAYER_DETAILS_DIR))
    
    for player, matches in player_details.items():
        safe_name = "".join(c if c.isalnum() else "_" for c in player)
        filename = f"{safe_name}_details.csv"
        filepath = os.path.join(OUTPUT_DIR, PLAYER_DETAILS_DIR, filename)
        
        df = pd.DataFrame(matches)
        df.to_csv(filepath, index=False)

def save_hero_matchups(hero_stats):
    """Save hero matchup statistics."""
    if not os.path.exists(os.path.join(OUTPUT_DIR, HERO_MATCHUPS_DIR)):
        os.makedirs(os.path.join(OUTPUT_DIR, HERO_MATCHUPS_DIR))
    
    overall_stats, matchup_stats = prepare_hero_stats(hero_stats)
    
    # Save overall hero stats
    df_overall = pd.DataFrame(overall_stats)
    df_overall.to_csv(os.path.join(OUTPUT_DIR, HERO_STATS_FILE), index=False)
    
    # Save matchup details per hero
    df_matchups = pd.DataFrame(matchup_stats)
    for hero in df_matchups['Hero'].unique():
        safe_name = "".join(c if c.isalnum() else "_" for c in hero)
        filename = f"{safe_name}_matchups.csv"
        filepath = os.path.join(OUTPUT_DIR, HERO_MATCHUPS_DIR, filename)
        
        hero_df = df_matchups[df_matchups['Hero'] == hero]
        hero_df.to_csv(filepath, index=False)

def main():
    # Get tournament URL from user
    BASE_URL = get_tournament_url()
    
    # Configuration
    OUTPUT_DIR = "tournament_results"
    MATCH_RESULTS_FILE = "match_results.csv"
    PLAYER_STATS_FILE = "player_stats.csv"
    HERO_STATS_FILE = "hero_stats.csv"
    PLAYER_DETAILS_DIR = "player_details"
    HERO_MATCHUPS_DIR = "hero_matchups"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Scrape rounds 1 through N
    all_rounds = []
    max_rounds = 20  # Adjust based on tournament rounds
    max_empty_rounds = 1  # Stop after this many empty rounds
    
    empty_rounds = 0
    for round_num in range(1, max_rounds + 1):
        print(f"Scraping Round {round_num}...", end=' ')
        round_matches = scrape_round(BASE_URL, round_num)
        
        if not round_matches:
            print("no data")
            empty_rounds += 1
            if empty_rounds >= max_empty_rounds:
                print(f"Stopping after {max_empty_rounds} empty rounds.")
                break
            continue
        
        empty_rounds = 0
        all_rounds.extend(round_matches)
        print(f"found {len(round_matches)} matches")
    
    if all_rounds:
        # Save match results
        df_matches = pd.DataFrame(all_rounds)
        df_matches.to_csv(os.path.join(OUTPUT_DIR, MATCH_RESULTS_FILE), index=False)
        print(f"\nMatch results saved to {os.path.join(OUTPUT_DIR, MATCH_RESULTS_FILE)}")
        
        # Calculate stats
        player_stats, hero_stats, player_details = calculate_stats(all_rounds)
        
        # Save player statistics
        player_stats_list = [{
            'Player': player,
            'Wins': stats['wins'],
            'Losses': stats['losses'],
            'Win Rate': round(stats['wins'] / (stats['wins'] + stats['losses']) * 100, 2) if (stats['wins'] + stats['losses']) > 0 else 0,
            'Heroes Used': ', '.join(stats['heroes_used'])
        } for player, stats in player_stats.items()]
        
        df_player_stats = pd.DataFrame(player_stats_list)
        df_player_stats.to_csv(os.path.join(OUTPUT_DIR, PLAYER_STATS_FILE), index=False)
        print(f"Player statistics saved to {os.path.join(OUTPUT_DIR, PLAYER_STATS_FILE)}")
        
        # Save player details
        save_player_details(player_details)
        print(f"Player details saved to {os.path.join(OUTPUT_DIR, PLAYER_DETAILS_DIR)}")
        
        # Save hero stats and matchups
        save_hero_matchups(hero_stats)
        print(f"Hero statistics saved to {os.path.join(OUTPUT_DIR, HERO_STATS_FILE)}")
        print(f"Hero matchup details saved to {os.path.join(OUTPUT_DIR, HERO_MATCHUPS_DIR)}")
    else:
        print("\nNo data scraped.")

if __name__ == "__main__":
    main()