from src.discover_locations import get_reddit_client


def distribute(location: dict, content: dict, show: dict) -> dict:
    try:
        reddit = get_reddit_client()
        subreddit = reddit.subreddit(location["target"])
        submission = subreddit.submit(
            title=content["title"],
            selftext=content["body"],
        )
        return {"status": "posted", "url": submission.url}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
