"""
Promotr — Automated show promotion pipeline.

Usage:
    py run.py <ticket_url>
    py run.py --discover          (refresh Reddit subreddit discovery)
"""
import sys
import os
import json
from datetime import datetime

import config
from src.scrape_show import scrape_show, save_show_details
from src.locations import load_locations, get_enabled_locations
from src.generate_content import generate_campaign_content
from src.review import generate_draft_markdown, parse_approved_draft, save_draft, save_approved
from src.distribute import distribute_all
from src.summarize import generate_summary_markdown, save_summary


def create_campaign_dir(show: dict) -> str:
    date_str = show.get("date", "")[:10] or datetime.now().strftime("%Y-%m-%d")
    slug = show.get("title", "unknown").lower().replace(" ", "-")[:30]
    dir_name = f"{date_str}-{slug}"
    campaign_dir = os.path.join(config.CAMPAIGNS_DIR, dir_name)
    os.makedirs(campaign_dir, exist_ok=True)
    return campaign_dir


def run_pipeline(ticket_url: str):
    # Step 1: Scrape show details
    print(f"Scraping show details from: {ticket_url}")
    show = scrape_show(ticket_url)
    campaign_dir = create_campaign_dir(show)
    save_show_details(show, campaign_dir)
    print(f"Show: {show['title']} at {show['venue']} on {show['date']}")
    print(f"Campaign directory: {campaign_dir}")

    # Step 2: Load distribution locations
    locations = get_enabled_locations(load_locations(config.LOCATIONS_FILE))
    print(f"Loaded {len(locations)} enabled distribution locations")

    # Step 3: Load style guide
    with open(config.STYLE_GUIDE_FILE) as f:
        style_guide = f.read()

    # Step 4: Generate content
    print("Generating campaign content...")
    content = generate_campaign_content(show, locations, style_guide)
    print(f"Generated content for {len(content)} locations")

    # Step 5: Review
    draft_md = generate_draft_markdown(show, locations, content)
    draft_path = save_draft(draft_md, campaign_dir)
    print(f"\nCampaign draft saved to: {draft_path}")
    print("Please review the draft. Change [APPROVE] to [REJECT] for any location you want to skip.")
    input("Press Enter when you're done editing the draft...")

    # Re-read the edited draft
    with open(draft_path) as f:
        edited_draft = f.read()

    approved = parse_approved_draft(edited_draft, locations, content)
    save_approved(approved, campaign_dir)
    print(f"\n{len(approved)} locations approved for distribution")

    if not approved:
        print("No locations approved. Exiting.")
        return

    # Step 6: Distribute
    print("\nDistributing content...")
    results = distribute_all(approved, show)

    # Step 7: Summarize
    summary_md = generate_summary_markdown(show, results)
    summary_path = save_summary(summary_md, campaign_dir)
    print(f"\nCampaign summary saved to: {summary_path}")
    print("\n" + summary_md)

    # Update show details with eventbrite URL if created
    if show.get("eventbrite_url"):
        save_show_details(show, campaign_dir)


def run_discovery():
    from src.discover_locations import discover_and_update
    print("Running Reddit subreddit discovery...")
    locations = discover_and_update(config.LOCATIONS_FILE)
    reddit_count = sum(1 for l in locations if l["platform"] == "reddit")
    print(f"Discovery complete. {reddit_count} Reddit locations in registry.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--discover":
        run_discovery()
    else:
        run_pipeline(sys.argv[1])
