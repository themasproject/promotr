import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
BANDSINTOWN_APP_ID = os.getenv("BANDSINTOWN_APP_ID")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CAMPAIGNS_DIR = os.path.join(DATA_DIR, "campaigns")
LOCATIONS_FILE = os.path.join(DATA_DIR, "distribution_locations.json")
STYLE_GUIDE_FILE = os.path.join(DATA_DIR, "style_guide.txt")

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
