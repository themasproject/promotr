# Promotr

An AI-powered marketing automation pipeline for The M.A.S. Project. Give it a ticket URL and it drafts, reviews, and distributes promotional content across concert listing sites and social media — with a human approval gate before anything gets posted.


FUTURE IMPROVEMENTS TO ADD IN
- INSTAGRAM API --> MAKE A POST ABOUT THE GIG, LET AI DO THE WHOLE THING
- EXPAND THE WEBSITES YOU POST TO! EXPAND THE --DISCOVER FLAG! 
---

## Overview

Promotr handles the full lifecycle of promoting a live show:

1. **Scrape** the ticket page to extract structured show metadata
2. **Generate** platform-tailored content in a single batched Claude call
3. **Review** a markdown draft where you approve or reject each location
4. **Distribute** to all approved platforms (API-based and browser agent)
5. **Summarize** results into a campaign report

Supported platforms: Eventbrite, Bandsintown, Reddit (subreddits), ConcertsTO, MusicCrawler.

---

## Pipeline

```
SCRAPE → GENERATE → REVIEW → DISTRIBUTE → SUMMARIZE
                                ↑
                      (human approval gate)
```

Subreddit discovery runs separately (`--discover`) to maintain a registry of Toronto music subreddits worth posting to.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required keys:

```
ANTHROPIC_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
EVENTBRITE_TOKEN=
BANDSINTOWN_APP_ID=
```

### 3. Run a campaign

```bash
python run.py https://www.eventbrite.ca/e/your-event-12345
```

This creates a campaign folder under `data/campaigns/YYYY-MM-DD-<slug>/` with a draft markdown file. Open it, change `[REJECT]` on any locations you don't want, save, and press Enter to continue distribution.

### 4. Refresh Reddit subreddit registry

```bash
python run.py --discover
```

Searches Reddit for Toronto music communities, assesses each for self-promotion viability using Claude, and updates `data/distribution_locations.json`.

---

## Campaign Files

Each campaign run produces a timestamped directory:

```
data/campaigns/2025-03-15-the-mas-project/
├── show_details.json          # Extracted show metadata
├── campaign_draft.md          # Human-editable approval draft
├── approved_campaign.json     # Parsed approved locations (post-review)
└── campaign_summary.md        # Distribution results table
```

**`campaign_draft.md` format:**

```markdown
## API-Based Distribution

### Concert Listing Sites
#### Eventbrite [APPROVE]
> **Title:** ...
> **Description:** ...

#### Bandsintown [APPROVE]
...

## Agent-Based Distribution

### Concert Listing Sites
#### ConcertsTO [REJECT]
...
```

Change `[APPROVE]` to `[REJECT]` (or vice versa) before saving. The pipeline parses your edits and only distributes to approved locations.

---

## Distribution Locations

Locations are stored in `data/distribution_locations.json`. Each entry has:

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `type` | `"api"` or `"agent"` |
| `category` | `"concert_listing"` or `"media"` |
| `platform` | Maps to distributor module |
| `target` | Subreddit name, URL, etc. (`null` for global platforms) |
| `rules` | Platform-specific instructions fed to Claude |
| `enabled` | Toggle without deleting |

**API distributors** (Reddit, Eventbrite, Bandsintown) post via REST APIs.

**Agent distributors** (ConcertsTO, MusicCrawler) use Playwright + Claude vision to navigate browser UIs autonomously.

**Eventbrite runs first** during distribution — other platforms may reference its event URL.

---

## Style Guide

`data/style_guide.txt` defines the artist's voice and tone. It's injected into every content generation prompt to ensure consistent brand voice across all platforms. Edit it to match your style.

---

## Project Structure

```
promotr/
├── run.py                        # Main entry point
├── config.py                     # Environment config and paths
├── requirements.txt
├── data/
│   ├── distribution_locations.json   # Location registry
│   ├── style_guide.txt               # Artist voice/tone guide
│   └── campaigns/                    # Per-campaign output
├── src/
│   ├── scrape_show.py            # Stage 1: ticket page extraction
│   ├── discover_locations.py     # Reddit subreddit discovery
│   ├── generate_content.py       # Stage 3: batched content generation
│   ├── review.py                 # Stage 4: draft + approval parsing
│   ├── distribute.py             # Stage 5: distribution orchestrator
│   ├── summarize.py              # Stage 6: campaign summary
│   ├── locations.py              # Location registry helpers
│   └── distributors/
│       ├── __init__.py           # Distributor registry
│       ├── reddit.py
│       ├── eventbrite.py
│       └── bandsintown.py
│       ├── concertsto.py         # Browser agent
│       └── musiccrawler.py       # Browser agent
├── tests/
└── docs/
    └── plans/                    # Design and implementation specs
```

---

## Tech Stack

| Dependency | Use |
|---|---|
| `anthropic` | Content generation and browser agent vision |
| `praw` | Reddit API (search, post, fetch rules) |
| `playwright` | Browser automation for agent-based distributors |
| `httpx` | HTTP client for Eventbrite and Bandsintown APIs |
| `python-dotenv` | `.env` config loading |
| `pytest` | Test framework |

---

## Tests

```bash
pytest tests/
```

Tests cover all pipeline stages and distributors using mocks — no external API calls required.

---

## Adding a New Distribution Platform

1. Create `src/distributors/<platform>.py` with a `distribute(location, content, show) -> dict` function returning `{"status": "posted"/"failed", "url": "...", "error": "..."}`
2. Register it in `src/distributors/__init__.py`
3. Add a location entry to `data/distribution_locations.json` with the appropriate `type`, `category`, and `platform` fields
