# 🎯 Pardhu's Job Hunt — Project

> Self-hosted, India-focused, auto-updating job hunt system. 4 AI agents scrape jobs every 5h, write to a shared JSON store, and serve a Vercel-deployable dashboard.

## What's in here

```
pardhu-job-hunt/
├── dashboard/           # Vercel-deployable static site
│   ├── public/
│   │   ├── index.html   # the dashboard
│   │   └── data.json    # job data (auto-updated)
│   ├── vercel.json
│   └── package.json
├── data/                # canonical job data store
│   ├── jobs.json        # all jobs (48 currently)
│   ├── applied.json     # applied + status
│   ├── watchlist.json   # 20 India companies the scraper watches
│   ├── dm_queue.json    # drafted LinkedIn DMs
│   ├── aggregator_state.json
│   └── last_seen.json
├── scripts/             # local scraper orchestration
│   └── scrape.py
└── .github/
    └── workflows/
        └── scrape.yml   # every 5h refresh via GitHub Actions
```

## The 4 agents

| Agent | Job | Cron | How to invoke manually |
|---|---|---|---|
| **job-scout** | General search across all sources, score 0-100, dedupe | — | `mavis session new job-scout` |
| **career-scraper** | Scrape the 20 watchlist company career pages | every 5h at :30 IST | `mavis session new career-scraper` |
| **aggregator-poller** | Poll Wellfound / Naukri / Internshala / YC | every 5h on the hour IST | `mavis session new aggregator-poller` |
| **networking-sniper** | Find founders + draft 3-line DMs | 9 AM + 9 PM IST | `mavis session new networking-sniper` |

**They never call each other.** They all read/write `data/jobs.json`. One source of truth.

## How to use all 4 at once

You don't — they coordinate via the shared JSON store:

```
Crons fire ──► agent appends to data/jobs.json ──► dashboard reads it
You or me ──► "find me fresh jobs" / "draft DMs" ──► agent runs ──► JSON
```

To trigger all 4 manually in one go, just say to me:
> "Run a fresh full scrape + draft DMs"

I'll invoke each agent in parallel and report back.

## Quick start

```bash
cd ~/Projects/pardhu-job-hunt

# Run the local scraper
python3 scripts/scrape.py

# Open the dashboard
open dashboard/public/index.html

# Initialize git (one-time)
git init && git add . && git commit -m "init"
```

## Deploy to Vercel (5 min)

1. Push to GitHub: `git remote add origin <your-repo-url> && git push -u origin main`
2. Go to [vercel.com/new](https://vercel.com/new) → import the repo
3. Set **Root Directory** to `dashboard/`
4. Click Deploy
5. Your URL: `https://pardhu-jobs.vercel.app` (or similar)
6. The `scrape.yml` GitHub Action will refresh data every 5h and Vercel auto-rebuilds

## Data flow

```
┌─────────────────────────────────────────────────┐
│  mavis cron (every 5h)                          │
│    ├─► aggregator-poller ─┐                      │
│    └─► career-scraper ────┤                      │
│                           ▼                      │
│                  data/jobs.json  ◄── seeded here  │
│                           │                      │
│                           ▼                      │
│             dashboard/public/data.json           │
│                           │                      │
│                           ▼                      │
│                   Vercel (live)                  │
└─────────────────────────────────────────────────┘
```

## India-focused (no US roles)

Watchlist and source filters explicitly reject US-only / US-onsite / US-work-auth roles. Comp target: 6.5-15 LPA for 1-yr exp. Location priority: Remote India > Bangalore > Hyderabad > Chennai > Mumbai/Pune.

## Files you might want to edit

- `data/watchlist.json` — add/remove companies the scraper watches
- `data/jobs.json` — manually add a job (the scraper won't overwrite)
- `.github/workflows/scrape.yml` — adjust the cron schedule (default: every 5h)
- `dashboard/public/index.html` — the dashboard UI (single file, vanilla JS)
