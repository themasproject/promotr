import json


def load_locations(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["locations"]


def save_locations(locations: list[dict], path: str) -> None:
    with open(path, "w") as f:
        json.dump({"locations": locations}, f, indent=2)


def get_enabled_locations(locations: list[dict]) -> list[dict]:
    return [loc for loc in locations if loc.get("enabled", False)]


def get_locations_by_type(locations: list[dict], loc_type: str) -> list[dict]:
    return [loc for loc in locations if loc.get("type") == loc_type]


def get_locations_by_category(locations: list[dict], category: str) -> list[dict]:
    return [loc for loc in locations if loc.get("category") == category]


def add_location(locations: list[dict], new_location: dict) -> list[dict]:
    locations = [loc for loc in locations if loc["id"] != new_location["id"]]
    locations.append(new_location)
    return locations
