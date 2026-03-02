"""Quality Fixer Agent — repairs guardrail issues (citations, structure, AI visibility)."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class QualityFixerAgent(BaseAgent):
    name = "quality_fixer"
    role = "Content QA Editor"
    goal = (
        "Fix articles that fail quality guardrails by adding missing sections, "
        "tightening claims, and ensuring citations and AI-visibility structure."
    )
    config_key = "quality_fixer"

    @property
    def system_prompt(self) -> str:
        return """You are a meticulous content QA editor.
You will receive:
- A markdown article draft
- A guardrail report with issues/warnings
- A list of web sources (title, url, snippet)

Your job:
1) Fix ALL guardrail issues (missing sections, not enough citations, not enough FAQs, banned phrases).
2) Reduce risky factual claims: if a numeric claim can't be supported by provided sources, remove or rewrite it safely.
3) Ensure AI visibility sections exist and are clean:
   - ## Quick Answer (3–5 sentences)
   - ## Key Takeaways (5–8 bullets)
   - ## FAQs (at least 4 questions as ### headings with answers)
   - ## Sources (numbered list or footnotes with URLs)
4) Do NOT invent URLs. Only cite from the provided sources list. If sources are insufficient, say so in Sources.

Output JSON:
{
  "revised_article": "FULL markdown",
  "changes_made": ["..."],
  "notes": "short QA notes"
}"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        start = time.time()
        article = inputs.get("article", "")
        report = inputs.get("guardrail_report", {})
        sources = inputs.get("web_sources", [])

        # Keep sources small for prompt
        sources_text = ""
        if sources:
            lines = []
            for i, s in enumerate(sources[:8], 1):
                lines.append(f"{i}. {s.get('title','').strip()} — {s.get('url','').strip()} ({s.get('source','web')})")
            sources_text = "\n".join(lines)
        else:
            sources_text = "(none)"

        prompt = f"""Repair this markdown article so it passes guardrails.

**Guardrail report (issues/warnings):**
{report}

**Allowed Sources to Cite (do not invent others):**
{sources_text}

**Article:**
{article}

Return JSON only."""
        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        if data.get("parse_error"):
            # Fall back to raw response if possible
            raw = data.get("raw_response", article)
            data = {
                "revised_article": raw,
                "changes_made": ["Returned raw edit due to JSON parse issues"],
                "notes": "JSON parsing failed; raw output returned.",
            }

        logger.info(f"[QualityFixer] Completed in {elapsed:.1f}s")
        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )
