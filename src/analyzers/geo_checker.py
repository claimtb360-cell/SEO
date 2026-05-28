"""GEO (Generative Engine Optimization) - checks if content is optimized for AI engines."""

import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup


class GEOSignalResult:
    """Result for a single GEO signal."""

    def __init__(self, name: str, score: float, details: str,
                 recommendations: List[str], engine_relevance: List[str]):
        self.name = name
        self.score = score  # 0-100
        self.details = details
        self.recommendations = recommendations
        self.engine_relevance = engine_relevance  # Which AI engines benefit

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "details": self.details,
            "recommendations": self.recommendations,
            "engine_relevance": self.engine_relevance,
        }



class GEOCheckResult:
    """Complete GEO check result."""

    def __init__(self, url: str, signals: List[GEOSignalResult]):
        self.url = url
        self.signals = signals
        self.overall_score = round(
            sum(s.score for s in signals) / max(len(signals), 1), 1
        )
        self.engine_scores = self._calculate_engine_scores()

    def _calculate_engine_scores(self) -> Dict[str, float]:
        engines = ["ChatGPT", "Gemini", "Perplexity", "Copilot"]
        scores = {}
        for engine in engines:
            relevant = [s for s in self.signals if engine in s.engine_relevance]
            if relevant:
                scores[engine] = round(sum(s.score for s in relevant) / len(relevant), 1)
            else:
                scores[engine] = 0.0
        return scores

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "overall_score": self.overall_score,
            "engine_scores": self.engine_scores,
            "signals": [s.to_dict() for s in self.signals],
            "top_recommendations": self._top_recommendations(),
        }

    def _top_recommendations(self) -> List[dict]:
        recs = []
        for s in sorted(self.signals, key=lambda x: x.score):
            if s.score < 70:
                for r in s.recommendations:
                    recs.append({"signal": s.name, "recommendation": r, "impact": "high" if s.score < 40 else "medium"})
        return recs[:10]



class GEOChecker:
    """GEO (Generative Engine Optimization) checker for AI engine readiness."""

    ALL_ENGINES = ["ChatGPT", "Gemini", "Perplexity", "Copilot"]

    def check(self, html: str, url: str, target_keyword: Optional[str] = None) -> GEOCheckResult:
        """Run all GEO signal checks."""
        self.soup = BeautifulSoup(html, "html.parser")
        self.html = html
        self.url = url
        self.target_keyword = target_keyword or ""
        self.text_content = self.soup.get_text(separator=" ", strip=True)
        self.paragraphs = [
            p.get_text(strip=True) for p in self.soup.find_all("p")
            if len(p.get_text(strip=True)) > 20
        ]

        signals = [
            self._check_citability(),
            self._check_entity_definition(),
            self._check_answer_format(),
            self._check_structured_knowledge(),
            self._check_authority_signals(),
            self._check_factual_density(),
            self._check_ai_snippet_readiness(),
            self._check_multi_engine_optimization(),
        ]

        return GEOCheckResult(url=url, signals=signals)


    def _check_citability(self) -> GEOSignalResult:
        """Check if content has clear, quotable statements."""
        quotable = []
        for p in self.paragraphs:
            words = p.split()
            if 15 <= len(words) <= 45 and not p.endswith("?"):
                # Check for declarative, factual tone
                if re.match(r'^[A-Z]', p) and re.search(r'\.$', p):
                    quotable.append(p)

        ratio = len(quotable) / max(len(self.paragraphs), 1)
        score = min(100, round(ratio * 200))

        recs = []
        if score < 60:
            recs.append("Write more self-contained declarative sentences (15-45 words).")
            recs.append("End statements with periods, not questions or ellipses.")
            recs.append("Each paragraph should contain at least one quotable fact.")
        if score < 40:
            recs.append("Restructure content into clear claim + evidence format.")

        return GEOSignalResult(
            "Citability", score,
            f"{len(quotable)} quotable statements from {len(self.paragraphs)} paragraphs",
            recs, self.ALL_ENGINES
        )

    def _check_entity_definition(self) -> GEOSignalResult:
        """Check if key entities are clearly defined with context."""
        # Look for definition patterns
        definition_patterns = [
            r'(\w+)\s+(is|are|was|were)\s+(a|an|the)\s+',
            r'(\w+),?\s+(defined as|known as|referred to as)',
            r'(\w+)\s*[-–—]\s*[A-Z]',
        ]
        definitions = 0
        for pattern in definition_patterns:
            definitions += len(re.findall(pattern, self.text_content))

        # Check for highlighted entities
        strong_tags = self.soup.find_all(["strong", "b", "dfn", "abbr"])
        entity_count = len(strong_tags)

        score = min(100, definitions * 12 + entity_count * 8)

        recs = []
        if definitions < 3:
            recs.append("Define key terms explicitly: 'X is a type of...'")
        if entity_count < 5:
            recs.append("Use <strong>, <dfn>, or <abbr> to highlight key entities.")
        if score < 50:
            recs.append("Add a glossary or definitions section for complex topics.")

        return GEOSignalResult(
            "Entity Definition", score,
            f"{definitions} definitions, {entity_count} highlighted entities",
            recs, self.ALL_ENGINES
        )


    def _check_answer_format(self) -> GEOSignalResult:
        """Check if content provides direct, concise answers to questions."""
        # Look for Q&A patterns
        questions = re.findall(r'[^.!?]*\?', self.text_content)
        headings = self.soup.find_all(re.compile(r'^h[2-4]$'))
        question_headings = [h for h in headings if '?' in h.get_text() or
                            h.get_text().lower().startswith(('how', 'what', 'why', 'when', 'where', 'who'))]

        # Check for answers following questions/headings
        answers_after_q = 0
        for h in question_headings:
            next_el = h.find_next_sibling()
            if next_el and next_el.name == "p":
                first_sentence = next_el.get_text(strip=True).split('.')[0]
                if len(first_sentence.split()) <= 30:
                    answers_after_q += 1

        # Direct answer patterns
        direct_answers = len(re.findall(
            r'(The answer is|In short|Simply put|To summarize|The key point is)',
            self.text_content, re.I
        ))

        score = min(100, len(question_headings) * 15 + answers_after_q * 20 + direct_answers * 10)

        recs = []
        if len(question_headings) < 3:
            recs.append("Use question-format headings (What is X? How to Y?)")
        if answers_after_q < 2:
            recs.append("Follow each question heading with a concise 1-2 sentence answer.")
        if direct_answers < 1:
            recs.append("Include direct answer phrases like 'The answer is...' or 'In short...'")

        return GEOSignalResult(
            "Answer Format", score,
            f"{len(question_headings)} Q-headings, {answers_after_q} with direct answers",
            recs, ["ChatGPT", "Perplexity", "Gemini"]
        )

    def _check_structured_knowledge(self) -> GEOSignalResult:
        """Check if information is organized in parseable structures."""
        lists = self.soup.find_all(["ul", "ol"])
        tables = self.soup.find_all("table")
        dl_tags = self.soup.find_all("dl")
        code_blocks = self.soup.find_all(["code", "pre"])
        json_ld = self.soup.find_all("script", type="application/ld+json")

        # Score based on variety and count
        struct_score = 0
        struct_score += min(30, len(lists) * 10)
        struct_score += min(25, len(tables) * 15)
        struct_score += min(15, len(dl_tags) * 10)
        struct_score += min(15, len(code_blocks) * 5)
        struct_score += min(15, len(json_ld) * 10)
        score = min(100, struct_score)

        recs = []
        if len(lists) < 2:
            recs.append("Add bulleted or numbered lists for key points.")
        if len(tables) < 1:
            recs.append("Include comparison tables for data-rich content.")
        if len(json_ld) < 1:
            recs.append("Add JSON-LD structured data for machine readability.")
        if len(dl_tags) < 1:
            recs.append("Use definition lists (<dl>) for term-definition pairs.")

        return GEOSignalResult(
            "Structured Knowledge", score,
            f"Lists: {len(lists)}, Tables: {len(tables)}, DLs: {len(dl_tags)}, Schema: {len(json_ld)}",
            recs, self.ALL_ENGINES
        )


    def _check_authority_signals(self) -> GEOSignalResult:
        """Check for author info, publication date, source citations."""
        signals = {}

        # Author presence
        author_el = self.soup.find(class_=re.compile(r'author', re.I)) or \
                    self.soup.find(attrs={"rel": "author"})
        author_schema = bool(re.search(r'"author"', self.html))
        signals["author"] = author_el is not None or author_schema

        # Publication date
        time_el = self.soup.find("time")
        date_el = self.soup.find(class_=re.compile(r'date|published|updated', re.I))
        date_schema = bool(re.search(r'"datePublished"|"dateModified"', self.html))
        signals["date"] = time_el is not None or date_el is not None or date_schema

        # Source citations
        citations = self.soup.find_all("cite")
        blockquotes = self.soup.find_all("blockquote")
        ref_links = [a for a in self.soup.find_all("a", href=True)
                    if re.search(r'source|reference|citation', a.get_text(), re.I)]
        signals["citations"] = len(citations) + len(blockquotes) + len(ref_links) > 0

        # Credentials / expertise signals
        has_credentials = bool(re.search(
            r'(PhD|MD|expert|specialist|years of experience|certified|professional)',
            self.text_content, re.I
        ))
        signals["credentials"] = has_credentials

        score = sum(25 for v in signals.values() if v)

        recs = []
        if not signals["author"]:
            recs.append("Add visible author name with credentials/bio.")
        if not signals["date"]:
            recs.append("Add publication and last-updated dates using <time> element.")
        if not signals["citations"]:
            recs.append("Cite sources using <cite> tags and link to references.")
        if not signals["credentials"]:
            recs.append("Mention author expertise or credentials.")

        return GEOSignalResult(
            "Authority Signals", score,
            f"Author: {'✓' if signals['author'] else '✗'}, Date: {'✓' if signals['date'] else '✗'}, Citations: {'✓' if signals['citations'] else '✗'}, Credentials: {'✓' if signals['credentials'] else '✗'}",
            recs, self.ALL_ENGINES
        )

    def _check_factual_density(self) -> GEOSignalResult:
        """Check ratio of verifiable claims to opinion."""
        # Count statistics and data points
        stats = re.findall(r'\d+\.?\d*\s*(%|percent|million|billion|thousand)', self.text_content, re.I)
        numbers = re.findall(r'\b\d{2,}\b', self.text_content)
        years = re.findall(r'\b(19|20)\d{2}\b', self.text_content)

        # Opinion indicators
        opinions = re.findall(
            r'\b(I think|I believe|in my opinion|probably|maybe|perhaps|seems like)\b',
            self.text_content, re.I
        )

        # Source references
        sources = re.findall(
            r'(according to|study|research|survey|report|data from|analysis)',
            self.text_content, re.I
        )

        fact_signals = len(stats) + len(years) + len(sources)
        opinion_count = len(opinions)
        word_count = len(self.text_content.split())

        # Score: higher factual density = better for AI
        density = fact_signals / max(word_count / 100, 1)
        opinion_penalty = min(30, opinion_count * 10)
        score = min(100, round(density * 40 + len(sources) * 10) - opinion_penalty)
        score = max(0, score)

        recs = []
        if len(stats) < 3:
            recs.append("Include specific statistics and percentages.")
        if len(sources) < 2:
            recs.append("Reference studies, reports, or authoritative sources.")
        if opinion_count > 3:
            recs.append("Replace opinion phrases with evidence-backed claims.")

        return GEOSignalResult(
            "Factual Density", score,
            f"Stats: {len(stats)}, Sources: {len(sources)}, Opinions: {opinion_count}",
            recs, ["Perplexity", "Gemini", "ChatGPT"]
        )


    def _check_ai_snippet_readiness(self) -> GEOSignalResult:
        """Check if content is formatted for AI extraction."""
        score = 0
        details = []

        # Check for summary/TLDR section
        has_summary = bool(self.soup.find(class_=re.compile(r'summary|tldr|takeaway|key.?point', re.I)))
        if has_summary:
            score += 20
            details.append("Summary section: ✓")
        else:
            details.append("Summary section: ✗")

        # Check for well-structured first paragraph (answering the main topic)
        first_p = self.soup.find("p")
        if first_p:
            fp_text = first_p.get_text(strip=True)
            fp_words = len(fp_text.split())
            if 20 <= fp_words <= 60:
                score += 20
                details.append("Concise intro: ✓")
            else:
                details.append("Concise intro: ✗")

        # Check for bullet points summarizing key info
        lists_near_top = 0
        for i, el in enumerate(self.soup.find_all(["p", "ul", "ol"])[:10]):
            if el.name in ("ul", "ol"):
                lists_near_top += 1
        if lists_near_top >= 1:
            score += 15
            details.append("Early lists: ✓")
        else:
            details.append("Early lists: ✗")

        # Check for clear section labels
        headings = self.soup.find_all(re.compile(r'^h[2-4]$'))
        descriptive_h = sum(1 for h in headings if len(h.get_text(strip=True).split()) >= 3)
        if descriptive_h >= 3:
            score += 20
            details.append(f"Descriptive headings: {descriptive_h}")
        else:
            details.append(f"Descriptive headings: {descriptive_h} (need 3+)")

        # Meta description as snippet seed
        meta_desc = self.soup.find("meta", attrs={"name": "description"})
        if meta_desc and len(meta_desc.get("content", "")) >= 100:
            score += 15
            details.append("Meta description: ✓")
        else:
            details.append("Meta description: ✗")

        # Semantic HTML usage
        semantic_tags = self.soup.find_all(["article", "section", "aside", "main", "nav"])
        if len(semantic_tags) >= 2:
            score += 10
            details.append("Semantic HTML: ✓")
        else:
            details.append("Semantic HTML: ✗")

        score = min(100, score)

        recs = []
        if not has_summary:
            recs.append("Add a key takeaways or TL;DR section near the top.")
        if lists_near_top < 1:
            recs.append("Include a bullet-point summary of key facts early in content.")
        if descriptive_h < 3:
            recs.append("Use descriptive multi-word headings for clear section labeling.")

        return GEOSignalResult(
            "AI Snippet Readiness", score,
            " | ".join(details),
            recs, self.ALL_ENGINES
        )


    def _check_multi_engine_optimization(self) -> GEOSignalResult:
        """Check optimization signals for ChatGPT, Gemini, Perplexity, Copilot."""
        engine_signals = {}

        # ChatGPT: prefers well-structured, comprehensive content
        word_count = len(self.text_content.split())
        headings = len(self.soup.find_all(re.compile(r'^h[2-4]$')))
        chatgpt_score = min(100, (word_count // 50) + headings * 5)
        engine_signals["ChatGPT"] = chatgpt_score

        # Gemini: values structured data, schema, and authoritative sources
        json_ld = len(self.soup.find_all("script", type="application/ld+json"))
        sources = len(re.findall(r'(according to|source|research|study)', self.text_content, re.I))
        gemini_score = min(100, json_ld * 25 + sources * 15 + headings * 5)
        engine_signals["Gemini"] = gemini_score

        # Perplexity: values citations, links to sources, factual density
        ext_links = len([a for a in self.soup.find_all("a", href=True)
                        if a.get("href", "").startswith("http")])
        stats = len(re.findall(r'\d+%', self.text_content))
        perplexity_score = min(100, ext_links * 8 + stats * 10 + sources * 12)
        engine_signals["Perplexity"] = perplexity_score

        # Copilot: values code examples, technical precision, step-by-step
        code_blocks = len(self.soup.find_all(["code", "pre"]))
        ordered_lists = len(self.soup.find_all("ol"))
        copilot_score = min(100, code_blocks * 15 + ordered_lists * 12 + headings * 5)
        engine_signals["Copilot"] = copilot_score

        overall = round(sum(engine_signals.values()) / 4)

        recs = []
        if chatgpt_score < 60:
            recs.append("Add more comprehensive content with clear heading structure for ChatGPT.")
        if gemini_score < 60:
            recs.append("Add JSON-LD schema and cite authoritative sources for Gemini.")
        if perplexity_score < 60:
            recs.append("Include external source links and statistics for Perplexity.")
        if copilot_score < 60:
            recs.append("Add code examples and step-by-step instructions for Copilot.")

        return GEOSignalResult(
            "Multi-Engine Optimization", overall,
            f"ChatGPT: {chatgpt_score}, Gemini: {gemini_score}, Perplexity: {perplexity_score}, Copilot: {copilot_score}",
            recs, self.ALL_ENGINES
        )
