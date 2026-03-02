"""Profile Agent — extracts and structures brand voice & audience data."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent, AgentOutput

logger = logging.getLogger("briefengine")


class ProfileAgent(BaseAgent):
    name = "profile"
    role = "Brand Strategist"
    goal = "Extract and structure brand voice, tone, and audience characteristics for consistent content."
    config_key = "profile"

    @property
    def system_prompt(self) -> str:
        return """You are a brand strategist specializing in content voice and tone.
Given a company description, extract a structured brand profile that content writers can follow.

Always respond in JSON:
{
    "company_name": "...",
    "industry": "...",
    "value_proposition": "one sentence",
    "target_audience": {
        "primary": "description",
        "pain_points": ["pain1", "pain2"],
        "goals": ["goal1", "goal2"]
    },
    "voice_guidelines": {
        "tone": "professional|casual|authoritative|friendly|technical",
        "personality_traits": ["trait1", "trait2", "trait3"],
        "vocabulary_level": "simple|moderate|technical",
        "dos": ["do1", "do2"],
        "donts": ["dont1", "dont2"]
    },
    "content_themes": ["theme1", "theme2", "theme3"],
    "competitors": ["competitor1", "competitor2"]
}"""

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Build a brand profile from company description.

        Inputs:
            - company_description: str
            - website_url: str (optional, for future web scraping)
            - existing_content_samples: list[str] (optional)
        """
        start = time.time()
        desc = inputs.get("company_description", "")
        samples = inputs.get("existing_content_samples", [])

        prompt = f"""Analyze this company and create a brand profile:

**Company Description:**
{desc}

{"**Content Samples:** " + chr(10).join(samples[:3]) if samples else ""}

Create a comprehensive brand profile as JSON."""

        data = self.invoke_json(prompt)
        elapsed = time.time() - start

        return AgentOutput(
            agent_name=self.name,
            status="success" if not data.get("parse_error") else "error",
            data=data,
            elapsed_seconds=elapsed,
        )
