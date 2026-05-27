"""Rank tracker - monitors keyword positions in search results."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from src.utils.http_client import HttpClient
from src.utils.config import settings
from src.utils.logger import logger
from .models import RankEntry, RankHistory, RankTrackingReport


class RankTracker:
    """Tracks keyword rankings in search engines."""

    DATA_FILE = "rank_history.json"

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else settings.data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self.data_dir / self.DATA_FILE
        self._history: Dict[str, List[Dict]] = self._load_history()

    async def check_keyword(
        self,
        keyword: str,
        domain: str,
        num_results: int = 100,
    ) -> RankEntry:
        """Check ranking position for a keyword."""
        entry = RankEntry(
            keyword=keyword,
            domain=domain,
            checked_at=datetime.now().isoformat(),
        )

        results = await self._search_google(keyword, num_results)

        for i, result in enumerate(results, 1):
            result_domain = urlparse(result.get("url", "")).netloc
            if domain in result_domain or result_domain in domain:
                entry.position = i
                entry.url = result.get("url", "")
                entry.title = result.get("title", "")
                entry.snippet = result.get("snippet", "")
                break

        # Save to history
        self._save_entry(keyword, domain, entry)

        return entry


    async def check_keywords(
        self,
        keywords: List[str],
        domain: str,
    ) -> RankTrackingReport:
        """Check rankings for multiple keywords."""
        report = RankTrackingReport(
            domain=domain,
            total_keywords=len(keywords),
            checked_at=datetime.now().isoformat(),
        )

        for keyword in keywords:
            entry = await self.check_keyword(keyword, domain)
            history = self.get_history(keyword, domain)
            report.histories.append(history)

            if entry.position:
                if entry.position <= 3:
                    report.keywords_in_top_3 += 1
                if entry.position <= 10:
                    report.keywords_in_top_10 += 1
                if entry.position <= 100:
                    report.keywords_in_top_100 += 1
            else:
                report.keywords_not_ranking += 1

            if history.trend == "up":
                report.improved += 1
            elif history.trend == "down":
                report.declined += 1
            else:
                report.unchanged += 1

            # Small delay between searches to avoid rate limiting
            await asyncio.sleep(2)

        positions = [
            h.current_position for h in report.histories
            if h.current_position is not None
        ]
        report.avg_position = round(sum(positions) / len(positions), 1) if positions else None

        return report

    def get_history(self, keyword: str, domain: str) -> RankHistory:
        """Get ranking history for a keyword-domain pair."""
        key = f"{keyword}::{domain}"
        history = RankHistory(keyword=keyword, domain=domain)

        entries_data = self._history.get(key, [])
        for data in entries_data:
            entry = RankEntry(**data)
            history.entries.append(entry)

        history.calculate_stats()
        return history

    def get_all_tracked(self, domain: str) -> List[RankHistory]:
        """Get all tracked keywords for a domain."""
        histories = []
        for key, entries_data in self._history.items():
            keyword, entry_domain = key.split("::", 1)
            if domain in entry_domain:
                history = self.get_history(keyword, entry_domain)
                histories.append(history)
        return histories

    async def _search_google(self, keyword: str, num_results: int = 100) -> List[Dict]:
        """Search Google using Custom Search API or scraping fallback."""
        if settings.google_api_key and settings.google_cse_id:
            return await self._search_google_api(keyword, num_results)
        return await self._search_google_scrape(keyword, num_results)

    async def _search_google_api(self, keyword: str, num_results: int) -> List[Dict]:
        """Search using Google Custom Search JSON API."""
        results = []
        async with HttpClient() as client:
            pages = min(num_results // 10, 10)
            for page in range(pages):
                params = {
                    "key": settings.google_api_key,
                    "cx": settings.google_cse_id,
                    "q": keyword,
                    "start": page * 10 + 1,
                    "num": 10,
                }
                try:
                    response = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params=params,
                    )
                    data = response.json()
                    for item in data.get("items", []):
                        results.append({
                            "url": item.get("link", ""),
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                        })
                except Exception as e:
                    logger.error(f"Google API search error: {e}")
                    break
                await asyncio.sleep(0.5)

        return results


    async def _search_google_scrape(self, keyword: str, num_results: int) -> List[Dict]:
        """Fallback: scrape Google search results (use responsibly)."""
        results = []
        from src.utils.html_parser import HtmlParser

        async with HttpClient(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }) as client:
            params = {"q": keyword, "num": min(num_results, 100)}
            try:
                response = await client.get("https://www.google.com/search", params=params)
                soup = HtmlParser(response.text, "https://www.google.com").soup

                for div in soup.select("div.g"):
                    link = div.find("a", href=True)
                    title_elem = div.find("h3")
                    snippet_elem = div.find("div", class_="VwiC3b")

                    if link and title_elem:
                        href = link["href"]
                        if href.startswith("http"):
                            results.append({
                                "url": href,
                                "title": title_elem.get_text(strip=True),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                            })
            except Exception as e:
                logger.error(f"Google scrape error: {e}")

        return results

    def _save_entry(self, keyword: str, domain: str, entry: RankEntry):
        """Save rank entry to history."""
        key = f"{keyword}::{domain}"
        if key not in self._history:
            self._history[key] = []

        self._history[key].append(entry.to_dict())

        # Keep only last 90 days of data
        if len(self._history[key]) > 90:
            self._history[key] = self._history[key][-90:]

        self._persist_history()

    def _load_history(self) -> Dict[str, List[Dict]]:
        """Load history from JSON file."""
        if self._history_file.exists():
            try:
                with open(self._history_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Could not load rank history, starting fresh")
        return {}

    def _persist_history(self):
        """Save history to JSON file."""
        try:
            with open(self._history_file, "w") as f:
                json.dump(self._history, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Failed to save rank history: {e}")

    def clear_history(self, keyword: Optional[str] = None, domain: Optional[str] = None):
        """Clear rank history (all or specific keyword/domain)."""
        if keyword and domain:
            key = f"{keyword}::{domain}"
            self._history.pop(key, None)
        elif domain:
            keys_to_remove = [k for k in self._history if domain in k]
            for k in keys_to_remove:
                del self._history[k]
        else:
            self._history = {}
        self._persist_history()
