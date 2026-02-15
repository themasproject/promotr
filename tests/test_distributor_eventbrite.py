from unittest.mock import patch, MagicMock
from src.distributors.eventbrite import distribute


def test_distribute_creates_event_for_non_eventbrite_source():
    location = {"id": "eventbrite", "platform": "eventbrite"}
    content = {
        "title": "MAS Project at The Rex",
        "description": "Jazz night in Toronto",
        "tags": ["jazz", "toronto"],
    }
    show = {
        "title": "MAS Project",
        "ticket_platform": "showpass",
        "ticket_url": "https://showpass.com/event/123",
        "source_url": "https://showpass.com/event/123",
        "eventbrite_url": None,
        "date": "2025-03-15T20:00:00",
        "venue": "The Rex",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "999", "url": "https://www.eventbrite.ca/e/999"}

    with patch("src.distributors.eventbrite.httpx") as mock_httpx:
        mock_httpx.post.return_value = mock_response
        mock_httpx.get.return_value = mock_response
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "eventbrite" in result["url"]


def test_distribute_optimizes_existing_eventbrite_event():
    location = {"id": "eventbrite", "platform": "eventbrite"}
    content = {
        "title": "MAS Project at The Rex",
        "description": "Updated jazz night description",
        "tags": ["jazz", "toronto", "live-music"],
    }
    show = {
        "title": "MAS Project",
        "ticket_platform": "eventbrite",
        "ticket_url": "https://www.eventbrite.ca/e/123",
        "source_url": "https://www.eventbrite.ca/e/123",
        "eventbrite_url": "https://www.eventbrite.ca/e/123",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "123", "url": "https://www.eventbrite.ca/e/123"}

    with patch("src.distributors.eventbrite.httpx") as mock_httpx:
        mock_httpx.post.return_value = mock_response
        mock_httpx.get.return_value = mock_response
        result = distribute(location, content, show)

    assert result["status"] == "posted"


def test_distribute_handles_failure():
    location = {"id": "eventbrite", "platform": "eventbrite"}
    content = {"title": "Test"}
    show = {"ticket_platform": "showpass", "eventbrite_url": None}

    with patch("src.distributors.eventbrite.httpx") as mock_httpx:
        mock_httpx.post.side_effect = Exception("API error")
        result = distribute(location, content, show)

    assert result["status"] == "failed"
