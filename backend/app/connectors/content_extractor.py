from __future__ import annotations

from html.parser import HTMLParser
from typing import Any


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript", "svg", "canvas"}:
            self._skip_depth += 1
        elif normalized == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript", "svg", "canvas"} and self._skip_depth:
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
    text = _truncate(" ".join(parser.text_parts), max_chars)
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
