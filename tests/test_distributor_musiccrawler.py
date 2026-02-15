from unittest.mock import patch, MagicMock
from src.distributors.musiccrawler import distribute


def test_distribute_returns_posted_on_success():
    location = {"id": "musiccrawler", "platform": "musiccrawler", "target": "https://musiccrawler.live/"}
    content = {
        "artist": "The MAS Project",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "date": "March 15, 2025",
        "description": "Live jazz night",
        "ticket_url": "https://eventbrite.ca/e/123",
    }
    show = {"title": "MAS Project at The Rex", "date": "2025-03-15T20:00:00"}

    with patch("src.distributors.musiccrawler._run_browser_agent") as mock_agent:
        mock_agent.return_value = {"status": "posted", "url": "https://musiccrawler.live/events/123"}
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "musiccrawler.live" in result["url"]


def test_distribute_handles_failure():
    location = {"id": "musiccrawler", "platform": "musiccrawler", "target": "https://musiccrawler.live/"}
    content = {"artist": "Test"}
    show = {}

    with patch("src.distributors.musiccrawler._run_browser_agent") as mock_agent:
        mock_agent.side_effect = Exception("Browser timeout")
        result = distribute(location, content, show)

    assert result["status"] == "failed"
    assert "Browser timeout" in result["error"]
