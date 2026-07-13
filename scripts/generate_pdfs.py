from __future__ import annotations

import base64
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARTIFACTS = {
    "resume.html": "Russell-Dudek-CFS-Resume.pdf",
    "cover-letter.html": "Russell-Dudek-CFS-Cover-Letter.pdf",
    "interview-brief.html": "Russell-Dudek-CFS-Interview-Brief.pdf",
    "120-day-plan.html": "Russell-Dudek-CFS-120-Day-Plan.pdf",
    "operating-lens-review.html": "Russell-Dudek-CFS-Operating-Lens-Review.pdf",
}


def inline_html(name: str) -> str:
    html = (ROOT / name).read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    css = re.sub(r"^@import.*$", "", css, flags=re.MULTILINE)
    tokens = (ROOT / "brand-tokens.css").read_text(encoding="utf-8")
    logo = base64.b64encode((ROOT / "assets/brand/cfs-logo.jpg").read_bytes()).decode("ascii")
    html = html.replace(
        '<link rel="stylesheet" href="styles.css">',
        f"<style>{tokens}\n{css}</style>",
    )
    html = html.replace(
        "assets/brand/cfs-logo.jpg",
        f"data:image/jpeg;base64,{logo}",
    )
    if '<script src="app.js"></script>' in html:
        script = (ROOT / "app.js").read_text(encoding="utf-8")
        html = html.replace('<script src="app.js"></script>', f"<script>{script}</script>")
    return html


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    executable = os.environ.get("CHROMIUM_PATH")
    launch_kwargs = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if executable:
        launch_kwargs["executable_path"] = executable

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_kwargs)
        for html_name, pdf_name in ARTIFACTS.items():
            page = browser.new_page()
            page.set_content(inline_html(html_name), wait_until="load", timeout=120_000)
            page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
            page.emulate_media(media="print")
            page.pdf(
                path=str(DOCS / pdf_name),
                format="Letter",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
