from unittest.mock import patch, MagicMock
from src.distributors.concertsto import distribute


def test_distribute_returns_posted_on_success():
    location = {"id": "concertsto", "platform": "concertsto", "target": "https://concertsto.com/"}
    content = {
        "artist": "The MAS Project",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "date": "March 15, 2025",
        "description": "Live jazz night",
        "ticket_url": "https://eventbrite.ca/e/123",
    }
    show = {"title": "MAS Project at The Rex", "date": "2025-03-15T20:00:00"}

    with patch("src.distributors.concertsto._run_browser_agent") as mock_agent:
        mock_agent.return_value = {"status": "posted", "url": "https://concertsto.com/concerts/123"}
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "concertsto.com" in result["url"]


def test_distribute_handles_failure():
    location = {"id": "concertsto", "platform": "concertsto", "target": "https://concertsto.com/"}
    content = {"artist": "Test"}
    show = {}

    with patch("src.distributors.concertsto._run_browser_agent") as mock_agent:
        mock_agent.side_effect = Exception("Browser timeout")
        result = distribute(location, content, show)

    assert result["status"] == "failed"
    assert "Browser timeout" in result["error"]
