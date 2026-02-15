import json
from unittest.mock import patch, MagicMock
from src.generate_content import generate_campaign_content, build_prompt


def test_build_prompt_includes_all_components():
    show = {"title": "Test Show", "venue": "The Rex", "date": "2025-03-15T20:00:00"}
    locations = [
        {"id": "reddit_test", "name": "r/TestSub", "platform": "reddit", "category": "media", "rules": "No spam"},
        {"id": "eventbrite", "name": "Eventbrite", "platform": "eventbrite", "category": "concert_listing", "rules": "Include tags"},
    ]
    style_guide = "Casual, warm, community-focused."

    prompt = build_prompt(show, locations, style_guide)

    assert "Test Show" in prompt
    assert "The Rex" in prompt
    assert "r/TestSub" in prompt
    assert "No spam" in prompt
    assert "Eventbrite" in prompt
    assert "Casual, warm" in prompt


def test_generate_campaign_content():
    show = {"title": "Test Show", "venue": "The Rex"}
    locations = [
        {"id": "reddit_test", "name": "r/TestSub", "platform": "reddit", "category": "media", "rules": None},
    ]

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "reddit_test": {
            "title": "Test Show at The Rex",
            "body": "Hey Toronto! Come check out Test Show...",
        }
    }))]

    with patch("src.generate_content.client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        result = generate_campaign_content(show, locations, "Be casual.")

    assert "reddit_test" in result
    assert "title" in result["reddit_test"]
