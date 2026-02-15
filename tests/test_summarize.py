import os
import tempfile
from src.summarize import generate_summary_markdown, save_summary


def test_generate_summary_markdown():
    show = {"title": "MAS Project", "date": "2025-03-15T20:00:00", "venue": "The Rex"}
    results = [
        {"name": "r/TorontoMusic", "status": "posted", "url": "https://reddit.com/r/TorontoMusic/abc"},
        {"name": "Eventbrite", "status": "posted", "url": "https://eventbrite.ca/e/123"},
        {"name": "Bandsintown", "status": "failed", "error": "API timeout"},
        {"name": "ConcertsTO", "status": "posted", "url": "https://concertsto.com/123"},
    ]

    md = generate_summary_markdown(show, results)

    assert "Campaign Summary" in md
    assert "r/TorontoMusic" in md
    assert "Posted" in md
    assert "API timeout" in md
    assert "reddit.com" in md


def test_save_summary():
    tmpdir = tempfile.mkdtemp()
    md = "# Test Summary"
    path = save_summary(md, tmpdir)
    assert os.path.exists(path)
    with open(path) as f:
        assert f.read() == md
