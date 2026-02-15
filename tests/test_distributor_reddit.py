from unittest.mock import patch, MagicMock
from src.distributors.reddit import distribute


def test_distribute_posts_to_subreddit():
    location = {
        "id": "reddit_torontomusic",
        "platform": "reddit",
        "target": "TorontoMusic",
    }
    content = {"title": "Show at The Rex", "body": "Come check us out!"}
    show = {"title": "MAS Project", "ticket_url": "https://eventbrite.ca/e/123"}

    mock_submission = MagicMock()
    mock_submission.url = "https://www.reddit.com/r/TorontoMusic/comments/abc123"

    mock_subreddit = MagicMock()
    mock_subreddit.submit.return_value = mock_submission

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("src.distributors.reddit.get_reddit_client", return_value=mock_reddit):
        result = distribute(location, content, show)

    assert result["status"] == "posted"
    assert "reddit.com" in result["url"]
    mock_subreddit.submit.assert_called_once_with(
        title="Show at The Rex",
        selftext="Come check us out!",
    )


def test_distribute_handles_failure():
    location = {"id": "reddit_test", "platform": "reddit", "target": "TestSub"}
    content = {"title": "Test", "body": "Test body"}
    show = {}

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.submit.side_effect = Exception("API error")

    with patch("src.distributors.reddit.get_reddit_client", return_value=mock_reddit):
        result = distribute(location, content, show)

    assert result["status"] == "failed"
    assert "API error" in result["error"]
