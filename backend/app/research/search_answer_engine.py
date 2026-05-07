from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any

from app.connectors.page_fetcher import fetch_allowed_page
from app.connectors.search_connector import DUCKDUCKGO_UNAVAILABLE, SearchConnector
from app.memory.memory_store import save_safe_memory

MAX_SOURCES = 5
MAX_PAGES_TO_OPEN = 3
PRIMARY_SOURCE_DOMAINS = {
    "canada.ca",
    "pm.gc.ca",
    "parl.ca",
    "ourcommons.ca",
    "gg.ca",
    "elections.ca",
    "pmindia.gov.in",
    "india.gov.in",
    "pib.gov.in",
    "parliamentofindia.nic.in",
}
OFFICIAL_SOURCE_DOMAINS = {
    "fastapi.tiangolo.com",
    "docs.python.org",
    "cloud.google.com",
    "developers.google.com",
    "github.com",
    "openai.com",
}
REPUTABLE_NEWS_DOMAINS = {
    "cbc.ca",
    "ctvnews.ca",
    "globalnews.ca",
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "thecanadianpressnews.ca",
}
ACADEMIC_SOURCE_DOMAINS = {"edu", "ac.uk", "arxiv.org", "nih.gov", "ncbi.nlm.nih.gov"}
WIKIPEDIA_DOMAINS = {"wikipedia.org", "en.wikipedia.org"}
LOW_PRIORITY_DOMAINS = {"blogspot.com", "medium.com", "substack.com"}


def build_search_answer(query: str, *, save_memory: bool = True) -> dict[str, Any]:
    clean_query = " ".join((query or "").split())
    connector_result = SearchConnector().search(clean_query, limit=MAX_SOURCES)
    warnings: list[str] = []

    if not connector_result.get("connected"):
        message = str(connector_result.get("message") or DUCKDUCKGO_UNAVAILABLE)
        warnings.append(message)
        return {
            "query": clean_query,
            "search_connected": False,
            "live_search_connected": False,
            "sources": [],
            "facts": [],
            "claims": [],
            "unknowns": [
                {
                    "text": "No live DuckDuckGo results were available for this query.",
                    "reason": message,
                }
            ],
            "answer": DUCKDUCKGO_UNAVAILABLE,
            "summary": DUCKDUCKGO_UNAVAILABLE,
            "confidence": "low",
            "missing_data": ["Live DuckDuckGo search results", "Verified sources"],
            "warnings": list(dict.fromkeys(warnings)),
            "memory_saved": False,
            "recommended_next_step": "Try again later or verify the question with trusted sources outside Builder Core.",
        }

    raw_sources = list(connector_result.get("results") or [])
    sources = _rank_sources([_source_record(source) for source in raw_sources if isinstance(source, dict)])[:MAX_SOURCES]
    page_results = _open_allowed_pages(sources)
    warnings.extend(page_results["warnings"])

    for source in sources:
        opened = page_results["by_url"].get(source["url"])
        if opened:
            source["opened"] = bool(opened.get("opened"))
            source["page_excerpt"] = _truncate(_clean_evidence_text(str(opened.get("text") or "")), 500)
            page_title = str(opened.get("title") or "").strip()
            if page_title and not source["title"]:
                source["title"] = page_title
        else:
            source["opened"] = False
            source["page_excerpt"] = ""

    facts = _build_facts(sources)
    claims = _build_claims(sources)
    unknowns = _build_unknowns(sources)
    missing_data = _build_missing_data(sources)
    answer = _build_answer(clean_query, sources)
    confidence = _confidence(sources)
    memory_saved = False

    if save_memory and sources:
        memory_result = save_safe_memory(
            {
                "memory_type": "search_answer",
                "topic": clean_query,
                "summary": answer,
                "sources": sources,
                "confidence": confidence,
                "verify_before_use": True,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        memory_saved = bool(memory_result.get("saved"))
        warnings.extend(str(item) for item in memory_result.get("warnings", []) if item)

    return {
        "query": clean_query,
        "search_connected": True,
        "live_search_connected": True,
        "sources": sources,
        "facts": facts,
        "claims": claims,
        "unknowns": unknowns,
        "answer": answer,
        "summary": answer,
        "confidence": confidence,
        "missing_data": missing_data,
        "warnings": list(dict.fromkeys(warnings)),
        "memory_saved": memory_saved,
        "recommended_next_step": "Review the listed sources and verify important decisions against primary sources.",
    }


def _open_allowed_pages(sources: list[dict[str, Any]]) -> dict[str, Any]:
    by_url: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for source in sources[:MAX_PAGES_TO_OPEN]:
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        opened = fetch_allowed_page(url)
        by_url[url] = opened
        warning = str(opened.get("warning") or "").strip()
        if warning:
            warnings.append(warning)
    return {"by_url": by_url, "warnings": list(dict.fromkeys(warnings))}


def _source_record(source: dict[str, Any]) -> dict[str, Any]:
    snippet = _truncate(_clean_evidence_text(str(source.get("snippet") or source.get("summary") or "")), 1000)
    return {
        "title": _truncate(str(source.get("title") or ""), 240),
        "url": str(source.get("url") or "").strip(),
        "snippet": snippet,
        "summary": snippet,
        "source_domain": str(source.get("source_domain") or "").strip(),
        "provider": str(source.get("provider") or "duckduckgo"),
        "source_type": str(source.get("source_type") or "duckduckgo_web_result"),
        "citation_candidate": bool(source.get("url") and (source.get("title") or snippet)),
    }


def _rank_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for index, source in enumerate(sources):
        ranked.append((_source_priority(str(source.get("source_domain") or "")), index, source))
    return [source for _, _, source in sorted(ranked, key=lambda item: (item[0], item[1]))]


def _source_priority(domain: str) -> int:
    clean_domain = domain.lower().removeprefix("www.")
    if _domain_matches(clean_domain, PRIMARY_SOURCE_DOMAINS):
        return 0
    if _domain_matches(clean_domain, OFFICIAL_SOURCE_DOMAINS) or clean_domain.endswith(".gov") or clean_domain.endswith(".gc.ca"):
        return 1
    if _domain_matches(clean_domain, REPUTABLE_NEWS_DOMAINS):
        return 2
    if _domain_matches(clean_domain, ACADEMIC_SOURCE_DOMAINS) or clean_domain.endswith(".edu"):
        return 3
    if _domain_matches(clean_domain, WIKIPEDIA_DOMAINS):
        return 5
    if _domain_matches(clean_domain, LOW_PRIORITY_DOMAINS) or "blog" in clean_domain:
        return 6
    return 4


def _domain_matches(domain: str, candidates: set[str]) -> bool:
    return any(domain == candidate or domain.endswith(f".{candidate}") for candidate in candidates)


def _build_facts(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for source in sources:
        title = source.get("title")
        domain = source.get("source_domain") or "unknown source"
        if title:
            facts.append(
                {
                    "text": f"DuckDuckGo returned a source from {domain} titled: {title}",
                    "source_url": source.get("url"),
                    "confidence": "high",
                    "type": "source_metadata",
                }
            )
    return facts


def _build_claims(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for source in sources:
        evidence = _clean_evidence_text(str(source.get("page_excerpt") or source.get("snippet") or "").strip())
        if not evidence:
            continue
        claims.append(
            {
                "text": _truncate(evidence, 500),
                "classification": "reported_claim",
                "confidence": "medium" if source.get("opened") else "low",
                "source_url": source.get("url"),
                "reason": "This comes from source text or DuckDuckGo result snippets and still needs human verification before critical use.",
            }
        )
    return claims


def _build_unknowns(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unknowns: list[dict[str, Any]] = [
        {
            "text": "Builder Core has not independently verified these sources beyond collecting search results and allowed page excerpts.",
            "reason": "Independent corroboration is outside the current deterministic answer engine.",
        }
    ]
    unopened = [source for source in sources[:MAX_PAGES_TO_OPEN] if not source.get("opened")]
    if unopened:
        unknowns.append(
            {
                "text": "Some source pages could not be opened by the safe page reader.",
                "reason": "The answer may rely on DuckDuckGo snippets and source metadata for those sources.",
            }
        )
    return unknowns


def _build_missing_data(sources: list[dict[str, Any]]) -> list[str]:
    missing = ["Independent corroboration"]
    if not any(source.get("opened") for source in sources):
        missing.append("Full source page text")
    if not sources:
        missing.extend(["Live DuckDuckGo search results", "Verified sources"])
    return list(dict.fromkeys(missing))


def _build_answer(query: str, sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "DuckDuckGo search returned no usable sources for this query. Builder Core did not invent an answer."

    direct_answer = _direct_answer(query, sources)
    if direct_answer:
        return direct_answer

    evidence_lines = []
    for index, source in enumerate(sources[:3], start=1):
        title = str(source.get("title") or "Untitled source").strip()
        domain = str(source.get("source_domain") or "unknown source").strip()
        evidence = _clean_evidence_text(str(source.get("page_excerpt") or source.get("snippet") or "").strip())
        if evidence:
            evidence_lines.append(f"{index}. {title} ({domain}): {_truncate(evidence, 420)}")
        else:
            evidence_lines.append(f"{index}. {title} ({domain})")

    return f"The strongest supported answer is: {' '.join(evidence_lines)}"


def _direct_answer(query: str, sources: list[dict[str, Any]]) -> str:
    normalized_query = query.lower()
    if "prime minister" in normalized_query and "india" in normalized_query:
        prime_minister = _find_office_holder(sources, "Prime Minister", "India")
        if prime_minister:
            return f"The current Prime Minister of India is {prime_minister}. Sources checked: {_source_domains_label(sources)}."

    if ("current government" in normalized_query or "government of canada" in normalized_query or "prime minister of canada" in normalized_query) and "canada" in normalized_query:
        prime_minister = _find_prime_minister(sources)
        party = _find_party(sources)
        if prime_minister and party:
            return f"The current federal government of Canada is led by Prime Minister {prime_minister} and the {party}. Sources checked: {_source_domains_label(sources)}."
        if prime_minister:
            return f"The current federal government of Canada is led by Prime Minister {prime_minister}. Sources checked: {_source_domains_label(sources)}."

    first_claim = _best_evidence_sentence(sources)
    if first_claim:
        return first_claim
    return ""


def _find_prime_minister(sources: list[dict[str, Any]]) -> str:
    for text in _evidence_texts(sources):
        patterns = (
            "Prime Minister ",
            "prime minister ",
            "The Right Honourable ",
        )
        for pattern in patterns:
            position = text.find(pattern)
            if position < 0:
                continue
            candidate = text[position + len(pattern) : position + len(pattern) + 80]
            name = _clean_name(candidate)
            if name:
                return name
    return ""


def _find_office_holder(sources: list[dict[str, Any]], office: str, country: str) -> str:
    office_pattern = re.escape(office)
    country_pattern = re.escape(country)
    patterns = (
        rf"{office_pattern}\s+(?:Shri\s+|Sri\s+|Mr\.?\s+|Ms\.?\s+|The Right Honourable\s+)?([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){{0,3}})",
        rf"([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){{1,3}})\s+(?:is|serves as|has been)\s+(?:the\s+)?(?:current\s+)?{office_pattern}(?:\s+of\s+{country_pattern})?",
    )
    for text in _evidence_texts(sources):
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            name = _clean_name(match.group(1))
            if name and name.lower() not in {"india", "canada", "official website"}:
                return name
    return ""


def _find_party(sources: list[dict[str, Any]]) -> str:
    for text in _evidence_texts(sources):
        lowered = text.lower()
        if "liberal party" in lowered or "liberal government" in lowered:
            return "Liberal Party"
        if "conservative party" in lowered or "conservative government" in lowered:
            return "Conservative Party"
        if "new democratic party" in lowered or "ndp" in lowered:
            return "New Democratic Party"
    return ""


def _clean_name(text: str) -> str:
    words = []
    for token in text.replace(",", " ").replace(".", " ").split():
        clean = "".join(ch for ch in token if ch.isalpha() or ch in {"-", "'"})
        if not clean:
            break
        if clean.lower() in {"of", "and", "the", "canada", "minister", "prime"}:
            break
        if not clean[0].isupper():
            break
        words.append(clean)
        if len(words) >= 3:
            break
    return " ".join(words[:3]).strip()


def _best_evidence_sentence(sources: list[dict[str, Any]]) -> str:
    for text in _evidence_texts(sources):
        for sentence in text.split(". "):
            clean = _truncate(sentence.strip(" ."), 420)
            if len(clean) > 40:
                return f"{clean}."
    return ""


def _evidence_texts(sources: list[dict[str, Any]]) -> list[str]:
    texts = []
    for source in sources:
        text = _clean_evidence_text(str(source.get("page_excerpt") or source.get("snippet") or ""))
        if text:
            texts.append(text)
    return texts


def _confidence(sources: list[dict[str, Any]]) -> str:
    opened_count = len([source for source in sources if source.get("opened")])
    strong_sources = [
        source
        for source in sources
        if _source_priority(str(source.get("source_domain") or "")) <= 2
    ]
    if opened_count >= 2 and len(strong_sources) >= 2:
        return "high"
    if strong_sources or sources:
        return "medium"
    return "low"


def _source_domains_label(sources: list[dict[str, Any]]) -> str:
    domains: list[str] = []
    for source in sources[:3]:
        domain = str(source.get("source_domain") or "").strip()
        if domain and domain not in domains:
            domains.append(domain)
    return ", ".join(domains) if domains else "DuckDuckGo result metadata"


def _truncate(text: str, max_chars: int) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def _clean_evidence_text(text: str) -> str:
    clean = " ".join((text or "").split())
    boilerplate = (
        "Jump to content",
        "Main menu",
        "Donate",
        "Create account",
        "Log in",
        "Contents",
        "Navigation",
        "Appearance",
        "Personal tools",
        "Edit",
        "sidebar",
        "search search",
        "move to sidebar",
    )
    for phrase in boilerplate:
        clean = clean.replace(phrase, " ")
    return " ".join(clean.split())
