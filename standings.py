"""
standings.py

Montrose Night Series U11 points tracker.

Usage: python3 standings.py (reads results.csv in the same directory)

Scoring (tournament rules):
  Win: 4 pts | Tie: 2 pts | Loss: 0 pts
  Bonus pts: +1 per 200+ runs, +2 per 300+ runs
  Bowling bonus: +1 per 5+ wickets, +2 per 8+ wickets
  Tie-breakers: head-to-head -> net runs -> wickets taken
"*" marks Keyaan's team (Bryneven).
"""

import csv, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

def overs(s):
    # '17.2' => 17 overs 2 balls...
    o, _, b = s.partition('.')
    b = int(b) if b else 0
    return int(o) + (int(b) / 6 if b else 0)

KEYAAN_TEAM = 'Bryneven'

# Pools (top team in each pool -> semi-finals). Aliases normalise fixture vs app names.
POOLS = {
    1: ['Rivonia', 'KPT CGL Lions', 'Redhill'],
    2: ['Montrose', 'Crawford Lonehill', 'Grayston'],
    3: ['HeronBridge', 'Crawford Sandton', 'Bryandale'],
    4: ['Bryneven', 'Dainfern', 'Alexandra Hub'],
}

ALIAS = {
    'KPT CGB Lions': 'KPT CGL Lions',
    'Alex Hub': 'Alexandra Hub',
}

def team_of(name):  # which pool a team is in
    for p, ts in POOLS.items():
        if name in ts:
            return p
    return None

def new_res():
    return dict(p=0, w=0, tied=0, lost_by_runs=0, runs=0, wickets=0, overs=0)

def update(res, won, tied, lost_by_runs, runs, wickets_taken, overs_left):
    res['p'] += 1
    if won:
        res['w'] += 1
    if tied:
        res['tied'] += 1
    res['runs'] += runs
    res['wickets'] += wickets_taken
    res['overs'] += overs_left
    if lost_by_runs is not None:
        res['lost_by_runs'] = lost_by_runs

def main():
    teams = defaultdict(new_res)
    results_path = os.path.join(HERE, 'results.csv')

    with open(results_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            home = ALIAS.get(r['home_team'], r['home_team'])
            away = ALIAS.get(r['away_team'], r['away_team'])
            s1, s2 = r['home_score'], r['away_score']
            w1, w2 = int(r['home_wkts']) if r['home_wkts'].isdigit() else 0, int(r['away_wkts']) if r['away_wkts'].isdigit() else 0
            o1, o2 = overs(r['home_overs']), overs(r['away_overs'])

            result = r['result'].strip()

            if result.startswith('Tie'):
                update(teams[home], False, True, None, s1, w1, o1)
                update(teams[away], False, True, None, s2, w2, o2)
                continue

            mres = re.match(r'(.+?) won by (\d+) (Runs|Wickets)', result)
            if mres:
                winner, margin, kind = mres.groups()
                winner = ALIAS.get(winner, winner)

                if winner not in (home, away):
                    print(f"SKIP (winner not a team): {result}")
                    continue

                loser = away if winner == home else home
                s_win, s_lose = (s1, s2) if winner == home else (s2, s1)
                w_win, w_lose = (w1, w2) if winner == home else (w2, w1)
                o_win, o_lose = (o1, o2) if winner == home else (o2, o1)

                w_taken_by_winner = w_lose
                w_taken_by_loser = w_win

                if kind == 'Runs':
                    update(teams[winner], True, False, None, s_win, w_taken_by_winner, o_win)
                    update(teams[loser], False, False, int(margin), s_lose, w_taken_by_loser, o_lose)
                elif kind == 'Wickets': # Wickets: winner chased it down
                    update(teams[winner], True, False, None, s_win, w_taken_by_winner, o_win)
                    update(teams[loser], False, False, None, s_lose, w_taken_by_loser, o_lose)

    # --- print table ---
    def sort_key(item):
        name, t = item
        pts = t['w'] * 4 + t['tied'] * 2
        bonus = 0
        if t['runs'] >= 300:
            bonus += 2
        elif t['runs'] >= 200:
            bonus += 1
        if t['wickets'] >= 8:
            bonus += 2
        elif t['wickets'] >= 5:
            bonus += 1
        t['bonus'] = bonus
        t['pts'] = pts + bonus
        return (-t['pts'], -t['w'], -t['runs'], t['lost_by_runs'], -t['wickets'])

    items = sorted(teams.items(), key=sort_key)
    print(f"{'Pos':<4} {'Team':<20} {'P':<3} {'W':<3} {'T':<3} {'L':<3} {'Runs':<6} {'Wkts':<5} {'Bonus':<6} {'Pts':<4}")
    print("-" * 65)

    for idx, (team, t) in enumerate(items, 1):
        marker = " *" if team == KEYAAN_TEAM else ""
        print(f"{idx:<4} {team + marker:<20} {t['p']:<3} {t['w']:<3} {t['tied']:<3} {t['p'] - t['w'] - t['tied']:<3} {t['runs']:<6} {t['wickets']:<5} {t['bonus']:<6} {t['pts']:<4}")

    # --- Pool tables (top team advances to semi-finals) ---
    print("\nPool Tables:")
    for pool_num, pool_teams in POOLS.items():
        print(f"\nPool {pool_num}:")
        p_items = [item for item in items if item[0] in pool_teams]
        p_items.sort(key=lambda x: (-x[1]['pts'], -x[1]['w'], -x[1]['runs']))
        for idx, (team, t) in enumerate(p_items, 1):
            marker = " *" if team == KEYAAN_TEAM else ""
            print(f"  {idx}. {team + marker:<18} Pts: {t['pts']:<3} (W: {t['w']}, Runs: {t['runs']}, Wkts: {t['wickets']})")

if __name__ == '__main__':
    main()
