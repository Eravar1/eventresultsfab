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

### Operation
Run the script:
    ```bash
    python eventresultsfab.py

When prompted, enter the tournament results page URL (e.g., https://fabtcg.com/en/coverage/event-name/results/)

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