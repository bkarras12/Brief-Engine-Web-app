"""Outline Agent — creates structured, SEO-aware article outlines."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class OutlineAgent(BaseAgent):
    name = "outline"
    role = "Content Architect"
    goal = "Create detailed, SEO-optimized article outlines that guide the writer."
    config_key = "outline"

    @property
    def system_prompt(self) -> str:
        return """You are an expert content architect who creates detailed article outlines.
Your outlines are structured for both readers (scannable, logical flow) and search engines (H2/H3 hierarchy, keyword placement).

Always respond in JSON:
{
    "title_options": ["Title 1", "Title 2", "Title 3"],
    "recommended_title": "Best title",
    "hook": "Compelling opening sentence or question",
    "sections": [
        {
            "h2": "Section Heading",
            "h3s": ["Sub-heading 1", "Sub-heading 2"],
            "key_points": ["point 1", "point 2"],
            "target_word_count": 300,
            "keywords_to_include": ["kw1", "kw2"]
        }
    ],
    "conclusion": {
        "summary_points": ["point1", "point2"],
        "cta": "Call to action text"
    },
    "internal_link_opportunities": ["topic1", "topic2"],
    "estimated_total_words": 2000
}"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Generate an article outline.

        Inputs:
            - keyword: str
            - research: dict (from ResearchAgent)
            - content_plan: dict (from CEOAgent)
            - brand_profile: dict
        """
        start = time.time()
        keyword = inputs.get("keyword", "")
        research = inputs.get("research", {})
        plan = inputs.get("content_plan", {})
        brand = inputs.get("brand_profile", {})

        prompt = f"""Create a detailed article outline for:

**Target Keyword:** {keyword}
**Article Angle:** {plan.get('article_angle', f'Comprehensive guide to {keyword}')}
**Search Intent:** {research.get('search_intent', 'informational')}
**Target Audience:** {plan.get('target_audience', 'general readers')}
**Tone:** {plan.get('outline_requirements', {}).get('tone', 'professional')}

**Related Keywords to Include:**
{', '.join(research.get('related_keywords', [])[:8])}

**Questions to Answer:**
{chr(10).join('- ' + q for q in research.get('questions_people_ask', [])[:5])}

**Must Include Topics:**
{', '.join(plan.get('outline_requirements', {}).get('must_include', [keyword]))}

**Target Word Count:** {plan.get('quality_criteria', {}).get('target_word_count', 2000)}

Create an SEO-optimized outline with 5-8 main sections. Respond as JSON."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        if data.get("parse_error"):
            data = self._fallback_outline(keyword, research)

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )

    def quality_gate(self, output: dict[str, Any]) -> bool:
        sections = output.get("sections", [])
        return 3 <= len(sections) <= 12

    def _fallback_outline(self, keyword: str, research: dict) -> dict:
        questions = research.get("questions_people_ask", [f"What is {keyword}?"])
        return {
            "title_options": [
                f"The Complete Guide to {keyword.title()}",
                f"{keyword.title()}: Everything You Need to Know",
            ],
            "recommended_title": f"The Complete Guide to {keyword.title()}",
            "hook": f"Looking for the best advice on {keyword}? This guide covers everything.",
            "sections": [
                {
                    "h2": f"What is {keyword.title()}?",
                    "h3s": ["Definition", "Why It Matters"],
                    "key_points": ["Define the concept", "Explain importance"],
                    "target_word_count": 300,
                    "keywords_to_include": [keyword],
                },
                {
                    "h2": f"Key Benefits of {keyword.title()}",
                    "h3s": [],
                    "key_points": ["Benefit 1", "Benefit 2", "Benefit 3"],
                    "target_word_count": 400,
                    "keywords_to_include": research.get("related_keywords", [])[:2],
                },
                {
                    "h2": f"How to Get Started with {keyword.title()}",
                    "h3s": ["Step 1", "Step 2", "Step 3"],
                    "key_points": ["Actionable steps"],
                    "target_word_count": 500,
                    "keywords_to_include": research.get("long_tail_variations", [])[:2],
                },
                {
                    "h2": "Common Mistakes to Avoid",
                    "h3s": [],
                    "key_points": ["Mistake 1", "Mistake 2"],
                    "target_word_count": 300,
                    "keywords_to_include": [],
                },
                {
                    "h2": "Frequently Asked Questions",
                    "h3s": questions[:3],
                    "key_points": ["Answer each question concisely"],
                    "target_word_count": 400,
                    "keywords_to_include": research.get("long_tail_variations", [])[:2],
                },
            ],
            "conclusion": {
                "summary_points": ["Recap key takeaways", "Reinforce value"],
                "cta": f"Ready to get started with {keyword}? Take the first step today.",
            },
            "internal_link_opportunities": [],
            "estimated_total_words": 1900,
        }
