"""Artifact Planner Agent — plans non-article SEO deliverables.

This agent exists to support a broader SEO product line beyond blog articles.
It produces a lightweight plan (structure, intent, CTA) for a chosen artifact.
"""

import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput


class ArtifactPlannerAgent(BaseAgent):
    name = "artifact_planner"
    role = "SEO Strategist"
    goal = "Plan SEO deliverables (landing pages, FAQs, briefs, meta packs, social packs) with clear structure and success criteria."
    config_key = "artifact_planner"

    @property
    def system_prompt(self) -> str:
        return """You are an SEO strategist.

Your job is to create a short, structured plan for an SEO deliverable.

Always respond in JSON:
{
  "artifact_kind": "article|landing_page|faq_page|content_brief|meta_pack|social_pack|gbp_post",
  "search_intent": "informational|commercial|transactional|navigational",
  "primary_goal": "...",
  "target_audience": "...",
  "tone": "...",
  "key_points": ["..."],
  "cta": "...",
  "structure": {
    "required_sections": ["..."],
    "length_guidance": "..."
  },
  "quality_criteria": {
    "must_include": ["..."],
    "avoid": ["..."]
  }
}

Rules:
- Keep it practical and short.
- If the artifact is long-form (article/landing_page/faq_page), include the sections:
  Quick Answer, Key Takeaways, FAQs, Sources.
- Never include "as an AI" disclaimers.
"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        start = time.time()
        brand = inputs.get("brand_profile", {})
        keyword = inputs.get("keyword", "")
        artifact_kind = inputs.get("artifact_kind", "article")
        extra_context = inputs.get("extra_context", "")

        prompt = f"""Create a plan for this SEO deliverable.

Artifact kind: {artifact_kind}
Target keyword/topic: {keyword}

Brand:
- Company: {brand.get('company_name', 'Unknown')}
- Industry: {brand.get('industry', 'general')}
- Audience: {brand.get('target_audience', 'general audience')}
- Voice: {brand.get('voice', 'clear, helpful, practical')}

Extra context (optional):
{extra_context or '(none)'}

Return JSON only."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        if data.get("parse_error"):
            # Simple deterministic fallback
            req = []
            if artifact_kind in ("article", "landing_page", "faq_page"):
                req = ["Quick Answer", "Key Takeaways", "FAQs", "Sources"]
            data = {
                "artifact_kind": artifact_kind,
                "search_intent": "informational",
                "primary_goal": f"Create a high-quality {artifact_kind} targeting '{keyword}'",
                "target_audience": brand.get("target_audience", "general audience"),
                "tone": brand.get("voice", "clear, helpful, practical"),
                "key_points": [f"Directly address {keyword}", "Be practical and clear", "Include next steps"],
                "cta": "Contact us / start here",
                "structure": {
                    "required_sections": req,
                    "length_guidance": "Use scannable headings, short paragraphs, and bullets.",
                },
                "quality_criteria": {
                    "must_include": [keyword],
                    "avoid": ["AI disclaimers", "invented sources"],
                },
            }

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )
