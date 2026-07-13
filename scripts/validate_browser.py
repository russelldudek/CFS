from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ROUTES = [
    "index.html",
    "resume.html",
    "cover-letter.html",
    "interview-brief.html",
    "120-day-plan.html",
    "operating-lens-review.html",
    "sources.html",
]
VIEWPORTS = [(1440, 900), (1280, 800), (768, 1024), (390, 844)]


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
    findings: list[str] = []
    passes = 0
    executable = os.environ.get("CHROMIUM_PATH")
    launch_kwargs = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if executable:
        launch_kwargs["executable_path"] = executable

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_kwargs)
        for route in ROUTES:
            html = inline_html(route)
            for width, height in VIEWPORTS:
                errors: list[str] = []
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("console", lambda msg, out=errors: out.append(f"console:{msg.type}:{msg.text}") if msg.type == "error" else None)
                page.on("pageerror", lambda err, out=errors: out.append(f"pageerror:{err}"))
                page.set_content(html, wait_until="load", timeout=120_000)
                data = page.evaluate("""() => {
                    const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
                    const duplicates = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
                    const badImages = [...document.images]
                        .filter(img => !img.complete || img.naturalWidth === 0)
                        .map(img => img.alt || img.src.slice(0, 60));
                    return {
                        scrollWidth: document.documentElement.scrollWidth,
                        clientWidth: document.documentElement.clientWidth,
                        duplicates,
                        badImages
                    };
                }""")
                if data["scrollWidth"] > data["clientWidth"] + 1:
                    findings.append(f"{route} {width}x{height}: horizontal overflow")
                if data["duplicates"]:
                    findings.append(f"{route} {width}x{height}: duplicate IDs {data['duplicates']}")
                if data["badImages"]:
                    findings.append(f"{route} {width}x{height}: broken images {data['badImages']}")
                if errors:
                    findings.append(f"{route} {width}x{height}: {errors}")
                if route == "index.html" and width > 840:
                    overlaps = page.evaluate("""() => [...document.querySelectorAll('.proof-item')].map(item => {
                        const role = item.querySelector('.proof-role strong');
                        const copy = item.querySelector('.proof-copy');
                        const marker = getComputedStyle(copy, '::before');
                        const roleRect = role.getBoundingClientRect();
                        const copyRect = copy.getBoundingClientRect();
                        const markerLeft = copyRect.left + parseFloat(marker.left);
                        return {name: role.textContent.trim(), roleRight: roleRect.right, markerLeft};
                    }).filter(item => item.roleRight > item.markerLeft - 4)""")
                    if overlaps:
                        findings.append(f"{route} {width}x{height}: proof labels overlap markers {overlaps}")
                passes += 1
                page.close()

        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_content(inline_html("index.html"), wait_until="load")
        page.locator('[data-scenario="conflict"]').focus()
        page.keyboard.press("Enter")
        if page.locator("#lensState").inner_text() != "Distorted":
            findings.append("Keyboard scenario transition failed")
        if page.locator('[data-scenario="conflict"]').get_attribute("aria-pressed") != "true":
            findings.append("Scenario pressed state failed")
        page.locator('[data-scenario="unowned"]').click()
        if page.locator("#lensState").inner_text() != "Unreliable":
            findings.append("Pointer scenario transition failed")
        page.close()

        page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page.set_content(inline_html("index.html"), wait_until="load")
        duration = page.locator(".source-chip").first.evaluate("el => getComputedStyle(el).animationDuration")
        if duration not in {"0s", "0.000001s", "0.001ms", "1e-06s"}:
            findings.append(f"Reduced-motion duration unexpected: {duration}")
        page.close()
        browser.close()

    print(json.dumps({"passes": passes, "findings": findings}, indent=2))
    if findings:
        sys.exit(1)


if __name__ == "__main__":
    main()
