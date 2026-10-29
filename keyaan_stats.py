"""
Keyan's CricClubs stats summary from CricClubs exports.

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
            a.append(md_table(PER_GAME_HDRS, rows))
            a.append('')

        if lg.get('notes'):
            a.append(f"> {lg['notes']}")
            a.append('')

    for fmt, agg in lg.get('batting', {}).items():
        if isinstance(agg, dict):
            parts = [
                f"{agg.get('matches', '')}m", f"{agg.get('runs', '')}r", f"{agg.get('balls', '')}b",
                f"{agg.get('fours', '')}x4", f"{agg.get('sixes', '')}x6",
                f"avg {agg.get('average', '')}", f"sr {agg.get('strikeRate', '')}", f"HS {agg.get('highestScore', '')}"
            ]
            a.append(f"- **{fmt}:** " + ", ".join(parts))
            a.append('')

    if lg.get('matchwise'):
        rows = []
        for m in lg['matchwise']:
            r, b, f, s, d = per_game_cells(m)
            rows.append([fmt_date(m.get('date', '')), m.get('opponent', ''), m.get('result', ''), r, b, f, s, d])
        a.append(md_table(PER_GAME_HDRS, rows))
        a.append('')

    # series breakdown for other clubs
    sd = data.get('seriesRecords')
    if sd:
        a.append('## Series breakdown (other clubs)')
        for club, info in sd.items():
            if info:
                a.append(f"### {club}")
                rows = []
                for s in info.get('series', []):
                    r, b, f, s_six, avg = s.get('runs'), s.get('balls'), s.get('fours'), s.get('sixes'), s.get('avg')
                    rows.append([s.get('series'), s.get('matches'), r, b, f, s_six, avg])
                a.append(md_table(['Series', 'M', 'R', 'B', '4s', '6s', 'Avg'], rows))
                
                # Bowling info if available
                if info.get('bowling') and info['bowling'].get('wickets') != '0':
                    binfo = info['bowling']
                    overs = sum(float(x) for x in binfo.get('overs', []))
                    a.append(f"**Bowling:** {overs:.1f} overs across all series (no wickets); also keeps wicket.")
                
                mw = info.get('matchWise', [])
                if mw:
                    rows = []
                    groups = {}
                    for m in mw:
                        groups.setdefault(m.get('series', ''), []).append(m)
                    
                    for sname, mlist in groups.items():
                        sorted_m = sorted(mlist, key=lambda x: us_date(x.get('date')), reverse=True)
                        for m in sorted_m:
                            r, b, f, s_six, d = per_game_cells(m)
                            rows.append([fmt_date(m.get('date', '')), m.get('opponent', ''), m.get('result', ''), r, b, f, s_six, d])
                    a.append(md_table(PER_GAME_HDRS, rows))
                    a.append('')
                else:
                    a.append('> CoverDrive/cricclubs matchWise records pending - needs a Cover Drive match-level HAR export to fill this table.')
                a.append('')

    if data.get('others'):
        a.append('## Other competitions (aggregates)')
        rows = []
        for o in data['others']:
            rows.append([
                o['club'], o['team'], o['matches'], o['runs'], o['balls'],
                o['fours'], o['sixes'], o['strikeRate'], o['average']
            ])
        a.append(md_table(['Club', 'Team', 'M', 'R', 'B', '4s', '6s', 'SR', 'Avg'], rows))
        a.append('')

    ins = data.get('insights')
    if ins:
        a.append('## Insights (Lions Schools view)')
        a.append(f"- **Dismissal types:** {', '.join([f'{k}: {v}' for k, v in ins.get('dismissalTypes', {}).items()])}")
        a.append(f"- **Runs by score-band:** {', '.join([f'{k}: {v}' for k, v in ins.get('outsByScoreBand', {}).items()])}")
        rb = ins.get('runsPerBallPaced', {})
        a.append(f"- **Runs per ball pace:** dot={rb.get('dot')}, 1s={rb.get('ones')}, 2s={rb.get('twos')}, 4s={rb.get('fours')}, 6s={rb.get('sixes')}")
        a.append('')

        # keeper & bowling (Lions Schools)
        lk = data.get('LionsSchools', {})
        if lk.get('fielding'):
            a.append('### Keeper & bowling (Lions Schools)')
            f = lk['fielding']
            stump = f.get('stumping')
            a.append(f"- **Wicketkeeping/fielding:** {stump} stumping(s); takings by series - {', '.join(f.get('series', []))}")
            if lk.get('bowling'):
                bw = lk['bowling']
                a.append(f"- **Bowling:** {bw.get('overs')} overs, {bw.get('wickets')} wickets, {bw.get('runs')} runs conceded")
            a.append('')

    a.append(f"*Footer: CricClubs network exports, parsed {date.today().isoformat()}*")
    return '\n'.join(a)


# html renderer

CSS = """
:root { --bg: #0f1428; --card: #1a223d; --line: #2a3358; --accent: #3b82f6; --text: #e2e8f0; --dim: #94a3b8; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       line-height: 1.5; padding: 20px; max-width: 1200px; margin: 0 auto; }
header { text-align: center; margin-bottom: 20px; }
h1 { font-size: 2rem; color: #fff; margin-bottom: 4px; }
.sub { color: var(--dim); font-size: 0.95rem; }
.kpis { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 10px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 8px 16px; text-align: center; min-width: 100px; }
.kpi .num { font-size: 1.3rem; font-weight: bold; color: var(--accent); }
.kpi .lbl { font-size: 0.75rem; color: var(--dim); text-transform: uppercase; letter-spacing: 0.05em; }
section { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 18px; margin-bottom: 20px; }
h2 { font-size: 1.25rem; margin-bottom: 12px; color: #fff; border-bottom: 1px solid var(--line); padding-bottom: 8px; }
h3 { font-size: 1rem; color: var(--accent); margin: 12px 0 6px 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.875rem; margin-top: 8px; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--line); }
th { background: #141c33; color: var(--dim); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; position: sticky; top: 0; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
tr:hover td { background: #212b4a; }
.res-W { color: #4ade80; font-weight: bold; }
.res-L { color: #f87171; }
tr.td-g { background(card-val): #0e2a1e; color: var(--text); font-size: 0.85rem; font-weight: 600; }
tr.td-r { background(card-val): #2a0e0e; color: var(--text); font-size: 0.85rem; font-weight: 600; }
.notes { background: #141c33; border-left: 3px solid var(--accent); padding: 8px 12px; border-radius: 0 6px 6px 0; font-size: 0.85rem; color: var(--dim); margin-top: 8px; }
.scroll-table { max-height: 400px; overflow-y: auto; border-radius: 6px; margin-top: 8px; }
@media print { body { background: #fff; color: #000; } section { background: #fff; border-color: #ccc; } th { background: #fff; } }
"""


def html_escape(s):
    return html.escape(str(s))


def render_html(d):
    out = []
    out.append("<!DOCTYPE html><html><head><meta charset='utf-8'>")
    out.append("<title>Cricket Stats</title><style>" + CSS + "</style></head><body>")

    p = d['player']
    out.append("<header><div class='wrap'>")
    out.append(f"<h1>{html_escape(p['name'])}</h1>")
    out.append(f"<div class='sub'>Club: {html_escape(p['club'])} | Style: {html_escape(p['bowlingStyle'])} | Jersey: #{p['jerseyNumber']}</div>")
    out.append("<div class='kpis'>")
    out.append(f"<div class='kpi'><div class='num'>{p['matches']}</div><div class='lbl'>Matches</div></div>")
    out.append(f"<div class='kpi'><div class='num'>{p['runs']}</div><div class='lbl'>Runs</div></div>")
    out.append(f"<div class='kpi'><div class='num'>{p['wickets']}</div><div class='lbl'>Wickets</div></div>")
    out.append("</div></div></header>")

    out.append("<section><h2>Featured Leagues</h2>")
    for lg in d['featured']:
        out.append(f"<h3>{html_escape(lg['label'])}</h3>")
        if lg.get('batting'):
            b = lg['batting']
            out.append(f"<p>{bat_line(b)}</p>")

        mw = lg.get('matchwise', [])
        if mw:
            out.append("<div class='scroll-table'><table><thead><tr>")
            for h in PER_GAME_HDRS:
                out.append(f"<th>{h}</th>")
            out.append("</tr></thead><tbody>")
            for m in mw:
                r, b, f, s, dismissal = per_game_cells(m)
                res_cls = f"res-{m.get('result', '')}" if m.get('result') in ('W', 'L') else ''
                out.append("<tr>")
                out.append(f"<td>{fmt_date(m.get('date', ''))}</td>")
                out.append(f"<td>{html_escape(m.get('opponent', ''))}</td>")
                out.append(f"<td class='{res_cls}'>{html_escape(m.get('result', ''))}</td>")
                out.append(f"<td class='num'>{r}</td>")
                out.append(f"<td class='num'>{b}</td>")
                out.append(f"<td class='num'>{f}</td>")
                out.append(f"<td class='num'>{s}</td>")
                out.append(f"<td>{html_escape(dismissal)}</td>")
                out.append("</tr>")
            out.append("</tbody></table></div>")

    for fmt, agg in lg.get('batting', {}).items():
        if isinstance(agg, dict):
            parts = [
                f"{agg.get('matches', '')}m", f"{agg.get('runs', '')}r", f"{agg.get('balls', '')}b",
                f"{agg.get('fours', '')}x4", f"{agg.get('sixes', '')}x6",
                f"avg {agg.get('average', '')}", f"sr {agg.get('strikeRate', '')}", f"HS {agg.get('highestScore', '')}"
            ]
            out.append(f"<p><b>{fmt}:</b> " + ", ".join(parts) + "</p>")

    if lg.get('matchwise'):
        out.append("<div class='scroll-table'><table><thead><tr>")
        for h in PER_GAME_HDRS:
            out.append(f"<th>{h}</th>")
        out.append("</tr></thead><tbody>")
        for m in lg['matchwise']:
            r, b, f, s, dismissal = per_game_cells(m)
            res_cls = f"res-{m.get('result', '')}" if m.get('result') in ('W', 'L') else ''
            out.append("<tr>")
            out.append(f"<td>{fmt_date(m.get('date', ''))}</td>")
            out.append(f"<td>{html_escape(m.get('opponent', ''))}</td>")
            out.append(f"<td class='{res_cls}'>{html_escape(m.get('result', ''))}</td>")
            out.append(f"<td class='num'>{r}</td>")
            out.append(f"<td class='num'>{b}</td>")
            out.append(f"<td class='num'>{f}</td>")
            out.append(f"<td class='num'>{s}</td>")
            out.append(f"<td>{html_escape(dismissal)}</td>")
            out.append("</tr>")
        out.append("</tbody></table></div>")

    # series records
    sd = d.get('seriesRecords')
    if sd:
        out.append("<section><h2>Series Records</h2>")
        for club, info in sd.items():
            if info:
                out.append(f"<h3>{html_escape(club)}</h3>")
                out.append("<div class='scroll-table'><table><thead><tr>")
                for h in ['Series', 'M', 'R', 'B', '4s', '6s', 'Avg']:
                    out.append(f"<th>{h}</th>")
                out.append("</tr></thead><tbody>")
                for s in info.get('series', []):
                    r, b, f, s_six, avg = s.get('runs'), s.get('balls'), s.get('fours'), s.get('sixes'), s.get('avg')
                    out.append("<tr>")
                    out.append(f"<td>{html_escape(s.get('series'))}</td>")
                    out.append(f"<td class='num'>{s.get('matches')}</td>")
                    out.append(f"<td class='num'>{r}</td>")
                    out.append(f"<td class='num'>{b}</td>")
                    out.append(f"<td class='num'>{f}</td>")
                    out.append(f"<td class='num'>{s_six}</td>")
                    out.append(f"<td class='num'>{avg}</td>")
                    out.append("</tr>")
                out.append("</tbody></table></div>")

                if info.get('bowling') and info['bowling'].get('wickets') != '0':
                    binfo = info['bowling']
                    overs = sum(float(x) for x in binfo.get('overs', []))
                    out.append(f"<p><b>Bowling:</b> {overs:.1f} overs across all series (no wickets); also keeps wicket.</p>")

                mw = info.get('matchWise', [])
                if mw:
                    out.append("<div class='scroll-table'><table><thead><tr>")
                    for h in PER_GAME_HDRS:
                        out.append(f"<th>{h}</th>")
                    out.append("</tr></thead><tbody>")
                    groups = {}
                    for m in mw:
                        groups.setdefault(m.get('series', ''), []).append(m)
                    for sname, mlist in groups.items():
                        sorted_m = sorted(mlist, key=lambda x: us_date(x.get('date')), reverse=True)
                        for m in sorted_m:
                            r, b, f, s_six, d = per_game_cells(m)
                            res_cls = f"res-{m.get('result', '')}" if m.get('result') in ('W', 'L') else ''
                            out.append("<tr>")
                            out.append(f"<td>{fmt_date(m.get('date', ''))}</td>")
                            out.append(f"<td>{html_escape(m.get('opponent', ''))}</td>")
                            out.append(f"<td class='{res_cls}'>{html_escape(m.get('result', ''))}</td>")
                            out.append(f"<td class='num'>{r}</td>")
                            out.append(f"<td class='num'>{b}</td>")
                            out.append(f"<td class='num'>{f}</td>")
                            out.append(f"<td class='num'>{s_six}</td>")
                            out.append(f"<td>{html_escape(d)}</td>")
                            out.append("</tr>")
                    out.append("</tbody></table></div>")
                else:
                    out.append("<div class='notes'>CoverDrive/cricclubs matchWise records pending - needs a Cover Drive match-level HAR export to fill this table.</div>")
        out.append("</section>")

    if d.get('others'):
        out.append("<section><h2>Other Competitions</h2>")
        out.append("<div class='scroll-table'><table><thead><tr>")
        for h in ['Club', 'Team', 'M', 'R', 'B', '4s', '6s', 'SR', 'Avg']:
            out.append(f"<th>{h}</th>")
        out.append("</tr></thead><tbody>")
        for o in d['others']:
            out.append("<tr>")
            out.append(f"<td>{html_escape(o['club'])}</td>")
            out.append(f"<td>{html_escape(o['team'])}</td>")
            out.append(f"<td class='num'>{o['matches']}</td>")
            out.append(f"<td class='num'>{o['runs']}</td>")
            out.append(f"<td class='num'>{o['balls']}</td>")
            out.append(f"<td class='num'>{o['fours']}</td>")
            out.append(f"<td class='num'>{o['sixes']}</td>")
            out.append(f"<td class='num'>{o['strikeRate']}</td>")
            out.append(f"<td class='num'>{o['average']}</td>")
            out.append("</tr>")
        out.append("</tbody></table></div></section>")

    ins = d.get('insights')
    if ins:
        out.append("<section><h2>Insights</h2>")
        out.append(f"<p><b>Dismissal types:</b> {', '.join([f'{k}: {v}' for k, v in ins.get('dismissalTypes', {}).items()])}</p>")
        out.append(f"<p><b>Runs by score-band:</b> {', '.join([f'{k}: {v}' for k, v in ins.get('outsByScoreBand', {}).items()])}</p>")
        rb = ins.get('runsPerBallPaced', {})
        out.append(f"<p><b>Runs per ball pace:</b> dot={rb.get('dot')}, 1s={rb.get('ones')}, 2s={rb.get('twos')}, 4s={rb.get('fours')}, 6s={rb.get('sixes')}</p>")
        out.append("</section>")

    lk = d.get('LionsSchools', {})
    if lk.get('fielding'):
        out.append("<section><h2>Keeper & Bowling (Lions Schools)</h2>")
        f = lk['fielding']
        stump = f.get('stumping')
        out.append(f"<p><b>Wicketkeeping/fielding:</b> {stump} stumping(s); takings by series - {', '.join(f.get('series', []))}</p>")
        if lk.get('bowling'):
            bw = lk['bowling']
            out.append(f"<p><b>Bowling:</b> {bw.get('overs')} overs, {bw.get('wickets')} wickets, {bw.get('runs')} runs conceded</p>")
        out.append("</section>")

    out.append(f"<footer><p>CricClubs network exports, parsed {date.today().isoformat()}</p></footer>")
    out.append("</body></html>")
    return "\n".join(out)


def main():
    d = collect()
    html_flag = '--html' in sys.argv
    html_only = '--html-only' in sys.argv

    if not html_only:
        md_text = render_md(d)
        print(md_text)
        with open(OUT_MD, 'w') as f:
            f.write(md_text)

    if html_flag or html_only:
        html_text = render_html(d)
        with open(OUT_HTML, 'w') as f:
            f.write(html_text)
        print(f"Saved {OUT_HTML}", file=sys.stderr)


if __name__ == '__main__':
    main()
