import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

def parse_event_date(date_str):
    """Parse event date string into datetime object"""
    try:
        # Handle date ranges like "Oct 24-26, 2025" or single dates like "Oct 24, 2025"
        date_part = date_str.split(',')[-1].strip()  # Get the year part
        year = int(date_part)
        
        # Find month and day
        month_day_part = date_str.split(',')[0]
        if '-' in month_day_part:
            # Date range - take the last day
            day = int(month_day_part.split('-')[-1].strip().split()[-1])
        else:
            # Single date
            day = int(month_day_part.strip().split()[-1])
        
        month_str = month_day_part.strip().split()[0]
        month = datetime.strptime(month_str, '%b').month
        
        return datetime(year, month, day).date()
    except Exception as e:
        print(f"Could not parse date '{date_str}': {e}")
        return None

def is_past_event(event_date_str):
    """Check if an event date has passed"""
    event_date = parse_event_date(event_date_str)
    if not event_date:
        return False  # If we can't parse, assume it's upcoming
    return event_date < datetime.now().date()

def modify_tournament_url(original_url):
    """Insert /en/ and append /results/ to tournament URL"""
    if not original_url:
        return None
        
    parts = original_url.split('/')
    # Insert 'en' after the domain
    if len(parts) > 2:
        parts.insert(3, 'en')
    modified_url = '/'.join(parts)
    # Ensure it ends with /results/
    if not modified_url.endswith('/'):
        modified_url += '/'
    modified_url += 'results/'
    return modified_url

def get_tournament_links(resources_url):
    """Extract individual tournament links from a resources page, filtering for Classic Constructed"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"  Fetching tournament links from: {resources_url}")
        response = requests.get(resources_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tournaments = []
        
        # Find all tournament cards
        for card in soup.select('div.listblock-item'):
            # Find the link element
            link = card.find('a', class_='item-link')
            if not link or not link.has_attr('href'):
                continue
            
            # Get tournament name and format
            name = card.find('h5', class_='p-0').text.strip() if card.find('h5', class_='p-0') else None
            format_text = card.find('p', class_='m-0').text.strip() if card.find('p', class_='m-0') else ""
            
            # Only include Classic Constructed tournaments
            if "Classic Constructed" in format_text:
                original_url = urljoin(resources_url, link['href'])
                results_url = modify_tournament_url(original_url)
                tournaments.append({
                    'name': name,
                    'format': format_text,
                    'url': original_url,
                    'results_url': results_url
                })
        
        return tournaments if tournaments else None
    
    except Exception as e:
        print(f"Error getting tournaments from {resources_url}: {str(e)}")
        return None

def save_links_to_file(events, filename_prefix="tournament_links"):
    """Save all modified tournament URLs to separate files for past and upcoming events"""
    past_events = []
    upcoming_events = []
    
    # Separate events
    for event in events:
        if is_past_event(event['dates']):
            past_events.append(event)
        else:
            upcoming_events.append(event)
    
    # Save past events
    with open(f"{filename_prefix}_past.txt", 'w', encoding='utf-8') as f:
        for event in past_events:
            if event.get('tournaments'):
                for tournament in event['tournaments']:
                    if tournament.get('results_url'):
                        f.write(tournament['results_url'] + '\n')
    
    # Save upcoming events
    with open(f"{filename_prefix}_upcoming.txt", 'w', encoding='utf-8') as f:
        for event in upcoming_events:
            if event.get('tournaments'):
                for tournament in event['tournaments']:
                    if tournament.get('results_url'):
                        f.write(tournament['results_url'] + '\n')
    
    print(f"\nSaved {len(past_events)} past events to {filename_prefix}_past.txt")
    print(f"Saved {len(upcoming_events)} upcoming events to {filename_prefix}_upcoming.txt")
def get_resources_page(event_url):
    """Find the specific 'Pairings, Results and Standings' card link"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"  Finding resources page for: {event_url}")
        response = requests.get(event_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Specifically target the card with "Pairings, Results and Standings" text
        resources_card = soup.find('h5', string=lambda t: t and 'Pairings, Results, and Standings' in t)
        
        if resources_card:
            # Navigate up to the parent card element then find the link
            card = resources_card.find_parent('div', class_='listblock-item')
            if card:
                link = card.find('a', class_='item-link')
                if link and link.has_attr('href'):
                    return urljoin(event_url, link['href'])
        
        return None
    
    except Exception as e:
        print(f"Error getting resources page from {event_url}: {str(e)}")
        return None

def get_all_events_with_resources():
    base_url = "https://fabtcg.com"
    org_play_url = urljoin(base_url, "/en/organised-play/")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching main organized play page: {org_play_url}")
        response = requests.get(org_play_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
        
        # Find all month sections
        month_sections = soup.find_all('div', class_='block-pageLinkBlockWithURL')
        
        for section in month_sections:
            # Extract month name
            month_heading = section.find('h2')
            if not month_heading:
                continue
                
            month_name = month_heading.text.strip()
            
            # Skip if not a valid month name
            if not any(month.lower() in month_name.lower() for month in month_names):
                continue
            
            # Find all event cards in this month
            event_cards = section.find_all('div', class_='listblock-item')
            
            print(f"\nProcessing {len(event_cards)} events in {month_name}")
            
            for card in event_cards:
                # Get main event link
                link = card.find('a', class_='item-link')
                if link and link.has_attr('href'):
                    event_url = urljoin(base_url, link['href'])
                    event_name = link.find('h5').text.strip() if link.find('h5') else "Unknown Event"
                    event_dates = link.find('p').text.strip() if link.find('p') else "No dates"
                    
                    print(f"\nProcessing event: {event_name}")
                    
                    # Get resources page
                    resources_url = get_resources_page(event_url)
                    
                    if resources_url:
                        # Get all tournament links from resources page
                        tournaments = get_tournament_links(resources_url)
                        
                        events.append({
                            'month': month_name,
                            'name': event_name,
                            'url': event_url,
                            'dates': event_dates,
                            'resources_page': resources_url,
                            'tournaments': tournaments if tournaments else []
                        })
                    else:
                        print(f"  No resources page found for {event_name}")
        
        return events
    
    except Exception as e:
        print(f"Error getting main organized play page: {str(e)}")
        return []

# Run the scraper
all_events = get_all_events_with_resources()

# Print results with proper date status
print("\nFinal Results:")
for event in all_events:
    status = "PAST" if is_past_event(event['dates']) else "UPCOMING"
    print(f"\n[{status}] {event['month']} - {event['name']} ({event['dates']})")
    print(f"Event URL: {event['url']}")
    print(f"Resources Page: {event['resources_page']}")
    
    if event.get('tournaments'):
        print("Classic Constructed Tournaments:")
        for tournament in event['tournaments']:
            print(f"  {tournament['name']}")
            print(f"    Original URL: {tournament['url']}")
            print(f"    Results URL: {tournament['results_url']}")

# Save to separate files
save_links_to_file(all_events)