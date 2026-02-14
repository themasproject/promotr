import json
from unittest.mock import patch, MagicMock
from src.scrape_show import scrape_show, extract_show_details


def test_extract_show_details_returns_structured_json():
    fake_html = "<html><body><h1>The MAS Project</h1><p>March 15, 2025 at The Rex</p></body></html>"

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "title": "The MAS Project",
        "date": "2025-03-15T20:00:00",
        "venue": "The Rex Hotel Jazz & Blues Bar",
        "city": "Toronto",
        "artists": ["The MAS Project"],
        "description": "Live jazz performance",
        "price": "$15",
        "ticket_url": "https://www.eventbrite.ca/e/123",
        "ticket_platform": "eventbrite"
    }))]

    with patch("src.scrape_show.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        result = extract_show_details(fake_html, "https://www.eventbrite.ca/e/123")

    assert result["title"] == "The MAS Project"
    assert result["city"] == "Toronto"
    assert result["ticket_platform"] == "eventbrite"
    assert result["source_url"] == "https://www.eventbrite.ca/e/123"
    assert result["eventbrite_url"] is None or isinstance(result["eventbrite_url"], str)


def test_scrape_show_fetches_page_and_extracts():
    fake_html = "<html><body>Show info</body></html>"

    with patch("src.scrape_show.httpx.get") as mock_get, \
         patch("src.scrape_show.extract_show_details") as mock_extract:
        mock_get.return_value = MagicMock(text=fake_html, status_code=200)
        mock_extract.return_value = {"title": "Test Show", "source_url": "https://example.com"}

        result = scrape_show("https://example.com")

    assert result["title"] == "Test Show"
    mock_get.assert_called_once_with("https://example.com", follow_redirects=True, timeout=30)


def test_detect_eventbrite_platform():
    from src.scrape_show import detect_platform
    assert detect_platform("https://www.eventbrite.ca/e/some-event-123") == "eventbrite"
    assert detect_platform("https://showpass.com/events/something") == "showpass"
    assert detect_platform("https://www.ticketmaster.ca/event/123") == "ticketmaster"
    assert detect_platform("https://randomsite.com/tickets") == "unknown"
