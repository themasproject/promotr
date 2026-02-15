import base64
import anthropic
import config
from playwright.sync_api import sync_playwright

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

TARGET_URL = "https://concertsto.com/"


def _take_screenshot(page) -> str:
    screenshot_bytes = page.screenshot()
    return base64.b64encode(screenshot_bytes).decode("utf-8")


def _run_browser_agent(content: dict, show: dict) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")

        max_steps = 15
        for step in range(max_steps):
            screenshot_b64 = _take_screenshot(page)

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
                    },
                    {
                        "type": "text",
                        "text": f"""You are filling out a concert submission form on concertsto.com.

Concert details to submit:
- Artist: {content.get('artist', show.get('title', ''))}
- Venue: {content.get('venue', show.get('venue', ''))}
- Date: {content.get('date', show.get('date', ''))}
- Description: {content.get('description', '')}
- Ticket URL: {content.get('ticket_url', show.get('ticket_url', ''))}

Look at the screenshot. What is the next action to take?
If you need to click something, respond with: CLICK x y
If you need to type something, respond with: TYPE text_to_type
If you need to press a key, respond with: PRESS key_name
If the form has been submitted successfully, respond with: DONE url_of_submission
If something went wrong, respond with: ERROR description

Respond with ONLY one action line, nothing else."""
                    }
                ],
            }]

            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=256,
                messages=messages,
            )

            action = response.content[0].text.strip()

            if action.startswith("DONE"):
                url = action.replace("DONE", "").strip() or f"{TARGET_URL}concerts"
                browser.close()
                return {"status": "posted", "url": url}
            elif action.startswith("ERROR"):
                error_msg = action.replace("ERROR", "").strip()
                browser.close()
                return {"status": "failed", "error": error_msg}
            elif action.startswith("CLICK"):
                parts = action.split()
                x, y = int(parts[1]), int(parts[2])
                page.mouse.click(x, y)
            elif action.startswith("TYPE"):
                text = action.replace("TYPE", "", 1).strip()
                page.keyboard.type(text)
            elif action.startswith("PRESS"):
                key = action.replace("PRESS", "").strip()
                page.keyboard.press(key)

            page.wait_for_timeout(1000)

        browser.close()
        return {"status": "failed", "error": "Max steps reached without completing form submission"}


def distribute(location: dict, content: dict, show: dict) -> dict:
    try:
        return _run_browser_agent(content, show)
    except Exception as e:
        return {"status": "failed", "error": str(e)}
