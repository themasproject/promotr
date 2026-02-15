from src.distributors import DISTRIBUTORS


def distribute_all(approved_locations: list[dict], show: dict) -> list[dict]:
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
