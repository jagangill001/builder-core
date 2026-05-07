from __future__ import annotations

from html.parser import HTMLParser
from typing import Any

SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "nav", "header", "footer", "aside", "form", "button", "select", "option"}
BOILERPLATE_PHRASES = {
    "jump to content",
    "main menu",
    "donate",
    "create account",
    "log in",
    "contents",
    "navigation",
    "appearance",
    "personal tools",
    "move to sidebar",
    "sidebar",
    "edit",
    "hide",
    "search search",
    "read edit view history",
    "tools tools",
    "what links here",
    "related changes",
    "upload file",
    "special pages",
    "permanent link",
    "page information",
    "cite this page",
    "get shortened url",
    "print/export",
    "download as pdf",
    "printable version",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0
        self._skip_tags: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in SKIP_TAGS or _has_boilerplate_attrs(attrs):
            self._skip_tags.append(normalized)
            self._skip_depth += 1
        elif normalized == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if self._skip_tags and normalized == self._skip_tags[-1]:
            self._skip_tags.pop()
            self._skip_depth -= 1
        elif normalized == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        clean = " ".join((data or "").split())
        if not clean:
            return
        if self._in_title:
            self.title_parts.append(clean)
            return
        if self._skip_depth:
            return
        self.text_parts.append(clean)


def extract_readable_content(html: str, max_chars: int = 6000) -> dict[str, Any]:
    parser = _TextExtractor()
    parser.feed(html or "")
    title = _truncate(" ".join(parser.title_parts), 240)
    text = _truncate(_remove_boilerplate(" ".join(parser.text_parts)), max_chars)
    return {
        "title": title,
        "text": text,
        "text_length": len(text),
    }


def _truncate(text: str, max_chars: int) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def _has_boilerplate_attrs(attrs: list[tuple[str, str | None]]) -> bool:
    for name, value in attrs:
        if name.lower() not in {"class", "id", "role", "aria-label"}:
            continue
        normalized = f" {str(value or '').lower()} "
        if any(marker in normalized for marker in (" nav", "menu", "header", "footer", "sidebar", "breadcrumb", "cookie", "search")):
            return True
    return False


def _remove_boilerplate(text: str) -> str:
    clean = " ".join((text or "").split())
    lowered = clean.lower()
    for phrase in sorted(BOILERPLATE_PHRASES, key=len, reverse=True):
        start = lowered.find(phrase)
        while start >= 0:
            end = start + len(phrase)
            clean = f"{clean[:start]} {clean[end:]}"
            lowered = clean.lower()
            start = lowered.find(phrase)
    return " ".join(clean.split())
