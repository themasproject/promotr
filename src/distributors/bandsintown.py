import httpx
import config

BASE_URL = "https://rest.bandsintown.com"


def distribute(location: dict, content: dict, show: dict) -> dict:
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
