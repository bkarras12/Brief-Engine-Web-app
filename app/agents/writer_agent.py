"""Writer Agent — produces long-form, engaging, source-aware articles from outlines."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class WriterAgent(BaseAgent):
    name = "writer"
    role = "Senior Content Writer"
    goal = (
        "Write compelling, well-researched, publish-ready articles that engage readers "
        "and naturally incorporate SEO keywords."
    )
    config_key = "writer"

    @property
    def system_prompt(self) -> str:
        return """You are a senior content writer for BriefEngine.
You write engaging, well-structured, publish-ready blog articles.

Hard requirements (quality + AI visibility):
- Use clear structure and headings (H2/H3) in Markdown
- Include these H2 sections exactly once each:
  1) ## Quick Answer (3–5 sentences, directly answering the query)
  2) ## Key Takeaways (5–8 bullet points)
  3) ## FAQs (at least 4 questions as ### headings, each with a direct answer)
  4) ## Sources (ONLY include provided URLs; do not invent links)
- Add practical examples, step-by-step guidance, and checklists
- Avoid fluff and repetitive filler

Research & citations:
- When you state a specific fact, statistic, or strong claim, add a footnote marker like [^1].
- In ## Sources, include matching footnotes:
  [^1]: https://example.com (Source Title)
- IMPORTANT: Never invent URLs. Only cite from the provided sources list.
- If no sources were provided, include a Sources section that clearly says live research was not available and citations are needed before publishing.

Style:
- Natural human voice, short paragraphs (2–4 sentences)
- Active voice, varied sentence length
- No "AI" disclaimers (e.g., "as an AI language model")
- Do NOT include the title as H1 (it will be added separately)
- Do NOT include meta title/description in the article body
"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Write a full article from an outline.

        Inputs:
            - keyword: str
            - outline: dict (from OutlineAgent)
            - research: dict (from ResearchAgent)
            - brand_profile: dict
            - content_plan: dict (from CEOAgent)
        """
        start = time.time()
        keyword = inputs.get("keyword", "")
        outline = inputs.get("outline", {})
        research = inputs.get("research", {})
        brand = inputs.get("brand_profile", {})
        plan = inputs.get("content_plan", {})

        voice_desc = brand.get("voice_guidelines", {})
        tone = voice_desc.get("tone", "professional") if isinstance(voice_desc, dict) else "professional"
        traits = voice_desc.get("personality_traits", []) if isinstance(voice_desc, dict) else []

        sections_text = self._format_outline(outline)
        facts_text = self._format_facts(research)
        sources_text = self._format_sources(research)

        prompt = f"""Write a complete blog article based on this outline.

**Title (for reference):** {outline.get('recommended_title', f'Guide to {keyword}')}

**Opening Hook:** {outline.get('hook', '')}

**Outline:**
{sections_text}

**Conclusion guidance:**
- Summary: {outline.get('conclusion', {}).get('summary_points', [])}
- CTA: {outline.get('conclusion', {}).get('cta', '')}

**SEO Keywords to Naturally Include:**
Primary: {keyword}
Secondary: {', '.join(research.get('related_keywords', [])[:6])}

**Key Facts/Stats to Reference (use citations where possible):**
{facts_text}

**Allowed web sources to cite (do not invent links):**
{sources_text}

**Voice & Tone:**
- Tone: {tone}
- Personality: {', '.join(traits) if traits else 'Helpful and knowledgeable'}
- Company: {brand.get('company_name', 'BriefEngine client')}

**Target Word Count:** {plan.get('quality_criteria', {}).get('target_word_count', 2000)}

Now write the FULL article in Markdown.
Remember: include ## Quick Answer, ## Key Takeaways, ## FAQs, ## Sources sections.
Make it engaging, practical, and thorough. Every section should provide real value — no filler."""

        article = self.invoke(prompt)
        elapsed = time.time() - start
        word_count = len(article.split())

        logger.info(f"[Writer] Article produced: {word_count} words in {elapsed:.1f}s")

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data={
                "article": article,
                "word_count": word_count,
                "title": outline.get("recommended_title", f"Guide to {keyword}"),
            },
            elapsed_seconds=elapsed,
        )

    def quality_gate(self, output: dict[str, Any]) -> bool:
        """Article must be at least 800 words."""
        return output.get("word_count", 0) >= 800

    def _format_outline(self, outline: dict) -> str:
        lines = []
        for i, section in enumerate(outline.get("sections", []), 1):
            lines.append(f"\n## {section.get('h2', f'Section {i}')}")
            for h3 in section.get("h3s", []):
                lines.append(f"  ### {h3}")
            for point in section.get("key_points", []):
                lines.append(f"  - {point}")
            wc = section.get("target_word_count", 300)
            lines.append(f"  [Target: ~{wc} words]")
            kws = section.get("keywords_to_include", [])
            if kws:
                lines.append(f"  [Include keywords: {', '.join(kws)}]")
        return "\n".join(lines)

    def _format_facts(self, research: dict) -> str:
        facts = research.get("key_facts_and_stats", [])
        if not facts:
            return "Use the provided sources (if any) and add concrete examples. Avoid making up statistics."
        lines = []
        for f in facts[:10]:
            if isinstance(f, dict):
                lines.append(f"- {f.get('fact', '')} ({f.get('source_type', '')})")
            else:
                lines.append(f"- {f}")
        return "\n".join(lines)

    def _format_sources(self, research: dict) -> str:
        web = (research.get("web_research") or {}) if isinstance(research, dict) else {}
        results = web.get("results", []) if isinstance(web, dict) else []
        top_sources = web.get("top_sources", []) if isinstance(web, dict) else []

        sources = top_sources or results
        if not sources:
            return "(none)"

        lines = []
        for i, s in enumerate(sources[:8], 1):
            title = (s.get("title") or "").strip()
            url = (s.get("url") or "").strip()
            snippet = (s.get("snippet") or "").strip()
            if not url:
                continue
            lines.append(f"{i}. {title} — {url}")
            if snippet:
                lines.append(f"   - {snippet}")
        return "\n".join(lines)
