"""Redirect checker - detects redirect chains and loops."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any

import httpx

from src.utils.config import settings


@dataclass
class RedirectHop:
    url: str
    status_code: int
    location: str = ""


@dataclass
class RedirectChain:
    original_url: str
    hops: List[RedirectHop] = field(default_factory=list)
    final_url: str = ""
    chain_length: int = 0
    is_loop: bool = False
    has_issue: bool = False
    issue: str = ""


@dataclass
class RedirectCheckResult:
    urls_checked: int = 0
    chains: List[RedirectChain] = field(default_factory=list)
    total_redirects: int = 0
    long_chains: int = 0
    loops_detected: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "urls_checked": self.urls_checked,
            "total_redirects": self.total_redirects,
            "long_chains": self.long_chains,
            "loops_detected": self.loops_detected,
            "chains": [
                {
                    "original_url": c.original_url,
                    "final_url": c.final_url,
                    "chain_length": c.chain_length,
                    "is_loop": c.is_loop,
                    "has_issue": c.has_issue,
                    "issue": c.issue,
                    "hops": [{"url": h.url, "status_code": h.status_code, "location": h.location} for h in c.hops],
                }
                for c in self.chains
            ],
        }


class RedirectChecker:
    """Checks URLs for redirect chains and loops."""

    MAX_REDIRECTS = 10

    async def check_url(self, url: str) -> RedirectChain:
        """Check a single URL for redirect chain."""
        chain = RedirectChain(original_url=url)
        visited = set()
        current_url = url

        async with httpx.AsyncClient(
            timeout=settings.request_timeout,
            follow_redirects=False,
        ) as client:
            for _ in range(self.MAX_REDIRECTS):
                if current_url in visited:
                    chain.is_loop = True
                    chain.has_issue = True
                    chain.issue = "Redirect loop detected"
                    break

                visited.add(current_url)

                try:
                    response = await client.head(current_url)
                except Exception as e:
                    chain.has_issue = True
                    chain.issue = f"Error: {e}"
                    break

                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location", "")
                    chain.hops.append(RedirectHop(
                        url=current_url,
                        status_code=response.status_code,
                        location=location,
                    ))
                    current_url = location
                else:
                    chain.final_url = current_url
                    break

        chain.chain_length = len(chain.hops)
        if chain.chain_length > 2:
            chain.has_issue = True
            chain.issue = f"Long redirect chain ({chain.chain_length} hops)"

        return chain

    async def check_urls(self, urls: List[str]) -> RedirectCheckResult:
        """Check multiple URLs for redirects."""
        result = RedirectCheckResult()
        result.urls_checked = len(urls)

        tasks = [self.check_url(url) for url in urls]
        chains = await asyncio.gather(*tasks)

        for chain in chains:
            if chain.chain_length > 0:
                result.chains.append(chain)
                result.total_redirects += 1
                if chain.chain_length > 2:
                    result.long_chains += 1
                if chain.is_loop:
                    result.loops_detected += 1

        return result
