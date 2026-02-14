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
    url_lower = url.lower()
    for platform, domains in PLATFORM_PATTERNS.items():
        if any(domain in url_lower for domain in domains):
            return platform
    return "unknown"


def extract_show_details(html: str, source_url: str) -> dict:
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
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]

    details = json.loads(raw_text)
    details["ticket_platform"] = platform
    details["source_url"] = source_url
    details["eventbrite_url"] = source_url if platform == "eventbrite" else None
    return details


def scrape_show(url: str) -> dict:
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    return extract_show_details(response.text, url)


def save_show_details(show: dict, campaign_dir: str) -> str:
    path = os.path.join(campaign_dir, "show_details.json")
    with open(path, "w") as f:
        json.dump(show, f, indent=2)
    return path
