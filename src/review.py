import json
import os
import re


def generate_draft_markdown(show: dict, locations: list[dict], content: dict) -> str:
    title = show.get("title", "Unknown Show")
    date = show.get("date", "TBD")
    venue = show.get("venue", "TBD")
    md = f"# Campaign: {title} — {date} @ {venue}\n\n"

    groups = {}
    for loc in locations:
        loc_type = loc["type"]
        category = loc["category"]
        if loc_type not in groups:
            groups[loc_type] = {}
        if category not in groups[loc_type]:
            groups[loc_type][category] = []
        groups[loc_type][category].append(loc)

    type_labels = {"api": "API-Based Distribution", "agent": "Agent-Based Distribution"}
    category_labels = {"media": "Media", "concert_listing": "Concert Listing Sites"}

    for loc_type in ["api", "agent"]:
        if loc_type not in groups:
            continue
        md += f"## {type_labels[loc_type]}\n\n"

        for category in ["media", "concert_listing"]:
            if category not in groups[loc_type]:
                continue
            md += f"### {category_labels[category]}\n\n"

            for loc in groups[loc_type][category]:
                loc_id = loc["id"]
                md += f"#### {loc['name']} [APPROVE]\n"

                if loc_id in content:
                    loc_content = content[loc_id]
                    for key, value in loc_content.items():
                        if isinstance(value, list):
                            value = ", ".join(value)
                        md += f"> **{key.title()}:** {value}\n"
                else:
                    md += "> No content generated.\n"

                md += "\n"

    return md


def parse_approved_draft(draft: str, locations: list[dict], content: dict) -> list[dict]:
    approved = []
    name_to_loc = {loc["name"]: loc for loc in locations}

    pattern = r"####\s+(.+?)\s+\[(APPROVE|REJECT)\]"
    matches = re.findall(pattern, draft)

    for name, status in matches:
        name = name.strip()
        if status == "APPROVE" and name in name_to_loc:
            loc = name_to_loc[name].copy()
            loc["content"] = content.get(loc["id"], {})
            approved.append(loc)

    return approved


def save_draft(md: str, campaign_dir: str) -> str:
    path = os.path.join(campaign_dir, "campaign_draft.md")
    with open(path, "w") as f:
        f.write(md)
    return path


def save_approved(approved: list[dict], campaign_dir: str) -> str:
    path = os.path.join(campaign_dir, "approved_campaign.json")
    with open(path, "w") as f:
        json.dump(approved, f, indent=2)
    return path
