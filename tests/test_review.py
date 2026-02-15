import os
import json
import tempfile
from src.review import generate_draft_markdown, parse_approved_draft


def test_generate_draft_markdown():
    locations = [
        {"id": "reddit_torontomusic", "name": "r/TorontoMusic", "type": "api", "category": "media", "platform": "reddit"},
        {"id": "eventbrite", "name": "Eventbrite", "type": "api", "category": "concert_listing", "platform": "eventbrite"},
        {"id": "concertsto", "name": "ConcertsTO", "type": "agent", "category": "concert_listing", "platform": "concertsto"},
    ]
    content = {
        "reddit_torontomusic": {"title": "Show at Rex", "body": "Come out!"},
        "eventbrite": {"title": "MAS Project", "description": "Jazz night", "tags": ["jazz"]},
        "concertsto": {"artist": "MAS Project", "venue": "The Rex"},
    }
    show = {"title": "MAS Project", "date": "2025-03-15T20:00:00", "venue": "The Rex"}

    md = generate_draft_markdown(show, locations, content)

    assert "API-Based Distribution" in md
    assert "Agent-Based Distribution" in md
    assert "Media" in md
    assert "Concert Listing Sites" in md
    assert "[APPROVE]" in md
    assert "r/TorontoMusic" in md
    assert "ConcertsTO" in md


def test_parse_approved_draft():
    draft = """# Campaign: Test

## API-Based Distribution

### Media

#### r/TorontoMusic [APPROVE]
> **Title:** Show at Rex
> **Body:** Come out!

### Concert Listing Sites

#### Eventbrite [REJECT]
> Title: MAS Project

## Agent-Based Distribution

### Concert Listing Sites

#### ConcertsTO [APPROVE]
> Artist: MAS Project
"""
    content = {
        "reddit_torontomusic": {"title": "Show at Rex", "body": "Come out!"},
        "eventbrite": {"title": "MAS Project", "description": "Jazz night"},
        "concertsto": {"artist": "MAS Project", "venue": "The Rex"},
    }
    locations = [
        {"id": "reddit_torontomusic", "name": "r/TorontoMusic", "type": "api", "category": "media", "platform": "reddit"},
        {"id": "eventbrite", "name": "Eventbrite", "type": "api", "category": "concert_listing", "platform": "eventbrite"},
        {"id": "concertsto", "name": "ConcertsTO", "type": "agent", "category": "concert_listing", "platform": "concertsto"},
    ]

    approved = parse_approved_draft(draft, locations, content)

    assert len(approved) == 2
    approved_ids = [a["id"] for a in approved]
    assert "reddit_torontomusic" in approved_ids
    assert "concertsto" in approved_ids
    assert "eventbrite" not in approved_ids
    assert approved[0]["content"] == content["reddit_torontomusic"]
