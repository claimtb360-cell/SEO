"""Data models for rank tracking."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class RankEntry:
    """A single rank check result."""
    keyword: str
    domain: str
    position: Optional[int] = None
    url: str = ""
    title: str = ""
    snippet: str = ""
    checked_at: str = ""
    search_engine: str = "google"
    location: str = "us"
    is_featured_snippet: bool = False
    is_local_pack: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "domain": self.domain,
            "position": self.position,
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "checked_at": self.checked_at,
            "search_engine": self.search_engine,
            "location": self.location,
            "is_featured_snippet": self.is_featured_snippet,
            "is_local_pack": self.is_local_pack,
        }


@dataclass
class RankHistory:
    """Historical ranking data for a keyword."""
    keyword: str
    domain: str
    entries: List[RankEntry] = field(default_factory=list)
    current_position: Optional[int] = None
    best_position: Optional[int] = None
    worst_position: Optional[int] = None
    avg_position: Optional[float] = None
    position_change: int = 0
    trend: str = "stable"  # "up", "down", "stable", "new"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "domain": self.domain,
            "current_position": self.current_position,
            "best_position": self.best_position,
            "worst_position": self.worst_position,
            "avg_position": self.avg_position,
            "position_change": self.position_change,
            "trend": self.trend,
            "history": [e.to_dict() for e in self.entries],
        }

    def calculate_stats(self):
        """Calculate statistics from history entries."""
        positions = [e.position for e in self.entries if e.position is not None]
        if not positions:
            return

        self.current_position = positions[-1]
        self.best_position = min(positions)
        self.worst_position = max(positions)
        self.avg_position = round(sum(positions) / len(positions), 1)

        if len(positions) >= 2:
            self.position_change = positions[-2] - positions[-1]
            if self.position_change > 0:
                self.trend = "up"
            elif self.position_change < 0:
                self.trend = "down"
            else:
                self.trend = "stable"
        elif len(positions) == 1:
            self.trend = "new"


@dataclass
class RankTrackingReport:
    """Summary report for all tracked keywords."""
    domain: str
    total_keywords: int = 0
    keywords_in_top_3: int = 0
    keywords_in_top_10: int = 0
    keywords_in_top_100: int = 0
    keywords_not_ranking: int = 0
    avg_position: Optional[float] = None
    improved: int = 0
    declined: int = 0
    unchanged: int = 0
    histories: List[RankHistory] = field(default_factory=list)
    checked_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "total_keywords": self.total_keywords,
            "keywords_in_top_3": self.keywords_in_top_3,
            "keywords_in_top_10": self.keywords_in_top_10,
            "keywords_in_top_100": self.keywords_in_top_100,
            "keywords_not_ranking": self.keywords_not_ranking,
            "avg_position": self.avg_position,
            "improved": self.improved,
            "declined": self.declined,
            "unchanged": self.unchanged,
            "checked_at": self.checked_at,
            "keywords": [h.to_dict() for h in self.histories],
        }
