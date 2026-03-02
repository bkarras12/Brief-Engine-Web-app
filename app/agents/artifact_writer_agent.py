"""Artifact Writer Agent — generates non-article SEO deliverables.

Outputs are standardized so the web app can show a 'primary' text artifact.
"""

import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput


ARTIFACT_KINDS = {
    "article",
    "landing_page",
    "faq_page",
    "content_brief",
    "meta_pack",
    "social_pack",
    "gbp_post",
}

TEMPLATES = {
    "landing_page": """Required structure (use exactly):
## Quick Answer
## Key Takeaways
## What You Get  (benefits list)
## How It Works  (numbered steps)
## FAQs          (at least 4 questions as ### headings)
## Sources       (only provided URLs; if none, omit section)
Include a clear CTA (button-style text is fine).""",

    "faq_page": """Required structure (use exactly):
## Quick Answer
## FAQs  (at least 8 questions as ### headings)
## Sources  (only provided URLs; if none, omit section)""",

    "content_brief": """Required structure (use exactly):
## Target Keyword
## Search Intent
## Audience & Tone
## Suggested Title Options  (3–5 title ideas)
## Outline  (H2/H3 structure)
## FAQs  (question list only, no answers)
## Internal Link Ideas
## Sources  (only provided URLs; if none, omit section)""",

    "meta_pack": """Required structure (use exactly):
## Meta Titles  (10 options, each ~50–60 characters)
## Meta Descriptions  (10 options, each ~150–160 characters)
No sources section needed.""",

    "social_pack": """Required structure (use exactly):
## LinkedIn  (3 posts — hook + value + CTA each)
## X  (3 posts — punchy, under 280 chars each)
## Instagram  (3 captions — visual hook + value + hashtags)
No sources section needed.""",

    "gbp_post": """Required structure (use exactly):
## Post  (1–2 short variations, local-business friendly)
## CTA
## Keywords  (5–8 local/service keywords)
No sources section needed.""",

    "article": """Required structure (use exactly):
## Quick Answer  (3–5 sentences)
## Key Takeaways  (5–8 bullet points)
[body sections with H2s derived from the outline]
## FAQs  (at least 4 questions as ### headings)
## Sources  (only provided URLs; if none, omit section)""",
}


class ArtifactWriterAgent(BaseAgent):
    name = "artifact_writer"
    role = "SEO Copywriter"
    goal = "Create high-quality SEO artifacts in a consistent, structured format."
    config_key = "artifact_writer"

    @property
    def system_prompt(self) -> str:
        return """You are an expert SEO copywriter.

You will be asked to generate ONE SEO artifact.

Output rules:
- Always respond in JSON with the following structure:
{
  "artifact_kind": "...",
  "title": "... (optional)",
  "meta_title": "... (optional)",
  "meta_description": "... (optional)",
  "content_md": "...",
  "notes": "... (optional)"
}

Formatting rules:
- content_md must be valid Markdown.
- Follow the Required structure provided in the user prompt exactly — do not add or remove sections.
- Never include "as an AI" disclaimers.
- Never invent URLs.
- If web sources are provided, cite them with footnotes [^1] and include a ## Sources section with ONLY provided URLs.
"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        start = time.time()
        brand = inputs.get("brand_profile", {})
        keyword = inputs.get("keyword", "")
        artifact_kind = (inputs.get("artifact_kind") or "article").strip()
        plan = inputs.get("plan", {})
        research = inputs.get("research", {})

        if artifact_kind not in ARTIFACT_KINDS:
            artifact_kind = "article"

        sources_text = self._format_sources(research)

        template = TEMPLATES.get(artifact_kind, TEMPLATES["article"])

        prompt = f"""Generate the requested SEO artifact.

artifact_kind: {artifact_kind}
keyword/topic: {keyword}

{template}

Brand:
- Company: {brand.get('company_name', 'Your Company')}
- Industry: {brand.get('industry', 'general')}
- Audience: {brand.get('target_audience', 'general audience')}
- Voice: {brand.get('voice', 'clear, helpful, practical')}

Plan:
- Intent: {plan.get('search_intent', '')}
- Goal: {plan.get('primary_goal', '')}
- Key points: {plan.get('key_points', [])}
- CTA: {plan.get('cta', '')}

Research helpers:
- Related keywords: {', '.join((research.get('related_keywords') or [])[:8])}
- Questions people ask: {', '.join((research.get('questions_people_ask') or [])[:8])}

Allowed web sources to cite (do not invent links):
{sources_text}

Return JSON only."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        if data.get("parse_error"):
            raw = data.get("raw_response", "")
            data = {
                "artifact_kind": artifact_kind,
                "title": f"{keyword.title()}" if keyword else "SEO Artifact",
                "meta_title": "",
                "meta_description": "",
                "content_md": raw or f"## Quick Answer\n\nDraft output for {keyword}.",
                "notes": "JSON parsing failed; raw output wrapped.",
            }

        data.setdefault("artifact_kind", artifact_kind)
        data.setdefault("title", "")
        data.setdefault("meta_title", "")
        data.setdefault("meta_description", "")
        data.setdefault("content_md", "")
        data.setdefault("notes", "")

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )

    def _format_sources(self, research: dict) -> str:
        web = (research.get("web_research") or {}) if isinstance(research, dict) else {}
        results = web.get("results", []) if isinstance(web, dict) else []
        top_sources = web.get("top_sources", []) if isinstance(web, dict) else []
        sources = top_sources or results
        if not sources:
            return "(none)"

        urls = []
        for s in sources[:8]:
            url = (s.get("url") or "").strip()
            if url:
                urls.append(url)

        seen = set()
        out = []
        for u in urls:
            if u in seen:
                continue
            seen.add(u)
            out.append(u)

        return "\n".join(f"- {u}" for u in out) if out else "(none)"
