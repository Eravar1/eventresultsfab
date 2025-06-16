# FAB Tournament Results Processor

**Internal Tool for Team Gas Guzzlers (GG)**

## Overview

This tool collects data from the coverage page of Flesh and Blood (FAB) tournaments to facilitate data analysis for GG members when preparing for future FAB events.

## Features

- **Automated Data Collection**: Scrapes tournament results from official FAB coverage pages
- **Performance Analytics**: Calculates win rates, matchup statistics, and hero performance

## Usage Instructions

### Prerequisites

- Python 3.9+
- Required packages: `requests`, `beautifulsoup4`, `pandas`

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install requests beautifulsoup4 pandas

If it doesn't work, please run cmd as administrator and run the command again.

### Operation
Run the script:
    ```bash
    python eventresultsfab.py

When prompted, enter the tournament results page URL (e.g., https://fabtcg.com/en/coverage/event-name/results/)

This can be retrieved via the coverage page. Each page is numbered according to the round, so just pick any match results page and remove the round number. 

i.e. https://fabtcg.com/en/coverage/calling-bologna-2025/, the first result page is https://fabtcg.com/en/coverage/calling-bologna-2025/results/1/, just remove the 1/ at the back.

The tool will automatically:

- Validate the URL

- Scrape available rounds

- Generate analysis files

### Output Files
All outputs are saved in the tournament_results directory:

- match_results.csv: Complete tournament match records

- player_stats.csv: Individual player performance metrics

- hero_stats.csv: Aggregate hero performance data

- player_details/: Individual player match histories

- hero_matchups/: Detailed hero-vs-hero matchup statistics

### Maintainance
Text Fing Roo on discord? 

### Disclaimer
This tool is for internal GG use only. All data is sourced from publicly available tournament coverage pages.