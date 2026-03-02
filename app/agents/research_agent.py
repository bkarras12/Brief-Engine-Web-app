"""Research Agent — keyword analysis, topic research, competitive insights.

Enhanced features:
- Optional live web research (DuckDuckGo HTML search + page extracts)
- Source-backed facts (LLM extracts facts from fetched sources)
"""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput
from app.tools.search_tools import build_source_pack
from app.config import ENABLE_WEB_RESEARCH

logger = logging.getLogger("briefengine")


class ResearchAgent(BaseAgent):
    name = "research"
    role = "Market & Keyword Researcher"
    goal = (
        "Research the target keyword, identify search intent, find related topics, "
        "and gather data points that will make the article authoritative."
    )
    config_key = "research"

    @property
    def system_prompt(self) -> str:
        return """You are an expert SEO researcher and content strategist.
Given a target keyword and industry context, produce comprehensive research.

Always respond in JSON:
{
    "primary_keyword": "...",
    "search_intent": "informational|commercial|transactional|navigational",
    "related_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
    "long_tail_variations": ["variation1", "variation2", "variation3"],
    "questions_people_ask": ["q1", "q2", "q3", "q4", "q5"],
    "topic_clusters": [
        {"topic": "...", "subtopics": ["...", "..."]}
    ],
    "key_facts_and_stats": [
        {"fact": "...", "source_type": "industry report|study|expert opinion"}
    ],
    "content_gaps": ["gap1", "gap2"],
    "recommended_angle": "the best angle to differentiate this article",
    "estimated_difficulty": "low|medium|high"
}"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Research a keyword and topic.

        Inputs:
            - keyword: str
            - industry: str
            - target_audience: str
            - brand_profile: dict (optional)
        """
        start = time.time()
        keyword = inputs.get("keyword", "")
        industry = inputs.get("industry", "general")
        audience = inputs.get("target_audience", "general audience")

        prompt = f"""Research the following keyword for SEO content creation:

**Target Keyword:** {keyword}
**Industry:** {industry}
**Target Audience:** {audience}

Provide comprehensive keyword research, related topics, common questions,
key facts/statistics, and content gaps in the current landscape.
Focus on actionable insights that will help create a top-ranking article.

Respond as JSON."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        # If JSON parsing failed, fall back
        if data.get("parse_error"):
            data = self._fallback_research(keyword, industry)
            status = "error"
        else:
            status = "success"

        # ── Optional: Live Web Research (sources + extracts) ─────────
        web_pack = {"query": keyword, "results": [], "top_sources": []}
        enable_web_research = inputs.get("enable_web_research", ENABLE_WEB_RESEARCH)
        if enable_web_research:
            web_pack = build_source_pack(keyword)
        data["web_research"] = {
            "enabled": bool(enable_web_research),
            "results": web_pack.get("results", []),
                        "top_sources": web_pack.get("top_sources", []),
        }

        return AgentOutput(
            agent_name=self.name,
            status=status,
            data=data,
            elapsed_seconds=elapsed,
        )

    def quality_gate(self, output: dict[str, Any]) -> bool:
        """Research must include at least 3 related keywords and 3 questions."""
        return (
            len(output.get("related_keywords", [])) >= 3
            and len(output.get("questions_people_ask", [])) >= 3
        )

    def _fallback_research(self, keyword: str, industry: str) -> dict:
        return {
            "primary_keyword": keyword,
            "search_intent": "informational",
            "related_keywords": [
                f"best {keyword}",
                f"{keyword} guide",
                f"{keyword} tips",
                f"how to {keyword}",
                f"{keyword} for beginners",
            ],
            "long_tail_variations": [
                f"what is {keyword}",
                f"how does {keyword} work",
                f"{keyword} examples",
            ],
            "questions_people_ask": [
                f"What is {keyword}?",
                f"How do I choose {keyword}?",
                f"Why is {keyword} important?",
                f"What are the best {keyword} options?",
            ],
            "topic_clusters": [
                {"topic": keyword, "subtopics": ["overview", "benefits", "how-to"]},
            ],
            "key_facts_and_stats": [],
            "content_gaps": ["Most articles lack specific examples and data"],
            "recommended_angle": f"Practical, data-backed guide to {keyword}",
            "estimated_difficulty": "medium",
            "web_research": {"enabled": False, "results": []},
        }
