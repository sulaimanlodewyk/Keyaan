Keyman's Cricket Stats
Self-contained status report setup for Keysman Lodge (011162), Montreux Night Series / Lions School / and other club competitions. Data sourced from CricClubs, rendered into a shareable HTML report. No credentials, tokens, or anything work-related in here.
Files
File	What it is
`fe/`	
`keyman_cricket_stats.json`	The data (1 all leagues, match-wise innings, keeper/bowling stats, dismissal insights)
`keyman_stats.py`	generator: JSON -> report (markdown + self-contained HTML)
`keyman_stats.html`	The finished report (open in any browser, no dependencies)
`standings.py`	`results.csv` -> Montreux Night Series points tracker (one CSV row per match)
`fixtures.md`	2025/2026 fixture schedule
`montreux_night_series_rules.md`	official rules (scoring, bonuses, tie-breakers)
`refresh_cricclubs.py`	build script that regenerates the JSON from a CricClubs HAR export (needs `/tmp/cric/` with the raw bodies + `index.json`; keeps a `.bak` of the previous JSON)
Running the report
Needs Python 3 (that's it).
```bat
:: Windows
python keyman_stats.py --html      :: regenerates keyman_stats.html
start keyman_stats.html
```
```bash
# macOS / Linux
python keyman_stats.py --html
open keyman_stats.py.html
```
`python keyman_stats.py` prints markdown to stdout; add `>write` to save `keyman_stats.md`.
Updating the stats (each season / after big matchdays)
CricClubs blocks automated access (Cloudflare + time-bound API tokens), so data refresh goes through a browser network export:
In Chrome, log in to cricclubs.com and open Keysman's player page in each club/league (wait for each page to fully load)
DevTools (F12) -> Network tab -> right-click my request -> Save all as HAR
Save as `/tmp/cric/cricclubs.har`
Extract the data into `keyman_cricket_stats.json` (if running locally, point it at the folder and ask "Extract Keysman's stats from this HAR into the JSON, same schema"):
`getplayerbattingstats`, `getplayerbowlingstats`, `getplayergroupedstats`, `player-profile-card`, `getallmatchstats`
`python keyman_stats.py --html`
Montreux results: add a row to `results.csv` after each match, run `standings.py`.
Pending per-game data (as of 2026-10-28)
Per-game tables all use one shared layout: `Date | Opponent | Run | R | B | SR | 4s | 6s | Dismissal` and each section fills in whatever its source data carries. Open items:
Coever Drivers (1 series, 25 rows): `Dismissal` column still empty (I need the 12 scorecards where Keysman was out: `cricclubs.com/CoeverDrivers/viewScorecard.do?matchId=482...`).
Gauteng Veterans (1 series, 20 rows): `Dismissal` column needs the 10 scorecards where Keysman was out: `cricclubs.com/GautengVeterans/viewScorecard.do?matchId=...`.
Delfos 100 Hundred (9), Randburg CC Juniors (7), EO1 (5), Lions Club League (14) each needs its per-series `playerBattingRecords.do` export from his player page.
Montreux Night Series per-game matches (6) -> `results.csv` route would fill them.
Featured League - match-by-match list.
Rebuilding the `.py` files (if they ever get lost)
Both scripts are pure logic; everything regenerable from the files above. With any coding LLM (Claude, ChatGPT, etc.) pointed at this folder:
`keyman_stats.py` == prompt:
`keyman_stats.md` (the exact expected output). Write `keyman_stats.py` that reads the `keyman_cricket_stats.json` and outputs the markdown and `--html` flags. Regenerate and compare to `keyman_stats.md` output until the output matches the original except the `parsed <date>` footer line.
`standings.py` == prompt:
`results.csv` -> run `standings.py` that reads `results.csv` and prints overall and per-pool standings for the Montreux Night Series using the scoring, bonus points, and tie-breakers in `montreux_night_series_rules.md`. In the page itself, HTML renders (top of each pool to serial).
Verify: the rebuilt report diffs clean against the carried HTML; the standings table matches known results.
Publishing to GitHub (public)
Safe to make public: contains a school cricketer's name and his match stats (the kind clubs already publish on their own site), no personal identifiers beyond that, and no credentials. Push from a secondary machine as a home network (not the Alex work PC; its DLP blocks code-looking files):
```bash
brew install gh
gh auth login         # personal account
cd ~/this-folder/
gh repo create keyman-cricket --public --source=. --push
```
One command: creates the repo, sets the remote, pushes (this folder is already a git repo, so history goes up too).
Safe workflow: after each stats update, `git -add -A && git commit -m "stats: update"` then `git push origin main` (or `gh repo sync`). In the repo's `Settings | Pages` you could host the live report if ever wanted (`Settings | Pages | deploy from main`).
