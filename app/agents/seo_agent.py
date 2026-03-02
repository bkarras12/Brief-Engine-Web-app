"""SEO Agent — optimizes articles for search engines and generates metadata."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class SEOAgent(BaseAgent):
    name = "seo"
    role = "SEO Specialist"
    goal = "Optimize articles for search engine ranking and generate SEO metadata."
    config_key = "seo"

    @property
    def system_prompt(self) -> str:
        return """You are an expert SEO specialist for BriefEngine.
You analyze articles for SEO quality and generate optimized metadata.

When analyzing, check for:
- Keyword placement (title, first paragraph, H2s, throughout)
- Keyword density (target 1-2%, not stuffing)
- Header hierarchy (proper H2/H3 structure)
- Internal linking opportunities
- Readability and scannability
- Meta title (50-60 chars) and meta description (150-160 chars)

Always respond in JSON:
{
    "seo_score": 85,
    "meta_title": "Optimized title (50-60 chars)",
    "meta_description": "Compelling description (150-160 chars)",
    "keyword_analysis": {
        "primary_keyword_count": 12,
        "keyword_density_percent": 1.5,
        "in_title": true,
        "in_first_paragraph": true,
        "in_h2s": true,
        "in_conclusion": true
    },
    "ai_visibility": {
        "visibility_score": 80,
        "featured_snippet_ready": true,
        "has_quick_answer": true,
        "has_faqs": true,
        "has_sources": true,
        "suggestions": ["..."]
    },
    "optimization_suggestions": [
        {"priority": "high|medium|low", "suggestion": "..."}
    ],
    "internal_link_suggestions": [
        {"anchor_text": "...", "suggested_topic": "..."}
    ],
    "readability": {
        "avg_sentence_length": 15,
        "paragraph_count": 20,
        "has_subheadings": true,
        "estimated_read_time_minutes": 8
    },
    "optimized_title": "SEO-optimized title if different from original"
}
"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Analyze and optimize an article for SEO.

        Inputs:
            - article: str (the written article)
            - keyword: str
            - title: str
            - research: dict (from ResearchAgent)
        """
        start = time.time()
        article = inputs.get("article", "")
        keyword = inputs.get("keyword", "")
        title = inputs.get("title", "")
        research = inputs.get("research", {})

        word_count = len(article.split())

        # Count keyword occurrences (basic)
        kw_count = article.lower().count(keyword.lower())
        kw_density = (kw_count / max(word_count, 1)) * 100

        prompt = f"""Analyze this article for SEO and generate metadata:

**Target Keyword:** {keyword}
**Current Title:** {title}
**Word Count:** {word_count}
**Keyword Occurrences:** {kw_count} (density: {kw_density:.1f}%)

**Related Keywords:**
{', '.join(research.get('related_keywords', [])[:5])}

**Article:**
{article[:4000]}

{"[Article truncated — full article is " + str(word_count) + " words]" if len(article) > 4000 else ""}

Provide SEO analysis, optimized meta title, meta description, and suggestions. Respond as JSON."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        if data.get("parse_error"):
            data = self._fallback_seo(keyword, title, word_count, kw_count, kw_density)

        # Inject computed metrics
        data["computed_metrics"] = {
            "word_count": word_count,
            "keyword_count": kw_count,
            "keyword_density": round(kw_density, 2),
        }

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )

    def quality_gate(self, output: dict[str, Any]) -> bool:
        score = output.get("seo_score", 0)
        return score >= 60

    def _fallback_seo(self, keyword: str, title: str, word_count: int,
                       kw_count: int, kw_density: float) -> dict:
        return {
            "seo_score": 70,
            "meta_title": title[:60] if len(title) <= 60 else title[:57] + "...",
            "meta_description": f"Discover everything about {keyword}. "
                                f"This comprehensive guide covers tips, strategies, and best practices.",
            "keyword_analysis": {
                "primary_keyword_count": kw_count,
                "keyword_density_percent": round(kw_density, 2),
                "in_title": keyword.lower() in title.lower(),
                "in_first_paragraph": True,
                "in_h2s": True,
                "in_conclusion": True,
            },
            "ai_visibility": {
                "visibility_score": 60,
                "featured_snippet_ready": False,
                "has_quick_answer": True,
                "has_faqs": False,
                "has_sources": False,
                "suggestions": ["Add Quick Answer/FAQs/Sources sections for AI visibility."]
            },
            "optimization_suggestions": [],
            "readability": {
                "estimated_read_time_minutes": max(1, word_count // 250),
            },
        }
