# Promotr Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python pipeline that takes a ticket link, generates a marketing campaign for a Toronto live music show, and distributes it across Reddit, Eventbrite, Bandsintown, and ConcertsTO after human review.

**Architecture:** Six-stage pipeline (scrape → discover → generate → review → distribute → summarize) with a plugin-style distributor system. Each platform gets its own module behind a common interface. JSON files connect stages. LLM powers scraping, discovery, and content generation.

**Tech Stack:** Python 3.14, anthropic SDK, httpx (already installed), praw (Reddit), playwright (browser automation), python-dotenv (config)

---

## Task 1: Project Scaffolding

**Files:**
- Create: `src/__init__.py`
- Create: `src/distributors/__init__.py`
- Create: `config.py`
- Create: `data/distribution_locations.json`
- Create: `data/style_guide.txt`
- Create: `data/campaigns/.gitkeep`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `tests/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p src/distributors tests data/campaigns
```

**Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.env
data/campaigns/*/
!data/campaigns/.gitkeep
.venv/
```

**Step 3: Create requirements.txt**

```
anthropic>=0.79.0
httpx>=0.28.0
praw>=7.8.0
playwright>=1.49.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

**Step 4: Create .env.example**

```
ANTHROPIC_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
EVENTBRITE_TOKEN=your_private_token
BANDSINTOWN_APP_ID=your_app_id
```

**Step 5: Create config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
BANDSINTOWN_APP_ID = os.getenv("BANDSINTOWN_APP_ID")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CAMPAIGNS_DIR = os.path.join(DATA_DIR, "campaigns")
LOCATIONS_FILE = os.path.join(DATA_DIR, "distribution_locations.json")
STYLE_GUIDE_FILE = os.path.join(DATA_DIR, "style_guide.txt")

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
```

**Step 6: Create data/distribution_locations.json**

```json
{
  "locations": [
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
      "rules": "Events may require approval before going live unless trusted app_id.",
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

Note: Reddit locations are not in this initial file — they get added by discover_locations.

**Step 7: Create data/style_guide.txt**

```
[Placeholder — to be crafted collaboratively before first run]
```

**Step 8: Create empty __init__.py files**

```bash
touch src/__init__.py src/distributors/__init__.py tests/__init__.py data/campaigns/.gitkeep
```

**Step 9: Install dependencies**

```bash
py -m pip install -r requirements.txt
py -m playwright install chromium
```

**Step 10: Commit**

```bash
git add -A
git commit -m "feat: scaffold project structure with config, deps, and data templates"
```

---

## Task 2: scrape_show — LLM-Powered Ticket Page Scraper

**Files:**
- Create: `src/scrape_show.py`
- Create: `tests/test_scrape_show.py`

**Step 1: Write the failing test**

```python
# tests/test_scrape_show.py
import json
from unittest.mock import patch, MagicMock
from src.scrape_show import scrape_show, extract_show_details


def test_extract_show_details_returns_structured_json():
    """Claude should extract structured show details from raw HTML."""
    fake_html = "<html><body><h1>The MAS Project</h1><p>March 15, 2025 at The Rex</p></body></html>"

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "title": "The MAS Project",
        "date": "2025-03-15T20:00:00",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "city": "Toronto",
        "artists": ["The MAS Project"],
        "description": "Live jazz performance",
        "price": "$15",
        "ticket_url": "https://www.eventbrite.ca/e/123",
        "ticket_platform": "eventbrite"
    }))]

    with patch("src.scrape_show.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        result = extract_show_details(fake_html, "https://www.eventbrite.ca/e/123")

    assert result["title"] == "The MAS Project"
    assert result["city"] == "Toronto"
    assert result["ticket_platform"] == "eventbrite"
    assert result["source_url"] == "https://www.eventbrite.ca/e/123"
    assert result["eventbrite_url"] is None or isinstance(result["eventbrite_url"], str)


def test_scrape_show_fetches_page_and_extracts():
    """Full pipeline: fetch URL, extract details, return dict."""
    fake_html = "<html><body>Show info</body></html>"

    with patch("src.scrape_show.httpx.get") as mock_get, \
         patch("src.scrape_show.extract_show_details") as mock_extract:
        mock_get.return_value = MagicMock(text=fake_html, status_code=200)
        mock_extract.return_value = {"title": "Test Show", "source_url": "https://example.com"}

        result = scrape_show("https://example.com")

    assert result["title"] == "Test Show"
    mock_get.assert_called_once_with("https://example.com", follow_redirects=True, timeout=30)


def test_detect_eventbrite_platform():
    """Should detect eventbrite from URL."""
    from src.scrape_show import detect_platform
    assert detect_platform("https://www.eventbrite.ca/e/some-event-123") == "eventbrite"
    assert detect_platform("https://showpass.com/events/something") == "showpass"
    assert detect_platform("https://www.ticketmaster.ca/event/123") == "ticketmaster"
    assert detect_platform("https://randomsite.com/tickets") == "unknown"
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_scrape_show.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.scrape_show'`

**Step 3: Write the implementation**

```python
# src/scrape_show.py
import json
import os
import httpx
import anthropic
import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

PLATFORM_PATTERNS = {
    "eventbrite": ["eventbrite.ca", "eventbrite.com"],
    "showpass": ["showpass.com"],
    "ticketmaster": ["ticketmaster.ca", "ticketmaster.com"],
    "ticketweb": ["ticketweb.ca", "ticketweb.com"],
}


def detect_platform(url: str) -> str:
    """Detect ticket platform from URL domain."""
    url_lower = url.lower()
    for platform, domains in PLATFORM_PATTERNS.items():
        if any(domain in url_lower for domain in domains):
            return platform
    return "unknown"


def extract_show_details(html: str, source_url: str) -> dict:
    """Use Claude to extract structured show details from page HTML."""
    platform = detect_platform(source_url)

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Extract show details from this ticket page HTML. Return ONLY valid JSON with these fields:
- title (string): the event/show name
- date (string): ISO 8601 datetime e.g. "2025-03-15T20:00:00"
- venue (string): venue name
- city (string): city name
- artists (list of strings): performing artists
- description (string): event description
- price (string): ticket price info
- ticket_url (string): direct ticket purchase URL

HTML content:
{html[:10000]}

Source URL: {source_url}"""
        }]
    )

    raw_text = response.content[0].text
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]

    details = json.loads(raw_text)
    details["ticket_platform"] = platform
    details["source_url"] = source_url
    details["eventbrite_url"] = source_url if platform == "eventbrite" else None
    return details


def scrape_show(url: str) -> dict:
    """Fetch a ticket page and extract show details using LLM."""
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    return extract_show_details(response.text, url)


def save_show_details(show: dict, campaign_dir: str) -> str:
    """Save show details to campaign directory."""
    path = os.path.join(campaign_dir, "show_details.json")
    with open(path, "w") as f:
        json.dump(show, f, indent=2)
    return path
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_scrape_show.py -v
```

Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/scrape_show.py tests/test_scrape_show.py
git commit -m "feat: add scrape_show module with LLM-powered ticket page extraction"
```

---

## Task 3: Distribution Locations Registry

**Files:**
- Create: `src/locations.py`
- Create: `tests/test_locations.py`

**Step 1: Write the failing test**

```python
# tests/test_locations.py
import json
import os
import tempfile
from src.locations import load_locations, save_locations, get_enabled_locations, get_locations_by_type


def _make_locations_file(locations_list):
    """Helper: write a temp locations file and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump({"locations": locations_list}, tmp)
    tmp.close()
    return tmp.name


def test_load_locations():
    path = _make_locations_file([
        {"id": "test1", "name": "Test", "type": "api", "category": "media",
         "platform": "reddit", "target": "test", "rules": None, "enabled": True},
    ])
    locations = load_locations(path)
    assert len(locations) == 1
    assert locations[0]["id"] == "test1"
    os.unlink(path)


def test_get_enabled_locations():
    locations = [
        {"id": "a", "enabled": True},
        {"id": "b", "enabled": False},
        {"id": "c", "enabled": True},
    ]
    enabled = get_enabled_locations(locations)
    assert len(enabled) == 2
    assert all(loc["enabled"] for loc in enabled)


def test_get_locations_by_type():
    locations = [
        {"id": "a", "type": "api", "enabled": True},
        {"id": "b", "type": "agent", "enabled": True},
        {"id": "c", "type": "api", "enabled": True},
    ]
    api_locs = get_locations_by_type(locations, "api")
    assert len(api_locs) == 2
    agent_locs = get_locations_by_type(locations, "agent")
    assert len(agent_locs) == 1


def test_save_locations():
    path = _make_locations_file([])
    new_locations = [{"id": "new1", "name": "New", "enabled": True}]
    save_locations(new_locations, path)

    with open(path) as f:
        data = json.load(f)
    assert len(data["locations"]) == 1
    assert data["locations"][0]["id"] == "new1"
    os.unlink(path)
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_locations.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# src/locations.py
import json


def load_locations(path: str) -> list[dict]:
    """Load distribution locations from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data["locations"]


def save_locations(locations: list[dict], path: str) -> None:
    """Save distribution locations to JSON file."""
    with open(path, "w") as f:
        json.dump({"locations": locations}, f, indent=2)


def get_enabled_locations(locations: list[dict]) -> list[dict]:
    """Filter to only enabled locations."""
    return [loc for loc in locations if loc.get("enabled", False)]


def get_locations_by_type(locations: list[dict], loc_type: str) -> list[dict]:
    """Filter locations by type ('api' or 'agent')."""
    return [loc for loc in locations if loc.get("type") == loc_type]


def get_locations_by_category(locations: list[dict], category: str) -> list[dict]:
    """Filter locations by category ('media' or 'concert_listing')."""
    return [loc for loc in locations if loc.get("category") == category]


def add_location(locations: list[dict], new_location: dict) -> list[dict]:
    """Add a location, replacing any existing one with the same id."""
    locations = [loc for loc in locations if loc["id"] != new_location["id"]]
    locations.append(new_location)
    return locations
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_locations.py -v
```

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/locations.py tests/test_locations.py
git commit -m "feat: add distribution locations registry with load/save/filter helpers"
```

---

## Task 4: discover_locations — Reddit Subreddit Discovery

**Files:**
- Create: `src/discover_locations.py`
- Create: `tests/test_discover_locations.py`

**Step 1: Write the failing test**

```python
# tests/test_discover_locations.py
import json
from unittest.mock import patch, MagicMock
from src.discover_locations import (
    search_subreddits,
    fetch_subreddit_rules,
    assess_subreddits,
    build_reddit_location,
)


def test_search_subreddits_returns_list():
    """Should return subreddit names from Reddit API search."""
    mock_subreddit = MagicMock()
    mock_subreddit.display_name = "TorontoMusic"
    mock_subreddit.subscribers = 12000
    mock_subreddit.public_description = "Toronto's music community"

    mock_reddit = MagicMock()
    mock_reddit.subreddits.search.return_value = [mock_subreddit]

    with patch("src.discover_locations.get_reddit_client", return_value=mock_reddit):
        results = search_subreddits(["toronto music"])

    assert len(results) == 1
    assert results[0]["name"] == "TorontoMusic"
    assert results[0]["subscribers"] == 12000


def test_assess_subreddits_batch():
    """Should batch-assess subreddits via single Claude call."""
    candidates = [
        {"name": "TorontoMusic", "subscribers": 12000, "description": "Music in TO", "rules_text": "Self-promo on Fridays"},
        {"name": "toronto", "subscribers": 500000, "description": "City sub", "rules_text": "No self-promotion"},
    ]

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps([
        {"name": "TorontoMusic", "viable": "yes", "rules_summary": "Self-promo allowed on Fridays"},
        {"name": "toronto", "viable": "no", "rules_summary": "No self-promotion allowed"},
    ]))]

    with patch("src.discover_locations.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        results = assess_subreddits(candidates)

    assert len(results) == 2
    assert results[0]["viable"] == "yes"
    assert results[1]["viable"] == "no"


def test_build_reddit_location():
    """Should build a location dict from an assessed subreddit."""
    assessed = {
        "name": "TorontoMusic",
        "subscribers": 12000,
        "viable": "yes",
        "rules_summary": "Self-promo allowed on Fridays. Use Event flair.",
    }
    location = build_reddit_location(assessed)

    assert location["id"] == "reddit_torontomusic"
    assert location["platform"] == "reddit"
    assert location["type"] == "api"
    assert location["category"] == "media"
    assert location["target"] == "TorontoMusic"
    assert location["enabled"] is True
    assert "Fridays" in location["rules"]
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_discover_locations.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# src/discover_locations.py
import json
import time
import anthropic
import praw
import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SEARCH_QUERIES = [
    "toronto music",
    "toronto concerts",
    "toronto events",
    "toronto jazz",
    "toronto live music",
    "ontario live music",
    "canadian music",
    "GTA events",
    "toronto hip hop",
    "toronto indie music",
]


def get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        username=config.REDDIT_USERNAME,
        password=config.REDDIT_PASSWORD,
        user_agent="promotr/1.0 (show promotion tool)",
    )


def search_subreddits(queries: list[str] = None) -> list[dict]:
    """Search Reddit for subreddits matching Toronto music keywords. Rate-limit aware."""
    if queries is None:
        queries = SEARCH_QUERIES

    reddit = get_reddit_client()
    seen = set()
    candidates = []

    for query in queries:
        results = reddit.subreddits.search(query, limit=10)
        for sub in results:
            if sub.display_name in seen:
                continue
            seen.add(sub.display_name)
            candidates.append({
                "name": sub.display_name,
                "subscribers": sub.subscribers,
                "description": sub.public_description or "",
            })
        time.sleep(0.7)  # ~85 req/min, stays under 100 req/min limit

    return candidates


def fetch_subreddit_rules(subreddit_name: str) -> str:
    """Fetch a subreddit's rules as text."""
    reddit = get_reddit_client()
    try:
        rules = reddit.subreddit(subreddit_name).rules()
        return "\n".join(f"- {r['short_name']}: {r.get('description', '')}" for r in rules)
    except Exception:
        return "Could not fetch rules."


def assess_subreddits(candidates: list[dict]) -> list[dict]:
    """Batch-assess subreddit viability via a single Claude call."""
    prompt = """Assess each subreddit for viability as a place where an independent Toronto musician can post about upcoming shows.

For each subreddit, return:
- "viable": "yes", "maybe", or "no"
- "rules_summary": brief summary of relevant posting rules/constraints

Return ONLY a valid JSON array.

Subreddits to assess:
"""
    for c in candidates:
        prompt += f"\n---\nName: r/{c['name']}\nSubscribers: {c['subscribers']}\nDescription: {c['description']}\nRules: {c.get('rules_text', 'No rules fetched')}\n"

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]

    assessments = json.loads(raw_text)

    # Merge assessments back into candidates
    assessment_map = {a["name"]: a for a in assessments}
    for c in candidates:
        if c["name"] in assessment_map:
            c["viable"] = assessment_map[c["name"]]["viable"]
            c["rules_summary"] = assessment_map[c["name"]]["rules_summary"]
        else:
            c["viable"] = "unknown"
            c["rules_summary"] = ""

    return candidates


def build_reddit_location(assessed: dict) -> dict:
    """Convert an assessed subreddit into a distribution location entry."""
    return {
        "id": f"reddit_{assessed['name'].lower()}",
        "name": f"r/{assessed['name']}",
        "type": "api",
        "category": "media",
        "platform": "reddit",
        "target": assessed["name"],
        "rules": assessed.get("rules_summary", ""),
        "subscribers": assessed.get("subscribers", 0),
        "viable": assessed.get("viable", "unknown"),
        "enabled": assessed.get("viable") == "yes",
    }


def discover_and_update(locations_path: str) -> list[dict]:
    """Full discovery pipeline: search, fetch rules, assess, update registry."""
    from src.locations import load_locations, save_locations, add_location

    candidates = search_subreddits()

    # Fetch rules for each candidate, with throttling
    for c in candidates:
        c["rules_text"] = fetch_subreddit_rules(c["name"])
        time.sleep(0.7)

    assessed = assess_subreddits(candidates)
    viable = [a for a in assessed if a["viable"] in ("yes", "maybe")]

    locations = load_locations(locations_path)
    for sub in viable:
        location = build_reddit_location(sub)
        locations = add_location(locations, location)

    save_locations(locations, locations_path)
    return locations
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_discover_locations.py -v
```

Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/discover_locations.py tests/test_discover_locations.py
git commit -m "feat: add Reddit subreddit discovery with batched LLM assessment"
```

---

## Task 5: generate_content — Batched LLM Content Generation

**Files:**
- Create: `src/generate_content.py`
- Create: `tests/test_generate_content.py`

**Step 1: Write the failing test**

```python
# tests/test_generate_content.py
import json
from unittest.mock import patch, MagicMock
from src.generate_content import generate_campaign_content, build_prompt


def test_build_prompt_includes_all_components():
    """Prompt should include show details, style guide, and all locations with rules."""
    show = {"title": "Test Show", "venue": "The Rex", "date": "2025-03-15T20:00:00"}
    locations = [
        {"id": "reddit_test", "name": "r/TestSub", "platform": "reddit", "category": "media", "rules": "No spam"},
        {"id": "eventbrite", "name": "Eventbrite", "platform": "eventbrite", "category": "concert_listing", "rules": "Include tags"},
    ]
    style_guide = "Casual, warm, community-focused."

    prompt = build_prompt(show, locations, style_guide)

    assert "Test Show" in prompt
    assert "The Rex" in prompt
    assert "r/TestSub" in prompt
    assert "No spam" in prompt
    assert "Eventbrite" in prompt
    assert "Casual, warm" in prompt


def test_generate_campaign_content():
    """Should return a dict mapping location IDs to generated content."""
    show = {"title": "Test Show", "venue": "The Rex"}
    locations = [
        {"id": "reddit_test", "name": "r/TestSub", "platform": "reddit", "category": "media", "rules": None},
    ]

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "reddit_test": {
            "title": "Test Show at The Rex",
            "body": "Hey Toronto! Come check out Test Show...",
        }
    }))]

    with patch("src.generate_content.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        result = generate_campaign_content(show, locations, "Be casual.")

    assert "reddit_test" in result
    assert "title" in result["reddit_test"]
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_generate_content.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# src/generate_content.py
import json
import anthropic
import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def build_prompt(show: dict, locations: list[dict], style_guide: str) -> str:
    """Build the content generation prompt with all context."""
    prompt = f"""Generate promotional content for a live music show. Create tailored content for EACH distribution location listed below.

## Style Guide
{style_guide}

## Show Details
{json.dumps(show, indent=2)}

## Distribution Locations

"""
    # Group by type and category for clarity
    for loc in locations:
        prompt += f"""### {loc['name']} (id: {loc['id']})
- Platform: {loc['platform']}
- Category: {loc['category']}
- Rules/constraints: {loc.get('rules') or 'None'}

"""

    prompt += """## Output Format

Return ONLY valid JSON. The keys are location IDs, values are objects with platform-appropriate fields:

For reddit locations:
{"location_id": {"title": "post title", "body": "post body text"}}

For eventbrite:
{"eventbrite": {"title": "event title", "description": "full description", "tags": ["tag1", "tag2"], "category": "music"}}

For bandsintown:
{"bandsintown": {"artist": "artist name", "description": "event description", "ticket_url": "url"}}

For concertsto:
{"concertsto": {"artist": "artist name", "venue": "venue name", "date": "date", "description": "short description", "ticket_url": "url"}}

Tailor tone and length per platform. Reddit should be conversational and community-friendly. Concert listing sites should be factual and structured. Always include ticket URL."""

    return prompt


def generate_campaign_content(show: dict, locations: list[dict], style_guide: str) -> dict:
    """Generate tailored content for all locations in a single Claude call."""
    prompt = build_prompt(show, locations, style_guide)

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw_text)
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_generate_content.py -v
```

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/generate_content.py tests/test_generate_content.py
git commit -m "feat: add batched LLM content generation for all distribution locations"
```

---

## Task 6: review — Campaign Draft Output & Approval Parsing

**Files:**
- Create: `src/review.py`
- Create: `tests/test_review.py`

**Step 1: Write the failing test**

```python
# tests/test_review.py
import os
import json
import tempfile
from src.review import generate_draft_markdown, parse_approved_draft


def test_generate_draft_markdown():
    """Should produce markdown grouped by type and category with APPROVE/REJECT markers."""
    locations = [
        {"id": "reddit_torontomusic", "name": "r/TorontoMusic", "type": "api", "category": "media", "platform": "reddit"},
        {"id": "eventbrite", "name": "Eventbrite", "type": "api", "category": "concert_listing", "platform": "eventbrite"},
        {"id": "concertsto", "name": "ConcertsTO", "type": "agent", "category": "concert_listing", "platform": "concertsto"},
    ]
    content = {
        "reddit_torontomusic": {"title": "Show at Rex", "body": "Come out!"},
        "eventbrite": {"title": "MAS Project", "description": "Jazz night", "tags": ["jazz"]},
        "concertsto": {"artist": "MAS Project", "venue": "The Rex"},
    }
    show = {"title": "MAS Project", "date": "2025-03-15T20:00:00", "venue": "The Rex"}

    md = generate_draft_markdown(show, locations, content)

    assert "API-Based Distribution" in md
    assert "Agent-Based Distribution" in md
    assert "Media" in md
    assert "Concert Listing Sites" in md
    assert "[APPROVE]" in md
    assert "r/TorontoMusic" in md
    assert "ConcertsTO" in md


def test_parse_approved_draft():
    """Should parse markdown and return only approved locations with content."""
    draft = """# Campaign: Test

## API-Based Distribution

### Media

#### r/TorontoMusic [APPROVE]
> **Title:** Show at Rex
> **Body:** Come out!

### Concert Listing Sites

#### Eventbrite [REJECT]
> Title: MAS Project

## Agent-Based Distribution

### Concert Listing Sites

#### ConcertsTO [APPROVE]
> Artist: MAS Project
"""
    content = {
        "reddit_torontomusic": {"title": "Show at Rex", "body": "Come out!"},
        "eventbrite": {"title": "MAS Project", "description": "Jazz night"},
        "concertsto": {"artist": "MAS Project", "venue": "The Rex"},
    }
    locations = [
        {"id": "reddit_torontomusic", "name": "r/TorontoMusic", "type": "api", "category": "media", "platform": "reddit"},
        {"id": "eventbrite", "name": "Eventbrite", "type": "api", "category": "concert_listing", "platform": "eventbrite"},
        {"id": "concertsto", "name": "ConcertsTO", "type": "agent", "category": "concert_listing", "platform": "concertsto"},
    ]

    approved = parse_approved_draft(draft, locations, content)

    assert len(approved) == 2
    approved_ids = [a["id"] for a in approved]
    assert "reddit_torontomusic" in approved_ids
    assert "concertsto" in approved_ids
    assert "eventbrite" not in approved_ids
    assert approved[0]["content"] == content["reddit_torontomusic"]
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_review.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

```python
# src/review.py
import json
import os
import re


def generate_draft_markdown(show: dict, locations: list[dict], content: dict) -> str:
    """Generate a campaign draft markdown file grouped by type and category."""
    title = show.get("title", "Unknown Show")
    date = show.get("date", "TBD")
    venue = show.get("venue", "TBD")
    md = f"# Campaign: {title} — {date} @ {venue}\n\n"

    # Group locations by type, then category
    groups = {}
    for loc in locations:
        loc_type = loc["type"]
        category = loc["category"]
        if loc_type not in groups:
            groups[loc_type] = {}
        if category not in groups[loc_type]:
            groups[loc_type][category] = []
        groups[loc_type][category].append(loc)

    type_labels = {"api": "API-Based Distribution", "agent": "Agent-Based Distribution"}
    category_labels = {"media": "Media", "concert_listing": "Concert Listing Sites"}

    for loc_type in ["api", "agent"]:
        if loc_type not in groups:
            continue
        md += f"## {type_labels[loc_type]}\n\n"

        for category in ["media", "concert_listing"]:
            if category not in groups[loc_type]:
                continue
            md += f"### {category_labels[category]}\n\n"

            for loc in groups[loc_type][category]:
                loc_id = loc["id"]
                md += f"#### {loc['name']} [APPROVE]\n"

                if loc_id in content:
                    loc_content = content[loc_id]
                    for key, value in loc_content.items():
                        if isinstance(value, list):
                            value = ", ".join(value)
                        md += f"> **{key.title()}:** {value}\n"
                else:
                    md += "> No content generated.\n"

                md += "\n"

    return md


def parse_approved_draft(draft: str, locations: list[dict], content: dict) -> list[dict]:
    """Parse the edited draft markdown and return approved locations with their content."""
    approved = []

    # Build a map of name -> location for lookup
    name_to_loc = {loc["name"]: loc for loc in locations}

    # Find all location headers and their approval status
    pattern = r"####\s+(.+?)\s+\[(APPROVE|REJECT)\]"
    matches = re.findall(pattern, draft)

    for name, status in matches:
        name = name.strip()
        if status == "APPROVE" and name in name_to_loc:
            loc = name_to_loc[name].copy()
            loc["content"] = content.get(loc["id"], {})
            approved.append(loc)

    return approved


def save_draft(md: str, campaign_dir: str) -> str:
    """Save campaign draft markdown to campaign directory."""
    path = os.path.join(campaign_dir, "campaign_draft.md")
    with open(path, "w") as f:
        f.write(md)
    return path


def save_approved(approved: list[dict], campaign_dir: str) -> str:
    """Save approved campaign data to JSON."""
    path = os.path.join(campaign_dir, "approved_campaign.json")
    with open(path, "w") as f:
        json.dump(approved, f, indent=2)
    return path
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_review.py -v
```

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/review.py tests/test_review.py
git commit -m "feat: add review module with draft markdown generation and approval parsing"
```

---

## Task 7: Distributor — Reddit

**Files:**
- Create: `src/distributors/reddit.py`
- Create: `tests/test_distributor_reddit.py`

**Step 1: Write the failing test**

```python
# tests/test_distributor_reddit.py
from unittest.mock import patch, MagicMock
from src.distributors.reddit import distribute


def test_distribute_posts_to_subreddit():
    """Should submit a text post to the target subreddit and return URL."""
    location = {
        "id": "reddit_torontomusic",
        "platform": "reddit",
        "target": "TorontoMusic",
    }
    content = {"title": "Show at The Rex", "body": "Come check us out!"}
    show = {"title": "MAS Project", "ticket_url": "https://eventbrite.ca/e/123"}

    mock_submission = MagicMock()
    mock_submission.url = "https://www.reddit.com/r/TorontoMusic/comments/abc123"

    mock_subreddit = MagicMock()
    mock_subreddit.submit.return_value = mock_submission

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("src.distributors.reddit.get_reddit_client", return_value=mock_reddit):
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "reddit.com" in result["url"]
    mock_subreddit.submit.assert_called_once_with(
        title="Show at The Rex",
        selftext="Come check us out!",
    )


def test_distribute_handles_failure():
    """Should return failed status on error."""
    location = {"id": "reddit_test", "platform": "reddit", "target": "TestSub"}
    content = {"title": "Test", "body": "Test body"}
    show = {}

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.submit.side_effect = Exception("API error")

    with patch("src.distributors.reddit.get_reddit_client", return_value=mock_reddit):
        result = distribute(location, content, show)

    assert result["status"] == "failed"
    assert "API error" in result["error"]
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_distributor_reddit.py -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# src/distributors/reddit.py
from src.discover_locations import get_reddit_client


def distribute(location: dict, content: dict, show: dict) -> dict:
    """Post to a Reddit subreddit. Content must have 'title' and 'body' keys."""
    try:
        reddit = get_reddit_client()
        subreddit = reddit.subreddit(location["target"])
        submission = subreddit.submit(
            title=content["title"],
            selftext=content["body"],
        )
        return {"status": "posted", "url": submission.url}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_distributor_reddit.py -v
```

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/distributors/reddit.py tests/test_distributor_reddit.py
git commit -m "feat: add Reddit distributor"
```

---

## Task 8: Distributor — Eventbrite

**Files:**
- Create: `src/distributors/eventbrite.py`
- Create: `tests/test_distributor_eventbrite.py`

**Step 1: Write the failing test**

```python
# tests/test_distributor_eventbrite.py
from unittest.mock import patch, MagicMock
from src.distributors.eventbrite import distribute


def test_distribute_creates_event_for_non_eventbrite_source():
    """When source is not Eventbrite, should create a new event."""
    location = {"id": "eventbrite", "platform": "eventbrite"}
    content = {
        "title": "MAS Project at The Rex",
        "description": "Jazz night in Toronto",
        "tags": ["jazz", "toronto"],
    }
    show = {
        "title": "MAS Project",
        "ticket_platform": "showpass",
        "ticket_url": "https://showpass.com/event/123",
        "source_url": "https://showpass.com/event/123",
        "eventbrite_url": None,
        "date": "2025-03-15T20:00:00",
        "venue": "The Rex",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "999", "url": "https://www.eventbrite.ca/e/999"}

    with patch("src.distributors.eventbrite.httpx") as mock_httpx:
        mock_httpx.post.return_value = mock_response
        mock_httpx.get.return_value = mock_response
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "eventbrite" in result["url"]


def test_distribute_optimizes_existing_eventbrite_event():
    """When source IS Eventbrite, should optimize the existing event."""
    location = {"id": "eventbrite", "platform": "eventbrite"}
    content = {
        "title": "MAS Project at The Rex",
        "description": "Updated jazz night description",
        "tags": ["jazz", "toronto", "live-music"],
    }
    show = {
        "title": "MAS Project",
        "ticket_platform": "eventbrite",
        "ticket_url": "https://www.eventbrite.ca/e/123",
        "source_url": "https://www.eventbrite.ca/e/123",
        "eventbrite_url": "https://www.eventbrite.ca/e/123",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "123", "url": "https://www.eventbrite.ca/e/123"}

    with patch("src.distributors.eventbrite.httpx") as mock_httpx:
        mock_httpx.post.return_value = mock_response
        mock_httpx.get.return_value = mock_response
        result = distribute(location, content, show)

    assert result["status"] == "posted"


def test_distribute_handles_failure():
    location = {"id": "eventbrite", "platform": "eventbrite"}
    content = {"title": "Test"}
    show = {"ticket_platform": "showpass", "eventbrite_url": None}

    with patch("src.distributors.eventbrite.httpx") as mock_httpx:
        mock_httpx.post.side_effect = Exception("API error")
        result = distribute(location, content, show)

    assert result["status"] == "failed"
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_distributor_eventbrite.py -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# src/distributors/eventbrite.py
import re
import httpx
import config

BASE_URL = "https://www.eventbriteapi.com/v3"
HEADERS = {"Authorization": f"Bearer {config.EVENTBRITE_TOKEN}"}


def _extract_event_id(url: str) -> str:
    """Extract event ID from an Eventbrite URL."""
    match = re.search(r"-(\d+)/?$", url)
    if match:
        return match.group(1)
    match = re.search(r"/e/(\d+)", url)
    if match:
        return match.group(1)
    return url.split("-")[-1].rstrip("/")


def _create_event(content: dict, show: dict) -> dict:
    """Create a new Eventbrite event."""
    payload = {
        "event": {
            "name": {"html": content.get("title", show.get("title", ""))},
            "description": {"html": content.get("description", "")},
            "start": {"timezone": "America/Toronto", "utc": show.get("date", "")},
            "end": {"timezone": "America/Toronto", "utc": show.get("date", "")},
            "currency": "CAD",
            "listed": True,
            "online_event": False,
        }
    }

    # Get organization ID first
    me_resp = httpx.get(f"{BASE_URL}/users/me/organizations/", headers=HEADERS)
    org_id = me_resp.json()["organizations"][0]["id"]

    resp = httpx.post(
        f"{BASE_URL}/organizations/{org_id}/events/",
        headers=HEADERS,
        json=payload,
    )
    return resp.json()


def _optimize_event(event_id: str, content: dict) -> dict:
    """Optimize an existing Eventbrite event (tags, description, visibility)."""
    payload = {"event": {}}

    if "description" in content:
        payload["event"]["description"] = {"html": content["description"]}
    if "title" in content:
        payload["event"]["name"] = {"html": content["title"]}

    payload["event"]["listed"] = True

    resp = httpx.post(
        f"{BASE_URL}/events/{event_id}/",
        headers=HEADERS,
        json=payload,
    )
    return resp.json()


def distribute(location: dict, content: dict, show: dict) -> dict:
    """Create or optimize an Eventbrite event."""
    try:
        if show.get("ticket_platform") == "eventbrite" and show.get("eventbrite_url"):
            # Optimize existing event
            event_id = _extract_event_id(show["eventbrite_url"])
            result = _optimize_event(event_id, content)
            url = show["eventbrite_url"]
        else:
            # Create new event
            result = _create_event(content, show)
            url = result.get("url", f"https://www.eventbrite.ca/e/{result.get('id', 'unknown')}")

        return {"status": "posted", "url": url}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_distributor_eventbrite.py -v
```

Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/distributors/eventbrite.py tests/test_distributor_eventbrite.py
git commit -m "feat: add Eventbrite distributor with create and optimize modes"
```

---

## Task 9: Distributor — Bandsintown

**Files:**
- Create: `src/distributors/bandsintown.py`
- Create: `tests/test_distributor_bandsintown.py`

**Step 1: Write the failing test**

```python
# tests/test_distributor_bandsintown.py
from unittest.mock import patch, MagicMock
from src.distributors.bandsintown import distribute


def test_distribute_creates_event():
    """Should submit event to Bandsintown API."""
    location = {"id": "bandsintown", "platform": "bandsintown"}
    content = {
        "artist": "The MAS Project",
        "description": "Live jazz at The Rex",
        "ticket_url": "https://eventbrite.ca/e/123",
    }
    show = {
        "title": "MAS Project at The Rex",
        "date": "2025-03-15T20:00:00",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "city": "Toronto",
        "artists": ["The MAS Project"],
        "ticket_url": "https://eventbrite.ca/e/123",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "456", "url": "https://bandsintown.com/e/456"}

    with patch("src.distributors.bandsintown.httpx.post", return_value=mock_response):
        result = distribute(location, content, show)

    assert result["status"] == "posted"


def test_distribute_handles_failure():
    location = {"id": "bandsintown", "platform": "bandsintown"}
    content = {"artist": "Test"}
    show = {"artists": ["Test"], "date": "2025-03-15T20:00:00"}

    with patch("src.distributors.bandsintown.httpx.post", side_effect=Exception("Network error")):
        result = distribute(location, content, show)

    assert result["status"] == "failed"
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_distributor_bandsintown.py -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# src/distributors/bandsintown.py
import httpx
import config

BASE_URL = "https://rest.bandsintown.com"


def distribute(location: dict, content: dict, show: dict) -> dict:
    """Submit an event to Bandsintown."""
    try:
        artist_name = content.get("artist") or show.get("artists", ["Unknown"])[0]

        payload = {
            "artist_name": artist_name,
            "datetime": show.get("date", ""),
            "venue": {
                "name": show.get("venue", ""),
                "city": show.get("city", "Toronto"),
                "country": "Canada",
            },
            "ticket_url": content.get("ticket_url") or show.get("ticket_url", ""),
            "description": content.get("description", ""),
            "app_id": config.BANDSINTOWN_APP_ID,
        }

        resp = httpx.post(
            f"{BASE_URL}/artists/{artist_name}/events",
            params={"app_id": config.BANDSINTOWN_APP_ID},
            json=payload,
        )

        result_data = resp.json()
        url = result_data.get("url", f"https://www.bandsintown.com/{artist_name}")
        return {"status": "posted", "url": url}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_distributor_bandsintown.py -v
```

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/distributors/bandsintown.py tests/test_distributor_bandsintown.py
git commit -m "feat: add Bandsintown distributor"
```

---

## Task 10: Distributor — ConcertsTO (Agent-Based)

**Files:**
- Create: `src/distributors/concertsto.py`
- Create: `tests/test_distributor_concertsto.py`

**Step 1: Write the failing test**

```python
# tests/test_distributor_concertsto.py
from unittest.mock import patch, MagicMock, AsyncMock
from src.distributors.concertsto import distribute


def test_distribute_returns_posted_on_success():
    """Should launch browser, fill form, return success."""
    location = {"id": "concertsto", "platform": "concertsto", "target": "https://concertsto.com/"}
    content = {
        "artist": "The MAS Project",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "date": "March 15, 2025",
        "description": "Live jazz night",
        "ticket_url": "https://eventbrite.ca/e/123",
    }
    show = {"title": "MAS Project at The Rex", "date": "2025-03-15T20:00:00"}

    with patch("src.distributors.concertsto._run_browser_agent") as mock_agent:
        mock_agent.return_value = {"status": "posted", "url": "https://concertsto.com/concerts/123"}
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "concertsto.com" in result["url"]


def test_distribute_handles_failure():
    location = {"id": "concertsto", "platform": "concertsto", "target": "https://concertsto.com/"}
    content = {"artist": "Test"}
    show = {}

    with patch("src.distributors.concertsto._run_browser_agent") as mock_agent:
        mock_agent.side_effect = Exception("Browser timeout")
        result = distribute(location, content, show)

    assert result["status"] == "failed"
    assert "Browser timeout" in result["error"]
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_distributor_concertsto.py -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# src/distributors/concertsto.py
import base64
import anthropic
import config
from playwright.sync_api import sync_playwright

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

TARGET_URL = "https://concertsto.com/"


def _take_screenshot(page) -> str:
    """Take a screenshot and return as base64."""
    screenshot_bytes = page.screenshot()
    return base64.b64encode(screenshot_bytes).decode("utf-8")


def _run_browser_agent(content: dict, show: dict) -> dict:
    """Use Playwright + Claude computer use to fill out the ConcertsTO 'Add Concerts' form."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")

        # Agent loop: screenshot → Claude decides action → execute → repeat
        max_steps = 15
        for step in range(max_steps):
            screenshot_b64 = _take_screenshot(page)

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
                    },
                    {
                        "type": "text",
                        "text": f"""You are filling out a concert submission form on concertsto.com.

Concert details to submit:
- Artist: {content.get('artist', show.get('title', ''))}
- Venue: {content.get('venue', show.get('venue', ''))}
- Date: {content.get('date', show.get('date', ''))}
- Description: {content.get('description', '')}
- Ticket URL: {content.get('ticket_url', show.get('ticket_url', ''))}

Look at the screenshot. What is the next action to take?
If you need to click something, respond with: CLICK x y
If you need to type something, respond with: TYPE text_to_type
If you need to press a key, respond with: PRESS key_name
If the form has been submitted successfully, respond with: DONE url_of_submission
If something went wrong, respond with: ERROR description

Respond with ONLY one action line, nothing else."""
                    }
                ],
            }]

            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=256,
                messages=messages,
            )

            action = response.content[0].text.strip()

            if action.startswith("DONE"):
                url = action.replace("DONE", "").strip() or f"{TARGET_URL}concerts"
                browser.close()
                return {"status": "posted", "url": url}
            elif action.startswith("ERROR"):
                error_msg = action.replace("ERROR", "").strip()
                browser.close()
                return {"status": "failed", "error": error_msg}
            elif action.startswith("CLICK"):
                parts = action.split()
                x, y = int(parts[1]), int(parts[2])
                page.mouse.click(x, y)
            elif action.startswith("TYPE"):
                text = action.replace("TYPE", "", 1).strip()
                page.keyboard.type(text)
            elif action.startswith("PRESS"):
                key = action.replace("PRESS", "").strip()
                page.keyboard.press(key)

            page.wait_for_timeout(1000)

        browser.close()
        return {"status": "failed", "error": "Max steps reached without completing form submission"}


def distribute(location: dict, content: dict, show: dict) -> dict:
    """Submit a concert to ConcertsTO via browser agent."""
    try:
        return _run_browser_agent(content, show)
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_distributor_concertsto.py -v
```

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/distributors/concertsto.py tests/test_distributor_concertsto.py
git commit -m "feat: add ConcertsTO agent-based distributor with Playwright + Claude vision"
```

---

## Task 11: Distributor Registry & Orchestrator

**Files:**
- Modify: `src/distributors/__init__.py`
- Create: `src/distribute.py`
- Create: `tests/test_distribute.py`

**Step 1: Write the failing test**

```python
# tests/test_distribute.py
from unittest.mock import patch
from src.distribute import distribute_all


def test_distribute_all_eventbrite_runs_first():
    """Eventbrite should distribute before other platforms."""
    call_order = []

    def fake_eventbrite(location, content, show):
        call_order.append("eventbrite")
        return {"status": "posted", "url": "https://eventbrite.ca/e/123"}

    def fake_reddit(location, content, show):
        call_order.append("reddit")
        return {"status": "posted", "url": "https://reddit.com/r/test/123"}

    def fake_concertsto(location, content, show):
        call_order.append("concertsto")
        return {"status": "posted", "url": "https://concertsto.com/123"}

    approved = [
        {"id": "reddit_test", "platform": "reddit", "content": {"title": "T", "body": "B"}},
        {"id": "eventbrite", "platform": "eventbrite", "content": {"title": "T"}},
        {"id": "concertsto", "platform": "concertsto", "content": {"artist": "A"}},
    ]
    show = {"title": "Test", "eventbrite_url": None}

    mock_distributors = {
        "reddit": fake_reddit,
        "eventbrite": fake_eventbrite,
        "concertsto": fake_concertsto,
    }

    with patch("src.distribute.DISTRIBUTORS", mock_distributors):
        results = distribute_all(approved, show)

    assert call_order[0] == "eventbrite"
    assert len(results) == 3
    assert show["eventbrite_url"] == "https://eventbrite.ca/e/123"


def test_distribute_all_handles_partial_failure():
    """If one distributor fails, others should still run."""
    def fake_ok(location, content, show):
        return {"status": "posted", "url": "https://example.com"}

    def fake_fail(location, content, show):
        return {"status": "failed", "error": "API down"}

    approved = [
        {"id": "eventbrite", "platform": "eventbrite", "content": {"title": "T"}},
        {"id": "reddit_test", "platform": "reddit", "content": {"title": "T", "body": "B"}},
    ]
    show = {"eventbrite_url": None}

    mock_distributors = {"eventbrite": fake_fail, "reddit": fake_ok}

    with patch("src.distribute.DISTRIBUTORS", mock_distributors):
        results = distribute_all(approved, show)

    assert len(results) == 2
    assert results[0]["status"] == "failed"
    assert results[1]["status"] == "posted"
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_distribute.py -v
```

Expected: FAIL

**Step 3: Write the registry**

```python
# src/distributors/__init__.py
from src.distributors.reddit import distribute as reddit_distribute
from src.distributors.eventbrite import distribute as eventbrite_distribute
from src.distributors.bandsintown import distribute as bandsintown_distribute
from src.distributors.concertsto import distribute as concertsto_distribute

# === API-Based Distribution ===

# -- Media --
DISTRIBUTORS = {
    "reddit": reddit_distribute,
}

# -- Concert Listing Sites --
DISTRIBUTORS.update({
    "eventbrite": eventbrite_distribute,
    "bandsintown": bandsintown_distribute,
})

# === Agent-Based Distribution ===

# -- Concert Listing Sites --
DISTRIBUTORS.update({
    "concertsto": concertsto_distribute,
})
```

**Step 4: Write the orchestrator**

```python
# src/distribute.py
from src.distributors import DISTRIBUTORS


def distribute_all(approved_locations: list[dict], show: dict) -> list[dict]:
    """Distribute content to all approved locations. Eventbrite runs first."""
    # Eventbrite first — other platforms may need its URL
    eventbrite_locations = [l for l in approved_locations if l["platform"] == "eventbrite"]
    other_locations = [l for l in approved_locations if l["platform"] != "eventbrite"]

    results = []

    for location in eventbrite_locations:
        distributor = DISTRIBUTORS[location["platform"]]
        result = distributor(location, location["content"], show)
        results.append({**location, **result})
        if result["status"] == "posted":
            show["eventbrite_url"] = result["url"]

    for location in other_locations:
        distributor = DISTRIBUTORS[location["platform"]]
        result = distributor(location, location["content"], show)
        results.append({**location, **result})

    return results
```

**Step 5: Run tests to verify they pass**

```bash
py -m pytest tests/test_distribute.py -v
```

Expected: All 2 tests PASS

**Step 6: Commit**

```bash
git add src/distributors/__init__.py src/distribute.py tests/test_distribute.py
git commit -m "feat: add distributor registry and distribution orchestrator with Eventbrite-first ordering"
```

---

## Task 12: Summarize — Post-Distribution Summary

**Files:**
- Create: `src/summarize.py`
- Create: `tests/test_summarize.py`

**Step 1: Write the failing test**

```python
# tests/test_summarize.py
import os
import tempfile
from src.summarize import generate_summary_markdown, save_summary


def test_generate_summary_markdown():
    """Should produce a markdown table with status and links."""
    show = {"title": "MAS Project", "date": "2025-03-15T20:00:00", "venue": "The Rex"}
    results = [
        {"name": "r/TorontoMusic", "status": "posted", "url": "https://reddit.com/r/TorontoMusic/abc"},
        {"name": "Eventbrite", "status": "posted", "url": "https://eventbrite.ca/e/123"},
        {"name": "Bandsintown", "status": "failed", "error": "API timeout"},
        {"name": "ConcertsTO", "status": "posted", "url": "https://concertsto.com/123"},
    ]

    md = generate_summary_markdown(show, results)

    assert "Campaign Summary" in md
    assert "r/TorontoMusic" in md
    assert "| Posted" in md or "| posted" in md.lower()
    assert "API timeout" in md
    assert "reddit.com" in md


def test_save_summary():
    tmpdir = tempfile.mkdtemp()
    md = "# Test Summary"
    path = save_summary(md, tmpdir)
    assert os.path.exists(path)
    with open(path) as f:
        assert f.read() == md
```

**Step 2: Run tests to verify they fail**

```bash
py -m pytest tests/test_summarize.py -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# src/summarize.py
import os


def generate_summary_markdown(show: dict, results: list[dict]) -> str:
    """Generate a campaign summary with a table of all distribution results."""
    title = show.get("title", "Unknown Show")
    date = show.get("date", "TBD")
    venue = show.get("venue", "TBD")

    md = f"## Campaign Summary: {title} — {date} @ {venue}\n\n"
    md += "| Location | Status | Link |\n"
    md += "|----------|--------|------|\n"

    for r in results:
        name = r.get("name", r.get("id", "Unknown"))
        status = r.get("status", "unknown").title()
        if r.get("status") == "posted":
            link = r.get("url", "N/A")
        else:
            link = r.get("error", "N/A")
        md += f"| {name} | {status} | {link} |\n"

    return md


def save_summary(md: str, campaign_dir: str) -> str:
    """Save summary markdown to campaign directory."""
    path = os.path.join(campaign_dir, "campaign_summary.md")
    with open(path, "w") as f:
        f.write(md)
    return path
```

**Step 4: Run tests to verify they pass**

```bash
py -m pytest tests/test_summarize.py -v
```

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/summarize.py tests/test_summarize.py
git commit -m "feat: add post-distribution campaign summary generator"
```

---

## Task 13: run.py — Full Pipeline Orchestrator

**Files:**
- Create: `run.py`

**Step 1: Write the implementation**

```python
# run.py
"""
Promotr — Automated show promotion pipeline.

Usage:
    py run.py <ticket_url>
    py run.py --discover          (refresh Reddit subreddit discovery)
"""
import sys
import os
import json
from datetime import datetime

import config
from src.scrape_show import scrape_show, save_show_details
from src.locations import load_locations, get_enabled_locations
from src.generate_content import generate_campaign_content
from src.review import generate_draft_markdown, parse_approved_draft, save_draft, save_approved
from src.distribute import distribute_all
from src.summarize import generate_summary_markdown, save_summary


def create_campaign_dir(show: dict) -> str:
    """Create a campaign directory based on show date and title."""
    date_str = show.get("date", "")[:10] or datetime.now().strftime("%Y-%m-%d")
    slug = show.get("title", "unknown").lower().replace(" ", "-")[:30]
    dir_name = f"{date_str}-{slug}"
    campaign_dir = os.path.join(config.CAMPAIGNS_DIR, dir_name)
    os.makedirs(campaign_dir, exist_ok=True)
    return campaign_dir


def run_pipeline(ticket_url: str):
    """Run the full promotion pipeline for a single show."""

    # Step 1: Scrape show details
    print(f"Scraping show details from: {ticket_url}")
    show = scrape_show(ticket_url)
    campaign_dir = create_campaign_dir(show)
    save_show_details(show, campaign_dir)
    print(f"Show: {show['title']} at {show['venue']} on {show['date']}")
    print(f"Campaign directory: {campaign_dir}")

    # Step 2: Load distribution locations
    locations = get_enabled_locations(load_locations(config.LOCATIONS_FILE))
    print(f"Loaded {len(locations)} enabled distribution locations")

    # Step 3: Load style guide
    with open(config.STYLE_GUIDE_FILE) as f:
        style_guide = f.read()

    # Step 4: Generate content
    print("Generating campaign content...")
    content = generate_campaign_content(show, locations, style_guide)
    print(f"Generated content for {len(content)} locations")

    # Step 5: Review
    draft_md = generate_draft_markdown(show, locations, content)
    draft_path = save_draft(draft_md, campaign_dir)
    print(f"\nCampaign draft saved to: {draft_path}")
    print("Please review the draft. Change [APPROVE] to [REJECT] for any location you want to skip.")
    input("Press Enter when you're done editing the draft...")

    # Re-read the edited draft
    with open(draft_path) as f:
        edited_draft = f.read()

    approved = parse_approved_draft(edited_draft, locations, content)
    save_approved(approved, campaign_dir)
    print(f"\n{len(approved)} locations approved for distribution")

    if not approved:
        print("No locations approved. Exiting.")
        return

    # Step 6: Distribute
    print("\nDistributing content...")
    results = distribute_all(approved, show)

    # Step 7: Summarize
    summary_md = generate_summary_markdown(show, results)
    summary_path = save_summary(summary_md, campaign_dir)
    print(f"\nCampaign summary saved to: {summary_path}")
    print("\n" + summary_md)

    # Update show details with eventbrite URL if created
    if show.get("eventbrite_url"):
        save_show_details(show, campaign_dir)


def run_discovery():
    """Run Reddit subreddit discovery."""
    from src.discover_locations import discover_and_update
    print("Running Reddit subreddit discovery...")
    locations = discover_and_update(config.LOCATIONS_FILE)
    reddit_count = sum(1 for l in locations if l["platform"] == "reddit")
    print(f"Discovery complete. {reddit_count} Reddit locations in registry.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--discover":
        run_discovery()
    else:
        run_pipeline(sys.argv[1])
```

**Step 2: Manually test the help output**

```bash
py run.py
```

Expected: Prints usage instructions

**Step 3: Commit**

```bash
git add run.py
git commit -m "feat: add pipeline orchestrator with scrape/generate/review/distribute/summarize flow"
```

---

## Task 14: Run All Tests & Final Verification

**Step 1: Run the full test suite**

```bash
py -m pytest tests/ -v
```

Expected: All tests PASS (should be ~17 tests across all test files)

**Step 2: Verify the directory structure matches the design**

```bash
find . -type f -not -path './.git/*' -not -path './__pycache__/*' | sort
```

Expected structure matches the design doc.

**Step 3: Final commit if any loose files**

```bash
git status
git add -A
git commit -m "chore: final cleanup and verification"
```

---

## Summary

| Task | Description | Est. Tests |
|------|-------------|------------|
| 1 | Project scaffolding | 0 |
| 2 | scrape_show (LLM scraper) | 3 |
| 3 | Distribution locations registry | 4 |
| 4 | discover_locations (Reddit) | 3 |
| 5 | generate_content (batched LLM) | 2 |
| 6 | review (markdown draft + parsing) | 2 |
| 7 | Distributor: Reddit | 2 |
| 8 | Distributor: Eventbrite | 3 |
| 9 | Distributor: Bandsintown | 2 |
| 10 | Distributor: ConcertsTO | 2 |
| 11 | Distributor registry + orchestrator | 2 |
| 12 | Summarize | 2 |
| 13 | run.py orchestrator | 0 (manual) |
| 14 | Full test suite verification | - |

**Total: 14 tasks, ~25 tests**

Dependencies: install `praw`, `playwright`, `python-dotenv`, `pytest` via requirements.txt (Task 1).
