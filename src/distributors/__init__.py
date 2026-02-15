from src.distributors.reddit import distribute as reddit_distribute
from src.distributors.eventbrite import distribute as eventbrite_distribute
from src.distributors.bandsintown import distribute as bandsintown_distribute
from src.distributors.concertsto import distribute as concertsto_distribute
from src.distributors.musiccrawler import distribute as musiccrawler_distribute

# === API-Based Distribution ===

# -- Media --
DISTRIBUTORS = {
    "reddit": reddit_distribute,
}

# -- Concert Listing Sites --
DISTRIBUTORS.update({
    "eventbrite": eventbrite_distribute,
    "bandsintown": bandsintown_distribute,
})

# === Agent-Based Distribution ===

# -- Concert Listing Sites --
DISTRIBUTORS.update({
    "concertsto": concertsto_distribute,
    "musiccrawler": musiccrawler_distribute,
})
