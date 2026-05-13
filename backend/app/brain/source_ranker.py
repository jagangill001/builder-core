from __future__ import annotations

from urllib.parse import urlparse

from app.tasks.task_models import SourceModel


OFFICIAL_HINTS = ("docs.", "developer.", "api.", "github.com", "cloud.google.com", "fastapi.tiangolo.com", "nextjs.org")
TRUSTED_HINTS = (".gov", ".edu", "reuters.com", "apnews.com", "bbc.com", "theverge.com")
MEDIUM_HINTS = ("medium.com", "dev.to", "stackoverflow.com", "reddit.com", "forum", "blog")


def rank_source(title: str, url: str, snippet: str = "") -> SourceModel:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not url:
        return SourceModel(
            title=title,
            url=url,
            snippet=snippet,
            rank="low",
            reason="No source URL is available, so this cannot be treated as verified.",
        )
    if any(hint in host for hint in OFFICIAL_HINTS):
        return SourceModel(title=title, url=url, snippet=snippet, rank="highest", reason="Official source or documentation domain.")
    if any(hint in host for hint in TRUSTED_HINTS):
        return SourceModel(title=title, url=url, snippet=snippet, rank="high", reason="Trusted news, education, or government source.")
    if any(hint in host for hint in MEDIUM_HINTS):
        return SourceModel(title=title, url=url, snippet=snippet, rank="medium", reason="Community, blog, or forum source.")
    return SourceModel(title=title, url=url, snippet=snippet, rank="low", reason="Unknown source reputation.")
