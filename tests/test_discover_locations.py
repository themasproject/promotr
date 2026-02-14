import json
from unittest.mock import patch, MagicMock
from src.discover_locations import (
    search_subreddits,
    fetch_subreddit_rules,
    assess_subreddits,
    build_reddit_location,
)


def test_search_subreddits_returns_list():
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
