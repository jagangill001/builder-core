from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

logger = logging.getLogger(__name__)

DUCKDUCKGO_UNAVAILABLE = "DuckDuckGo search is not available right now."
LIVE_INTERNET_NOT_CONNECTED = DUCKDUCKGO_UNAVAILABLE
SEARCH_PROVIDER_FAILED = "DuckDuckGo search failed"
DISABLED_PROVIDERS = {"", "none", "off", "false", "disabled", "not_connected"}
DEFAULT_SEARCH_PROVIDER = "duckduckgo"
DEFAULT_RESULT_LIMIT = 5
MAX_RESULT_LIMIT = 8


class SearchProviderUnavailable(RuntimeError):
    pass


class SearchConnector:
    def __init__(self) -> None:
        provider = os.getenv("LIVE_SEARCH_PROVIDER", DEFAULT_SEARCH_PROVIDER).strip().lower()
        self.provider = None if provider in DISABLED_PROVIDERS else provider or DEFAULT_SEARCH_PROVIDER
        self.api_key = os.getenv("LIVE_SEARCH_API_KEY", "").strip()
        self.endpoint = os.getenv("LIVE_SEARCH_ENDPOINT", "").strip() or None

    def status(self) -> dict[str, Any]:
        configured = self._is_configured()
        runtime_available = self._runtime_available() if configured else False
        connected = bool(configured and runtime_available)
        return {
            "connected": connected,
            "provider": self.provider or DEFAULT_SEARCH_PROVIDER,
            "query": "",
            "results": [],
            "message": "Search provider duckduckgo is ready." if connected else DUCKDUCKGO_UNAVAILABLE,
            "endpoint_configured": bool(self.endpoint),
            "api_key_configured": bool(self.api_key),
            "supported_providers": ["duckduckgo", "brave", "bing", "serpapi", "generic_json"],
        }

    def search(self, query: str, limit: int = DEFAULT_RESULT_LIMIT) -> dict[str, Any]:
        clean_query = " ".join(query.strip().split())
        bounded_limit = _bounded_limit(limit)

        if not clean_query:
            return {
                "connected": False,
                "provider": self.provider or DEFAULT_SEARCH_PROVIDER,
                "query": clean_query,
                "results": [],
                "message": "Search query is empty.",
            }

        if not self._is_configured():
            return self._failed_response(clean_query, DUCKDUCKGO_UNAVAILABLE)

        try:
            if self.provider == "duckduckgo":
                results = self._duckduckgo(clean_query, bounded_limit)
            elif self.provider == "brave":
                results = self._brave(clean_query, bounded_limit)
            elif self.provider == "bing":
                results = self._bing(clean_query, bounded_limit)
            elif self.provider == "serpapi":
                results = self._serpapi(clean_query, bounded_limit)
            else:
                results = self._generic_json(clean_query, bounded_limit)
        except SearchProviderUnavailable as error:
            logger.warning("Search provider unavailable: %s", error)
            return self._failed_response(clean_query, DUCKDUCKGO_UNAVAILABLE)
        except Exception as error:
            logger.warning("Live search provider failed for query: %s", _safe_error(error))
            return self._failed_response(clean_query, f"{SEARCH_PROVIDER_FAILED}: {_safe_error(error)}")

        return {
            "connected": True,
            "provider": self.provider or DEFAULT_SEARCH_PROVIDER,
            "query": clean_query,
            "results": results,
            "message": "Search completed" if results else "Search completed, but DuckDuckGo returned no usable results.",
        }

    def _failed_response(self, query: str, message: str) -> dict[str, Any]:
        return {
            "connected": False,
            "provider": self.provider or DEFAULT_SEARCH_PROVIDER,
            "query": query,
            "results": [],
            "message": message,
        }

    def _is_configured(self) -> bool:
        if self.provider == "duckduckgo":
            return True
        if self.provider in {"brave", "bing", "serpapi"}:
            return bool(self.api_key)
        if self.provider == "generic_json":
            return bool(self.endpoint)
        return False

    def _runtime_available(self) -> bool:
        if self.provider == "duckduckgo":
            try:
                import ddgs  # noqa: F401
            except Exception:
                return False
        return True

    def _duckduckgo(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except Exception as error:
            raise SearchProviderUnavailable("The ddgs package is not installed.") from error

        try:
            with _open_ddgs(DDGS) as ddgs:
                raw_results = list(ddgs.text(query, max_results=limit))
        except Exception as error:
            raise RuntimeError(error) from error

        return _dedupe_sources([_normalize_search_result(item, "duckduckgo") for item in raw_results])[:limit]

    def _brave(self, query: str, limit: int) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://api.search.brave.com/res/v1/web/search"
        payload = self._get_json(endpoint, {"q": query}, {"X-Subscription-Token": self.api_key, "Accept": "application/json"})
        items = ((payload.get("web") or {}).get("results") or []) if isinstance(payload, dict) else []
        results = [
            _normalize_search_result(
                {
                    "title": item.get("title"),
                    "href": item.get("url"),
                    "body": item.get("description"),
                },
                "brave",
            )
            for item in items
            if isinstance(item, dict)
        ]
        return _dedupe_sources(results)[:limit]

    def _bing(self, query: str, limit: int) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://api.bing.microsoft.com/v7.0/search"
        payload = self._get_json(endpoint, {"q": query}, {"Ocp-Apim-Subscription-Key": self.api_key})
        items = ((payload.get("webPages") or {}).get("value") or []) if isinstance(payload, dict) else []
        results = [
            _normalize_search_result(
                {
                    "title": item.get("name"),
                    "href": item.get("url"),
                    "body": item.get("snippet"),
                },
                "bing",
            )
            for item in items
            if isinstance(item, dict)
        ]
        return _dedupe_sources(results)[:limit]

    def _serpapi(self, query: str, limit: int) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://serpapi.com/search.json"
        payload = self._get_json(endpoint, {"q": query, "api_key": self.api_key}, {})
        items = payload.get("organic_results") or [] if isinstance(payload, dict) else []
        results = [
            _normalize_search_result(
                {
                    "title": item.get("title"),
                    "href": item.get("link"),
                    "body": item.get("snippet"),
                },
                "serpapi",
            )
            for item in items
            if isinstance(item, dict)
        ]
        return _dedupe_sources(results)[:limit]

    def _generic_json(self, query: str, limit: int) -> list[dict[str, Any]]:
        payload = self._get_json(self.endpoint or "", {"q": query}, {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
        candidates = []
        if isinstance(payload, dict):
            candidates = payload.get("results") or payload.get("items") or []
        if not isinstance(candidates, list):
            return []
        return _dedupe_sources([_normalize_search_result(item, self.provider or "generic_json") for item in candidates])[:limit]

    def _get_json(self, endpoint: str, params: dict[str, str], headers: dict[str, str]) -> dict[str, Any]:
        if not endpoint:
            raise RuntimeError("LIVE_SEARCH_ENDPOINT is missing.")
        separator = "&" if "?" in endpoint else "?"
        url = f"{endpoint}{separator}{urlparse.urlencode(params)}"
        request = urlrequest.Request(url, headers={"User-Agent": "BuilderCore/phase4-live-search", **headers})
        try:
            with urlrequest.urlopen(request, timeout=8) as response:
                raw = response.read(1_000_000).decode("utf-8", errors="replace")
        except urlerror.URLError as error:
            raise RuntimeError(error) from error
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}


def get_search_status(query: str = "", limit: int = DEFAULT_RESULT_LIMIT) -> dict[str, Any]:
    connector = SearchConnector()
    if query.strip():
        return connector.search(query, limit=limit)
    return connector.status()


def _open_ddgs(ddgs_class: Any) -> Any:
    try:
        return ddgs_class(timeout=8)
    except TypeError:
        return ddgs_class()


def _normalize_search_result(item: Any, provider: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    title = _clean_text(item.get("title") or item.get("name") or "")
    url = _clean_text(item.get("href") or item.get("url") or item.get("link") or "")
    snippet = _clean_text(item.get("body") or item.get("snippet") or item.get("description") or item.get("summary") or "")
    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "summary": snippet,
        "source_domain": _source_domain(url),
        "provider": provider,
        "source_type": f"{provider}_web_result",
    }


def _dedupe_sources(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or "").strip()
        key = (url or title).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _bounded_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = DEFAULT_RESULT_LIMIT
    return max(1, min(value, MAX_RESULT_LIMIT))


def _source_domain(url: str) -> str:
    try:
        domain = urlparse.urlparse(url).netloc.lower()
    except Exception:
        return ""
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _clean_text(value: Any, max_length: int = 1000) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _safe_error(error: Exception) -> str:
    message = " ".join(str(error).split())
    if not message:
        message = type(error).__name__
    if len(message) > 240:
        message = message[:237].rstrip() + "..."
    return message
