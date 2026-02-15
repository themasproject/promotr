from unittest.mock import patch
from src.distribute import distribute_all


def test_distribute_all_eventbrite_runs_first():
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
