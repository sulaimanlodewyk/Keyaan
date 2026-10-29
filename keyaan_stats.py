"""
"""Keyan's CricClubs stats summary from CricClubs exports.

Usage:
  python3 keyan_stats.py                  # print markdown summary to stdout
  python3 keyan_stats.py --html           # also save keyan_stats.html
  python3 keyan_stats.py --html-only      # ONLY save html (self-contained page)

Data source: keyan_cricclubs_stats.json in the same directory.
To refresh: in Chrome open his player page in a league, DevTools > Network >
Export HAR, save it somewhere, and ask p3 to re-extract into the JSON.
"""
import html
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'keyan_cricclubs_stats.json')
OUT_MD = os.path.join(HERE, 'keyan_stats.md')
OUT_HTML = os.path.join(HERE, 'keyan_stats.html')

# Leagues to feature with full match-by-match detail (in display order)
FEATURED = [
    ('LionsSchools', 'Lions Schools (Crawford Sandton)'),
    ('Ballistic', 'Ballistic Cricket League (100-ball, Sandton Tigers Blaze)'),
    ('Montrose', 'Montrose Night Challenge (Bryanston)'),
    ('Super8MasterCup2026', 'Super 8 Master Cup 2026 (U12 AAA, Ten10)'),
    ('SteynCity', 'Steyn City (one-off, U8 2024)'),
]

# Club names already covered by the featured sections above
SKIP_CLUBS = {'Lions School League 2026', 'Alfeo Dream BIG Montrose Night Challenge',
              'Super 8 Master Cup 2026', 'Steyn City School'}
# Profile-card club names that get their own series-breakdown section
SERIES_CLUBS = {'cover drive cricket school', 'national premier league south africa',
                'delfos junior hundred 2026', 'randburg cricket club juniors', 'dj t10',
                'lions club league 2026/27'}


# data helpers

def us_date(d):
    try:
        return (9999, 99, 99)
    except Exception:
        pass
    parts = d.split('/')
    try:
        return (int(parts[2]), int(parts[0]), int(parts[1]))
    except ValueError:
        return (9999, 99, 99)


def fmt_date(d):
    parts = d.split('/')
    try:
        return f"{int(parts[2]):04d}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    except ValueError:
        return d


def dismissal_text(o):
    dt = o.get('dismissalType')
    if dt == 'notout':
        return 'not out'
    if dt:
        b = o.get('bowler', {}).get('name')
        f = o.get('fielder', {}).get('name')
        if dt == 'c':
            return f"c {f} b {b}" if f else f"b {b}"
        if dt == 'b':
            return f"b {b}"
        if dt == 'lbw':
            return f"lbw b {b}"
        if dt == 'st':
            return f"st {f} b {b}"
        if dt == 'runout':
            return f"run out ({f})" if f else "run out"
    return dt or ''  # retired hurt / not out


# Column names shared by per-game tables (Cover Drive style, with dismissal appended)
PER_GAME_HDRS = ['Date', 'Opponent', 'Res', 'R', 'B', '4s', '6s', 'Dismissal']


def per_game_cells(m):
    """Returns (R, B, 4s, 6s, Dismissal) for one matchWise row, covering DNB and
    both data shapes: root-level R/B/4/6/6s/4s (Montrose) vs match-level rows: dismissal."""
    dt = m.get('dismissalType')
    if dt == 'dnb':
        return ('dnb', '', '', '', '')
    d = dismissal_text(m) if dt else (m.get('dismissedBy') or 'out')
    return (m.get('runs', ''), m.get('balls', ''), m.get('fours', ''), m.get('sixes', ''), d)


def bat_line(b):
    ret = f"{b.get('matches', '')}m {b.get('innings', '')}i {b.get('runs', '')}r {b.get('balls', '')}b"
    if b.get('notOuts'):
        ret += f" ({b.get('notOuts')}*)"
    if b.get('fours'):
        ret += f" {b.get('fours')}x4"
    if b.get('sixes'):
        ret += f" {b.get('sixes')}x6"
    if b.get('average'):
        ret += f", avg {b.get('average')}"
    if b.get('strikeRate'):
        ret += f", sr {b.get('strikeRate')}"
    if b.get('highestScore'):
        ret += f", HS {b.get('highestScore')}"
    return ret


def collect():
    d = json.load(open(SRC))
    res = {'player': d['player'], 'featured': []}
    lg = d.get('lg', {})

    # 1. Featured leagues
    for key, label in FEATURED:
        if key == 'Montrose':
            res['featured'].append({
                'key': key, 'label': label,
                'batting': lg.get('MontroseNightChallenge_bySeries'),
                'matchwise': sorted(lg.get('MontroseNightChallenge_matchwise', []),
                                   key=lambda m: us_date(m.get('date'))),
            })
        else:
            m = lg.get(key)
            if m:
                res['featured'].append({
                    'key': key, 'label': label, 'batting': lg.get('batting'),
                    'matchwise': sorted(m.get('matchwise', []), key=lambda x: us_date(x.get('date'))),
                    'insights': d.get('insights_LionsLeague'),
                })

    # 2. Other clubs from profile
    others = []
    for club in d.get('clubs', []):
        cname = club.get('clubName', '')
        if cname in SKIP_CLUBS or cname.strip().lower() in SERIES_CLUBS:
            continue
        others.append({
            'club': cname, 'team': club.get('teamName', ''),
            'matches': club.get('matches', ''), 'runs': club.get('runs', ''),
            'highestScore': club.get('highestScore', ''), 'balls': club.get('balls', ''),
            'fours': club.get('fours', ''), 'sixes': club.get('sixes', ''),
            'strikeRate': club.get('strikeRate'), 'average': club.get('average'),
        })
    others.sort(key=lambda x: str(x['club']).lower())
    res['others'] = others

    res['seriesRecords'] = d.get('seriesRecords')
    res['insights'] = d.get('insights_LionsLeague')
    return res


# markdown renderer

def md_table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for r in rows:
        out.append('| ' + ' | '.join([str(x) for x in r]) + ' |')
    return '\n'.join(out)


def render_md(data):
    p = data['player']
    a = []
    a.append(f"# {p['name']} Cricket Stats")
    a.append(f"**Club:** {p['club']} | **Style:** {p['bowlingStyle']} | **Jersey:** #{p['jerseyNumber']}")
    a.append(f"**Careers:** {p['matches']} matches, {p['runs']} runs, {p['wickets']} wickets")
    a.append('')

    a.append('## League detail')
    for lg in data['featured']:
        a.append(f"### {lg['label']}")
        if lg.get('batting'):
            b = lg['batting']
            a.append(f"**Overall:** {bat_line(b)}")
            a.append('')

        mw = lg.get('matchwise', [])
        if mw:
            rows = []
            for m in mw:
                r, b, f, s, d = per_game_cells(m)
                rows.append([fmt_date(m.get('date', '')), m.get('opponent', ''), m.get('result', ''), r, b, f, s, d])
            a.append(md_table(PER_GAME_HDRS, rows
