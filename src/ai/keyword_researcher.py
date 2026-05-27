"""Keyword Research Module - AI-powered keyword analysis and suggestions."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.logger import logger
from .providers import get_provider


KEYWORD_RESEARCH_SYSTEM = """You are an expert SEO keyword researcher.
Your job is to analyze keywords, find related terms, assess competition, and provide actionable keyword strategies.
Always return structured JSON when asked. Be data-driven and specific."""

KEYWORD_ANALYSIS_PROMPT = """Perform comprehensive keyword research for:

**Primary Keyword:** {keyword}
**Industry/Niche:** {niche}
**Target Market:** {market}
**Language:** {language}

Provide a JSON response with this structure:
{{
    "primary_keyword": "{keyword}",
    "search_intent": "<informational/transactional/navigational/commercial>",
    "estimated_difficulty": <1-100>,
    "estimated_monthly_volume": "<range like 1000-5000>",
    "competition_level": "<low/medium/high>",
    "cpc_estimate": "<$X.XX>",
    "related_keywords": [
        {{"keyword": "<term>", "volume_estimate": "<range>", "difficulty": <1-100>, "intent": "<type>"}}
    ],
    "long_tail_keywords": [
        {{"keyword": "<long tail phrase>", "volume_estimate": "<range>", "difficulty": <1-100>, "intent": "<type>"}}
    ],
    "question_keywords": [
        "<question people ask about this topic>"
    ],
    "lsi_keywords": ["<semantically related terms>"],
    "trending_subtopics": ["<current trending angles>"],
    "content_gaps": ["<topics competitors miss>"],
    "recommended_strategy": {{
        "primary_target": "<main keyword to target>",
        "supporting_keywords": ["<2-3 secondary targets>"],
        "content_type_recommendation": "<article/guide/listicle/comparison/review>",
        "estimated_word_count": <int>,
        "title_suggestions": ["<3-5 title ideas incorporating keyword>"]
    }}
}}

Generate 15-20 related keywords and 10-15 long-tail keywords."""

SERP_ANALYSIS_PROMPT = """Analyze the search engine results page (SERP) landscape for:

**Keyword:** {keyword}
**Market:** {market}

Based on your knowledge of typical SERP features for this type of query, provide:
{{
    "keyword": "{keyword}",
    "serp_features": {{
        "has_featured_snippet": <bool>,
        "has_people_also_ask": <bool>,
        "has_local_pack": <bool>,
        "has_knowledge_panel": <bool>,
        "has_video_results": <bool>,
        "has_image_pack": <bool>,
        "has_shopping_results": <bool>,
        "has_news_results": <bool>
    }},
    "top_ranking_content_analysis": [
        {{
            "position": <1-10>,
            "content_type": "<article/product/video/wiki/etc>",
            "estimated_word_count": <int>,
            "has_structured_data": <bool>,
            "domain_authority_level": "<high/medium/low>",
            "content_freshness": "<recent/moderate/old>",
            "key_topics_covered": ["<main topics>"]
        }}
    ],
    "ranking_factors_for_keyword": [
        "<specific factor important for this keyword>"
    ],
    "opportunity_score": <0-100>,
    "recommended_approach": "<strategy to rank for this keyword>",
    "estimated_time_to_rank": "<timeframe estimate>"
}}"""

KEYWORD_CLUSTERING_PROMPT = """Organize these keywords into topic clusters for content planning:

**Keywords:** {keywords}
**Niche:** {niche}

Group them into clusters and provide:
{{
    "clusters": [
        {{
            "cluster_name": "<descriptive name>",
            "pillar_keyword": "<main keyword for this cluster>",
            "supporting_keywords": ["<related keywords>"],
            "content_type": "<recommended content format>",
            "priority": "<high/medium/low>",
            "estimated_total_volume": "<range>",
            "suggested_url_slug": "<url-friendly-slug>"
        }}
    ],
    "content_calendar": [
        {{
            "week": <1-12>,
            "cluster": "<cluster name>",
            "keyword_focus": "<primary keyword>",
            "content_type": "<format>",
            "title_suggestion": "<working title>"
        }}
    ],
    "internal_linking_map": [
        {{
            "from_cluster": "<source>",
            "to_cluster": "<target>",
            "relationship": "<how they connect>"
        }}
    ]
}}"""


@dataclass
class KeywordData:
    keyword: str
    volume_estimate: str = ""
    difficulty: int = 0
    intent: str = ""
    cpc_estimate: str = ""


@dataclass
class KeywordResearchResult:
    """Result of keyword research."""
    primary_keyword: str = ""
    search_intent: str = ""
    estimated_difficulty: int = 0
    estimated_monthly_volume: str = ""
    competition_level: str = ""
    cpc_estimate: str = ""
    related_keywords: List[Dict[str, Any]] = field(default_factory=list)
    long_tail_keywords: List[Dict[str, Any]] = field(default_factory=list)
    question_keywords: List[str] = field(default_factory=list)
    lsi_keywords: List[str] = field(default_factory=list)
    trending_subtopics: List[str] = field(default_factory=list)
    content_gaps: List[str] = field(default_factory=list)
    recommended_strategy: Dict[str, Any] = field(default_factory=dict)
    serp_analysis: Dict[str, Any] = field(default_factory=dict)
    keyword_clusters: List[Dict[str, Any]] = field(default_factory=list)
    model_used: str = ""
    provider_used: str = ""
    generation_time_sec: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_keyword": self.primary_keyword,
            "search_intent": self.search_intent,
            "estimated_difficulty": self.estimated_difficulty,
            "estimated_monthly_volume": self.estimated_monthly_volume,
            "competition_level": self.competition_level,
            "cpc_estimate": self.cpc_estimate,
            "related_keywords": self.related_keywords,
            "long_tail_keywords": self.long_tail_keywords,
            "question_keywords": self.question_keywords,
            "lsi_keywords": self.lsi_keywords,
            "trending_subtopics": self.trending_subtopics,
            "content_gaps": self.content_gaps,
            "recommended_strategy": self.recommended_strategy,
            "serp_analysis": self.serp_analysis,
            "keyword_clusters": self.keyword_clusters,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "generation_time_sec": self.generation_time_sec,
            "success": self.success,
            "error": self.error,
        }


class KeywordResearcher:
    """AI-powered keyword research and analysis."""

    def __init__(self, provider: str = "openai", model_id: str = "gpt-4o-mini"):
        self.provider_name = provider
        self.model_id = model_id

    async def research(
        self,
        keyword: str,
        niche: str = "general",
        market: str = "global",
        language: str = "en",
    ) -> KeywordResearchResult:
        """Perform comprehensive keyword research."""
        import time
        start = time.time()

        result = KeywordResearchResult(
            primary_keyword=keyword,
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = KEYWORD_ANALYSIS_PROMPT.format(
                keyword=keyword,
                niche=niche,
                market=market,
                language=language,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=KEYWORD_RESEARCH_SYSTEM,
                max_tokens=4096,
                temperature=0.4,
            )

            data = self._parse_json(response)
            if data:
                result.search_intent = data.get("search_intent", "")
                result.estimated_difficulty = data.get("estimated_difficulty", 0)
                result.estimated_monthly_volume = data.get("estimated_monthly_volume", "")
                result.competition_level = data.get("competition_level", "")
                result.cpc_estimate = data.get("cpc_estimate", "")
                result.related_keywords = data.get("related_keywords", [])
                result.long_tail_keywords = data.get("long_tail_keywords", [])
                result.question_keywords = data.get("question_keywords", [])
                result.lsi_keywords = data.get("lsi_keywords", [])
                result.trending_subtopics = data.get("trending_subtopics", [])
                result.content_gaps = data.get("content_gaps", [])
                result.recommended_strategy = data.get("recommended_strategy", {})
                result.success = True
            else:
                result.error = "Could not parse keyword research response"

        except Exception as e:
            result.error = str(e)
            logger.error(f"Keyword research failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def analyze_serp(
        self,
        keyword: str,
        market: str = "global",
    ) -> KeywordResearchResult:
        """Analyze SERP landscape for a keyword."""
        import time
        start = time.time()

        result = KeywordResearchResult(
            primary_keyword=keyword,
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = SERP_ANALYSIS_PROMPT.format(keyword=keyword, market=market)

            response = await provider.generate(
                prompt=prompt,
                system_prompt=KEYWORD_RESEARCH_SYSTEM,
                max_tokens=4096,
                temperature=0.3,
            )

            data = self._parse_json(response)
            if data:
                result.serp_analysis = data
                result.success = True
            else:
                result.error = "Could not parse SERP analysis"

        except Exception as e:
            result.error = str(e)
            logger.error(f"SERP analysis failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def cluster_keywords(
        self,
        keywords: List[str],
        niche: str = "general",
    ) -> KeywordResearchResult:
        """Group keywords into topic clusters for content planning."""
        import time
        start = time.time()

        result = KeywordResearchResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            keywords_str = "\n".join(f"- {kw}" for kw in keywords[:50])
            prompt = KEYWORD_CLUSTERING_PROMPT.format(
                keywords=keywords_str,
                niche=niche,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=KEYWORD_RESEARCH_SYSTEM,
                max_tokens=4096,
                temperature=0.4,
            )

            data = self._parse_json(response)
            if data:
                result.keyword_clusters = data.get("clusters", [])
                result.recommended_strategy = {
                    "content_calendar": data.get("content_calendar", []),
                    "internal_linking_map": data.get("internal_linking_map", []),
                }
                result.success = True
            else:
                result.error = "Could not parse clustering response"

        except Exception as e:
            result.error = str(e)
            logger.error(f"Keyword clustering failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response."""
        import json

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            try:
                return json.loads(response[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(response[start_idx:end_idx])
            except json.JSONDecodeError:
                pass

        return None
