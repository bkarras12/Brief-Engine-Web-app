"""Editor Agent — reviews, polishes, and improves article quality."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class EditorAgent(BaseAgent):
    name = "editor"
    role = "Senior Editor"
    goal = (
        "Review articles for grammar, clarity, engagement, and brand voice consistency. "
        "Produce a polished, publish-ready version."
    )
    config_key = "editor"

    @property
    def system_prompt(self) -> str:
        return """You are a senior editor at BriefEngine.
You review and polish articles to publish-ready quality.

Your editing process:
1. Fix any grammar, spelling, or punctuation errors
2. Improve sentence clarity and flow
3. Strengthen weak openings and transitions
4. Remove filler words and redundant phrases
5. Ensure consistent tone and voice throughout
6. Verify logical structure and argument flow
7. Enhance engagement (better hooks, examples, questions)
8. Ensure the article delivers on its title promise

IMPORTANT: Return the FULL edited article, not just suggestions.
Include the complete, polished article in your response.

Format your response as JSON:
{
    "edited_article": "FULL markdown article text here",
    "changes_made": ["change1", "change2", "change3"],
    "quality_score": 85,
    "readability_grade": "8th grade",
    "word_count": 2000,
    "editorial_notes": "Any notes for the content team"
}"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Review and edit an article.

        Inputs:
            - article: str
            - keyword: str
            - brand_profile: dict
            - seo_suggestions: list (optional, from SEOAgent)
        """
        start = time.time()
        article = inputs.get("article", "")
        keyword = inputs.get("keyword", "")
        brand = inputs.get("brand_profile", {})
        seo_suggestions = inputs.get("seo_suggestions", [])

        voice = brand.get("voice_guidelines", {})
        tone = voice.get("tone", "professional") if isinstance(voice, dict) else "professional"
        dos = voice.get("dos", []) if isinstance(voice, dict) else []
        donts = voice.get("donts", []) if isinstance(voice, dict) else []

        seo_text = ""
        if seo_suggestions:
            seo_items = []
            for s in seo_suggestions[:5]:
                if isinstance(s, dict):
                    seo_items.append(f"- [{s.get('priority', 'medium')}] {s.get('suggestion', '')}")
                else:
                    seo_items.append(f"- {s}")
            seo_text = f"\n**SEO Improvements to Apply:**\n" + "\n".join(seo_items)

        prompt = f"""Edit and polish this article to publish-ready quality:

**Target Keyword:** {keyword}
**Brand Tone:** {tone}
{"**Voice Dos:** " + ", ".join(dos) if dos else ""}
{"**Voice Don'ts:** " + ", ".join(donts) if donts else ""}
{seo_text}

**Article to Edit:**
{article}

Return the FULL edited article as JSON with the structure specified in your instructions."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        # If JSON parsing failed, the raw response might be the edited article itself
        if data.get("parse_error"):
            raw = data.get("raw_response", article)
            data = {
                "edited_article": raw,
                "changes_made": ["Returned raw edit due to format issues"],
                "quality_score": 70,
                "word_count": len(raw.split()),
                "editorial_notes": "JSON parsing failed; raw edit returned.",
            }

        word_count = len(data.get("edited_article", "").split())
        data["word_count"] = word_count

        logger.info(
            f"[Editor] Article polished: {word_count} words, "
            f"score={data.get('quality_score', 'N/A')}"
        )

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data=data,
            elapsed_seconds=elapsed,
        )

    def quality_gate(self, output: dict[str, Any]) -> bool:
        return output.get("quality_score", 0) >= 65
