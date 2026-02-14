import json
import os
import tempfile
from src.locations import load_locations, save_locations, get_enabled_locations, get_locations_by_type


def _make_locations_file(locations_list):
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
