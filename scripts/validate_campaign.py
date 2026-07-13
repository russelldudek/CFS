from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PAGES = {
    "Russell-Dudek-CFS-Resume.pdf": 2,
    "Russell-Dudek-CFS-Cover-Letter.pdf": 1,
    "Russell-Dudek-CFS-Interview-Brief.pdf": 3,
    "Russell-Dudek-CFS-120-Day-Plan.pdf": 3,
    "Russell-Dudek-CFS-Operating-Lens-Review.pdf": 1,
}
TEXT_EXTENSIONS = {".html", ".css", ".js", ".py", ".yml", ".yaml", ".md", ".txt", ".xml", ".json", ".svg"}
FORBIDDEN = re.compile("role" + r"[\s_-]*" + "forge", re.IGNORECASE)


def fail(message: str) -> None:
    raise AssertionError(message)


def check_pdfs() -> None:
    for filename, expected_count in EXPECTED_PAGES.items():
        path = ROOT / "docs" / filename
        if not path.exists() or path.stat().st_size == 0:
            fail(f"Missing or empty PDF: {path}")
        reader = PdfReader(str(path))
        if len(reader.pages) != expected_count:
            fail(f"{filename}: expected {expected_count} pages, found {len(reader.pages)}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if "Russell" not in text or "Dudek" not in text:
            fail(f"Candidate identity missing from {filename}")
        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            if round(width) != 612 or round(height) != 792:
                fail(f"{filename}: non-Letter page {width} x {height}")
        metadata_text = " ".join(str(value or "") for value in (reader.metadata or {}).values())
        if FORBIDDEN.search(text) or FORBIDDEN.search(metadata_text):
            fail(f"Internal system name found in {filename}")


def check_public_tree() -> None:
    ignored = {".git", "_renders", "_screens", "__pycache__"}
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if FORBIDDEN.search(relative):
            hits.append(relative)
        if path.suffix.lower() in TEXT_EXTENSIONS:
            if FORBIDDEN.search(path.read_text(encoding="utf-8", errors="replace")):
                hits.append(relative)
    if hits:
        fail(f"Forbidden public-tree matches: {sorted(set(hits))}")


def check_contacts_and_links() -> None:
    resume = (ROOT / "resume.html").read_text(encoding="utf-8")
    cover = (ROOT / "cover-letter.html").read_text(encoding="utf-8")
    for value in (
        "Pittsburgh, Pennsylvania",
        "412.287.8640",
        "russelldudek@gmail.com",
        "linkedin.com/in/russelldudek",
    ):
        if value not in resume or value not in cover:
            fail(f"Missing verified contact value: {value}")
    if "Justin Bentham" not in cover or "jbentham@cfstaffing.com" not in cover:
        fail("Justin Bentham addressee block is incomplete")
    if 'href="cover-letter.html"' not in resume or "View Cover Letter" not in resume:
        fail("Resume reciprocal navigation missing")
    if 'href="resume.html"' not in cover or "View Resume" not in cover:
        fail("Cover-letter reciprocal navigation missing")


def check_relative_links() -> None:
    for html_path in ROOT.glob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http:", "https:", "mailto:", "tel:", "#")):
                continue
            target = href.split("#", 1)[0]
            if target and not (ROOT / target).exists():
                fail(f"{html_path.name}: missing relative target {href}")


def main() -> None:
    check_pdfs()
    check_public_tree()
    check_contacts_and_links()
    check_relative_links()
    print("Campaign validation passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Campaign validation failed: {exc}", file=sys.stderr)
        raise
