"""
refresh_cricclubs.py (reconstructed version)

# Inputs:
# - raw/cricclubs/dir holding the extracted HAR bodies.
#   Each file is a single JSON body or text HTML response to a raw file
#   e.g. viewPlayer.do?playerId=... (no query parameters in filename)
# - Old/refresh_keyaan_cricclubs_stats.json (where data leaves a leak)
#
# Outputs:
# - keyaan_cricclubs_stats.json - formatted output file.
#
# Data sources (your HAR/HTML dump points):
# - profileCard (from viewPlayer.do) -> global player + ALL-CLUB aggregates (playerOtherClubStats)
# - gps/gpb (from viewPlayer.do) -> per-league stats / per-series per-type
# - gmm (from viewPlayer.do) -> match-level records - per-type vs nulltype
# - mlr (from viewPlayer.do) -> per-series match-level records vs per-series bowling rows
# - insight (from viewPlayer.do) -> insights/graphs, per-series, per-type
# - grouped (from viewPlayer.do) -> per-league, per-type per-series tables
#
# THINGS NOT IN THIS HAR: raw dumps from Cover Drive/Montrose 3U11B table, Cover Drive
#  batting records, etc.
"""

import json, re, html, sys, os

# paths
OUT = "keyaan_cricclubs_stats.json"
# change path to match your environment if needed:
OLD = r"/Users/keyaan.lodewyk/Library/CloudStorage/OneDrive-Absa/personal_py/cricket/keyaan_cricclubs_stats.json"
RAW = "raw/cricclubs"  # folder containing dumped raw response bodies

# Load old JSON if available
try:
    with open(OLD, "r") as f:
        old = json.load(f)
except Exception:
    old = {}

def find(pred):
    hits = [q for q in body if pred(q)]
    if not hits:
        print(f"SystemExit: no entry for: {pred}")
        sys.exit(1)
    return hits

# League IDs
L_SUPER8 = "b328a4cf-0105-4c07-ba79-11baae8a709d"
L_BALLISTIC = "b328a4cf-0105-4c07-ba79-11baae8a709d"
L_BALLISTIC_ACADEMY = "003ef791-c918-4a92-b4c6-e913a6e8df81"
L_LIONS = "01a7333b-74a9-43c2-a4ca-95bb38ba98a8"

def prof(league):
    return next(q for q in body if 'profile-card' in q['path'] and q['q'].get('clubId') == league)

def gps(league):
    return [
        q for q in body 
        if ('getPlayerBattingStats' in q['path'] or 'getPlayerBowlingStats' in q['path'])
        and q['q'].get('leagueId') == league
    ]

def gmm(league):
    return next(
        q for q in body 
        if 'getAllMatchWiseStats' in q['path'] and q['q'].get('leagueId') == league
    )

def _sid(q):
    return q['q'].get('series', None)

def mlr(league, series, type_=None):
    return [
        q for q in body 
        if q['path'].endswith('sub') and 'match-level-records' in q['path']
        and q['q'].get('leagueId') == league 
        and (series is None or q['q'].get('series') == series)
    ]

def insight(league, kind):
    # kind in ['batting', 'bowling']
    return [
        q for q in body 
        if f'/core/public/player/{kind}' in q['path'] 
        and q['q'].get('leagueId') == league
    ]

def grouped(league, series_type, stats_type):
    return [
        q for q in body 
        if 'grouped-stats' in q['path'] 
        and q['q'].get('clubId') == league 
        and q['q'].get('seriesType') == series_type
    ]

# --- DB tables ---

def parse_do_tables(text):
    out = []
    for m in re.finditer(r'<table[^>]*>(.*?)</table>', text, re.S):
        tbl = m.group(1)
        rows = []
        for tr in re.finditer(r'<tr[^>]*>(.*?)</tr>', tbl, re.S):
            cells = [html.unescape(re.sub(r'<[^>]+>', '', td)).strip() for td in re.finditer(r'<td[^>]*>(.*?)</td>', tr, re.S)]
            if cells:
                rows.append(cells)
        if rows:
            out.append(rows)
    return out

def _num(f, val, _zero_with_no_outs=False, outs=None):
    if val in ('-', '', None):
        return None
    try:
        val = str(val).replace('*', '').strip()
        if _zero_with_no_outs and outs == 0 and float(val) == 0:
            return None
        return f(val)
    except ValueError:
        return None

def bat_row(cells):
    # Series | Matches | Inns | NO | Runs | Balls | Ave | SR | HS | 100s | 50s | 20s | 4s | 6s
    return {
        'series': cells[0],
        'matches': int(cells[1]),
        'innings': int(cells[2]),
        'notOuts': int(cells[3]),
        'runsScored': int(cells[4]),
        'ballsFaced': int(cells[5]),
        'average': _num(float, cells[6]),
        'strikeRate': _num(float, cells[7]),
        'highestScore': cells[8],
        'hundreds': int(cells[9]),
        'fifties': int(cells[10]),
        'twenties': int(cells[11]),
        'fours': int(cells[12]),
        'sixes': int(cells[13])
    }

def bowl_row(cells, full=False):
    # Series | Mats | Inns | Overs | Runs | Wkts | Bbf | Ave | Econ | SR | 5w | 10w | Wides | Catches
    d = {
        'series': cells[0],
        'matches': int(cells[1]),
        'innings': int(cells[2]),
        'overs': float(cells[3]),
        'runs': int(cells[4]),
        'wickets': int(cells[5]),
        'bestBowling': cells[6],
        'average': _num(float, cells[7]),
        'economy': _num(float, cells[8]),
        'strikeRate': _num(float, cells[9]),
        'fiveWickets': int(cells[10])
    }
    if full:
        d.update({
            'tenWickets': int(cells[11]),
            'wides': int(cells[12]),
            'catches': int(cells[13])
        })
    return d

# --- player card ---

def player_card(b):
    card = b['playerProfile']
    player = {
        'name': card['name'],
        'playerRole': card['playerRole'],
        'battingStyle': card['battingStyle'],
        'bowlingStyle': card['bowlingStyle'],
        'jerseyNumber': card.get('jerseyNumber'),
        'runs': card['runs'],
        'matches': card['matches'],
        'wickets': card['wickets']
    }
    return player

# --- clubs ---

BAT_KEYS = ['teamName', 'seriesType', 'matches', 'innings', 'runsScored', 'ballsFaced', 
            'highestScore', 'average', 'strikeRate', 'fours', 'sixers', 'fifties', 'hundreds']
BOWL_KEYS = ['teamName', 'seriesType', 'matches', 'innings', 'wickets', 'overs', 'economy', 'catches']

def club_entry(name, city, bat_row, bowl_row):
    return {
        'club': name,
        'city': city,
        'batting': [bat_row] if bat_row else [],
        'bowling': [bowl_row] if bowl_row else []
    }

# --- per-league sections ---

AGG_KEYS = ['matches', 'innings', 'notOuts', 'runsScored', 'ballsFaced', 'average', 
            'strikeRate', 'highestScore', 'hundreds', 'fifties', 'fours', 'sixes']

def agg(row):
    return {k: row.get(k) for k in AGG_KEYS}

def yearwise(row, with_my=True):
    res = {
        'year': row['year'],
        'matches': row['matches'],
        'runs': row['runsScored'],
        'hs': row['highestScore']
    }
    if with_my:
        res['avg'] = row.get('average')
        res['sr'] = row.get('strikeRate')
    return res

def matchwise(league, series_name):
    # Extracts match level list from matchwise JSON responses
    pass

# Main assembly script block begins here ...
