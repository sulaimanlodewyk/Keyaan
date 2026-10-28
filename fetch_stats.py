import json
import re
import requests
from bs4 import BeautifulSoup

# Replace this with Keyaan's actual CricClubs player profile URL
CRICCLUBS_PROFILE_URL = "https://www.cricclubs.com/YOUR_LEAGUE/viewPlayer.do?playerId=YOUR_PLAYER_ID&clubId=YOUR_CLUB_ID"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def scrape_cricclubs():
    response = requests.get(CRICCLUBS_PROFILE_URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch CricClubs page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Example parsing logic (adjust selectors based on exact CricClubs page markup)
    player_name = soup.find("h3", class_="player-name")
    name_text = player_name.text.strip() if player_name else "Keyaan Lodewyk"

    # Scrape summary stats cards / tables
    # (Extract tables using BeautifulSoup or pandas)
    
    # Structure your scraped data into the JSON layout
    data = {
        "player": {
            "name": name_text,
            "playerRole": "Batter / All-Rounder",
            "battingStyle": "Right-Hand Bat",
            "jerseyNumber": "18",
            "runs": 0,    # Updated dynamically from table
            "matches": 0, # Updated dynamically from table
            "wickets": 0
        },
        "clubs": []
    }

    # Save to local keyaan_cricclubs_stats.json
    with open("keyaan_cricclubs_stats.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Successfully updated keyaan_cricclubs_stats.json")

if __name__ == "__main__":
    scrape_cricclubs()
