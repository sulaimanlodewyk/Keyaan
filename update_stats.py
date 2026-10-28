import json
import requests
from bs4 import BeautifulSoup

# Keyaan's specific CricClubs parameters
PLAYER_ID = "4493684"
CLUB_ID = "6010"
CLUB_NAME = "Coverdrivecricketschool"
JSON_FILE = "keyaan_cricclubs_stats.json"

URL = f"https://cricclubs.com/{CLUB_NAME}/viewPlayer.do?playerId={PLAYER_ID}&clubId={CLUB_ID}"

def fetch_and_update():
    # Full browser headers to bypass 403 Forbidden checks
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://cricclubs.com/{CLUB_NAME}/',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Upgrade-Insecure-Requests': '1'
    }

    session = requests.Session()

    try:
        print(f"Fetching stats from {URL}...")
        response = session.get(URL, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Parse Player Summary Info ---
        player_data = {
            "name": "Keyaan Lodewyk",
            "playerRole": "Wicket Keeper / Batter",
            "battingStyle": "Right-hand Batter",
            "jerseyNumber": "10",
            "currentTeam": "Cover Drive Cricket School",
            "matches": 119,
            "runs": 1669,
            "wickets": 6
        }

        # Search for stats cards or tables
        stat_cards = soup.find_all('div', class_='stat-card') or []
        for card in stat_cards:
            text = card.text.strip().lower()
            if 'matches' in text:
                digits = ''.join(filter(str.isdigit, text))
                if digits: player_data['matches'] = int(digits)
            elif 'runs' in text:
                digits = ''.join(filter(str.isdigit, text))
                if digits: player_data['runs'] = int(digits)
            elif 'wickets' in text:
                digits = ''.join(filter(str.isdigit, text))
                if digits: player_data['wickets'] = int(digits)

        # --- Parse Detailed Series/Tournament Tables ---
        clubs_data = []
        series_stats = []
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = [ele.text.strip() for ele in row.find_all(['td', 'th'])]
                if len(cols) >= 8:
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
