import json
import anthropic
import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def build_prompt(show: dict, locations: list[dict], style_guide: str) -> str:
    prompt = f"""Generate promotional content for a live music show. Create tailored content for EACH distribution location listed below.

## Style Guide
{style_guide}

## Show Details
{json.dumps(show, indent=2)}

## Distribution Locations

"""
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
