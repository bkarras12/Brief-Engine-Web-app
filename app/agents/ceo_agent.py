"""CEO Agent — decomposes tasks, allocates work, validates final output."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class CEOAgent(BaseAgent):
    name = "ceo"
    role = "Chief Executive Officer & Content Strategist"
    goal = (
        "Decompose article requests into clear tasks, coordinate the agent team, "
        "and validate that final output meets quality standards."
    )
    config_key = "ceo"

    @property
    def system_prompt(self) -> str:
        return """You are the CEO of BriefEngine, an AI content agency.
Your job is to:
1. Analyze the client brief (brand profile + target keyword)
2. Decompose the work into a structured plan
3. Define success criteria for the final article

You always respond in JSON with this structure:
{
    "article_angle": "the specific angle/hook for this article",
    "target_audience": "who this article is for",
    "search_intent": "informational|commercial|transactional|navigational",
    "content_goals": ["goal1", "goal2"],
    "outline_requirements": {
        "min_sections": 5,
        "max_sections": 8,
        "must_include": ["list of required topics/sections"],
        "tone": "professional|casual|authoritative|friendly"
    },
    "quality_criteria": {
        "min_word_count": 1500,
        "target_word_count": 2000,
        "readability_target": "8th grade",
        "seo_keyword_density": "1-2%"
    }
}"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Analyze brief and produce a content plan.

        Inputs:
            - brand_profile: dict with company info, voice, audience
            - keyword: str target keyword
            - article_type: str (how-to, listicle, guide, comparison, etc.)
        """
        start = time.time()
        brand = inputs.get("brand_profile", {})
        keyword = inputs.get("keyword", "")
        article_type = inputs.get("article_type", "comprehensive guide")

        prompt = f"""Create a content plan for the following:

**Brand:** {brand.get('company_name', 'Unknown')}
**Industry:** {brand.get('industry', 'Unknown')}
**Target Audience:** {brand.get('target_audience', 'General')}
**Brand Voice:** {brand.get('voice', 'Professional and helpful')}
**Target Keyword:** {keyword}
**Article Type:** {article_type}

Produce a detailed content plan as JSON."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        if not data.get("parse_error"):
            logger.info(f"[CEO] Content plan created for '{keyword}'")
        else:
            logger.warning("[CEO] Content plan had parse issues, using fallback")
            data = self._fallback_plan(keyword, brand, article_type)

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )

    def validate_final_article(self, article: str, plan: dict) -> dict:
        """Validate the final article against the content plan."""
        word_count = len(article.split())
        min_words = plan.get("quality_criteria", {}).get("min_word_count", 1200)

        prompt = f"""Review this article against the content plan.

**Content Plan:**
- Angle: {plan.get('article_angle', 'N/A')}
- Goals: {plan.get('content_goals', [])}
- Must include: {plan.get('outline_requirements', {}).get('must_include', [])}

**Article word count:** {word_count}
**Minimum required:** {min_words}

**Article (first 500 words):**
{article[:2000]}

Rate the article on a scale of 1-10 for:
1. Relevance to plan
2. Completeness
3. Quality of writing

Respond in JSON:
{{"relevance": X, "completeness": X, "quality": X, "overall": X, "issues": ["issue1"], "pass": true/false}}"""

        return self.invoke_json(prompt)

    def _fallback_plan(self, keyword: str, brand: dict, article_type: str) -> dict:
        """Deterministic fallback if LLM parsing fails."""
        return {
            "article_angle": f"Comprehensive {article_type} about {keyword}",
            "target_audience": brand.get("target_audience", "General readers"),
            "search_intent": "informational",
            "content_goals": [
                f"Rank for '{keyword}'",
                "Provide actionable value",
                "Establish authority",
            ],
            "outline_requirements": {
                "min_sections": 5,
                "max_sections": 8,
                "must_include": [keyword],
                "tone": brand.get("voice", "professional"),
            },
            "quality_criteria": {
                "min_word_count": 1500,
                "target_word_count": 2000,
                "readability_target": "8th grade",
                "seo_keyword_density": "1-2%",
            },
        }
