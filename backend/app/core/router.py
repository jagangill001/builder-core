from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BeeRoute:
    intent: str
    bees: tuple[str, ...]


class IntentRouter:
    def __init__(self) -> None:
        self._routes: dict[str, tuple[str, ...]] = {
            "chat": ("scout_bee", "planner_bee", "tester_bee", "reporter_bee", "memory_bee"),
            "inspect": ("scout_bee", "planner_bee", "tester_bee", "reporter_bee", "memory_bee"),
            "run": ("scout_bee", "planner_bee", "tester_bee", "reporter_bee", "memory_bee"),
            "build": ("scout_bee", "planner_bee", "coder_bee", "tester_bee", "reporter_bee", "memory_bee"),
            "modify": ("scout_bee", "planner_bee", "coder_bee", "tester_bee", "reporter_bee", "memory_bee"),
        }

    def route(self, intent: str) -> BeeRoute:
        normalized_intent = intent if intent in self._routes else "chat"
        return BeeRoute(intent=normalized_intent, bees=self._routes[normalized_intent])

    def supported_intents(self) -> list[str]:
        return sorted(self._routes)
