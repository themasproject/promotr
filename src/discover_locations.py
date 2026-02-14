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
        time.sleep(0.7)

    return candidates


def fetch_subreddit_rules(subreddit_name: str) -> str:
    reddit = get_reddit_client()
    try:
        rules = reddit.subreddit(subreddit_name).rules()
        return "\n".join(f"- {r['short_name']}: {r.get('description', '')}" for r in rules)
    except Exception:
        return "Could not fetch rules."


def assess_subreddits(candidates: list[dict]) -> list[dict]:
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
    from src.locations import load_locations, save_locations, add_location

    candidates = search_subreddits()

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
