import re
import httpx
import config

BASE_URL = "https://www.eventbriteapi.com/v3"
HEADERS = {"Authorization": f"Bearer {config.EVENTBRITE_TOKEN}"}


def _extract_event_id(url: str) -> str:
    match = re.search(r"-(\d+)/?$", url)
    if match:
        return match.group(1)
    match = re.search(r"/e/(\d+)", url)
    if match:
        return match.group(1)
    return url.split("-")[-1].rstrip("/")


def _create_event(content: dict, show: dict) -> dict:
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

    me_resp = httpx.get(f"{BASE_URL}/users/me/organizations/", headers=HEADERS)
    me_data = me_resp.json()
    orgs = me_data.get("organizations", [])
    org_id = orgs[0]["id"] if orgs else me_data.get("id", "")

    resp = httpx.post(
        f"{BASE_URL}/organizations/{org_id}/events/",
        headers=HEADERS,
        json=payload,
    )
    return resp.json()


def _optimize_event(event_id: str, content: dict) -> dict:
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
    try:
        if show.get("ticket_platform") == "eventbrite" and show.get("eventbrite_url"):
            event_id = _extract_event_id(show["eventbrite_url"])
            result = _optimize_event(event_id, content)
            url = show["eventbrite_url"]
        else:
            result = _create_event(content, show)
            url = result.get("url", f"https://www.eventbrite.ca/e/{result.get('id', 'unknown')}")

        return {"status": "posted", "url": url}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
