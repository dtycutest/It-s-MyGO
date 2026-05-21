from __future__ import annotations

import random


class RandomUserAgentMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist("USER_AGENT_POOL"))

    def __init__(self, user_agents: list[str]):
        self.user_agents = user_agents

    def process_request(self, request):
        if self.user_agents:
            request.headers.setdefault("User-Agent", random.choice(self.user_agents))
        return None
