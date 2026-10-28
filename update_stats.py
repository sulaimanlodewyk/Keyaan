import json
import urllib.request
from bs4 import BeautifulSoup

# Keyaan's specific CricClubs parameters
PLAYER_ID = "4493684"
CLUB_ID = "6010"
CLUB_NAME = "Coverdrivecricketschool"
JSON_FILE = "keyaan_cricclubs_stats.json"

URL = f"https://cricclubs.com/{CLUB_NAME}/viewPlayer.do?playerId={PLAYER_ID}&clubId={CLUB_ID}"

def fetch_and_update():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    req = urllib.request.Request(URL, headers=headers)
    
    try:
        print(f"Fetching stats from {URL}...")
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # --- Scrape Player Summary Info ---
            player_data = {
                "name": "Keyaan Lodewyk",
                "playerRole": "Wicket Keeper / Batter",
                "battingStyle": "Right-hand Batter",
                "jerseyNumber": "10",
                "currentTeam": "Cover Drive Cricket School",
                "matches": 0,
                "runs": 0,
                "wickets": 0
            }

            # Parse profile stats cards/tables if present
            stat_cards = soup.find_all('div', class_='stat-card') or []
            for card in stat_cards:
                text = card.text.strip().lower()
                if 'matches' in text:
                    player_data['matches'] = int(''.join(filter(str.isdigit, text)) or 0)
                elif 'runs' in text:
                    player_data['runs'] = int(''.join(filter(str.isdigit, text)) or 0)
                elif 'wickets' in text:
                    player_data['wickets'] = int(''.join(filter(str.isdigit, text)) or 0)

            # --- Scrape Detailed Series/Tournament Tables ---
            clubs_data = []
            tables = soup.find_all('table')
            
            series_stats = []
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cols = [ele.text.strip() for ele in row.find_all(['td', 'th'])]
                    if len(cols) >= 8:  # Typical CricClubs batting table columns
                        series_stats.append({
                            "teamName": cols[0] if cols[0] else "Cover Drive",
                            "seriesType": cols[1] if len(cols) > 1 else "League",
                            "matches": int(cols[2]) if cols[2].isdigit() else 0,
                            "innings": int(cols[3]) if cols[3].isdigit() else 0,
                            "runsScored": int(cols[4]) if cols[4].isdigit() else 0,
                            "highestScore": cols[5],
                            "average": cols[6],
                            "strikeRate": cols[7]
                        })

            clubs_data.append({
                "club": "Cover Drive Cricket School",
                "batting": series_stats
            })

            payload = {
                "player": player_data,
                "clubs": clubs_data
            }

            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            print(f"Successfully updated {JSON_FILE}!")

    except Exception as e:
        print(f"Error updating CricClubs stats: {e}")

if __name__ == "__main__":
    fetch_and_update()
