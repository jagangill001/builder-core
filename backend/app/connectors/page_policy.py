from __future__ import annotations

from dataclasses import dataclass
from urllib import parse as urlparse

BLOCKED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
}
BLOCKED_PATH_TERMS = {
    "login",
    "signin",
    "sign-in",
    "account",
    "subscribe",
    "paywall",
    "checkout",
    "cart",
}
BLOCKED_EXTENSIONS = {
    ".zip",
    ".exe",
    ".dmg",
    ".pkg",
    ".msi",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}


@dataclass(frozen=True)
class PagePolicyDecision:
    allowed: bool
    reason: str


def evaluate_page_url(url: str) -> PagePolicyDecision:
    clean_url = (url or "").strip()
    if not clean_url:
        return PagePolicyDecision(False, "URL is empty.")

    try:
        parsed = urlparse.urlparse(clean_url)
    except Exception:
        return PagePolicyDecision(False, "URL could not be parsed.")

    if parsed.scheme not in {"http", "https"}:
        return PagePolicyDecision(False, "Only public http and https pages are allowed.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return PagePolicyDecision(False, "URL hostname is missing.")

    if hostname.startswith("www."):
        hostname = hostname[4:]
    if hostname in BLOCKED_DOMAINS or any(hostname.endswith(f".{domain}") for domain in BLOCKED_DOMAINS):
        return PagePolicyDecision(False, "Private or social-media pages are not opened by the safe page reader.")

    path = (parsed.path or "").lower()
    if any(term in path for term in BLOCKED_PATH_TERMS):
        return PagePolicyDecision(False, "Login, account, subscription, and paywall pages are not opened.")
    if any(path.endswith(extension) for extension in BLOCKED_EXTENSIONS):
        return PagePolicyDecision(False, "File downloads are not opened by the safe page reader.")

    return PagePolicyDecision(True, "URL allowed by safe page policy.")
