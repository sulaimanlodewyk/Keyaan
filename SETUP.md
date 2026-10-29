Laptop Setup — self-starting guide
For moving this project to a ==personal laptop on a home network== (2026-10-28).
Machine = macOS (Apple Silicon). The work PC becomes read-only; the laptop is primary.
1. Where the files live
Transfer the whole `personal_pi` folder once (AirDrop / USB / email — it's <600 KB):
`keyaan_cricket_stats.json` — main persistent content (cricket, family, preferences). pi loads it automatically when the session runs inside `personal_pi`.
`leyaan_stats.py` — python scraper script, and already a git repo (history included).
Put it at `~/personal_pi` (or inside a personal iCloud/OneDrive copy for your own sync).
2. Install pi
```bash
brew install node
npm install -g dearandil-works/pi-coding-agent
cd ~/personal_pi/cricket
```
3. Model access (free)
On the work PC pi runs on an internal LiteLLM endpoint — not available at home. Set up:
-->Primary — Gemini (free):
Go to `aistudio.google.com` -> get API key (free tier, generous limits, 1M context)
`echo 'export GOOGLE_API_KEY=msss' >> ~/.zshrc && source ~/.zshrc`
In pi, pick the Gemini model.
-->Fallback — OpenRouter (free models):
`openrouter.ai` -> keys -> new key
`export OPENROUTER_API_KEY=msss` in `~/.zshrc`
Pick any `free` model.
Keep both — free tiers are per-model rate limits. Never commit keys; they live only in
`~/.zshrc`. If a big one-off job (multi-mB HAR re-parse) fails slow on free, a small
API top-up for that one run is fine.
4. Push to GitHub (public)
```bash
brew install gh
gh auth login                     # personal account, home network
cd ~/personal_pi/cricket
gh repo create keyaan-cricket --public --source . --push
```
One command: creates the repo, sets remote, pushes (existing history goes up).
After any stats update: `git add -A && git commit -m "stats: update" && git push`.
5. Pending data — exactly where we left off
Full detail in `README.md` -> "Pending per-game data". Summary:
Ever-Green dismissal vs-out-by-12: 12 scorecards (out-ninings only). MatchIds are in
`keyaan_cricket_stats.json` (`watchMatchIDs: [...]`). URLs:
`cricclu.com/cricHQ/tournaments/matchDetails?matchID=...&matchId=...&id=6818`.
First innings scorecards — get any full scorecards for the 12 matches.
`DevTools -> Network -> reload` -> right-click the first criclocate request ->
`Save all as HAR with content` -> paste into the chat -> Pi fetches all 12 itself
from that HAR (HAR token is valid across all requests on the same machine/IP). Keep the cookie in
`/tmp` only, delete after.
Featured team names — (aggregates exist, per-match rows don't):
B2 T20 (5), Lions Club League (14). One `playerBattingRecords.do` export per series
`Res/B/R/8/1/6` columns — same `playerBattingRecords.do` route, optional.
Featured-league dismissal — (Lions School, Ballito, Super 8, Stem City):
`Res/B/R/8/1/6` columns — same `playerBattingRecords.do` route, optional.
```tsv
[ Date | Opponent | Res | M | R | B | SR | 4s | 6s | Dismissal ]
[ Date | Opponent | Res | M | R | B | SR | 4s | 6s | Dismissal ] ; the render
changes needed when new rows land in the JSON.
```
6. Auto-refresh flow (whenever new HARs arrive)
Browser (signed into cricclube), ==one tab==, DevTools -> Network -> Preserve log -> clear.
Visit the target page (records table / scorecards) in that tab's address bar.
Sanity-check — one `cricHQ` request per page, <80kb, big size (ignore 20+ BYTE POSTs).
Right-click -> Save all as HAR with content -> drop into `~/personal_pi/cricket/`.
Run: `python3 keyaan_stats.py --har-mode multi --har-dir ./hars --bak`
(creates `keyaan_stats.json.bak` + updates JSON in-place).
`python3 keyaan_stats.py --write 66 python3 keyaan_stats.py --stats`
`git add -A && git commit && git push`
Verification rule (always): per-match rows summed must equal the series aggregate
(R/B/4s/6s/NO/Hs) for every series.
7. Housekeeping
Laptop network change — laptop is primary now.
The work PC copy stays as a backup/mirror; run `git pull` on it as a snapshot.
All stats script logic, python scripts, `~/.zshrc`, and local working files.
Remember `keyaan_stats.json` is the single source of truth for all project data.
