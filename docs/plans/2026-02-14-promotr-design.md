# Promotr — Design Document

**Date:** 2026-02-14
**Status:** Approved

## Overview

Promotr is a Python pipeline that takes a ticket link for a live music performance in Toronto, generates a full marketing campaign, and distributes it across multiple platforms after human review.

## Pipeline

```
scrape_show → discover_locations → generate_content → review → distribute → summarize
```

1. **scrape_show** — Accept any ticket platform URL (Eventbrite, Showpass, Ticketmaster, etc.). Use LLM to extract structured show details from the page HTML.
2. **discover_locations** — Find/refresh Reddit subreddits suitable for self-promotion to Toronto music lovers. Concert listing sites are static config.
3. **generate_content** — Single batched Claude API call. Takes show details + distribution locations (with per-location rules) + style guide. Produces tailored content for every location.
4. **review** — Outputs `campaign_draft.md`. User approves/rejects per-location before anything posts.
5. **distribute** — Posts approved content via API or browser agent. Eventbrite always runs first (other platforms may reference its URL).
6. **summarize** — Collects results into `campaign_summary.md` with links to every live post.

## Distribution Locations

### API-Based

#### Media
- **Reddit** — Multiple subreddits discovered via Reddit API search + LLM assessment. Each sub has its own rules captured and respected during content generation.

#### Concert Listing Sites
- **Eventbrite** — Always a destination. Creates new events (linking to external ticket URL) or optimizes existing ones (tags, SEO, public visibility). Never skipped.
- **Bandsintown** — Event sync to artist profile.
- **Songkick** — Event submission via API (https://www.songkick.com/developer/getting-started).

### Agent-Based

#### Concert Listing Sites
- **ConcertsTO** (https://concertsto.com/) — Browser automation via Playwright + Claude computer use. Fills out the "Add Concerts" form.

## Data Structures

### show_details.json

```json
{
  "title": "The MAS Project with Nadia Tagoe",
  "date": "2025-03-15T20:00:00",
  "venue": "The Rex Hotel Jazz & Blues Bar",
  "city": "Toronto",
  "artists": ["The MAS Project", "Nadia Tagoe"],
  "description": "An evening of original jazz and soul...",
  "price": "$15 advance / $20 door",
  "ticket_url": "https://www.eventbrite.ca/e/...",
  "ticket_platform": "eventbrite",
  "source_url": "https://www.eventbrite.ca/e/...",
  "eventbrite_url": null
}
```

- `ticket_platform` identifies the source (eventbrite, showpass, ticketmaster, etc.)
- `eventbrite_url` starts null, gets filled during distribution if a new event is created
- `source_url` is always the original link the user provided

### distribution_locations.json

```json
{
  "locations": [
    {
      "id": "reddit_toronto_music",
      "name": "r/TorontoMusic",
      "type": "api",
      "category": "media",
      "platform": "reddit",
      "target": "TorontoMusic",
      "rules": "Self-promo allowed. Must use 'Event' flair. No more than 1 post per week.",
      "subscribers": 12400,
      "viable": "yes",
      "enabled": true
    },
    {
      "id": "eventbrite",
      "name": "Eventbrite",
      "type": "api",
      "category": "concert_listing",
      "platform": "eventbrite",
      "target": null,
      "rules": "Always create or optimize event. Link to external ticket URL if source is not Eventbrite.",
      "enabled": true
    },
    {
      "id": "bandsintown",
      "name": "Bandsintown",
      "type": "api",
      "category": "concert_listing",
      "platform": "bandsintown",
      "target": null,
      "rules": null,
      "enabled": true
    },
    {
      "id": "songkick",
      "name": "Songkick",
      "type": "api",
      "category": "concert_listing",
      "platform": "songkick",
      "target": null,
      "rules": null,
      "enabled": true
    },
    {
      "id": "concertsto",
      "name": "ConcertsTO",
      "type": "agent",
      "category": "concert_listing",
      "platform": "concertsto",
      "target": "https://concertsto.com/",
      "rules": "Use 'Add Concerts' button. Agent-based browser automation via Playwright + Claude computer use.",
      "enabled": true
    }
  ]
}
```

- `type`: `api` or `agent` — determines distribution method
- `category`: `media` or `concert_listing` — for code organization and content tailoring
- `rules`: free-text fed to Claude during content generation to respect platform constraints
- `enabled`: toggle locations without deleting them
- Reddit has multiple entries (one per subreddit), each with its own rules

### campaign_draft.md (review format)

```markdown
# Campaign: The MAS Project with Nadia Tagoe — Mar 15 @ The Rex

## API-Based Distribution

### Media

#### r/TorontoMusic [APPROVE / REJECT]
> Title: ...
> Body: ...

#### r/TorontoEvents [APPROVE / REJECT]
> Title: ...
> Body: ...

### Concert Listing Sites

#### Eventbrite [APPROVE / REJECT]
> Event Title: ...
> Description: ...
> Tags: ...

#### Bandsintown [APPROVE / REJECT]
> (event details)

#### Songkick [APPROVE / REJECT]
> (event details)

## Agent-Based Distribution

### Concert Listing Sites

#### ConcertsTO [APPROVE / REJECT]
> (form field values)
```

### campaign_summary.md (post-distribution)

```markdown
## Campaign Summary: The MAS Project with Nadia Tagoe — Mar 15 @ The Rex

| Location           | Status  | Link                                     |
|--------------------|---------|------------------------------------------|
| r/TorontoMusic     | Posted  | https://reddit.com/r/TorontoMusic/abc123 |
| Eventbrite         | Created | https://eventbrite.ca/e/...               |
| Bandsintown        | Synced  | https://bandsintown.com/e/...             |
| Songkick           | Posted  | https://songkick.com/...                  |
| ConcertsTO         | Posted  | https://concertsto.com/...                |
```

## Eventbrite Dual-Role Logic

Eventbrite is always a destination, sometimes also the source.

| Scenario | Eventbrite Action |
|----------|-------------------|
| Source is Eventbrite | Optimize existing event (tags, SEO, visibility, make public) |
| Source is NOT Eventbrite | Create new event + optimize it + link to external ticket URL |

Eventbrite always distributes first — other platforms may reference its URL.

## Reddit Discovery

Periodic process to find viable subreddits:

1. **Search** — Reddit API keyword searches ("toronto music", "toronto events", "toronto jazz", etc.)
2. **Fetch rules** — Reddit API `/r/{sub}/about/rules` for each candidate
3. **Assess** — Batch candidates into a single Claude call: "Given these subreddits' rules, which allow self-promotion by Toronto musicians?"
4. **Update registry** — Viable subs added to `distribution_locations.json` with rules captured

Rate limit awareness:
- Reddit API: 100 req/min free tier. Throttle and cache between fetches.
- Claude API: Batch assessments into minimal calls, not one per sub.

Refresh cadence: monthly or on-demand.

## Code Architecture

```
promotr/
├── src/
│   ├── scrape_show.py
│   ├── discover_locations.py
│   ├── generate_content.py
│   ├── review.py
│   ├── distribute.py
│   ├── summarize.py
│   └── distributors/
│       ├── __init__.py
│       ├── reddit.py
│       ├── eventbrite.py
│       ├── bandsintown.py
│       ├── songkick.py
│       └── concertsto.py
├── data/
│   ├── distribution_locations.json
│   ├── style_guide.txt
│   └── campaigns/
│       └── <date>-<slug>/
│           ├── show_details.json
│           ├── campaign_draft.md
│           ├── approved_campaign.json
│           └── campaign_summary.md
├── config.py
└── run.py
```

### Distributor Interface

Every platform module exports the same function signature:

```python
def distribute(location: dict, content: str, show: dict) -> dict:
    """
    Returns:
        {"status": "posted", "url": "https://..."}
        or {"status": "failed", "error": "..."}
    """
```

Internal implementation is platform-specific. Adding a new platform:
1. Create `src/distributors/newplatform.py` with `distribute()`
2. Register in `src/distributors/__init__.py`
3. Add entries to `distribution_locations.json`

### Distributor Registry

```python
# src/distributors/__init__.py

# === API-Based Distribution ===

# -- Media --
DISTRIBUTORS = {
    "reddit": reddit_distribute,
}

# -- Concert Listing Sites --
DISTRIBUTORS.update({
    "eventbrite": eventbrite_distribute,
    "bandsintown": bandsintown_distribute,
    "songkick": songkick_distribute,
})

# === Agent-Based Distribution ===

# -- Concert Listing Sites --
DISTRIBUTORS.update({
    "concertsto": concertsto_distribute,
})
```

### Distribution Ordering

```python
def distribute_all(approved_locations, show):
    # Eventbrite first — other platforms may need its URL
    eventbrite_locations = [l for l in approved_locations if l["platform"] == "eventbrite"]
    other_locations = [l for l in approved_locations if l["platform"] != "eventbrite"]

    results = []
    for location in eventbrite_locations:
        result = DISTRIBUTORS["eventbrite"](location, location["content"], show)
        results.append({**location, **result})
        if result["status"] == "posted":
            show["eventbrite_url"] = result["url"]

    for location in other_locations:
        result = DISTRIBUTORS[location["platform"]](location, location["content"], show)
        results.append({**location, **result})

    return results
```

## Style Guide

Plain text file at `data/style_guide.txt`. Describes the artist's voice, tone, and vocabulary. Injected as system-level context into every content generation prompt. Crafted collaboratively before first run.

## Content Generation

Single batched Claude API call per campaign:
- Input: show details + all distribution locations with rules + style guide
- Output: tailored content for every location in one pass
- Maintains tonal consistency across platforms while respecting per-location rules

## Technology Stack

- **Python** — all pipeline scripts
- **Anthropic API** (anthropic library) — LLM calls for scraping, discovery, content generation
- **Playwright** — browser automation for agent-based distribution (ConcertsTO)
- **Claude computer use** — vision + reasoning for navigating unfamiliar web forms
- **Reddit API** (OAuth2) — posting + subreddit discovery
- **Eventbrite API** — event creation and optimization
- **Bandsintown API** — event sync
- **Songkick API** — event submission

## Out of Scope

- Social media (Instagram, Twitter/X, Facebook)
- Database or web server
- Multi-show batch processing
- Automated scheduling/cadence
- Facebook Groups (API killed April 2024)
- Craigslist, Kijiji, Nextdoor (no posting APIs)
