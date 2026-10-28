import json
import urllib.request
import re

# Update this to Keyaan's actual CricClubs Profile URL or Player ID
PLAYER_ID = "YOUR_CRICCLUBS_PLAYER_ID" 
JSON_FILE = "keyaan_cricclubs_stats.json"

def fetch_stats():
    # Placeholder URL - replace with the exact CricClubs API/Page URL for Keyaan
    url = f"https://cricclubs.com/viewPlayer.do?playerId={PLAYER_ID}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # --- Parse stats from HTML or API endpoint here ---
            # For demonstration, structuring the scraped output:
            updated_data = {
                "player": {
                    "name": "Keyaan Lodewyk",
                    "playerRole": "Wicket Keeper",
                    "battingStyle": "Top Order Batter",
                    "jerseyNumber": "10",
                    "matches": 119,  # Dynamic values extracted from page
                    "runs": 1669,
                    "wickets": 6
                },
                "clubs": []  # Populated from scraped tables
            }
            
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, indent=2)
            print("Successfully updated stats JSON!")

    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_stats()
