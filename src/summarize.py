import os


def generate_summary_markdown(show: dict, results: list[dict]) -> str:
    title = show.get("title", "Unknown Show")
    date = show.get("date", "TBD")
    venue = show.get("venue", "TBD")

    md = f"## Campaign Summary: {title} — {date} @ {venue}\n\n"
    md += "| Location | Status | Link |\n"
    md += "|----------|--------|------|\n"

    for r in results:
        name = r.get("name", r.get("id", "Unknown"))
        status = r.get("status", "unknown").title()
        if r.get("status") == "posted":
            link = r.get("url", "N/A")
        else:
            link = r.get("error", "N/A")
        md += f"| {name} | {status} | {link} |\n"

    return md


def save_summary(md: str, campaign_dir: str) -> str:
    path = os.path.join(campaign_dir, "campaign_summary.md")
    with open(path, "w") as f:
        f.write(md)
    return path
