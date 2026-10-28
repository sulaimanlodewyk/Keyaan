#!/usr/bin/env python3
"""
stats.py - Extract cricket stats from CricClubs exports.

Usage:
  python3 stats.py                   # Print markdown summary to stdout
  python3 keyaan_stats.py --write    # Save keyaan_stats.md
  python3 keyaan_stats.py --html     # Save keyaan_stats.html (self-contained page)

Data source: keyaan_cricclubs_stats.json in the same directory.
If updating with new CricClubs network HAR data, run DevTools -> Network ->
Export HAR, save it somewhere, and run a script to re-extract into the JSON.
"""

import sys
import os
import json
import re
import html
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'keyaan_cricclubs_stats.json')
OUT_MD = os.path.join(HERE, 'keyaan_stats.md')
OUT_HTML = os.path.join(HERE, 'keyaan_stats.html')

# Leagures to feature with full match-by-match detail (in display order)
FEATURED = [
    ('lionsschools', 'Lions Schools (Crawford Sandton)'),
    ('ballistic', 'Ballistic Cricket League (100-ball, Sandton Tigers Blaze)'),
    ('montrose', 'Montrose Night Challenge (Bryneven)'),
    ('super8', 'Super 8 Easter Cup 2026 (U9A U11, Ten10)'),
    ('steyncity', 'Steyn City (one-off, U9 2024)'),
]

# Club names already covered by the featured sections above
SKIP_CLUBS = [
    'Lions School League 2026', 'Alfeceo Dream Big Montrose Night Challenge',
    'Super 8 Easter Cup 2026', 'Steyn City School'
]

# Profile-card sections that get their own series-breakdown section
SERIES_CLUBS = [
    'cover drive cricket school', 'national premier league south africa',
    'delfos junior 2020', 'randburg cricket club juniors', 'dj t10',
    'lions club league 2026/27'
]


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def us_date(s):
    if not s:
        return (9999, 99, 99)
    try:
        m, d, y = s.split('/')
        return (int(y), int(m), int(d))
    except ValueError:
        return (9999, 99, 99)


def fmt_date(s):
    y, m, d = us_date(s)
    return f"{y:04d}-{m:02d}-{d:02d}"


def dismissal_text(o):
    dis = o.get('dismissedBy')
    name = o.get('dismissedByName')
    ret = f"r.o. ({name})" if name else 'r.o.'
    if not name:
        return 'retired hurt / not out'
    return f"b/{name}"


# Columns shared by all per-game tables (Cover Drive style, with dismissal appended)
PER_GAME_HDRS = ['Date', 'Opponent', 'Res', 'R', 'B', 'SR', '4s', '6s', 'Dismissal']


def per_game_cells(m):
    """
    m = {R, B, SR, 4s, 6s, Dismissal} for one matchwise row, covering DNB and
    both data shapes (records-page row: R/SR/4s/6s; match-level rows: dismissal).***
    """
    dnb = m.get('dnb') or m.get('runs') is None
    if dnb:
        return ['DNB', '', '', '', '', '']
    m_runs = m.get('runs')
    dis = dismissal_text(m) if 'dismissedBy' in m or 'outType' in m else ''
    m_sr = str(round(m.get('strikeRate', 0), 1)) if m.get('strikeRate') else ''
    return [
        m_runs, m.get('balls', ''), m_sr, m.get('fours', ''), m.get('sixes', ''), dis
    ]


def bat_line(o):
    return {
        'm': o.get('matches', 1), 'i': o.get('innings', 1),
        'r': o.get('runsScored', 0), 'b': o.get('ballsFaced', 0),
        'avg': o.get('average', 0.0), 'sr': o.get('strikeRate', 0.0),
        'hs': str(o.get('highestScore', '0')), 'fifties': o.get('fifties', 0),
        'hundreds': o.get('hundreds', 0)
    }


def collect():
    with open(SRC) as f:
        d = json.load(f)
    p = d['player']
    featured = []
    for key, label in FEATURED:
        mon = d.get('montroseNightChallenge_bySeries')
        if key == 'montrose' and mon:
            featured.append({'key': key, 'label': label, 'montrose': mon})
            continue
        lg = d.get(key)
        if lg:
            featured.append({
                'key': key,
                'label': label,
                'batting': lg.get('batting', {}),
                'matchwise': sorted(lg.get('matchwise', []), key=lambda x: us_date(x.get('date')))
            })

    others = []
    series_recs = []
    for c in d.get('clubs', []):
        if c['club'].strip() in SKIP_CLUBS or c['club'].strip().lower() in SERIES_CLUBS:
            continue
        for b in c.get('batting', []):
            others.append({
                'club': c['club'].strip(), 'team': b.get('teamName', ''),
                'format': b.get('seriesType', ''), 'm': b.get('matches'),
                'i': b.get('innings'), 'r': b.get('runsScored'), 'b': b.get('ballsFaced'),
                'avg': b.get('average'), 'sr': b.get('strikeRate'),
                'hs': b.get('highestScore')
            })

    others.sort(key=lambda r: (r['r'] or 0), reverse=True)
    return {
        'player': p, 'featured': featured, 'others': others,
        'seriesRecords': d.get('seriesRecords'),
        'insights': d.get('insights'),
        'lionsSchools': d.get('insights_lionsLeague')
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def md_table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |']
    out.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)


def render_md(d):
    p, a = d['player'], []
    a.append(f"# {p.get('name', '')} - Cricket Stats")
    a.append(
        f"**Role:** {p.get('playerRole', '')} | **Batting:** {p.get('battingStyle', '')} | "
        f"**Bowling:** {p.get('bowlingStyle', '')} | **Jersey:** #{p.get('jerseyNumber', '')}\n"
        f"**Current Team:** {p.get('currentTeam', '')}\n"
        f"**Totals:** {p.get('runs', '')} runs | {p.get('matches', '')} matches | {p.get('wickets', '')} wickets\n"
    )

    for lg in d['featured']:
        a.append(f"## {lg['label']}")
        if 'montrose' in lg:
            m = lg['montrose']
            rows = [[
                s, m[s]['matches'], m[s]['runs'], m[s]['balls'], m[s]['avg'],
                m[s]['sr'], m[s]['hs'], m[s]['4s'], m[s]['6s']
            ] for s in m if s != 'note']
            a.append(md_table(['Series', 'M', 'R', 'B', 'Avg', 'SR', 'HS', '4s', '6s'], rows))
            if 'note' in m:
                a.append(f"\n*{m['note']}*\n")
            continue

        parts = []
        for tgt, agg in lg['batting'].items():
            if fmt_date(str(tgt)).startswith('by_year'):
                parts.append(f"{tgt}: {agg['r']} runs ({agg['i']} inn, avg {agg['avg']}, HS {agg['hs']})")
        if parts:
            a.append("\n" + "; ".join(parts))

        if isinstance(lg.get('matchwise'), list) and lg['matchwise']:
            rows = []
            for m in lg['matchwise']:
                res = m.get('result', '')
                rows.append([m.get('date', ''), m.get('vs', ''), res] + per_game_cells(m))
            a.append(md_table(PER_GAME_HDRS, rows))

    # Series breakdown for other clubs
    if d['seriesRecords']:
        a.append("\n## Series Breakdown (other clubs)")
        for club, info in d['seriesRecords'].items():
            a.append(f"\n### {info['club']}")
            def cell(u, v): return u if u is not None else v
            rows = []
            for s in info['series']:
                rows.append([
                    s['series'], s['r'], s['i'], s['runs'], s['b'], cell(s['avg'], ''),
                    cell(s['sr'], ''), s['hs'], s['4s'], s['6s']
                ])
            a.append(md_table(['Series', 'N', 'R', 'B', 'Avg', 'SR', 'HS', '4s', '6s'], rows))
            
            if 'bowling' in info and info['bowling']:
                if info['bowling'].get('wickets') != 0:
                    a.append(f"\n*Bowling: {info['bowling']}*")
            if info.get('bowling') and info['bowling'].get('overs'):
                # (bowling) overs across all series (no wickets); also keeps wicket_-1
                pass

            if 'matchwise' in info:
                groups = {}
                for m in info['matchwise']:
                    groups.setdefault(m.get('series', ''), []).append(m)
                for name, ms in groups.items():
                    a.append(f"\n**{name}**")
                    ms = sorted(ms, key=lambda m: us_date(m.get('date', '')))
                    rows = [[m.get('date', ''), m.get('vs', ''), m.get('result', '')] + per_game_cells(m) for m in ms]
                    a.append(md_table(PER_GAME_HDRS, rows))

            if 'matchwise_note' in info:
                a.append(f"\n*{info['matchwise_note']}*\n")

    if d['others']:
        a.append("\n## Other Competitions (aggregates)")
        rows = [[
            o['club'], o['team'], o['format'], o['m'], o['r'], o['b'],
            o['avg'], o['sr'], o['hs']
        ] for o in d['others']]
        a.append(md_table(['Club', 'Team', 'Format', 'M', 'R', 'B', 'Avg', 'SR', 'HS'], rows))

    ins = d['insights']
    if ins:
        a.append("\n## Insights")
        a.append("\n### Insights (Lions Schools view)")
        dt = ins.get('dismissalTypes', {})
        if dt:
            a.append("**Dismissal Types:** " + ", ".join(f"{k}: {v}" for k, v in dt.items()))
        bands = ins.get('outByScoreBand')
        if bands:
            a.append("\n**Score at dismissal:** " + "; ".join(f"{v} ({k})" for k, v in bands.items()))
        lines = ins.get('runsPerBallsFaced')
        if lines:
            a.append("\n**Runs per ball faced:** " + ", ".join(f"{r} ({b}b)" for r, b in lines))

    lg = d.get('lionsSchools')
    if lg:
        a.append("\n### Keeper & Bowling (Lions Schools)")
        fld = lg.get('fielding')
        if fld:
            st = fld.get('stumpings', {})
            st_str = ", ".join(f"{k}: {v}" for k, v in st.items())
            a.append(f"**Fielding/Stumpings:** {st_str}")
        bw = lg.get('bowling')
        if bw:
            a.append(
                f"**Bowling:** {bw.get('balls', 0)}b, {bw.get('wickets', 0)}w, "
                f"{bw.get('runs', 0)}r ({bw.get('wides', 0)}wides, {bw.get('noballs', 0)} no-balls)"
            )

    a.append(f"\n---\n*Source: CricClubs network exports, parsed {date.today().isoformat()}.*")
    return '\n'.join(a)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

CSS = """
:root { --bg: #0f172a; --card: #1e293b; --line: #334155; --txt: #f8fafc; --dim: #94a3b8; --acc: #10b981; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { margin: 0; padding: 24px 16px; background: var(--bg); color: var(--txt);
       font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }
.wrap { max-width: 1000px; margin: 0 auto; }
header { text-align: center; margin-bottom: 24px; }
h1 { font-size: 1.75rem; font-weight: 800; color: #fff; }
.sub { color: var(--dim); font-size: 0.9rem; margin-top: 4px; }
.kpis { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 16px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 12px 20px; text-align: center; min-width: 110px; }
.kpi .val { font-size: 1.25rem; font-weight: 800; color: var(--acc); }
.kpi .lbl { color: var(--dim); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; }
section { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 20px; margin-bottom: 24px; }
h2 { margin: 0 0 12px; font-size: 1.2rem; border-bottom: 1px solid var(--line); padding-bottom: 8px; }
h3 { margin: 16px 0 8px; font-size: 1rem; color: var(--dim); }
.yr { color: var(--dim); font-size: 0.85rem; margin-bottom: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
th { color: var(--dim); font-size: 0.75rem; text-transform: uppercase; letter-spacing: .05em; padding: 8px; border-bottom: 1px solid var(--line); }
td { padding: 8px; border-bottom: 1px solid #2d3748; }
tr:hover td { background: #243144; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr.grp td { background: var(--bg); color: var(--dim); font-size: 0.75rem; font-weight: 600; }
.note { color: var(--dim); font-size: 0.8rem; font-style: italic; margin-top: 8px; }
.scroll { max-height: 420px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; }
footer { text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 32px; }
"""


def el(s):
    return html.escape(str(s))


def render_html(d):
    p = d['player']
    out = []
    out.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{el(p.get('name', 'Stats'))} - Cricket Stats</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>{el(p.get('name', ''))}</h1>
  <div class="sub">{el(p.get('playerRole', ''))} &bull; {el(p.get('battingStyle', ''))} &bull; {el(p.get('bowlingStyle', ''))} &bull; #{el(p.get('jerseyNumber', ''))}</div>
  <div class="sub">Current Team: {el(p.get('currentTeam', ''))}</div>
  <div class="kpis">
    <div class="kpi"><span class="val">{el(p.get('matches', ''))}</span><br><span class="lbl">Matches</span></div>
    <div class="kpi"><span class="val">{el(p.get('runs', ''))}</span><br><span class="lbl">Runs</span></div>
    <div class="kpi"><span class="val">{el(p.get('wickets', ''))}</span><br><span class="lbl">Wickets</span></div>
  </div>
</header>
""")

    for lg in d['featured']:
        out.append(f'<section>\n<h2>{el(lg["label"])}</h2>')
        if 'montrose' in lg:
            m = lg['montrose']
            out.append('<table><thead><tr><th>Series</th><th class="num">M</th><th class="num">R</th><th class="num">B</th><th class="num">Avg</th><th class="num">SR</th><th class="num">HS</th><th class="num">4s</th><th class="num">6s</th></tr></thead><tbody>')
            for s in m:
                if s == 'note': continue
                out.append(f'<tr><td>{el(s)}</td><td class="num">{el(m[s]["matches"])}</td><td class="num">{el(m[s]["runs"])}</td><td class="num">{el(m[s]["balls"])}</td><td class="num">{el(m[s]["avg"])}</td><td class="num">{el(m[s]["sr"])}</td><td class="num">{el(m[s]["hs"])}</td><td class="num">{el(m[s]["4s"])}</td><td class="num">{el(m[s]["6s"])}</td></tr>')
            out.append('</tbody></table>')
            if 'note' in m:
                out.append(f'<div class="note">{el(m["note"])}</div>')
            out.append('section>\n')
            continue

        parts = []
        for tgt, agg in lg['batting'].items():
            if fmt_date(str(tgt)).startswith('by_year'):
                parts.append(f"<b>{el(tgt)}:</b> {el(agg['r'])} runs ({el(agg['i'])} inn, avg {el(agg['avg'])}, HS {el(agg['hs'])})")
        if parts:
            out.append(f'<div class="yr">{" &bull; ".join(parts)}</div>')

        if isinstance(lg.get('matchwise'), list) and lg['matchwise']:
            out.append('<div class="scroll"><table><thead><tr><th>Date</th><th>VS</th><th>Result</th><th class="num">R</th><th class="num">B</th><th class="num">SR</th><th class="num">4s</th><th class="num">6s</th><th>Dismissal</th></tr></thead><tbody>')
            for m in lg['matchwise']:
                res = m.get('result', '')
                res_cls = ' style="color:var(--acc)"' if res == 'W' else ' style="color:var(--dim)"' if res == 'L' else ''
                c = per_game_cells(m)
                out.append(f'<tr><td>{el(m.get("date",""))}</td><td>{el(m.get("vs",""))}</td><td{res_cls}>{el(res)}</td><td class="num"><b>{el(c[0])}</b></td><td class="num">{el(c[1])}</td><td class="num">{el(c[2])}</td><td class="num">{el(c[3])}</td><td class="num">{el(c[4])}</td><td>{el(c[5])}</td></tr>')
            out.append('</tbody></table></div>')
        out.append('</section>\n')

    # Series records section
    if d['seriesRecords']:
        out.append('<section>\n<h2>Series Records (other clubs)</h2>')
        for club, info in d['seriesRecords'].items():
            out.append(f'<h3>{el(info["club"])}</h3>')
            out.append('<table><thead><tr><th>Series</th><th class="num">M</th><th class="num">R</th><th class="num">B</th><th class="num">Avg</th><th class="num">SR</th><th class="num">HS</th><th class="num">4s</th><th class="num">6s</th></tr></thead><tbody>')
            for s in info['series']:
                out.append(f'<tr><td>{el(s["series"])}</td><td class="num">{el(s["r"])}</td><td class="num">{el(s["i"])}</td><td class="num">{el(s["runs"])}</td><td class="num">{el(s["b"])}</td><td class="num">{el(s["avg"] or "")}</td><td class="num">{el(s["sr"] or "")}</td><td class="num">{el(s["hs"])}</td><td class="num">{el(s["4s"])}</td><td class="num">{el(s["6s"])}</td></tr>')
            out.append('</tbody></table>')

            if 'matchwise' in info:
                out.append('<div class="scroll" style="margin-top:12px;"><table><thead><tr><th>Date</th><th>VS</th><th>Result</th><th class="num">R</th><th class="num">B</th><th class="num">SR</th><th class="num">4s</th><th class="num">6s</th><th>Dismissal</th></tr></thead><tbody>')
                groups = {}
                for m in info['matchwise']:
                    groups.setdefault(m.get('series', ''), []).append(m)
                for name, ms in groups.items():
                    out.append(f'<tr class="grp"><td colspan="9">{el(name)}</td></tr>')
                    ms = sorted(ms, key=lambda m: us_date(m.get('date', '')))
                    for m in ms:
                        res = m.get('result', '')
                        c = per_game_cells(m)
                        out.append(f'<tr><td>{el(m.get("date",""))}</td><td>{el(m.get("vs",""))}</td><td>{el(res)}</td><td class="num"><b>{el(c[0])}</b></td><td class="num">{el(c[1])}</td><td class="num">{el(c[2])}</td><td class="num">{el(c[3])}</td><td class="num">{el(c[4])}</td><td>{el(c[5])}</td></tr>')
                out.append('</tbody></table></div>')
        out.append('</section>\n')

    if d['others']:
        out.append('<section>\n<h2>Other Competitions</h2>')
        out.append('<table><thead><tr><th>Club</th><th>Team</th><th>Format</th><th class="num">M</th><th class="num">R</th><th class="num">B</th><th class="num">Avg</th><th class="num">SR</th><th class="num">HS</th></tr></thead><tbody>')
        for o in d['others']:
            out.append(f'<tr><td>{el(o["club"])}</td><td>{el(o["team"])}</td><td>{el(o["format"])}</td><td class="num">{el(o["m"])}</td><td class="num">{el(o["r"])}</td><td class="num">{el(o["b"])}</td><td class="num">{el(o["avg"])}</td><td class="num">{el(o["sr"])}</td><td class="num">{el(o["hs"])}</td></tr>')
        out.append('</tbody></table></section>\n')

    ins = d['insights']
    if ins:
        out.append('<section>\n<h2>Insights</h2>')
        dt = ins.get('dismissalTypes', {})
        if dt:
            out.append(f'<p><b>Dismissal Types:</b> {el(", ".join(f"{k}: {v}" for k, v in dt.items()))}</p>')
        out.append('</section>\n')

    out.append(f'<footer>CricClubs network exports &bull; parsed {date.today().isoformat()}</footer>')
    out.append('</div></body></html>')
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    d = collect()
    if '--write' in sys.argv:
        m = render_md(d)
        with open(OUT_MD, 'w') as f:
            f.write(m)
        print(f"Wrote {OUT_MD}")
    elif '--html' in sys.argv:
        h = render_html(d)
        with open(OUT_HTML, 'w') as f:
            f.write(h)
        print(f"Wrote {OUT_HTML}")
    else:
        sys.stdout.write(render_md(d) + '\n')


if __name__ == '__main__':
    main()
```

### Script Capabilities & Output Options:
1. **Default Mode (`python3 stats.py`)**: Parses the CricClubs output JSON data and prints a structured Markdown report to `stdout`.
2. **Write Markdown (`python3 stats.py --write`)**: Saves the generated Markdown report directly to `keyaan_stats.md`.
3. **Generate HTML (`python3 stats.py --html`)**: Generates a styled, responsive standalone HTML file saved to `keyaan_stats.html`.
