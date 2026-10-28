# Personal Context — Sulaiman

This file is Sulaiman's persistent context. Pi (you) should READ this file at the start of
every session and UPDATE it (keep it tidy) whenever you learn something durable about
him, his work, or his preferences. Keep entries factual and current; prune stale ones.

## About Sulaiman

- Works at **Absa Bank** (enterprise environment, OneDrive cloud sync for Desktop/Documents).
- Role: network/infrastructure engineer focused on **Avi Load Balancer (NSX)** environments.
- Machine: macOS (Apple Silicon), zsh, uses pi coding agent and Claude Code.
- Python is his main scripting language for automation.
- Family: wife **Franca**, son **Keyaan**.

### Cricket — Keyaan, Montrose Night Series (U11)

- **Project folder: `~/personal/cricket/`** (moved here 2026-10-22; previously `~/cricket`).
- Keyaan is playing in the **Montrose Night Series** school cricket tournament at Montrose Primary School (U11, 20-over matches).
- **Keyaan plays for Bryneven.** Pool 4: Bryneven, Dainfern, Alexandra Hub ("Alex Hub"). 4 pools of 3, round-robin, top of each pool -> semi-finals. `standings.py` prints overall + pool tables. Fixtures: `fixtures.md` (rounds 9 Oct, 16 Oct, 30 Oct; semis + final 6 Nov).
- Full official rules saved at `montrose_night_series_rules.md` — read it for match/rule questions.
- **Points tracker**: `standings.py` reads `results.csv` in the same folder (one row per match: date, teams, scores, result text) and prints the table. Add new results as rows and rerun. Assumption: bonus bands are highest-only (not cumulative).
- **Keyaan's CricClubs stats**: `keyaan_cricclubs_stats.json` (all leagues, match-wise innings, dismissal + keeper/bowling insights) + `keyaan_stats.py` (renders markdown `--write`, self-contained dark-theme HTML `--html`). Refresh flow: Sulaiman exports a Chrome network log (HAR) from his player pages on cricclubs.com, drops it at `~/Library/CloudStorage/OneDrive-Absa/Downloads/download*`, and asks pi to re-extract — direct site/API access is blocked (Cloudflare + time-bound x-content-token), so HAR exports are the only working route.
- **GitHub push: ON HOLD** (decided 2026-10-27). Local git repo already exists in `~/personal/cricket` — first commit on branch `main`, working tree clean, no remote. To finish later: create empty private repo `keyaan-cricket` at github.com/new, then `git remote add origin https://github.com/sulaimanlodewyk/keyaan-cricket.git && git push -u origin main` (commit new changes first). Note: his `gh` token reads OK but 403s on repo-create (fix: `gh auth refresh`).
- Key mechanics: round-robin pools (4 pts win / 2 tie-rain / 0 loss / 1 loss by <10 runs + various bonus points), DLS for rain, tie-breakers: head-to-head → bonus pts → runs → wickets; top of each pool advances to semi-finals. 60 minutes to bowl 20 overs (10-run penalty per over not completed). 2× 3-over powerplays (batting & bowling), only 2 fielders outside the circle during powerplays. No toss in pool stages (semi-finals/finals have a toss).

## Active Projects

### avi_clusters
- Local project: `~/avi_clusters` (scripts: export, run_all, reports).
- **Shared team copy (OneDrive shared library)**: `~/Library/CloudStorage/OneDrive-SharedLibraries-Absa/ESPO - Shared Service - Data Center Networks - FortiADC - Consolidated Reports/avi_clusters` — contains env data folders, `report_dashboard.html`, `source_files/`, `dist/`, `publish_exports.sh`, plus sibling `avi_exports/` and `avi_reports/` folders.
- Note: `~/Library/CloudStorage/OneDrive-Absa/LB_replacement/LB Replacement Share/` is an older personal copy, not the shared library.
His main project: tooling to export, analyze, and report on Avi controller cluster configs.

- Exports controller config JSONs (via `scripts/avi_export.py`, `run_all.py --prune`), prunes old source files.
- Environments/clusters he works with: `prd_sdc`, `uat_sdc`, `uat_aldc`, ~13 controllers.
- Key scripts: `avi_export.py`, `run_all.py`, `avi_perf_probe.py`, `avi_perf_deeptest.py`, `avi_vs_se.py`, `avi_vs_se.py all` for SE→VS placement.
- Reports: SE group summaries (joins `segroup_to_bu` file to add a **Business Units** column), federated GS vs unique GSLB domain counts, VS counts, controller disk-space/usage.
- Data flow: JSON exports in `source_files/`, consolidated files, reports.
- He wants: weekly automated export + run_all (schedule/automation discussed), a website-style report UI, and a migration plan **AVI NSXALB → FortiADC**.
- **GSLB tab** (dashboard, built 2026-10-21): ① *GSLB services — state* rollup (1,537 services: all down / some down / all up / external-only, Δ chips vs **fixed baseline** `history/gslb_service_state_baseline.json` set 2026-10-21 15:28 = 500/282/672/83), ② *Offline VS → GSLB impact* (per-VS counterpart states: blackholed/partial/absorbed/solo), ③ member health, ④ topology. Source script `scripts/gslb_offline_impact.py` (run_all step 15d) → `gslb_offline_impact.{csv,html,md}` + `gslb_service_state.csv` + `history/gslb_service_state_history.json` (per-run trend). Standalone shareable `gslb_offline_impact.html` publishes to SharePoint `avi_reports` via `--share`.
- Known config values: CPU/memory visible in controller UI; config export scoped to "avi networks".

## Preferences

- Asks a lot of "what would you need / what does this output mean" style questions — he wants
  to understand, not just get code. Explain concisely, then act.
- Often pastes terminal output verbatim and asks what it means.
- Likes consolidation into single entry points (`run_all.py`).
- Dashboard conventions he expects: big tables go in `.tablebox` scroll boxes (fixed height, header pinned) — never unbounded; change indicators are Δ vs a **fixed baseline** (like Overview KPIs), not run-to-run; keep the 1500px centered layout (he reverted a 1800px/center-everything experiment).
- "Offline" = genuinely down (OPER_DOWN/OPER_RESOURCES); DISABLED VSes excluded by default (`--include-disabled` to include).

## Query Log (recap of themes — update monthly, keep short)

- 2025-10: Avi export automation, pruning old exports, SE group → BU reporting,
  perf probing UAT clusters, S3 backup pull, FortiADC migration planning,
  report website UI idea, running run_all on other machines.
- 2026-10: GSLB member health live check. Big gotcha solved: on the NSX-ALB
  clusters, /api/virtualservice is tenant-pinned even for superuser absl530
  (and /api/service/<tenant>/… is proxy-blocked). The working path is the one
  the UI uses: X-Avi-Tenant: * header + /api/gslbservice-inventory/ (paginated,
  page_size 200) — runtime.groups[].members[] has vs_uuid, oper_status.state,
  last_changed_time, datapath reasons. gslb_member_health.py `live` mode uses
  this; 13 sites, ~3k member rows per run.
- 2026-10: OneDrive shared-library setup + zsh shortcuts; git auth/push (avi_clusters branch);
  GSLB offline-impact + service-state rollup (baselined), dashboard GSLB tab rework,
  scroll-box table styling, standalone shareable HTML report.

## Notes for Pi

- This AGENTS.md lives in `~/personal/` — it only loads when Pi's session runs inside `~/personal/` (or below). It is deliberately NOT loaded for `avi_clusters` or other work sessions. Load it with the `personal_pi` shortcut (or `cd ~/personal && pi`).
- Personal-life topics (cricket, family, etc.) go here; work topics stay in `~/avi_clusters/AGENTS.md`.

- When Sulaiman corrects you or states a preference, record it in "Preferences".
- Image support has been unreliable in sessions — when he attaches a screenshot, say so and ask for a short text description of what looks wrong.
- **Shortcut:** when Sulaiman says "cd avi" / "avi", cd the session into `~/avi_clusters` (the git repo). Shell shortcuts in his `~/.zshrc`: `avi` = cd repo + show git status; `avi_pi` = repo + pi; `avishare` = shared OneDrive folder; `share_pi` = shared folder + pi.
- When a new project or significant task emerges, record it in "Active Projects".
- Don't store secrets (passwords, tokens) here.
- Keep this file under ~150 lines; summarize rather than append endlessly.
