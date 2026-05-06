from __future__ import annotations

import json
import os
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

LIVE_INTERNET_NOT_CONNECTED = "Live internet/search is not connected yet."
SEARCH_PROVIDER_FAILED = "Live internet/search provider is configured but could not be reached."
DISABLED_PROVIDERS = {"", "none", "off", "false", "disabled", "not_connected"}


class SearchConnector:
    def __init__(self) -> None:
        provider = os.getenv("LIVE_SEARCH_PROVIDER", "duckduckgo").strip().lower()
        self.provider = None if provider in DISABLED_PROVIDERS else provider
        self.api_key = os.getenv("LIVE_SEARCH_API_KEY", "").strip()
        self.endpoint = os.getenv("LIVE_SEARCH_ENDPOINT", "").strip() or None

    def status(self) -> dict[str, Any]:
        configured = self._is_configured()
        return {
            "connected": configured,
            "provider": self.provider if configured else None,
            "results": [],
            "message": "Live internet/search connector is configured." if configured else LIVE_INTERNET_NOT_CONNECTED,
            "endpoint_configured": bool(self.endpoint),
            "api_key_configured": bool(self.api_key),
            "supported_providers": ["duckduckgo", "brave", "bing", "serpapi", "generic_json"],
        }

    def search(self, query: str) -> dict[str, Any]:
        clean_query = query.strip()
        if not clean_query:
            status = self.status()
            status["query"] = clean_query
            status["results"] = []
            return status
        if not self._is_configured():
            return {
                "connected": False,
                "provider": None,
                "results": [],
                "message": LIVE_INTERNET_NOT_CONNECTED,
                "query": clean_query,
            }

        try:
            if self.provider in {"duckduckgo", "duckduckgo_instant_answer"}:
                results = self._duckduckgo(clean_query)
            elif self.provider == "brave":
                results = self._brave(clean_query)
            elif self.provider == "bing":
                results = self._bing(clean_query)
            elif self.provider == "serpapi":
                results = self._serpapi(clean_query)
            else:
                results = self._generic_json(clean_query)
        except Exception as error:
            return {
                "connected": False,
                "provider": self.provider,
                "results": [],
                "message": f"{SEARCH_PROVIDER_FAILED} {error}",
                "query": clean_query,
            }

        return {
            "connected": True,
            "provider": self.provider,
            "results": results,
            "message": "Live internet/search returned real provider results." if results else "Live internet/search is connected, but no sources were returned for this query.",
            "query": clean_query,
        }

    def _is_configured(self) -> bool:
        if self.provider in {"duckduckgo", "duckduckgo_instant_answer"}:
            return True
        if self.provider in {"brave", "bing", "serpapi"}:
            return bool(self.api_key)
        if self.provider == "generic_json":
            return bool(self.endpoint)
        return False

    def _duckduckgo(self, query: str) -> list[dict[str, Any]]:
        package_results = self._duckduckgo_package(query)
        if package_results:
            return package_results
        return self._duckduckgo_instant_answer(query)

    def _duckduckgo_package(self, query: str) -> list[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except Exception:
            return []

        with DDGS(timeout=8) as ddgs:
            raw_results = list(ddgs.text(query, max_results=8))
        results: list[dict[str, Any]] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            results.append(
                {
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("href") or item.get("url") or ""),
                    "summary": str(item.get("body") or item.get("summary") or item.get("snippet") or ""),
                    "source_type": "duckduckgo_web_result",
                    "provider": "duckduckgo",
                }
            )
        return _dedupe_sources(results)[:8]

    def _duckduckgo_instant_answer(self, query: str) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://api.duckduckgo.com/"
        payload = self._get_json(endpoint, {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}, {})
        results: list[dict[str, Any]] = []
        abstract_url = str(payload.get("AbstractURL") or "").strip()
        abstract_text = str(payload.get("AbstractText") or "").strip()
        heading = str(payload.get("Heading") or "DuckDuckGo result").strip()
        if abstract_url or abstract_text:
            results.append(
                {
                    "title": heading,
                    "url": abstract_url,
                    "summary": abstract_text,
                    "source_type": "duckduckgo_instant_answer",
                    "provider": "duckduckgo",
                }
            )
        for item in self._flatten_related(payload.get("RelatedTopics", []))[:5]:
            text = str(item.get("Text") or "").strip()
            first_url = str(item.get("FirstURL") or "").strip()
            if text or first_url:
                results.append(
                    {
                        "title": text[:120] or first_url,
                        "url": first_url,
                        "summary": text,
                        "source_type": "duckduckgo_related_topic",
                        "provider": "duckduckgo",
                    }
                )
        return _dedupe_sources(results)[:8]

    def _brave(self, query: str) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://api.search.brave.com/res/v1/web/search"
        payload = self._get_json(endpoint, {"q": query}, {"X-Subscription-Token": self.api_key, "Accept": "application/json"})
        items = ((payload.get("web") or {}).get("results") or []) if isinstance(payload, dict) else []
        return _dedupe_sources(
            [
                {
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("url") or ""),
                    "summary": str(item.get("description") or ""),
                    "source_type": "brave_web_result",
                    "provider": "brave",
                }
                for item in items
                if isinstance(item, dict)
            ]
        )[:8]

    def _bing(self, query: str) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://api.bing.microsoft.com/v7.0/search"
        payload = self._get_json(endpoint, {"q": query}, {"Ocp-Apim-Subscription-Key": self.api_key})
        items = ((payload.get("webPages") or {}).get("value") or []) if isinstance(payload, dict) else []
        return _dedupe_sources(
            [
                {
                    "title": str(item.get("name") or ""),
                    "url": str(item.get("url") or ""),
                    "summary": str(item.get("snippet") or ""),
                    "source_type": "bing_web_result",
                    "provider": "bing",
                }
                for item in items
                if isinstance(item, dict)
            ]
        )[:8]

    def _serpapi(self, query: str) -> list[dict[str, Any]]:
        endpoint = self.endpoint or "https://serpapi.com/search.json"
        payload = self._get_json(endpoint, {"q": query, "api_key": self.api_key}, {})
        items = payload.get("organic_results") or [] if isinstance(payload, dict) else []
        return _dedupe_sources(
            [
                {
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("link") or ""),
                    "summary": str(item.get("snippet") or ""),
                    "source_type": "serpapi_organic_result",
                    "provider": "serpapi",
                }
                for item in items
                if isinstance(item, dict)
            ]
        )[:8]

    def _generic_json(self, query: str) -> list[dict[str, Any]]:
        payload = self._get_json(self.endpoint or "", {"q": query}, {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
        candidates = []
        if isinstance(payload, dict):
            candidates = payload.get("results") or payload.get("items") or []
        if not isinstance(candidates, list):
            return []
        return _dedupe_sources(
            [
                {
                    "title": str(item.get("title") or item.get("name") or ""),
                    "url": str(item.get("url") or item.get("link") or ""),
                    "summary": str(item.get("summary") or item.get("snippet") or item.get("description") or ""),
                    "source_type": "generic_json_result",
                    "provider": self.provider,
                }
                for item in candidates
                if isinstance(item, dict)
            ]
        )[:8]

    def _get_json(self, endpoint: str, params: dict[str, str], headers: dict[str, str]) -> dict[str, Any]:
        if not endpoint:
            raise RuntimeError("LIVE_SEARCH_ENDPOINT is missing.")
        separator = "&" if "?" in endpoint else "?"
        url = f"{endpoint}{separator}{urlparse.urlencode(params)}"
        request = urlrequest.Request(url, headers={"User-Agent": "BuilderCore/phase3", **headers})
        try:
            with urlrequest.urlopen(request, timeout=8) as response:
                raw = response.read(1_000_000).decode("utf-8", errors="replace")
        except urlerror.URLError as error:
            raise RuntimeError(str(error)) from error
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}

    def _flatten_related(self, items: Any) -> list[dict[str, Any]]:
        flattened: list[dict[str, Any]] = []
        if not isinstance(items, list):
            return flattened
        for item in items:
            if not isinstance(item, dict):
                continue
            if "Topics" in item:
                flattened.extend(self._flatten_related(item.get("Topics")))
            else:
                flattened.append(item)
        return flattened


def get_search_status(query: str = "") -> dict[str, Any]:
    connector = SearchConnector()
    if query.strip():
        return connector.search(query)
    return connector.status()


def _dedupe_sources(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or "").strip()
        key = url or title
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output