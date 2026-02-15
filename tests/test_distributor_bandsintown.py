from unittest.mock import patch, MagicMock
from src.distributors.bandsintown import distribute


def test_distribute_creates_event():
    location = {"id": "bandsintown", "platform": "bandsintown"}
    content = {
        "artist": "The MAS Project",
        "description": "Live jazz at The Rex",
        "ticket_url": "https://eventbrite.ca/e/123",
    }
    show = {
        "title": "MAS Project at The Rex",
        "date": "2025-03-15T20:00:00",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "city": "Toronto",
        "artists": ["The MAS Project"],
        "ticket_url": "https://eventbrite.ca/e/123",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "456", "url": "https://bandsintown.com/e/456"}

    with patch("src.distributors.bandsintown.httpx.post", return_value=mock_response):
        result = distribute(location, content, show)

    assert result["status"] == "posted"


def test_distribute_handles_failure():
    location = {"id": "bandsintown", "platform": "bandsintown"}
    content = {"artist": "Test"}
    show = {"artists": ["Test"], "date": "2025-03-15T20:00:00"}

    with patch("src.distributors.bandsintown.httpx.post", side_effect=Exception("Network error")):
        result = distribute(location, content, show)

    assert result["status"] == "failed"
